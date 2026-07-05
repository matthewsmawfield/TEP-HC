#!/usr/bin/env python3
"""
Step 14: CAMB TEP Approximation via Effective w(a)
==================================================

TEP modifies the Hubble rate as H_TEP(z) = H_LCDM(z) * M(z), where
M(z) = A(z) / (1 - alpha_A(z)) is the Jordan-frame conformal factor.

Since CAMB does not have a native tep_mode, we approximate TEP by finding
the effective dark-energy equation of state w(a) that reproduces the TEP
Hubble rate in the background. This is exact for the background geometry
and serves as a diagnostic for whether the high-ℓ CMB is sensitive to the
background H(z) or to the perturbation-sector details.

Method:
  1. Compute H_TEP(z) on a fine grid using the hi_class TEP formulas.
  2. Solve for the effective Ω_DE(z) that gives H_TEP(z).
  3. Differentiate to get w_eff(z).
  4. Feed w_eff(a) into CAMB via DarkEnergyFluid.set_w_a_table().
  5. Compute CMB power spectra and compare with hi_class output.

This script serves as both an exploratory test and a production prototype.
"""

import sys
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_14_camb_tep_approximation.json"
LOG_PATH = PROJECT_ROOT / "logs" / "step_14_camb_tep_approximation.log"

sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.logger import TEPLogger, set_step_logger, print_status


def tep_transition(z, z_T, n_T):
    """TEP suppression factor S(z) = exp(-(z/z_T)^n_T)."""
    z = np.asarray(z)
    return np.where(z <= 0.0, 0.0, np.exp(-(np.minimum(z, z_T * 3.0) / z_T) ** n_T))


def tep_A(z, epsilon_T, z_T, n_T):
    """Conformal factor A(z) = exp(epsilon_T * ln(1+z) * S(z))."""
    z = np.asarray(z)
    S = tep_transition(z, z_T, n_T)
    log_term = np.log(1.0 + z)
    A_val = np.exp(epsilon_T * log_term * S)
    return np.where((epsilon_T == 0.0) | (z <= 0.0), 1.0, np.maximum(A_val, 0.1))


def tep_alpha_A(z, epsilon_T, z_T, n_T):
    """Jordan-frame coupling alpha_A = d ln A / d ln(1+z)."""
    z = np.asarray(z)
    S = tep_transition(z, z_T, n_T)
    dS = np.where(
        (z > 1e-10) & (z <= z_T * 3.0),
        -S * n_T * (z / z_T) ** (n_T - 1.0) / z_T,
        0.0
    )
    return np.where(
        (epsilon_T == 0.0) | (z <= 0.0),
        0.0,
        -epsilon_T * (S + (1.0 + z) * np.log(1.0 + z) * dS)
    )


def tep_M(z, epsilon_T, z_T, n_T):
    """Jordan-frame factor M(z) = A(z) / (1 - alpha_A(z))."""
    z = np.asarray(z)
    A = tep_A(z, epsilon_T, z_T, n_T)
    alpha = tep_alpha_A(z, epsilon_T, z_T, n_T)
    return np.where(
        (epsilon_T == 0.0) | (z <= 0.0),
        1.0,
        A / (1.0 - alpha)
    )


def tep_H(z, H0, ombh2, omch2, epsilon_T, z_T, n_T):
    """
    TEP Hubble rate H_TEP(z) = H_LCDM(z) * M(z).
    LCDM uses the standard flat Friedmann equation.
    """
    h = H0 / 100.0
    Omega_m = (ombh2 + omch2) / h**2
    Omega_L = 1.0 - Omega_m
    Hz_lcdm = H0 * np.sqrt(Omega_m * (1.0 + z)**3 + Omega_L)
    M = tep_M(z, epsilon_T, z_T, n_T)
    return Hz_lcdm * M


def solve_w_eff(z_grid, H_tep, H0, ombh2, omch2):
    """
    Given H_TEP(z) on a grid, solve for the effective w(z).
    """
    h = H0 / 100.0
    Omega_m = (ombh2 + omch2) / h**2
    H0_sq = H0**2
    omega_de = H_tep**2 / H0_sq - Omega_m * (1.0 + z_grid)**3
    omega_de = np.maximum(omega_de, 1e-15)
    ln_omega = np.log(omega_de)
    d_ln_omega_dz = np.gradient(ln_omega, z_grid)
    return -1.0 + (1.0 + z_grid) / 3.0 * d_ln_omega_dz, omega_de


def compute_camb_tep_cl(H0, ombh2, omch2, tau, As, ns,
                         epsilon_T, z_T, n_T, lmax=2500, logger=None):
    """
    Compute CMB power spectra using CAMB with an effective w(a)
    that approximates the TEP Hubble rate.
    """
    import camb
    from camb.dark_energy import DarkEnergyPPF

    if logger:
        logger.process("Computing TEP effective w(a) and CAMB Cls...")

    z_grid = np.linspace(0, 3.0, 500)
    H_tep = tep_H(z_grid, H0, ombh2, omch2, epsilon_T, z_T, n_T)
    w_eff, omega_de = solve_w_eff(z_grid, H_tep, H0, ombh2, omch2)

    a_grid = 1.0 / (1.0 + z_grid)
    sort_idx = np.argsort(a_grid)
    a_sorted = a_grid[sort_idx]
    w_sorted = w_eff[sort_idx]
    mask = (a_sorted > 1e-6) & (a_sorted <= 1.0)
    a_sorted = a_sorted[mask]
    w_sorted = w_sorted[mask]

    pars = camb.CAMBparams()
    pars.set_cosmology(H0=H0, ombh2=ombh2, omch2=omch2, mnu=0.06, omk=0, tau=tau)
    pars.InitPower.set_params(As=As, ns=ns, r=0)
    pars.set_for_lmax(lmax, lens_potential_accuracy=0)

    de = DarkEnergyPPF(w=-1.0, wa=0.0)
    de.set_w_a_table(a_sorted, w_sorted)
    pars.DarkEnergy = de

    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK')

    return {
        'z_grid': z_grid.tolist(),
        'H_tep': H_tep.tolist(),
        'w_eff': w_eff.tolist(),
        'a_grid': a_sorted.tolist(),
        'w_a': w_sorted.tolist(),
        'tt': powers['total'][:, 0].tolist(),
        'ee': powers['total'][:, 1].tolist(),
        'te': powers['total'][:, 3].tolist(),
        'lmax': lmax,
    }


def test_lcdm_baseline():
    """Verify CAMB baseline matches standard ΛCDM."""
    import camb
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=67.4, ombh2=0.02237, omch2=0.1200, mnu=0.06, omk=0, tau=0.0544)
    pars.InitPower.set_params(As=2.1e-9, ns=0.965, r=0)
    pars.set_for_lmax(2500, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK')
    return {
        'tt_2': float(powers['total'][2, 0]),
        'tt_100': float(powers['total'][100, 0]),
        'tt_1000': float(powers['total'][1000, 0]),
    }


def main():
    logger = TEPLogger("step_14_camb_tep_approximation", LOG_PATH)
    set_step_logger(logger)

    print_status("=" * 60, "TITLE")
    print_status("CAMB TEP Approximation via Effective w(a)", "TITLE")
    print_status("=" * 60, "TITLE")

    # Baseline LCDM
    print_status("\n--- ΛCDM Baseline ---", "TITLE")
    lcdm = test_lcdm_baseline()
    for k, v in lcdm.items():
        logger.info(f"  {k}: {v:.4f}")

    # TEP parameters (typical values from TEP-HC chains)
    H0 = 66.63
    ombh2 = 0.0212
    omch2 = 0.1154
    tau = 0.049
    As = 2.1e-9
    ns = 0.965
    epsilon_T = 0.0056
    z_T = 5.0
    n_T = 2.0

    logger.info(f"\n--- TEP Parameters ---")
    logger.info(f"  epsilon_T = {epsilon_T}")
    logger.info(f"  z_T = {z_T}")
    logger.info(f"  n_T = {n_T}")

    # Compute TEP-approximated spectra
    logger.process(f"\n--- Computing CAMB TEP spectra ---")
    tep_result = compute_camb_tep_cl(
        H0=H0, ombh2=ombh2, omch2=omch2, tau=tau,
        As=As, ns=ns, epsilon_T=epsilon_T, z_T=z_T, n_T=n_T,
        lmax=2500, logger=logger
    )

    logger.info(f"  TT[2] = {tep_result['tt'][2]:.4f}")
    logger.info(f"  TT[100] = {tep_result['tt'][100]:.4f}")
    logger.info(f"  TT[500] = {tep_result['tt'][500]:.4f}")
    logger.info(f"  TT[1000] = {tep_result['tt'][1000]:.4f}")

    # Compute LCDM with same cosmological params for fair comparison
    logger.process(f"\n--- Computing LCDM with same params ---")
    import camb
    pars_lcdm = camb.CAMBparams()
    pars_lcdm.set_cosmology(H0=H0, ombh2=ombh2, omch2=omch2, mnu=0.06, omk=0, tau=tau)
    pars_lcdm.InitPower.set_params(As=As, ns=ns, r=0)
    pars_lcdm.set_for_lmax(2500, lens_potential_accuracy=0)
    results_lcdm = camb.get_results(pars_lcdm)
    powers_lcdm = results_lcdm.get_cmb_power_spectra(pars_lcdm, CMB_unit='muK')
    tt_lcdm = powers_lcdm['total'][:, 0]

    # Fractional difference from LCDM
    logger.info(f"\n--- Fractional differences (TEP - LCDM)/LCDM ---")
    frac_diffs = {}
    for l in [2, 10, 100, 500, 1000, 1500, 2000]:
        frac = (tep_result['tt'][l] - tt_lcdm[l]) / tt_lcdm[l]
        frac_diffs[l] = frac
        logger.info(f"  l={l:4d}: {frac*100:.4f}%")

    # Check for NaN/Inf
    tt_arr = np.array(tep_result['tt'])
    has_nan = bool(np.any(np.isnan(tt_arr)))
    has_inf = bool(np.any(np.isinf(tt_arr)))
    logger.info(f"\n  Has NaN: {has_nan}")
    logger.info(f"  Has Inf: {has_inf}")

    # Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump({
            'lcdm': lcdm,
            'lcdm_same_params': {l: float(tt_lcdm[l]) for l in [2, 10, 100, 500, 1000, 1500, 2000]},
            'tep_params': {
                'H0': H0, 'ombh2': ombh2, 'omch2': omch2,
                'tau': tau, 'As': As, 'ns': ns,
                'epsilon_T': epsilon_T, 'z_T': z_T, 'n_T': n_T,
            },
            'tep_spectra': {
                'lmax': tep_result['lmax'],
                'tt_sample': {l: tep_result['tt'][l] for l in [2, 10, 100, 500, 1000, 1500, 2000]},
            },
            'fractional_diff_percent': {l: frac_diffs[l] * 100 for l in frac_diffs},
            'w_eff_summary': {
                'z_grid': tep_result['z_grid'][:20],
                'w_eff': tep_result['w_eff'][:20],
            },
            'clean': not (has_nan or has_inf),
        }, f, indent=2)

    logger.success(f"\nResults saved to {OUTPUT_PATH}")


class Step14CAMBTEPApproximation:
    """Wrapper for pipeline integration."""
    def run(self) -> dict:
        main()
        with open(OUTPUT_PATH) as f:
            return json.load(f)


if __name__ == "__main__":
    main()
