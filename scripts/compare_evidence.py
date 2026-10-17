#!/usr/bin/env python3
"""Read-only evidence comparison. Missing provenance stays unresolved, never passes."""
import argparse
import json
import math
from pathlib import Path

import numpy as np


def inspect_result(data, label):
    issues = []
    for field in ('logz', 'logzerr', 'n_call'):
        value = data.get(field)
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            issues.append(f'{label}: missing/nonfinite {field}')
    if isinstance(data.get('logzerr'), (int, float)) and data['logzerr'] < 0:
        issues.append(f'{label}: negative logzerr')
    if isinstance(data.get('n_call'), (int, float)) and data['n_call'] <= 0:
        issues.append(f'{label}: n_call must be positive')
    ess = None
    try:
        weights = np.asarray(data['weights'], dtype=float)
        if (weights.ndim != 1 or not len(weights) or not np.all(np.isfinite(weights))
                or np.any(weights < 0) or weights.sum() <= 0):
            raise ValueError('invalid weights')
        weights /= weights.sum()
        ess = float(1 / np.sum(weights**2))
        samples = data.get('samples')
        if not isinstance(samples, list) or len(samples) != len(weights):
            issues.append(f'{label}: samples/weights length mismatch')
    except (KeyError, TypeError, ValueError):
        issues.append(f'{label}: cannot recompute posterior ESS from weights')
    audit = data.get('evaluation_diagnostics', {})
    if audit.get('coverage') != 'entire_run':
        issues.append(f'{label}: complete evaluation diagnostics unavailable')
    counts = audit.get('counts', {})
    if not counts or counts.get('finite', 0) <= 0:
        issues.append(f'{label}: no finite evaluations recorded')
    for status, count in counts.items():
        if status != 'finite' and count:
            issues.append(f'{label}: {count} evaluations marked {status}; inspect exclusion/failure cause')
    config = data.get('provenance', {}).get('model_config')
    if not config:
        issues.append(f'{label}: run-time model configuration snapshot unavailable')
    def finite_or_none(value):
        return value if isinstance(value, (int, float)) and math.isfinite(value) else None
    return {'posterior_ess_from_weights': ess, 'n_call': finite_or_none(data.get('n_call')),
            'logzerr': finite_or_none(data.get('logzerr')), 'evaluation_counts': counts}, issues


def compare(lcdm, tep):
    lhs, issues = inspect_result(lcdm, 'LCDM')
    rhs, other = inspect_result(tep, 'TEP')
    issues += other
    priors_l = lcdm.get('param_priors', {})
    priors_t = tep.get('param_priors', {})
    if not priors_l or not priors_t:
        issues.append('Sampled parameter priors missing')
    if set(priors_t) - set(priors_l) != {'epsilon_T'} or set(priors_l) - set(priors_t):
        issues.append('Models are not the expected matched pair with only epsilon_T added')
    for name in set(priors_l) & set(priors_t):
        if priors_l[name] != priors_t[name]:
            issues.append(f'Shared parameter prior differs: {name}')
    configs = [d.get('provenance', {}).get('model_config') for d in (lcdm, tep)]
    if all(configs):
        a, b = configs
        for field in ('likelihood', 'prior'):
            if a.get(field) != b.get(field):
                issues.append(f'Configuration differs: {field}')
        # Reference/proposal values affect sampling, not the model; compare
        # fixed/derived definitions as well as the recorded sampled priors.
        def physics_params(cfg):
            return {k: {x: y for x, y in v.items() if x not in ('ref', 'proposal', 'latex')}
                    if isinstance(v, dict) else v
                    for k, v in cfg.get('params', {}).items() if k != 'epsilon_T'}
        if physics_params(a) != physics_params(b):
            issues.append('Shared fixed/derived parameter definitions differ')
        def baseline_theory(cfg):
            theory = json.loads(json.dumps(cfg.get('theory')))
            if isinstance(theory, dict):
                for spec in theory.values():
                    if isinstance(spec, dict):
                        extra = spec.get('extra_args', {})
                        for key in ('tep_mode', 'z_T', 'n_T'):
                            extra.pop(key, None)
            return theory
        if baseline_theory(a) != baseline_theory(b):
            issues.append('Theory settings differ beyond the declared TEP switches')
    valid_numbers = all(isinstance(d.get(k), (int, float)) and math.isfinite(d[k])
                        for d in (lcdm, tep) for k in ('logz', 'logzerr'))
    delta = tep['logz'] - lcdm['logz'] if valid_numbers else None
    uncertainty = math.hypot(tep['logzerr'], lcdm['logzerr']) if valid_numbers else None
    return {'status': 'review_required' if issues else 'automatic_checks_passed',
            'delta_logz_tep_minus_lcdm': delta,
            'delta_logz_error_independent_runs': uncertainty,
            'log10_bayes_factor_tep_over_lcdm': delta / math.log(10) if delta is not None else None,
            'LCDM': lhs, 'TEP': rhs, 'issues': issues,
            'scope': 'Configured HC background comparison, retaining CDM; not full-corpus closure.',
            'note': 'Automatic checks do not certify solver physics, adequate ESS or absence of shared systematics.'}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('lcdm', type=Path)
    ap.add_argument('tep', type=Path)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    missing = [str(p) for p in (args.lcdm, args.tep) if not p.is_file()]
    if missing:
        report = {'status': 'pending', 'missing_files': missing}
    else:
        try:
            report = compare(json.loads(args.lcdm.read_text()), json.loads(args.tep.read_text()))
        except (ValueError, TypeError, KeyError) as exc:
            report = {'status': 'invalid_input', 'error': str(exc)}
    content = json.dumps(report, indent=2, allow_nan=False)
    if args.output:
        args.output.write_text(content + '\n')
    print(content)
    return 0 if report['status'] == 'automatic_checks_passed' else 2


if __name__ == '__main__':
    raise SystemExit(main())
