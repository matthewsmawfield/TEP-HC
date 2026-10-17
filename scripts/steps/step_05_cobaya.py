#!/usr/bin/env python3
"""
Step 05: Cobaya MCMC Setup
==========================
Configures the Cobaya MCMC pipeline with the full cosmological suite:
Planck 2018 + BAO (SDSS DR12) + Pantheon+ SNIa.

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

# Relative to project root; Cobaya is always launched from PROJECT_ROOT (step 06).
HICLASS_REL_PATH = "external/hi_class/hi_class"
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

COBAYA_CONFIG_TEP_PERT = """# TEP-HC Active Perturbation Configuration
# ========================================
# TEP minimal-conformal perturbation closure (TEP-HC v0.4).
# H_TEP(z) = H_LCDM(z) * M(z)  [background]
# Scalar fluctuations evolved via hi_class SMG EFT (gravity_model = tep).
# Likelihoods: Planck 2018 low-l TT/EE + lensing + BAO + Pantheon+

theory:
  classy:
    path: __HICLASS_PATH__
    ignore_obsolete: true
    extra_args:
      output: tCl,pCl,lCl,mPk
      lensing: yes
      modes: s
      non_linear: halofit
      # Native TEP background Hubble modification
      tep_mode: 'yes'
      z_T: 5.0
      n_T: 2.0
      # Active scalar perturbation closure (delta-phi variable; x_smg =
      # dphi/phi' is singular at the alpha_A=0 turnover z~2.6)
      gravity_model: 'tep'
      M2_evolution: 'yes'
      use_pert_var_deltaphi_smg: 'yes'
      pert_initial_conditions_smg: 'zero'
      # S_Sigma = 1 (unscreened cosmological scalar, TEP-C0); tep_kin_boost
      # = 10 -> wc = +700 (production value, gravity_smg/tep.c): large
      # kineticity decouples the scalar so the SMG spectra track the
      # tep_mode background-only result to ~1-3%. wc = +7 (K=1) leaves the
      # scalar strongly coupled: TT amplified ~14x at l=10 and lensing
      # power suppressed, giving -inf posterior everywhere.
      tep_screening_s: 1.0
      tep_kin_boost: 10.0

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
    seed: 44

output: results/mcmc_chains/tep_hiclass_perturbations
resume: false
"""


def _inject_hiclass_path(template: str) -> str:
    return template.replace(_HICLASS_PATH_PLACEHOLDER, HICLASS_REL_PATH)


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
            # Current checked-in production configurations take precedence over
            # fallback templates. Re-running setup must not silently change the
            # priors, likelihoods, or screening parameters of an existing run.
            specifications = [
                ("tep_hiclass_suite.yaml", COBAYA_CONFIG_TEMPLATE),
                ("lcdm_comparison.yaml", COBAYA_CONFIG_LCDM),
                ("tep_hiclass_perturbations.yaml", COBAYA_CONFIG_TEP_PERT),
            ]
            results["configs_written"] = []
            results["configs_preserved"] = []
            for filename, template in specifications:
                path = self.cobaya_dir / filename
                if path.exists():
                    info = yaml.safe_load(path.read_text())
                    if not isinstance(info, dict) or any(
                        key not in info for key in ("theory", "likelihood", "params", "sampler", "output")
                    ):
                        raise ValueError(f"Invalid production configuration: {path}")
                    results["configs_preserved"].append(str(path))
                    print_status(f"  Preserved production configuration: {path}", "SUCCESS")
                else:
                    path.write_text(_inject_hiclass_path(template))
                    results["configs_written"].append(str(path))
                    print_status(f"  Created fallback configuration: {path}", "SUCCESS")

            results["status"] = "SUCCESS"

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            raise

        return results


if __name__ == "__main__":
    step = Step05Cobaya()
    step.run()
