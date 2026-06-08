#!/usr/bin/env python3
"""
Analyze A_planck sensitivity run
================================
Compares the loosened-prior chain (A_planck in [0.9, 1.25]) against the
baseline chain (A_planck in [0.9, 1.1]) to answer reviewer question:
  - Does loosening stabilize H0 error bars?
  - Does it induce a degeneracy cascade with epsilon_T?

Outputs JSON to results/07b_aplanck_sensitivity.json
"""

import sys
import json
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

CHAIN_BASE = PROJECT_ROOT / "results" / "mcmc_chains" / "tep_hiclass_suite.1.txt"
CHAIN_SENS = PROJECT_ROOT / "results" / "mcmc_chains" / "tep_hiclass_aplanck_sens.1.txt"
OUT_JSON = PROJECT_ROOT / "results" / "07b_aplanck_sensitivity.json"

def load_chain(path):
    with open(path) as f:
        header = f.readline().strip()
    cols = [c.strip() for c in header[1:].split()]
    cmap = {name: i for i, name in enumerate(cols)}
    data = np.loadtxt(path)
    return data, cmap

def weighted_stats(x, w):
    wsum = np.sum(w)
    mean = np.sum(w * x) / wsum
    var = np.sum(w * (x - mean)**2) / wsum
    return float(mean), float(np.sqrt(var))

def weighted_correlation(x, y, w):
    mx, sx = weighted_stats(x, w)
    my, sy = weighted_stats(y, w)
    cov = np.sum(w * (x - mx) * (y - my)) / np.sum(w)
    return cov / (sx * sy)

def analyze(data, cmap, label):
    burn = int(0.3 * data.shape[0])
    post = data[burn:]
    w = post[:, 0]
    params = ["A_planck", "H0", "epsilon_T", "n_s", "omega_b", "omega_cdm", "tau_reio", "sigma8"]
    out = {"label": label, "n_samples": int(post.shape[0])}
    for p in params:
        idx = cmap[p]
        col = post[:, idx]
        mn, std = weighted_stats(col, w)
        out[p] = {"mean": mn, "std": std, "min": float(col.min()), "max": float(col.max())}
    # correlations
    a = post[:, cmap["A_planck"]]
    h = post[:, cmap["H0"]]
    e = post[:, cmap["epsilon_T"]]
    out["corr_Aplanck_H0"] = float(weighted_correlation(a, h, w))
    out["corr_Aplanck_epsilonT"] = float(weighted_correlation(a, e, w))
    out["corr_H0_epsilonT"] = float(weighted_correlation(h, e, w))
    return out

def main():
    results = {"status": "RUNNING", "baseline": None, "sensitivity": None, "comparison": None}

    if not CHAIN_BASE.exists():
        raise FileNotFoundError(f"Baseline chain not found: {CHAIN_BASE}")
    if not CHAIN_SENS.exists():
        raise FileNotFoundError(f"Sensitivity chain not found: {CHAIN_SENS}. Run scripts/diagnostics/run_aplanck_sensitivity_mcmc.py first.")

    base_data, base_map = load_chain(CHAIN_BASE)
    sens_data, sens_map = load_chain(CHAIN_SENS)

    results["baseline"] = analyze(base_data, base_map, "baseline [0.9,1.1]")
    results["sensitivity"] = analyze(sens_data, sens_map, "loosened [0.9,1.25]")

    # comparison
    b = results["baseline"]
    s = results["sensitivity"]
    comp = {}
    for p in ["A_planck", "H0", "epsilon_T", "n_s", "omega_b", "omega_cdm", "tau_reio", "sigma8"]:
        dmean = s[p]["mean"] - b[p]["mean"]
        dstd = s[p]["std"] - b[p]["std"]
        comp[p] = {
            "delta_mean": round(dmean, 6),
            "delta_std": round(dstd, 6),
            "baseline_mean_std": f"{b[p]['mean']:.4f} ± {b[p]['std']:.4f}",
            "sensitivity_mean_std": f"{s[p]['mean']:.4f} ± {s[p]['std']:.4f}",
        }
    results["comparison"] = comp
    results["status"] = "SUCCESS"

    with open(OUT_JSON, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Saved comparison to {OUT_JSON}")
    print("\nKey results:")
    for p in ["A_planck", "H0", "epsilon_T"]:
        c = comp[p]
        print(f"  {p}: {c['baseline_mean_std']} → {c['sensitivity_mean_std']}  (Δmean={c['delta_mean']:+.5f}, Δstd={c['delta_std']:+.5f})")
    print(f"\nCorrelations in sensitivity run:")
    print(f"  corr(A_planck, H0)        = {s['corr_Aplanck_H0']:+.4f}")
    print(f"  corr(A_planck, epsilon_T)  = {s['corr_Aplanck_epsilonT']:+.4f}")
    print(f"  corr(H0, epsilon_T)        = {s['corr_H0_epsilonT']:+.4f}")

if __name__ == "__main__":
    main()
