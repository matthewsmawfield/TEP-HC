#!/usr/bin/env python3
"""
Step 18: Minimal Standalone MCMC with CAMB + TEP Effective w(a)
===============================================================

This script implements a minimal MCMC using emcee, with CAMB as the
theory backend and the Planck plik_lite likelihood for high-ℓ TTTEEE.

The TEP effective w(a) is computed on-the-fly from the sampled parameters.
This serves as a production prototype for the high-ℓ constraint.

Parameters sampled:
  - H0, ombh2, omch2, tau, As, ns (standard cosmology)
  - epsilon_T (TEP amplitude; z_T and n_T are fixed at 5.0 and 2.0)
  - A_planck (Planck calibration nuisance)

This is an APPROXIMATE implementation. The true TEP conformal transformation
is not exactly equivalent to a modified w(a), but for the high-ℓ acoustic
sector this approximation is expected to capture the dominant physics.
"""

import json
import numpy as np
from pathlib import Path
import sys
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_18_camb_tep_mcmc.json"
CHAIN_PATH = PROJECT_ROOT / "results" / "step_18_camb_tep_mcmc_chain.npz"

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


def compute_tep_cls(H0, ombh2, omch2, tau, As, ns, epsilon_T, z_T, n_T, lmax=2508):
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
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK', raw_cl=True)
    return powers['total']


class MockProvider:
    def __init__(self):
        self.cls_array = None

    def set_cls(self, cls_array):
        self.cls_array = cls_array

    def get_Cl(self, units="FIRASmuK2"):
        return {
            'tt': self.cls_array[:, 0],
            'ee': self.cls_array[:, 1],
            'bb': self.cls_array[:, 2],
            'te': self.cls_array[:, 3],
        }


# Cache the plik_lite likelihood instance to avoid repeated self-tests
_plik_lite_instance = None
_mock_provider = MockProvider()


def get_loglike_plik(cls_array, A_planck=1.0):
    global _plik_lite_instance
    if _plik_lite_instance is None:
        from cobaya.likelihoods.planck_2018_highl_plik import TTTEEE_lite
        LikelihoodClass = getattr(TTTEEE_lite, 'TTTEEE_lite')
        packages_path = str(PROJECT_ROOT / "data" / "external" / "cobaya_packages")
        _plik_lite_instance = LikelihoodClass({}, packages_path=packages_path)
        _plik_lite_instance.provider = _mock_provider
    _mock_provider.set_cls(cls_array)
    return _plik_lite_instance.logp(A_planck=A_planck)


def log_prob(theta, plik_only=True):
    """
    theta = [H0, ombh2, omch2, tau, log(1e10 As), ns, epsilon_T, A_planck]
    """
    H0, ombh2, omch2, tau, log10As, ns, epsilon_T, A_planck = theta
    As = np.exp(log10As) * 1e-10

    # Prior bounds
    if not (50 < H0 < 90): return -np.inf
    if not (0.01 < ombh2 < 0.04): return -np.inf
    if not (0.05 < omch2 < 0.25): return -np.inf
    if not (0.01 < tau < 0.15): return -np.inf
    if not (2.5 < log10As < 3.5): return -np.inf
    if not (0.8 < ns < 1.1): return -np.inf
    if not (0.0 <= epsilon_T < 0.1): return -np.inf
    if not (0.9 < A_planck < 1.25): return -np.inf

    try:
        cls = compute_tep_cls(
            H0=H0, ombh2=ombh2, omch2=omch2, tau=tau,
            As=As, ns=ns, epsilon_T=epsilon_T, z_T=5.0, n_T=2.0,
            lmax=2508
        )
        loglike_plik = get_loglike_plik(cls, A_planck=A_planck)

        if not np.isfinite(loglike_plik):
            return -np.inf

        # Simple Gaussian priors (very broad)
        log_prior = 0.0

        return loglike_plik + log_prior
    except Exception as e:
        return -np.inf


def run_emcee(n_walkers=16, n_steps=50, progress=True):
    """Run a short emcee MCMC to test the pipeline."""
    try:
        import emcee
    except ImportError:
        print("emcee not installed. Installing...")
        os.system("pip install emcee")
        import emcee

    # Initial guess near LCDM + small epsilon_T
    initial = np.array([67.4, 0.02237, 0.1200, 0.0544, 3.044, 0.965, 0.005, 1.0])
    ndim = len(initial)

    # Perturb initial positions
    pos = initial + 0.01 * initial * np.random.randn(n_walkers, ndim)
    pos[:, 6] = np.abs(pos[:, 6])  # epsilon_T >= 0
    pos[:, 7] = np.clip(pos[:, 7], 0.9, 1.25)

    sampler = emcee.EnsembleSampler(n_walkers, ndim, log_prob)
    sampler.run_mcmc(pos, n_steps, progress=progress)

    return sampler


def main():
    print("=" * 60)
    print("CAMB TEP Minimal MCMC (emcee)")
    print("=" * 60)

    print("\nRunning short test chain (16 walkers x 50 steps)...")
    sampler = run_emcee(n_walkers=16, n_steps=50)

    # Discard burn-in and flatten
    samples = sampler.get_chain(discard=10, flat=True)
    log_probs = sampler.get_log_prob(discard=10, flat=True)

    print(f"\nCollected {len(samples)} post-burn-in samples")
    print(f"Mean log_prob: {np.mean(log_probs):.2f}")
    print(f"Std log_prob: {np.std(log_probs):.2f}")

    # Parameter names
    names = ['H0', 'ombh2', 'omch2', 'tau', 'log10As', 'ns', 'epsilon_T', 'A_planck']
    print("\n--- Posterior means ---")
    for i, name in enumerate(names):
        print(f"  {name}: {np.mean(samples[:, i]):.5f} ± {np.std(samples[:, i]):.5f}")

    # Save chain
    np.savez(CHAIN_PATH, chain=samples, log_prob=log_probs, names=names)
    print(f"\nChain saved to {CHAIN_PATH}")

    # Save summary
    with open(OUTPUT_PATH, "w") as f:
        json.dump({
            'n_samples': len(samples),
            'n_walkers': 16,
            'n_steps': 50,
            'burn_in': 10,
            'mean_log_prob': float(np.mean(log_probs)),
            'std_log_prob': float(np.std(log_probs)),
            'posterior_means': {
                name: float(np.mean(samples[:, i])) for i, name in enumerate(names)
            },
            'posterior_stds': {
                name: float(np.std(samples[:, i])) for i, name in enumerate(names)
            },
        }, f, indent=2)
    print(f"Summary saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
