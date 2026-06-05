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
        chain_files = sorted(self.chains_dir.glob(f"{prefix}*.txt"))
        chain_files = [f for f in chain_files if f.suffix == '.txt' and f.stem.split('.')[-1].isdigit()]
        
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
    
    def _gelman_rubin(self, chains, idx):
        """Compute Gelman-Rubin R-1 for a given parameter index across chains."""
        m = len(chains)
        if m < 2:
            return None
        # Use same length for all chains (minimum)
        n = min(c.shape[0] for c in chains)
        chain_means = []
        chain_vars = []
        for c in chains:
            col = c[:n, idx]
            chain_means.append(np.mean(col))
            chain_vars.append(np.var(col, ddof=1) if n > 1 else 0.0)
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
    
    def run(self) -> dict:
        """Execute rigorous posterior analysis on ALL chain files."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status("SCOPE: hi_class with native TEP background-only implementation.", "INFO")
        print_status("Reference: TEP-C0 (Paper 26) native TEP + full Planck finds n_s = 0.9623 +- 0.0046.", "INFO")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "RUNNING",
            "tep": {},
            "lcdm": {},
            "comparison": {}
        }
        
        try:
            # Load all TEP chains matching tep_hiclass_suite prefix
            tep_combined, tep_chains, tep_cols = self._load_chains("tep_hiclass_suite")
            if tep_combined is None:
                # Fallback to single-chain production run
                tep_combined, tep_chains, tep_cols = self._load_chains("tep_hiclass_chain")
            if tep_combined is None:
                raise FileNotFoundError("No TEP MCMC chains found.")
            
            # LCDM comparison skipped: existing lcdm_comparison chain uses
            # Planck high-l Plik (different likelihoods), making comparison
            # methodologically invalid. TEP constraints are reported standalone
            # against published Planck 2018 values in the manuscript.
            lcdm_available = False
            
            # Map parameter names to column indices dynamically from headers
            param_names = ["A_s", "n_s", "H0", "omega_b", "omega_cdm", "tau_reio", "A_planck", "epsilon_T", "sigma8"]
            
            def _get_idx(col_map, name):
                if name in col_map:
                    return col_map[name]
                # Fallback: logA maps to A_s via lambda, but we want A_s if available
                if name == "A_s" and "logA" in col_map:
                    return col_map["logA"]
                raise KeyError(f"Parameter {name} not found in chain header")
            
            def _stats(data, idx):
                col = data[:, idx]
                w = data[:, 0]
                w_sum = np.sum(w)
                mean = np.sum(w * col) / w_sum
                w2 = np.sum(w**2)
                n_eff = w_sum**2 / w2 if w2 > 0 else len(col)
                var = np.sum(w * (col - mean)**2) / (w_sum * (1 - 1/n_eff)) if n_eff > 1 else 0.0
                s = np.argsort(col)
                median = col[s][np.searchsorted(np.cumsum(w[s]), 0.5 * w_sum)]
                return {"mean": float(mean), "std": float(np.sqrt(var)), "median": float(median),
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
            
            # Apply 30% burn-in to combined data for posterior analysis
            burn_in = int(0.3 * tep_combined.shape[0])
            tep_post = tep_combined[burn_in:]
            
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
            results["tep"]["tep_c0_reference"] = "TEP-C0 (Paper 26) native TEP: n_s = 0.9623 +- 0.0046"
            results["tep"]["n_samples"] = tep_post.shape[0]
            results["tep"]["n_chains"] = n_chains
            results["tep"]["max_R_minus_1"] = max_r
            results["tep"]["gelman_rubin_applicable"] = n_chains >= 2
            
            if lcdm_available:
                print_status("LCDM constraints:", "INFO")
                for name in param_names:
                    idx = _get_idx(lcdm_cols, name)
                    st = _stats(lcdm_data, idx)
                    results["lcdm"][name] = st
                    fmt = "{:.3e}" if abs(st["mean"]) < 0.001 else "{:.5f}"
                    print_status(f"    {name}: " + fmt.format(st["mean"]) + f" ± {st['std']:.5f}", "INFO")
                
                results["lcdm"]["best_logpost"] = float(-np.min(lcdm_data[:, 1]))
                results["lcdm"]["n_samples"] = lcdm_data.shape[0]
                
                print_status("Comparison:", "INFO")
                dchi2 = 2.0 * (float(np.min(tep_post[:, 1])) - float(np.min(lcdm_data[:, 1])))
                results["comparison"]["delta_chi2"] = dchi2
                print_status(f"    Δχ² = {dchi2:.3f}", "INFO")
                
                for name in param_names:
                    dmu = results["tep"][name]["mean"] - results["lcdm"][name]["mean"]
                    joint = np.sqrt(results["tep"][name]["std"]**2 + results["lcdm"][name]["std"]**2)
                    results["comparison"][f"{name}_diff"] = {"delta_mean": dmu, "sigma_joint": joint}
                    print_status(f"    Δ{name}: {dmu:.5f} (joint σ = {joint:.5f})", "INFO")
            
            results["status"] = "SUCCESS"
            
            # Save rigorous summary
            output_file = self.results_dir / "07_mcmc_summary_full.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            print_status(f"  ✓ Saved summary to {output_file}", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results


if __name__ == "__main__":
    step = Step07Posteriors()
    step.run()
