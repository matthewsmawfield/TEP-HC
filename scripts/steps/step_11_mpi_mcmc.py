#!/usr/bin/env python3
"""
Step 09: Multi-Chain MPI MCMC (Active Perturbation)
====================================================
Launches a 4-chain parallel MPI MCMC run for the active-perturbation
configuration with cross-chain Gelman-Rubin diagnostics.

This is the production-grade peer-review defense configuration.

Outputs:
    - results/mcmc_chains/tep_hiclass_perturbations_mpi.*.txt
    - logs/step_09_mpi_mcmc_full.log
    - results/09_mpi_mcmc_summary.json
"""

import sys
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step11MPIMCMC:
    """Step 11: 4-chain MPI MCMC with active perturbations."""

    STEP_NAME = "11_mpi_mcmc"
    STEP_DESCRIPTION = "Multi-Chain MPI MCMC (Active Perturbation)"

    N_CHAINS = 4
    YAML_CONFIG = "data/cobaya/tep_hiclass_perturbations_mpi.yaml"
    OUTPUT_PREFIX = "tep_hiclass_perturbations_mpi"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.chains_dir = self.results_dir / "mcmc_chains"
        self.logs_dir = self.root_dir / "logs"
        self.fig_dir = self.results_dir / "figures"

        for d in [self.results_dir, self.chains_dir, self.logs_dir, self.fig_dir]:
            d.mkdir(parents=True, exist_ok=True)

        log_file = self.logs_dir / f"step_{self.STEP_NAME}_full.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}_full", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Launch 4-chain MPI MCMC and wait for convergence."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")

        yaml_path = self.root_dir / self.YAML_CONFIG
        if not yaml_path.exists():
            raise FileNotFoundError(f"Config not found: {yaml_path}")

        # Clean stale chain files for this prefix
        stale = list(self.chains_dir.glob(f"{self.OUTPUT_PREFIX}.*.txt"))
        stale += list(self.chains_dir.glob(f"{self.OUTPUT_PREFIX}.*.progress"))
        for f in stale:
            f.unlink()
            print_status(f"  Removed stale: {f.name}", "INFO")

        cmd = [
            "mpirun", "-np", str(self.N_CHAINS),
            "cobaya-run", str(yaml_path)
        ]

        print_status(f"Launching {self.N_CHAINS}-chain MPI MCMC...", "PROCESS")
        print_status(f"  Config: {self.YAML_CONFIG}", "INFO")
        print_status(f"  Output: {self.chains_dir}/{self.OUTPUT_PREFIX}.*.txt", "INFO")
        print_status(f"  Command: {' '.join(cmd)}", "INFO")

        start_time = time.time()

        # Run cobaya; stdout/stderr go to the step log
        with open(self.logger.log_file, "a") as log_fh:
            log_fh.write(f"\n{'='*60}\n")
            log_fh.write(f"MPI RUN STARTED: {datetime.now().isoformat()}\n")
            log_fh.write(f"Command: {' '.join(cmd)}\n")
            log_fh.write(f"{'='*60}\n\n")
            log_fh.flush()

            proc = subprocess.Popen(
                cmd,
                stdout=log_fh,
                stderr=subprocess.STDOUT,
                cwd=self.root_dir
            )

            # Poll until completion
            try:
                while proc.poll() is None:
                    time.sleep(30)
                    # Print a heartbeat every 30s
                    elapsed = time.time() - start_time
                    print_status(
                        f"  Sampling... elapsed {elapsed/60:.0f} min",
                        "INFO",
                        end="\r"
                    )
            except KeyboardInterrupt:
                print_status("\nInterrupted. Terminating MPI run...", "WARNING")
                proc.terminate()
                proc.wait(timeout=30)
                raise

        elapsed = time.time() - start_time
        returncode = proc.returncode

        print_status(f"\nMPI run finished (exit code {returncode})",
                     "SUCCESS" if returncode == 0 else "ERROR")
        print_status(f"  Wall time: {elapsed/3600:.1f} hours", "INFO")

        # Collect outputs
        chain_files = sorted(self.chains_dir.glob(f"{self.OUTPUT_PREFIX}.*.txt"))
        print_status(f"  Chain files: {len(chain_files)}", "INFO")

        # Parse final R-1 from log
        rminus1 = self._extract_final_rminus1()

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS" if returncode == 0 else "FAILED",
            "exit_code": returncode,
            "wall_time_hours": round(elapsed / 3600, 2),
            "n_chains": self.N_CHAINS,
            "chain_files": [str(f.name) for f in chain_files],
            "final_Rminus1": rminus1,
            "yaml_config": self.YAML_CONFIG,
        }

        summary_file = self.results_dir / "09_mpi_mcmc_summary.json"
        import json
        with open(summary_file, "w") as f:
            json.dump(results, f, indent=2)
        print_status(f"  Summary: {summary_file}", "INFO")

        if rminus1 is not None and rminus1 < 0.05:
            print_status(f"  Cross-chain R-1 = {rminus1:.4f} (< 0.05) — CONVERGED",
                         "SUCCESS")
        elif rminus1 is not None:
            print_status(f"  Cross-chain R-1 = {rminus1:.4f} — not fully converged",
                         "WARNING")

        print_status("Step completed.", "SUCCESS" if returncode == 0 else "ERROR")
        return results

    def _extract_final_rminus1(self) -> float | None:
        """Parse the final cross-chain R-1 from the log file."""
        log_path = self.logger.log_file
        if not log_path.exists():
            return None
        try:
            with open(log_path) as f:
                lines = f.readlines()
            # Find last 'Convergence of means: R-1 = X'
            for line in reversed(lines):
                if "Convergence of means:" in line and "R-1 =" in line:
                    parts = line.split("R-1 =")
                    if len(parts) > 1:
                        val_str = parts[1].split()[0]
                        return float(val_str)
        except Exception:
            pass
        return None


if __name__ == "__main__":
    step = Step11MPIMCMC()
    step.run()
