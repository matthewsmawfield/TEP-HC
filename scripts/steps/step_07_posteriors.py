#!/usr/bin/env python3
"""
Step 07: Posterior Analysis
===========================
Analyzes joint MCMC chains from hi_class with native TEP background-only
implementation or archived proxy runs.

# For native TEP: H_TEP(z) = H_LCDM(z) * M(z)  (where M(z) is the covariant disformal factor)
Standard GR perturbations; only background H(z) is modified.

Outputs:
    - logs/step_07_posteriors_full.log
    - results/07_mcmc_summary_full.json
"""

import sys
import json
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status
from scripts.utils.chain_integrity import inspect_chain_prefix, require_completed_chains


class Step07Posteriors:
    """Step 07: Posterior analysis from MCMC chains (Rigorous)."""
    
    STEP_NAME = "07_posteriors"
    STEP_DESCRIPTION = "Posterior Analysis (Rigorous Audit)"
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.chains_dir = self.results_dir / "mcmc_chains"
        
        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}_full.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}_full", log_file)
        set_step_logger(self.logger)
    
    def _load_chains(self, prefix: str, min_cols: int = 8):
        """Load and validate chain files for a given prefix, returning (combined, chains_list, col_map)."""
        directory = self.chains_dir / prefix
        if not any(directory.glob(prefix + ".*.txt")):
            directory = self.chains_dir
        candidates = list(directory.glob(f"{prefix}*.txt"))
        chain_files = sorted(
            f for f in candidates
            if f.suffix == '.txt'
            and f.stem.rsplit('.', 1)[-1].isdigit()
            and f.stem.rsplit('.', 1)[0] == prefix
        )
        
        if not chain_files:
            print_status(f"  ! No chain files found for prefix: {prefix}", "WARNING")
            return None, None, None
        
        all_data = []
        per_chain_data = []
        total_rows = 0
        col_map = None
        for cf in chain_files:
            with open(cf) as f:
                header = f.readline().strip()
            if header.startswith('#'):
                cols = [c.strip() for c in header[1:].split()]
                col_map = {name: i for i, name in enumerate(cols)}
            data = np.loadtxt(cf)
            if data.ndim == 2 and data.shape[1] >= min_cols:
                all_data.append(data)
                total_rows += data.shape[0]
                # Apply per-chain burn-in (30%)
                burn_in = int(0.3 * data.shape[0])
                per_chain_data.append(data[burn_in:])
        
        if not all_data or col_map is None:
            print_status(f"  ! Could not parse chain files for: {prefix}", "WARNING")
            return None, None, None
        
        combined = np.vstack(all_data)
        
        unique_rows = len(np.unique(combined, axis=0))
        if unique_rows < total_rows * 0.5:
            raise RuntimeError(
                f"CRITICAL: Chains for {prefix} have only {unique_rows}/{total_rows} unique rows. "
                "This indicates synthetic/mocked data. Pipeline MUST fail."
            )
        
        print_status(f"  ✓ Loaded {total_rows:,} samples from {len(chain_files)} chains ({prefix})", "SUCCESS")
        return combined, per_chain_data, col_map
    
    def _read_cobaya_sampler_rminus1(self, prefix: str):
        """Read Cobaya's internal MCMC R-1 from the .progress file when present."""
        nested = self.chains_dir / prefix / f"{prefix}.progress"
        progress = nested if nested.exists() else self.chains_dir / f"{prefix}.progress"
        if not progress.exists():
            return None
        try:
            import yaml
            with open(progress) as f:
                data = yaml.safe_load(f)
            if not isinstance(data, dict):
                data = {}
            for key in ("Rminus1", "R_minus_1", "R-1"):
                if key in data and data[key] is not None:
                    return float(data[key])
            sampler = data.get("sampler", {})
            mcmc = sampler.get("mcmc", {}) if isinstance(sampler, dict) else {}
            for key in ("Rminus1", "R_minus_1", "R-1"):
                if key in mcmc and mcmc[key] is not None:
                    return float(mcmc[key])
        except Exception:
            pass
        # Cobaya production progress is a whitespace table, not YAML.
        try:
            lines=progress.read_text().splitlines()
            header=next(line.lstrip('#').split() for line in lines if line.startswith('#'))
            rows=[line.split() for line in lines if line.strip() and not line.startswith('#')]
            value=float(rows[-1][header.index('Rminus1')])
            if np.isfinite(value):return value
        except (StopIteration,ValueError,IndexError):
            pass
        # Fallback: scan raw text for "R-1 = <float>" lines from Cobaya logs
        try:
            text = progress.read_text()
            import re
            matches = re.findall(r"R-1\s*[=:]\s*([0-9.]+)", text)
            if matches:
                return float(matches[-1])
        except Exception:
            return None
        return None
    
    def _gelman_rubin(self, chains, idx):
        """Classic scalar R-hat minus one on the uncompressed iteration chains;
        distinct from Cobaya's multivariate internal convergence metric."""
        m = len(chains)
        if m < 2:
            return None
        # Cobaya rows have integer frequency weights: rejected states are
        # compressed, so equal row counts are unequal iteration lengths.
        weights=[np.asarray(c[:,0],dtype=float) for c in chains]
        if any(not np.all(np.isfinite(w)) or np.any(w<=0) or not np.allclose(w,np.rint(w),rtol=0,atol=1e-8) for w in weights):
            raise ValueError('Classic chain R-hat requires positive integer frequency weights')
        n=int(min(np.sum(w) for w in weights))
        if n<2:return None
        chain_means=[];chain_vars=[]
        for c,w in zip(chains,weights):
            # Take exactly the same iteration prefix without expanding rows.
            effective=np.clip(n-(np.cumsum(w)-w),0,w)
            col=c[:,idx];mean=float(np.dot(effective,col)/n)
            chain_means.append(mean)
            chain_vars.append(float(np.dot(effective,(col-mean)**2)/(n-1)))
        chain_means = np.array(chain_means)
        chain_vars = np.array(chain_vars)
        overall_mean = np.mean(chain_means)
        B = n * np.sum((chain_means - overall_mean) ** 2) / (m - 1)
        W = np.mean(chain_vars)
        if W == 0:
            return float('inf')
        V_hat = ((n - 1) / n) * W + B / n
        R_hat = np.sqrt(V_hat / W)
        return float(R_hat - 1.0)
    
    def run(self, allow_incomplete: bool = False) -> dict:
        """Execute rigorous posterior analysis on ALL chain files."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status("SCOPE: hi_class with native TEP background-only + active-perturbation.", "INFO")
        print_status("Reference: C0 background/acoustic diagnostic epsilon_T = -0.0015 +- 0.0037; its amplitude is distinct from the HC inference parameter.", "INFO")
        
        # Published summaries require coherent saved collections. Diagnostic
        # callers may opt in to incomplete outputs and must label that scope.
        integrity = {}
        for prefix in ("tep_hiclass_suite", "tep_hiclass_perturbations",
                       "tep_native_ttteee", "lcdm_ttteee", "tep_zscan_ttteee",
                       "tep_hiclass_perturbations_ttteee"):
            nested = self.chains_dir / prefix / prefix
            base = nested if any(nested.parent.glob(prefix + ".*.txt")) else self.chains_dir / prefix
            if prefix in ("tep_zscan_ttteee", "tep_hiclass_perturbations_ttteee") and not any(base.parent.glob(prefix + ".*.txt")):
                continue
            integrity[prefix] = (inspect_chain_prefix(base) if allow_incomplete
                                 else require_completed_chains(base))

        results = {
            "chain_integrity": integrity,
            "diagnostic_only": allow_incomplete,
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING",
            "burn_in_scope": "First 30% of rows removed separately from each chain before weighted pooling",
            "inference_scope": "Summary of the available chain files; execution success does not certify convergence or provenance of a separate reported production run",
            "R_minus_1_scope": "Classic scalar R-hat on integer-frequency-expanded chains; not Cobaya multivariate internal Rminus1",
            "tep": {},
            "tep_perturbation": {},
            "tep_ttteee": {},
            "lcdm": {},
            "comparison": {},
            "ttteee_comparison": {}
        }
        
        try:
            # ---- Load background-only TEP chains ----
            tep_combined, tep_chains, tep_cols = self._load_chains("tep_hiclass_suite")
            if tep_combined is None:
                tep_combined, tep_chains, tep_cols = self._load_chains("tep_hiclass_chain")
            if tep_combined is None:
                raise FileNotFoundError("No TEP background MCMC chains found.")
            
            # ---- Load active-perturbation TEP chains ----
            pert_combined, pert_chains, pert_cols = self._load_chains("tep_hiclass_perturbations")
            if pert_combined is None:
                print_status("  ! No perturbation chains found; proceeding with background-only.", "WARNING")
                pert_combined = None
            
            # ---- High-l TTTEEE chains (headline full-likelihood runs) ----
            ttteee_combined, ttteee_chains, ttteee_cols = self._load_chains("tep_native_ttteee")
            if ttteee_combined is None:
                print_status("  ! No native TEP TTTEEE chains found.", "WARNING")
            lcdm_combined, lcdm_chains, lcdm_cols = self._load_chains("lcdm_ttteee")
            if lcdm_combined is None:
                print_status("  ! No LCDM TTTEEE chains found.", "WARNING")
            
            # Map parameter names to column indices dynamically from headers
            param_names = ["A_s", "n_s", "H0", "omega_b", "omega_cdm", "tau_reio", "A_planck", "epsilon_T", "sigma8"]
            
            def _get_idx(col_map, name):
                if name in col_map:
                    return col_map[name]
                if name == "A_s" and "logA" in col_map:
                    return col_map["logA"]
                raise KeyError(f"Parameter {name} not found in chain header")
            
            def _stats(data, idx):
                col = data[:, idx]
                w = data[:, 0]
                w_sum = np.sum(w)
                mean = np.sum(w * col) / w_sum
                # Frequency weights count repeated chain states, rather than
                # importance weights. Match sample variance on expanded rows.
                var = np.sum(w * (col - mean)**2) / (w_sum - 1) if w_sum > 1 else 0.0
                s = np.argsort(col)
                cw = np.cumsum(w[s])
                median = col[s][min(np.searchsorted(cw, 0.5 * w_sum), len(s) - 1)]
                upper_95 = col[s][min(np.searchsorted(cw, 0.95 * w_sum), len(s) - 1)]
                upper_975 = col[s][min(np.searchsorted(cw, 0.975 * w_sum), len(s) - 1)]
                return {"mean": float(mean), "std": float(np.sqrt(var)), "median": float(median),
                        "upper_95": float(upper_95), "upper_975": float(upper_975),
                        "min": float(np.min(col)), "max": float(np.max(col))}
            
            n_chains = len(tep_chains)
            r_minus_1 = {}
            max_r = None
            if n_chains < 2:
                print_status(
                    f"Gelman-Rubin R-1: N/A ({n_chains} chain loaded; requires >= 2 chains)",
                    "INFO",
                )
                for name in param_names:
                    r_minus_1[name] = None
            else:
                print_status("Cross-chain Gelman-Rubin R-1:", "INFO")
                max_r = 0.0
                for name in param_names:
                    idx = _get_idx(tep_cols, name)
                    r1 = self._gelman_rubin(tep_chains, idx)
                    r_minus_1[name] = r1
                    max_r = max(max_r, r1)
                    print_status(f"    {name}: R-1 = {r1:.4f}", "INFO")
                level = "INFO" if max_r < 0.05 else "WARNING"
                print_status(f"  Max R-1 across parameters: {max_r:.4f}", level)
            
            # Apply the already-computed 30% burn-in separately to every chain
            tep_post = np.vstack(tep_chains)
            
            # Compute S8 column: S8 = sigma8 * sqrt( (omega_cdm + omega_b)/(H0/100)^2 / 0.3 )
            idx_sigma8 = _get_idx(tep_cols, "sigma8")
            idx_ocdm = _get_idx(tep_cols, "omega_cdm")
            idx_ob = _get_idx(tep_cols, "omega_b")
            idx_H0 = _get_idx(tep_cols, "H0")
            
            sigma8_col = tep_post[:, idx_sigma8]
            ocdm_col = tep_post[:, idx_ocdm]
            ob_col = tep_post[:, idx_ob]
            h0_col = tep_post[:, idx_H0]
            
            Om = (ocdm_col + ob_col) / (h0_col / 100.0)**2
            S8_col = sigma8_col * np.sqrt(Om / 0.3)
            
            # Add S8 to the dataset dynamically
            tep_post = np.column_stack((tep_post, S8_col))
            tep_cols["S8"] = tep_post.shape[1] - 1
            param_names.append("S8")
            r_minus_1["S8"] = None  # derived parameter; no cross-chain R-1 unless computed per chain

            chain_word = "chain" if n_chains == 1 else "chains"
            print_status(f"TEP constraints (combined, {n_chains} {chain_word}):", "INFO")
            for name in param_names:
                idx = _get_idx(tep_cols, name)
                st = _stats(tep_post, idx)
                st["R_minus_1"] = r_minus_1[name]
                results["tep"][name] = st
                fmt = "{:.3e}" if abs(st["mean"]) < 0.001 else "{:.5f}"
                print_status(f"    {name}: " + fmt.format(st["mean"]) + f" ± {st['std']:.5f}", "INFO")
            
            results["tep"]["best_logpost"] = float(-np.min(tep_post[:, 1]))
            results["tep"]["tep_c0_reference"] = (
                "TEP-C0 (Paper 26) native TEP: n_s = 0.9619 +- 0.0046; "
                "joint epsilon_T = (6.75 +- 0.24) x 10^-6"
            )
            results["tep"]["n_samples"] = tep_post.shape[0]
            results["tep"]["n_chains"] = n_chains
            results["tep"]["max_R_minus_1"] = max_r
            results["tep"]["gelman_rubin_applicable"] = n_chains >= 2
            internal_r = self._read_cobaya_sampler_rminus1("tep_hiclass_suite")
            results["tep"]["internal_sampler_R_minus_1"] = internal_r
            if internal_r is not None:
                print_status(f"  Cobaya internal sampler R-1: {internal_r:.4f}", "INFO")
            
            # ---- Active-perturbation analysis ----
            if pert_combined is not None:
                print_status("Active-perturbation constraints:", "INFO")
                
                pert_post = np.vstack(pert_chains)
                
                # Compute S8 for perturbation chain
                p_sigma8 = pert_post[:, _get_idx(pert_cols, "sigma8")]
                p_ocdm = pert_post[:, _get_idx(pert_cols, "omega_cdm")]
                p_ob = pert_post[:, _get_idx(pert_cols, "omega_b")]
                p_h0 = pert_post[:, _get_idx(pert_cols, "H0")]
                p_Om = (p_ocdm + p_ob) / (p_h0 / 100.0)**2
                p_S8 = p_sigma8 * np.sqrt(p_Om / 0.3)
                pert_post = np.column_stack((pert_post, p_S8))
                pert_cols["S8"] = pert_post.shape[1] - 1
                
                pert_n_chains = len(pert_chains)
                pert_r_minus_1 = {}
                pert_max_r = None
                if pert_n_chains >= 2:
                    for name in param_names:
                        idx = _get_idx(pert_cols, name)
                        # Skip S8 for R-1 (derived parameter, not in original chains)
                        if name == "S8":
                            continue
                        r1 = self._gelman_rubin(pert_chains, idx)
                        pert_r_minus_1[name] = r1
                        if pert_max_r is None or r1 > pert_max_r:
                            pert_max_r = r1
                    print_status(f"  Max R-1 across parameters: {pert_max_r:.4f}", "INFO")
                
                for name in param_names + ["S8"]:
                    idx = _get_idx(pert_cols, name)
                    st = _stats(pert_post, idx)
                    st["R_minus_1"] = pert_r_minus_1.get(name, None)
                    results["tep_perturbation"][name] = st
                    fmt = "{:.3e}" if abs(st["mean"]) < 0.001 else "{:.5f}"
                    print_status(f"    {name}: " + fmt.format(st["mean"]) + f" ± {st['std']:.5f}", "INFO")
                
                results["tep_perturbation"]["n_samples"] = pert_post.shape[0]
                results["tep_perturbation"]["n_chains"] = pert_n_chains
                results["tep_perturbation"]["max_R_minus_1"] = pert_max_r
                
                # ---- Comparison: background vs perturbation ----
                print_status("Comparison (perturbation - background):", "INFO")
                comp = results["comparison"]
                
                bg_chi2_min = float(np.min(tep_post[:, _get_idx(tep_cols, "chi2")]))
                pert_chi2_min = float(np.min(pert_post[:, _get_idx(pert_cols, "chi2")]))
                comp["delta_chi2"] = pert_chi2_min - bg_chi2_min
                print_status(f"    Δχ² = {comp['delta_chi2']:.3f}", "INFO")
                
                for name in param_names + ["S8"]:
                    bg_st = results["tep"][name]
                    pert_st = results["tep_perturbation"][name]
                    dmu = pert_st["mean"] - bg_st["mean"]
                    joint = np.sqrt(bg_st["std"]**2 + pert_st["std"]**2)
                    sigma = dmu / joint if joint > 0 else 0.0
                    comp[name] = {
                        "delta_mean": dmu,
                        "sigma_joint": joint,
                        "delta_sigma": sigma
                    }
                    print_status(f"    Δ{name}: {dmu:.6f} (joint σ = {joint:.5f}, Δ/σ = {sigma:.2f})", "INFO")
                
                # Summary: max disagreement
                max_disagree = max(comp[n]["delta_sigma"] for n in param_names + ["S8"])
                comp["max_disagreement_sigma"] = float(max_disagree)
                print_status(f"  Maximum parameter disagreement: {max_disagree:.2f}σ", "INFO")
            
            # ---- Native TEP high-l TTTEEE posterior ----
            if ttteee_combined is not None:
                print_status("Native TEP high-l TTTEEE constraints:", "INFO")
                ttteee_post = np.vstack(ttteee_chains)

                t_sigma8 = ttteee_post[:, _get_idx(ttteee_cols, "sigma8")]
                t_ocdm = ttteee_post[:, _get_idx(ttteee_cols, "omega_cdm")]
                t_ob = ttteee_post[:, _get_idx(ttteee_cols, "omega_b")]
                t_h0 = ttteee_post[:, _get_idx(ttteee_cols, "H0")]
                t_Om = (t_ocdm + t_ob) / (t_h0 / 100.0)**2
                t_S8 = t_sigma8 * np.sqrt(t_Om / 0.3)
                ttteee_post = np.column_stack((ttteee_post, t_S8))
                ttteee_cols["S8"] = ttteee_post.shape[1] - 1

                t_n_chains = len(ttteee_chains)
                t_r_minus_1 = {}
                t_max_r = None
                if t_n_chains >= 2:
                    for name in param_names:
                        if name == "S8":
                            continue
                        r1 = self._gelman_rubin(ttteee_chains, _get_idx(ttteee_cols, name))
                        t_r_minus_1[name] = r1
                        if t_max_r is None or r1 > t_max_r:
                            t_max_r = r1
                    print_status(f"  Max R-1 across parameters: {t_max_r:.4f}", "INFO")

                for name in param_names:
                    st = _stats(ttteee_post, _get_idx(ttteee_cols, name))
                    st["R_minus_1"] = t_r_minus_1.get(name, None)
                    results["tep_ttteee"][name] = st
                    fmt = "{:.3e}" if abs(st["mean"]) < 0.001 else "{:.5f}"
                    print_status(f"    {name}: " + fmt.format(st["mean"]) + f" ± {st['std']:.5f}", "INFO")

                results["tep_ttteee"]["best_logpost"] = float(-np.min(ttteee_post[:, 1]))
                results["tep_ttteee"]["n_samples"] = int(ttteee_post.shape[0])
                results["tep_ttteee"]["n_chains"] = t_n_chains
                results["tep_ttteee"]["max_R_minus_1"] = t_max_r
                results["tep_ttteee"]["internal_sampler_R_minus_1"] = self._read_cobaya_sampler_rminus1("tep_native_ttteee")

            # ---- LCDM high-l TTTEEE reference posterior ----
            if lcdm_combined is not None:
                print_status("LCDM high-l TTTEEE constraints:", "INFO")
                lcdm_post = np.vstack(lcdm_chains)

                l_sigma8 = lcdm_post[:, _get_idx(lcdm_cols, "sigma8")]
                l_ocdm = lcdm_post[:, _get_idx(lcdm_cols, "omega_cdm")]
                l_ob = lcdm_post[:, _get_idx(lcdm_cols, "omega_b")]
                l_h0 = lcdm_post[:, _get_idx(lcdm_cols, "H0")]
                l_Om = (l_ocdm + l_ob) / (l_h0 / 100.0)**2
                l_S8 = l_sigma8 * np.sqrt(l_Om / 0.3)
                lcdm_post = np.column_stack((lcdm_post, l_S8))
                lcdm_cols["S8"] = lcdm_post.shape[1] - 1

                l_n_chains = len(lcdm_chains)
                l_r_minus_1 = {}
                l_max_r = None
                if l_n_chains >= 2:
                    for name in param_names:
                        if name not in lcdm_cols or name == "S8":
                            continue
                        r1 = self._gelman_rubin(lcdm_chains, _get_idx(lcdm_cols, name))
                        l_r_minus_1[name] = r1
                        if l_max_r is None or r1 > l_max_r:
                            l_max_r = r1
                    print_status(f"  Max R-1 across parameters: {l_max_r:.4f}", "INFO")

                for name in param_names:
                    if name not in lcdm_cols:
                        continue
                    st = _stats(lcdm_post, _get_idx(lcdm_cols, name))
                    st["R_minus_1"] = l_r_minus_1.get(name, None)
                    results["lcdm"][name] = st
                    fmt = "{:.3e}" if abs(st["mean"]) < 0.001 else "{:.5f}"
                    print_status(f"    {name}: " + fmt.format(st["mean"]) + f" ± {st['std']:.5f}", "INFO")

                results["lcdm"]["best_logpost"] = float(-np.min(lcdm_post[:, 1]))
                results["lcdm"]["n_samples"] = int(lcdm_post.shape[0])
                results["lcdm"]["n_chains"] = l_n_chains
                results["lcdm"]["max_R_minus_1"] = l_max_r
                results["lcdm"]["internal_sampler_R_minus_1"] = self._read_cobaya_sampler_rminus1("lcdm_ttteee")

            # ---- TEP vs LCDM comparison on the matched TTTEEE likelihood ----
            if ttteee_combined is not None and lcdm_combined is not None:
                print_status("TTTEEE comparison (TEP - LCDM, chi2 excludes prior normalization):", "INFO")
                tchi2_min = float(np.min(ttteee_post[:, _get_idx(ttteee_cols, "chi2")]))
                lchi2_min = float(np.min(lcdm_post[:, _get_idx(lcdm_cols, "chi2")]))
                comp = results["ttteee_comparison"]
                comp["delta_chi2"] = tchi2_min - lchi2_min
                comp["chi2_min_tep"] = tchi2_min
                comp["chi2_min_lcdm"] = lchi2_min
                print_status(f"    Δχ² = {comp['delta_chi2']:.3f}", "INFO")

                for name in param_names:
                    if name not in results["tep_ttteee"] or name not in results["lcdm"]:
                        continue
                    t_st = results["tep_ttteee"][name]
                    l_st = results["lcdm"][name]
                    dmu = t_st["mean"] - l_st["mean"]
                    joint = np.sqrt(t_st["std"]**2 + l_st["std"]**2)
                    comp[name] = {"delta_mean": dmu, "sigma_joint": joint,
                                  "delta_sigma": dmu / joint if joint > 0 else 0.0}
                    print_status(f"    Δ{name}: {dmu:.6f} (joint σ = {joint:.5f})", "INFO")

            # ---- Free-z_T TTTEEE posterior (z_T marginalized) ----
            zscan_combined, zscan_chains, zscan_cols = self._load_chains("tep_zscan_ttteee")
            if zscan_combined is not None:
                print_status("Free-z_T TTTEEE constraints (z_T sampled):", "INFO")
                zscan_post = np.vstack(zscan_chains)

                z_sigma8 = zscan_post[:, _get_idx(zscan_cols, "sigma8")]
                z_ocdm = zscan_post[:, _get_idx(zscan_cols, "omega_cdm")]
                z_ob = zscan_post[:, _get_idx(zscan_cols, "omega_b")]
                z_h0 = zscan_post[:, _get_idx(zscan_cols, "H0")]
                z_Om = (z_ocdm + z_ob) / (z_h0 / 100.0)**2
                z_S8 = z_sigma8 * np.sqrt(z_Om / 0.3)
                zscan_post = np.column_stack((zscan_post, z_S8))
                zscan_cols["S8"] = zscan_post.shape[1] - 1

                z_n_chains = len(zscan_chains)
                z_r_minus_1 = {}
                z_max_r = None
                z_param_names = param_names + ["z_T"]
                if z_n_chains >= 2:
                    for name in z_param_names:
                        if name == "S8" or name not in zscan_cols:
                            continue
                        r1 = self._gelman_rubin(zscan_chains, _get_idx(zscan_cols, name))
                        z_r_minus_1[name] = r1
                        if z_max_r is None or r1 > z_max_r:
                            z_max_r = r1
                    print_status(f"  Max R-1 across parameters: {z_max_r:.4f}", "INFO")

                results["tep_zscan"] = {}
                for name in z_param_names:
                    if name not in zscan_cols:
                        continue
                    st = _stats(zscan_post, _get_idx(zscan_cols, name))
                    st["R_minus_1"] = z_r_minus_1.get(name, None)
                    results["tep_zscan"][name] = st
                    print_status(f"    {name}: {st['mean']:.5f} ± {st['std']:.5f}", "INFO")

                results["tep_zscan"]["best_logpost"] = float(-np.min(zscan_post[:, 1]))
                results["tep_zscan"]["n_samples"] = int(zscan_post.shape[0])
                results["tep_zscan"]["n_chains"] = z_n_chains
                results["tep_zscan"]["max_R_minus_1"] = z_max_r
                # Convergence gate: the chain's own stopping criterion is
                # Rminus1_stop = 0.05.  Posterior summaries must not be
                # consumed as publishable constraints until max_R_minus_1
                # is below that threshold; exploratory values are still
                # recorded but flagged.
                z_converged = (z_max_r is not None and z_max_r < 0.05)
                results["tep_zscan"]["convergence_threshold"] = 0.05
                results["tep_zscan"]["converged"] = bool(z_converged)
                results["tep_zscan"]["status"] = (
                    "CONVERGED" if z_converged else
                    "UNCONVERGED_PROVISIONAL_ONLY")
                if not z_converged:
                    print_status(
                        "  WARNING: tep_zscan chain UNCONVERGED "
                        f"(max R-1 = {z_max_r}); posterior summaries are "
                        "provisional and must not be quoted as final "
                        "constraints.", "WARNING")

                # Mode-split analysis: the profile scan shows the turnover
                # penalty switching on at z_T ~ 4-5.  Report the epsilon_T
                # posterior separately below/above z_T = 4 so a bimodal
                # (low-z_T positive-valley vs high-z_T bound) structure is
                # not masked by the pooled mean.
                if "z_T" in zscan_cols and "epsilon_T" in zscan_cols:
                    iz = zscan_post[:, _get_idx(zscan_cols, "z_T")]
                    ie = zscan_post[:, _get_idx(zscan_cols, "epsilon_T")]
                    iw = zscan_post[:, 0]
                    modes = {}
                    for label, mask in (
                        ("low_zT", iz < 4.0),
                        ("high_zT", iz >= 4.0),
                    ):
                        m = np.where(mask)[0]
                        if len(m) < 10:
                            modes[label] = {"mass_fraction": float(
                                np.sum(iw[m]) / np.sum(iw)), "note": "fewer than 10 samples"}
                            continue
                        sub = zscan_post[m]
                        st = _stats(sub, _get_idx(zscan_cols, "epsilon_T"))
                        zst = _stats(sub, _get_idx(zscan_cols, "z_T"))
                        st["mass_fraction"] = float(np.sum(iw[m]) / np.sum(iw))
                        st["z_T_median"] = zst["median"]
                        modes[label] = st
                        print_status(
                            f"    mode {label} (z_T {'<' if label=='low_zT' else '>='} 4): "
                            f"eps={st['mean']:.4f} ± {st['std']:.4f}, "
                            f"mass={st['mass_fraction']:.3f}", "INFO")
                    results["tep_zscan"]["mode_split"] = {
                        "split_at_z_T": 4.0,
                        "modes": modes,
                    }

            # ---- Active-perturbation high-l TTTEEE posterior ----
            pt_combined, pt_chains, pt_cols = self._load_chains(
                "tep_hiclass_perturbations_ttteee")
            if pt_combined is not None:
                print_status("Active-perturbation high-l TTTEEE constraints:", "INFO")
                pt_post = np.vstack(pt_chains)
                results["tep_perturbation_ttteee"] = {}
                pt_n = len(pt_chains)
                pt_max_r = None
                pt_r = {}
                if pt_n >= 2:
                    for name in param_names:
                        if name not in pt_cols:
                            continue
                        r1 = self._gelman_rubin(pt_chains, _get_idx(pt_cols, name))
                        pt_r[name] = r1
                        if pt_max_r is None or r1 > pt_max_r:
                            pt_max_r = r1
                for name in param_names:
                    if name not in pt_cols:
                        continue
                    st = _stats(pt_post, _get_idx(pt_cols, name))
                    st["R_minus_1"] = pt_r.get(name, None)
                    results["tep_perturbation_ttteee"][name] = st
                    print_status(f"    {name}: {st['mean']:.5f} ± {st['std']:.5f}", "INFO")
                results["tep_perturbation_ttteee"]["n_samples"] = int(pt_post.shape[0])
                results["tep_perturbation_ttteee"]["n_chains"] = pt_n
                results["tep_perturbation_ttteee"]["max_R_minus_1"] = pt_max_r

            provisional = []
            for key, prefix in (
                ("tep", "tep_hiclass_suite"),
                ("tep_perturbation", "tep_hiclass_perturbations"),
                ("tep_ttteee", "tep_native_ttteee"),
                ("lcdm", "lcdm_ttteee"),
                ("tep_zscan", "tep_zscan_ttteee"),
                ("tep_perturbation_ttteee", "tep_hiclass_perturbations_ttteee"),
            ):
                section = results.get(key)
                if not section:
                    continue
                report = integrity[prefix]
                r = section.get("max_R_minus_1")
                section["collection_integrity_valid"] = report["valid_completed_run"]
                section["sampler_converged"] = bool(report["checkpoint"].get("converged"))
                section["convergence_threshold"] = 0.05
                section["converged"] = bool(report["valid_completed_run"] and
                                             r is not None and np.isfinite(r) and r < 0.05)
                section["status"] = "CONVERGED" if section["converged"] else "PROVISIONAL_ONLY"
                if not section["converged"]:
                    provisional.append(prefix)
            if provisional and not allow_incomplete:
                raise RuntimeError("Posterior diagnostics still provisional: " + ", ".join(provisional))
            results["status"] = "DIAGNOSTIC_ONLY" if allow_incomplete else "SUCCESS"

            # Save rigorous summary
            output_file = self.results_dir / "07_mcmc_summary_full.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print_status(f"  ✓ Saved summary to {output_file}", "SUCCESS")
            
            # Print key take-away
            if pert_combined is not None:
                eps_diff = results["comparison"]["epsilon_T"]["delta_sigma"]
                print_status(f"Key result: background vs perturbation ε_T agrees to {eps_diff:.2f}σ", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results


if __name__ == "__main__":
    step = Step07Posteriors()
    step.run()
