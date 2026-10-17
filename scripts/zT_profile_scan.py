#!/usr/bin/env python3
"""Fixed-cosmology z_T x epsilon_T profile scan (upgrade 1, immediate).

Rebuilds the cobaya model per z_T (z_T lives in extra_args) and evaluates
Delta chi2 on an epsilon_T grid at TWO anchor cosmologies:

  - tep_anchor: converged TEP TTTEEE best-fit region (epsilon_T ~ 0.004)
  - lcdm_anchor: converged LCDM TTTEEE best-fit region (epsilon_T = 0)

The two anchors are needed because the positive-amplitude valley seen at
low z_T is a degeneracy direction: relative to the TEP anchor it reads as
an improvement, relative to the LCDM anchor as a modest penalty. Only the
full free-z_T posterior (tep_zscan_ttteee) settles which mode wins after
nuisance reoptimization.

Output: results/zT_profile_scan.json
"""
import json
import yaml
from pathlib import Path
from cobaya.model import get_model

ROOT = Path(__file__).resolve().parent.parent
ANCHORS = {
    'tep_anchor': {'logA': 3.044, 'n_s': 0.9659, 'H0': 67.82,
                   'omega_b': 0.02237, 'omega_cdm': 0.1192,
                   'tau_reio': 0.0544, 'A_planck': 1.0},
    'lcdm_anchor': {'logA': 3.044, 'n_s': 0.9660, 'H0': 67.89,
                    'omega_b': 0.02237, 'omega_cdm': 0.1199,
                    'tau_reio': 0.0544, 'A_planck': 1.0},
}
ZTS = [1.0, 2.0, 3.0, 5.0, 8.0, 10.0, 20.0, 50.0]
EPS = [0.0, 0.002, 0.004, 0.0071, 0.010]

with open(ROOT / 'data/cobaya/tep_native_mcmc_ttteee.yaml') as f:
    info = yaml.safe_load(f)
info['packages_path'] = str(ROOT / 'data/external/cobaya_packages')

out = {
    'note': ('Delta chi2 relative to epsilon_T=0 at the same anchor and '
             'z_T. Fixed-cosmology slice only -- not a marginalized '
             'posterior. Anchor choice changes the sign of the low-z_T '
             'valley: it is a degeneracy direction, not an unconditional '
             'improvement over LCDM.'),
    'anchors': ANCHORS, 'z_T_grid': ZTS, 'eps_grid': EPS, 'grid': {}}
for anchor_name, base in ANCHORS.items():
    for zt in ZTS:
        info2 = yaml.safe_load(yaml.dump(info))
        info2['theory']['classy']['extra_args']['z_T'] = zt
        m = get_model(info2)
        row = {}
        for e in EPS:
            p = dict(base)
            p['epsilon_T'] = e
            ll, _ = m.loglike(p)
            row[f'{e:g}'] = -2.0 * ll
        m.close()
        base0 = row['0']
        row = {k: v - base0 for k, v in row.items()}
        out['grid'].setdefault(anchor_name, {})[f'{zt:g}'] = row
        print(f'{anchor_name} z_T={zt}: '
              + ' '.join(f'{k}:{v:+.2f}' for k, v in row.items()),
              flush=True)

(ROOT / 'results' / 'zT_profile_scan.json').write_text(
    json.dumps(out, indent=2))
