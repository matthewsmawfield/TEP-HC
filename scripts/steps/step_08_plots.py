#!/usr/bin/env python3
"""
Step 08: Posterior Visualization (GetDist)
==========================================
Generates marginalized posterior triangle plots comparing background-only
and active-perturbation MCMC chains.

Outputs:
    - results/figures/tep_perturbation_triangle.png
    - logs/step_08_plots_full.log
"""

import sys
import numpy as np
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step08Plots:
    """Step 08: Generate comparison triangle plot via GetDist."""

    STEP_NAME = "08_plots"
    STEP_DESCRIPTION = "Posterior Visualization (GetDist)"

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.fig_dir = self.results_dir / "figures"
        self.fig_dir.mkdir(parents=True, exist_ok=True)

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}_full.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}_full", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Generate GetDist triangle plot comparing background vs perturbation."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status("Loading MCMC chains for GetDist visualization...", "PROCESS")

        try:
            from getdist import plots, MCSamples
        except ImportError:
            raise ImportError("getdist not installed. Install: pip install getdist")

        chains_dir = self.results_dir / "mcmc_chains"

        # ---- Load background-only chain ----
        bg_file = chains_dir / "tep_hiclass_suite.1.txt"
        pert_file = chains_dir / "tep_hiclass_perturbations.1.txt"

        if not bg_file.exists():
            raise FileNotFoundError(f"Background chain not found: {bg_file}")
        if not pert_file.exists():
            raise FileNotFoundError(f"Perturbation chain not found: {pert_file}")

        # Read headers for parameter names
        def _read_header(fpath):
            with open(fpath) as f:
                line = f.readline().strip()
            if line.startswith('#'):
                names = [c.strip() for c in line[1:].split()]
                # Skip weight, minuslogpost; keep actual params + chi2 for possible use
                return names
            return None

        bg_names = _read_header(bg_file)
        pert_names = _read_header(pert_file)

        # Load data
        bg_data = np.loadtxt(bg_file)
        pert_data = np.loadtxt(pert_file)

        # Apply 30% burn-in
        bg_burn = int(0.3 * bg_data.shape[0])
        pert_burn = int(0.3 * pert_data.shape[0])
        bg_post = bg_data[bg_burn:]
        pert_post = pert_data[pert_burn:]

        print_status(f"  Background: {bg_post.shape[0]} post-burn-in samples", "INFO")
        print_status(f"  Perturbation: {pert_post.shape[0]} post-burn-in samples", "INFO")

        # Map parameter names to indices (skip weight col 0, minuslogpost col 1)
        # GetDist expects: weight column, -loglike column, then parameter columns
        # But MCSamples.from_numpy can accept explicit arrays

        # Parameters to plot
        plot_params = ["epsilon_T", "H0", "n_s", "sigma8"]

        def _extract(samples, names, params):
            """Extract parameter columns from samples using header names."""
            # Find indices
            idxs = []
            for p in params:
                if p in names:
                    idxs.append(names.index(p))
                else:
                    raise KeyError(f"Parameter {p} not found in header: {names}")
            return samples[:, idxs]

        bg_params = _extract(bg_post, bg_names, plot_params)
        pert_params = _extract(pert_post, pert_names, plot_params)

        # Create MCSamples: pass weights and loglikes separately
        bg_samples = MCSamples(
            samples=bg_params,
            weights=bg_post[:, 0],
            loglikes=bg_post[:, 1],
            names=["epsilon_T", "H0", "n_s", "sigma8"],
            labels=[r"\epsilon_T", r"H_0", r"n_s", r"\sigma_8"],
            sampler="mcmc",
            name_tag="background-only"
        )
        pert_samples = MCSamples(
            samples=pert_params,
            weights=pert_post[:, 0],
            loglikes=pert_post[:, 1],
            names=["epsilon_T", "H0", "n_s", "sigma8"],
            labels=[r"\epsilon_T", r"H_0", r"n_s", r"\sigma_8"],
            sampler="mcmc",
            name_tag="active-perturbation"
        )

        # Generate triangle plot
        print_status("Generating triangle plot...", "PROCESS")
        g = plots.get_subplot_plotter()
        g.settings.figure_legend_frame = False
        g.settings.legend_fontsize = 14
        g.settings.axes_fontsize = 12
        g.settings.lab_fontsize = 14

        g.triangle_plot(
            [bg_samples, pert_samples],
            plot_params,
            filled=True,
            legend_labels=[
                r"Background-only TEP ($\delta\phi$ frozen)",
                r"Active-perturbation TEP ($\delta\phi$ evolved)"
            ],
            legend_loc="upper right",
            colors=["#1f77b4", "#d62728"],  # blue, red
            line_args=[{"lw": 1.5, "color": "#1f77b4"}, {"lw": 1.5, "color": "#d62728"}],
            contour_colors=["#1f77b4", "#d62728"],
            contour_ls="-",
            contour_lws=1.5,
        )

        output_file = self.fig_dir / "tep_perturbation_triangle.png"
        g.export(str(output_file))
        print_status(f"  ✓ Saved triangle plot: {output_file}", "SUCCESS")

        # Also generate 2D ε_T vs H0 and ε_T vs S8 plots
        print_status("Generating 2D constraint panels...", "PROCESS")

        # Compute S8 for both chains
        def _compute_S8(data, names):
            s8_idx = names.index("sigma8")
            ocdm_idx = names.index("omega_cdm")
            ob_idx = names.index("omega_b")
            h0_idx = names.index("H0")
            s8 = data[:, s8_idx]
            ocdm = data[:, ocdm_idx]
            ob = data[:, ob_idx]
            h0 = data[:, h0_idx]
            Om = (ocdm + ob) / (h0 / 100.0)**2
            return s8 * np.sqrt(Om / 0.3)

        bg_S8 = _compute_S8(bg_post, bg_names)
        pert_S8 = _compute_S8(pert_post, pert_names)

        # Create S8 samples
        bg_s8_params = np.column_stack([
            bg_params[:, 0],  # epsilon_T
            bg_params[:, 1],  # H0
            bg_S8
        ])
        pert_s8_params = np.column_stack([
            pert_params[:, 0],
            pert_params[:, 1],
            pert_S8
        ])

        bg_s8_samples = MCSamples(
            samples=bg_s8_params,
            weights=bg_post[:, 0],
            loglikes=bg_post[:, 1],
            names=["epsilon_T", "H0", "S8"],
            labels=[r"\epsilon_T", r"H_0", r"S_8"],
            sampler="mcmc",
            name_tag="bg"
        )
        pert_s8_samples = MCSamples(
            samples=pert_s8_params,
            weights=pert_post[:, 0],
            loglikes=pert_post[:, 1],
            names=["epsilon_T", "H0", "S8"],
            labels=[r"\epsilon_T", r"H_0", r"S_8"],
            sampler="mcmc",
            name_tag="pert"
        )

        g2 = plots.get_subplot_plotter()
        g2.settings.figure_legend_frame = False
        g2.settings.legend_fontsize = 12
        g2.settings.axes_fontsize = 10
        g2.settings.lab_fontsize = 12

        g2.triangle_plot(
            [bg_s8_samples, pert_s8_samples],
            ["epsilon_T", "H0", "S8"],
            filled=True,
            legend_labels=[
                r"Background-only",
                r"Active-perturbation"
            ],
            legend_loc="upper right",
            colors=["#1f77b4", "#d62728"],
            line_args=[{"lw": 1.5, "color": "#1f77b4"}, {"lw": 1.5, "color": "#d62728"}],
            contour_colors=["#1f77b4", "#d62728"],
        )

        output_s8 = self.fig_dir / "tep_perturbation_S8_triangle.png"
        g2.export(str(output_s8))
        print_status(f"  ✓ Saved S8 triangle plot: {output_s8}", "SUCCESS")

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "status": "SUCCESS",
            "figures": [
                str(output_file.relative_to(self.root_dir)),
                str(output_s8.relative_to(self.root_dir))
            ],
            "n_samples_bg": int(bg_post.shape[0]),
            "n_samples_pert": int(pert_post.shape[0])
        }

        print_status("Step completed.", "SUCCESS")
        return results


if __name__ == "__main__":
    step = Step08Plots()
    step.run()
