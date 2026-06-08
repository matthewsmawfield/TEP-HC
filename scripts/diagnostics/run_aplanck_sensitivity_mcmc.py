#!/usr/bin/env python3
"""
Sensitivity MCMC: A_planck prior [0.9, 1.25]
============================================
Runs Cobaya with identical settings to tep_hiclass_suite.yaml but with
A_planck uniform prior loosened from [0.9, 1.1] to [0.9, 1.25].
Output prefix: tep_hiclass_aplanck_sens
"""

import sys
import subprocess
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

CONFIG_PATH = PROJECT_ROOT / "data" / "cobaya" / "tep_hiclass_aplanck_sens.yaml"
CHAIN_DIR = PROJECT_ROOT / "results" / "mcmc_chains"
LOG_DIR = PROJECT_ROOT / "logs"

# Packages path (same logic as step_06)
EXTERNAL_PACKAGES = os.environ.get("COBAYA_EXTERNAL_PACKAGES", "")
EXISTING = Path(EXTERNAL_PACKAGES) if EXTERNAL_PACKAGES else PROJECT_ROOT.parent.parent / "TVP" / "TVP" / "data" / "external" / "cosmology_likelihoods"
LOCAL = PROJECT_ROOT / "data" / "external" / "cobaya_packages"
PACKAGES_PATH = EXISTING if EXISTING.exists() and (EXISTING / "data" / "planck_2018").exists() else LOCAL
os.environ["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)
os.environ["COBAYA_NOMPI"] = "1"

CONFIG_CONTENT = """# TEP-HC A_planck sensitivity test
# A_planck prior loosened to [0.9, 1.25]
theory:
  classy:
    path: external/hi_class/hi_class
    ignore_obsolete: true
    extra_args:
      output: tCl,pCl,lCl,mPk
      lensing: yes
      modes: s,t
      non_linear: halofit
      tep_mode: 'yes'
      z_T: 5.0
      n_T: 2.0

likelihood:
  planck_2018_lowl.TT: null
  planck_2018_lowl.EE: null
  planck_2018_lensing.native: null
  bao.sdss_dr12_consensus_final: null
  sn.pantheonplus: null

params:
  logA:
    prior: {min: 2.5, max: 3.5}
    ref: {dist: norm, loc: 3.044, scale: 0.014}
    proposal: 0.01
    drop: true
  A_s:
    value: 'lambda logA: 1e-10*np.exp(logA)'
  n_s:
    prior: {min: 0.94, max: 1.0}
    ref: {dist: norm, loc: 0.966, scale: 0.004}
    proposal: 0.004
  H0:
    prior: {min: 40, max: 100}
    ref: {dist: norm, loc: 67.4, scale: 0.5}
    proposal: 1.5
  omega_b:
    prior: {min: 0.005, max: 0.1}
    ref: {dist: norm, loc: 0.0224, scale: 0.0002}
    proposal: 0.0003
  omega_cdm:
    prior: {min: 0.01, max: 0.99}
    ref: {dist: norm, loc: 0.12, scale: 0.001}
    proposal: 0.0015
  tau_reio:
    prior: {min: 0.01, max: 0.8}
    ref: {dist: norm, loc: 0.054, scale: 0.007}
    proposal: 0.01
  A_planck:
    prior: {min: 0.9, max: 1.25}
    ref: {dist: norm, loc: 1.0, scale: 0.0025}
    proposal: 0.005
  epsilon_T:
    prior: {min: -1.0, max: 1.0}
    ref: {dist: norm, loc: 0.006, scale: 0.005}
    proposal: 0.0005
    latex: '\\epsilon_T'
  sigma8:
    latex: '\\sigma_8'

sampler:
  mcmc:
    burn_in: 0
    max_tries: 10000
    max_samples: 500000
    Rminus1_stop: 0.05
    Rminus1_cl_stop: 0.2
    output_every: 10
    learn_proposal: true
    learn_proposal_Rminus1_max_early: 100.0
    fallback_covmat_scale: 3
    drag: true
    seed: 99

output: results/mcmc_chains/tep_hiclass_aplanck_sens
resume: false
"""

def main():
    # Write config
    with open(CONFIG_PATH, 'w') as f:
        f.write(CONFIG_CONTENT)
    print(f"Wrote config: {CONFIG_PATH}")

    # Clean old files for this prefix
    prefix = "tep_hiclass_aplanck_sens"
    for pattern in [f"{prefix}*.txt", f"{prefix}*.progress", f"{prefix}*.covmat",
                    f"{prefix}*.checkpoint", f"{prefix}*.updated.yaml", f"{prefix}*.input.yaml"]:
        for f in CHAIN_DIR.glob(pattern):
            print(f"Removing old: {f.name}")
            f.unlink()

    # Run cobaya
    cmd = ["cobaya-run", str(CONFIG_PATH)]
    logfile = LOG_DIR / "aplanck_sensitivity_mcmc.log"
    print(f"Launching Cobaya (log: {logfile})")
    env = os.environ.copy()
    env["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)
    env["COBAYA_NOMPI"] = "1"

    with open(logfile, 'w') as lf:
        result = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env)

    print(f"Cobaya finished with return code {result.returncode}")
    if result.returncode != 0:
        # Print tail of log
        lines = logfile.read_text().split('\n')
        print("\n".join(lines[-30:]))
        raise RuntimeError("Cobaya failed")

    print("Run complete. Analyze with scripts/diagnostics/analyze_aplanck_sens.py")

if __name__ == "__main__":
    main()
