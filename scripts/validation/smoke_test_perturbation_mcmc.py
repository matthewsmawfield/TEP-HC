#!/usr/bin/env python3
"""
Smoke-test: Active Perturbation MCMC Initialization
=====================================================
Runs a minimal Cobaya chain with gravity_model=tep to verify that:
  1. hi_class initializes the SMG perturbation module without crash.
  2. The first few likelihood evaluations succeed at the reference point.
  3. The chain sampler can take at least 20 steps without divergence.

This is NOT a science run. It exists solely to validate the C-level
perturbation closure before committing a full overnight MCMC.
"""

import sys
import os
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

os.environ["COBAYA_PACKAGES_PATH"] = str(
    os.environ.get("COBAYA_PACKAGES_PATH",
                   PROJECT_ROOT / "data" / "external" / "cobaya_packages")
)

# Only disable MPI if mpirun is not available
if subprocess.run(["which", "mpirun"], capture_output=True).returncode != 0:
    os.environ["COBAYA_NOMPI"] = "1"

from cobaya.run import run
from scripts.utils.logger import print_status


CONFIG = {
    "theory": {
        "classy": {
            "path": "external/hi_class/hi_class",
            "ignore_obsolete": True,
            "extra_args": {
                "output": "tCl,pCl,lCl,mPk",
                "lensing": "yes",
                "modes": "s,t",
                "non_linear": "halofit",
                "tep_mode": "yes",
                "z_T": 5.0,
                "n_T": 2.0,
                "gravity_model": "tep",
                "M2_evolution": "yes",
            }
        }
    },
    "likelihood": {
        "planck_2018_lowl.TT": None,
    },
    "params": {
        "logA": {"prior": {"min": 2.5, "max": 3.5}, "ref": {"dist": "norm", "loc": 3.044, "scale": 0.014}, "proposal": 0.01, "drop": True},
        "A_s": {"value": "lambda logA: 1e-10*np.exp(logA)"},
        "n_s": {"prior": {"min": 0.94, "max": 1.0}, "ref": {"dist": "norm", "loc": 0.966, "scale": 0.004}, "proposal": 0.004},
        "H0": {"prior": {"min": 40, "max": 100}, "ref": {"dist": "norm", "loc": 67.4, "scale": 0.5}, "proposal": 1.5},
        "omega_b": {"prior": {"min": 0.005, "max": 0.1}, "ref": {"dist": "norm", "loc": 0.0224, "scale": 0.0002}, "proposal": 0.0003},
        "omega_cdm": {"prior": {"min": 0.01, "max": 0.99}, "ref": {"dist": "norm", "loc": 0.12, "scale": 0.001}, "proposal": 0.0015},
        "tau_reio": {"prior": {"min": 0.01, "max": 0.8}, "ref": {"dist": "norm", "loc": 0.054, "scale": 0.007}, "proposal": 0.01},
        "epsilon_T": {"prior": {"min": -1.0, "max": 1.0}, "ref": {"dist": "norm", "loc": 0.006, "scale": 0.005}, "proposal": 0.0005, "latex": "\\epsilon_T"},
    },
    "sampler": {
        "mcmc": {
            "burn_in": 0,
            "max_tries": 5000,
            "max_samples": 50,
            "Rminus1_stop": 10.0,
            "Rminus1_cl_stop": 10.0,
            "output_every": 1,
            "learn_proposal": False,
            "drag": False,
            "seed": 99,
        }
    },
    "output": "results/mcmc_chains/smoke_test_tep_pert",
    "resume": False,
    "force": True,
    "debug": True,
}

if __name__ == "__main__":
    print_status("SMOKE TEST: Active perturbation MCMC (gravity_model=tep)", "TITLE")
    print_status(f"  Output: {CONFIG['output']}", "INFO")
    print_status("  Likelihoods: Planck 2018 low-l TT only (minimal)", "INFO")
    print_status("  Steps: 50 (fast)", "INFO")

    try:
        updated_info, sampler = run(CONFIG)
        print_status("SMOKE TEST PASSED: hi_class SMG perturbation mode stable.", "SUCCESS")
        print_status(f"  Final logpost: {sampler.collection['minuslogpost'].iloc[-1]:.4f}", "INFO")
    except Exception as e:
        print_status(f"SMOKE TEST FAILED: {e}", "ERROR")
        sys.exit(1)
