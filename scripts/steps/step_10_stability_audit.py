#!/usr/bin/env python3
"""
Step 10: Stability Audit
========================
Evaluates the exact stability discriminants across the full redshift range.
Demonstrates that the TEP scalar perturbation sector is ghost-free and
gradient-stable with no pathological growth in the late-universe unscreened regime.

Audits:
  - No-ghost discriminant D(z) = alpha_K + (3/2) alpha_B^2 = +alpha_A^2 > 0
  - Sound speed c_s^2(z) = 1 exactly (conformal isomorphism)
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

            # 1. No-ghost check: D(z) = alpha_A^2 must be strictly positive
            D = eft["D"]
            D_min = float(np.min(D))
            ghost_free = D_min > 0

            # 2. Gradient stability: c_s^2 = 1 exactly
            cs2 = eft["c_s2"]
            gradient_free = np.all(cs2 > 0)

            # 3. Planck-mass running boundedness
            alpha_M = eft["alpha_M"]
            alpha_M_max = float(np.max(np.abs(alpha_M)))
            alpha_M_bounded = alpha_M_max < 10.0  # conservative

            # 4. Transition-regime smoothness
            # Compute dalpha_M/dz and check for jumps near z_T
            dalpha_M_dz = np.gradient(alpha_M, z)
            # Normalize by |alpha_M| to get relative jump; avoid division by zero
            rel_jump = np.zeros_like(dalpha_M_dz)
            nonzero = np.abs(alpha_M) > 1e-12
            rel_jump[nonzero] = np.abs(dalpha_M_dz[nonzero]) / np.abs(alpha_M[nonzero])

            # Focus on the transition regime around z_T
            transition_mask = (z >= 0.5 * z_T) & (z <= 2.0 * z_T)
            max_jump_transition = float(np.max(rel_jump[transition_mask])) if np.any(transition_mask) else 0.0
            transition_smooth = max_jump_transition < self.DERIVATIVE_JUMP_TOLERANCE

            results["parameters"] = {"epsilon_T": epsilon_T, "z_T": z_T, "n_T": n_T}
            results["redshift_range"] = {"z_min": float(z[0]), "z_max": float(z[-1]), "n_points": len(z)}
            results["ghost_free"] = {"passed": ghost_free, "D_min": D_min}
            results["gradient_free"] = {"passed": gradient_free, "cs2_min": float(np.min(cs2))}
            results["alpha_M_bounded"] = {"passed": alpha_M_bounded, "max_abs_alpha_M": alpha_M_max}
            results["transition_smoothness"] = {
                "passed": transition_smooth,
                "max_relative_jump": max_jump_transition,
                "tolerance": self.DERIVATIVE_JUMP_TOLERANCE,
                "transition_regime": f"{0.5*z_T} <= z <= {2.0*z_T}"
            }
            results["ghost_free_identity"] = bool(np.allclose(D, alpha_A**2, atol=1e-14))

            # Overall pass/fail
            all_passed = ghost_free and gradient_free and alpha_M_bounded and transition_smooth
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
