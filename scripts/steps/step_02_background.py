#!/usr/bin/env python3
"""
Step 02: Background Evolution Analysis
======================================
Computes background scalar field evolution and Hubble expansion history.

Outputs:
    - logs/step_02_background.log
    - results/background_evolution.csv
    - results/figures/background_phi_evolution.png
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step02Background:
    """Step 02: Background evolution computation."""
    
    STEP_NAME = "02_background"
    STEP_DESCRIPTION = "Background Evolution Analysis"
    
    # Cosmological parameters (Planck 2018 baseline)
    H0_DEFAULT = 67.36  # km/s/Mpc
    OMEGA_M_DEFAULT = 0.315
    OMEGA_B_DEFAULT = 0.0493
    OMEGA_CDM_DEFAULT = 0.265
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.results_dir = self.root_dir / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.figures_dir = self.results_dir / "figures"
        self.figures_dir.mkdir(exist_ok=True)
        
        log_file = self.log_dir / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute background evolution step."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status(f"Started at: {datetime.now().isoformat()}", "INFO")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "redshifts": [],
            "phi_evolution": [],
            "H_evolution": [],
            "screening_status": [],
            "status": "RUNNING"
        }
        
        try:
            # Define redshift grid (z=1100 to z=0)
            print_status("Setting up redshift grid...", "PROCESS")
            z_grid = np.logspace(-4, np.log10(1100), 1000)[::-1]  # High to low
            results["redshifts"] = z_grid.tolist()
            
            # Compute cosmological densities
            print_status("Computing background densities...", "PROCESS")
            rho_crit = self._critical_density(z_grid)
            
            # Screening threshold: 20 g/cm^3 = 4.6e37 kg/m^3
            rho_screen = 4.6e37  # kg/m^3
            
            # At z=1100: rho ~ 1e-113 Planck units, way below screening
            print_status(f"  Density at z=1100: {rho_crit[0]:.2e} kg/m^3", "INFO")
            print_status(f"  Screening threshold: {rho_screen:.2e} kg/m^3", "INFO")
            print_status(f"  Ratio: {rho_crit[0]/rho_screen:.2e} (fully unscreened)", "SUCCESS")
            
            # Compute scalar field evolution
            print_status("Computing scalar field evolution...", "PROCESS")
            phi_evolution = self._compute_phi_evolution(z_grid)
            results["phi_evolution"] = phi_evolution.tolist()
            
            # Compute modified Hubble expansion
            print_status("Computing Hubble expansion...", "PROCESS")
            H_evolution = self._compute_Hubble(z_grid, phi_evolution)
            results["H_evolution"] = H_evolution.tolist()
            
            # Determine screening status at each redshift
            print_status("Determining screening status...", "PROCESS")
            screening = ["UNSCREENED" if r < rho_screen else "SCREENED" for r in rho_crit]
            results["screening_status"] = screening
            
            # Key finding: CMB epoch is unscreened
            z_cmb = 1089
            idx_cmb = np.argmin(np.abs(z_grid - z_cmb))
            print_status(f"\nCMB Epoch (z={z_cmb}):", "TITLE")
            print_status(f"  Screening status: {screening[idx_cmb]}", "INFO")
            print_status(f"  phi/phi_init: {phi_evolution[idx_cmb]:.4f}", "INFO")
            print_status(f"  H(z)/H_LambdaCDM: {H_evolution[idx_cmb]/self._H_lcdm(z_cmb):.6f}", "INFO")
            
            # Save results
            print_status("Saving results...", "PROCESS")
            output_file = self.results_dir / "background_evolution.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print_status(f"  ✓ Saved {output_file}", "SUCCESS")
            
            # Summary statistics
            print_status("\nBackground Evolution Summary:", "TITLE")
            print_status(f"  Max |phi deviation|: {np.max(np.abs(phi_evolution)):.4f}", "INFO")
            print_status(f"  Max |Delta H/H|: {np.max(np.abs(H_evolution/self._H_lcdm(z_grid) - 1)):.6f}", "INFO")
            print_status(f"  Screening transitions: {screening.count('SCREENED')} / {len(screening)}", "INFO")
            
            results["status"] = "SUCCESS"
            print_status(f"STEP {self.STEP_NAME} COMPLETED", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results
    
    def _critical_density(self, z: np.ndarray) -> np.ndarray:
        """Compute critical density as function of redshift (kg/m^3)."""
        # rho_crit(z) = rho_crit_0 * E^2(z)
        # E^2(z) = Omega_m * (1+z)^3 + Omega_r * (1+z)^4 + Omega_L
        H0_si = self.H0_DEFAULT * 1000 / (3.086e19)  # Convert to s^-1
        rho_crit_0 = 3.0 * H0_si**2 / (8.0 * np.pi * 6.674e-11)  # kg/m^3
        
        Omega_r = 9.2e-5  # Radiation density
        Omega_L = 1.0 - self.OMEGA_M_DEFAULT - Omega_r
        
        E_squared = (self.OMEGA_M_DEFAULT * (1+z)**3 + 
                    Omega_r * (1+z)**4 + 
                    Omega_L)
        
        return rho_crit_0 * E_squared
    
    def _H_lcdm(self, z: np.ndarray) -> np.ndarray:
        """Compute LambdaCDM Hubble parameter (km/s/Mpc)."""
        Omega_r = 9.2e-5
        Omega_L = 1.0 - self.OMEGA_M_DEFAULT - Omega_r
        
        E_squared = (self.OMEGA_M_DEFAULT * (1+z)**3 + 
                    Omega_r * (1+z)**4 + 
                    Omega_L)
        
        return self.H0_DEFAULT * np.sqrt(E_squared)
    
    def _compute_phi_evolution(self, z: np.ndarray) -> np.ndarray:
        """
        Compute scalar field evolution.
        
        During radiation domination: T^mu_mu ~ 0, phi frozen
        During matter domination: phi evolves with T^mu_mu ~ -rho_m
        """
        # Simplified evolution: phi tracks matter density
        # In full implementation, this solves the ODE from tep.c
        
        phi = np.zeros_like(z)
        
        # Matter-radiation equality at z ~ 3400
        z_eq = 3400
        
        for i, zi in enumerate(z):
            if zi > z_eq:
                # Radiation domination: phi frozen
                phi[i] = 1.0
            else:
                # Matter domination: mild evolution
                # phi ~ log(rho_matter) with saturation
                a = 1.0 / (1.0 + zi)
                phi[i] = 1.0 + 0.1 * np.log(a / (1.0/(1.0 + z_eq)))
        
        return phi
    
    def _compute_Hubble(self, z: np.ndarray, phi: np.ndarray) -> np.ndarray:
        """Compute modified Hubble parameter including scalar field effects."""
        H_lcdm = self._H_lcdm(z)
        
        # Small correction from scalar field energy density
        # At early times (z > 100): correction is negligible
        correction = 1.0 + 1e-6 * (phi - 1.0)
        
        return H_lcdm * correction


if __name__ == "__main__":
    step = Step02Background()
    step.run()
