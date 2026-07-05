#!/usr/bin/env python3
"""
Step 17: Full Planck plik_lite Evaluation with CAMB TEP Cls
===========================================================

This script evaluates the Planck 2018 plik_lite TTTEEE likelihood using
CAMB-generated CMB spectra with the TEP effective w(a) approximation.

It creates a mock Cobaya provider that returns our CAMB Cls, then calls
the likelihood's log_likelihood method directly.
"""

import sys
import json
import numpy as np
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_17_camb_plik_full_eval.json"
LOG_PATH = PROJECT_ROOT / "logs" / "step_17_camb_plik_full_eval.log"

os.environ['COBAYA_PACKAGES_PATH'] = str(
    PROJECT_ROOT / "data" / "external" / "cobaya_packages"
)

sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.logger import TEPLogger, set_step_logger, print_status


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


def generate_tep_cls(H0, ombh2, omch2, tau, As, ns, epsilon_T, z_T, n_T, lmax=2508, logger=None):
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


def evaluate_plik_lite(cls_array, logger=None):
    """Evaluate plik_lite with given CAMB Cls."""
    try:
        loglike = get_loglike_plik(cls_array, A_planck=1.0)
        chi2 = -2 * loglike
        result = {
            "status": "OK",
            "loglike": float(loglike),
            "chi2": float(chi2),
        }
        if logger:
            logger.success(f"  loglike={loglike:.2f}, chi2={chi2:.2f}")
        return result
    except Exception as e:
        import traceback
        msg = str(e)
        if logger:
            logger.error(f"  plik_lite evaluation failed: {msg}")
        return {"status": "ERROR", "message": msg, "traceback": traceback.format_exc()}


def evaluate_lcdm_plik(logger=None):
    """Evaluate plik_lite with standard LCDM CAMB Cls for comparison."""
    import camb
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=66.63, ombh2=0.0212, omch2=0.1154, mnu=0.06, omk=0, tau=0.049)
    pars.InitPower.set_params(As=2.1e-9, ns=0.965, r=0)
    pars.set_for_lmax(2508, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK', raw_cl=True)
    if logger:
        logger.process("Evaluating plik_lite with LCDM Cls...")
    return evaluate_plik_lite(powers['total'], logger=logger)


def main():
    logger = TEPLogger("step_17_camb_plik_full_eval", LOG_PATH)
    set_step_logger(logger)

    print_status("=" * 60, "TITLE")
    print_status("Full plik_lite Evaluation with CAMB TEP", "TITLE")
    print_status("=" * 60, "TITLE")

    # 1. LCDM baseline
    logger.info("\n1. LCDM baseline...")
    lcdm_result = evaluate_lcdm_plik(logger=logger)
    for k, v in lcdm_result.items():
        logger.info(f"   {k}: {v}")

    # 2. TEP approximation
    logger.info("\n2. Generating TEP Cls with CAMB...")
    cls = generate_tep_cls(
        H0=66.63, ombh2=0.0212, omch2=0.1154, tau=0.049,
        As=2.1e-9, ns=0.965,
        epsilon_T=0.0056, z_T=5.0, n_T=2.0,
        lmax=2508, logger=logger
    )
    logger.info(f"   Cls shape: {cls.shape}")

    logger.info("\n3. Evaluating plik_lite with TEP Cls...")
    tep_result = evaluate_plik_lite(cls, logger=logger)
    for k, v in tep_result.items():
        logger.info(f"   {k}: {v}")

    # 3. Comparison
    delta_chi2 = None
    if lcdm_result.get('status') == 'OK' and tep_result.get('status') == 'OK':
        delta_chi2 = tep_result['chi2'] - lcdm_result['chi2']
        logger.info(f"\n4. Delta chi2 (TEP - LCDM): {delta_chi2:.2f}")

    # Save results
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    def convert(obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    with open(OUTPUT_PATH, "w") as f:
        json.dump({
            'lcdm': convert(lcdm_result),
            'tep': convert(tep_result),
            'delta_chi2': float(delta_chi2) if delta_chi2 is not None else None,
        }, f, indent=2, default=str)

    logger.success(f"\nResults saved to {OUTPUT_PATH}")


class Step17CAMBPlikFullEval:
    """Wrapper for pipeline integration."""
    def run(self) -> dict:
        main()
        with open(OUTPUT_PATH) as f:
            return json.load(f)


if __name__ == "__main__":
    main()
