#!/usr/bin/env python3
"""
TEP-HC Analysis Pipeline Master Script
========================================
Orchestrates the full hi_class/EFT cosmology analysis pipeline for Paper 18.

This script executes the scientific workflow in strict sequential order:
0. Environment setup and dependency check
1. Install dependencies and download data (Cobaya, Planck likelihoods, hi_class + TEP patch)
2. Background evolution computation
3. Bellini-Sawicki alpha functions validation
4. CMB power spectra generation
5. Jordan-frame no-Dark-Energy reconstruction
6. Cobaya MCMC configuration
7. MCMC execution
8. Posterior analysis
9. Results synthesis

Usage:
    python scripts/run_all.py
    python scripts/run_all.py --start-step 02
    python scripts/run_all.py --stop-step 05
    python scripts/run_all.py --skip-steps 06,07

Author: Matthew Lukin Smawfield
Date: April 2026
Version: v0.1-Cambridge
License: CC-BY-4.0
"""

import sys
import time
import json
import argparse
import os
import subprocess
from pathlib import Path
from datetime import datetime

# M4 Pro Performance Optimization: Set environment variables
# Auto-detect Apple Silicon and configure optimal threading
if sys.platform == 'darwin':
    try:
        # Detect core count
        ncpu = int(subprocess.run(['sysctl', '-n', 'hw.ncpu'], 
                                 capture_output=True, text=True).stdout.strip())
        if ncpu >= 10:
            # M4 Pro or similar: Use performance cores for CLASS, all cores for NumPy
            p_cores = min(10, ncpu - 4)  # Estimate P-cores
            os.environ.setdefault('OMP_NUM_THREADS', str(p_cores))
            os.environ.setdefault('VECLIB_MAXIMUM_THREADS', str(ncpu))
            os.environ.setdefault('OPENBLAS_NUM_THREADS', str(ncpu))
            os.environ.setdefault('NUMEXPR_NUM_THREADS', str(ncpu))
    except Exception:
        pass

# Set Cobaya packages path - use existing if available
PROJECT_ROOT = Path(__file__).resolve().parents[1]
# Check for external packages path from environment variable or default location
EXTERNAL_PACKAGES = os.environ.get("COBAYA_EXTERNAL_PACKAGES", "")
EXISTING_PACKAGES_PATH = Path(EXTERNAL_PACKAGES) if EXTERNAL_PACKAGES else PROJECT_ROOT.parent.parent / "TVP" / "TVP" / "data" / "external" / "cosmology_likelihoods"
LOCAL_PACKAGES_PATH = PROJECT_ROOT / "data" / "external" / "cobaya_packages"

if EXISTING_PACKAGES_PATH.exists() and (EXISTING_PACKAGES_PATH / "data" / "planck_2018").exists():
    os.environ["COBAYA_PACKAGES_PATH"] = str(EXISTING_PACKAGES_PATH)
else:
    os.environ["COBAYA_PACKAGES_PATH"] = str(LOCAL_PACKAGES_PATH)

# Detect MPI availability - only disable if mpirun not available
_MPI_AVAILABLE = subprocess.run(["which", "mpirun"], capture_output=True).returncode == 0
if not _MPI_AVAILABLE:
    os.environ["COBAYA_NOMPI"] = "1"

# Ensure project root is in path
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status, print_table

# Import all steps
from scripts.steps.step_00_setup import Step00Setup
from scripts.steps.step_00b_install import Step00bInstall
from scripts.steps.step_02_background import Step02Background
from scripts.steps.step_03_alphas import Step03Alphas
from scripts.steps.step_04_cmb import Step04CMB
from scripts.steps.step_04b_jordan_frame import Step04BJordanFrame
from scripts.steps.step_05_cobaya import Step05Cobaya
from scripts.steps.step_06_mcmc import Step06MCMC
from scripts.steps.step_07_posteriors import Step07Posteriors
from scripts.steps.step_08_synthesis import Step08Synthesis

# Step registry
STEP_REGISTRY = {
    0: ("00_setup", Step00Setup, "Environment Setup and Dependency Check"),
    1: ("00b_install", Step00bInstall, "Install Dependencies and Download Data"),
    2: ("02_background", Step02Background, "Background Evolution Analysis"),
    3: ("03_alphas", Step03Alphas, "Alpha Functions Validation"),
    4: ("04_cmb", Step04CMB, "CMB Spectra Generation"),
    5: ("04b_jordan_frame", Step04BJordanFrame, "Jordan-Frame No-Dark-Energy Reconstruction"),
    6: ("05_cobaya", Step05Cobaya, "Cobaya MCMC Setup"),
    7: ("06_mcmc", Step06MCMC, "MCMC Execution"),
    8: ("07_posteriors", Step07Posteriors, "Posterior Analysis"),
    9: ("08_synthesis", Step08Synthesis, "Results Synthesis"),
}


def run_pipeline(args: argparse.Namespace) -> dict:
    """
    Execute the full analysis pipeline.
    
    Args:
        args: Command-line arguments
        
    Returns:
        Dictionary with pipeline execution results
    """
    # Setup global logger
    logs_dir = PROJECT_ROOT / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    pipeline_logger = TEPLogger(
        "pipeline_master",
        log_file_path=logs_dir / "pipeline_master.log"
    )
    set_step_logger(pipeline_logger)
    
    print_status("=" * 70, "TITLE")
    print_status("TEP-HC ANALYSIS PIPELINE", "TITLE")
    print_status("Paper 18: hi_class/EFT Cosmology (Cambridge)", "TITLE")
    print_status("=" * 70, "TITLE")
    print_status(f"Project Root: {PROJECT_ROOT}", "INFO")
    print_status(f"Started: {datetime.now().isoformat()}", "INFO")
    print_status(f"Python: {sys.version.split()[0]}", "INFO")
    print_status("")
    
    # Determine step range
    start_step = args.start_step if args.start_step is not None else 0
    stop_step = args.stop_step if args.stop_step is not None else 9
    skip_steps = set(args.skip_steps) if args.skip_steps else set()
    
    print_status(f"Pipeline Configuration:", "TITLE")
    print_status(f"  Start step: {start_step}", "INFO")
    print_status(f"  Stop step: {stop_step}", "INFO")
    if skip_steps:
        print_status(f"  Skip steps: {sorted(skip_steps)}", "INFO")
    print_status("")
    
    # Execution tracking
    results = {
        "pipeline_start": datetime.now().isoformat(),
        "steps_completed": [],
        "steps_failed": [],
        "steps_skipped": [],
        "execution_times": {},
        "status": "RUNNING"
    }
    
    total_start_time = time.time()
    
    # Execute steps
    for step_num in range(start_step, stop_step + 1):
        if step_num in skip_steps:
            print_status(f">>> STEP {step_num:02d}: SKIPPED", "WARNING")
            results["steps_skipped"].append(step_num)
            continue
        
        if step_num not in STEP_REGISTRY:
            print_status(f">>> STEP {step_num:02d}: NOT FOUND", "ERROR")
            results["steps_failed"].append(step_num)
            continue
        
        step_id, StepClass, step_desc = STEP_REGISTRY[step_num]
        
        print_status(f">>> STEP {step_num:02d}: {step_desc.upper()}", "TITLE")
        print_status("")
        
        step_start_time = time.time()
        
        try:
            # Instantiate and run step
            step_instance = StepClass()
            
            # Pass special arguments to step 01 (00b_install)
            if step_num == 1:
                kwargs = {}
                if hasattr(args, 'force_install') and args.force_install:
                    kwargs['force_install'] = True
                if hasattr(args, 'skip_planck') and args.skip_planck:
                    kwargs['skip_planck'] = True
                step_result = step_instance.run(**kwargs)
            else:
                step_result = step_instance.run()
            
            # Record success
            results["steps_completed"].append(step_num)
            step_time = time.time() - step_start_time
            results["execution_times"][step_id] = round(step_time, 2)
            
            print_status(f"\nStep {step_num:02d} completed in {step_time:.1f}s", "SUCCESS")
            
        except Exception as e:
            # Record failure
            results["steps_failed"].append(step_num)
            step_time = time.time() - step_start_time
            results["execution_times"][step_id] = round(step_time, 2)
            
            print_status(f"\nStep {step_num:02d} failed after {step_time:.1f}s", "ERROR")
            print_status(f"Error: {e}", "ERROR")
            
            if not args.continue_on_error:
                print_status("\nPipeline halted. Use --continue-on-error to proceed.", "WARNING")
                results["status"] = "FAILED"
                break
        
        print_status("")
        print_status("-" * 70, "TITLE")
        print_status("")
    
    # Pipeline summary
    total_time = time.time() - total_start_time
    results["pipeline_end"] = datetime.now().isoformat()
    results["total_time_seconds"] = round(total_time, 2)
    
    print_status("=" * 70, "TITLE")
    print_status("PIPELINE EXECUTION SUMMARY", "TITLE")
    print_status("=" * 70, "TITLE")
    print_status("")
    
    # Summary table
    print_table(
        ["Metric", "Count", "Time (s)"],
        [
            ["Steps Completed", len(results["steps_completed"]), "-"],
            ["Steps Skipped", len(results["steps_skipped"]), "-"],
            ["Steps Failed", len(results["steps_failed"]), "-"],
            ["Total Time", "-", f"{total_time:.1f}"]
        ],
        title="Execution Statistics"
    )
    
    print_status("")
    
    # Step timing breakdown
    if results["execution_times"]:
        print_status("Step Timing Breakdown:", "TITLE")
        for step_id, elapsed in sorted(results["execution_times"].items()):
            print_status(f"  {step_id:20s}: {elapsed:6.1f}s", "INFO")
    
    print_status("")
    
    # Final status
    if results["steps_failed"]:
        results["status"] = "COMPLETED_WITH_ERRORS" if args.continue_on_error else "FAILED"
        print_status(f"Status: {results['status']}", "WARNING")
    else:
        results["status"] = "SUCCESS"
        print_status("Status: ALL STEPS COMPLETED SUCCESSFULLY", "SUCCESS")
    
    print_status("")
    print_status(f"Results directory: {PROJECT_ROOT / 'results'}", "INFO")
    print_status(f"Logs directory: {PROJECT_ROOT / 'logs'}", "INFO")
    print_status("")
    print_status("=" * 70, "TITLE")
    
    # Save pipeline results
    results_file = PROJECT_ROOT / "results" / "pipeline_results.json"
    results_file.parent.mkdir(parents=True, exist_ok=True)
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    print_status(f"Pipeline results saved to: {results_file}", "INFO")
    
    return results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="TEP-HC Analysis Pipeline - hi_class/EFT Cosmology",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Pipeline Steps:
  00 - Environment setup and dependency check
  01 - Install dependencies and download data (hi_class + native TEP patch)
  02 - Background evolution analysis
  03 - Bellini-Sawicki alpha functions validation
  04 - CMB power spectra generation
  05 - Jordan-frame no-Dark-Energy reconstruction
  06 - Cobaya MCMC configuration
  07 - MCMC execution
  08 - Posterior analysis
  09 - Results synthesis

Examples:
  python scripts/run_all.py                  # Run full pipeline
  python scripts/run_all.py --start-step 1   # Start from installation
  python scripts/run_all.py --stop-step 5    # Run through step 05
  python scripts/run_all.py --skip-steps 7,8  # Skip MCMC (7) and posteriors (8)
  python scripts/run_all.py --skip-steps 8,9  # Skip posteriors (8) and synthesis (9)
        """
    )
    
    parser.add_argument(
        "--start-step",
        type=int,
        choices=range(0, 10),
        help="First step to execute (0-9)"
    )
    
    parser.add_argument(
        "--stop-step",
        type=int,
        choices=range(0, 10),
        help="Last step to execute (0-9)"
    )
    
    parser.add_argument(
        "--skip-steps",
        type=lambda s: [int(x) for x in s.split(",")],
        help="Comma-separated list of steps to skip"
    )
    
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Continue pipeline even if a step fails"
    )
    
    parser.add_argument(
        "--list-steps",
        action="store_true",
        help="List all pipeline steps and exit"
    )
    
    parser.add_argument(
        "--force-install",
        action="store_true",
        help="Force re-installation of dependencies and data (Step 01)"
    )
    
    parser.add_argument(
        "--skip-planck",
        action="store_true",
        help="Skip Planck likelihood download (for quick testing)"
    )
    
    args = parser.parse_args()
    
    # List steps if requested
    if args.list_steps:
        print("TEP-HC Pipeline Steps:")
        print("=" * 50)
        for num, (step_id, _, desc) in STEP_REGISTRY.items():
            print(f"  {num:02d}. {step_id:15s} - {desc}")
        return
    
    # Run pipeline
    try:
        results = run_pipeline(args)
        
        # Exit with appropriate code
        if results["status"] == "SUCCESS":
            sys.exit(0)
        elif results["status"] == "COMPLETED_WITH_ERRORS":
            sys.exit(1)
        else:
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nPipeline crashed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()
