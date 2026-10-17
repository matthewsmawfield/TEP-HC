#!/usr/bin/env python3
"""
Step 10: Stability Audit
========================
Evaluates the exact stability discriminants across the full redshift range
for the corrected delta-phi closure (alpha_K = wc alpha_A^2; production
wc = +700 = Z_E - 6 for tep_kin_boost = 10, with wc = +7 retained as the
minimal-stable diagnostic; production S_Sigma = 1).

Audits:
  - No-ghost discriminant D(z) = alpha_K + (3/2) alpha_B^2
        = (wc + 6 S^2) alpha_A^2 > 0
  - Kinetic-coefficient sign wc > 0: the operative linear-stability
    criterion. D > 0 alone is NOT sufficient — the canonical-EF branch
    wc = -5 has D = alpha_A^2 > 0 yet is linearly unstable
    (tachyonic/scalarization channel, median P(k) enhancement ~1e8;
    see results/closure_response_scan.json).
  - Sound speed c_s^2(z) = 1 (asserted by conformal isomorphism; the
    hi_class build overrides the generic cs2 reconstruction for tep)
  - Planck-mass running |alpha_M(z)| bounded
  - Transition-regime smoothness: no discontinuous jumps in alpha_M'(z)
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from core.cosmology import alpha_A_native, evaluate_tep_eft_sector
from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step10StabilityAudit:
    """Step 10: Scalar-sector stability audit (Exact EFT closure)."""

    STEP_NAME = "10_stability_audit"
    STEP_DESCRIPTION = "Scalar Perturbation Stability Audit"

    # Tolerance for discontinuity detection in alpha_M derivative
    DERIVATIVE_JUMP_TOLERANCE = 1.0  # relative jump in dalpha_M/dz

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Execute rigorous stability audit."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }

        try:
            # Fiducial TEP parameters (must match step_04_cmb.py)
            epsilon_T = 0.0066
            z_T = 5.0
            n_T = 2.0

            # Fine redshift grid for stability evaluation
            z = np.linspace(0.0, 2000.0, 5000)

            # Exact conformal-factor derivative
            alpha_A = alpha_A_native(z, epsilon_T, z_T, n_T)

            # Exact EFT sector
            eft = evaluate_tep_eft_sector(alpha_A)

            # 1. No-ghost check: D(z) = (wc + 6 S^2) alpha_A^2 >= 0 (no
            # ghosts). D = 0 at z = 0 (local reference frame), at the
            # turnover z* ~ 2.65, and at high z where the suppression
            # underflows — all documented scalar-decoupling limits.
            D = eft["D"]
            D_min = float(np.min(D[z > 0]))
            ghost_free = D_min > -1e-300

            # 2. Gradient stability: c_s^2 = 1 exactly
            cs2 = eft["c_s2"]
            gradient_free = bool(np.all(cs2 > 0))

            # 3. Planck-mass running boundedness
            alpha_M = eft["alpha_M"]
            alpha_M_max = float(np.max(np.abs(alpha_M)))
            alpha_M_bounded = alpha_M_max < 10.0  # conservative

            # 4. Transition-regime smoothness
            # Compute dalpha_M/dz and check for jumps near z_T
            dalpha_M_dz = np.gradient(alpha_M, z)

            # Focus on the transition regime around z_T. Normalize by the
            # characteristic transition amplitude rather than |alpha_M|(z):
            # alpha_M -> 0 at the documented turnover z* ~ 2.65 (scalar
            # decoupling point), where pointwise normalization is ill-posed.
            transition_mask = (z >= 0.5 * z_T) & (z <= 2.0 * z_T)
            transition_scale = float(np.max(np.abs(alpha_M[transition_mask]))) if np.any(transition_mask) else 0.0
            max_jump_transition = (
                float(np.max(np.abs(dalpha_M_dz[transition_mask])) / transition_scale)
                if transition_scale > 0 else 0.0
            )
            transition_smooth = max_jump_transition < self.DERIVATIVE_JUMP_TOLERANCE

            results["parameters"] = {"epsilon_T": epsilon_T, "z_T": z_T, "n_T": n_T}
            results["redshift_range"] = {"z_min": float(z[0]), "z_max": float(z[-1]), "n_points": len(z)}
            results["ghost_free"] = {"passed": ghost_free, "D_min": D_min}
            results["gradient_free"] = {"passed": gradient_free, "cs2_min": float(np.min(cs2))}
            results["alpha_M_bounded"] = {"passed": alpha_M_bounded, "max_abs_alpha_M": alpha_M_max}
            results["transition_smoothness"] = {
                "passed": transition_smooth,
                "max_relative_jump": max_jump_transition,
                "normalization": "transition-window max|alpha_M|",
                "tolerance": self.DERIVATIVE_JUMP_TOLERANCE,
                "transition_regime": f"{0.5*z_T} <= z <= {2.0*z_T}"
            }
            results["ghost_free_identity"] = bool(
                np.allclose(D, (eft["wc"] + 6.0 * eft["screening_s"] ** 2) * alpha_A**2, atol=1e-14))
            results["wc"] = eft["wc"]
            results["screening_s"] = eft["screening_s"]
            # Operative linear-stability criterion: positive Jordan
            # kinetic coefficient. wc = -5 (canonical EF image) passes
            # D > 0 but carries a runaway tachyonic mode.
            results["kinetic_stable"] = bool(eft["wc"] > 0)

            # Overall pass/fail
            all_passed = (ghost_free and gradient_free and alpha_M_bounded
                          and transition_smooth and results["kinetic_stable"])
            results["all_passed"] = all_passed

            # Store sampled discriminants for plotting
            sample_idx = np.linspace(0, len(z) - 1, 200, dtype=int)
            results["sampled_z"] = z[sample_idx].tolist()
            results["sampled_alpha_A"] = alpha_A[sample_idx].tolist()
            results["sampled_alpha_M"] = alpha_M[sample_idx].tolist()
            results["sampled_alpha_B"] = eft["alpha_B"][sample_idx].tolist()
            results["sampled_alpha_K"] = eft["alpha_K"][sample_idx].tolist()
            results["sampled_D"] = D[sample_idx].tolist()
            results["sampled_cs2"] = cs2[sample_idx].tolist()

            results["status"] = "SUCCESS" if all_passed else "WARNING"

            output_file = self.results_dir / "10_stability_audit.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            print_status(f"  ✓ Saved stability audit to {output_file}", "SUCCESS")
            if all_passed:
                print_status("  All stability checks PASSED", "SUCCESS")
            else:
                print_status("  Some stability checks FAILED", "WARNING")

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise

        return results


if __name__ == "__main__":
    step = Step10StabilityAudit()
    step.run()
