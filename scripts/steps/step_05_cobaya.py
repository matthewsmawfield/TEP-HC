#!/usr/bin/env python3
"""
Step 05: Cobaya MCMC Setup
==========================
Configures the Cobaya MCMC pipeline with the full cosmological suite:
Planck 2018 + BAO (SDSS DR16) + Pantheon+ SNIa.

Outputs:
    - logs/step_05_cobaya_full.log
    - data/cobaya/tep_hiclass_suite.yaml
    - data/cobaya/lcdm_comparison.yaml
"""

import sys
import json
import yaml
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status

HICLASS_PATH = (PROJECT_ROOT / "external" / "hi_class" / "hi_class").resolve()
_HICLASS_PATH_PLACEHOLDER = "__HICLASS_PATH__"


COBAYA_CONFIG_TEMPLATE = """# TEP-HC hi_class Configuration
# ===========================
# Native TEP background-only implementation (TEP-C0, Paper 26)
# H_TEP(z) = H_LCDM(z) * M(z)
#   M(z) = A(z) / (1 - alpha_A(z))  [exact Jordan-frame factor]
# Standard GR perturbations; only background H(z) is modified.
# Likelihoods: Planck 2018 low-l TT/EE + lensing + BAO + Pantheon+

theory:
  classy:
    path: __HICLASS_PATH__
    ignore_obsolete: true
    extra_args:
      output: tCl,pCl,lCl,mPk
      lensing: yes
      modes: s,t
      non_linear: halofit
      # Native TEP background-only Hubble modification
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
    prior: {min: 0.9, max: 1.1}
    ref: {dist: norm, loc: 1.0, scale: 0.0025}
    proposal: 0.005
  epsilon_T:
    prior: {min: -1.0, max: 1.0}
    ref: {dist: norm, loc: 0.018, scale: 0.005}
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
    seed: 42

output: results/mcmc_chains/tep_hiclass_suite
resume: false
"""

COBAYA_CONFIG_LCDM = """# TEP-HC LambdaCDM Comparison Configuration
# =========================================
# Standard LCDM with identical likelihoods to tep_hiclass_suite.yaml
# (low-l TT/EE + lensing + BAO + Pantheon+; no high-l Plik).
# Optional reference run only; step 07 does not use this for evidence.

theory:
  classy:
    path: __HICLASS_PATH__
    ignore_obsolete: true
    extra_args:
      output: tCl,pCl,lCl,mPk
      lensing: yes
      modes: s,t
      non_linear: halofit

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
    prior: {min: 0.9, max: 1.1}
    ref: {dist: norm, loc: 1.0, scale: 0.0025}
    proposal: 0.005
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
    seed: 43

output: results/mcmc_chains/lcdm_comparison
resume: false
"""


def _inject_hiclass_path(template: str) -> str:
    return template.replace(_HICLASS_PATH_PLACEHOLDER, str(HICLASS_PATH))


class Step05Cobaya:
    """Step 05: Cobaya MCMC configuration (Full Suite)."""
    
    STEP_NAME = "05_cobaya"
    STEP_DESCRIPTION = "Cobaya MCMC Setup (Full Suite)"
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.cobaya_dir = self.root_dir / "data" / "cobaya"
        self.cobaya_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}_full.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}_full", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute Cobaya setup for full suite."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }
        
        try:
            # Native TEP config is self-contained in the template
            config_path = self.cobaya_dir / "tep_hiclass_suite.yaml"
            with open(config_path, 'w') as f:
                f.write(_inject_hiclass_path(COBAYA_CONFIG_TEMPLATE))
            
            print_status(f"  ✓ Created {config_path} (native TEP background-only)", "SUCCESS")
            
            # Also generate LCDM comparison config
            lcdm_path = self.cobaya_dir / "lcdm_comparison.yaml"
            with open(lcdm_path, 'w') as f:
                f.write(_inject_hiclass_path(COBAYA_CONFIG_LCDM))
            print_status(f"  ✓ Created {lcdm_path} (ΛCDM comparison)", "SUCCESS")
            
            results["status"] = "SUCCESS"
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise
        
        return results


if __name__ == "__main__":
    step = Step05Cobaya()
    step.run()
