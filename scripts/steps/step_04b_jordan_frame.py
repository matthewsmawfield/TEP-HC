#!/usr/bin/env python3
"""
Step 04b: Jordan-Frame No-Dark-Energy Reconstruction
====================================================
Evaluates whether TEP can recover the observed acoustic scale 100*theta_s
in a universe completely devoid of Dark Energy (Einstein-de Sitter, Omega_m=1).

Method: run hi_class native tep_mode with Omega_Lambda=0 and scan epsilon_T.

Note: H_TEP = H_LCDM * M(z) (disformal metric: background expansion and
null geodesics are separate).
The physical expansion rate in the Jordan frame is:
    H~(~z) = H_LCDM(~z) * [A(phi)/(1 - alpha_A)]
By treating hi_class's internal scale factor as the physical Jordan-frame
variable, standard thermodynamics (T ~ 1+~z, rho_b ~ (1+~z)^3) are natively
correct. The only modification is the background Hubble rate.

Outputs:
    - results/04b_jordan_frame_scan.json
    - results/figures/figure_5_jordan_theta_s.png (if matplotlib available)
"""

import sys
import json
import subprocess
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step04BJordanFrame:
    """Step 04b: Jordan-frame EdS + TEP scan for theta_s recovery."""

    STEP_NAME = "04b_jordan_frame"
    STEP_DESCRIPTION = "Jordan-Frame No-Dark-Energy theta_s Reconstruction"

    # Scan parameters: epsilon_T values to test
    EPSILON_T_VALUES = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
    Z_T_STANDARD = 5.0
    Z_T_UNSCREENED = 1e6  # Effectively infinity: no early-universe suppression

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.figures_dir = self.results_dir / "figures"
        self.figures_dir.mkdir(parents=True, exist_ok=True)
        self.hi_class_bin = self.root_dir / "external" / "hi_class" / "hi_class" / "class"

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Execute Jordan-frame EdS + TEP scan."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "standard_scan": {"z_T": self.Z_T_STANDARD, "scan": []},
            "unscreened_scan": {"z_T": self.Z_T_UNSCREENED, "scan": []},
            "status": "RUNNING"
        }

        try:
            if not self.hi_class_bin.exists():
                print_status(
                    f"  hi_class binary not found at {self.hi_class_bin}; "
                    "Jordan-frame scan skipped (install hi_class to enable).",
                    "WARNING"
                )
                results["status"] = "SKIPPED"
                results["reason"] = "hi_class binary not found"
                return results

            # --- Standard scan (z_T = 5, early-universe suppression active) ---
            print_status(f"  === Standard Scan (z_T = {self.Z_T_STANDARD}) ===", "TITLE")
            for eps in self.EPSILON_T_VALUES:
                print_status(f"  Running EdS + tep_mode, z_T={self.Z_T_STANDARD}, epsilon_T = {eps:.2f}...", "PROCESS")
                scan_result = self._run_single_eps(eps, z_T=self.Z_T_STANDARD)
                results["standard_scan"]["scan"].append(scan_result)
                status_icon = "SUCCESS" if scan_result.get("success") else "WARNING"
                print_status(
                    f"    100*theta_s = {scan_result.get('theta_s_100', 'N/A')} "
                    f"(r_s = {scan_result.get('r_s_Mpc', 'N/A')} Mpc)",
                    status_icon
                )

            # --- Unscreened limit scan (z_T -> infinity, no early-universe suppression) ---
            print_status(f"  === Unscreened Limit Scan (z_T = {self.Z_T_UNSCREENED:.0e}) ===", "TITLE")
            for eps in self.EPSILON_T_VALUES:
                print_status(f"  Running EdS + tep_mode, z_T={self.Z_T_UNSCREENED:.0e}, epsilon_T = {eps:.2f}...", "PROCESS")
                scan_result = self._run_single_eps(eps, z_T=self.Z_T_UNSCREENED)
                results["unscreened_scan"]["scan"].append(scan_result)
                status_icon = "SUCCESS" if scan_result.get("success") else "WARNING"
                print_status(
                    f"    100*theta_s = {scan_result.get('theta_s_100', 'N/A')} "
                    f"(r_s = {scan_result.get('r_s_Mpc', 'N/A')} Mpc)",
                    status_icon
                )

            # Generate figure if matplotlib available
            self._generate_figure(results["standard_scan"]["scan"], results["unscreened_scan"]["scan"])

            results["status"] = "SUCCESS"

            output_file = self.results_dir / "04b_jordan_frame_scan.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print_status(f"  ✓ Saved scan results to {output_file}", "SUCCESS")

        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise

        return results

    def _run_single_eps(self, epsilon_T: float, z_T: float = 5.0) -> dict:
        """Run hi_class for a single epsilon_T in EdS + tep_mode."""
        z_label = "inf" if z_T > 1e5 else f"{z_T:.0f}"
        root_stem = f"jordan_z{z_label}_eps{epsilon_T:.2f}"
        ini_path = self.results_dir / f"{root_stem}.ini"

        # Clean stale outputs
        self._clean_outputs(root_stem)

        # Write ini: EdS matter-only, no Lambda, native TEP
        content = f"""
output = tCl
l_max_scalars = 2500
write background = yes
# Einstein-de Sitter: matter-only, no Dark Energy
H0 = 67.36
omega_b = 0.022383
omega_cdm = 0.120011
Omega_Lambda = 0.0
Omega_k = 0.0
tau_reio = 0.0543
ln10^{{10}}A_s = 3.0448
n_s = 0.96605
YHe = 0.2454
root = {root_stem}_

# Native TEP background-only Hubble modification
tep_mode = yes
epsilon_T = {epsilon_T}
z_T = {z_T}
n_T = 2.0
"""
        with open(ini_path, 'w') as f:
            f.write(content)

        # Run hi_class
        try:
            result = subprocess.run(
                [str(self.hi_class_bin), ini_path.name],
                cwd=ini_path.parent,
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                return {
                    "epsilon_T": epsilon_T,
                    "success": False,
                    "error": f"hi_class exit code {result.returncode}: {result.stderr[:500]}"
                }
        except subprocess.TimeoutExpired:
            return {
                "epsilon_T": epsilon_T,
                "success": False,
                "error": "hi_class timeout (300s)"
            }

        # Extract r_s and theta_s from background table
        try:
            bg_file = self._latest_output(root_stem, "background")
            import numpy as np
            bg = np.loadtxt(bg_file)
            # Columns: 0:z 1:propertime 2:conftime 3:H 4:comov.dist ...
            # Find row closest to recombination z ~ 1089
            z_rec = 1089.0
            idx = int(np.argmin(np.abs(bg[:, 0] - z_rec)))
            r_s = float(bg[idx, 7])   # comoving sound horizon
            D_c = float(bg[idx, 4])   # comoving distance
            theta_s = r_s / D_c
            return {
                "epsilon_T": epsilon_T,
                "success": True,
                "r_s_Mpc": round(r_s, 4),
                "D_comov_Mpc": round(D_c, 4),
                "theta_s": round(theta_s, 6),
                "theta_s_100": round(theta_s * 100, 4)
            }
        except Exception as e:
            return {
                "epsilon_T": epsilon_T,
                "success": False,
                "error": f"Background parse failed: {str(e)[:500]}"
            }

    def _clean_outputs(self, root_stem):
        """Remove stale hi_class outputs for a given root."""
        for f in self.results_dir.glob(f"{root_stem}_*"):
            try:
                f.unlink()
            except OSError:
                pass

    def _latest_output(self, root_stem, kind):
        """Return highest-numbered hi_class output file for a root."""
        import numpy as np
        candidates = sorted(self.results_dir.glob(f"{root_stem}_*_{kind}.dat"))
        if not candidates:
            raise FileNotFoundError(
                f"No hi_class '{kind}' output found for root '{root_stem}'"
            )

        def _suffix(p):
            try:
                return int(p.stem.split("_")[-2])
            except (ValueError, IndexError):
                return -1
        return max(candidates, key=_suffix)

    def _generate_figure(self, standard_scan, unscreened_scan):
        """Generate figure 5: theta_s vs epsilon_T for both standard and unscreened scans."""
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            print_status("  matplotlib not available; figure skipped", "INFO")
            return

        # Extract standard scan data
        std_eps = []
        std_theta = []
        for r in standard_scan:
            if r.get("success"):
                std_eps.append(r["epsilon_T"])
                std_theta.append(r["theta_s_100"])

        # Extract unscreened scan data
        unscr_eps = []
        unscr_theta = []
        for r in unscreened_scan:
            if r.get("success"):
                unscr_eps.append(r["epsilon_T"])
                unscr_theta.append(r["theta_s_100"])

        if len(std_eps) < 2 and len(unscr_eps) < 2:
            print_status("  Insufficient successful runs for figure", "WARNING")
            return

        std_eps = np.array(std_eps)
        std_theta = np.array(std_theta)
        unscr_eps = np.array(unscr_eps)
        unscr_theta = np.array(unscr_theta)

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

        # --- Panel 1: Standard scan (z_T = 5) ---
        if len(std_eps) >= 2:
            ax1.plot(std_eps, std_theta, 'ko-', markersize=6, linewidth=1.5,
                     label=r'Standard ($z_T=5$)')
            ax1.axhline(1.0411, color='C0', linestyle='--', linewidth=1.5,
                        label=r'Planck: $100\,\theta_s = 1.0411$')
            ax1.set_xlabel(r'$\epsilon_T$')
            ax1.set_ylabel(r'$100\,\theta_s$')
            ax1.set_title(r'Standard TEP ($z_T=5$): Early-Universe Suppression Active')
            ax1.legend(loc='upper left', fontsize=8)
            ax1.set_xlim(left=0)

        # --- Panel 2: Unscreened limit scan ---
        if len(unscr_eps) >= 2:
            ax2.plot(unscr_eps, unscr_theta, 'rs-', markersize=6, linewidth=1.5,
                     label=r'Unscreened ($z_T \to \infty$)')
            ax2.axhline(1.0411, color='C0', linestyle='--', linewidth=1.5,
                        label=r'Planck: $100\,\theta_s = 1.0411$')
            # Highlight recovery point
            if len(unscr_theta) > 0:
                recovery_idx = np.argmin(np.abs(unscr_theta - 1.0411))
                recovery_eps = unscr_eps[recovery_idx]
                recovery_theta = unscr_theta[recovery_idx]
                ax2.plot(recovery_eps, recovery_theta, 'g*', markersize=14,
                         label=rf'Recovery: $\epsilon_T \approx {recovery_eps:.2f}$')
            ax2.set_xlabel(r'$\epsilon_T$')
            ax2.set_ylabel(r'$100\,\theta_s$')
            ax2.set_title(r'Unscreened Limit ($z_T \to \infty$): No Early-Universe Protection')
            ax2.legend(loc='upper right', fontsize=8)
            ax2.set_xlim(left=0)

        fig.suptitle('Jordan-Frame EdS + TEP: Two Regimes', fontsize=12)
        fig.tight_layout()

        fig_path = self.figures_dir / "figure_5_jordan_theta_s.png"
        fig.savefig(fig_path, dpi=150)
        plt.close(fig)
        print_status(f"  ✓ Saved figure to {fig_path}", "SUCCESS")


if __name__ == "__main__":
    step = Step04BJordanFrame()
    step.run()
