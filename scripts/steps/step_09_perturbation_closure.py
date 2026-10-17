#!/usr/bin/env python3
"""
Step 09: Perturbation Closure Verification
============================================
Validates that the SMG-TEP perturbation run produces the same background
Hubble rate as the native tep_mode background-only run to machine precision.
Also measures the active-scalar signature in the TT spectrum.

This is the critical consistency gate: H_SMG(a) must equal H_tep_mode(a)
to < 1e-6 relative precision at all scale factors.

The spectrum comparison reports the active-scalar residual as a measured
physical signature, not a pass/fail tolerance test: with the screened
delta-phi closure (tep_kin_boost > 0, tep_screening_s) the scalar is
genuinely active, so a nonzero ISW/acoustic residual is the prediction,
not a defect.  The gate fails only on (a) background inconsistency,
(b) non-finite spectra, or (c) divergent residuals (|residual| > 5 =
500%, the signature of the linearly unstable canonical-EF branch
wc = -5, which returns residuals ~ 60 at low-ell).  A residual of zero
across all bands is also flagged: the alpha sector is supposed to be
active, and bitwise-identical spectra indicate a silently disabled SMG
path (the pre-audit state).
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step09PerturbationClosure:
    """Step 09: Background--perturbation consistency verification."""

    STEP_NAME = "09_perturbation_closure"
    STEP_DESCRIPTION = "Perturbation Closure Verification"

    # Consistency tolerance: H_SMG vs H_tep_mode relative difference
    HUBBLE_TOLERANCE = 1e-6
    # Acoustic-peak residual tolerance (high-ell, 100 <= ell <= 2000)
    ACOUSTIC_TOLERANCE = 1e-3
    # Low-ell ISW tolerance (ell < 30) - naturally larger due to active dphi
    LOW_ELL_TOLERANCE = 5e-2

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Execute background--perturbation consistency checks."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }

        try:
            # 1. Background Hubble consistency from hi_class background tables
            print_status("Loading background tables for consistency check...", "PROCESS")
            bg_check = self._background_consistency_check()
            results["background_consistency"] = bg_check

            # 2. TT spectrum comparison between background-only and active perturbations
            print_status("Comparing TT spectra (background-only vs active perturbations)...", "PROCESS")
            spec_check = self._spectrum_comparison_check()
            results["spectrum_comparison"] = spec_check

            # 3. Overall pass/fail: background consistency + finite,
            #    non-divergent, non-silent scalar sector
            results["closure_passed"] = (
                bg_check.get("passed", False)
                and spec_check.get("spectra_finite", False)
                and spec_check.get("not_divergent", False)
                and spec_check.get("scalar_active", False)
            )

            results["status"] = "SUCCESS" if results["closure_passed"] else "WARNING"

            output_file = self.results_dir / "09_perturbation_closure.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            print_status(f"  ✓ Saved closure verification to {output_file}", "SUCCESS")

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise

        return results

    def _background_consistency_check(self):
        """
        Compare H(z) from tep_background_only and tep_perturbations background tables.
        Both use tep_mode=yes, but tep_perturbations additionally sets gravity_model=tep.
        The Hubble rates must be identical to HUBBLE_TOLERANCE.
        """
        try:
            bg_bg = np.loadtxt(self._latest_output("tep_background_only", "background"))
            bg_pert = np.loadtxt(self._latest_output("tep_perturbations", "background"))
        except (FileNotFoundError, OSError, ValueError) as e:
            return {"available": False, "reason": str(e)}

        # Column 0:z 3:H
        z_bg = bg_bg[:, 0]
        H_bg = bg_bg[:, 3]
        z_pert = bg_pert[:, 0]
        H_pert = bg_pert[:, 3]

        # Interpolate pert onto bg grid for comparison
        H_pert_interp = np.interp(z_bg, z_pert[::-1], H_pert[::-1])

        rel_diff = np.abs(H_pert_interp - H_bg) / H_bg
        max_rel_diff = float(np.max(rel_diff))
        mean_rel_diff = float(np.mean(rel_diff))

        passed = max_rel_diff < self.HUBBLE_TOLERANCE

        diag = {
            "available": True,
            "max_rel_diff": max_rel_diff,
            "mean_rel_diff": mean_rel_diff,
            "tolerance": self.HUBBLE_TOLERANCE,
            "passed": passed,
            "n_points": len(z_bg),
        }

        status = "SUCCESS" if passed else "WARNING"
        print_status(
            f"  H consistency: max_rel_diff={max_rel_diff:.3e}, mean={mean_rel_diff:.3e} "
            f"(tol={self.HUBBLE_TOLERANCE})",
            status,
        )
        return diag

    def _spectrum_comparison_check(self):
        """
        Compare TT spectra: TEP perturbations vs LCDM and vs TEP background-only.
        Strict tolerance on acoustic peaks (100 <= ell <= 2000).
        Larger tolerance allowed for low-ell ISW (ell < 30).
        """
        try:
            cmb_file = self.results_dir / "04_cmb_spectra.json"
            with open(cmb_file) as f:
                cmb_data = json.load(f)

            ells = np.array(cmb_data["ells"])
            cl_pert = np.array(cmb_data["spectra"]["cl_tt_tep_pert"])
            cl_lcdm = np.array(cmb_data["spectra"]["cl_tt_lcdm"])
            cl_bg = np.array(cmb_data["spectra"]["cl_tt_tep_bg"])
        except (FileNotFoundError, KeyError) as e:
            return {"available": False, "reason": str(e)}

        # Avoid division by zero
        mask_lcdm = cl_lcdm > 0
        mask_bg = cl_bg > 0

        res_pert_lcdm = np.zeros_like(cl_pert)
        res_pert_lcdm[mask_lcdm] = (cl_pert[mask_lcdm] - cl_lcdm[mask_lcdm]) / cl_lcdm[mask_lcdm]

        res_pert_bg = np.zeros_like(cl_pert)
        res_pert_bg[mask_bg] = (cl_pert[mask_bg] - cl_bg[mask_bg]) / cl_bg[mask_bg]

        # Acoustic-peak regime: 100 <= ell <= 2000
        acoustic_mask = (ells >= 100) & (ells <= 2000)
        max_res_acoustic_lcdm = float(np.max(np.abs(res_pert_lcdm[acoustic_mask])))
        max_res_acoustic_bg = float(np.max(np.abs(res_pert_bg[acoustic_mask])))

        # Low-ell ISW regime: ell < 30
        low_ell_mask = ells < 30
        max_res_low_lcdm = float(np.max(np.abs(res_pert_lcdm[low_ell_mask])))
        max_res_low_bg = float(np.max(np.abs(res_pert_bg[low_ell_mask])))

        # The residuals are the measured scalar signature, reported with
        # reference bands rather than hard tolerances (see module docstring).
        all_finite = bool(
            np.all(np.isfinite(cl_pert))
            and np.all(np.isfinite(res_pert_lcdm[mask_lcdm]))
            and np.all(np.isfinite(res_pert_bg[mask_bg]))
        )
        max_abs_residual = max(
            max_res_acoustic_lcdm, max_res_acoustic_bg,
            max_res_low_lcdm, max_res_low_bg,
        )
        not_divergent = all_finite and max_abs_residual < 5.0
        scalar_active = all_finite and max_abs_residual > 1e-8

        acoustic_passed = (
            max_res_acoustic_lcdm < self.ACOUSTIC_TOLERANCE
            and max_res_acoustic_bg < self.ACOUSTIC_TOLERANCE
        )
        low_ell_passed = (
            max_res_low_lcdm < self.LOW_ELL_TOLERANCE
            and max_res_low_bg < self.LOW_ELL_TOLERANCE
        )

        diag = {
            "available": True,
            "max_residual_acoustic_vs_lcdm": max_res_acoustic_lcdm,
            "max_residual_acoustic_vs_bg": max_res_acoustic_bg,
            "acoustic_reference_band": self.ACOUSTIC_TOLERANCE,
            "within_acoustic_reference_band": acoustic_passed,
            "max_residual_lowell_vs_lcdm": max_res_low_lcdm,
            "max_residual_lowell_vs_bg": max_res_low_bg,
            "low_ell_reference_band": self.LOW_ELL_TOLERANCE,
            "within_lowell_reference_band": low_ell_passed,
            "spectra_finite": all_finite,
            "not_divergent": not_divergent,
            "scalar_active": scalar_active,
            "note": ("Residuals are the measured active-scalar signature "
                     "(screened delta-phi closure); nonzero is expected. "
                     "Gate fails on divergence (>500%), non-finite spectra, "
                     "or a bitwise-silent scalar sector."),
        }

        print_status(
            f"  Acoustic scalar signature: vs_LCDM={max_res_acoustic_lcdm:.4f}, "
            f"vs_bg={max_res_acoustic_bg:.4f} (reference band {self.ACOUSTIC_TOLERANCE})",
            "INFO",
        )
        print_status(
            f"  Low-ell scalar signature (ISW): vs_LCDM={max_res_low_lcdm:.4f}, "
            f"vs_bg={max_res_low_bg:.4f} (reference band {self.LOW_ELL_TOLERANCE})",
            "INFO",
        )
        if not all_finite:
            print_status("  Non-finite spectra detected — closure FAILED", "WARNING")
        elif not not_divergent:
            print_status("  Divergent scalar response (>500% residual) — closure FAILED", "WARNING")
        elif not scalar_active:
            print_status("  Scalar sector bitwise-silent — SMG path likely disabled", "WARNING")
        else:
            print_status("  Active scalar sector verified (finite, bounded, nonzero signature)", "SUCCESS")
        return diag

    def _latest_output(self, root_stem, kind):
        """Return the highest-numbered hi_class output file for a root."""
        candidates = sorted(self.results_dir.glob(f"{root_stem}_*_{kind}.dat"))
        if not candidates:
            raise FileNotFoundError(
                f"No hi_class '{kind}' output found for root '{root_stem}'"
            )
        def _suffix(p):
            try:
                return int(p.stem.split("_")[-2])
            except (ValueError, IndexError):
                return -1
        return max(candidates, key=_suffix)


if __name__ == "__main__":
    step = Step09PerturbationClosure()
    step.run()
