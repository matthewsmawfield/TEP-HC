#!/usr/bin/env python3
"""
Step 24: Low-ell ISW residual across the deltaphi closure branches
==================================================================
Runs hi_class (tCl to l_max=100) on the production screened branch
(wc=700), the weak-lensing-amplitude branch (wc=6300), and the
minimally stable unscreened branch (wc=7), and records the low-ell
TT residual versus the Lambda-CDM and TEP-background references.

This makes the manuscript's branch-dependent ISW claims traceable to
registered products rather than interpolation.

Output: results/step_24_lowell_isw_scan.json
"""

import sys
import json
import subprocess
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status

EPS_T_FID = 0.0066
Z_T_FID = 5.0
N_T_FID = 2.0

# tep.c maps tep_kin_boost K > 0 -> wc = 7 K^2 (Z_E = wc + 6 at beta_A^2=1),
# K < 0 -> wc = K (canonical image wc=-5 at K=-5).
BRANCHES = [
    ("wc7",     1.0,   "minimal stable unscreened (wc=+7, Z=13)"),
    ("wc700",  10.0,   "production screened (wc=+700, Z=706)"),
    ("wc6300", 30.0,   "weak-lensing amplitude (wc=+6300, Z=6306)"),
]

# Closure-response scan rows: (label, S_Sigma, wc).  K = sqrt(wc/7) for
# wc > 0; K = wc for wc < 0 (canonical image branch).
SCAN_ROWS = [
    ("canonical EF image (manuscript map, wc=-5)", 1.0,  -5),
    ("wc=-1 (Z=5)",                                1.0,  -1),
    ("wc=+1 (Z=7)",                                1.0,   1),
    ("wc=+5 (Z=11)",                               1.0,   5),
    ("wc=+7 (Z=13, minimal stable)",               1.0,   7),
    ("wc=+15.75 (Z=22)",                           1.0,  15.75),
    ("wc=+63 (Z=69)",                              1.0,  63),
    ("wc=+700 (Z=706, GR-recovery)",               1.0,  700),
    ("wc=+6300 (Z=6306)",                          1.0, 6300),
    ("screened S=0.1 wc=7",                        0.1,   7),
    ("screened S=0.03 wc=7",                       0.03,  7),
]

PK_INI_TEMPLATE = """
output = mPk
H0 = 67.36
omega_b = 0.022383
omega_cdm = 0.120011
tau_reio = 0.0543
ln10^{{10}}A_s = 3.0448
n_s = 0.96605
YHe = 0.2454
root = {root}
z_pk = 0
P_k_max_h/Mpc = 1.0

tep_mode = yes
epsilon_T = {eps}
z_T = {z_t}
n_T = {n_t}

gravity_model = tep
M2_evolution = yes
use_pert_var_deltaphi_smg = yes
pert_initial_conditions_smg = zero
tep_screening_s = {s_sigma}
tep_kin_boost = {boost}
"""

LCDM_PK_INI = """
output = mPk
H0 = 67.36
omega_b = 0.022383
omega_cdm = 0.120011
tau_reio = 0.0543
ln10^{{10}}A_s = 3.0448
n_s = 0.96605
YHe = 0.2454
root = {root}
z_pk = 0
P_k_max_h/Mpc = 1.0
"""

INI_TEMPLATE = """
output = tCl
l_max_scalars = 2500
write background = yes
H0 = 67.36
omega_b = 0.022383
omega_cdm = 0.120011
tau_reio = 0.0543
ln10^{{10}}A_s = 3.0448
n_s = 0.96605
YHe = 0.2454
root = {root}
z_pk = 0, 0.5
P_k_max_h/Mpc = 1.0

tep_mode = yes
epsilon_T = {eps}
z_T = {z_t}
n_T = {n_t}

gravity_model = tep
M2_evolution = yes
use_pert_var_deltaphi_smg = yes
pert_initial_conditions_smg = zero
tep_screening_s = 1.0
tep_kin_boost = {boost}
"""


class Step24LowellISW:
    STEP_NAME = "24_lowell_isw_scan"
    STEP_DESCRIPTION = "Low-ell ISW residual across closure branches"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.hi_class_bin = (
            self.root_dir / "external" / "hi_class" / "hi_class" / "class"
        )
        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def _clean(self, stem):
        for f in self.results_dir.glob(f"{stem}_0*_*.dat"):
            f.unlink(missing_ok=True)

    def _run_branch(self, tag, boost):
        self._clean(f"step24_{tag}")
        ini = self.results_dir / f"step24_{tag}.ini"
        ini.write_text(INI_TEMPLATE.format(
            root=f"step24_{tag}_", eps=EPS_T_FID, z_t=Z_T_FID,
            n_t=N_T_FID, boost=boost))
        result = subprocess.run(
            [str(self.hi_class_bin), str(ini)],
            cwd=self.results_dir,
            capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"hi_class failed for {tag}: {result.stderr[-300:]}")
        return np.loadtxt(self.results_dir / f"step24_{tag}_00_cl.dat")

    def _sigma8(self, k, pk):
        R = 8.0
        x = k * R
        W = np.ones_like(x)
        mask = x > 1e-6
        W[mask] = 3.0 * (np.sin(x[mask]) - x[mask] * np.cos(x[mask])) / (x[mask] ** 3)
        integrand = k ** 2 * pk * W ** 2
        return np.sqrt((1.0 / (2.0 * np.pi ** 2)) * np.trapezoid(integrand, k))

    def _run_pk(self, tag, ini_text):
        self._clean(f"step24_{tag}")
        ini = self.results_dir / f"step24_{tag}.ini"
        ini.write_text(ini_text)
        result = subprocess.run(
            [str(self.hi_class_bin), str(ini)],
            cwd=self.results_dir,
            capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"hi_class failed for {tag}: {result.stderr[-300:]}")
        return np.loadtxt(self.results_dir / f"step24_{tag}_00_pk.dat",
                          comments="#")

    def _closure_scan(self):
        print_status("  Running closure-response scan (mPk per branch)...", "PROCESS")
        lcdm = self._run_pk("lcdm_scan", LCDM_PK_INI.format(root="step24_lcdm_scan_"))
        k_l, pk_l = lcdm[:, 0], lcdm[:, 1]
        s8_lcdm = self._sigma8(k_l, pk_l)

        rows = []
        for i, (label, s_sigma, wc) in enumerate(SCAN_ROWS):
            boost = wc if wc < 0 else float(np.sqrt(wc / 7.0))
            stag = f"scan{i:02d}"
            pk = self._run_pk(
                stag,
                PK_INI_TEMPLATE.format(root=f"step24_{stag}_", eps=EPS_T_FID,
                                       z_t=Z_T_FID, n_t=N_T_FID,
                                       s_sigma=s_sigma, boost=boost))
            k, p = pk[:, 0], pk[:, 1]
            ratio = p / np.interp(k, k_l, pk_l) - 1.0
            finite = int(np.sum(np.isfinite(ratio)))
            rows.append({
                "label": label,
                "S_sigma": s_sigma,
                "wc": wc,
                "Z_eff": wc + 6,
                "tep_kin_boost": boost,
                "sigma8": self._sigma8(k, p),
                "median_pk_ratio_minus1": float(np.nanmedian(ratio)),
                "max_abs_ratio_minus1": float(np.nanmax(np.abs(ratio))),
                "finite": finite,
            })
        scan = {
            "step": "closure_response_scan",
            "date": datetime.now().date().isoformat(),
            "note": ("sigma8 and P(k) response of the deltaphi SMG closure as a "
                     "function of the effective Jordan kinetic coefficient "
                     "wc = Z_E - 6 beta_A^2 and screening S_Sigma.  "
                     "alpha_B = 2 S alpha_A, alpha_K = wc alpha_A^2.  "
                     "Regenerated by step_24_lowell_isw_scan.py."),
            "lcdm_sigma8": s8_lcdm,
            "scan": rows,
        }
        out = self.results_dir / "closure_response_scan.json"
        with open(out, "w") as f:
            json.dump(scan, f, indent=2)
        print_status(f"  Saved {out}", "SUCCESS")
        return scan

    def run(self):
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        results = {"step": self.STEP_NAME,
                   "timestamp": datetime.now().isoformat(),
                   "status": "RUNNING"}
        try:
            lcdm = np.loadtxt(self.results_dir / "lcdm_post_00_cl.dat")
            bg = np.loadtxt(self.results_dir / "tep_bg_post_00_cl.dat")

            branches = {}
            for tag, boost, label in BRANCHES:
                print_status(f"  Running {label}...", "PROCESS")
                cl = self._run_branch(tag, boost)
                n_low = min(9, cl.shape[0])          # ell = 2..10
                res_lcdm = cl[:n_low, 1] / lcdm[:n_low, 1] - 1
                res_bg = cl[:n_low, 1] / bg[:n_low, 1] - 1
                if not np.all(np.isfinite(res_lcdm)):
                    raise RuntimeError(f"Non-finite low-ell spectra for {tag}")
                branches[tag] = {
                    "label": label,
                    "tep_kin_boost": boost,
                    "ell2_residual_vs_lcdm": float(res_lcdm[0]),
                    "ell2_residual_vs_bg": float(res_bg[0]),
                    "max_abs_lowell_residual_vs_lcdm": float(np.max(np.abs(res_lcdm))),
                    "max_abs_lowell_residual_vs_bg": float(np.max(np.abs(res_bg))),
                    "residual_vs_lcdm_by_ell": {
                        int(cl[i, 0]): float(res_lcdm[i]) for i in range(n_low)},
                }

            results["branches"] = branches
            results["closure_scan"] = self._closure_scan()
            results["reference"] = {
                "lcdm": "results/lcdm_post_00_cl.dat",
                "tep_background": "results/tep_bg_post_00_cl.dat",
            }
            results["status"] = "SUCCESS"
            out = self.results_dir / "step_24_lowell_isw_scan.json"
            with open(out, "w") as f:
                json.dump(results, f, indent=2)
            print_status(f"  Saved {out}", "SUCCESS")
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        return results


if __name__ == "__main__":
    Step24LowellISW().run()
