#!/usr/bin/env python3
"""Pressure sensitivity by an explicit w -> 0- sequence in the supported fluid solver.

This tests a phenomenological near-dust limit, not an action-derived TEP fluid.
No CLASS guards are changed. Both the zero-sound-speed CDM control and the
finite-pressure sequence must converge before the limit is reported usable.
The fluid density is counted in the metric sources, but CLASS's conventional
sigma8 matter selection is not used to compare a fluid with CDM.
"""
import hashlib
import json
import sys
from pathlib import Path
import numpy as np
from step_25_acoustic_pressure_audit import ROOT, CORPUS, spectrum_comparison


def run():
    source = CORPUS/'TEP-BBN/results/step_20_ambient_bath_front.json'
    bbn = json.loads(source.read_text())['F_boundary_perturbation_spectrum']
    exact = bbn['exact_boltzmann_two_branch_closure']
    cp2 = bbn['perturbation_mode_closure']['quadratic_action_coefficients']['c_p_eff_squared_derived']
    libraries = sorted((ROOT/'external/hi_class/hi_class').glob('build/lib.*/classy*.so'))
    if len(libraries) != 1: raise RuntimeError('Expected one local CLASS library')
    sys.path.insert(0,str(libraries[0].parent))
    import classy
    if Path(classy.__file__).resolve()!=libraries[0].resolve(): raise RuntimeError('Unexpected CLASS library')
    H0=exact['H0_km_s_Mpc']; density=exact['omega_phi_derived_clock_slope']
    base={'output':'tCl,pCl,lCl','lensing':'yes','l_max_scalars':2500,
          'H0':H0,'omega_b':exact['omega_b'],'A_s':float(np.exp(3.044)*1e-10),
          'n_s':.9686,'tau_reio':.0479,'tep_mode':'yes','z_T':5.,'n_T':2.,
          'epsilon_T':.00488,'gauge':'newtonian'}
    spectra={}; records={}; failure=None
    scenarios={'cdm':{'omega_cdm':density}}
    sequence=[-1e-2,-1e-3,-1e-4,-1e-5,-1e-6,-1e-7]
    for i,w in enumerate(sequence):
        for tag,sound in [('zero',0.),('pressure',cp2)]:
            scenarios[f'{tag}_{i}']={'omega_cdm':0.,'Omega_fld':density/(H0/100)**2,
                                    'w0_fld':w,'wa_fld':0.,'cs2_fld':sound,'use_ppf':'no'}
    for name,params in scenarios.items():
        print('Computing',name,flush=True);model=classy.Class()
        try:
            model.set(dict(base,**params));model.compute()
            spectra[name]={k:np.asarray(v).copy() for k,v in model.lensed_cl(2500).items()}
            if not all(np.all(np.isfinite(a)) for a in spectra[name].values()):
                raise ValueError('Non-finite spectrum')
            records[name]={'parameters':dict(base,**params)}
        except Exception as exc:
            failure={'scenario':name,'type':type(exc).__name__,'message':str(exc)};break
        finally:
            model.struct_cleanup();model.empty()
    checks={}; comparisons={}
    def metric(report):
        return max(v.get('rms_fractional_change',v.get('rms_change_over_sqrt_TT_EE',float('inf'))) for v in report.values())
    if failure is None:
        for i in range(len(sequence)):
            comparisons[f'zero_{i}_vs_cdm']=spectrum_comparison(spectra['cdm'],spectra[f'zero_{i}'])
            comparisons[f'pressure_{i}_vs_zero']=spectrum_comparison(spectra[f'zero_{i}'],spectra[f'pressure_{i}'])
        for tag in ('zero','pressure'):
            comparisons[f'{tag}_last_step']=spectrum_comparison(spectra[f'{tag}_{len(sequence)-2}'],spectra[f'{tag}_{len(sequence)-1}'])
            checks[f'{tag}_sequence_rms_below_0p5percent']=metric(comparisons[f'{tag}_last_step'])<.005
        checks['zero_pressure_control_rms_below_0p5percent']=metric(comparisons[f'zero_{len(sequence)-1}_vs_cdm'])<.005
    out={'scope':__doc__,'status':('solver_comparison_unavailable' if failure else
          'controlled_near_dust_limit_completed' if all(checks.values()) else 'limit_not_validated'),
         'failure':failure,'checks':checks,'w_sequence':sequence,'sound_speed_squared_prescribed':cp2,
         'multipole_range':[30,2000],'comparisons':comparisons,'scenarios':records,
         'limitations':['Finite negative-w sequence; not an exact w=0 integration.',
                        'No likelihood or parameter refit; pressure response does not validate its action origin.',
                        'Convergence is tested over this sequence and multipole range, not every numerical setting.'],
         'provenance':{'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       'bbn_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                       'classy_sha256':hashlib.sha256(libraries[0].read_bytes()).hexdigest()}}
    path=ROOT/'results/step_26_near_dust_pressure_limit.json'
    path.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    np.savez_compressed(path.with_suffix('.npz'),**{f'{n}_{k}':v for n,s in spectra.items() for k,v in s.items()})
    print(out['status'],checks,flush=True)
    return 0 if out['status']=='controlled_near_dust_limit_completed' else 2

if __name__=='__main__': raise SystemExit(run())
