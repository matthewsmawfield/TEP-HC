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
from scripts.utils.chain_integrity import inspect_chain_prefix, require_completed_chains, assert_no_active_writer

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
    STEP_DESCRIPTION = "MCMC Execution with hi_class: background-only + active perturbations + native TTTEEE + LCDM TTTEEE reference (Real Data Only)"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.cobaya_config = self.root_dir / "data" / "cobaya" / "tep_hiclass_suite.yaml"
        self.pert_config = self.root_dir / "data" / "cobaya" / "tep_hiclass_perturbations.yaml"
        self.lcdm_config = self.root_dir / "data" / "cobaya" / "lcdm_comparison.yaml"
        self.ttteee_config = self.root_dir / "data" / "cobaya" / "tep_native_mcmc_ttteee.yaml"
        self.lcdm_ttteee_config = self.root_dir / "data" / "cobaya" / "lcdm_mcmc_ttteee.yaml"
        self.chain_dir = self.root_dir / "results" / "mcmc_chains"
        self.chain_prefix = "tep_hiclass_suite"
        self.pert_prefix = "tep_hiclass_perturbations"
        self.lcdm_prefix = "lcdm_comparison"
        self.ttteee_prefix = "tep_native_ttteee"
        self.lcdm_ttteee_prefix = "lcdm_ttteee"
        
        log_file = self.log_dir / f"step_{self.STEP_NAME}_full.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}_full", log_file)
        set_step_logger(self.logger)
    
    def _delete_old_chains(self):
        """Preserve incomplete/inconsistent state before starting a replacement.

        Valid unfinished collections remain resumable. No saved output is deleted.
        Learned proposal covariance can initialize a replacement without treating
        an inconsistent checkpoint as evidence of a completed run.
        """
        import shutil
        self._proposal_covmats = {}
        stamp = datetime.now().strftime('%Y%m%dT%H%M%S%f')
        for prefix in (self.chain_prefix, self.pert_prefix,
                       self.ttteee_prefix, self.lcdm_ttteee_prefix):
            base = self._chain_file(prefix).parent / prefix
            files = list(base.parent.glob(prefix + '.*'))
            if not files:
                continue
            assert_no_active_writer(base)
            report = inspect_chain_prefix(base)
            faults = [issue for issue in report['issues']
                      if issue != 'Sampler has not certified convergence']
            if not faults:
                continue
            archive = self.chain_dir / '_preserved' / stamp / prefix
            archive.mkdir(parents=True, exist_ok=False)
            for path in files:
                shutil.move(str(path), str(archive / path.name))
            covmat = archive / (prefix + '.covmat')
            if covmat.is_file():
                self._proposal_covmats[prefix] = str(covmat.resolve())
            print_status(f"  Preserved inconsistent output in {archive}: " +
                         '; '.join(faults), "WARNING")

    def _chain_file(self, prefix):
        """Chain file may live flat or in a per-run subdirectory."""
        nested = self.chain_dir / prefix / f"{prefix}.1.txt"
        return nested if nested.exists() or any(nested.parent.glob(prefix + ".*")) else self.chain_dir / f"{prefix}.1.txt"

    def _verify_chains_fresh(self, start_time, prefix):
        """Validate all saved ranks and their state, including a valid cached run.

        start_time is retained for caller compatibility. File freshness alone is
        insufficient, and a verified completed run need not be resampled.
        """
        base = self._chain_file(prefix).parent / prefix
        report = require_completed_chains(base)
        import json
        manifest = base.with_suffix('.manifest.json')
        manifest.write_text(json.dumps(report, indent=2) + '\n')
        print_status(f"  Verified {report['mpi_size']} chains, "
                     f"{report['raw_rows']} retained rows: {prefix}", "SUCCESS")
        return report

    def run(self) -> dict:
        """Execute REAL MCMC run. Fails if real likelihoods unavailable."""
        print_status("=" * 60, "INFO")
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status(f"Run started at: {datetime.now().isoformat()}", "INFO")
        print_status("=" * 60, "INFO")
        
        start_time = time.time()
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }
        
        try:
            # 1. Verify configs exist
            for cfg in [self.cobaya_config, self.pert_config,
                        self.ttteee_config, self.lcdm_ttteee_config]:
                if not cfg.exists():
                    raise FileNotFoundError(
                        f"CRITICAL: Cobaya config not found: {cfg}\n"
                        "Cannot proceed without real likelihood configuration."
                    )

            # 2. Preserve inconsistent outputs; resume consistent collections
            self._delete_old_chains()

            # Detect optimal core usage
            optimal_cores = get_optimal_cores()
            env = os.environ.copy()
            env["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)
            env["COBAYA_NOMPI"] = "1"

            # ---- Chain runs ----
            # All four chains are required. The converged background-only
            # chain resumes serially (fast), then the remaining chains run
            # CONCURRENTLY under MPI: `mpirun -np N` spawns N independent
            # walkers that share the learned proposal, giving ~Nx the samples
            # per hour and a proper multi-chain Gelman-Rubin diagnostic.
            # (label, config, log, prefix, results-key, required, mpi_ranks)
            runs = [
                ("background-only TEP", self.cobaya_config,
                 "cobaya_background.log", self.chain_prefix, "background_chain", True, 4),
                ("native TEP high-l TTTEEE", self.ttteee_config,
                 "cobaya_ttteee.log", self.ttteee_prefix, "ttteee_chain", True, 4),
                ("LCDM high-l TTTEEE reference", self.lcdm_ttteee_config,
                 "cobaya_lcdm_ttteee.log", self.lcdm_ttteee_prefix, "lcdm_ttteee_chain", True, 2),
                ("active perturbations", self.pert_config,
                 "cobaya_perturbations.log", self.pert_prefix, "perturbation_chain", True, 2),
            ]

            # Resume with the saved rank count, never a conflicting launch size.
            runs = [(label, cfg, log_name, prefix, key, required,
                     inspect_chain_prefix(self._chain_file(prefix).parent / prefix)['mpi_size']
                     if self._chain_file(prefix).exists() else np_ranks)
                    for label, cfg, log_name, prefix, key, required, np_ranks in runs]

            def _chain_cmd(cfg, prefix, np_ranks):
                import yaml
                chain_file = self._chain_file(prefix)
                if chain_file.exists():
                    extra = ["-r"]
                else:
                    extra = []  # fresh prefix: no destructive --force is needed
                    covmat = self._proposal_covmats.get(prefix)
                    if covmat:
                        info = yaml.safe_load(cfg.read_text())
                        info['sampler']['mcmc']['covmat'] = covmat
                        effective = self.log_dir / (prefix + '_recovery.yaml')
                        effective.write_text(yaml.safe_dump(info, sort_keys=False))
                        cfg = effective
                runner = [sys.executable, "-m", "cobaya.run", str(cfg)] + extra
                if np_ranks > 1:
                    return ["mpirun", "-np", str(np_ranks)] + runner
                return runner

            def _chain_env(np_ranks):
                e = env.copy()
                if np_ranks > 1:
                    e.pop("COBAYA_NOMPI", None)
                    e["OMP_NUM_THREADS"] = os.environ.get("TEP_MCMC_OMP_THREADS", "1")
                e["OPENBLAS_NUM_THREADS"] = "1"
                return e

            def _extract_error(chain_log):
                if chain_log.exists():
                    for line in reversed(chain_log.read_text().split('\n')):
                        if 'LoggedError' in line or 'Error' in line or 'error' in line.lower():
                            return line.strip()
                return "Unknown error"

            # First run (suite) stays serial so its instant resume does not
            # compete for cores with the MPI jobs below.
            first, parallel_runs = runs[0], runs[1:]

            label, cfg, log_name, prefix, key, required, np_ranks = first
            print_status(f"Launching Cobaya MCMC ({label})...", "PROCESS")
            run_start = time.time()
            chain_log = self.log_dir / log_name
            cmd = _chain_cmd(cfg, prefix, np_ranks)
            with open(chain_log, 'a') as logfile:
                proc = subprocess.run(cmd, stdout=logfile,
                                      stderr=subprocess.STDOUT,
                                      stdin=subprocess.DEVNULL,
                                      env=_chain_env(np_ranks), cwd=self.root_dir)
            if proc.returncode != 0:
                raise RuntimeError(f"{label} MCMC exited with code "
                                   f"{proc.returncode}.\nActual error: "
                                   f"{_extract_error(chain_log)}")
            self._verify_chains_fresh(run_start, prefix)
            results[key] = "SUCCESS"

            # Remaining chains in parallel; each MPI rank is one chain.
            print_status("Launching remaining chains in parallel under MPI...", "PROCESS")
            procs = []
            for label, cfg, log_name, prefix, key, required, np_ranks in parallel_runs:
                print_status(f"  {label}: mpirun -np {np_ranks} (log: logs/{log_name})", "INFO")
                chain_log = self.log_dir / log_name
                cmd = _chain_cmd(cfg, prefix, np_ranks)
                logfile = open(chain_log, 'a')
                launch_start = time.time()
                p = subprocess.Popen(cmd, stdout=logfile,
                                     stderr=subprocess.STDOUT,
                                     stdin=subprocess.DEVNULL,
                                     env=_chain_env(np_ranks), cwd=self.root_dir)
                procs.append((label, prefix, key, required, chain_log,
                              p, logfile, launch_start))

            for label, prefix, key, required, chain_log, p, logfile, t0 in procs:
                rc = p.wait()
                logfile.close()
                if rc != 0:
                    actual_error = _extract_error(chain_log)
                    msg = (f"{label} MCMC exited with code {rc}.\n"
                           f"Actual error: {actual_error}")
                    if required:
                        raise RuntimeError(msg)
                    print_status(f"  ! Optional chain failed, continuing: {msg}", "ERROR")
                    results[key] = f"FAILED: {actual_error}"
                    continue
                print_status(f"  Verifying {label} chain...", "PROCESS")
                self._verify_chains_fresh(t0, prefix)
                results[key] = "SUCCESS"

            n_ok = sum(1 for v in results.values() if v == "SUCCESS")
            results["status"] = "SUCCESS" if n_ok == len(runs) else "PARTIAL"
            print_status(f"\n  ✓ {n_ok}/{len(runs)} MCMC chains completed successfully", "SUCCESS")
            
        except Exception as e:
            results["status"] = "FAILED"
            results["error"] = str(e)
            print_status(f"\n  ✗ Step FAILED (no fallback used): {e}", "ERROR")
            raise
        
        return results


if __name__ == "__main__":
    step = Step06MCMC()
    step.run()
