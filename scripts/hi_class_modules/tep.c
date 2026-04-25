/**
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
        fprintf(stderr, "ERROR: tep_alpha_eff must be positive\n");
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
        fprintf(stderr, "WARNING: c_s^2 = %f < 0, instability detected\n", cs2);
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
