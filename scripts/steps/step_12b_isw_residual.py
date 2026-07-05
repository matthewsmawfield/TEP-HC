#!/usr/bin/env python3
"""
Step 12b: ISW Residual vs Cosmic-Variance Floor (TEP-HC, Paper 18)
=================================================================

Concern: Does TEP predict an ISW signal at low-ℓ that exceeds the cosmic-variance
floor? If so, this is a testable low-ℓ prediction.

The ISW (Integrated Sachs-Wolfe) effect arises from time-varying gravitational
potentials along the line of sight. In standard ΛCDM, the ISW is sourced by
late-time dark-energy-driven potential decay. In TEP, the conformal background
factor A_dyn(z) modifies the effective Hubble friction and thus the growth of
potentials at late times.

This script estimates the TEP ISW amplitude relative to ΛCDM and compares the
predicted difference to the cosmic-variance floor at low-ℓ.

Required deliverable: JSON with ISW amplitude comparison and testability verdict.
"""

import sys
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = PROJECT_ROOT / "results" / "step_12b_isw_residual.json"
LOG_PATH = PROJECT_ROOT / "logs" / "step_12b_isw_residual.log"

sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.logger import TEPLogger, set_step_logger, print_status


def tep_isw_estimate(logger):
    """
    Analytic estimate of the ISW difference between TEP and ΛCDM.

    In ΛCDM, the ISW power at low-ℓ is proportional to the square of the
    integrated potential derivative:
        C_l^ISW ∝ [∫ dη (∂Φ/∂η) j_l(k(η_0-η))]^2

    The potential Φ is related to the density contrast via Poisson's equation
    and evolves according to the growth function D(z):
        Φ(z) ∝ D(z) / a(z)   (in the conformal Newtonian gauge)

    In TEP, the Jordan-frame scale factor is modified by M(z) = A_dyn/(1-α_A).
    At late times (z < z_t), A_dyn deviates from unity, altering the effective
    expansion history and thus the growth function D_TEP(z).

    We approximate the fractional change in the ISW amplitude by the fractional
    change in the late-time growth rate, using the TEP-HC homogeneous amplitude
    ε_T^HC = 0.0056 ± 0.0043 as the characteristic deviation scale.
    """
    logger.process("Computing ISW residual vs cosmic-variance floor...")

    # TEP homogeneous amplitude (from TEP-HC joint MCMC)
    epsilon_T = 0.0056
    epsilon_T_err = 0.0043

    # Approximate: the ISW amplitude scales roughly as the fractional deviation
    # in the late-time potential evolution. For small ε_T, the ISW modification
    # is O(ε_T) relative to ΛCDM.
    # This is a back-of-the-envelope scaling; a full Boltzmann integration would
    # be required for a precise number.
    delta_isw_fractional = 2.0 * epsilon_T  # ~1.1%

    # Cosmic variance at low-ℓ
    # For a single C_l at multipole ℓ, fractional cosmic variance is:
    #   σ(C_l) / C_l ≈ sqrt(2 / (2ℓ + 1))
    # The ISW contributes to the total C_l at low-ℓ at roughly the 10% level
    # in ΛCDM (Planck 2018). So the ISW-only cosmic variance is larger.
    # For a difference between two models, the detectability threshold is
    # approximately when |ΔC_l| > σ(C_l).

    ell_values = np.array([2, 3, 4, 5, 6, 7, 8, 9, 10])

    # Fractional cosmic variance for the total C_l at each ℓ
    cosmic_var_frac = np.sqrt(2.0 / (2.0 * ell_values + 1.0))

    # The ISW contributes ~10% of the total low-ℓ power in ΛCDM.
    # So the fractional cosmic variance for the ISW-only component is
    # approximately sqrt(2/(2ℓ+1)) / 0.1 = 10 * sqrt(2/(2ℓ+1)).
    # But for detecting a *difference* between TEP and ΛCDM, we compare the
    # fractional ISW difference to the fractional cosmic variance of the total C_l.
    isw_contribution_to_total = 0.10  # ~10% of total C_l at low ell

    # The predicted TEP ISW difference relative to the total C_l:
    delta_C_l_over_C_l = delta_isw_fractional * isw_contribution_to_total

    # Signal-to-noise for detecting the TEP ISW difference at each ℓ
    # S/N ≈ |ΔC_l| / σ(C_l) = (fractional difference) / (cosmic variance fraction)
    sn_per_ell = delta_C_l_over_C_l / cosmic_var_frac

    # Cumulative S/N over ℓ = 2–10 (approximate, assuming independence)
    sn_total = np.sqrt(np.sum(sn_per_ell**2))

    results = {
        "description": "ISW residual vs cosmic-variance floor for TEP vs ΛCDM",
        "assumptions": [
            "ISW amplitude scales with the fractional change in late-time potential evolution.",
            "TEP homogeneous amplitude ε_T^HC = 0.0056 ± 0.0043 sets the characteristic deviation scale.",
            "ISW contributes ~10% of total low-ℓ CMB power in ΛCDM.",
            "Cosmic variance for total C_l: σ/C_l ≈ sqrt(2/(2ℓ+1)).",
            "This is an analytic estimate; a full Boltzmann integration would refine the amplitude."
        ],
        "parameters": {
            "epsilon_T_HC": epsilon_T,
            "epsilon_T_HC_uncertainty": epsilon_T_err,
            "delta_isw_fractional": float(delta_isw_fractional),
            "isw_contribution_to_total_C_l": isw_contribution_to_total
        },
        "low_ell_analysis": {
            "ell_values": [int(e) for e in ell_values],
            "cosmic_variance_fraction": [float(cv) for cv in cosmic_var_frac],
            "predicted_delta_C_l_over_C_l": [float(delta_C_l_over_C_l) for _ in ell_values],
            "signal_to_noise_per_ell": [float(sn) for sn in sn_per_ell],
            "cumulative_signal_to_noise_ell2_10": float(sn_total)
        },
        "verdict": {
            "isw_detectable": bool(sn_total > 1.0),
            "required_snr_for_detection": 3.0,
            "predicted_snr": float(sn_total),
            "interpretation": (
                f"The predicted TEP ISW modification at low-ℓ has S/N ≈ {sn_total:.2f} "
                f"relative to the cosmic-variance floor. " +
                ("This is below the threshold for a confident detection (S/N > 3). "
                 if sn_total < 3.0 else
                 "This exceeds the threshold for detection. ") +
                "A full Boltzmann integration of the ISW power spectrum with the native "
                "hi_class tep_mode implementation is required for a definitive number. "
                "The present analytic estimate serves as a scoping calculation."
            )
        }
    }

    return results


def main():
    logger = TEPLogger("step_12b_isw_residual", LOG_PATH)
    set_step_logger(logger)

    print_status("=" * 60, "TITLE")
    print_status("ISW Residual vs Cosmic-Variance Floor", "TITLE")
    print_status("=" * 60, "TITLE")

    results = tep_isw_estimate(logger)

    logger.info(f"TEP homogeneous amplitude: ε_T^HC = {results['parameters']['epsilon_T_HC']}")
    logger.info(f"Predicted fractional ISW change: {results['parameters']['delta_isw_fractional']:.4f}")
    logger.info("Low-ℓ cosmic variance and predicted signal:")
    for i, ell in enumerate(results["low_ell_analysis"]["ell_values"]):
        cv = results["low_ell_analysis"]["cosmic_variance_fraction"][i]
        sn = results["low_ell_analysis"]["signal_to_noise_per_ell"][i]
        logger.info(f"  ℓ = {ell:2d}: cosmic-var frac = {cv:.3f}, S/N = {sn:.3f}")

    logger.info(f"Cumulative S/N (ℓ = 2–10): {results['low_ell_analysis']['cumulative_signal_to_noise_ell2_10']:.3f}")
    logger.info(f"Verdict: {results['verdict']['interpretation']}")

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(results, f, indent=2)

    logger.success(f"Results written to {OUTPUT_PATH}")


class Step12bISWResidual:
    """Wrapper for pipeline integration."""
    def run(self) -> dict:
        main()
        with open(OUTPUT_PATH) as f:
            return json.load(f)


if __name__ == "__main__":
    main()
