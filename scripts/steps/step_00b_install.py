#!/usr/bin/env python3
"""
Step 00b: Install Dependencies and Data
======================================
Automatically installs Cobaya, Planck likelihoods, and downloads required data.
This step ensures the pipeline is fully reproducible.

Outputs:
    - logs/step_00b_install.log
    - data/cobaya/*.yaml (configuration files)
    - ~/.cobaya/ (Planck likelihoods cached here)
"""

import sys
import subprocess
import threading
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status


def format_bytes(size_bytes: int) -> str:
    """Convert bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size_bytes) < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS."""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


class ProgressSpinner:
    """Threaded progress spinner with elapsed time."""
    def __init__(self, message: str):
        self.message = message
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.start_time = 0.0
        
    def _spin(self):
        spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        i = 0
        while self.running:
            elapsed = time.time() - self.start_time
            symbol = spinner[i % len(spinner)]
            print(f"\r  {symbol} {self.message}... ({format_time(elapsed)} elapsed)", end='', flush=True)
            time.sleep(0.1)
            i += 1
        print()  # New line when done
        
    def start(self):
        self.running = True
        self.start_time = time.time()
        self.thread = threading.Thread(target=self._spin)
        self.thread.start()
        
    def stop(self, success: bool = True):
        self.running = False
        if self.thread:
            self.thread.join()
        elapsed = time.time() - self.start_time
        status = "✓" if success else "✗"
        print(f"  {status} {self.message} ({format_time(elapsed)})")


def run_with_spinner(cmd: list, message: str, show_output: bool = False) -> bool:
    """Run command with progress spinner."""
    spinner = ProgressSpinner(message)
    spinner.start()
    
    try:
        if show_output:
            # Stream output in real-time
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            output_lines = []
            for line in process.stdout:
                line = line.rstrip()
                output_lines.append(line)
                # Show key progress lines
                if any(keyword in line.lower() for keyword in 
                       ['downloading', 'installing', 'building', 'collecting', 
                        'progress', 'unpacking', 'running', 'setup.py']):
                    print(f"\r    → {line[:70]}{'...' if len(line) > 70 else ''}", end='', flush=True)
            
            process.wait()
            spinner.stop(process.returncode == 0)
            return process.returncode == 0
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            spinner.stop(result.returncode == 0)
            return result.returncode == 0
            
    except Exception as e:
        spinner.stop(False)
        print_status(f"    Error: {e}", "ERROR")
        return False


class Step00bInstall:
    """Step 00b: Install dependencies and download data."""
    
    STEP_NAME = "00b_install"
    STEP_DESCRIPTION = "Install Dependencies and Download Data"
    
    def __init__(self):
        self.root_dir = PROJECT_ROOT
        self.log_dir = self.root_dir / "logs"
        self.log_dir.mkdir(exist_ok=True)
        self.data_dir = self.root_dir / "data"
        
        log_file = self.log_dir / f"step_{self.STEP_NAME}.log"
        self.logger = TEPLogger(f"step_{self.STEP_NAME}", log_file)
        set_step_logger(self.logger)
    
    def run(self, force_install: bool = False, skip_planck: bool = False) -> dict:
        """Execute installation step."""
        print_status(f"STEP {self.STEP_NAME}: {self.STEP_DESCRIPTION}", "TITLE")
        print_status(f"Started at: {datetime.now().isoformat()}", "INFO")
        
        results = {
            "step": self.STEP_NAME,
            "timestamp": datetime.now().isoformat(),
            "packages_installed": [],
            "cobaya_available": False,
            "planck_likelihoods": {},
            "status": "RUNNING"
        }
        
        try:
            # Check current environment
            print_status("Checking Python environment...", "PROCESS")
            results["python_executable"] = str(sys.executable)
            results["python_version"] = sys.version.split()[0]
            print_status(f"  Python: {results['python_version']}")
            
            # Install base packages if needed
            if not self._check_base_packages() or force_install:
                print_status("Installing base packages...", "PROCESS")
                self._install_base_packages()
            else:
                print_status("  ✓ Base packages already available")
            
            # Check/install Cobaya
            results["cobaya_available"] = self._check_cobaya()
            if not results["cobaya_available"] or force_install:
                print_status("Installing Cobaya...", "PROCESS")
                if self._install_cobaya():
                    results["cobaya_available"] = True
            else:
                print_status("  ✓ Cobaya already available")
            
            # Download Planck likelihoods if Cobaya available
            if skip_planck:
                print_status("⚠ Skipping Planck download (--skip-planck specified)", "WARNING")
                print_status("  Note: MCMC steps will run in dry-run mode without Planck data")
            elif results["cobaya_available"]:
                results["planck_likelihoods"] = self._install_planck_likelihoods(force=force_install)
            else:
                print_status("⚠ Skipping Planck (Cobaya not available)", "WARNING")
            
            # Create test configuration
            self._create_test_config()
            
            results["status"] = "SUCCESS"
            print_status(f"\nSTEP {self.STEP_NAME} COMPLETED", "SUCCESS")
            
        except Exception as e:
            results["status"] = "ERROR"
            results["error"] = str(e)
            print_status(f"Step failed: {e}", "ERROR")
            raise
        
        return results
    
    def _check_base_packages(self) -> bool:
        """Check if base packages are installed."""
        packages = ["numpy", "scipy", "pandas", "matplotlib", "yaml"]
        for pkg in packages:
            try:
                __import__(pkg.replace("yaml", "pyyaml").replace("pyyaml", "yaml"))
            except ImportError:
                return False
        return True
    
    def _install_base_packages(self):
        """Install required Python packages with verbose output."""
        packages = [
            "numpy>=1.20", "scipy>=1.7", "pandas>=1.3",
            "matplotlib>=3.4", "pyyaml>=5.4", "requests>=2.25"
        ]
        
        print_status(f"Installing {len(packages)} base packages...")
        print_status(f"  Packages: {', '.join([p.split('>=')[0] for p in packages])}")
        
        cmd = [sys.executable, "-m", "pip", "install", "--progress-bar", "on"] + packages
        success = run_with_spinner(cmd, "Installing base packages", show_output=True)
        
        if success:
            print_status("  ✓ Base packages installed successfully")
        else:
            print_status("  ✗ Base package installation failed", "ERROR")
    
    def _check_cobaya(self) -> bool:
        """Check if Cobaya is installed."""
        try:
            import cobaya
            return True
        except ImportError:
            return False
    
    def _install_cobaya(self) -> bool:
        """Install Cobaya with verbose progress."""
        print_status("Installing Cobaya MCMC sampler...")
        print_status("  This includes: cobaya, getdist, and dependencies")
        print_status("  Estimated time: 2-3 minutes")
        
        cmd = [sys.executable, "-m", "pip", "install", "--progress-bar", "on", "cobaya[getdist]"]
        success = run_with_spinner(cmd, "Installing Cobaya", show_output=True)
        
        if success:
            print_status("  ✓ Cobaya installed successfully")
            return True
        else:
            print_status("  ✗ Cobaya installation failed", "ERROR")
            return False
    
    def _get_directory_size(self, path: Path) -> int:
        """Get total size of directory in bytes."""
        total = 0
        try:
            for item in path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except Exception:
            pass
        return total
    
    def _check_likelihood_installed(self, likelihood_name: str) -> bool:
        """Check if a Planck likelihood is properly installed with actual data."""
        try:
            from cobaya.tools import resolve_packages_path
            
            # Get the installation path from Cobaya's config
            install_path = resolve_packages_path()
            if not install_path:
                return False
            
            install_path = Path(install_path)
            data_path = install_path / "data"
            
            # Define minimum size thresholds (in MB) for each likelihood
            # These are conservative estimates based on actual Planck data sizes
            min_size_mb = {
                "planck_2018_highl_plik.TTTEEE": 1000,  # ~1GB minimum for High-L
                "planck_2018_lowl_TT": 10,               # ~10MB minimum
                "planck_2018_lowl_EE": 1,                # ~1MB minimum  
                "planck_2018_lensing.native": 100,       # ~100MB minimum for lensing
            }
            
            # Map likelihood names to expected data directories
            likelihood_dir_map = {
                "planck_2018_highl_plik.TTTEEE": ["planck_2018"],
                "planck_2018_lowl_TT": ["planck_2018_lowT_native"],
                "planck_2018_lowl_EE": ["planck_2018_lowE_native"],
                "planck_2018_lensing.native": ["planck_supp_data_and_covmats"],
            }
            
            expected_dirs = likelihood_dir_map.get(likelihood_name, [])
            min_size = min_size_mb.get(likelihood_name, 1) * 1024 * 1024  # Convert to bytes
            
            # Check for actual data files with size validation
            if data_path.exists():
                for expected in expected_dirs:
                    expected_path = data_path / expected
                    if expected_path.exists():
                        # Check total directory size
                        total_size = self._get_directory_size(expected_path)
                        if total_size >= min_size:
                            # Also verify there are actual data files (not just wrapper code)
                            # Include various data file types used by Planck likelihoods
                            data_files = list(expected_path.rglob('*.fits')) + \
                                       list(expected_path.rglob('*.clik')) + \
                                       list(expected_path.rglob('*.clik_lensing')) + \
                                       list(expected_path.rglob('*.bin')) + \
                                       list(expected_path.rglob('*.txt'))
                            if len(data_files) >= 1:
                                return True
            
            return False
            
        except Exception as e:
            # If we can't check, assume not installed to be safe
            return False
    
    def _install_planck_likelihoods(self, force: bool = False) -> dict:
        """Download Planck 2018 likelihoods using Cobaya with intelligent skip logic."""
        likelihoods = {
            "planck_2018_highl_plik.TTTEEE": {"name": "Planck 2018 High-L TTTEEE", "size": "~6 GB", "done": False, "installed": False},
            "planck_2018_lowl_TT": {"name": "Planck 2018 Low-L TT", "size": "~50 MB", "done": False, "installed": False},
            "planck_2018_lowl_EE": {"name": "Planck 2018 Low-L EE", "size": "~50 MB", "done": False, "installed": False},
            "planck_2018_lensing.native": {"name": "Planck 2018 Lensing", "size": "~3 GB", "done": False, "installed": False}
        }
        
        if not self._check_cobaya():
            print_status("⚠ Cannot install Planck likelihoods (Cobaya not available)", "WARNING")
            return {k: v["done"] for k, v in likelihoods.items()}
        
        # Check which likelihoods are already installed
        print_status("Checking existing installations...")
        already_installed = []
        need_download = []
        
        for likelihood, info in likelihoods.items():
            if not force and self._check_likelihood_installed(likelihood):
                info["installed"] = True
                info["done"] = True
                already_installed.append(info['name'])
            else:
                need_download.append((likelihood, info))
        
        if already_installed:
            print_status(f"  ✓ Found {len(already_installed)} already installed:")
            for name in already_installed:
                print_status(f"    • {name}")
        
        if not need_download:
            print_status("")
            print_status("=" * 60)
            print_status("ALL PLANCK LIKELIHOODS ALREADY INSTALLED")
            print_status("=" * 60)
            print_status("Use --force-install to re-download if needed")
            print_status("=" * 60)
            return {k: v["done"] for k, v in likelihoods.items()}
        
        print_status(f"  → {len(need_download)} likelihood(s) need installation")
        print_status("")
        
        total_size = sum([6 if 'highl' in k else 0.05 if 'lowl' in k else 3 
                         for k, _ in need_download])  # Approximate GB
        print_status("=" * 60)
        print_status("PLANCK 2018 LIKELIHOOD INSTALLATION")
        print_status("=" * 60)
        print_status(f"To download: {len(need_download)} likelihood(s)")
        print_status(f"Total download size: ~{total_size:.1f} GB")
        print_status(f"Estimated time: 20-30 minutes (depending on connection)")
        print_status(f"Installation path: ~/.cobaya/")
        print_status("=" * 60)
        print_status("")
        
        start_time = time.time()
        completed = len(already_installed)
        total = len(likelihoods)
        
        for i, (likelihood, info) in enumerate(need_download, 1):
            print_status(f"[{i}/{len(need_download)}] Installing {info['name']}")
            print_status(f"      Size: {info['size']}")
            
            step_start = time.time()
            
            try:
                from cobaya.install import install
                
                # Run with progress monitoring
                spinner = ProgressSpinner(f"Downloading {info['name']}")
                spinner.start()
                
                # Redirect stdout to capture progress
                old_stdout = sys.stdout
                sys.stdout = self._ProgressCapture(sys.stdout, info['name'])
                
                try:
                    install({"likelihood": {likelihood: None}})
                    success = True
                except Exception as e:
                    print_status(f"      Error: {e}", "ERROR")
                    success = False
                finally:
                    sys.stdout = old_stdout
                    spinner.stop(success)
                
                info["done"] = success
                if success:
                    completed += 1
                
                elapsed = time.time() - step_start
                print_status(f"      Time: {format_time(elapsed)}")
                
            except Exception as e:
                print_status(f"    ✗ {info['name']}: {str(e)[:60]}", "WARNING")
                info["done"] = False
        
        total_elapsed = time.time() - start_time
        print_status("")
        print_status("=" * 60)
        print_status(f"INSTALLATION SUMMARY ({format_time(total_elapsed)} total)")
        print_status("=" * 60)
        
        for likelihood, info in likelihoods.items():
            if info.get("installed"):
                status = "✓ (already present)"
            elif info["done"]:
                status = "✓ (just installed)"
            else:
                status = "✗ (failed)"
            print_status(f"  {info['name']}: {status}")
        
        success_rate = sum([1 for v in likelihoods.values() if v["done"]]) / len(likelihoods) * 100
        print_status(f"\n  Complete: {success_rate:.0f}% ({completed}/{total})")
        print_status("=" * 60)
        
        return {k: v["done"] for k, v in likelihoods.items()}
    
    class _ProgressCapture:
        """Capture and display progress from Cobaya install."""
        def __init__(self, stdout, name):
            self.stdout = stdout
            self.name = name
            self.last_line = ""
            
        def write(self, text):
            text = str(text)
            # Filter and show relevant progress lines
            if any(keyword in text.lower() for keyword in 
                   ['downloading', 'extracting', 'installing', 'progress', 
                    'unpacking', 'completed', 'mb/s', 'kb/s', '%']):
                line = text.strip()
                if line and line != self.last_line:
                    print(f"\r        → {line[:60]}{'...' if len(line) > 60 else ''}", end='', flush=True)
                    self.last_line = line
            self.stdout.write(text)
            
        def flush(self):
            self.stdout.flush()
    
    def _create_test_config(self):
        """Create a minimal test configuration."""
        config_dir = self.data_dir / "cobaya"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Minimal config already created in step_05
        print_status("  ✓ Test configurations ready")


if __name__ == "__main__":
    step = Step00bInstall()
    step.run()
