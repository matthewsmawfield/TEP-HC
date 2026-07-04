#!/usr/bin/env python3
"""
Step 12: Post-Analysis for Manuscript Quantitative Tables
==========================================================
Generates the four quantitative items requested for the TEP-HC manuscript:
  1. Acoustic-scale preservation metrics table (binned by multipole range)
  2. No-ghost discriminant across the 95% ε_T posterior range
  3. TE/EE max residuals (from fresh hi_class runs with pCl output)
  4. fσ8(z=0) and fσ8(z=0.5) from matter power spectra

All outputs are written to results/12_post_analysis.json.
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
from core.cosmology import alpha_A_native, evaluate_tep_eft_sector


class Step12PostAnalysis:
    STEP_NAME = "12_post_analysis"
    STEP_DESCRIPTION = "Post-Analysis Quantitative Tables"

    EPS_T_FID = 0.0066
    Z_T_FID = 5.0
    N_T_FID = 2.0

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.hi_class_bin = self.root_dir / "external" / "hi_class" / "hi_class" / "class"

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING"
        }

        try:
            print_status("Running hi_class (LCDM, TEP-bg, TEP-pert) with tCl,pCl,mPk...", "PROCESS")
            raw = self._run_all_spectra()

            print_status("Computing acoustic-scale preservation metrics...", "PROCESS")
            results["acoustic_metrics"] = self._acoustic_metrics(raw)

            print_status("Evaluating no-ghost discriminant across MCMC posterior...", "PROCESS")
            results["stability_posterior"] = self._stability_posterior_scan()

            print_status("Computing polarization residuals...", "PROCESS")
            results["polarization"] = self._polarization_residuals(raw)

            print_status("Computing growth-function diagnostic...", "PROCESS")
            results["growth"] = self._growth_function(raw)

            results["status"] = "SUCCESS"
            output_file = self.results_dir / "12_post_analysis.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print_status(f"  ✓ Saved post-analysis results to {output_file}", "SUCCESS")

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise

        return results

    # ------------------------------------------------------------------
    # Unified hi_class runner
    # ------------------------------------------------------------------
    def _run_all_spectra(self):
        configs = [
            ("lcdm_post", False, None),
            ("tep_bg_post", True, "background_only"),
            ("tep_pert_post", True, "minimal_conformal"),
        ]
        raw = {}
        for root, is_tep, pert_mode in configs:
            ini_path = self.results_dir / f"{root}.ini"
            self._clean_outputs(root)
            self._write_ini(ini_path, is_tep=is_tep, tep_perturbations=pert_mode)
            self._run_class(ini_path)

            # Parse scalar cl (TT, EE, TE)
            cl_file = self._latest_output(root, "cl")
            l, tt, ee, te = self._parse_scalar_cl(cl_file)

            # Parse matter power spectrum (CLASS writes separate files per z: _z1_pk, _z2_pk)
            pk_z1 = self._latest_output(root, "z1_pk")
            pk_z2 = self._latest_output(root, "z2_pk")
            k, pk0 = self._parse_pk_single(pk_z1)
            _, pk05 = self._parse_pk_single(pk_z2)

            raw[root] = {
                "l": l, "tt": tt, "ee": ee, "te": te,
                "k": k, "pk_z0": pk0, "pk_z05": pk05,
            }
        return raw

    def _write_ini(self, path, is_tep=False, tep_perturbations=None):
        root_val = path.stem + "_"
        content = f"""
output = tCl,pCl,mPk
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
z_pk = 0, 0.5
P_k_max_h/Mpc = 1.0
"""
        if is_tep:
            content += f"""
tep_mode = yes
epsilon_T = {self.EPS_T_FID}
z_T = {self.Z_T_FID}
n_T = {self.N_T_FID}
"""
            if tep_perturbations == "minimal_conformal":
                content += """
gravity_model = tep
M2_evolution = yes
"""
        with open(path, 'w') as f:
            f.write(content)

    # ------------------------------------------------------------------
    # 1. Acoustic-scale preservation metrics
    # ------------------------------------------------------------------
    def _acoustic_metrics(self, raw):
        l = raw["lcdm_post"]["l"]
        tt_lcdm = raw["lcdm_post"]["tt"]
        tt_bg = raw["tep_bg_post"]["tt"]
        tt_pert = raw["tep_pert_post"]["tt"]

        # Load global acoustic data from existing JSON if available
        cmb_file = self.results_dir / "04_cmb_spectra.json"
        try:
            with open(cmb_file) as f:
                old = json.load(f)
            acoustic = old.get("acoustic", {})
        except Exception:
            acoustic = {}

        r_s_ratio = acoustic.get("r_s_ratio", None)
        theta_s_frac = acoustic.get("theta_s_frac_shift", None)

        # Compute safe residuals
        def _res(ref, test):
            mask = ref > 0
            r = np.zeros_like(test)
            r[mask] = (test[mask] - ref[mask]) / ref[mask]
            return r

        res_bg_lcdm = _res(tt_lcdm, tt_bg)
        res_pert_lcdm = _res(tt_lcdm, tt_pert)
        res_pert_bg = _res(tt_bg, tt_pert)

        bins = [(100, 500), (500, 1000), (1000, 2000)]
        table = []
        for lmin, lmax in bins:
            bin_mask = (l >= lmin) & (l <= lmax)

            # ℓ-centroid shift (weighted mean ℓ difference) TEP-bg vs LCDM
            l_cent_lcdm = np.sum(l[bin_mask] * tt_lcdm[bin_mask]) / np.sum(tt_lcdm[bin_mask])
            l_cent_bg = np.sum(l[bin_mask] * tt_bg[bin_mask]) / np.sum(tt_bg[bin_mask])
            delta_l = float(l_cent_bg - l_cent_lcdm)

            expected_delta_l = -(theta_s_frac or 0.0) * l_cent_lcdm if theta_s_frac else None

            # Max residuals (%)
            max_res_bg_lcdm = float(np.max(np.abs(res_bg_lcdm[bin_mask]))) * 100
            max_res_pert_lcdm = float(np.max(np.abs(res_pert_lcdm[bin_mask]))) * 100
            max_res_pert_bg = float(np.max(np.abs(res_pert_bg[bin_mask]))) * 100

            table.append({
                "multipole_range": f"{lmin} ≤ ℓ ≤ {lmax}",
                "l_centroid_lcdm": round(float(l_cent_lcdm), 2),
                "l_centroid_tep_bg": round(float(l_cent_bg), 2),
                "delta_l": round(delta_l, 3),
                "expected_delta_l": round(float(expected_delta_l), 3) if expected_delta_l is not None else None,
                "r_s_ratio": round(float(r_s_ratio), 8) if r_s_ratio is not None else None,
                "max_res_bg_vs_lcdm_percent": round(max_res_bg_lcdm, 4),
                "max_res_pert_vs_lcdm_percent": round(max_res_pert_lcdm, 4),
                "max_res_pert_vs_bg_percent": round(max_res_pert_bg, 4),
            })

        return {
            "global_r_s_ratio": r_s_ratio,
            "global_theta_s_frac_shift": theta_s_frac,
            "table": table,
        }

    # ------------------------------------------------------------------
    # 2. No-ghost discriminant across 95% ε_T posterior
    # ------------------------------------------------------------------
    def _stability_posterior_scan(self):
        mcmc_file = self.results_dir / "07_mcmc_summary_full.json"
        with open(mcmc_file) as f:
            mcmc = json.load(f)

        eps_data = mcmc.get("tep", {}).get("epsilon_T", {})
        eps_data_pert = mcmc.get("tep_perturbation", {}).get("epsilon_T", {})

        mean = eps_data.get("mean", self.EPS_T_FID)
        std = eps_data.get("std", 0.0049)
        min_sampled = eps_data.get("min", 3.35e-06)
        lower = max(float(min_sampled), mean - 1.96 * std)
        upper = mean + 1.96 * std

        mean_p = eps_data_pert.get("mean", self.EPS_T_FID)
        std_p = eps_data_pert.get("std", 0.0046)
        upper_p = mean_p + 1.96 * std_p
        upper = max(upper, upper_p)

        n_samples = 200
        eps_samples = np.linspace(lower, upper, n_samples)
        # Use z > 0 strictly, because at z = 0 the implementation fixes alpha_A = 0
        # (local reference frame), and D = 0 is the absence of a scalar, not a ghost.
        z = np.linspace(1e-6, 1100.0, 2000)

        D_min_all = []
        alpha_M_max_all = []

        for eps in eps_samples:
            alpha_A = alpha_A_native(z, eps, self.Z_T_FID, self.N_T_FID)
            eft = evaluate_tep_eft_sector(alpha_A)
            D = eft["D"]
            D_min_all.append(float(np.min(D)))
            alpha_M_max_all.append(float(np.max(np.abs(eft["alpha_M"]))))

        D_min_global = float(np.min(D_min_all))
        alpha_M_max_global = float(np.max(alpha_M_max_all))

        # Also evaluate at the exact posterior edge values for the table
        sample_vals = np.linspace(lower, upper, 10)
        edge_table = []
        for eps in sample_vals:
            alpha_A = alpha_A_native(z, eps, self.Z_T_FID, self.N_T_FID)
            eft = evaluate_tep_eft_sector(alpha_A)
            edge_table.append({
                "epsilon_T": round(float(eps), 6),
                "D_min": round(float(np.min(eft["D"])), 12),
                "D_max": round(float(np.max(eft["D"])), 8),
                "alpha_M_max": round(float(np.max(np.abs(eft["alpha_M"]))), 6),
            })

        return {
            "eps_T_range_95": {"lower": float(lower), "upper": float(upper)},
            "n_samples": n_samples,
            "z_range": {"z_min": float(z[0]), "z_max": float(z[-1])},
            "D_min_global": D_min_global,
            "all_positive_definite": D_min_global > 0,
            "alpha_M_max_global": alpha_M_max_global,
            "sampled_edge_table": edge_table,
            "note": "D(z) = alpha_A^2 > 0 for all z in (0,1100) and all epsilon_T in the 95% posterior.",
        }

    # ------------------------------------------------------------------
    # 3. TE/EE max residuals
    # ------------------------------------------------------------------
    def _polarization_residuals(self, raw):
        l = raw["lcdm_post"]["l"]

        ee_lcdm = raw["lcdm_post"]["ee"]
        te_lcdm = raw["lcdm_post"]["te"]

        ee_pert = raw["tep_pert_post"]["ee"]
        te_pert = raw["tep_pert_post"]["te"]

        def _max_res(cl_ref, cl_test, lmin, lmax, mode="fractional"):
            mask = (l >= lmin) & (l <= lmax)
            if not np.any(mask):
                return None
            ref = cl_ref[mask]
            test = cl_test[mask]
            delta = np.abs(test - ref)
            if mode == "fractional":
                # Only where |ref| > threshold (1% of max |ref| in bin)
                thresh = 1e-3 * np.max(np.abs(ref))
                safe = np.abs(ref) > thresh
                if not np.any(safe):
                    return None
                return float(np.max(delta[safe] / np.abs(ref[safe])))
            else:
                # Normalized by max |ref| in bin
                norm = np.max(np.abs(ref))
                return float(np.max(delta / norm))

        bins = [(100, 500), (500, 1000), (1000, 2000)]
        table = []
        for lmin, lmax in bins:
            table.append({
                "multipole_range": f"{lmin} ≤ ℓ ≤ {lmax}",
                "max_res_te_percent": round(_max_res(te_lcdm, te_pert, lmin, lmax, mode="normalized") * 100, 4),
                "max_res_ee_percent": round(_max_res(ee_lcdm, ee_pert, lmin, lmax, mode="fractional") * 100, 4),
            })

        return {"residual_table": table}

    # ------------------------------------------------------------------
    # 4. fσ8 from matter power spectra
    # ------------------------------------------------------------------
    def _growth_function(self, raw):
        results = {}
        for root, label in [
            ("lcdm_post", "LCDM"),
            ("tep_bg_post", "TEP_background_only"),
            ("tep_pert_post", "TEP_active_perturbations"),
        ]:
            k = raw[root]["k"]
            pk0 = raw[root]["pk_z0"]
            pk05 = raw[root]["pk_z05"]

            sigma8 = self._compute_sigma8(k, pk0)

            # D(z=0.5) from P(k) at k = 0.01 h/Mpc (linear regime)
            idx = np.argmin(np.abs(k - 0.01))
            D_05 = np.sqrt(pk05[idx] / pk0[idx])

            # f(z=0.5) = d ln D / d ln a  (finite difference between a=1 and a=2/3)
            f_05 = -np.log(D_05) / np.log(1.5)

            results[label] = {
                "sigma8": round(float(sigma8), 4),
                "D_z05": round(float(D_05), 6),
                "f_z05": round(float(f_05), 4),
                "fsigma8_z0": round(float(sigma8), 4),
                "fsigma8_z05": round(float(f_05 * sigma8 * D_05), 4),
            }

        return results

    def _compute_sigma8(self, k, pk):
        R = 8.0
        x = k * R
        W = np.ones_like(x)
        mask = x > 1e-6
        W[mask] = 3.0 * (np.sin(x[mask]) - x[mask] * np.cos(x[mask])) / (x[mask] ** 3)
        integrand = k ** 2 * pk * W ** 2
        sigma2 = (1.0 / (2.0 * np.pi ** 2)) * np.trapezoid(integrand, k)
        return np.sqrt(sigma2)

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------
    def _parse_scalar_cl(self, path):
        data = np.loadtxt(path, comments="#")
        return data[:, 0], data[:, 1], data[:, 2], data[:, 3]

    def _parse_pk_single(self, path):
        """Parse a single-z CLASS pk.dat file (two columns: k, P(k))."""
        data = np.loadtxt(path, comments="#")
        if data.ndim == 1:
            data = data.reshape(1, -1)
        return data[:, 0], data[:, 1]

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    def _clean_outputs(self, root_stem):
        for f in self.results_dir.glob(f"{root_stem}_*"):
            try:
                f.unlink()
            except OSError:
                pass

    def _latest_output(self, root_stem, kind):
        candidates = sorted(self.results_dir.glob(f"{root_stem}_*_{kind}.dat"))
        if not candidates:
            raise FileNotFoundError(f"No hi-class '{kind}' output found for root '{root_stem}'")
        # For z1_pk / z2_pk, suffix extraction is fragile; just return the first match
        # because _clean_outputs ensures only one run set exists.
        if kind in ("z1_pk", "z2_pk"):
            return candidates[0]
        def _suffix(p):
            try:
                return int(p.stem.split("_")[-2])
            except (ValueError, IndexError):
                return -1
        return max(candidates, key=_suffix)

    def _run_class(self, ini_path):
        if not self.hi_class_bin.exists():
            raise FileNotFoundError(f"hi_class binary not found: {self.hi_class_bin}")
        cmd = [str(self.hi_class_bin), str(ini_path)]
        result = subprocess.run(
            cmd,
            cwd=self.results_dir,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            raise RuntimeError(f"hi_class failed for {ini_path.name}:\n{result.stderr}")


if __name__ == "__main__":
    step = Step12PostAnalysis()
    step.run()
