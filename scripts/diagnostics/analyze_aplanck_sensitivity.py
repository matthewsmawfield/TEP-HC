#!/usr/bin/env python3
"""
Analyze A_planck sensitivity results.

1. Load partial chains from tep_hiclass_aplanck_sens (widened prior [0.9, 1.25])
2. Load main chain from tep_hiclass_suite (original prior [0.9, 1.1])
3. Importance-sample reweight main chain to widened prior
4. Compare posteriors and quantify degeneracy
"""

import numpy as np
import json
from pathlib import Path
import warnings

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CHAINS_DIR = PROJECT_ROOT / "results" / "mcmc_chains"
RESULTS_DIR = PROJECT_ROOT / "results"

# Column mapping for chain files
# logA, n_s, H0, omega_b, omega_cdm, tau_reio, A_planck, epsilon_T, chi2, ...
PARAM_NAMES = ['logA', 'n_s', 'H0', 'omega_b', 'omega_cdm', 'tau_reio', 'A_planck', 'epsilon_T']


def load_chain_files(prefix, max_chains=4):
    """Load all chain files for a given prefix."""
    all_samples = []
    for i in range(1, max_chains + 1):
        chain_file = CHAINS_DIR / f"{prefix}.{i}.txt"
        if chain_file.exists() and chain_file.stat().st_size > 0:
            # Skip comment lines, load data
            data = np.loadtxt(chain_file)
            if data.ndim == 1:
                data = data.reshape(1, -1)
            all_samples.append(data)
            print(f"  Loaded {chain_file.name}: {len(data)} samples")
    if not all_samples:
        return None
    return np.vstack(all_samples)


def extract_params(data):
    """Extract parameter columns from chain data."""
    # Columns: 0=weight, 1=-logL, 2=logA, 3=n_s, 4=H0, 5=omega_b, 6=omega_cdm, 7=tau_reio, 8=A_planck, 9=epsilon_T
    params = {}
    for i, name in enumerate(PARAM_NAMES):
        params[name] = data[:, 2 + i]
    params['weight'] = data[:, 0]
    params['logL'] = -data[:, 1]
    return params


def weighted_stats(values, weights):
    """Compute weighted mean, std, median, min, max."""
    total_weight = np.sum(weights)
    if total_weight == 0:
        return None, None, None, None, None
    mean = np.average(values, weights=weights)
    variance = np.average((values - mean) ** 2, weights=weights)
    std = np.sqrt(variance)
    # Weighted median
    sorted_idx = np.argsort(values)
    sorted_vals = values[sorted_idx]
    sorted_weights = weights[sorted_idx]
    cumsum = np.cumsum(sorted_weights)
    median_idx = np.searchsorted(cumsum, total_weight / 2.0)
    median = sorted_vals[min(median_idx, len(values) - 1)]
    return mean, std, median, np.min(values), np.max(values)


def weighted_correlation(x, y, weights):
    """Compute weighted Pearson correlation."""
    mean_x = np.average(x, weights=weights)
    mean_y = np.average(y, weights=weights)
    cov_xy = np.average((x - mean_x) * (y - mean_y), weights=weights)
    var_x = np.average((x - mean_x) ** 2, weights=weights)
    var_y = np.average((y - mean_y) ** 2, weights=weights)
    if var_x == 0 or var_y == 0:
        return 0.0
    return cov_xy / np.sqrt(var_x * var_y)


def compute_hpd(values, weights, cred=0.68):
    """Compute highest posterior density interval."""
    sorted_idx = np.argsort(values)
    sorted_vals = values[sorted_idx]
    sorted_weights = weights[sorted_idx]
    total_weight = np.sum(sorted_weights)
    target_weight = cred * total_weight

    best_lo, best_hi = sorted_vals[0], sorted_vals[-1]
    best_width = best_hi - best_lo

    n = len(sorted_vals)
    for i in range(n):
        cumsum = 0.0
        for j in range(i, n):
            cumsum += sorted_weights[j]
            if cumsum >= target_weight:
                width = sorted_vals[j] - sorted_vals[i]
                if width < best_width:
                    best_width = width
                    best_lo = sorted_vals[i]
                    best_hi = sorted_vals[j]
                break
    return best_lo, best_hi


def reweight_uniform_prior(samples, old_min, old_max, new_min, new_max):
    """
    Importance-sampling reweighting from old uniform prior to new uniform prior.
    Weight factor = (new_prior / old_prior) = (old_range / new_range)
    For samples outside new range, weight = 0.
    """
    weights = np.ones(len(samples))
    in_range = (samples >= new_min) & (samples <= new_max)
    weights[~in_range] = 0.0
    weights[in_range] *= (old_max - old_min) / (new_max - new_min)
    return weights


def analyze_sensitivity():
    print("=" * 60)
    print("A_planck Sensitivity Analysis")
    print("=" * 60)

    # ---- Load widened-prior partial chains ----
    print("\n[1] Loading widened-prior chains (A_planck: [0.9, 1.25])...")
    data_wide = load_chain_files("tep_hiclass_aplanck_sens")
    if data_wide is None:
        print("  No chain files found for widened prior run.")
        return

    p_wide = extract_params(data_wide)
    w_wide = p_wide['weight']

    # ---- Load main chain (original prior) ----
    print("\n[2] Loading main chain (A_planck: [0.9, 1.1])...")
    data_main = load_chain_files("tep_hiclass_suite")
    if data_main is None:
        print("  No chain files found for main run.")
        return

    p_main = extract_params(data_main)
    w_main = p_main['weight']

    # ---- Analyze widened-prior chains ----
    print("\n[3] Widened-prior posterior statistics:")
    results_wide = {}
    for name in PARAM_NAMES:
        mean, std, median, vmin, vmax = weighted_stats(p_wide[name], w_wide)
        hpd_lo, hpd_hi = compute_hpd(p_wide[name], w_wide)
        results_wide[name] = {
            'mean': float(mean), 'std': float(std),
            'median': float(median), 'min': float(vmin), 'max': float(vmax),
            'hpd68': [float(hpd_lo), float(hpd_hi)]
        }
        print(f"  {name:12s}: {mean:.6f} ± {std:.6f}  (range: {vmin:.4f}..{vmax:.4f})  HPD68: [{hpd_lo:.4f}, {hpd_hi:.4f}]")

    # ---- Correlations in widened prior ----
    print("\n[4] Correlation matrix (widened prior):")
    corr_ah = weighted_correlation(p_wide['A_planck'], p_wide['H0'], w_wide)
    corr_ae = weighted_correlation(p_wide['A_planck'], p_wide['epsilon_T'], w_wide)
    corr_he = weighted_correlation(p_wide['H0'], p_wide['epsilon_T'], w_wide)
    print(f"  corr(A_planck, H0)       = {corr_ah:+.4f}")
    print(f"  corr(A_planck, epsilon_T)= {corr_ae:+.4f}")
    print(f"  corr(H0, epsilon_T)      = {corr_he:+.4f}")

    # ---- Main chain original-prior stats ----
    print("\n[5] Original-prior posterior statistics:")
    results_orig = {}
    for name in PARAM_NAMES:
        mean, std, median, vmin, vmax = weighted_stats(p_main[name], w_main)
        hpd_lo, hpd_hi = compute_hpd(p_main[name], w_main)
        results_orig[name] = {
            'mean': float(mean), 'std': float(std),
            'median': float(median), 'min': float(vmin), 'max': float(vmax),
            'hpd68': [float(hpd_lo), float(hpd_hi)]
        }
        print(f"  {name:12s}: {mean:.6f} ± {std:.6f}  (range: {vmin:.4f}..{vmax:.4f})  HPD68: [{hpd_lo:.4f}, {hpd_hi:.4f}]")

    # ---- Importance-sampling reweight main chain to widened prior ----
    print("\n[6] Importance-sampling reweighting main chain -> widened prior...")
    w_reweight = reweight_uniform_prior(
        p_main['A_planck'],
        old_min=0.9, old_max=1.1,
        new_min=0.9, new_max=1.25
    )
    # Combine with original weights
    w_reweighted = w_main * w_reweight
    effective_samples = np.sum(w_reweighted) ** 2 / np.sum(w_reweighted ** 2)

    print(f"  Effective samples after reweighting: {effective_samples:.0f}")
    print(f"  Samples truncated by new prior: {np.sum(w_reweight == 0)} / {len(w_reweight)}")

    results_reweight = {}
    for name in PARAM_NAMES:
        mean, std, median, vmin, vmax = weighted_stats(p_main[name], w_reweighted)
        hpd_lo, hpd_hi = compute_hpd(p_main[name], w_reweighted)
        results_reweight[name] = {
            'mean': float(mean), 'std': float(std),
            'median': float(median), 'min': float(vmin), 'max': float(vmax),
            'hpd68': [float(hpd_lo), float(hpd_hi)]
        }
        print(f"  {name:12s}: {mean:.6f} ± {std:.6f}  HPD68: [{hpd_lo:.4f}, {hpd_hi:.4f}]")

    # ---- Compare H0 shifts ----
    print("\n[7] H0 comparison across methods:")
    h0_orig = results_orig['H0']
    h0_wide = results_wide['H0']
    h0_reweight = results_reweight['H0']

    shift_wide = h0_wide['mean'] - h0_orig['mean']
    shift_reweight = h0_reweight['mean'] - h0_orig['mean']

    print(f"  Original prior [0.9, 1.1]:    H0 = {h0_orig['mean']:.3f} ± {h0_orig['std']:.3f}")
    print(f"  Widened prior [0.9, 1.25]:      H0 = {h0_wide['mean']:.3f} ± {h0_wide['std']:.3f}")
    print(f"  Reweighted main chain:          H0 = {h0_reweight['mean']:.3f} ± {h0_reweight['std']:.3f}")
    print(f"  Shift (widened - original):     ΔH0 = {shift_wide:+.3f}")
    print(f"  Shift (reweighted - original): ΔH0 = {shift_reweight:+.3f}")

    # ---- Epsilon_T comparison ----
    print("\n[8] epsilon_T comparison:")
    et_orig = results_orig['epsilon_T']
    et_wide = results_wide['epsilon_T']
    et_reweight = results_reweight['epsilon_T']

    print(f"  Original prior [0.9, 1.1]:    epsilon_T = {et_orig['mean']:.6f} ± {et_orig['std']:.6f}")
    print(f"  Widened prior [0.9, 1.25]:      epsilon_T = {et_wide['mean']:.6f} ± {et_wide['std']:.6f}")
    print(f"  Reweighted main chain:          epsilon_T = {et_reweight['mean']:.6f} ± {et_reweight['std']:.6f}")

    # ---- Degeneracy analysis ----
    print("\n[9] Degeneracy analysis:")
    print(f"  corr(A_planck, epsilon_T) in widened run: {corr_ae:+.4f}")

    # Split widened chain by A_planck value
    a_vals = p_wide['A_planck']
    e_vals = p_wide['epsilon_T']
    split_at = 1.15
    mask_high = a_vals > split_at
    mask_low = a_vals <= split_at

    if np.sum(mask_high) > 10 and np.sum(mask_low) > 10:
        e_high_mean, e_high_std, _, _, _ = weighted_stats(e_vals[mask_high], w_wide[mask_high])
        e_low_mean, e_low_std, _, _, _ = weighted_stats(e_vals[mask_low], w_wide[mask_low])
        diff = e_high_mean - e_low_mean
        diff_sigma = diff / np.sqrt(e_high_std**2 + e_low_std**2) if (e_high_std > 0 and e_low_std > 0) else 0
        print(f"  epsilon_T (A_planck > {split_at}): {e_high_mean:.6f} ± {e_high_std:.6f}  (N={np.sum(mask_high)})")
        print(f"  epsilon_T (A_planck ≤ {split_at}): {e_low_mean:.6f} ± {e_low_std:.6f}  (N={np.sum(mask_low)})")
        print(f"  Difference: {diff:.6f} ({diff_sigma:.2f}σ)")

    # ---- Save results ----
    output = {
        'widened_prior': results_wide,
        'original_prior': results_orig,
        'reweighted': results_reweight,
        'correlations': {
            'A_planck_H0': float(corr_ah),
            'A_planck_epsilon_T': float(corr_ae),
            'H0_epsilon_T': float(corr_he)
        },
        'H0_shift': {
            'widened_vs_original': float(shift_wide),
            'reweighted_vs_original': float(shift_reweight)
        },
        'sample_counts': {
            'widened_total': len(data_wide),
            'main_total': len(data_main),
            'reweighted_effective': float(effective_samples)
        }
    }

    output_file = RESULTS_DIR / 'aplanck_sensitivity_analysis.json'
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n[10] Results saved to: {output_file}")

    return output


if __name__ == '__main__':
    analyze_sensitivity()
