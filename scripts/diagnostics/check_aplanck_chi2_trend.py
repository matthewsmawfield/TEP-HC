#!/usr/bin/env python3
"""
Diagnostic: chi2 trend vs A_planck
==================================
Check whether the likelihood keeps improving as A_planck approaches 1.1.
If chi2 is still dropping at the boundary, the posterior will shift when
the bound is removed.
"""

import sys
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

CHAIN_FILE = PROJECT_ROOT / "results" / "mcmc_chains" / "tep_hiclass_suite.1.txt"

def main():
    with open(CHAIN_FILE) as f:
        header = f.readline().strip()
    cols = [c.strip() for c in header[1:].split()]
    cmap = {name: i for i, name in enumerate(cols)}
    data = np.loadtxt(CHAIN_FILE)
    burn = int(0.3 * data.shape[0])
    post = data[burn:]
    w = post[:, 0]
    a = post[:, cmap["A_planck"]]
    chi2 = post[:, cmap["chi2"]]
    chi2_cmb = post[:, cmap["chi2__CMB"]]
    chi2_bao = post[:, cmap["chi2__BAO"]]
    chi2_sn = post[:, cmap["chi2__SN"]]

    # Bin by A_planck and compute mean chi2 in each bin
    bins = np.linspace(1.0, 1.1, 11)
    print("Bin        N      <A_planck>   <chi2_tot>  <chi2_CMB>  <chi2_BAO>  <chi2_SN>")
    for i in range(len(bins)-1):
        lo, hi = bins[i], bins[i+1]
        mask = (a >= lo) & (a < hi)
        if mask.sum() < 10:
            continue
        n = mask.sum()
        wa = w[mask]
        def wmean(x):
            return np.sum(wa * x[mask]) / np.sum(wa)
        print(f"[{lo:.3f},{hi:.3f}) {n:5d}   {wmean(a):.4f}     {wmean(chi2):8.2f}  {wmean(chi2_cmb):8.2f}  {wmean(chi2_bao):8.2f}  {wmean(chi2_sn):8.2f}")

    # Compare chi2 for top 5% A_planck vs bottom 50% A_planck
    a_sorted = np.sort(a)
    thresh = a_sorted[int(0.95 * len(a))]
    mask_top = a >= thresh
    mask_bot = a <= np.median(a)
    for label, mask in [(f"top 5% (>{thresh:.4f})", mask_top), ("bottom 50%", mask_bot)]:
        wa = w[mask]
        def wmean(x):
            return np.sum(wa * x[mask]) / np.sum(wa)
        print(f"\n{label}: A_planck={wmean(a):.4f}, chi2_tot={wmean(chi2):.2f}, chi2_CMB={wmean(chi2_cmb):.2f}")

if __name__ == "__main__":
    main()
