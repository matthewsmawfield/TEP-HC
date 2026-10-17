#!/usr/bin/env python3
"""Controlled pressure sensitivity, NOT an action-derived TEP replacement model.

Uses the unchanged local hi_class build. The derived BBN density is held fixed;
CDM is compared with a w=0 fluid, first cs2=0 then the proposed finite cs2.
The zero-pressure fluid control checks equation/solver equivalence before the
finite-pressure difference is interpreted. No fit or likelihood is performed.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT.parent


def spectrum_comparison(reference, candidate, lo=30, hi=2000):
    out = {}
    sl = slice(lo, hi + 1)
    for key in ('tt', 'ee', 'pp'):
        a, b = reference[key][sl], candidate[key][sl]
        relative = (b - a) / a
        out[key] = {'rms_fractional_change': float(np.sqrt(np.mean(relative**2))),
                    'max_abs_fractional_change': float(np.max(np.abs(relative)))}
    # TE crosses zero: use sqrt(TT*EE), not a divergent relative TE error.
    scale = np.sqrt(reference['tt'][sl] * reference['ee'][sl])
    te_delta = (candidate['te'][sl] - reference['te'][sl]) / scale
    out['te'] = {'rms_change_over_sqrt_TT_EE': float(np.sqrt(np.mean(te_delta**2))),
                 'max_abs_change_over_sqrt_TT_EE': float(np.max(np.abs(te_delta)))}
    return out


def run(output):
    source = CORPUS / 'TEP-BBN/results/step_20_ambient_bath_front.json'
    source_bytes = source.read_bytes()
    bbn = json.loads(source_bytes)['F_boundary_perturbation_spectrum']
    exact = bbn['exact_boltzmann_two_branch_closure']
    cp2 = bbn['perturbation_mode_closure']['quadratic_action_coefficients']['c_p_eff_squared_derived']
    build = ROOT / 'external/hi_class/hi_class'
    libraries = sorted(build.glob('build/lib.*/classy*.so'))
    if len(libraries) != 1:
        raise RuntimeError(f'Expected one explicit compiled classy library, got {libraries}')
    sys.path.insert(0, str(libraries[0].parent))
    import classy
    if Path(classy.__file__).resolve() != libraries[0].resolve():
        raise RuntimeError('Unexpected CLASS build loaded')
    H0 = exact['H0_km_s_Mpc']
    density = exact['omega_phi_derived_clock_slope']
    base = {'output': 'tCl,pCl,lCl,mPk', 'lensing': 'yes',
            'l_max_scalars': 2500, 'P_k_max_h/Mpc': 10.0,
            'H0': H0, 'omega_b': exact['omega_b'],
            'A_s': float(np.exp(3.044)*1e-10), 'n_s': .9686, 'tau_reio': .0479,
            'tep_mode': 'yes', 'z_T': 5.0, 'n_T': 2.0, 'epsilon_T': .00488,
            'gauge': 'newtonian'}
    scenarios = {
        'pressureless_cdm_slot': {'omega_cdm': density},
        'zero_pressure_fluid_control': {'omega_cdm': 0., 'Omega_fld': density/(H0/100)**2,
                                       'w0_fld': 0., 'wa_fld': 0., 'cs2_fld': 0., 'use_ppf': 'no'},
        'finite_pressure_fluid_diagnostic': {'omega_cdm': 0., 'Omega_fld': density/(H0/100)**2,
                                           'w0_fld': 0., 'wa_fld': 0., 'cs2_fld': cp2, 'use_ppf': 'no'},
    }
    outputs, spectra = {}, {}
    failure = None
    for name, additions in scenarios.items():
        print('Computing', name, flush=True)
        cosmo = classy.Class()
        params = dict(base, **additions)
        try:
            cosmo.set(params)
            cosmo.compute()
            spectra[name] = {k: np.asarray(v).copy() for k,v in cosmo.lensed_cl(2500).items()}
            outputs[name] = {'parameters': params, '100_theta_s': float(cosmo.theta_s_100()),
                             'sigma8': float(cosmo.sigma8()),
                             'derived': cosmo.get_current_derived_parameters(['rs_rec','z_rec'])}
        except classy.CosmoComputationError as exc:
            failure = {'scenario': name, 'error': str(exc), 'parameters': params}
            # An unsupported solver configuration is not a model prediction.
            # Preserve the completed baseline and do not bypass CLASS's guard.
            break
        finally:
            cosmo.struct_cleanup()
            cosmo.empty()
    reference = spectra.get('pressureless_cdm_slot')
    comparisons = {k: spectrum_comparison(reference, spectra[k]) for k in spectra if k != 'pressureless_cdm_slot'}
    result = {'scope': __doc__, 'status': 'solver_comparison_unavailable' if failure else 'diagnostic_completed',
              'failure': failure,
              'finite_pressure_comparison_completed': 'finite_pressure_fluid_diagnostic' in comparisons,
              'bbn_source_sha256': hashlib.sha256(source_bytes).hexdigest(),
              'classy_library': str(libraries[0]),
              'classy_sha256': hashlib.sha256(libraries[0].read_bytes()).hexdigest(),
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'sound_speed_squared_requested': cp2, 'multipole_range': [30,2000],
              'scenarios': outputs, 'comparisons_to_pressureless': comparisons,
              'interpretation_limit': 'Fluid pressure is a sensitivity experiment, not a derived temporal-condensate action. No likelihood, refit, or exclusion significance is claimed.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    np.savez_compressed(output.with_suffix('.npz'), **{f'{name}_{key}':v for name,cl in spectra.items() for key,v in cl.items()})
    print(json.dumps({'status': result['status'], 'failure': failure, 'comparisons': comparisons}, indent=2))
    return 2 if failure else 0


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output',type=Path,default=ROOT/'results/step_25_acoustic_pressure_audit.json')
    raise SystemExit(run(ap.parse_args().output))
