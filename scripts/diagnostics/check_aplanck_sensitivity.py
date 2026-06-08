#!/usr/bin/env python3
"""
Diagnostic: A_planck prior sensitivity
====================================
Analyzes existing TEP-HC MCMC chains to quantify the correlation structure
between A_planck, H0, and epsilon_T. This informs whether loosening the
A_planck uniform prior from [0.9, 1.1] to [0.9, 1.25] would:
  (a) stabilize H0 error bars, or
  (b) induce a degeneracy cascade with epsilon_T.
"""

import sys
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

CHAIN_FILE = PROJECT_ROOT / "results" / "mcmc_chains" / "tep_hiclass_suite.1.txt"

def load_chain(path):
    with open(path) as f:
        header = f.readline().strip()
    cols = [c.strip() for c in header[1:].split()]
    col_map = {name: i for i, name in enumerate(cols)}
    data = np.loadtxt(path)
    return data, col_map

def weighted_stats(x, w):
    wsum = np.sum(w)
    mean = np.sum(w * x) / wsum
    var = np.sum(w * (x - mean)**2) / wsum
    return mean, np.sqrt(var)

def weighted_correlation(x, y, w):
    mx, _ = weighted_stats(x, w)
    my, _ = weighted_stats(y, w)
    cov = np.sum(w * (x - mx) * (y - my)) / np.sum(w)
    sx = np.sqrt(np.sum(w * (x - mx)**2) / np.sum(w))
    sy = np.sqrt(np.sum(w * (y - my)**2) / np.sum(w))
    return cov / (sx * sy)

def main():
    data, cmap = load_chain(CHAIN_FILE)
    print(f"Loaded {data.shape[0]} samples from {CHAIN_FILE.name}")

    # 30% burn-in
    burn = int(0.3 * data.shape[0])
    post = data[burn:]
    w = post[:, 0]

    a_idx = cmap["A_planck"]
    h_idx = cmap["H0"]
    e_idx = cmap["epsilon_T"]

    a = post[:, a_idx]
    h = post[:, h_idx]
    e = post[:, e_idx]

    # --- Current marginal statistics ---
    for name, arr in [("A_planck", a), ("H0", h), ("epsilon_T", e)]:
        mn, std = weighted_stats(arr, w)
        print(f"{name}: {mn:.5f} ± {std:.5f}  [min={arr.min():.5f}, max={arr.max():.5f}]")

    # --- Correlations ---
    rho_ah = weighted_correlation(a, h, w)
    rho_ae = weighted_correlation(a, e, w)
    rho_he = weighted_correlation(h, e, w)

    print(f"\nCorrelation matrix (weighted):")
    print(f"  corr(A_planck, H0)       = {rho_ah:+.4f}")
    print(f"  corr(A_planck, epsilon_T)= {rho_ae:+.4f}")
    print(f"  corr(H0, epsilon_T)      = {rho_he:+.4f}")

    # --- Truncation diagnostics ---
    a_max = a.max()
    n_at_bound = np.sum(a > 1.095)
    print(f"\nTruncation at upper bound (1.1):")
    print(f"  Maximum sampled A_planck = {a_max:.5f}")
    print(f"  Samples within 0.005 of bound = {n_at_bound} ({100*n_at_bound/len(a):.1f}%)")

    # --- Subsample above/below median A_planck ---
    med_a = np.median(a)
    mask_high = a > med_a
    mask_low = a <= med_a

    for label, mask in [("high A_planck", mask_high), ("low A_planck", mask_low)]:
        h_sub = h[mask]
        e_sub = e[mask]
        w_sub = w[mask]
        mh, sh = weighted_stats(h_sub, w_sub)
        me, se = weighted_stats(e_sub, w_sub)
        print(f"  {label}: H0 = {mh:.3f} ± {sh:.3f}, epsilon_T = {me:.5f} ± {se:.5f}")

    # --- Linear regression: how much does H0 shift per unit A_planck? ---
    # Fit H0 = b0 + b1 * A_planck + b2 * epsilon_T
    X = np.column_stack((np.ones(len(a)), a, e))
    wn = w / w.sum()  # normalized weights
    Wsqrt = np.sqrt(wn)
    Xw = X * Wsqrt[:, None]
    hw = h * Wsqrt
    beta = np.linalg.lstsq(Xw, hw, rcond=None)[0]
    print(f"\nLinear fit: H0 = {beta[0]:.3f} + {beta[1]:.3f}*A_planck + {beta[2]:.3f}*epsilon_T")
    print(f"  => A 0.1 increase in A_planck shifts H0 by ~{beta[1]*0.1:.3f}")

    # --- Project what happens if bound is lifted ---
    # Assume Gaussian tail beyond 1.1 with same mean and std
    mn_a, std_a = weighted_stats(a, w)
    print(f"\nPrior-saturation projection:")
    print(f"  Current posterior mean/std: {mn_a:.4f} ± {std_a:.4f}")
    print(f"  If the upper bound were removed, the tail would extend to ~{mn_a + 2*std_a:.3f} (2σ)")
    # How many sigma is the bound from the mean?
    sigmas_to_bound = (1.1 - mn_a) / std_a
    print(f"  The 1.1 bound is {sigmas_to_bound:.2f}σ above the mean — mild truncation.")

    # --- Degeneracy cascade test ---
    # Look at epsilon_T in samples where A_planck > 1.08 vs < 1.08
    mask_above = a > 1.08
    mask_below = a <= 1.08
    me_above, se_above = weighted_stats(e[mask_above], w[mask_above])
    me_below, se_below = weighted_stats(e[mask_below], w[mask_below])
    print(f"\nDegeneracy test (split at A_planck = 1.08):")
    print(f"  epsilon_T above 1.08: {me_above:.6f} ± {se_above:.6f}")
    print(f"  epsilon_T below 1.08: {me_below:.6f} ± {se_below:.6f}")
    print(f"  Difference: {me_above - me_below:.6f} ( {(me_above - me_below)/np.sqrt(se_above**2 + se_below**2):.2f}σ )")

if __name__ == "__main__":
    main()
