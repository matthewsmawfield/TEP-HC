#!/usr/bin/env python3
"""
Step 19: Fast Likelihood Grid Scan for TEP epsilon_T (CAMB + plik_lite)
=========================================================================

Evaluates the Planck plik_lite TTTEEE likelihood on a grid of epsilon_T values,
using CAMB with the effective w(a) TEP approximation. All other parameters
are fixed at their LCDM best-fit values.

This gives a quick estimate of the high-ℓ acoustic constraint on epsilon_T
without running a full MCMC.
"""

import sys
import json
import numpy as np
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_19_camb_tep_grid.json"
LOG_PATH = PROJECT_ROOT / "logs" / "step_19_camb_tep_grid.log"

os.environ['COBAYA_PACKAGES_PATH'] = str(
    PROJECT_ROOT / "data" / "external" / "cobaya_packages"
)

sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.logger import TEPLogger, set_step_logger, print_status


def tep_H_grid(z, H0, ombh2, omch2, epsilon_T, z_T, n_T):
    h = H0 / 100.0
    Omega_m = (ombh2 + omch2) / h**2
    Omega_L = 1.0 - Omega_m
    Hz_lcdm = H0 * np.sqrt(Omega_m * (1.0 + z)**3 + Omega_L)

    S = np.where(z <= 0.0, 0.0, np.exp(-(np.minimum(z, z_T * 3.0) / z_T) ** n_T))
    A = np.exp(epsilon_T * np.log(1.0 + z) * S)
    A = np.maximum(A, 0.1)
    dS = np.where(
        (z > 1e-10) & (z <= z_T * 3.0),
        -S * n_T * (z / z_T) ** (n_T - 1.0) / z_T,
        0.0
    )
    alpha_A = -epsilon_T * (S + (1.0 + z) * np.log(1.0 + z) * dS)
    M = A / (1.0 - alpha_A)
    return Hz_lcdm * M


def solve_w_eff(z_grid, H_tep, H0, ombh2, omch2):
    h = H0 / 100.0
    Omega_m = (ombh2 + omch2) / h**2
    omega_de = H_tep**2 / H0**2 - Omega_m * (1.0 + z_grid)**3
    omega_de = np.maximum(omega_de, 1e-15)
    ln_omega = np.log(omega_de)
    d_ln_omega_dz = np.gradient(ln_omega, z_grid)
    return -1.0 + (1.0 + z_grid) / 3.0 * d_ln_omega_dz


def compute_tep_cls(H0, ombh2, omch2, tau, As, ns, epsilon_T, z_T, n_T, lmax=2508):
    import camb
    from camb.dark_energy import DarkEnergyPPF

    z_grid = np.linspace(0, 3.0, 500)
    H_tep = tep_H_grid(z_grid, H0, ombh2, omch2, epsilon_T, z_T, n_T)
    w_eff = solve_w_eff(z_grid, H_tep, H0, ombh2, omch2)

    a_grid = 1.0 / (1.0 + z_grid)
    sort_idx = np.argsort(a_grid)
    a_sorted = a_grid[sort_idx]
    w_sorted = w_eff[sort_idx]
    mask = (a_sorted > 1e-6) & (a_sorted <= 1.0)

    pars = camb.CAMBparams()
    pars.set_cosmology(H0=H0, ombh2=ombh2, omch2=omch2, mnu=0.06, omk=0, tau=tau)
    pars.InitPower.set_params(As=As, ns=ns, r=0)
    pars.set_for_lmax(lmax, lens_potential_accuracy=0)

    de = DarkEnergyPPF(w=-1.0, wa=0.0)
    de.set_w_a_table(a_sorted[mask], w_sorted[mask])
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


def main():
    logger = TEPLogger("step_19_camb_tep_grid", LOG_PATH)
    set_step_logger(logger)

    print_status("=" * 60, "TITLE")
    print_status("CAMB TEP Grid Scan (plik_lite TTTEEE)", "TITLE")
    print_status("=" * 60, "TITLE")

    # LCDM best-fit parameters
    H0 = 66.63
    ombh2 = 0.0212
    omch2 = 0.1154
    tau = 0.049
    As = 2.1e-9
    ns = 0.965
    z_T = 5.0
    n_T = 2.0
    A_planck = 1.0

    epsilon_values = np.linspace(0.0, 0.02, 11)
    results = []

    logger.info(f"\nEvaluating {len(epsilon_values)} epsilon_T values...")
    for i, eps in enumerate(epsilon_values):
        logger.process(f"  [{i+1}/{len(epsilon_values)}] epsilon_T = {eps:.4f} ... ")
        try:
            cls = compute_tep_cls(
                H0=H0, ombh2=ombh2, omch2=omch2, tau=tau,
                As=As, ns=ns, epsilon_T=eps, z_T=z_T, n_T=n_T,
                lmax=2508
            )
            loglike = get_loglike_plik(cls, A_planck=A_planck)
            chi2 = -2 * loglike
            results.append({
                'epsilon_T': float(eps),
                'loglike': float(loglike),
                'chi2': float(chi2),
                'status': 'OK'
            })
            logger.success(f"  loglike = {loglike:.2f}, chi2 = {chi2:.2f}")
        except Exception as e:
            results.append({
                'epsilon_T': float(eps),
                'status': 'ERROR',
                'message': str(e)
            })
            logger.error(f"  ERROR: {e}")

    # Find minimum
    ok_results = [r for r in results if r['status'] == 'OK']
    if ok_results:
        best = min(ok_results, key=lambda r: r['chi2'])
        logger.info(f"\n--- Best fit ---")
        logger.info(f"  epsilon_T = {best['epsilon_T']:.5f}")
        logger.info(f"  chi2 = {best['chi2']:.2f}")

        # Compute delta chi2 relative to LCDM (eps=0)
        lcdm = [r for r in ok_results if abs(r['epsilon_T']) < 1e-8]
        if lcdm:
            delta_chi2 = best['chi2'] - lcdm[0]['chi2']
            logger.info(f"  Delta chi2 (best - LCDM) = {delta_chi2:.2f}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump({
            'fixed_params': {
                'H0': H0, 'ombh2': ombh2, 'omch2': omch2,
                'tau': tau, 'As': As, 'ns': ns,
                'z_T': z_T, 'n_T': n_T, 'A_planck': A_planck,
            },
            'grid_results': results,
            'best_fit': best if ok_results else None,
        }, f, indent=2, default=str)

    logger.success(f"\nResults saved to {OUTPUT_PATH}")


class Step19CAMBTEPGrid:
    """Wrapper for pipeline integration."""
    def run(self) -> dict:
        main()
        with open(OUTPUT_PATH) as f:
            return json.load(f)


if __name__ == "__main__":
    main()
