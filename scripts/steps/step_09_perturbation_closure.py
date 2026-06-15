#!/usr/bin/env python3
"""
Step 09: Perturbation Closure Verification
============================================
Validates that the SMG-TEP perturbation run produces the same background
Hubble rate as the native tep_mode background-only run to machine precision.
Also compares TT spectra between background-only and active-perturbation TEP.

This is the critical consistency gate: H_SMG(a) must equal H_tep_mode(a)
to < 1e-6 relative precision at all scale factors.
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

            # 3. Overall pass/fail
            results["closure_passed"] = (
                bg_check["passed"] and spec_check["acoustic_passed"]
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
            "acoustic_tolerance": self.ACOUSTIC_TOLERANCE,
            "acoustic_passed": acoustic_passed,
            "max_residual_lowell_vs_lcdm": max_res_low_lcdm,
            "max_residual_lowell_vs_bg": max_res_low_bg,
            "low_ell_tolerance": self.LOW_ELL_TOLERANCE,
            "low_ell_passed": low_ell_passed,
        }

        print_status(
            f"  Acoustic residuals: vs_LCDM={max_res_acoustic_lcdm:.4f}, "
            f"vs_bg={max_res_acoustic_bg:.4f} (tol={self.ACOUSTIC_TOLERANCE})",
            "SUCCESS" if acoustic_passed else "WARNING",
        )
        print_status(
            f"  Low-ell residuals: vs_LCDM={max_res_low_lcdm:.4f}, "
            f"vs_bg={max_res_low_bg:.4f} (tol={self.LOW_ELL_TOLERANCE})",
            "SUCCESS" if low_ell_passed else "WARNING",
        )
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
