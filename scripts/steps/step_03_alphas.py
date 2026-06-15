#!/usr/bin/env python3
"""
Step 03: Bellini-Sawicki Alpha Functions (Integrity Audit)
=========================================================
Computes exact Bellini-Sawicki alpha functions from the TEP conformal factor.
All alphas derive from the single dimensionless quantity alpha_A(z) using
the analytical EFT closure.  No approximations or fudge factors permitted.
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


class Step03Alphas:
    """Step 03: Alpha functions computation (Exact EFT closure)."""

    STEP_NAME = "03_alphas"
    STEP_DESCRIPTION = "Bellini-Sawicki Alpha Functions (Exact EFT Closure)"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Execute exact alpha functions computation from alpha_A(z)."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }

        try:
            bg_file = self.results_dir / "02_background_evolution.json"
            with open(bg_file) as f:
                bg_data = json.load(f)

            z = np.array(bg_data["redshifts"])
            epsilon_T = bg_data.get("epsilon_T", 0.0066)
            z_T = bg_data.get("z_T", 5.0)
            n_T = bg_data.get("n_T", 2.0)

            # Exact native TEP conformal-factor derivative
            alpha_A = alpha_A_native(z, epsilon_T, z_T, n_T)

            # Exact Bellini-Sawicki parameters and stability discriminants
            eft = evaluate_tep_eft_sector(alpha_A)

            results["redshifts"] = z.tolist()
            results["epsilon_T"] = epsilon_T
            results["z_T"] = z_T
            results["n_T"] = n_T
            results["alpha_A"] = np.atleast_1d(alpha_A).tolist()
            results["alpha_M"] = np.atleast_1d(eft["alpha_M"]).tolist()
            results["alpha_B"] = np.atleast_1d(eft["alpha_B"]).tolist()
            results["alpha_K"] = np.atleast_1d(eft["alpha_K"]).tolist()
            results["alpha_T"] = np.atleast_1d(eft["alpha_T"]).tolist()
            results["D"] = np.atleast_1d(eft["D"]).tolist()
            results["c_s2"] = np.atleast_1d(eft["c_s2"]).tolist()
            results["is_stable"] = bool(eft["is_stable"])

            # Cross-check: D must equal alpha_A^2 to numerical precision
            D_min = float(np.min(eft["D"]))
            alpha_A_max = float(np.max(np.abs(alpha_A)))
            results["D_min"] = D_min
            results["alpha_A_max"] = alpha_A_max
            results["ghost_free_identity"] = bool(np.allclose(eft["D"], alpha_A**2, atol=1e-14))

            results["status"] = "SUCCESS"

            # Save
            output_file = self.results_dir / "03_alpha_functions.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            print_status(f"  ✓ Saved exact EFT closure results to {output_file}", "SUCCESS")

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise

        return results


if __name__ == "__main__":
    step = Step03Alphas()
    step.run()
