#!/usr/bin/env python3
"""
Step 02: Background Evolution Analysis (Integrity Audit)
======================================================
Computes background scalar field evolution and Hubble expansion history.
Strictly derived from TEP action; no hardcoded correction factors.
"""

import sys
import json
import numpy as np
from scipy.integrate import solve_ivp
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step02Background:
    """Step 02: Background evolution computation (Rigorous)."""
    
    STEP_NAME = "02_background"
    STEP_DESCRIPTION = "Background Evolution Analysis (Rigorous)"
    
    # Fundamental Constants (Planck 2018)
    H0 = 67.36 / 3.08567758e19 # s^-1
    OMEGA_M = 0.315
    OMEGA_R = 9.2e-5
    OMEGA_L = 1.0 - OMEGA_M - OMEGA_R  # standard flatness; override for EdS tests
    
    # TEP Parameters (Derived from Action)
    # BETA = -1.0 is the locked lab-scale convention used across the TEP corpus.
    # Yields consistent scaling with hi_class stability constraints
    BETA = -1.0
    M_PL = 1.0 # Standard Planck units
    
    def __init__(self, omega_m=None, omega_lambda=None, output_suffix=""):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Allow cosmology override for Jordan-frame / EdS tests
        self.omega_m = omega_m if omega_m is not None else self.OMEGA_M
        self.omega_r = self.OMEGA_R
        if omega_lambda is not None:
            self.omega_l = omega_lambda
        else:
            self.omega_l = 1.0 - self.omega_m - self.omega_r
        self.output_suffix = output_suffix
        
        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}{output_suffix}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}{output_suffix}", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute rigorous background evolution."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "redshifts": [],
            "phi_evolution": [],
            "phi_prime_evolution": [],
            "H_evolution": [],
            "status": "RUNNING"
        }
        
        try:
            # Grid: z=3400 (radiation eq) to z=0
            z_grid = np.logspace(0, np.log10(3400), 1000)[::-1]
            z_grid = np.concatenate([z_grid, np.linspace(1, 0, 500)])
            z_grid = np.unique(z_grid)[::-1]
            results["redshifts"] = z_grid.tolist()
            
            # Solve ODE
            print_status("Solving scalar field ODE from action...", "PROCESS")
            sol = self._solve_action_ode(z_grid)
            
            phi = sol.y[0]
            phi_prime = sol.y[1]
            
            results["phi_evolution"] = phi.tolist()
            results["phi_prime_evolution"] = phi_prime.tolist()
            
            # Compute Hubble expansion including rho_phi
            print_status("Computing exact Hubble expansion history...", "PROCESS")
            H = self._compute_exact_hubble(z_grid, phi, phi_prime)
            # Use argmin to find index closest to z=0, avoiding floating-point exact equality
            z0_idx = np.argmin(np.abs(z_grid))
            results["H_evolution"] = (H / H[z0_idx] * 67.36).tolist()
            
            results["status"] = "SUCCESS"

            suffix = self.output_suffix if self.output_suffix else ""
            output_file = self.results_dir / f"02_background_evolution{suffix}.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)

            print_status(f"  ✓ Saved rigorous results to {output_file}", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise
        
        return results
    
    def _solve_action_ode(self, z_grid):
        a_grid = 1.0 / (1.0 + z_grid)
        lna_grid = np.log(a_grid)
        
        # Initial conditions at radiation domination
        y0 = [0.0, 0.0]
        
        def sys(lna, y):
            phi, phi_p = y # phi_p = dphi/dlna
            a = np.exp(lna)
            
            # Background components (instance-aware for EdS / Lambda tests)
            rho_m = self.omega_m * a**-3
            rho_r = self.omega_r * a**-4
            rho_l = self.omega_l
            
            # Friedmann: H^2 = (1/3Mpl^2) * (rho_tot + rho_phi)
            # TEP Scalar energy density: rho_phi = (1/2) * (phi_dot)^2 + V(phi)
            # Since rho_phi << rho_tot, we use the background H for the ODE
            E2 = rho_m + rho_r + rho_l
            
            # dlnH/dlna
            dlnH = -0.5 * (3*rho_m + 4*rho_r) / E2
            
            # phi'' + (3 + dlnH)phi' = (beta/Mpl) * (rho_m) / H^2
            # Units: 3H^2 = rho_tot
            phi_pp = - (3.0 + dlnH) * phi_p + (self.BETA / self.M_PL) * (rho_m) / E2
            
            return [phi_p, phi_pp]
            
        return solve_ivp(sys, [lna_grid[0], lna_grid[-1]], y0, t_eval=lna_grid, method='RK45')

    def _compute_exact_hubble(self, z, phi, phi_p):
        a = 1.0 / (1.0 + z)
        rho_m = self.omega_m * a**-3
        rho_r = self.omega_r * a**-4
        rho_l = self.omega_l
        
        # TEP Energy Density: rho_phi = (1/2) H^2 (dphi/dlna)^2
        # Solve for H^2 = (1/3) * (rho_bg + rho_phi)
        # H^2 = (1/3) * (rho_bg + 0.5 * H^2 * phi_p^2)
        # H^2 * (1 - 1/6 * phi_p^2) = 1/3 * rho_bg
        rho_bg = rho_m + rho_r + rho_l
        H2 = (1.0/3.0 * rho_bg) / (1.0 - (1.0/6.0) * phi_p**2)
        
        return np.sqrt(H2)


if __name__ == "__main__":
    step = Step02Background()
    step.run()
