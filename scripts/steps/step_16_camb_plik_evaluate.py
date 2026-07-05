#!/usr/bin/env python3
"""
Step 16: Evaluate Planck plik_lite with CAMB TEP Cls
=====================================================

This script fully evaluates the Planck 2018 plik_lite TTTEEE likelihood
using CAMB-generated CMB spectra with the TEP effective w(a) approximation.

If the likelihood evaluation returns a finite, physically sensible chi2,
the path to a full CAMB-based TTTEEE MCMC is open.
"""

import json
import numpy as np
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_16_camb_plik_evaluate.json"

os.environ['COBAYA_PACKAGES_PATH'] = str(
    PROJECT_ROOT / "data" / "external" / "cobaya_packages"
)


def tep_transition(z, z_T, n_T):
    z = np.asarray(z)
    return np.where(z <= 0.0, 0.0, np.exp(-(np.minimum(z, z_T * 3.0) / z_T) ** n_T))


def tep_A(z, epsilon_T, z_T, n_T):
    z = np.asarray(z)
    S = tep_transition(z, z_T, n_T)
    A_val = np.exp(epsilon_T * np.log(1.0 + z) * S)
    return np.where((epsilon_T == 0.0) | (z <= 0.0), 1.0, np.maximum(A_val, 0.1))


def tep_alpha_A(z, epsilon_T, z_T, n_T):
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
    z = np.asarray(z)
    A = tep_A(z, epsilon_T, z_T, n_T)
    alpha = tep_alpha_A(z, epsilon_T, z_T, n_T)
    return np.where((epsilon_T == 0.0) | (z <= 0.0), 1.0, A / (1.0 - alpha))


def tep_H(z, H0, ombh2, omch2, epsilon_T, z_T, n_T):
    h = H0 / 100.0
    Omega_m = (ombh2 + omch2) / h**2
    Omega_L = 1.0 - Omega_m
    Hz_lcdm = H0 * np.sqrt(Omega_m * (1.0 + z)**3 + Omega_L)
    return Hz_lcdm * tep_M(z, epsilon_T, z_T, n_T)


def solve_w_eff(z_grid, H_tep, H0, ombh2, omch2):
    h = H0 / 100.0
    Omega_m = (ombh2 + omch2) / h**2
    omega_de = H_tep**2 / H0**2 - Omega_m * (1.0 + z_grid)**3
    omega_de = np.maximum(omega_de, 1e-15)
    ln_omega = np.log(omega_de)
    d_ln_omega_dz = np.gradient(ln_omega, z_grid)
    return -1.0 + (1.0 + z_grid) / 3.0 * d_ln_omega_dz, omega_de


def generate_tep_cls(H0, ombh2, omch2, tau, As, ns, epsilon_T, z_T, n_T, lmax=2508):
    import camb
    from camb.dark_energy import DarkEnergyPPF

    z_grid = np.linspace(0, 3.0, 500)
    H_tep = tep_H(z_grid, H0, ombh2, omch2, epsilon_T, z_T, n_T)
    w_eff, _ = solve_w_eff(z_grid, H_tep, H0, ombh2, omch2)

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
    return powers['total']


def evaluate_plik_lite(cls_array):
    """
    Evaluate Planck plik_lite TTTEEE likelihood with given Cls.

    The plik_lite likelihood uses pre-marginalized nuisance parameters
    and only requires TT, EE, TE spectra.
    """
    try:
        from cobaya.likelihoods.planck_2018_highl_plik import TTTEEE_lite
        LikelihoodClass = getattr(TTTEEE_lite, 'TTTEEE_lite')

        # Create minimal Cobaya info for the likelihood
        info = {
            'path': str(PROJECT_ROOT / "data" / "external" / "cobaya_packages"),
            'likelihood': {
                'planck_2018_highl_plik.TTTEEE_lite': {}
            }
        }

        # Instantiate the likelihood
        likelihood = LikelihoodClass(info['likelihood']['planck_2018_highl_plik.TTTEEE_lite'],
                                     packages_path=info['path'])

        # The likelihood expects a dictionary with Cls in a specific format
        # Check what method it uses to get Cls
        # Cobaya likelihoods typically have a `logp` or `loglikelihood` method
        # that takes a dictionary of parameters

        # For plik_lite, the Cls are typically provided via a `theory` provider
        # We need to understand the exact interface

        # Let's inspect the class
        import inspect
        methods = [m for m in dir(likelihood) if not m.startswith('_')]
        print(f"Likelihood methods: {methods[:20]}")

        # The standard Cobaya likelihood interface is:
        # logp(cls_dict) or logp(params_dict)
        # where cls_dict contains the theory Cls

        # For Planck likelihoods, the expected keys are typically:
        # 'tt', 'ee', 'te', 'bb' or similar
        # Let's check the exact requirements

        return {
            "status": "INSPECTED",
            "likelihood_class": str(LikelihoodClass),
            "methods": methods,
            "note": "Need to understand exact Cls format expected by plik_lite",
        }

    except Exception as e:
        import traceback
        return {
            "status": "ERROR",
            "message": str(e),
            "traceback": traceback.format_exc(),
        }


def main():
    print("=" * 60)
    print("Planck plik_lite + CAMB TEP Evaluation")
    print("=" * 60)

    # Generate TEP Cls
    print("\n1. Generating TEP Cls with CAMB...")
    cls = generate_tep_cls(
        H0=66.63, ombh2=0.0212, omch2=0.1154, tau=0.049,
        As=2.1e-9, ns=0.965,
        epsilon_T=0.0056, z_T=5.0, n_T=2.0,
        lmax=2508
    )
    print(f"   Cls shape: {cls.shape}")
    print(f"   TT[100] = {cls[100, 0]:.2f}")

    # Evaluate likelihood
    print("\n2. Evaluating plik_lite...")
    result = evaluate_plik_lite(cls)
    for k, v in result.items():
        print(f"   {k}: {v}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(result, f, indent=2)

    print(f"\nResults saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
