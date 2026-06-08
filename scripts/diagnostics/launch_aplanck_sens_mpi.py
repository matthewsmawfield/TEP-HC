#!/usr/bin/env python3
"""Launch 4-chain MPI Cobaya run for A_planck sensitivity with widened prior."""

import subprocess
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG = PROJECT_ROOT / "logs" / "aplanck_sens_mpi4.log"

env = os.environ.copy()
env["COBAYA_PACKAGES_PATH"] = str(PROJECT_ROOT / "data" / "external" / "cobaya_packages")
env["OMP_NUM_THREADS"] = "1"
# Do NOT set COBAYA_NOMPI — we want MPI

# Clean any stale lock files
for f in (PROJECT_ROOT / "results" / "mcmc_chains").glob("tep_hiclass_aplanck_sens.input.yaml.locked"):
    f.unlink()

with open(LOG, 'w') as logfile:
    proc = subprocess.Popen(
        ["mpirun", "-np", "4", "cobaya-run",
         str(PROJECT_ROOT / "data" / "cobaya" / "tep_hiclass_aplanck_sens.yaml")],
        cwd=str(PROJECT_ROOT),
        env=env,
        stdout=logfile,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )

print(f"Launched MPI Cobaya (PID {proc.pid}). Log: {LOG}")
