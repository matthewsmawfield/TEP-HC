#!/usr/bin/env python3
"""
Step 04: CMB Spectra Generation (Real Data Path)
==============================================
Generates CMB temperature power spectra using full Boltzmann solvers.
Uses the hi_class C executable for maximum reliability.
"""

import sys
import json
import subprocess
import os
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step04CMB:
    """Step 04: Generate CMB power spectra with full Boltzmann solvers."""
    
    STEP_NAME = "04_cmb"
    STEP_DESCRIPTION = "CMB Spectra Generation (Real Data)"
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.hi_class_bin = self.root_dir / "external" / "hi_class" / "hi_class" / "class"
        
        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
    
    def run(self) -> dict:
        """Execute CMB spectra generation via C-engine."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "spectra": {},
            "status": "RUNNING"
        }
        
        try:
            # 1. Generate .ini files for hi_class (using relative paths for root)
            print_status("Preparing hi_class input configurations...", "PROCESS")
            lcdm_ini = self.results_dir / "lcdm_baseline.ini"
            tep_ini = self.results_dir / "tep_model.ini"

            # IMPORTANT: hi_class appends an auto-incrementing suffix (_00, _01, ...)
            # to the `root` on every run and never overwrites existing files. If we
            # leave old outputs in place, a later run writes _0N while a hardcoded
            # read of _00 silently returns a STALE spectrum from an earlier build.
            # Remove previous outputs so the fresh run is unambiguously *_00_*.
            self._clean_outputs("lcdm_baseline")
            self._clean_outputs("tep_model")

            self._write_ini(lcdm_ini, is_tep=False)
            self._write_ini(tep_ini, is_tep=True)

            # 2. Run hi_class C-executable from results_dir
            print_status("Running hi_class C-engine (LambdaCDM)...", "PROCESS")
            self._run_class(lcdm_ini)

            print_status("Running hi_class C-engine (TEP)...", "PROCESS")
            self._run_class(tep_ini)

            # 3. Parse and analyze results (resolve actual filenames written)
            print_status("Parsing Boltzmann-solved spectra...", "PROCESS")
            ells, cl_lcdm = self._parse_output(self._latest_output("lcdm_baseline", "cl"))
            _, cl_tep = self._parse_output(self._latest_output("tep_model", "cl"))

            results["ells"] = ells.tolist()
            results["spectra"]["cl_tt_lcdm"] = cl_lcdm.tolist()
            results["spectra"]["cl_tt_tep"] = cl_tep.tolist()

            # Residuals
            residuals = (cl_tep - cl_lcdm) / cl_lcdm
            results["spectra"]["residuals"] = residuals.tolist()

            # 4. Acoustic-scale preservation diagnostic (the physically meaningful
            #    test of early-universe freezing). r_s and theta_s come from the
            #    background tables; r_s must be preserved to ppm if the TEP field
            #    truly freezes before recombination.
            print_status("Computing acoustic-scale preservation (r_s, theta_s)...", "PROCESS")
            results["acoustic"] = self._acoustic_diagnostic()

            results["status"] = "SUCCESS"
            
            # Save final results
            output_file = self.results_dir / "04_cmb_spectra.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print_status(f"  ✓ Saved real results to {output_file}", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results
    
    def _write_ini(self, path, is_tep=False):
        # Use relative root to avoid space issues
        root_val = path.stem + "_"
        content = f"""
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
root = {root_val}
"""
        if is_tep:
            # Native TEP background-only modification (standard GR perturbations):
            #   H_TEP(z) = H_LCDM(z) * M(z)
            #   M(z)     = A(z) / (1 - alpha_A(z))
            #   A(z)     = exp(epsilon_T * ln(1+z) * S(z))
            #   S(z)     = exp(-(z/z_T)^n_T)   [authoritative TEP-C0 form]
            # The exp() factor freezes the modification for z >> z_T, preserving
            # r_s, BBN and the CMB peaks; ln(1+z) fixes f_T(0)=0 (H0 unchanged).
            # epsilon_T below is a representative fiducial for the consistency
            # check; the homogeneous amplitude is bounded to ~0 by the CMB
            # (TEP-C0, Paper 26) and is a free parameter in the MCMC.
            epsilon_T = 0.0066   # representative fiducial (not a completed-fit value)
            z_T = 5.0            # Transition redshift
            n_T = 2.0            # Transition steepness
            
            print_status(f"  Native TEP: epsilon_T={epsilon_T}, z_T={z_T}, n_T={n_T}", "INFO")
            
            content += f"""
# Native TEP background-only Hubble modification (TEP-C0, Paper 26)
# Standard GR perturbations; only H(z) is modified via tep_mode
tep_mode = yes
epsilon_T = {epsilon_T}
z_T = {z_T}
n_T = {n_T}
"""
        with open(path, 'w') as f:
            f.write(content)

    def _clean_outputs(self, root_stem):
        """Remove stale hi_class outputs for a given root so the next run is *_00_*."""
        for f in self.results_dir.glob(f"{root_stem}_*"):
            try:
                f.unlink()
            except OSError:
                pass

    def _latest_output(self, root_stem, kind):
        """Return the highest-numbered hi_class output file for a root, e.g. the
        most recent `<root>_<NN>_<kind>.dat`. Robust to the auto-increment suffix."""
        candidates = sorted(self.results_dir.glob(f"{root_stem}_*_{kind}.dat"))
        if not candidates:
            raise FileNotFoundError(
                f"No hi_class '{kind}' output found for root '{root_stem}' in {self.results_dir}"
            )
        # Sort by the integer suffix to pick the latest deterministically.
        def _suffix(p):
            try:
                return int(p.stem.split("_")[-2])
            except (ValueError, IndexError):
                return -1
        return max(candidates, key=_suffix)

    def _acoustic_diagnostic(self):
        """Compute r_s and theta_s from the background tables and report the
        TEP/LCDM ratios. r_s preservation (ratio ~ 1) demonstrates that the TEP
        field freezes before recombination; any theta_s shift is a pure late-time
        angular-diameter-distance projection (degenerate with H0)."""
        try:
            bg_lcdm = np.loadtxt(self._latest_output("lcdm_baseline", "background"))
            bg_tep = np.loadtxt(self._latest_output("tep_model", "background"))
        except (FileNotFoundError, OSError, ValueError) as e:
            print_status(f"  Acoustic diagnostic unavailable: {e}", "WARNING")
            return {"available": False, "reason": str(e)}

        # Background columns (hi_class): 0:z 1:propertime 2:conftime 3:H
        # 4:comov.dist 5:ang.diam.dist 6:lum.dist 7:comov.snd.hrz ...
        z_rec = 1089.0
        def at_rec(arr):
            i = int(np.argmin(np.abs(arr[:, 0] - z_rec)))
            return arr[i, 0], arr[i, 7], arr[i, 4]  # z, r_s, D_comov
        zL, rsL, dcL = at_rec(bg_lcdm)
        zT, rsT, dcT = at_rec(bg_tep)
        theta_L = rsL / dcL
        theta_T = rsT / dcT
        diag = {
            "available": True,
            "z_star": zL,
            "r_s_lcdm_Mpc": rsL,
            "r_s_tep_Mpc": rsT,
            "r_s_ratio": rsT / rsL,
            "D_comov_ratio": dcT / dcL,
            "theta_s_lcdm": theta_L,
            "theta_s_tep": theta_T,
            "theta_s_frac_shift": theta_T / theta_L - 1.0,
        }
        print_status(
            f"  r_s ratio = {diag['r_s_ratio']:.7f} (preservation), "
            f"theta_s shift = {diag['theta_s_frac_shift']*100:+.4f}%",
            "INFO",
        )
        return diag

    def _run_class(self, ini_path):
        # Run from the directory where .ini is to ensure relative root works
        cwd = ini_path.parent
        cmd = [str(self.hi_class_bin), ini_path.name]
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"hi_class failed with return code {result.returncode}. Out: {result.stdout} Err: {result.stderr}")

    def _parse_output(self, dat_path):
        data = np.loadtxt(dat_path, comments='#')
        ells = data[:, 0]
        cl_tt = data[:, 1]
        return ells, cl_tt


if __name__ == "__main__":
    step = Step04CMB()
    step.run()
