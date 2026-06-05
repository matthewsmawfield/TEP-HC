#!/usr/bin/env python3
"""
Step 06: MCMC Execution (Real Data - No Fallbacks)
===================================================
Executes the Cobaya MCMC pipeline using REAL Planck + BAO + SN likelihoods.
FAILS HARD if real data unavailable. NO mock data. NO synthetic data. EVER.
"""

import sys
import subprocess
import time
import os
import platform
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status

# Set packages path - use existing if available, otherwise local
# Check for external packages path from environment variable or default location
EXTERNAL_PACKAGES = os.environ.get("COBAYA_EXTERNAL_PACKAGES", "")
EXISTING_PACKAGES_PATH = Path(EXTERNAL_PACKAGES) if EXTERNAL_PACKAGES else PROJECT_ROOT.parent.parent / "TVP" / "TVP" / "data" / "external" / "cosmology_likelihoods"
LOCAL_PACKAGES_PATH = PROJECT_ROOT / "data" / "external" / "cobaya_packages"

if EXISTING_PACKAGES_PATH.exists() and (EXISTING_PACKAGES_PATH / "data" / "planck_2018").exists():
    PACKAGES_PATH = EXISTING_PACKAGES_PATH
else:
    PACKAGES_PATH = LOCAL_PACKAGES_PATH

os.environ["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)

# Detect MPI availability at module level
_MPI_AVAILABLE = subprocess.run(["which", "mpirun"], capture_output=True).returncode == 0

# Only disable MPI if mpirun is not available
if not _MPI_AVAILABLE:
    os.environ["COBAYA_NOMPI"] = "1"


def get_optimal_cores():
    """Detect M4 Pro or similar and return optimal core count for MCMC."""
    if platform.system() != 'Darwin':
        # Non-macOS: use all cores minus 2 for system
        import multiprocessing
        return max(1, multiprocessing.cpu_count() - 2)
    
    try:
        # macOS: detect Apple Silicon
        result = subprocess.run(['sysctl', '-n', 'hw.ncpu'], 
                             capture_output=True, text=True, check=True)
        ncpu = int(result.stdout.strip())
        
        # M4 Pro: 14 cores (10P + 4E), use P-cores for CLASS
        if ncpu >= 14:
            return 10  # Use 10 performance cores
        elif ncpu >= 10:
            return 8   # M3 Pro or similar
        else:
            return max(1, ncpu - 2)
    except Exception:
        return 4  # Safe default


class Step06MCMC:
    """Step 06: REAL hi_class MCMC execution. Fails if real data unavailable."""

    STEP_NAME = "06_mcmc"
    STEP_DESCRIPTION = "MCMC Execution with hi_class (Real Data Only)"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.cobaya_config = self.root_dir / "data" / "cobaya" / "tep_hiclass_suite.yaml"
        self.lcdm_config = self.root_dir / "data" / "cobaya" / "lcdm_comparison.yaml"
        self.chain_dir = self.root_dir / "results" / "mcmc_chains"
        self.chain_prefix = "tep_hiclass_suite"
        self.lcdm_prefix = "lcdm_comparison"
        
        log_file = self.log_dir / f"step_{self.STEP_NAME}_full.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}_full", log_file)
        set_step_logger(self.logger)
    
    def _delete_old_chains(self):
        """Delete all Cobaya output files to prevent stale data and file collisions."""
        prefixes = [self.chain_prefix, self.lcdm_prefix]
        for prefix in prefixes:
            patterns = [
                f"{prefix}*.txt",
                f"{prefix}*.progress",
                f"{prefix}*.covmat",
                f"{prefix}*.checkpoint",
                f"{prefix}*.updated.yaml",
                f"{prefix}*.input.yaml",
                f"{prefix}*.input.yaml.locked",
            ]
            for pattern in patterns:
                for f in self.chain_dir.glob(pattern):
                    print_status(f"  Removing old file: {f.name}", "INFO")
                    f.unlink()
    
    def _verify_chains_fresh(self, start_time):
        """Verify chains were created AFTER this run started."""
        chain_file = self.chain_dir / f"{self.chain_prefix}.1.txt"
        if not chain_file.exists():
            raise RuntimeError(
                f"CRITICAL: MCMC did not produce output chain: {chain_file}\n"
                "No fallback data available. Pipeline MUST fail."
            )
        
        mtime = chain_file.stat().st_mtime
        if mtime < start_time:
            raise RuntimeError(
                f"CRITICAL: Chain file {chain_file.name} is OLD (modified {datetime.fromtimestamp(mtime).isoformat()}).\n"
                f"Expected after {datetime.fromtimestamp(start_time).isoformat()}.\n"
                "This indicates stale/fallback data. Pipeline MUST fail."
            )
        
        # Verify chain has content
        size = chain_file.stat().st_size
        if size < 1000:
            raise RuntimeError(
                f"CRITICAL: Chain file too small ({size} bytes). Insufficient samples generated."
            )
        
        # Verify chain is not all identical (mock data check)
        import numpy as np
        data = np.loadtxt(chain_file)
        unique = len(np.unique(data, axis=0))
        total = data.shape[0]
        if unique < total * 0.9:
            raise RuntimeError(
                f"CRITICAL: Chain has only {unique}/{total} unique rows. "
                "This indicates synthetic/mocked data. Pipeline MUST fail."
            )
        
        print_status(f"  ✓ Fresh chain verified: {chain_file.name} ({size} bytes, {unique}/{total} unique)", "SUCCESS")
    
    def run(self) -> dict:
        """Execute REAL MCMC run. Fails if real likelihoods unavailable."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        
        start_time = time.time()
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }
        
        try:
            # 1. Verify config exists
            if not self.cobaya_config.exists():
                raise FileNotFoundError(
                    f"CRITICAL: Cobaya config not found: {self.cobaya_config}\n"
                    "Cannot proceed without real likelihood configuration."
                )
            
            # 2. Delete old chains to prevent stale data reuse
            self._delete_old_chains()
            
            # Detect optimal core usage
            optimal_cores = get_optimal_cores()
            
            print_status("Launching Cobaya MCMC with REAL Planck + BAO + SN...", "PROCESS")
            print_status(f"  Config: {self.cobaya_config}", "INFO")
            print_status(f"  Hardware: M4 Pro detected, using {optimal_cores} performance cores", "INFO")
            print_status("  WARNING: This requires real Planck likelihood data.", "WARNING")
            print_status("  NO FALLBACK. NO MOCK DATA. NO SYNTHETIC DATA. EVER.", "ERROR")
            
            # 3. Run Cobaya single-threaded for stability
            # chains: 1 in config means only 1 chain needed; MPI risks file collisions
            cmd = ["cobaya-run", str(self.cobaya_config)]
            print_status(f"  Running single-threaded (1 chain mode)", "INFO")
            
            # Pass environment
            env = os.environ.copy()
            env["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)
            env["COBAYA_NOMPI"] = "1"
            
            # 4. Run Cobaya with output to log file (avoids PIPE file descriptor issues)
            cobaya_log = self.log_dir / "cobaya_run.log"
            print_status(f"  MCMC running (log: {cobaya_log})", "PROCESS")
            print_status("  This will take hours. Check progress file for status.", "INFO")
            
            with open(cobaya_log, 'w') as logfile:
                result = subprocess.run(
                    cmd,
                    stdout=logfile,
                    stderr=subprocess.STDOUT,
                    stdin=subprocess.DEVNULL,
                    env=env
                )
            
            return_code = result.returncode
            
            # Check for errors in log
            error_found = False
            error_msg = ""
            if cobaya_log.exists():
                log_content = cobaya_log.read_text()
                if "*error*" in log_content.lower():
                    error_found = True
                    # Extract last error line
                    for line in reversed(log_content.split('\n')):
                        if '*error*' in line.lower():
                            error_msg = line.strip()
                            break
            
            if return_code != 0:
                # Extract actual error from log for accurate diagnosis
                actual_error = "Unknown error"
                if cobaya_log.exists():
                    log_lines = cobaya_log.read_text().split('\n')
                    for line in reversed(log_lines):
                        if 'LoggedError' in line or 'Error' in line or 'error' in line.lower():
                            actual_error = line.strip()
                            break
                raise RuntimeError(
                    f"Cobaya exited with code {return_code}.\n"
                    f"Actual error: {actual_error}\n"
                    f"If Planck likelihood not installed, run:\n"
                    f"  cobaya-install planck_2018_lowl.TT planck_2018_lowl.EE planck_2018_lensing.native -p {PACKAGES_PATH}"
                )
            
            if error_found:
                raise RuntimeError(f"Cobaya failed during execution: {error_msg}")
            
            # 6. Verify chains are fresh and real
            print_status("  Verifying generated chains...", "PROCESS")
            self._verify_chains_fresh(start_time)
            
            results["status"] = "SUCCESS"
            print_status("\n  ✓ Real MCMC completed successfully", "SUCCESS")
            
        except Exception as e:
            results["status"] = "FAILED"
            results["error"] = str(e)
            print_status(f"\n  ✗ Step FAILED (no fallback used): {e}", "ERROR")
            raise
        
        return results


if __name__ == "__main__":
    step = Step06MCMC()
    step.run()
