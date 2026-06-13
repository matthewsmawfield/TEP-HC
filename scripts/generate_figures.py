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
from scripts.utils.plot_style import set_pub_style, COLORS, export_figsize, save_fig

FIGURES_DIR = PROJECT_ROOT / 'results' / 'figures'
LITERATURE_JSON = PROJECT_ROOT / 'data/references/literature_benchmarks.json'
MCMC_SUMMARY_JSON = PROJECT_ROOT / 'results/07_mcmc_summary_full.json'
JORDAN_SCAN_JSON = PROJECT_ROOT / 'results/04b_jordan_frame_scan.json'


def _load_json(path: Path, label: str) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"{label} not found at {path}. "
            "Run the TEP-HC pipeline and ensure required inputs are present."
        )
    with open(path) as f:
        return json.load(f)


def _extract_scan_series(scan_rows):
    """Return (epsilon_T, theta_s_100) arrays from successful Jordan-frame scan rows."""
    eps = []
    theta = []
    for row in scan_rows:
        if row.get('success'):
            eps.append(row['epsilon_T'])
            theta.append(row['theta_s_100'])
    return np.array(eps), np.array(theta)


def _eds_baseline_theta(scan_rows) -> float:
    for row in scan_rows:
        if row.get('success') and row['epsilon_T'] == 0.0:
            return float(row['theta_s_100'])
    raise ValueError('No successful epsilon_T=0 row in Jordan-frame scan')


def figure_4_h0_comparison():
    """H0: literature benchmarks plus this paper's hi_class joint MCMC."""
    lit = _load_json(LITERATURE_JSON, 'Literature benchmarks')
    mcmc = _load_json(MCMC_SUMMARY_JSON, 'MCMC summary (run step 07)')

    h0_mcmc = mcmc['tep']['H0']
    planck = lit['h0_km_s_mpc']['planck2018_lcdm']
    sh0es = lit['h0_km_s_mpc']['sh0es_local_uncorrected']
    corrected = lit['h0_km_s_mpc']['sh0es_tep_corrected']

    measurements = [
        (planck['label'], planck['value'], planck['error'], COLORS['planck']),
        (
            'hi_class joint MCMC\n(this paper; Planck low-$\\ell$+lensing+BAO+Pantheon+)',
            h0_mcmc['mean'], h0_mcmc['std'], COLORS['tep'],
        ),
        (corrected['label'], corrected['value'], corrected['error'], COLORS['accent']),
        (sh0es['label'], sh0es['value'], sh0es['error'], COLORS['shoes']),
    ]

    fig, ax = plt.subplots(figsize=export_figsize('web_two_panel'))
    y_pos = np.arange(len(measurements))

    for i, (name, value, error, color) in enumerate(measurements):
        ax.errorbar(
            value, i, xerr=error, fmt='o', markersize=6,
            color=color, ecolor=color, capsize=4, capthick=1.2,
            alpha=0.9, linewidth=1.2,
        )
        ax.text(
            value + error + 0.28, i, f'{value:.2f} ± {error:.2f}',
            va='center', color=COLORS['text'], fontsize=8,
        )

    ax.set_yticks(y_pos)
    ax.set_yticklabels([m[0] for m in measurements])
    ax.set_xlabel(r'$H_0$ [km/s/Mpc]')
    ax.set_title('Early-universe CMB vs late-universe Cepheids')
    ax.set_xlim(64, 76)
    ax.axvline(planck['value'], color=COLORS['planck'], linestyle='--', alpha=0.35, linewidth=0.9)
    ax.axvline(sh0es['value'], color=COLORS['shoes'], linestyle='--', alpha=0.35, linewidth=0.9)

    tension_sigma = (sh0es['value'] - planck['value']) / np.hypot(sh0es['error'], planck['error'])
    ax.annotate(
        f'{tension_sigma:.1f}$\\sigma$ tension',
        xy=(70.2, len(measurements) - 1 + 0.12), ha='center', fontsize=8,
        bbox=dict(boxstyle='round', facecolor=COLORS['gray_light'], alpha=0.9, edgecolor=COLORS['border'], pad=0.35),
    )
    ax.annotate(
        'TEP: clock-transport\nbias in unscreened media',
        xy=(70.2, 1.35), ha='center', fontsize=8, color=COLORS['tep'],
        bbox=dict(boxstyle='round', facecolor='white', alpha=0.9, edgecolor=COLORS['accent'], pad=0.35),
    )

    out = FIGURES_DIR / 'figure_1_H0_comparison.png'
    save_fig(fig, out)
    print(f"  Generated {out.name}")


def figure_5_jordan_theta_s():
    """Jordan-frame EdS + TEP dual scan: theta_s vs epsilon_T."""
    data = _load_json(JORDAN_SCAN_JSON, 'Jordan-frame scan (run step 04b)')
    lit = _load_json(LITERATURE_JSON, 'Literature benchmarks')
    planck_ref = lit['planck_theta_s_100_lcdm']['value']

    std_eps, std_theta = _extract_scan_series(data['standard_scan']['scan'])
    unscr_eps, unscr_theta = _extract_scan_series(data['unscreened_scan']['scan'])
    eds_baseline = _eds_baseline_theta(data['standard_scan']['scan'])

    if len(std_eps) < 2 and len(unscr_eps) < 2:
        raise ValueError('Insufficient successful Jordan-frame scan points for figure 5')

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=export_figsize('double_column'))
    eds_label = rf'EdS baseline ($100\,\theta_s={eds_baseline:.4f}$)'
    planck_label = rf'Planck $\Lambda$CDM ref. ({planck_ref})'

    def _draw_panel(ax, eps, theta, series_color, marker, series_label, title):
        ax.plot(eps, theta, color=series_color, marker=marker, markersize=5, linewidth=1.4, label=series_label)
        ax.axhline(eds_baseline, color=COLORS['tep'], linestyle='-', linewidth=1.2, label=eds_label)
        ax.axhline(planck_ref, color=COLORS['planck'], linestyle='--', linewidth=1.2, label=planck_label)
        ax.set_xlabel(r'$\epsilon_T$')
        ax.set_ylabel(r'$100\,\theta_s$')
        ax.set_title(title)
        ax.legend(loc='best', fontsize=7)
        ax.set_xlim(left=0)

    if len(std_eps) >= 2:
        _draw_panel(
            ax1, std_eps, std_theta, COLORS['tep'], 'o',
            r'Standard ($z_T=5$)',
            'Standard ($z_T=5$): suppression active',
        )

    if len(unscr_eps) >= 2:
        _draw_panel(
            ax2, unscr_eps, unscr_theta, COLORS['alt'], 's',
            r'Unscreened ($z_T \to \infty$)',
            r'Unscreened ($z_T \to \infty$): no protection',
        )
        eps0_idx = int(np.where(unscr_eps == 0.0)[0][0])
        ax2.plot(
            unscr_eps[eps0_idx], unscr_theta[eps0_idx],
            marker='*', markersize=10, linestyle='none', color=COLORS['purple_accent'],
            label=r'EdS limit ($\epsilon_T=0$)',
        )
        ax2.legend(loc='best', fontsize=7)
        ax2.set_ylim(0.65, 1.06)

    fig.subplots_adjust(wspace=0.22)

    out = FIGURES_DIR / 'figure_2_jordan_theta_s.png'
    save_fig(fig, out)
    print(f"  Generated {out.name}")


def main():
    print('=' * 60)
    print('GENERATING TEP-HC FIGURES')
    print('=' * 60)

    set_pub_style()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    figure_4_h0_comparison()
    figure_5_jordan_theta_s()

    print()
    print('=' * 60)
    print('  ALL FIGURES GENERATED')
    print('=' * 60)


if __name__ == '__main__':
    main()
