#!/usr/bin/env python3
"""
Step 00: Environment Setup and Dependency Check
===============================================
Verifies all required dependencies for hi_class/EFT analysis pipeline.

Outputs:
    - logs/step_00_setup.log
    - data/interim/step_00_dependency_status.json
"""

import sys
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


class Step00Setup:
    """Step 00: Environment setup and dependency verification."""
    
    STEP_NAME = "00_setup"
    STEP_DESCRIPTION = "Environment Setup and Dependency Check"
    
    REQUIRED_PACKAGES = [
        "numpy",
        "scipy", 
        "pandas",
        "matplotlib",
        "cobaya",
        "getdist",
        "pyyaml"
    ]
    
    REQUIRED_SYSTEM_DEPS = [
        ("gcc", "GCC compiler"),
        ("make", "Make build system"),
        ("git", "Git version control")
    ]
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.data_dir = self.root_dir / "data" / "interim"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        log_file = self.log_dir / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
        
    def run(self) -> dict:
        """Execute the setup step."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status(f"Started at: {datetime.now().isoformat()}", "INFO")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "python_packages": {},
            "system_dependencies": {},
            "directories_created": [],
            "status": "RUNNING"
        }
        
        try:
            # Check requirements.txt exists
            print_status("Checking requirements.txt...", "PROCESS")
            req_file = self.root_dir / "requirements.txt"
            if req_file.exists():
                with open(req_file) as f:
                    num_pkgs = sum(1 for line in f if line.strip() and not line.startswith('#'))
                print_status(f"  ✓ requirements.txt found ({num_pkgs} packages)")
            else:
                print_status(f"  ✗ requirements.txt NOT FOUND", "WARNING")
            
            # Check Python packages
            print_status("Checking Python packages...", "PROCESS")
            print_status("  (Missing packages will be installed by Step 00b from requirements.txt)")
            
            for pkg in self.REQUIRED_PACKAGES:
                status = self._check_python_package(pkg)
                results["python_packages"][pkg] = status
                if status["available"]:
                    print_status(f"  ✓ {pkg:15s} {status['version']}", "SUCCESS")
                else:
                    print_status(f"  ⚠ {pkg:15s} NOT FOUND (will install in step 00b)", "WARNING")
            
            # Check system dependencies
            print_status("Checking system dependencies...", "PROCESS")
            for cmd, desc in self.REQUIRED_SYSTEM_DEPS:
                status = self._check_system_dep(cmd, desc)
                results["system_dependencies"][cmd] = status
                if status["available"]:
                    print_status(f"  ✓ {cmd:10s} ({desc})", "SUCCESS")
                else:
                    print_status(f"  ✗ {cmd:10s} ({desc}) NOT FOUND", "WARNING")
            
            # Check M4 Pro optimizations
            print_status("Checking M4 Pro optimization status...", "PROCESS")
            import os
            import platform
            
            # Check threading environment
            omp_threads = os.environ.get('OMP_NUM_THREADS', 'NOT SET')
            veclib_threads = os.environ.get('VECLIB_MAXIMUM_THREADS', 'NOT SET')
            
            # Detect Apple Silicon
            is_apple_silicon = platform.system() == 'Darwin' and platform.machine() == 'arm64'
            
            # Check MPI
            mpi_check = subprocess.run(["which", "mpirun"], capture_output=True)
            mpi_available = mpi_check.returncode == 0
            
            print_status(f"  Platform: {platform.system()} {platform.machine()}")
            if is_apple_silicon:
                print_status(f"  ✓ Apple Silicon detected (M4 Pro optimized)", "SUCCESS")
            print_status(f"  OMP_NUM_THREADS: {omp_threads}")
            print_status(f"  VECLIB_MAXIMUM_THREADS: {veclib_threads}")
            
            if mpi_available:
                print_status(f"  ✓ OpenMPI available (parallel chains enabled)", "SUCCESS")
                results["mpi_available"] = True
            else:
                print_status(f"  ○ OpenMPI not yet installed (will auto-install in step 00b)", "INFO")
                results["mpi_available"] = False
            
            # Create directory structure
            print_status("Creating directory structure...", "PROCESS")
            dirs_to_create = [
                "data/interim",
                "data/processed",
                "data/hi_class",
                "data/cobaya",
                "results/mcmc_chains",
                "results/figures",
                "logs"
            ]
            for dir_path in dirs_to_create:
                full_path = self.root_dir / dir_path
                full_path.mkdir(parents=True, exist_ok=True)
                results["directories_created"].append(str(full_path))
                print_status(f"  ✓ {dir_path}", "SUCCESS")
            
            # Check for hi_class
            print_status("Checking hi_class availability...", "PROCESS")
            hi_class_status = self._check_hi_class()
            results["hi_class"] = hi_class_status
            if hi_class_status["available"]:
                print_status(f"  ✓ hi_class found at {hi_class_status['path']}", "SUCCESS")
            else:
                print_status(f"  ✗ hi_class not found. Install from https://github.com/lesgourg/class_public", "WARNING")
                print_status(f"    (Pipeline will create module code but cannot run without hi_class)", "INFO")
            
            results["status"] = "SUCCESS"
            
            # Save results
            output_file = self.data_dir / "step_00_dependency_status.json"
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2)
            print_status(f"Results saved to {output_file}", "INFO")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        print_status(f"STEP {self.STEP_NAME} COMPLETED", "SUCCESS")
        return results
    
    def _check_python_package(self, package: str) -> dict:
        """Check if a Python package is available."""
        try:
            if package == "pyyaml":
                import yaml
                return {"available": True, "version": yaml.__version__}
            else:
                mod = __import__(package)
                version = getattr(mod, "__version__", "unknown")
                return {"available": True, "version": version}
        except ImportError:
            return {"available": False, "version": None}
    
    def _check_system_dep(self, command: str, description: str) -> dict:
        """Check if a system command is available."""
        try:
            result = subprocess.run(
                [command, "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return {"available": True, "description": description}
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"available": False, "description": description}
    
    def _check_hi_class(self) -> dict:
        """Check if hi_class is installed and importable."""
        # First check if Python module can be imported
        try:
            import classy
            import inspect
            classy_path = inspect.getfile(classy)
            return {"available": True, "path": str(Path(classy_path).parent.parent)}
        except ImportError:
            pass
        
        # Check common installation paths
        hi_class_paths = [
            self.root_dir / "external" / "hi_class",
            self.root_dir / "external" / "hi_class" / "hi_class",  # Nested from install
            self.root_dir / "hi_class",
            self.root_dir / "class",
            Path.home() / "hi_class",
            Path.home() / "class"
        ]
        
        for path in hi_class_paths:
            # Check for source directory or compiled python module
            if (path / "source" / "models").exists() or (path / "python" / "classy.pyx").exists():
                return {"available": True, "path": str(path)}
        
        return {"available": False, "path": None}


if __name__ == "__main__":
    step = Step00Setup()
    step.run()
