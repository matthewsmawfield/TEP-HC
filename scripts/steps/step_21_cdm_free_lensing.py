#!/usr/bin/env python3
"""
Step 21: CDM-Free Lensing Potential Diagnostic
================================================
Fixed-parameter scope diagnostic for the TEP-HC no-particulate-dark-matter
ontology. At the published 5-chain active posterior point, the patched
hi_class is evaluated twice in each perturbation mode:

  1. with the posterior CDM fluid (omega_cdm = 0.1155), and
  2. with omega_cdm = 0 (baryons + scalar sector only),

recording C_ell^{phiphi} and sigma8. This is NOT a re-fit and NOT a
CDM-free likelihood: it measures how much of the lensing potential the
implemented pure-conformal scalar sector sources when the independent
CDM fluid is removed. The answer feeds directly into whether the
"phantom mass" ontology can claim to replace dark matter in the optical
sector.

Modes compared:
  - background-only: tep_mode native bridge, delta_phi frozen;
  - active perturbation: gravity_model = tep, M2_evolution = yes,
    alpha_M = -2 alpha_A, alpha_B = 2 alpha_A, alpha_K = -5 alpha_A^2.

Output: results/step_21_cdm_free_lensing.json
"""

import sys
import os
import json
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

HICLASS_PYTHON = PROJECT_ROOT / "external" / "hi_class" / "hi_class" / "python"
os.environ["PYTHONPATH"] = str(HICLASS_PYTHON) + os.pathsep + os.environ.get("PYTHONPATH", "")
sys.path.insert(0, str(HICLASS_PYTHON))

from scripts.utils.logger import TEPLogger, set_step_logger

# Fixed point: 5-chain active posterior (Section 4.5 of the manuscript).
POSTERIOR_PARAMS = {
    "output": "tCl,pCl,lCl,mPk",
    "lensing": "yes",
    "modes": "s",
    "l_max_scalars": 500,
    "non_linear": "none",
    "H0": 66.77,
    "omega_b": 0.02144,
    "A_s": 2.1e-9,
    "n_s": 0.9956,
    "tau_reio": 0.0497,
    "tep_mode": "yes",
    "z_T": 5.0,
    "n_T": 2.0,
    "epsilon_T": 0.00547,
}
ACTIVE_EXTRA = {"gravity_model": "tep", "M2_evolution": "yes"}
OMEGA_CDM_POSTERIOR = 0.1155
ELL_PROBES = [100, 400]


def run_point(params):
    import classy

    cosmo = classy.Class()
    cosmo.set(params)
    cosmo.compute()
    cls = cosmo.lensed_cl(params["l_max_scalars"])
    out = {
        "pp": {str(ell): float(cls["pp"][ell]) for ell in ELL_PROBES},
        "sigma8": float(cosmo.sigma8()),
    }
    cosmo.struct_cleanup()
    cosmo.empty()
    return out


def git_short_hash(path):
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=path, capture_output=True, text=True
        ).stdout.strip() or None
    except Exception:
        return None


class Step21CdmFreeLensing:
    STEP_NAME = "step_21_cdm_free_lensing"

    def __init__(self):
        self.log_dir = PROJECT_ROOT / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.log_path = self.log_dir / f"{self.STEP_NAME}.log"
        if self.log_path.exists():
            self.log_path.unlink()
        self.output_path = PROJECT_ROOT / "results" / f"{self.STEP_NAME}.json"

    def run(self):
        logger = TEPLogger(self.STEP_NAME, self.log_path)
        set_step_logger(logger)
        logger.info("=" * 60)
        logger.info("Step 21: CDM-Free Lensing Potential Diagnostic")
        logger.info("=" * 60)

        so_path = HICLASS_PYTHON / "classy.cpython-313-darwin.so"
        wrapper_hash = None
        if so_path.exists():
            wrapper_hash = hashlib.sha256(so_path.read_bytes()).hexdigest()[:16]

        results = {
            "step": self.STEP_NAME,
            "description": (
                "Fixed-posterior-point lensing-potential comparison of the "
                "patched hi_class with and without the standard CDM fluid. "
                "Scope diagnostic only: not a re-fit, not a CDM-free likelihood."
            ),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "parameters": dict(POSTERIOR_PARAMS),
            "active_extra_params": ACTIVE_EXTRA,
            "omega_cdm_posterior": OMEGA_CDM_POSTERIOR,
            "ell_probes": ELL_PROBES,
            "hiclass": {
                "path": str(HICLASS_PYTHON.parent),
                "git_head": git_short_hash(HICLASS_PYTHON.parent),
                "wrapper_sha256_16": wrapper_hash,
            },
            "modes": {},
        }

        for mode_name, extra in [
            ("background_only", {}),
            ("active_perturbation", ACTIVE_EXTRA),
        ]:
            results["modes"][mode_name] = {}
            for cdm_label, omega in [("with_cdm", OMEGA_CDM_POSTERIOR), ("no_cdm", 0.0)]:
                params = dict(POSTERIOR_PARAMS, **extra)
                params["omega_cdm"] = omega
                logger.process(f"{mode_name} / omega_cdm = {omega}")
                out = run_point(params)
                results["modes"][mode_name][cdm_label] = out
                logger.info(f"    pp[100] = {out['pp']['100']:.6e}  "
                            f"pp[400] = {out['pp']['400']:.6e}  "
                            f"sigma8 = {out['sigma8']:.4f}")

            w = results["modes"][mode_name]["with_cdm"]
            wo = results["modes"][mode_name]["no_cdm"]
            results["modes"][mode_name]["ratios_no_cdm_over_with_cdm"] = {
                f"pp[{ell}]": wo["pp"][str(ell)] / w["pp"][str(ell)] for ell in ELL_PROBES
            }
            results["modes"][mode_name]["ratios_no_cdm_over_with_cdm"]["sigma8"] = (
                wo["sigma8"] / w["sigma8"]
            )
            r = results["modes"][mode_name]["ratios_no_cdm_over_with_cdm"]
            logger.info(f"    no-CDM/CDM ratios: pp[100]={r['pp[100]']:.4f}  "
                        f"pp[400]={r['pp[400]']:.5f}  sigma8={r['sigma8']:.4f}")

        results["interpretation"] = (
            "Removing omega_cdm collapses the lensing potential in BOTH the "
            "background-only and active-perturbation branches at the published "
            "epsilon_T posterior. The implemented pure-conformal scalar sector "
            "(alpha functions ~ epsilon_T ~ 5e-3, rho_smg = 0 by construction) "
            "does not cluster sufficiently to replace the CDM fluid. The HC "
            "Planck-lensing fit therefore remains a CDM-containing benchmark, "
            "and a CDM-free optical-sector closure is an open requirement for "
            "the no-particulate-dark-matter ontology."
        )

        with open(self.output_path, "w") as f:
            json.dump(results, f, indent=2)
        logger.success(f"Results saved to {self.output_path}")
        return results


if __name__ == "__main__":
    Step21CdmFreeLensing().run()
