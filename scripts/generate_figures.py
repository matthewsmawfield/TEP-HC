#!/usr/bin/env python3
"""Generate publication-quality figures for TEP-HC."""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
from scripts.utils.plot_style import set_pub_style, COLORS, FIG_SIZES, save_fig

FIGURES_DIR = PROJECT_ROOT / 'results' / 'figures'


def figure_1_alpha_evolution():
    """Alpha function evolution with redshift."""
    with open(PROJECT_ROOT / 'results/03_alpha_functions.json') as f:
        data = json.load(f)

    z = np.array(data['redshifts'])
    alpha_M = np.array(data['alpha_M'])
    alpha_T = np.array(data['alpha_T'])
    alpha_B = np.array(data['alpha_B'])
    alpha_K = np.array(data['alpha_K'])

    series = [
        (r'$\alpha_M$', alpha_M, COLORS['tep']),
        (r'$\alpha_T$', alpha_T, COLORS['red']),
        (r'$\alpha_B$', alpha_B, COLORS['model']),
        (r'$\alpha_K$', alpha_K, COLORS['observed']),
    ]

    fig, axes = plt.subplots(2, 2, figsize=FIG_SIZES['web_quad'])
    fig.suptitle('TEP Alpha Functions: Bellini–Sawicki EFT', fontsize=13, y=1.02)

    for ax, (label, values, color) in zip(axes.flat, series):
        ax.semilogx(1 + z, values, color=color, linewidth=2.0, label=label)
        ax.axvline(1100, color=COLORS['gr'], linestyle='--', alpha=0.7, label='CMB epoch')
        ax.axhline(0, color=COLORS['text'], linestyle='-', alpha=0.25, linewidth=0.8)
        ax.set_xlabel('1 + z')
        ax.set_ylabel(label)
        ax.set_xlim(1, 1200)
        ax.legend(loc='upper right', fontsize=9)

    out = FIGURES_DIR / 'figure_1_alpha_evolution.png'
    save_fig(fig, out)
    print(f"  Generated {out.name}")


def figure_2_cmb_residuals():
    """CMB residual analysis for the native TEP background modification.

    The physically meaningful statement is twofold and is read directly from the
    pipeline output (no hardcoded numbers):
      (a) the fractional C_ell residual at the fiducial epsilon_T, which is a
          *coherent* pattern -- a rigid angular rescaling of the spectrum, not a
          change in acoustic-peak morphology;
      (b) the sound horizon r_s is preserved to ppm (early-time freezing works),
          so the entire residual is a late-time angular-diameter-distance
          projection (theta_s), which is degenerate with H0 and absorbed by the
          standard parameters in a joint fit (-> epsilon_T bounded to ~0, TEP-C0).
    """
    with open(PROJECT_ROOT / 'results/04_cmb_spectra.json') as f:
        data = json.load(f)

    ells = np.array(data['ells'])
    residuals = np.array(data['spectra']['residuals'])
    acoustic = data.get('acoustic', {})
    r_s_ratio = acoustic.get('r_s_ratio', float('nan'))
    theta_shift = acoustic.get('theta_s_frac_shift', float('nan')) * 100.0

    # Read the fiducial epsilon_T from the generated tep ini for an honest caption.
    eps_T = None
    try:
        for line in (PROJECT_ROOT / 'results/tep_model.ini').read_text().splitlines():
            if line.strip().startswith('epsilon_T'):
                eps_T = float(line.split('=')[1])
    except (OSError, ValueError):
        pass
    eps_str = f'{eps_T:g}' if eps_T is not None else 'fiducial'

    mask_acoustic = (ells >= 100) & (ells <= 2000)
    max_acoustic = np.nanmax(np.abs(residuals[mask_acoustic])) * 100

    fig, axes = plt.subplots(1, 2, figsize=FIG_SIZES['double_column'])
    fig.suptitle(
        'Native TEP background modification: CMB TT impact is a projection',
        fontsize=12, y=1.02,
    )

    # Panel (a): residual across the acoustic range (coherent peak-shift pattern)
    ax = axes[0]
    ax.plot(ells[mask_acoustic], residuals[mask_acoustic] * 100, color=COLORS['tep'], linewidth=1.2)
    ax.axhline(0, color=COLORS['gr'], linestyle='--', alpha=0.7)
    for peak in [220, 540, 810]:
        ax.axvline(peak, color=COLORS['light_gray'], linestyle='--', alpha=0.5)
    ax.set_xlabel(r'Multipole $\ell$')
    ax.set_ylabel(r'$\Delta C_\ell^{TT} / C_\ell^{TT}$ [%]')
    ax.set_xlim(100, 2000)
    ax.set_title(
        rf'(a) $\epsilon_T={eps_str}$: coherent shift, max $|\Delta C_\ell/C_\ell|={max_acoustic:.2f}\%$',
        fontsize=10,
    )

    # Panel (b): the acoustic-scale bookkeeping -- r_s preserved, theta_s shifted
    ax = axes[1]
    ax.axis('off')
    txt = (
        r'$\bf{Acoustic\ scale\ bookkeeping}$' + '\n\n'
        rf'Sound horizon ratio  $r_s^{{\rm TEP}}/r_s^{{\Lambda\rm CDM}} = {r_s_ratio:.7f}$' + '\n'
        r'(preserved to ppm $\Rightarrow$ early-time freezing intact:' + '\n'
        r'$r_s$, BBN and peak morphology untouched)' + '\n\n'
        rf'Angular scale shift  $\Delta\theta_s/\theta_s = {theta_shift:+.4f}\%$' + '\n'
        r'(pure late-time $D_A$ projection; degenerate with $H_0$)' + '\n\n'
        r'$\Rightarrow$ residual is a rigid $\ell$-rescaling that standard' + '\n'
        r'parameters absorb; the CMB therefore bounds the' + '\n'
        r'homogeneous amplitude to $\epsilon_T\approx0$ (TEP-C0, Paper 26).'
    )
    ax.text(0.02, 0.98, txt, va='top', ha='left', fontsize=9.5,
            transform=ax.transAxes,
            bbox=dict(boxstyle='round', facecolor='white', edgecolor=COLORS['tep'], alpha=0.95))

    out = FIGURES_DIR / 'figure_2_cmb_residuals.png'
    save_fig(fig, out)
    print(f"  Generated {out.name}")


def figure_3_sne_evidence():
    """Late-time Bayesian evidence for the TEP geometry (TEP-C0, Paper 26).

    These Bayes factors come from the *completed, verified* SNe-only nested
    sampling over the full 1701x1701 Pantheon+ stat+sys covariance
    (TEP-C0 step_03_01). They are the genuine late-universe evidence that this
    paper relies on; the homogeneous CMB amplitude is bounded separately
    (Section 5). We deliberately do NOT plot the old propto_omega proxy chains
    (Appendix A), which are an unvalidated numerical artifact, nor the joint
    SNe+CMB MCMC, which is not yet a completed run.
    """
    # Verified Bayes factors vs LCDM from TEP-C0 results/step_03_01 (Paper 26 Table).
    models = [
        ('EdS\n(pure matter)', 3.48e-126),
        ('Pure shear\n(tired light)', 3.40e-10),
        (r'TEP M1' + '\n' + r'($z_T{=}5$)', 7.21),
        ('TEP M1\n(free $z_T$)', 10.24),
        ('wCDM', 18.52),
        ('CPL\n($w_0w_a$)', 17.83),
    ]
    names = [m[0] for m in models]
    bf = np.array([m[1] for m in models])
    lnbf = np.log(bf)
    colors = []
    for n in names:
        if 'TEP' in n:
            colors.append(COLORS['tep'])
        elif 'EdS' in n or 'shear' in n:
            colors.append(COLORS['red'])
        else:
            colors.append(COLORS['model'])

    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.bar(range(len(names)), lnbf, color=colors, alpha=0.85, edgecolor=COLORS['text'])
    ax.axhline(0, color=COLORS['gr'], linewidth=1.0)
    ax.axhspan(0, 1, alpha=0.06, color=COLORS['text'])
    ax.axhspan(1, 3, alpha=0.10, color=COLORS['tep'])
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names, fontsize=8)
    ax.set_ylabel(r'$\ln$ Bayes factor vs $\Lambda$CDM')
    ax.set_title('Late-time SNe evidence (Pantheon+, full covariance; TEP-C0 nested sampling)',
                 fontsize=11)
    for i, v in enumerate(lnbf):
        ax.text(i, v + (0.4 if v >= 0 else -0.4), f'{v:.1f}',
                ha='center', va='bottom' if v >= 0 else 'top', fontsize=8)
    ax.text(0.99, 0.04,
            'TEP and dark-energy models are all "substantial/strong" over $\\Lambda$CDM;\n'
            'EdS and pure tired-light are decisively rejected.',
            transform=ax.transAxes, ha='right', va='bottom', fontsize=8.5,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor=COLORS['gr']))

    out = FIGURES_DIR / 'figure_3_sne_evidence.png'
    save_fig(fig, out)
    print(f"  Generated {out.name}")


def figure_4_h0_comparison():
    """H0 in the TEP picture: homogeneous background stays Planck-compatible;
    the local SH0ES value is reinterpreted as a clock-transport bias (Paper 11).

    We do NOT plot the old propto_omega proxy chain H0 (66.0), which is an
    unvalidated artifact (Appendix A). The TEP homogeneous background is
    Planck-compatible by construction (epsilon_T bounded to ~0 on homogeneous
    scales); the late-time tension is resolved locally, not via a modified
    expansion history.
    """
    fig, ax = plt.subplots(figsize=(7.8, 3.8))

    measurements = [
        ('Planck 2018 (CMB, $\\Lambda$CDM)', 67.36, 0.54, COLORS['planck']),
        ('TEP homogeneous background\n($\\epsilon_T\\!\\to\\!0$; Planck-compatible)', 67.36, 0.54, COLORS['tep']),
        ('SH0ES local, TEP-corrected\n(clock bias removed; Paper 11)', 69.1, 1.0, COLORS['model']),
        ('SH0ES (local, uncorrected)', 73.04, 1.04, COLORS['shoes']),
    ]

    y_pos = np.arange(len(measurements))

    for i, (name, value, error, color) in enumerate(measurements):
        ax.errorbar(
            value, i, xerr=error, fmt='o', markersize=10,
            color=color, ecolor=color, capsize=5, capthick=2,
            alpha=0.9,
        )
        ax.text(
            value + error + 0.35, i, f'{value:.2f} ± {error:.2f}',
            va='center', fontsize=10, color=COLORS['text'],
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([m[0] for m in measurements])
    ax.set_xlabel(r'$H_0$ [km/s/Mpc]')
    ax.set_title(r'$H_0$ Measurements: Early Universe CMB vs Late Universe Cepheids')
    ax.set_xlim(65, 76)
    ax.axvline(67.36, color=COLORS['planck'], linestyle='--', alpha=0.35)
    ax.axvline(73.04, color=COLORS['shoes'], linestyle='--', alpha=0.35)

    ax.annotate(
        'Hubble tension:\n4.8σ discrepancy',
        xy=(70.2, len(measurements) - 1 + 0.15), fontsize=10, ha='center',
        bbox=dict(boxstyle='round', facecolor=COLORS['light_gray'], alpha=0.8, edgecolor=COLORS['gr']),
    )
    ax.annotate(
        'TEP interpretation:\nproper-time calibration\nin unscreened media',
        xy=(70.2, 0.35), fontsize=9, ha='center', color=COLORS['tep'],
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor=COLORS['tep']),
    )

    out = FIGURES_DIR / 'figure_4_H0_comparison.png'
    save_fig(fig, out)
    print(f"  Generated {out.name}")


def main():
    print('=' * 60)
    print('GENERATING TEP-HC FIGURES')
    print('=' * 60)

    set_pub_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figure_1_alpha_evolution()
    figure_2_cmb_residuals()
    figure_3_sne_evidence()
    figure_4_h0_comparison()

    print()
    print('=' * 60)
    print('  ALL FIGURES GENERATED')
    print('=' * 60)


if __name__ == '__main__':
    main()
