/**
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
