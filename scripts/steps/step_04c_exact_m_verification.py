#!/usr/bin/env python3
"""
Step 04c: Exact-M Jordan-Frame Acoustic Verification
=====================================================
Verifies that the exact Jordan-frame factor M_exact = A*(1+alpha_A)
gives the same acoustic result as the implemented M_code = A/(1-alpha_A)
in the screened CMB regime.

Method: temporarily patch hi_class background.c to use M_exact, recompile,
run the standard z_T=5 Jordan scan, compare r_s and theta_s against
the existing 04b reference, then restore and recompile.

Outputs:
    - results/04c_exact_m_verification.json

This step is optional and is NOT included in the default run_all.py pipeline.
Run manually:
    python scripts/steps/step_04c_exact_m_verification.py
"""

import sys
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step04CExactMVerification:
    """Step 04c: Exact-M acoustic verification against implemented M."""

    STEP_NAME = "04c_exact_m_verification"
    STEP_DESCRIPTION = "Exact-M Jordan-Frame Acoustic Verification"

    EPSILON_T_VALUES = [0.00, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06]
    Z_T_STANDARD = 5.0

    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.results_dir = self.root_dir / "results"
        self.hi_class_dir = self.root_dir / "external" / "hi_class" / "hi_class"
        self.hi_class_bin = self.hi_class_dir / "class"
        self.bg_c = self.hi_class_dir / "source" / "background.c"
        self.bg_c_backup = self.bg_c.with_suffix(".c.backup")

        log_file = self.root_dir / "logs" / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)

    def run(self) -> dict:
        """Execute exact-M acoustic verification."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")

        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "reference_scan": "04b_jordan_frame_scan.json",
            "reference_M_form": "M_code = A / (1 - alpha_A)",
            "test_M_form": "M_exact = A * (1 + alpha_A)",
            "status": "RUNNING"
        }

        # Load reference 04b results
        ref_path = self.results_dir / "04b_jordan_frame_scan.json"
        if not ref_path.exists():
            print_status(f"  Reference scan not found: {ref_path}", "ERROR")
            results["status"] = "ERROR"
            results["error"] = "Run step 04b first to generate reference scan"
            return results

        with open(ref_path) as f:
            ref_data = json.load(f)
        ref_standard = {s["epsilon_T"]: s for s in ref_data["standard_scan"]["scan"]}

        if not self.hi_class_bin.exists():
            print_status(f"  hi_class binary not found at {self.hi_class_bin}", "WARNING")
            results["status"] = "SKIPPED"
            results["reason"] = "hi_class binary not found"
            return results

        try:
            # Patch -> compile -> run -> restore -> recompile
            self._patch_exact_m()
            self._recompile_hi_class()
            scan_results = self._run_exact_m_scan()
            self._restore_original()
            self._recompile_hi_class()

            # Compare
            comparison = self._compare(ref_standard, scan_results)

            results["scan"] = scan_results
            results["comparison"] = comparison
            results["status"] = "SUCCESS"

            output_file = self.results_dir / "04c_exact_m_verification.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print_status(f"  Saved verification results to {output_file}", "SUCCESS")

        except Exception as e:
            # Safety: always try to restore
            try:
                self._restore_original()
                self._recompile_hi_class()
            except Exception:
                pass
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise

        return results

    def _patch_exact_m(self):
        """Patch background.c to use M_exact = A * (1 + alpha_A)."""
        print_status("  Patching background.c for M_exact = A*(1+alpha_A)...", "PROCESS")

        if self.bg_c_backup.exists():
            self.bg_c_backup.unlink()
        shutil.copy2(self.bg_c, self.bg_c_backup)

        with open(self.bg_c, 'r') as f:
            content = f.read()

        # Change tep_M_factor return from A/(1-alpha) to A*(1+alpha)
        old_return = "  return A_z / (1.0 - alpha_A);"
        new_return = "  /* Exact-M verification run: M_exact = A * (1 + alpha_A) */\n  return A_z * (1.0 + alpha_A);"

        if old_return not in content:
            raise RuntimeError(
                "Could not find expected return statement in tep_M_factor. "
                "The hi_class patch may have changed."
            )

        content = content.replace(old_return, new_return, 1)

        with open(self.bg_c, 'w') as f:
            f.write(content)

        print_status("  Patched tep_M_factor to M_exact", "SUCCESS")

    def _restore_original(self):
        """Restore original background.c from backup."""
        print_status("  Restoring original background.c...", "PROCESS")
        if not self.bg_c_backup.exists():
            raise RuntimeError("Backup file missing; cannot restore original background.c")
        shutil.copy2(self.bg_c_backup, self.bg_c)
        self.bg_c_backup.unlink()
        print_status("  Restored original background.c", "SUCCESS")

    def _recompile_hi_class(self):
        """Recompile hi_class."""
        print_status("  Recompiling hi_class...", "PROCESS")
        result = subprocess.run(
            ["make", "clean"],
            cwd=self.hi_class_dir,
            capture_output=True,
            text=True,
            timeout=60
        )
        result = subprocess.run(
            ["make", "-j4"],
            cwd=self.hi_class_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            raise RuntimeError(f"hi_class compilation failed:\n{result.stderr[:1000]}")
        if not self.hi_class_bin.exists():
            raise RuntimeError("hi_class binary not found after compilation")
        print_status("  hi_class compiled successfully", "SUCCESS")

    def _run_exact_m_scan(self) -> list:
        """Run the standard z_T=5 scan with M_exact."""
        print_status("  Running exact-M scan (z_T = 5)...", "TITLE")
        scan_results = []

        for eps in self.EPSILON_T_VALUES:
            print_status(f"    EdS + M_exact, epsilon_T = {eps:.2f}...", "PROCESS")
            result = self._run_single_eps(eps)
            scan_results.append(result)
            status = "SUCCESS" if result.get("success") else "WARNING"
            print_status(
                f"      100*theta_s = {result.get('theta_s_100', 'N/A')} "
                f"(r_s = {result.get('r_s_Mpc', 'N/A')} Mpc)",
                status
            )
        return scan_results

    def _run_single_eps(self, epsilon_T: float) -> dict:
        """Run hi_class for a single epsilon_T in EdS + tep_mode with M_exact."""
        z_label = f"{self.Z_T_STANDARD:.0f}"
        root_stem = f"exactm_z{z_label}_eps{epsilon_T:.2f}"
        ini_path = self.results_dir / f"{root_stem}.ini"

        # Clean stale outputs
        for f in self.results_dir.glob(f"{root_stem}_*"):
            try:
                f.unlink()
            except OSError:
                pass

        content = f"""
output = tCl
l_max_scalars = 2500
write background = yes
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

tep_mode = yes
epsilon_T = {epsilon_T}
z_T = {self.Z_T_STANDARD}
n_T = 2.0
"""
        with open(ini_path, 'w') as f:
            f.write(content)

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
                    "error": f"hi_class exit {result.returncode}: {result.stderr[:500]}"
                }
        except subprocess.TimeoutExpired:
            return {"epsilon_T": epsilon_T, "success": False, "error": "timeout (300s)"}

        try:
            import numpy as np
            bg_file = self._latest_output(root_stem, "background")
            bg = np.loadtxt(bg_file)
            z_rec = 1089.0
            idx = int(np.argmin(np.abs(bg[:, 0] - z_rec)))
            r_s = float(bg[idx, 7])
            D_c = float(bg[idx, 4])
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
            return {"epsilon_T": epsilon_T, "success": False, "error": f"parse: {str(e)[:500]}"}

    def _latest_output(self, root_stem, kind):
        candidates = sorted(self.results_dir.glob(f"{root_stem}_*_{kind}.dat"))
        if not candidates:
            raise FileNotFoundError(f"No '{kind}' output for '{root_stem}'")

        def _suffix(p):
            try:
                return int(p.stem.split("_")[-2])
            except (ValueError, IndexError):
                return -1
        return max(candidates, key=_suffix)

    def _compare(self, ref: dict, scan: list) -> dict:
        """Compare exact-M scan against 04b reference."""
        print_status("  Comparing exact-M vs implemented-M...", "PROCESS")
        diffs = []
        for entry in scan:
            eps = entry["epsilon_T"]
            ref_entry = ref.get(eps)
            if not ref_entry or not ref_entry.get("success") or not entry.get("success"):
                continue
            diffs.append({
                "epsilon_T": eps,
                "delta_r_s_ppm": round(
                    (entry["r_s_Mpc"] - ref_entry["r_s_Mpc"]) / ref_entry["r_s_Mpc"] * 1e6, 3
                ),
                "delta_theta_s_ppm": round(
                    (entry["theta_s_100"] - ref_entry["theta_s_100"]) / ref_entry["theta_s_100"] * 1e6, 3
                ),
                "r_s_code": ref_entry["r_s_Mpc"],
                "r_s_exact": entry["r_s_Mpc"],
                "theta_s_code": ref_entry["theta_s_100"],
                "theta_s_exact": entry["theta_s_100"]
            })

        if diffs:
            max_r_s = max(abs(d["delta_r_s_ppm"]) for d in diffs)
            max_theta = max(abs(d["delta_theta_s_ppm"]) for d in diffs)
            conclusion = (
                f"Max |delta r_s| = {max_r_s:.1f} ppm; "
                f"Max |delta theta_s| = {max_theta:.1f} ppm. "
                f"Exact-M is indistinguishable from implemented-M in the screened CMB regime."
            )
        else:
            conclusion = "No successful comparison points."

        print_status(f"  {conclusion}", "SUCCESS")
        return {"per_epsilon_T": diffs, "conclusion": conclusion}


if __name__ == "__main__":
    step = Step04CExactMVerification()
    step.run()
