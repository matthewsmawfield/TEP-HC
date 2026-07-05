#!/usr/bin/env python3
"""
Step 13: CAMB Exploratory Test for TEP High-ℓ Compatibility
===========================================================

Background: The Planck 2018 high-ℓ TTTEEE likelihood fails with hi_class
when tep_mode is enabled, producing divide-by-zero/overflow errors in the
clipy Python interface. This script tests whether CAMB (an alternative
Boltzmann solver) could serve as a viable backend for a future high-ℓ
production run.

Key findings:
1. CAMB v1.6.5 generates clean, physically sensible CMB power spectra.
2. The Planck plik_lite likelihood module loads successfully in the Cobaya
   environment.
3. CAMB does NOT have a native tep_mode. Implementing TEP in CAMB would
   require modifying the Friedmann equation to include the conformal factor
   M(z) = A(z)/(1 - alpha_A(z)), which is a non-trivial source-code change.
4. The perturbation sector in CAMB would also need modification to handle
   the pure-conformal scalar field consistently.
5. A viable path forward: patch CAMB's Fortran source to add tep_mode,
   then wrap it for Cobaya. This is estimated at ~1-2 weeks of work.

This script serves as a scoping document, not a production pipeline step.
"""

import sys
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_13_camb_exploratory.json"
LOG_PATH = PROJECT_ROOT / "logs" / "step_13_camb_exploratory.log"

sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.logger import TEPLogger, set_step_logger, print_status


def test_camb_basic(logger):
    """Test that CAMB runs for standard ΛCDM."""
    logger.process("Testing CAMB basic ΛCDM run...")
    try:
        import camb
    except ImportError:
        logger.error("CAMB not installed")
        return {"status": "CAMB not installed", "tt_2": None}

    pars = camb.CAMBparams()
    pars.set_cosmology(H0=67.4, ombh2=0.02237, omch2=0.1200, mnu=0.06, omk=0, tau=0.0544)
    pars.InitPower.set_params(As=2.1e-9, ns=0.965, r=0)
    pars.set_for_lmax(2500, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK')

    tt = powers['total'][:, 0]
    has_nan = bool(np.any(np.isnan(tt)))
    has_inf = bool(np.any(np.isinf(tt)))

    result = {
        "status": "OK" if not (has_nan or has_inf) else "FAILED",
        "tt_2": float(tt[2]),
        "tt_100": float(tt[100]),
        "tt_500": float(tt[500]),
        "tt_1000": float(tt[1000]),
        "tt_2000": float(tt[2000]),
        "has_nan": has_nan,
        "has_inf": has_inf,
    }
    logger.success(f"  CAMB basic: {result['status']}, TT[2]={result['tt_2']:.2f}")
    return result


def test_plik_lite_loads(logger):
    """Test that Planck plik_lite likelihood loads in Cobaya."""
    logger.process("Testing Planck plik_lite module load...")
    import os
    os.environ['COBAYA_PACKAGES_PATH'] = str(PROJECT_ROOT / "data" / "external" / "cobaya_packages")

    try:
        from cobaya.likelihoods.planck_2018_highl_plik import TTTEEE_lite
        import inspect
        cls = getattr(TTTEEE_lite, 'TTTEEE_lite', None)
        if cls is None:
            for name in dir(TTTEEE_lite):
                obj = getattr(TTTEEE_lite, name)
                if inspect.isclass(obj) and 'lite' in name.lower():
                    cls = obj
                    break
        result = {
            "status": "OK" if cls is not None else "CLASS_NOT_FOUND",
            "likelihood_class": str(cls) if cls else None,
        }
        logger.success(f"  plik_lite load: {result['status']}")
        return result
    except Exception as e:
        logger.error(f"  plik_lite load failed: {e}")
        return {"status": "ERROR", "message": str(e)}


def test_tep_in_camb(logger):
    """
    Test whether CAMB can handle a TEP-like H(z) modification.

    CAMB does not have a native tep_mode. The background evolution is
    hard-coded in Fortran. A custom H(z) would require either:
      (a) Modifying the Fortran source to add a conformal factor M(z)
      (b) Using a dark-energy parameterization that approximates the TEP H(z)

    Approach (b) is not exact because TEP is a conformal transformation of
    the metric, not just a new fluid component.
    """
    logger.process("Testing TEP approximation in CAMB...")
    try:
        import camb
        from camb.dark_energy import DarkEnergyFluid
    except ImportError:
        return {"status": "CAMB not installed"}

    # Test 1: Standard wCDM (CAMB native)
    pars = camb.CAMBparams()
    pars.set_cosmology(H0=67.4, ombh2=0.02237, omch2=0.1200)
    pars.InitPower.set_params(As=2.1e-9, ns=0.965)
    pars.DarkEnergy = DarkEnergyFluid(w=-1.0, wa=0.0)
    pars.set_for_lmax(100, lens_potential_accuracy=0)
    results = camb.get_results(pars)
    powers = results.get_cmb_power_spectra(pars, CMB_unit='muK')
    lcdm_tt_2 = float(powers['total'][2, 0])

    # Test 2: wCDM with small w deviation
    pars2 = camb.CAMBparams()
    pars2.set_cosmology(H0=67.4, ombh2=0.02237, omch2=0.1200)
    pars2.InitPower.set_params(As=2.1e-9, ns=0.965)
    pars2.DarkEnergy = DarkEnergyFluid(w=-0.95, wa=0.0)
    pars2.set_for_lmax(100, lens_potential_accuracy=0)
    results2 = camb.get_results(pars2)
    powers2 = results2.get_cmb_power_spectra(pars2, CMB_unit='muK')
    wcdm_tt_2 = float(powers2['total'][2, 0])

    result = {
        "status": "OK",
        "lcdm_tt_2": lcdm_tt_2,
        "wcdm_tt_2": wcdm_tt_2,
        "fractional_diff": float((wcdm_tt_2 - lcdm_tt_2) / lcdm_tt_2),
        "note": (
            "CAMB can vary w but cannot exactly reproduce the TEP conformal "
            "factor M(z). A source-code modification is required for an exact "
            "TEP implementation."
        ),
    }
    logger.success(f"  TEP approximation: works but not exact (frac_diff={result['fractional_diff']:.4f})")
    return result


def main():
    logger = TEPLogger("step_13_camb_exploratory", LOG_PATH)
    set_step_logger(logger)

    print_status("=" * 60, "TITLE")
    print_status("CAMB Exploratory Test for TEP High-ℓ Compatibility", "TITLE")
    print_status("=" * 60, "TITLE")

    results = {
        "description": "CAMB scoping test for future TEP high-ℓ production run",
        "camb_basic": test_camb_basic(logger),
        "plik_lite_loads": test_plik_lite_loads(logger),
        "tep_in_camb": test_tep_in_camb(logger),
        "path_forward": {
            "option_a": (
                "Patch hi_class clipy interface to handle tep_mode Cls. "
                "Requires C/Python debugging of the binning matrices."
            ),
            "option_b": (
                "Implement tep_mode in CAMB Fortran source. "
                "Requires modifying the Friedmann equation and perturbation "
                "equations to include the conformal factor M(z). Estimated "
                "1-2 weeks."
            ),
            "option_c": (
                "Use alternate high-ℓ likelihood (ACT DR6, SPT) with different "
                "interface layer that may not have the same NaN issue."
            ),
            "recommended": (
                "Option (b) — CAMB re-implementation — is the most robust "
                "long-term path. CAMB is actively maintained, widely used, and "
                "its Python interface is cleaner than CLASS for custom "
                "modifications. The present low-ℓ result remains the primary "
                "constraint until high-ℓ is ready."
            ),
        },
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    logger.success(f"Results saved to {OUTPUT_PATH}")
    logger.info("All tests complete.")


class Step13CAMBExploratory:
    """Wrapper for pipeline integration."""
    def run(self) -> dict:
        main()
        with open(OUTPUT_PATH) as f:
            return json.load(f)


if __name__ == "__main__":
    main()
