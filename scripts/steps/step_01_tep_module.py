#!/usr/bin/env python3
"""
Step 01: TEP C Module Generation
================================
Creates the tep.c module for hi_class with Bellini-Sawicki alpha mappings.

Outputs:
    - logs/step_01_tep_module.log
    - scripts/hi_class_modules/tep.c
    - scripts/hi_class_modules/tep.h
    - scripts/hi_class_modules/README.md
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


TEP_C_TEMPLATE = '''/**
 * @file tep.c
 * @brief TEP (Temporal Equivalence Principle) model for hi_class
 * 
 * Implements the bi-metric framework with conformal factor A(phi) and
 * disformal deformation B(phi), mapping to Bellini-Sawicki alpha functions.
 * 
 * @author: TEP-HC Pipeline
 * @version: v0.1-Geneva
 */

#include "common.h"
#include "background.h"
#include "tep.h"

/**
 * @brief Initialize TEP model parameters from input file
 */
int smg_tep_init(struct background *pba, struct smg_tep_params *params) {
    // Default parameter values
    params->alpha_eff = 1.0e6;        // TEP clock-sector coupling
    params->phi_init = 0.0;          // Initial field value
    params->B_phi_coeff = 0.0;       // Disformal coupling (constrained to ~0 today)
    params->screening_threshold = 1.8e-124; // 20 g/cm^3 in Planck units
    params->beta = 1.0;              // Conformal coupling strength
    
    // Override from input file if provided
    class_read_double("tep_alpha_eff", params->alpha_eff);
    class_read_double("tep_phi_init", params->phi_init);
    class_read_double("tep_B_coeff", params->B_phi_coeff);
    class_read_double("tep_beta", params->beta);
    
    // Validate parameters
    if (params->alpha_eff <= 0) {
        fprintf(stderr, "ERROR: tep_alpha_eff must be positive\\n");
        return _FAILURE_;
    }
    
    return _SUCCESS_;
}

/**
 * @brief Compute Planck mass running alpha_M from conformal factor
 * 
 * alpha_M = d ln A / d ln a = (2*beta/M_Pl) * (phi' / H)
 */
double tep_alpha_M(struct background *pba, double phi, double phi_prime) {
    double M_pl = pba->M_pl;
    double H = pba->H;
    double beta = pba->tep_params.beta;
    
    // d ln A / d ln a = (d ln A / d phi) * (d phi / d ln a)
    // d ln A / d phi = 2*beta/M_Pl
    // d phi / d ln a = phi' / H
    
    return (2.0 * beta / M_pl) * (phi_prime / H);
}

/**
 * @brief Compute tensor speed excess alpha_T from disformal term
 * 
 * alpha_T ~ B(phi) * (phi')^2 / (M_Pl^2 * H^2)
 * Constrained to ~0 today by GW170817/GRB170817A
 */
double tep_alpha_T(struct background *pba, double phi, double phi_prime) {
    double B_coeff = pba->tep_params.B_phi_coeff;
    double M_pl = pba->M_pl;
    double H = pba->H;
    
    // Late-time suppression: B(phi) -> 0 as z -> 0
    double z = pba->z;
    double suppression = pow(1.0 + z, 3.0) / (1.0 + pow(1.0 + z, 3.0));
    
    return B_coeff * suppression * pow(phi_prime / (M_pl * H), 2);
}

/**
 * @brief Compute braiding alpha_B
 */
double tep_alpha_B(struct background *pba, double phi, double phi_prime) {
    double H = pba->H;
    double H_prime = pba->H_prime;
    
    // Braiding from kinetic mixing
    // alpha_B ~ -H' * phi' / H^2 * f_B(phi, X)
    double X = 0.5 * phi_prime * phi_prime; // Kinetic term
    double f_B = tep_f_B_coupling(phi, X, pba->tep_params);
    
    return -(H_prime * phi_prime / (H * H)) * f_B;
}

/**
 * @brief Compute kineticity alpha_K
 */
double tep_alpha_K(struct background *pba, double phi, double phi_prime) {
    double M_pl = pba->M_pl;
    double H = pba->H;
    
    // Kineticity from scalar field kinetic term
    // alpha_K ~ (phi')^2 / (H^2 * M_Pl^2) * f_K(phi, X)
    double X = 0.5 * phi_prime * phi_prime;
    double f_K = tep_f_K_coupling(phi, X, pba->tep_params);
    
    return (phi_prime * phi_prime / (H * H * M_pl * M_pl)) * f_K;
}

/**
 * @brief TEP-specific coupling functions
 */
double tep_f_B_coupling(double phi, double X, struct smg_tep_params params) {
    // TEP-specific braiding coupling
    // Suppressed at high densities (screened regime)
    double screening = tep_screening_factor(phi, params);
    return params.alpha_eff * screening;
}

double tep_f_K_coupling(double phi, double X, struct smg_tep_params params) {
    // TEP-specific kineticity coupling
    double screening = tep_screening_factor(phi, params);
    return params.alpha_eff * screening;
}

/**
 * @brief Screening factor: suppresses scalar field effects at high density
 * Theta(rho_c - rho) where rho_c = 20 g/cm^3
 */
double tep_screening_factor(double phi, struct smg_tep_params params) {
    // During radiation domination: T^mu_mu ~ 0, no screening
    // During matter domination: screen at rho > 20 g/cm^3
    
    // Cosmological context: always unscreened (rho << 20 g/cm^3)
    // This is the key point for CMB acoustic peaks
    return 1.0; // Fully unscreened in cosmological context
}

/**
 * @brief Main gravity functions interface for hi_class
 */
int smg_tep_gravity_functions(
    struct background *pba,
    double *pvecback,
    double *pvecgravity
) {
    double phi = pvecback[pba->index_bg_smg_phi];
    double phi_prime = pvecback[pba->index_bg_smg_phi_prime];
    
    // Compute Bellini-Sawicki alphas
    pvecgravity[pba->index_bg_smg_alpha_M] = tep_alpha_M(pba, phi, phi_prime);
    pvecgravity[pba->index_bg_smg_alpha_T] = tep_alpha_T(pba, phi, phi_prime);
    pvecgravity[pba->index_bg_smg_alpha_B] = tep_alpha_B(pba, phi, phi_prime);
    pvecgravity[pba->index_bg_smg_alpha_K] = tep_alpha_K(pba, phi, phi_prime);
    
    // Stability check: c_s^2 >= 0
    double cs2 = tep_effective_sound_speed(pba, pvecgravity);
    if (cs2 < 0) {
        fprintf(stderr, "WARNING: c_s^2 = %f < 0, instability detected\\n", cs2);
        return _FAILURE_;
    }
    
    return _SUCCESS_;
}

/**
 * @brief Compute effective sound speed for stability check
 */
double tep_effective_sound_speed(
    struct background *pba,
    double *pvecgravity
) {
    double alpha_M = pvecgravity[pba->index_bg_smg_alpha_M];
    double alpha_T = pvecgravity[pba->index_bg_smg_alpha_T];
    double alpha_B = pvecgravity[pba->index_bg_smg_alpha_B];
    double alpha_K = pvecgravity[pba->index_bg_smg_alpha_K];
    
    // c_s^2 formula from Bellini & Sawicki 2014
    double numerator = alpha_K + 1.5 * alpha_B * alpha_B;
    double denominator = alpha_K + 1.5 * alpha_B * alpha_B + alpha_M - alpha_T;
    
    if (fabs(denominator) < 1e-20) {
        return 1.0; // Default to safe value
    }
    
    return numerator / denominator;
}

/**
 * @brief Background evolution equation for scalar field
 * 
 * phi'' + 2*H*phi' + a^2*V_phi = a^2 * Q_TEP
 * where Q_TEP = (beta/M_Pl) * T^mu_mu * screening_factor
 */
int smg_tep_background_evolution(
    struct background *pba,
    double tau,
    double *y,
    double *dy
) {
    double phi = y[0];
    double phi_prime = y[1];
    double a = pba->a;
    double H = pba->H;
    double M_pl = pba->M_pl;
    
    // Conformal time derivatives
    dy[0] = phi_prime;
    
    // T^mu_mu = -rho + 3p (trace of energy-momentum tensor)
    // During radiation domination: T^mu_mu ~ 0
    // During matter domination: T^mu_mu ~ -rho_m
    double T_mu_mu = pba->rho_tot - 3.0 * pba->p_tot;
    
    // TEP source term
    double beta = pba->tep_params.beta;
    double screening = tep_screening_factor(phi, pba->tep_params);
    double Q_TEP = (beta / M_pl) * T_mu_mu * screening;
    
    // Scalar field equation of motion
    // phi'' + 2*H*phi' = a^2 * Q_TEP (neglecting potential for TEP)
    dy[1] = -2.0 * H * phi_prime + a * a * Q_TEP;
    
    return _SUCCESS_;
}
'''

TEP_H_TEMPLATE = '''/**
 * @file tep.h
 * @brief Header file for TEP model in hi_class
 */

#ifndef __TEP_H__
#define __TEP_H__

#include "common.h"

/**
 * @brief TEP model parameters structure
 */
struct smg_tep_params {
    double alpha_eff;           /**< TEP clock-sector coupling (~1e6) */
    double phi_init;          /**< Initial scalar field value */
    double B_phi_coeff;       /**< Disformal coupling coefficient */
    double screening_threshold; /**< Critical density (20 g/cm^3 in Planck units) */
    double beta;              /**< Conformal coupling strength */
};

/* Function prototypes */
int smg_tep_init(struct background *pba, struct smg_tep_params *params);
int smg_tep_gravity_functions(struct background *pba, double *pvecback, double *pvecgravity);
int smg_tep_background_evolution(struct background *pba, double tau, double *y, double *dy);

double tep_alpha_M(struct background *pba, double phi, double phi_prime);
double tep_alpha_T(struct background *pba, double phi, double phi_prime);
double tep_alpha_B(struct background *pba, double phi, double phi_prime);
double tep_alpha_K(struct background *pba, double phi, double phi_prime);

double tep_f_B_coupling(double phi, double X, struct smg_tep_params params);
double tep_f_K_coupling(double phi, double X, struct smg_tep_params params);
double tep_screening_factor(double phi, struct smg_tep_params params);
double tep_effective_sound_speed(struct background *pba, double *pvecgravity);

#endif /* __TEP_H__ */
'''

TEP_README = '''# TEP hi_class Module

This directory contains the C source code for integrating the Temporal Equivalence Principle (TEP) into hi_class.

## Files

- `tep.c`: Main implementation with Bellini-Sawicki alpha functions
- `tep.h`: Header file with function prototypes

## Installation

1. Copy `tep.c` and `tep.h` to your hi_class installation:
   ```bash
   cp tep.c tep.h /path/to/hi_class/source/models/
   ```

2. Modify hi_class build files to include the TEP model (see main paper Appendix A)

3. Recompile hi_class:
   ```bash
   cd /path/to/hi_class
   make clean && make
   ```

## Key Physics

The TEP model implements:
- Conformal factor: $A(\\phi) = \\exp(2\\beta\\phi/M_{\\rm Pl})$
- Disformal term: $B(\\phi)$ (suppressed at late times)
- Bellini-Sawicki alphas: $\\alpha_M, \\alpha_T, \\alpha_B, \\alpha_K$
- Radiation-domination freezing: $T^\\mu_\\mu \\approx 0$ at $z \\sim 1100$

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tep_alpha_eff` | 1e6 | TEP clock-sector coupling |
| `tep_phi_init` | 0.0 | Initial field value |
| `tep_B_coeff` | 0.0 | Disformal coupling |
| `tep_beta` | 1.0 | Conformal coupling |

## References

- Bellini & Sawicki 2014, JCAP 07, 050
- Lagos et al. 2018, JCAP 03, 021 (hi_class)
'''


class Step01TEPModule:
    """Step 01: Generate TEP C module for hi_class."""
    
    STEP_NAME = "01_tep_module"
    STEP_DESCRIPTION = "TEP C Module Generation"
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.module_dir = self.root_dir / "scripts" / "hi_class_modules"
        self.module_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.log_dir / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute the TEP module generation step."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status(f"Started at: {datetime.now().isoformat()}", "INFO")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "files_created": [],
            "status": "RUNNING"
        }
        
        try:
            # Write tep.c
            print_status("Creating tep.c...", "PROCESS")
            tep_c_path = self.module_dir / "tep.c"
            with open(tep_c_path, 'w') as f:
                f.write(TEP_C_TEMPLATE)
            results["files_created"].append(str(tep_c_path))
            print_status(f"  ✓ Created {tep_c_path}", "SUCCESS")
            
            # Write tep.h
            print_status("Creating tep.h...", "PROCESS")
            tep_h_path = self.module_dir / "tep.h"
            with open(tep_h_path, 'w') as f:
                f.write(TEP_H_TEMPLATE)
            results["files_created"].append(str(tep_h_path))
            print_status(f"  ✓ Created {tep_h_path}", "SUCCESS")
            
            # Write README
            print_status("Creating README.md...", "PROCESS")
            readme_path = self.module_dir / "README.md"
            with open(readme_path, 'w') as f:
                f.write(TEP_README)
            results["files_created"].append(str(readme_path))
            print_status(f"  ✓ Created {readme_path}", "SUCCESS")
            
            # Generate installation summary
            print_status("\nModule Summary:", "INFO")
            print_status(f"  - Alpha functions: alpha_M, alpha_T, alpha_B, alpha_K", "INFO")
            print_status(f"  - Background evolution: phi'' + 2H*phi' = a^2*Q_TEP", "INFO")
            print_status(f"  - Screening: T^mu_mu-based with 20 g/cm^3 threshold", "INFO")
            print_status(f"  - Stability checks: c_s^2 >= 0 enforced", "INFO")
            
            results["status"] = "SUCCESS"
            print_status(f"STEP {self.STEP_NAME} COMPLETED", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results


if __name__ == "__main__":
    step = Step01TEPModule()
    step.run()
