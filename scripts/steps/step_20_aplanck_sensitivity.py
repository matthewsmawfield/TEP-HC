#!/usr/bin/env python3
"""
Step 20: A_planck Prior Sensitivity Test
=========================================
Tests robustness of ε_T inference to Planck calibration prior truncation.
Widens A_planck prior from [0.9, 1.1] to [0.9, 1.25] and re-runs MCMC.
"""

import sys
import subprocess
import os
import json
import numpy as np
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status

# Set packages path
EXTERNAL_PACKAGES = os.environ.get("COBAYA_EXTERNAL_PACKAGES", "")
EXISTING_PACKAGES_PATH = Path(EXTERNAL_PACKAGES) if EXTERNAL_PACKAGES else PROJECT_ROOT.parent.parent / "TVP" / "TVP" / "data" / "external" / "cosmology_likelihoods"
LOCAL_PACKAGES_PATH = PROJECT_ROOT / "data" / "external" / "cobaya_packages"

if EXISTING_PACKAGES_PATH.exists() and (EXISTING_PACKAGES_PATH / "data" / "planck_2018").exists():
    PACKAGES_PATH = EXISTING_PACKAGES_PATH
else:
    PACKAGES_PATH = LOCAL_PACKAGES_PATH

os.environ["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)
os.environ["COBAYA_NOMPI"] = "1"


class Step20AplanckSensitivity:
    """Step 20: A_planck prior sensitivity test."""

    STEP_NAME = "step_20_aplanck_sensitivity"
    STEP_DESCRIPTION = "A_planck prior sensitivity test: widens prior to [0.9, 1.25]"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.config_path = self.root_dir / "data" / "cobaya" / "tep_hiclass_aplanck_sens.yaml"
        self.chain_dir = self.root_dir / "results" / "mcmc_chains"
        self.output_path = self.root_dir / "results" / "step_20_aplanck_sensitivity.json"
        self.log_path = self.log_dir / f"{self.STEP_NAME}_full.log"
        
        # Clear log file at start of new run
        if self.log_path.exists():
            self.log_path.unlink()

    def check_no_running_cobaya(self, logger):
        """Ensure no other Cobaya processes are running."""
        try:
            result = subprocess.run(["pgrep", "-f", "cobaya-run"], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                if pids and pids[0]:
                    logger.warning(f"Found running Cobaya processes: {pids}")
                    logger.info("Killing existing Cobaya processes...")
                    for pid in pids:
                        try:
                            subprocess.run(["kill", pid], capture_output=True)
                            logger.info(f"Killed process {pid}")
                        except Exception as e:
                            logger.warning(f"Could not kill process {pid}: {e}")
                    time.sleep(1)
        except Exception as e:
            logger.warning(f"Could not check for running Cobaya processes: {e}")

    def clean_old_chains(self, logger):
        """Remove old chain files for this run."""
        prefix = "tep_hiclass_aplanck_sens"
        patterns = [f"{prefix}*.txt", f"{prefix}*.progress", f"{prefix}*.covmat",
                    f"{prefix}*.checkpoint", f"{prefix}*.updated.yaml", f"{prefix}*.input.yaml",
                    f"{prefix}*.locked"]
        
        for pattern in patterns:
            for f in self.chain_dir.glob(pattern):
                try:
                    f.unlink()
                    logger.info(f"Removed old chain file: {f.name}")
                except Exception as e:
                    logger.warning(f"Could not remove {f.name}: {e}")
        
        # Wait a moment to ensure file system cleanup
        time.sleep(0.5)

    def run_mcmc(self, logger):
        """Execute Cobaya MCMC with widened A_planck prior."""
        logger.process("Starting A_planck sensitivity MCMC run...")
        
        cmd = ["cobaya-run", str(self.config_path)]
        env = os.environ.copy()
        env["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)
        env["COBAYA_NOMPI"] = "1"

        # Run Cobaya with live logging
        logger.info(f"Running: {' '.join(cmd)}")
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                  stdin=subprocess.DEVNULL, env=env, text=True)
        
        # Stream output to log
        for line in process.stdout:
            logger.info(line.strip())
        
        process.wait()
        
        if process.returncode != 0:
            logger.error("Cobaya MCMC failed")
            raise RuntimeError("Cobaya MCMC failed")
        
        logger.success("Cobaya MCMC completed successfully")

    def analyze_results(self, logger):
        """Parse chain results and compute statistics."""
        logger.process("Analyzing MCMC results...")
        
        # Load chain
        chain_file = self.chain_dir / "tep_hiclass_aplanck_sens.1.txt"
        if not chain_file.exists():
            raise FileNotFoundError(f"Chain file not found: {chain_file}")
        
        chain = np.loadtxt(chain_file)
        
        # Parse header
        with open(chain_file) as f:
            header = f.readline().strip('#').split()
        
        # Create parameter mapping
        param_map = {name: i for i, name in enumerate(header)}
        
        # Extract key parameters
        epsilon_T_idx = param_map['epsilon_T']
        A_planck_idx = param_map['A_planck']
        H0_idx = param_map['H0']
        
        epsilon_T = chain[:, epsilon_T_idx]
        A_planck = chain[:, A_planck_idx]
        H0 = chain[:, H0_idx]
        
        # Compute statistics
        results = {
            "run_name": "tep_hiclass_aplanck_sens",
            "description": "A_planck widened-prior sensitivity test with covmat",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "n_chains": 4,
            "samples_per_chain": len(chain) // 4,
            "total_samples": len(chain),
            "parameters": {
                "epsilon_T": {
                    "mean": float(np.mean(epsilon_T)),
                    "std": float(np.std(epsilon_T)),
                    "median": float(np.median(epsilon_T)),
                    "min": float(np.min(epsilon_T)),
                    "max": float(np.max(epsilon_T))
                },
                "A_planck": {
                    "mean": float(np.mean(A_planck)),
                    "std": float(np.std(A_planck)),
                    "median": float(np.median(A_planck)),
                    "min": float(np.min(A_planck)),
                    "max": float(np.max(A_planck))
                },
                "H0": {
                    "mean": float(np.mean(H0)),
                    "std": float(np.std(H0)),
                    "median": float(np.median(H0)),
                    "min": float(np.min(H0)),
                    "max": float(np.max(H0))
                }
            }
        }
        
        # Load progress file for convergence info
        progress_file = self.chain_dir / "tep_hiclass_aplanck_sens.progress"
        if progress_file.exists():
            with open(progress_file) as f:
                lines = f.readlines()
                if len(lines) > 1:
                    last_line = lines[-1].split()
                    if len(last_line) >= 5:
                        results["max_Rminus1"] = float(last_line[4])
        
        return results

    def run(self):
        """Execute the full A_planck sensitivity test."""
        logger = TEPLogger(self.STEP_NAME, self.log_path)
        set_step_logger(logger)
        
        logger.info("=" * 60)
        logger.info(f"Step {self.STEP_NAME}: A_planck Prior Sensitivity Test")
        logger.info("=" * 60)
        
        # Check for running Cobaya processes
        self.check_no_running_cobaya(logger)
        
        # Clean old chains
        self.clean_old_chains(logger)
        
        # Run MCMC
        self.run_mcmc(logger)
        
        # Analyze results
        results = self.analyze_results(logger)
        
        # Save results
        with open(self.output_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        logger.success(f"Results saved to {self.output_path}")
        logger.info(f"ε_T = {results['parameters']['epsilon_T']['mean']:.4f} ± {results['parameters']['epsilon_T']['std']:.4f}")
        logger.info(f"A_planck = {results['parameters']['A_planck']['mean']:.4f} ± {results['parameters']['A_planck']['std']:.4f}")
        
        logger.success(f"Step {self.STEP_NAME} completed successfully")
        return results


def main():
    step = Step20AplanckSensitivity()
    step.run()


if __name__ == "__main__":
    main()
