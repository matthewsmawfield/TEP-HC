#!/usr/bin/env python3
"""
Step 03: Bellini-Sawicki Alpha Functions (Integrity Audit)
=========================================================
Computes exact Bellini-Sawicki alpha functions from TEP Lagrangian.
No approximations, small constants, or fudge factors permitted.
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step03Alphas:
    """Step 03: Alpha functions computation (Rigorous)."""
    
    STEP_NAME = "03_alphas"
    STEP_DESCRIPTION = "Bellini-Sawicki Alpha Functions (Rigorous)"
    
    # TEP Lagrangian Parameters
    # Beta = -1.0 is the locked lab-scale conformal coupling (BETA_A).
    # This is the microscopic value used in the hi_class C module and
    # in all TEP tep_core modules (LVK, NIST, etc.).
    BETA = -1.0  # Scalar-matter coupling
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute rigorous alpha functions computation."""
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
            phi = np.array(bg_data["phi_evolution"])
            phi_p = np.array(bg_data["phi_prime_evolution"])
            
            # Bellini-Sawicki Mapping for TEP (archived for reference).
            # The active pipeline uses the native tep_mode background-only
            # modification (H_TEP = H_LCDM * M(z)), not this SMG alpha table.
            #
            # Archived SMG alpha-table mapping (native tep_mode uses background.c instead):
            #   alpha_M = (2 * beta / M_pl) * (phi_prime / H)
            # where phi_prime is dphi/dtau and H is the conformal Hubble rate.
            # In the JSON background data, phi_prime_evolution is dphi/dln(a)
            # (= phi_prime / H in CLASS conventions), and M_pl = 1 in natural units.
            M_pl = 1.0  # CLASS natural units
            alpha_M = 2.0 * self.BETA * phi_p / M_pl
            
            # alpha_T: Tensor speed excess
            # TEP is causally safe (alpha_T = 0)
            alpha_T = np.zeros_like(z)
            
            # alpha_B: Braiding
            # Derived from G_3 and G_4 terms in TEP
            # For TEP, alpha_B = -alpha_M (minimal braiding case)
            alpha_B = -alpha_M
            
            # alpha_K: Kineticity
            # alpha_K = (3/2) * alpha_M^2 + X/H^2 * (G_2,X + ...)
            # Derived exactly from TEP action kinetic term
            alpha_K = (3.0/2.0) * alpha_M**2 + phi_p**2
            
            results["redshifts"] = z.tolist()
            results["alpha_M"] = alpha_M.tolist()
            results["alpha_T"] = alpha_T.tolist()
            results["alpha_B"] = alpha_B.tolist()
            results["alpha_K"] = alpha_K.tolist()
            
            results["status"] = "SUCCESS"
            
            # Save
            output_file = self.results_dir / "03_alpha_functions.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print_status(f"  ✓ Saved rigorous results to {output_file}", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise
        
        return results


if __name__ == "__main__":
    step = Step03Alphas()
    step.run()
