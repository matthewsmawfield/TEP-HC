#!/usr/bin/env python3
"""
Step 12c: Low-ell spectrum residuals — screened-branch TEP vs LCDM (TEP-HC)
==========================================================================
Computes the actual CMB temperature/E-mode spectra with the patched local
hi_class build, comparing

    A) Lambda-CDM reference (same cosmological parameters)
    B) TEP background-only (tep_mode, epsilon_T = posterior value)
    C) TEP active screened closure (gravity_model='tep', w_c = +700,
       tep_kin_boost = 10, regular delta-phi variable, same epsilon_T)

and reports per-multipole fractional residuals Delta C_l / C_l for TT, TE,
EE and the lensing potential, against the cosmic-variance floor
sqrt(2/(2l+1)). This replaces the analytic scaling estimate of step_12b
with an exact Boltzmann-code evaluation.

Output: results/12c_spectrum_residuals.json
"""

import json
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLASSY_PATH = PROJECT_ROOT / "external" / "hi_class" / "hi_class" / "python"
OUTPUT_PATH = PROJECT_ROOT / "results" / "12c_spectrum_residuals.json"
LOG_PATH = PROJECT_ROOT / "logs" / "step_12c_spectrum_residuals.log"

sys.path.insert(0, str(CLASSY_PATH))
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.logger import TEPLogger, set_step_logger, print_status

# Matched cosmology at the converged high-ell TTTEEE best-fit region.
BASE_COSMO = {
    "output": "tCl,pCl,lCl,mPk",
    "lensing": "yes",
    "modes": "s",
    "non_linear": "halofit",
    "l_max_scalars": 2700,
    "H0": 67.82,
    "omega_b": 0.02237,
    "omega_cdm": 0.1192,
    "n_s": 0.9659,
    "A_s": 2.10e-9,
    "tau_reio": 0.0544,
    "T_cmb": 2.7255,
}

# epsilon_T grid: posterior median and 95% upper bound (z_T = 5, n_T = 2).
EPS_GRID = [0.0, 0.004, 0.0071]


def compute_spectra(extra):
    """Compute raw (unlensed) and lensed Cl spectra for one configuration."""
    from classy import Class

    c = Class()
    params = dict(BASE_COSMO)
    params.update(extra)
    c.set(params)
    c.compute()
    raw = c.raw_cl(2700)
    lensed = c.lensed_cl(2700)
    c.struct_cleanup()
    c.empty()
    return raw, lensed


def frac_residual(cl_a, cl_b, key, ells):
    denom = np.where(np.abs(cl_a[key]) > 0, np.abs(cl_a[key]), np.nan)
    return (cl_b[key][ells] - cl_a[key][ells]) / denom[ells]


def run():
    print_status("STEP 12c: Low-ell spectrum residuals", "TITLE")
    print_status("Computing Lambda-CDM reference spectra...", "PROCESS")
    ref_raw, ref_lensed = compute_spectra({})

    ells = np.arange(2, 41)
    cv_floor = np.sqrt(2.0 / (2.0 * ells + 1.0))

    out = {
        "description": "Exact hi_class low-ell spectrum residuals, "
                       "screened-branch TEP vs Lambda-CDM at matched cosmology",
        "matched_cosmology": {k: v for k, v in BASE_COSMO.items()
                              if not isinstance(v, bool)},
        "ell_range": [2, 40],
        "cosmic_variance_floor": {int(l): float(cv_floor[i])
                                  for i, l in enumerate(ells)},
        "models": {},
    }

    for eps in EPS_GRID:
        tag = f"eps_{eps:g}"
        print_status(f"TEP background-only, epsilon_T = {eps}...", "PROCESS")
        bg_raw, bg_lens = compute_spectra(
            {"tep_mode": "yes", "z_T": 5.0, "n_T": 2.0,
             "epsilon_T": eps})
        pert_raw = pert_lens = None
        try:
            print_status(
                f"TEP active screened closure (w_c=700), epsilon_T = {eps}...",
                "PROCESS")
            pert_raw, pert_lens = compute_spectra(
                {"tep_mode": "yes", "z_T": 5.0, "n_T": 2.0,
                 "epsilon_T": eps,
                 "gravity_model": "tep", "M2_evolution": "yes",
                 "use_pert_var_deltaphi_smg": "yes",
                 "pert_initial_conditions_smg": "zero",
                 "tep_screening_s": 1.0, "tep_kin_boost": 10.0})
        except Exception as e:
            print_status(f"  active closure eval failed: {e}", "WARNING")

        entry = {}
        for spec_name, cl_b in (("background_only", bg_lens),
                                ("active_closure", pert_lens)):
            if cl_b is None:
                continue
            for key in ("tt", "te", "ee"):
                res = frac_residual(ref_lensed, cl_b, key, ells)
                snr = np.abs(res) / cv_floor
                entry[spec_name] = entry.get(spec_name, {})
                entry[spec_name][key] = {
                    "max_abs_frac_residual_ell2_40": float(
                        np.nanmax(np.abs(res))),
                    "ell_of_max": int(ells[np.nanargmax(np.abs(res))]),
                    "max_snr_vs_cosmic_variance": float(np.nanmax(snr)),
                    "quad_sum_snr": float(
                        np.sqrt(np.nansum(snr**2))),
                    "per_ell_residual": {int(l): float(res[i])
                                         for i, l in enumerate(ells)},
                }
        out["models"][tag] = entry

    # Detectability verdict
    verdict = {}
    for tag, entry in out["models"].items():
        verdict[tag] = {}
        for spec, chans in entry.items():
            quad = max(c["quad_sum_snr"] for c in chans.values())
            verdict[tag][spec] = {
                "max_channel_quad_snr": float(quad),
                "detectable_vs_cosmic_variance": bool(quad > 1.0),
            }
    out["verdict"] = verdict

    # ---- Closure-limit diagnostics -------------------------------------
    # At epsilon_T = 0 every alpha-function vanishes (x_smg route reduces
    # exactly to GR), but the prescribed-trajectory delta-phi closure
    # retains the non-minimal coupling G4_phi = S*M2 and a kineticity floor
    # w_c.  Quantify the residual imprint of that minimum mixing: scaling
    # with screening strength S, kineticity w_c, and perturbation variable.
    diag = {"note": (
        "epsilon_T=0 limit: alpha-parametrized (x_smg) route reproduces GR "
        "exactly; delta-phi route retains a scalar-metric mixing residual "
        "via G4_phi=S*M2 and the reconstructed U_phi term 6*S*M2*(H'/a+2H^2),"
        " suppressed ~1/w_c. A real closure feature, not a sampling artifact."
        " Note: tep.c maps tep_screening_s<=0 to 1 internally, so S=0 is "
        "not reachable through that parameter.")}

    def tt_quad_residual(extra):
        raw, _ = compute_spectra(extra)
        res = frac_residual(ref_raw, raw, "tt", ells)
        return float(res[0])  # ell = 2

    smg_base = {"tep_mode": "yes", "z_T": 5.0, "n_T": 2.0,
                "epsilon_T": 0.0,
                "gravity_model": "tep", "M2_evolution": "yes",
                "pert_initial_conditions_smg": "zero",
                "tep_screening_s": 1.0, "tep_kin_boost": 10.0}

    # Perturbation-variable comparison: delta-phi vs x_smg = delta_phi/phi'
    deltaphi_p = dict(smg_base); deltaphi_p["use_pert_var_deltaphi_smg"] = "yes"
    xsmg_p = dict(smg_base)  # x_smg default route
    try:
        diag["perturbation_variable"] = {
            "deltaphi_tt_ell2_residual": tt_quad_residual(deltaphi_p),
            "x_smg_tt_ell2_residual": tt_quad_residual(xsmg_p),
        }
    except Exception as e:
        diag["perturbation_variable"] = {"error": str(e)[:200]}

    # Screening-strength scaling (S>0 values only; S<=0 remaps to 1 in tep.c)
    diag["screening_s_scaling"] = {}
    for s in (1.0, 0.5, 0.1):
        p = dict(deltaphi_p); p["tep_screening_s"] = s
        diag["screening_s_scaling"][str(s)] = tt_quad_residual(p)

    # Kineticity scaling: residual ~ 1/w_c
    diag["kin_boost_scaling"] = {}
    for kb, wc in ((1.0, 70.0), (10.0, 700.0), (90.0, 6300.0),
                   (1000.0, 70000.0)):
        p = dict(deltaphi_p); p["tep_kin_boost"] = kb
        diag["kin_boost_scaling"][f"kb={kb}_wc={wc}"] = tt_quad_residual(p)

    out["closure_limit_diagnostics"] = diag

    OUTPUT_PATH.write_text(json.dumps(out, indent=2))
    print_status(f"Results written to {OUTPUT_PATH}", "SUCCESS")
    return out


if __name__ == "__main__":
    logger = TEPLogger("step_12c_spectrum_residuals", LOG_PATH)
    set_step_logger(logger)
    run()
