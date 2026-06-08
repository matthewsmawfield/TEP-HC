#!/bin/bash
# A_planck sensitivity MCMC launcher — runs inside screen
set -e
cd "/Users/matthewsmawfield/www/Temporal Equivalence Principle/TEP-HC"
export COBAYA_PACKAGES_PATH="/Users/matthewsmawfield/www/Temporal Equivalence Principle/TEP-HC/data/external/cobaya_packages"
export OMP_NUM_THREADS=1

LOG="logs/aplanck_sens_mpi4.log"
> "$LOG"  # truncate log

echo "[$(date)] Starting A_planck sensitivity MCMC (4 chains, MPI)" >> "$LOG"
mpirun -np 4 cobaya-run --force "data/cobaya/tep_hiclass_aplanck_sens.yaml" >> "$LOG" 2>&1
EXIT=$?
echo "[$(date)] Finished with exit code $EXIT" >> "$LOG"
