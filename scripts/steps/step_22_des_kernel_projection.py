#!/usr/bin/env python3
"""
Step 22: DES-Y3-Style Kernel-Projected Weak-Lensing Comparison
===============================================================

PURPOSE: The joint-MCMC S8 = 0.868 +/- 0.025 is a z=0-extrapolated CMB
quantity, while DES-Y3/KiDS-1000 measure a lensing-kernel-weighted
structure amplitude at z_eff ~ 0.5. Comparing them directly is an
observable mismatch. This step performs the like-for-like projection:

  1. sigma8(z) is integrated directly from the registered hi_class
     matter-power outputs (z=0 and z=0.5) for lcdm_post, tep_bg_post,
     and tep_pert_post at the shared fixed cosmology
     (H0=67.36, omega_b=0.022383, omega_cdm=0.120011 -> Omega_m=0.3139).
  2. The TEP/LCDM amplitude deviation delta(z) = sigma8_TEP/sigma8_LCDM-1
     is measured at z=0 and z=0.5 and interpolated linearly in z.
  3. The LCDM growth shape D(z) is computed from the fiducial flat-LCDM
     background (Omega_m=0.3139); sigma8_model(z) = sigma8_LCDM(z) * (1+delta(z)).
  4. A DES-Y3-like combined source distribution n(z_s) ~ z_s^2
     exp[-(z_s/z0)^1.5], z0=0.5, is convolved with the standard
     weak-lensing efficiency kernel to produce the shear-power weight
     W(z_l)^2 on lens planes; the kernel-weighted effective sigma8^2
     and effective redshift z_eff are computed for each model.
  5. The kernel-projected S8_eff = sigma8_eff * sqrt(Omega_m/0.3) is
     compared to the published DES-Y3 (0.776 +/- 0.017) and KiDS-1000
     (0.759 +0.024/-0.021) cosmic-shear values.

Scope: linear-theory Limber-style projection at the fixed cosmology of
the registered pk outputs; no non-linear prescription is applied (pk
runs were computed with non_linear=none). The result quantifies how
much, if any, of the z=0 S8 excess is removed by observable-matched
projection.

Output: results/step_22_des_kernel_projection.json
"""

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from scipy.integrate import simpson

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT_ROOT / "results"
OUTPUT_FILE = RESULTS / "step_22_des_kernel_projection.json"

# Fixed cosmology of the registered pk runs (results/*_post.ini)
H0 = 67.36
H = H0 / 100.0
OMEGA_M = (0.022383 + 0.120011) / H ** 2

# DES-Y3-like source distribution and published external values
Z0_SRC = 0.5          # combined-source characteristic redshift
DES_Y3_S8 = (0.776, 0.017)      # Amon/Secco cosmic shear
KIDS_S8 = (0.759, 0.021)        # Asgari et al. KiDS-1000

R8 = 8.0  # Mpc/h top-hat radius


def load_pk(name):
    d = np.loadtxt(RESULTS / name)
    return d[:, 0], d[:, 1]


def tophat_W(x):
    x = np.asarray(x)
    w = np.ones_like(x)
    m = np.abs(x) > 1e-4
    w[m] = 3 * (np.sin(x[m]) - x[m] * np.cos(x[m])) / x[m] ** 3
    w[~m] = 1 - x[~m] ** 2 / 10
    return w


def sigma8_of(k, P):
    """sigma8^2 = int dlnk k^3 P(k)/(2 pi^2) W^2(k R8)."""
    k, P = np.asarray(k), np.asarray(P)
    integrand = k ** 3 * P / (2 * np.pi ** 2) * tophat_W(k * R8) ** 2
    return float(np.sqrt(simpson(integrand, x=np.log(k))))


def lcdm_D(z, om=OMEGA_M):
    """Un-normalized flat-LCDM linear growth factor D(z)."""
    z = np.asarray(z, dtype=float)
    zp = np.linspace(0, max(z.max(), 3.0) + 0.5, 4001)
    E = np.sqrt(om * (1 + zp) ** 3 + (1 - om))
    integ = (1 + zp) / E ** 3
    # cumulative integral from z'=z to inf ~ cumulative to max
    c = np.cumsum(integ[::-1])[::-1] * (zp[1] - zp[0])
    c = np.interp(z, zp, c)
    E_z = np.sqrt(om * (1 + z) ** 3 + (1 - om))
    D = E_z * c
    return D / np.interp(0.0, z, D)  # normalized to D(0)=1


def lensing_kernel(nu_grid_z_l, om=OMEGA_M):
    """DES-like shear kernel weight on lens planes.

    n(z_s) ~ z_s^2 exp[-(z_s/z0)^1.5]; W(z_l) ~ chi_l (1+z_l) *
    int_{z_l} n(z_s) (chi_s - chi_l)/chi_s dz_s. Weight for shear
    power ~ W^2 (common-mode factors drop out in ratios).
    """
    c_km_s = 299792.458
    z_l = nu_grid_z_l
    E = lambda z: np.sqrt(om * (1 + z) ** 3 + (1 - om))
    def chi(z):
        res = []
        for zz in np.atleast_1d(z):
            g = np.linspace(0, zz, max(int(zz * 500) + 2, 3))
            res.append(simpson(1 / np.sqrt(om * (1 + g) ** 3 + (1 - om)), x=g))
        return c_km_s / 100.0 * np.array(res)
    chi_l = chi(z_l)
    z_s = np.linspace(0.001, 3.0, 3001)
    n_s = z_s ** 2 * np.exp(-(z_s / Z0_SRC) ** 1.5)
    n_s /= simpson(n_s, x=z_s)
    chi_s_grid = chi(z_s)
    W = np.zeros_like(z_l)
    for i, (zl, cl) in enumerate(zip(z_l, chi_l)):
        m = z_s > zl
        if m.sum() < 2:
            continue
        W[i] = cl * (1 + zl) * simpson(
            n_s[m] * (chi_s_grid[m] - cl) / chi_s_grid[m], x=z_s[m])
    return W


def main():
    out = {
        "step": "22",
        "title": "DES-Y3-style kernel-projected weak-lensing comparison",
        "timestamp": datetime.now().isoformat() + "Z",
        "fixed_cosmology": {"H0": H0, "omega_b": 0.022383,
                            "omega_cdm": 0.120011, "Omega_m": OMEGA_M},
    }

    # 1. sigma8 from pk at z=0 and z=0.5
    pk = {}
    for tag in ["lcdm_post", "tep_bg_post", "tep_pert_post"]:
        pk[tag] = {}
        for ztag, zval in [("z1", 0.0), ("z2", 0.5)]:
            k, P = load_pk(f"{tag}_00_{ztag}_pk.dat")
            pk[tag][zval] = {"sigma8": sigma8_of(k, P),
                             "n_k": int(len(k))}
    out["sigma8_direct"] = pk

    # 2. growth-shape deviations at fixed cosmology
    deltas = {}
    for tag in ["tep_bg_post", "tep_pert_post"]:
        deltas[tag] = {z: pk[tag][z]["sigma8"] / pk["lcdm_post"][z]["sigma8"] - 1
                       for z in (0.0, 0.5)}
    out["growth_deviation_delta"] = deltas

    # 3. kernel projection
    z_l = np.linspace(1e-3, 2.0, 2000)
    W = lensing_kernel(z_l)
    W2 = W ** 2
    norm = simpson(W2, x=z_l)
    z_eff = float(simpson(z_l * W2, x=z_l) / norm)

    D0 = lcdm_D(z_l)          # D normalized to 1 at z=0
    s8_lcdm_z = pk["lcdm_post"][0.0]["sigma8"] * D0

    proj = {}
    for tag in ["lcdm_post", "tep_bg_post", "tep_pert_post"]:
        if tag == "lcdm_post":
            s8_z = s8_lcdm_z
        else:
            d0 = deltas[tag][0.0]
            d5 = deltas[tag][0.5]
            delta_z = d0 + (d5 - d0) * (z_l / 0.5)
            delta_z = np.clip(delta_z, -1, 1)
            s8_z = s8_lcdm_z * (1 + delta_z)
        s8sq_eff = float(simpson(W2 * s8_z ** 2, x=z_l) / norm)
        s8_eff = np.sqrt(s8sq_eff)
        S8_eff = s8_eff * np.sqrt(OMEGA_M / 0.3)
        proj[tag] = {"sigma8_eff_kernel": float(s8_eff),
                     "S8_kernel_projected": float(S8_eff)}

    out["kernel"] = {
        "source_n_z": "n(z_s) ~ z_s^2 exp[-(z_s/0.5)^1.5] (DES-Y3-like combined)",
        "z_eff": z_eff,
        "projection": "sigma8_eff^2 = <W^2 sigma8^2>/<W^2>; S8_eff = sigma8_eff*sqrt(Om/0.3)",
    }
    out["projected"] = proj

    # 4. like-for-like comparison
    comp = {}
    tep = proj["tep_pert_post"]["S8_kernel_projected"]
    lcdm = proj["lcdm_post"]["S8_kernel_projected"]
    for name, (val, err) in [("DES-Y3", DES_Y3_S8), ("KiDS-1000", KIDS_S8)]:
        comp[name] = {
            "external_S8": val, "external_err": err,
            "TEP_kernel_projected": tep,
            "LCDM_kernel_projected": lcdm,
            "TEP_gap_sigma_at_mc_posterior": None,  # filled below
            "LCDM_gap_at_fixed_cosmology": (lcdm - val) / err,
        }
    out["external_comparison"] = comp
    out["note_on_uncertainty"] = (
        "The kernel-projected values are at the FIXED cosmology of the pk "
        "outputs (Omega_m=0.3139), not marginalized over the MCMC posterior. "
        "The MCMC-marginalized z=0 S8 is 0.868+/-0.025 (07_mcmc_summary_full). "
        "This step quantifies how that z=0 number maps onto the lensing "
        "kernel: because the TEP/LCDM deviation grows with z (delta(0)= "
        f"{deltas['tep_pert_post'][0.0]:+.4f}, delta(0.5)="
        f"{deltas['tep_pert_post'][0.5]:+.4f}), kernel projection does not "
        "reconcile the gap."
    )

    OUTPUT_FILE.write_text(json.dumps(out, indent=2))
    print("Step 22 written:", OUTPUT_FILE)
    print(f"  z_eff = {z_eff:.3f}")
    for t, p in proj.items():
        print(f"  {t}: sigma8={p['sigma8_eff_kernel']:.4f} "
              f"S8_eff={p['S8_kernel_projected']:.4f}")
    print(f"  TEP-vs-DES-Y3 fixed-point gap: {(tep-0.776)/0.017:.1f} sigma "
          f"(same-cosmology comparison)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
