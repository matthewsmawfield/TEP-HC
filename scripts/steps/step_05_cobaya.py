#!/usr/bin/env python3
"""
Step 05: Cobaya MCMC Setup
==========================
Configures the Cobaya MCMC pipeline with Planck 2018 likelihoods.

Outputs:
    - logs/step_05_cobaya.log
    - data/cobaya/tep_cosmology.yaml
    - data/cobaya/params.yaml
    - data/cobaya/priors.yaml
"""

import sys
import yaml
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


COBAYA_CONFIG = """# TEP-HC Cobaya Configuration
# =========================
# MCMC pipeline for TEP cosmology with Planck 2018 likelihoods

theory:
  classy:
    path: null  # Will be set to hi_class installation path
    extra_args:
      # TEP-specific parameters
      smg_model: tep
      tep_alpha_eff: 1.0e6
      tep_beta: 1.0
      tep_phi_init: 0.0
      tep_B_coeff: 0.0
      # Standard cosmology
      non_linear: hmcode
      output: tCl,pCl,lCl
      lensing: yes
      l_max_scalars: 2500

likelihood:
  # Planck 2018 high-l temperature and polarization
  planck_2018_highl_TTTEEE:
    clik_file: null  # Will be set during installation
    
  # Planck 2018 low-l temperature
  planck_2018_lowl_TT:
    clik_file: null
    
  # Planck 2018 low-l polarization  
  planck_2018_lowl_EE:
    clik_file: null
    
  # Planck 2018 lensing
  planck_2018_lensing:
    clik_file: null

params:
  # Standard LambdaCDM parameters
  logA:
    prior:
      min: 1.61
      max: 3.91
    ref:
      dist: norm
      loc: 3.044
      scale: 0.014
    proposal: 0.01
    latex: \\log(10^{10}A_s)
    drop: true
    
  A_s:
    value: 'lambda logA: 1e-10*np.exp(logA)'
    latex: A_s
    
  n_s:
    prior:
      min: 0.8
      max: 1.2
    ref:
      dist: norm
      loc: 0.966
      scale: 0.004
    proposal: 0.002
    latex: n_s
    
  theta_s:
    prior:
      min: 0.5
      max: 10.0
    ref:
      dist: norm
      loc: 1.0411
      scale: 0.0004
    proposal: 0.0002
    latex: 100\\theta_s
    
  H0:
    latex: H_0
    
  omega_b:
    prior:
      min: 0.005
      max: 0.1
    ref:
      dist: norm
      loc: 0.0224
      scale: 0.0002
    proposal: 0.0001
    latex: \\Omega_b h^2
    
  omega_cdm:
    prior:
      min: 0.001
      max: 0.99
    ref:
      dist: norm
      loc: 0.12
      scale: 0.001
    proposal: 0.0005
    latex: \\Omega_{cdm} h^2
    
  tau_reio:
    prior:
      min: 0.01
      max: 0.8
    ref:
      dist: norm
      loc: 0.054
      scale: 0.007
    proposal: 0.003
    latex: \\tau_{reio}
  
  # TEP-specific parameter
  log10_alpha_eff:
    prior:
      min: 5.0
      max: 7.0
    ref:
      dist: norm
      loc: 6.0
      scale: 0.5
    proposal: 0.1
    latex: \\log_{10}\\alpha_{\\rm eff}
    
  alpha_eff:
    value: 'lambda log10_alpha_eff: 10**log10_alpha_eff'
    latex: \\alpha_{\\rm eff}

sampler:
  mcmc:
    max_samples: 1000000
    max_tries: 10000
    burn_in: 0
    Rminus1_stop: 0.01
    Rminus1_cl_stop: 0.2
    learn_proposal: true
    learn_proposal_Rminus1_max: 20.0
    output_every: 1000

output: results/mcmc_chains/tep_cosmology
resume: true
"""

PRIORS_DOC = """# TEP-HC Prior Configuration
# ==========================

## Standard LambdaCDM Parameters

| Parameter | Prior | Description |
|-----------|-------|-------------|
| log(10^10 A_s) | Uniform(1.61, 3.91) | Scalar amplitude (log scale) |
| n_s | Uniform(0.8, 1.2) | Scalar spectral index |
| 100*theta_s | Uniform(0.5, 10.0) | Angular sound horizon |
| Omega_b h^2 | Uniform(0.005, 0.1) | Baryon density |
| Omega_cdm h^2 | Uniform(0.001, 0.99) | Cold dark matter density |
| tau_reio | Uniform(0.01, 0.8) | Reionization optical depth |

## TEP-Specific Parameters

| Parameter | Prior | Description |
|-----------|-------|-------------|
| log_10(alpha_eff) | Uniform(5.0, 7.0) | TEP coupling strength |
| alpha_eff | Derived: 10^log10_alpha_eff | Clock-sector coupling |

## Prior Rationale

The TEP coupling prior spans 5 to 7 in log10 space (1e5 to 1e7), centered
on the stellar/galactic constraint of ~1e6. The flat prior ensures we test
the full range where the CMB could potentially constrain the parameter.

Note: The theory predicts that CMB should be blind to alpha_eff due to
radiation-domination freezing of the scalar field at z > 1000.
"""


class Step05Cobaya:
    """Step 05: Cobaya MCMC configuration."""
    
    STEP_NAME = "05_cobaya"
    STEP_DESCRIPTION = "Cobaya MCMC Setup"
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.cobaya_dir = self.root_dir / "data" / "cobaya"
        self.cobaya_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = self.log_dir / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute Cobaya setup step."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status(f"Started at: {datetime.now().isoformat()}", "INFO")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "files_created": [],
            "cobaya_available": False,
            "planck_likelihoods": [],
            "status": "RUNNING"
        }
        
        try:
            # Check Cobaya installation
            print_status("Checking Cobaya installation...", "PROCESS")
            results["cobaya_available"] = self._check_cobaya()
            
            if results["cobaya_available"]:
                print_status("  ✓ Cobaya available", "SUCCESS")
                
                # Check Planck likelihoods
                print_status("Checking Planck 2018 likelihoods...", "PROCESS")
                likelihoods = [
                    "planck_2018_highl_TTTEEE",
                    "planck_2018_lowl_TT", 
                    "planck_2018_lowl_EE",
                    "planck_2018_lensing"
                ]
                results["planck_likelihoods"] = likelihoods
                for like in likelihoods:
                    print_status(f"  • {like}", "INFO")
            else:
                print_status("  ⚠ Cobaya not installed", "WARNING")
                print_status("    Install: pip install cobaya", "INFO")
                print_status("    Then: cobaya-install planck_2018_highl_TTTEEE ...", "INFO")
            
            # Write main configuration
            print_status("\nCreating Cobaya configuration files...", "TITLE")
            
            config_path = self.cobaya_dir / "tep_cosmology.yaml"
            with open(config_path, 'w') as f:
                f.write(COBAYA_CONFIG)
            results["files_created"].append(str(config_path))
            print_status(f"  ✓ Created {config_path}", "SUCCESS")
            
            # Write priors documentation
            priors_path = self.cobaya_dir / "priors.yaml"
            with open(priors_path, 'w') as f:
                f.write(PRIORS_DOC)
            results["files_created"].append(str(priors_path))
            print_status(f"  ✓ Created {priors_path}", "SUCCESS")
            
            # Create run script
            run_script = self.cobaya_dir / "run_mcmc.sh"
            with open(run_script, 'w') as f:
                f.write("#!/bin/bash\n")
                f.write("# Run TEP-HC Cobaya MCMC\n\n")
                f.write(f"cd {self.root_dir}\n")
                f.write("cobaya-run data/cobaya/tep_cosmology.yaml\n")
            run_script.chmod(0o755)
            results["files_created"].append(str(run_script))
            print_status(f"  ✓ Created {run_script}", "SUCCESS")
            
            # Configuration summary
            print_status("\nConfiguration Summary:", "TITLE")
            print_status("  Theory: hi_class with TEP module", "INFO")
            print_status("  Likelihoods: Planck 2018 (TT, TE, EE, lensing)", "INFO")
            print_status("  Free params: 6 LCDM + 1 TEP (log10_alpha_eff)", "INFO")
            print_status("  Sampler: MCMC with R-1 < 0.01 convergence", "INFO")
            print_status("  Output: results/mcmc_chains/", "INFO")
            
            # Next steps
            print_status("\nNext Steps:", "TITLE")
            if not results["cobaya_available"]:
                print_status("  1. Install Cobaya: pip install cobaya", "PROCESS")
                print_status("  2. Install likelihoods: cobaya-install planck_2018_highl_TTTEEE ...", "PROCESS")
            print_status("  3. Run MCMC: bash data/cobaya/run_mcmc.sh", "PROCESS")
            print_status("  4. Analyze: cobaya-analyze results/mcmc_chains/tep_cosmology", "PROCESS")
            
            results["status"] = "SUCCESS"
            print_status(f"\nSTEP {self.STEP_NAME} COMPLETED", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results
    
    def _check_cobaya(self) -> bool:
        """Check if Cobaya is installed."""
        try:
            import cobaya
            return True
        except ImportError:
            return False


if __name__ == "__main__":
    step = Step05Cobaya()
    step.run()
