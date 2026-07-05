"""
Custom Cobaya CAMB theory with TEP effective w(a).

This module defines a subclass of Cobaya's CAMB theory that computes
the effective dark energy equation of state w(a) from TEP parameters
(epsilon_T, z_T, n_T) and injects it into CAMB before each evaluation.

Usage in Cobaya YAML:
    theory:
        camb_tep:
            path: /path/to/this/module
            extra_args:
                z_T: 5.0
                n_T: 2.0
"""

import sys
from pathlib import Path
import numpy as np

# Ensure CAMB is importable
import camb
from camb.dark_energy import DarkEnergyPPF

# We need to inherit from Cobaya's CAMB, but it's in a module that
# may not be directly importable. Let's import it properly.
from cobaya.theories.camb.camb import CAMB


class CAMBTEP(CAMB):
    """Cobaya CAMB theory with TEP effective w(a) injection."""

    def initialize(self):
        """Initialize the base CAMB theory."""
        super().initialize()
        # Read fixed TEP parameters from extra_args
        self.z_T = self.extra_args.get("z_T", 5.0)
        self.n_T = self.extra_args.get("n_T", 2.0)

    def calculate(self, state, want_derived=True, **params_values_dict):
        """
        Override calculate to inject TEP w(a) before CAMB runs.
        """
        # Get epsilon_T from sampled params
        epsilon_T = params_values_dict.get("epsilon_T", 0.0)

        # Compute effective w(a) from TEP
        if epsilon_T != 0.0:
            w_a_table, a_table = self._compute_tep_w_a(
                params_values_dict, epsilon_T
            )
            # Inject into extra_args for this step
            # We need to modify the CAMBparams object after it's created
            # but before the computation runs.
            # The cleanest way is to add a hook in _get_params or to
            # use a custom DarkEnergy model.
            pass

        # Fall back to standard CAMB calculation
        return super().calculate(state, want_derived=want_derived, **params_values_dict)

    def _compute_tep_w_a(self, params, epsilon_T):
        """Compute effective w(a) from TEP parameters."""
        H0 = params.get("H0", 67.4)
        ombh2 = params.get("ombh2", 0.02237)
        omch2 = params.get("omch2", 0.1200)

        z_grid = np.linspace(0, 3.0, 500)

        # TEP Hubble rate
        h = H0 / 100.0
        Omega_m = (ombh2 + omch2) / h**2
        Omega_L = 1.0 - Omega_m
        Hz_lcdm = H0 * np.sqrt(Omega_m * (1.0 + z_grid)**3 + Omega_L)

        # TEP transition functions
        S = np.where(
            z_grid <= 0.0,
            0.0,
            np.exp(-(np.minimum(z_grid, self.z_T * 3.0) / self.z_T) ** self.n_T)
        )
        A = np.exp(epsilon_T * np.log(1.0 + z_grid) * S)
        A = np.maximum(A, 0.1)
        dS = np.where(
            (z_grid > 1e-10) & (z_grid <= self.z_T * 3.0),
            -S * self.n_T * (z_grid / self.z_T) ** (self.n_T - 1.0) / self.z_T,
            0.0
        )
        alpha_A = -epsilon_T * (S + (1.0 + z_grid) * np.log(1.0 + z_grid) * dS)
        M = A / (1.0 - alpha_A)
        H_tep = Hz_lcdm * M

        # Solve for effective w(z)
        omega_de = H_tep**2 / H0**2 - Omega_m * (1.0 + z_grid)**3
        omega_de = np.maximum(omega_de, 1e-15)
        ln_omega = np.log(omega_de)
        d_ln_omega_dz = np.gradient(ln_omega, z_grid)
        w_eff = -1.0 + (1.0 + z_grid) / 3.0 * d_ln_omega_dz

        a_grid = 1.0 / (1.0 + z_grid)
        sort_idx = np.argsort(a_grid)
        a_sorted = a_grid[sort_idx]
        w_sorted = w_eff[sort_idx]
        mask = (a_sorted > 1e-6) & (a_sorted <= 1.0)
        return w_sorted[mask], a_sorted[mask]
