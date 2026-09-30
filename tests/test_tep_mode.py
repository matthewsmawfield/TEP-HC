#!/usr/bin/env python3
"""
pytest unit-test suite for TEP-HC native hi_class implementation
===============================================================

Tests that tep_mode reduces to ΛCDM when ε_T = 0 and that the patched
hi_class produces numerically stable outputs.

Run with:
    cd TEP-HC && python -m pytest tests/test_tep_mode.py -v
"""

import sys
import os
from pathlib import Path
import numpy as np
import pytest

# Ensure patched hi_class is on PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
HICLASS_PYTHON = PROJECT_ROOT / "external" / "hi_class" / "hi_class" / "python"
os.environ["PYTHONPATH"] = str(HICLASS_PYTHON) + os.pathsep + os.environ.get("PYTHONPATH", "")
sys.path.insert(0, str(HICLASS_PYTHON))

# Common CLASS parameters (Planck 2018 best-fit)
BASE_PARAMS = {
    "output": "tCl,pCl,lCl,mPk",
    "lensing": "yes",
    "modes": "s",
    "l_max_scalars": 100,
    "non_linear": "none",
    "H0": 67.4,
    "omega_b": 0.0224,
    "omega_cdm": 0.120,
    "A_s": 2.1e-9,
    "n_s": 0.965,
    "tau_reio": 0.054,
}


def run_classy(params, ell_max=100):
    """Run CLASS/hi_class with given parameters."""
    try:
        import classy
    except ImportError as e:
        pytest.skip(f"classy not available: {e}")

    cosmo = classy.Class()
    cosmo.set(params)
    cosmo.compute()
    cls = cosmo.lensed_cl(ell_max)
    cls["sigma8"] = cosmo.sigma8()
    cosmo.struct_cleanup()
    cosmo.empty()
    return cls


class TestTepModeLambdaCDM:
    """Test that tep_mode with ε_T = 0 reproduces ΛCDM."""

    def test_tep_mode_zero_epsilon_matches_lcdm(self):
        """
        When tep_mode='yes' and epsilon_T=0, the TEP background modification
        vanishes and the output must match standard ΛCDM to high precision.
        """
        # Standard ΛCDM
        lcdm_params = dict(BASE_PARAMS)
        lcdm_cls = run_classy(lcdm_params)

        # TEP with ε_T = 0
        tep_params = dict(BASE_PARAMS)
        tep_params.update({
            "tep_mode": "yes",
            "z_T": 5.0,
            "n_T": 2.0,
            "epsilon_T": 0.0,
        })
        tep_cls = run_classy(tep_params)

        # Compare TT spectra
        tt_lcdm = lcdm_cls["tt"][2:]
        tt_tep = tep_cls["tt"][2:]

        # Relative difference
        rel_diff = np.abs(tt_tep - tt_lcdm) / (np.abs(tt_lcdm) + 1e-30)
        max_rel_diff = np.max(rel_diff)

        # They should agree to within 1e-4 (100 ppm) everywhere
        assert max_rel_diff < 1e-4, (
            f"tep_mode with ε_T=0 deviates from ΛCDM by {max_rel_diff:.3e} "
            f"in TT (max allowed 1e-4)"
        )

    def test_tep_mode_nonzero_epsilon_changes_cls(self):
        """
        With ε_T ≠ 0, the Cls must differ from ΛCDM (non-degeneracy test).
        """
        lcdm_params = dict(BASE_PARAMS)
        lcdm_cls = run_classy(lcdm_params)

        tep_params = dict(BASE_PARAMS)
        tep_params.update({
            "tep_mode": "yes",
            "z_T": 5.0,
            "n_T": 2.0,
            "epsilon_T": 0.01,
        })
        tep_cls = run_classy(tep_params)

        tt_lcdm = lcdm_cls["tt"][2:]
        tt_tep = tep_cls["tt"][2:]

        # Must differ by more than 1e-6 somewhere (i.e., non-zero effect)
        rel_diff = np.abs(tt_tep - tt_lcdm) / (np.abs(tt_lcdm) + 1e-30)
        assert np.max(rel_diff) > 1e-6, (
            "tep_mode with ε_T=0.01 produces no detectable change in Cls"
        )

    def test_tep_mode_preserves_acoustic_scale(self):
        """
        The first acoustic peak position must be preserved to within 0.5%.
        """
        lcdm_params = dict(BASE_PARAMS)
        lcdm_params["l_max_scalars"] = 2700
        lcdm_cls = run_classy(lcdm_params)

        tep_params = dict(BASE_PARAMS)
        tep_params.update({
            "tep_mode": "yes",
            "z_T": 5.0,
            "n_T": 2.0,
            "epsilon_T": 0.005,
        })
        tep_params["l_max_scalars"] = 2700
        tep_cls = run_classy(tep_params)

        tt_lcdm = lcdm_cls["tt"][2:]
        tt_tep = tep_cls["tt"][2:]

        # Find first peak
        l_lcdm = np.argmax(tt_lcdm[20:200]) + 20
        l_tep = np.argmax(tt_tep[20:200]) + 20

        peak_shift = abs(l_tep - l_lcdm) / l_lcdm
        assert peak_shift < 0.005, (
            f"First acoustic peak shifted by {peak_shift:.3%} (max 0.5%)"
        )

    def test_tep_mode_does_not_crash_with_varied_zT(self):
        """
        Stability sweep over z_T values.
        """
        for z_T in [1.0, 5.0, 10.0, 50.0, 100.0]:
            tep_params = dict(BASE_PARAMS)
            tep_params.update({
                "tep_mode": "yes",
                "z_T": z_T,
                "n_T": 2.0,
                "epsilon_T": 0.01,
            })
            try:
                cls = run_classy(tep_params)
                assert cls["tt"] is not None
            except Exception as e:
                pytest.fail(f"tep_mode crashed with z_T={z_T}: {e}")


class TestCdmLensingScope:
    """
    Fixed-posterior-point CDM-free lensing scope diagnostic (step 21).

    At the published active posterior, removing the standard CDM fluid must
    collapse C_l^{phiphi} in the CURRENT implementation (pure-conformal scalar
    sector with rho_smg = 0 and alpha functions ~ epsilon_T). These assertions
    guard the manuscript's claim-status wording: if a future closure makes the
    scalar sector source a CDM-level lensing potential, these bounds will fail
    and the manuscript claims must be revisited, not just the test.
    """

    POSTERIOR_PARAMS = dict(
        BASE_PARAMS, l_max_scalars=500, non_linear="none",
        H0=66.77, omega_b=0.02144, n_s=0.9956,
        tau_reio=0.0497, tep_mode="yes", z_T=5.0,
        n_T=2.0, epsilon_T=0.00547,
    )

    def _check_lensing_depends_on_cdm(self, extra_params):
        params = dict(self.POSTERIOR_PARAMS, **extra_params)
        with_cdm = run_classy(dict(params, omega_cdm=0.1155), 500)
        without_cdm = run_classy(dict(params, omega_cdm=0.0), 500)
        assert 0 < without_cdm["pp"][100] < 0.3 * with_cdm["pp"][100]
        assert 0 < without_cdm["pp"][400] < 0.1 * with_cdm["pp"][400]
        assert 0 < without_cdm["sigma8"] < 0.3 * with_cdm["sigma8"]

    def test_background_only_lensing_depends_on_cdm_fluid(self):
        self._check_lensing_depends_on_cdm({})

    def test_active_perturbation_lensing_depends_on_cdm_fluid(self):
        self._check_lensing_depends_on_cdm(
            {"gravity_model": "tep", "M2_evolution": "yes"}
        )


class TestStability:
    """Numerical stability tests."""

    def test_no_nan_in_output(self):
        """
        Output spectra must contain no NaN or Inf.
        """
        tep_params = dict(BASE_PARAMS)
        tep_params.update({
            "tep_mode": "yes",
            "z_T": 5.0,
            "n_T": 2.0,
            "epsilon_T": 0.01,
        })
        tep_params["l_max_scalars"] = 500
        cls = run_classy(tep_params)

        for key in ["tt", "ee", "te"]:
            arr = cls.get(key, [])
            if len(arr) > 0:
                assert not np.any(np.isnan(arr)), f"NaN found in {key}"
                assert not np.any(np.isinf(arr)), f"Inf found in {key}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
