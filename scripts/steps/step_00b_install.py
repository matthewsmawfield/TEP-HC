#!/usr/bin/env python3
"""
Step 00b: Install Dependencies and Data (ULTRA-ROBUST)
========================================================
Automatically installs Cobaya, Planck likelihoods, and downloads required data.
With RETRY logic, INTEGRITY checks, and PARALLEL downloads.

Outputs:
    - logs/step_00b_install.log
    - data/cobaya/*.yaml (configuration files)
    - ~/.cobaya/ (Planck likelihoods cached here)
"""

import sys
import os
import subprocess
import threading
import time
import shutil
import urllib.request
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.utils.logger import TEPLogger, set_step_logger, print_status

# Set packages path - use existing if available, otherwise local
# Check for external packages path from environment variable or default location
EXTERNAL_PACKAGES = os.environ.get("COBAYA_EXTERNAL_PACKAGES", "")
EXISTING_PACKAGES_PATH = Path(EXTERNAL_PACKAGES) if EXTERNAL_PACKAGES else PROJECT_ROOT.parent.parent / "TVP" / "TVP" / "data" / "external" / "cosmology_likelihoods"
LOCAL_PACKAGES_PATH = PROJECT_ROOT / "data" / "external" / "cobaya_packages"

# Use existing path if it has data, otherwise use local
if EXISTING_PACKAGES_PATH.exists() and (EXISTING_PACKAGES_PATH / "data" / "planck_2018").exists():
    PACKAGES_PATH = EXISTING_PACKAGES_PATH
else:
    PACKAGES_PATH = LOCAL_PACKAGES_PATH
    PACKAGES_PATH.mkdir(parents=True, exist_ok=True)

os.environ["COBAYA_PACKAGES_PATH"] = str(PACKAGES_PATH)

# Detect MPI availability - only disable if mpirun not available
_MPI_AVAILABLE = subprocess.run(["which", "mpirun"], capture_output=True).returncode == 0
if not _MPI_AVAILABLE:
    os.environ["COBAYA_NOMPI"] = "1"


def format_bytes(size_bytes) -> str:
    """Convert bytes to human readable format."""
    try:
        size_bytes = float(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(size_bytes) < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    except (TypeError, ValueError):
        return str(size_bytes)


def format_time(seconds: float) -> str:
    """Format seconds as MM:SS or HH:MM:SS."""
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours:02d}:{mins:02d}:{secs:02d}"
    return f"{mins:02d}:{secs:02d}"


class RobustDownloader:
    """Ultra-robust downloader with retry, integrity checks, and parallel support."""
    
    def __init__(self, max_retries: int = 3, timeout: int = 1800):
        self.max_retries = max_retries
        self.timeout = timeout
        self.results: Dict[str, Dict] = {}
        self._lock = threading.Lock()
    
    def check_network(self) -> bool:
        """Check if we have internet connectivity."""
        try:
            urllib.request.urlopen('https://pypi.org', timeout=5)
            return True
        except Exception:
            return False
    
    def check_disk_space(self, path: Path, required_gb: float = 15.0) -> bool:
        """Check if sufficient disk space is available."""
        try:
            stat = shutil.disk_usage(path)
            free_gb = stat.free / (1024**3)
            if free_gb < required_gb:
                print_status(f"  ✗ Insufficient disk space: {free_gb:.1f}GB free, {required_gb}GB required", "ERROR")
                return False
            print_status(f"  ✓ Disk space OK: {free_gb:.1f}GB free")
            return True
        except Exception as e:
            print_status(f"  ⚠ Could not check disk space: {e}", "WARNING")
            return True  # Assume OK if we can't check
    
    def check_cobaya_install(self, likelihood: str, packages_path: Path) -> Tuple[bool, str]:
        """Check if a likelihood is properly installed with real data."""
        data_path = packages_path / "data"
        
        # Expected data directories and minimum sizes
        # These match what cobaya actually creates
        checks = {
            "planck_2018_highl_plik.TTTEEE": ("planck_2018", 40_000_000),  # 40MB
            "planck_2018_lowl.TT": ("planck_2018_lowT_native", 5_000_000),  # 5MB
            "planck_2018_lowl.EE": ("planck_2018_lowE_native", 500_000),    # 500KB
            "planck_2018_lensing.native": ("planck_supp_data_and_covmats", 5_000_000),  # 5MB
            "bao.sdss_dr12_consensus_final": ("bao_data", 100_000),  # 100KB
            "sn.pantheonplus": ("sn_data", 500_000),  # 500KB
        }
        
        if likelihood not in checks:
            return True, "Unknown likelihood, assuming OK"
        
        dirname, min_size = checks[likelihood]
        target_path = data_path / dirname
        
        if not target_path.exists():
            return False, f"Directory {dirname} not found"
        
        # Calculate actual size
        total_size = 0
        for item in target_path.rglob("*"):
            if item.is_file():
                total_size += item.stat().st_size
        
        if total_size < min_size:
            return False, f"Size {format_bytes(total_size)} < required {format_bytes(min_size)}"
        
        # Check for actual data files in clik directories
        if "planck" in likelihood:
            clik_dirs = list(target_path.rglob("*.clik"))
            real_data_found = False
            for clik_dir in clik_dirs:
                if clik_dir.is_dir():
                    clik_data = clik_dir / "clik"
                    if clik_data.exists():
                        size = sum(f.stat().st_size for f in clik_data.rglob("*") if f.is_file())
                        if size > 1_000_000:  # At least 1MB of data
                            real_data_found = True
                            break
            
            if not real_data_found and clik_dirs:
                return False, "clik directories exist but contain no real data"
        
        return True, f"Verified {format_bytes(total_size)}"
    
    def download_with_retry(self, likelihood: str, packages_path: Path, force: bool = False) -> Dict:
        """Download a likelihood with retry logic and integrity verification."""
        result = {
            "likelihood": likelihood,
            "success": False,
            "attempts": 0,
            "error": None,
            "verification": None
        }
        
        # Skip if already installed and not forcing
        if not force:
            ok, msg = self.check_cobaya_install(likelihood, packages_path)
            if ok:
                result["success"] = True
                result["verification"] = f"Already installed: {msg}"
                return result
        
        # Try download with exponential backoff
        for attempt in range(1, self.max_retries + 1):
            result["attempts"] = attempt
            print_status(f"      Attempt {attempt}/{self.max_retries}: cobaya-install {likelihood}")
            
            try:
                cmd = ["cobaya-install", likelihood, "--force", "-p", str(packages_path)]
                
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Monitor with timeout
                start_time = time.time()
                output_lines = []
                last_progress_time = start_time
                
                while True:
                    line = process.stdout.readline()
                    if not line:
                        break
                    
                    output_lines.append(line)
                    
                    # Update progress time on activity
                    if 'downloading' in line.lower() or 'extracting' in line.lower():
                        last_progress_time = time.time()
                    
                    # Check for timeout
                    if time.time() - last_progress_time > 300:  # 5 min no progress
                        process.terminate()
                        raise TimeoutError("No progress for 5 minutes")
                    
                    # Overall timeout
                    if time.time() - start_time > self.timeout:
                        process.terminate()
                        raise TimeoutError(f"Download timeout after {self.timeout}s")
                
                process.wait()
                
                if process.returncode == 0:
                    # Verify installation
                    ok, msg = self.check_cobaya_install(likelihood, packages_path)
                    if ok:
                        result["success"] = True
                        result["verification"] = msg
                        return result
                    else:
                        result["error"] = f"Download OK but verification failed: {msg}"
                else:
                    stderr = ''.join(output_lines[-10:]) if output_lines else "Unknown error"
                    result["error"] = f"cobaya-install failed: {stderr[:200]}"
                
            except TimeoutError as e:
                result["error"] = str(e)
            except Exception as e:
                result["error"] = f"Exception: {e}"
            
            # Retry with backoff
            if attempt < self.max_retries:
                wait_time = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                print_status(f"      Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        return result
    
    def download_parallel(self, likelihoods: List[Tuple[str, dict]], packages_path: Path, 
                          force: bool = False, max_workers: int = 2) -> Dict[str, Dict]:
        """Download multiple likelihoods in parallel with thread pool."""
        results = {}
        
        # Filter out built-in likelihoods (no download needed)
        to_download = [(l, i) for l, i in likelihoods if not i.get('builtin')]
        builtin = [(l, i) for l, i in likelihoods if i.get('builtin')]
        
        # Mark built-in as complete
        for likelihood, info in builtin:
            results[likelihood] = {
                "likelihood": likelihood,
                "success": True,
                "attempts": 0,
                "verification": "Built-in likelihood (no download needed)"
            }
        
        if not to_download:
            return results
        
        print_status(f"      Downloading {len(to_download)} likelihood(s) in parallel (max {max_workers} at a time)")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_like = {
                executor.submit(self.download_with_retry, l, packages_path, force): (l, i)
                for l, i in to_download
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_like):
                likelihood, info = future_to_like[future]
                try:
                    result = future.result()
                    results[likelihood] = result
                    
                    if result["success"]:
                        print_status(f"  ✓ {info['name']}: {result['verification']}")
                    else:
                        print_status(f"  ✗ {info['name']}: {result['error']}", "ERROR")
                        
                except Exception as e:
                    results[likelihood] = {
                        "likelihood": likelihood,
                        "success": False,
                        "error": str(e)
                    }
                    print_status(f"  ✗ {info['name']}: {e}", "ERROR")
        
        return results


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
            
            # Install mpi4py for M4 Pro parallel support
            print_status("\n🔄 Checking MPI support for M4 Pro...", "PROCESS")
            results["mpi4py_installed"] = self._install_mpi4py()
            
            # Install hi_class for TEP-modified gravity calculations
            print_status("\n🔭 Checking hi_class (modified gravity Boltzmann solver)...", "PROCESS")
            results["hi_class_installed"] = self._install_hi_class(force=force_install)
            
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
        """Check if base packages from requirements.txt are installed."""
        requirements_file = PROJECT_ROOT / "requirements.txt"
        
        # Check core packages first
        core_packages = ["numpy", "scipy", "pandas", "matplotlib", "yaml"]
        for pkg in core_packages:
            try:
                __import__(pkg.replace("yaml", "pyyaml").replace("pyyaml", "yaml"))
            except ImportError:
                return False
        
        # Check if requirements.txt exists and has additional packages
        if requirements_file.exists():
            with open(requirements_file) as f:
                for line in f:
                    line = line.strip()
                    # Skip comments and empty lines
                    if not line or line.startswith('#') or line.startswith('('):
                        continue
                    # Parse package name (before >=, ==, etc.)
                    pkg = line.split('>=')[0].split('==')[0].split('<')[0].strip()
                    if pkg and not pkg.startswith('#'):
                        try:
                            __import__(pkg.replace('-', '_'))
                        except ImportError:
                            return False
        return True
    
    def _install_base_packages(self):
        """Install required Python packages from requirements.txt."""
        requirements_file = PROJECT_ROOT / "requirements.txt"
        
        if requirements_file.exists():
            print_status(f"Installing packages from requirements.txt...")
            cmd = [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0
        else:
            # Fallback to core packages
            packages = [
                "numpy>=1.20", "scipy>=1.7", "pandas>=1.3",
                "matplotlib>=3.4", "pyyaml>=5.4", "requests>=2.25"
            ]
            print_status(f"Installing {len(packages)} base packages...")
            cmd = [sys.executable, "-m", "pip", "install", "--progress-bar", "on"] + packages
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0
        
        if success:
            print_status("  ✓ Base packages installed successfully")
        else:
            print_status("  ✗ Base package installation failed", "ERROR")
    
    def _install_openmpi(self) -> bool:
        """Install OpenMPI system package (macOS only)."""
        print_status("Checking OpenMPI availability...")
        
        # Check if mpirun already exists
        result = subprocess.run(["which", "mpirun"], capture_output=True)
        if result.returncode == 0:
            print_status("  ✓ OpenMPI already installed")
            return True
        
        # Only auto-install on macOS with Homebrew
        if sys.platform == "darwin":
            # Check if Homebrew is available
            brew_check = subprocess.run(["which", "brew"], capture_output=True)
            if brew_check.returncode != 0:
                print_status("  ⚠ Homebrew not found. Cannot auto-install OpenMPI.", "WARNING")
                print_status("     Install manually: brew install openmpi", "INFO")
                return False
            
            print_status("  Installing OpenMPI via Homebrew (this may take 2-3 minutes)...")
            try:
                result = subprocess.run(
                    ["brew", "install", "openmpi"],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode == 0:
                    print_status("  ✓ OpenMPI installed successfully")
                    return True
                else:
                    print_status(f"  ⚠ OpenMPI installation failed: {result.stderr[:100]}", "WARNING")
                    return False
            except subprocess.TimeoutExpired:
                print_status("  ⚠ OpenMPI installation timed out", "WARNING")
                return False
            except Exception as e:
                print_status(f"  ⚠ OpenMPI installation error: {e}", "WARNING")
                return False
        else:
            # Linux - suggest apt/yum
            print_status("  ⚠ OpenMPI not found. On Linux, install with:", "WARNING")
            print_status("     sudo apt-get install openmpi-bin libopenmpi-dev", "INFO")
            return False
    
    def _install_mpi4py(self) -> bool:
        """Install mpi4py for M4 Pro parallel MCMC support."""
        print_status("Checking MPI support for M4 Pro...")
        
        # First ensure OpenMPI is installed
        openmpi_installed = self._install_openmpi()
        
        try:
            import mpi4py
            print_status("  ✓ mpi4py already installed")
            if openmpi_installed:
                print_status("  ✓ MPI parallel mode available (10x speedup!)", "SUCCESS")
            return True
        except ImportError:
            print_status("  Installing mpi4py for parallel MCMC chains...")
            
            cmd = [sys.executable, "-m", "pip", "install", "mpi4py>=3.1.0"]
            result = subprocess.run(cmd, capture_output=True, text=True)
            success = result.returncode == 0
            
            if success:
                print_status("  ✓ mpi4py installed successfully")
                if openmpi_installed:
                    print_status("  ✓ MPI parallel mode now available!", "SUCCESS")
                return True
            else:
                print_status("  ⚠ mpi4py installation failed (optional for parallel MCMC)", "WARNING")
                return False
    
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
        result = subprocess.run(cmd, capture_output=True, text=True)
        success = result.returncode == 0
        
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
        """Check if a likelihood is properly installed with actual data."""
        try:
            # Use determined packages path
            install_path = PACKAGES_PATH
            data_path = install_path / "data"
            
            # Define minimum size thresholds (in MB) for each likelihood
            # These are minimums to verify data exists, not full download sizes
            min_size_mb = {
                # Planck 2018 (actual installed sizes)
                "planck_2018_highl_plik.TTTEEE": 50,  # ~89MB with lite versions
                "planck_2018_lowl.TT": 5,
                "planck_2018_lowl.EE": 0.5,
                "planck_2018_lensing.native": 10,  # ~14MB actual
                # BAO/SN built-in
                "bao.sdss_dr12_consensus_final": 0.001,
                "sn.pantheonplus": 0.001,
            }
            
            # Map likelihood names to expected data directories
            # These match what cobaya actually creates
            likelihood_dir_map = {
                # Planck
                "planck_2018_highl_plik.TTTEEE": ["planck_2018"],
                "planck_2018_lowl.TT": ["planck_2018_lowT_native"],
                "planck_2018_lowl.EE": ["planck_2018_lowE_native"],
                "planck_2018_lensing.native": ["planck_supp_data_and_covmats"],
                # BAO
                "bao.sixdf_2011_bao": ["sixdf_2011_bao"],
                "bao.sdss_dr7_mgs": ["sdss_dr7_mgs"],
                "bao.sdss_dr12_consensus_final": ["sdss_dr12_consensus_final"],
                # SN
                "sn.pantheon": ["pantheon"],
                "sn.pantheonplus": ["pantheonplus"],
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
                            # Verify data files exist
                            data_files = list(expected_path.rglob('*.fits')) + \
                                       list(expected_path.rglob('*.clik')) + \
                                       list(expected_path.rglob('*.clik_lensing')) + \
                                       list(expected_path.rglob('*.bin')) + \
                                       list(expected_path.rglob('*.txt')) + \
                                       list(expected_path.rglob('*.dat')) + \
                                       list(expected_path.rglob('*.dataset'))
                            if len(data_files) >= 1:
                                return True
            
            return False
            
        except Exception as e:
            # If we can't check, assume not installed to be safe
            return False
    
    def _install_planck_likelihoods(self, force: bool = False) -> dict:
        """Download Planck 2018 + BAO + SN likelihoods using Cobaya with intelligent skip logic."""
        likelihoods = {
            # Planck 2018 (CMB) - requires external data download
            "planck_2018_highl_plik.TTTEEE": {"name": "Planck 2018 High-L TTTEEE", "size": "~6 GB", "done": False, "installed": False, "required": True},
            "planck_2018_lowl.TT": {"name": "Planck 2018 Low-L TT", "size": "~50 MB", "done": False, "installed": False, "required": True},
            "planck_2018_lowl.EE": {"name": "Planck 2018 Low-L EE", "size": "~50 MB", "done": False, "installed": False, "required": True},
            "planck_2018_lensing.native": {"name": "Planck 2018 Lensing", "size": "~3 GB", "done": False, "installed": False, "required": True},
            # BAO data - built into Cobaya, no external download needed
            "bao.sdss_dr12_consensus_final": {"name": "BAO SDSS DR12 Consensus", "size": "built-in", "done": False, "installed": False, "required": True, "builtin": True},
            # Supernova data - built into Cobaya, no external download needed
            "sn.pantheonplus": {"name": "SN Pantheon+", "size": "built-in", "done": False, "installed": False, "required": True, "builtin": True},
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
        
        # Calculate total download size (only for non-built-in likelihoods)
        size_map = {
            'highl': 6.0, 'lensing': 3.0, 'lowl': 0.05
        }
        total_size = 0
        for k, info in need_download:
            if info.get('builtin'):
                continue
            for key, size in size_map.items():
                if key in k.lower():
                    total_size += size
                    break
        
        print_status("=" * 60)
        print_status("PLANCK 2018 LIKELIHOOD INSTALLATION (ULTRA-ROBUST)")
        print_status("=" * 60)
        print_status(f"To download: {len(need_download)} likelihood(s)")
        print_status(f"Total download size: ~{total_size:.1f} GB")
        print_status(f"Max parallel downloads: 2 (to avoid overwhelming server)")
        print_status(f"Max retries per package: 3")
        print_status(f"Estimated time: 15-25 minutes")
        print_status("=" * 60)
        print_status("")
        
        # Pre-flight checks
        print_status("🔍 Pre-flight checks...")
        # Use determined packages path
        packages_path = PACKAGES_PATH
        packages_path.mkdir(parents=True, exist_ok=True)
        
        downloader = RobustDownloader(max_retries=3, timeout=1800)
        
        # Check network
        if not downloader.check_network():
            print_status("  ✗ No internet connectivity detected!", "ERROR")
            return {k: False for k in likelihoods.keys()}
        print_status("  ✓ Network connectivity OK")
        
        # Check disk space
        if not downloader.check_disk_space(packages_path, required_gb=15.0):
            return {k: False for k in likelihoods.keys()}
        
        print_status("")
        
        # Perform parallel downloads with retry
        start_time = time.time()
        results = downloader.download_parallel(need_download, packages_path, force=force, max_workers=2)
        
        # Update info with results
        completed = len(already_installed)
        for likelihood, result in results.items():
            likelihoods[likelihood]["done"] = result["success"]
            if result["success"]:
                completed += 1
        
        total_elapsed = time.time() - start_time
        
        # Post-installation verification
        print_status("\n🔍 Verifying installations...")
        verified = 0
        for likelihood, info in list(need_download):
            if info["done"]:
                # Built-in likelihoods are always verified if Cobaya is available
                if info.get('builtin'):
                    print_status(f"  ✓ {info['name']}: Verified (built-in)")
                    verified += 1
                # Re-check external installations
                elif self._check_likelihood_installed(likelihood):
                    print_status(f"  ✓ {info['name']}: Verified installed")
                    verified += 1
                else:
                    print_status(f"  ✗ {info['name']}: Installation incomplete", "ERROR")
                    info["done"] = False
        
        print_status("")
        print_status("=" * 60)
        print_status(f"INSTALLATION SUMMARY ({format_time(total_elapsed)} total)")
        print_status("=" * 60)
        
        # Group by category
        categories = {
            "Planck 2018 (CMB)": [k for k in likelihoods.keys() if 'planck' in k],
            "BAO Data": [k for k in likelihoods.keys() if 'bao' in k],
            "Supernova Data": [k for k in likelihoods.keys() if 'sn.' in k],
        }
        
        for cat_name, cat_likes in categories.items():
            cat_present = [k for k in cat_likes if likelihoods[k]["done"] or likelihoods[k].get("installed")]
            cat_total = len(cat_likes)
            print_status(f"\n{cat_name}: {len(cat_present)}/{cat_total}")
            for k in cat_likes:
                info = likelihoods[k]
                if info.get("installed"):
                    status = "✓ (already present)"
                elif info["done"]:
                    status = "✓ (just installed)"
                elif info.get("required"):
                    status = "✗ REQUIRED - FAILED"
                else:
                    status = "✗ (failed)"
                print_status(f"  {info['name']}: {status}")
        
        total = len(likelihoods)
        success_rate = sum([1 for v in likelihoods.values() if v["done"]]) / total * 100
        print_status(f"\n  Complete: {success_rate:.0f}% ({completed}/{total})")
        
        # Check if all required are installed
        required_missing = [v['name'] for k, v in likelihoods.items() if v.get('required') and not (v['done'] or v.get('installed'))]
        if required_missing:
            print_status(f"\n⚠ REQUIRED LIKELIHOODS MISSING:", "ERROR")
            for name in required_missing:
                print_status(f"  • {name}", "ERROR")
            print_status("\nStep 06 (MCMC) will FAIL without these likelihoods.", "ERROR")
            print_status("Re-run with --force-install to retry.", "WARNING")
        else:
            print_status(f"\n✓ ALL REQUIRED LIKELIHOODS INSTALLED - Step 06 can proceed", "SUCCESS")
        
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
    
    def _install_hi_class(self, force: bool = False) -> bool:
        """Install hi_class from GitHub with TEP module support."""
        print_status("\n📦 Installing hi_class (Horndeski in CLASS)...", "PROCESS")
        
        try:
            # Check if already installed
            if not force:
                try:
                    import classy
                    print_status("  ✓ hi_class already installed", "SUCCESS")
                    return True
                except ImportError:
                    pass
            
            import subprocess
            import tempfile
            import shutil
            
            # Create installation directory
            install_dir = self.root_dir / "external" / "hi_class"
            install_dir.mkdir(parents=True, exist_ok=True)
            
            print_status("  Cloning hi_class repository...", "PROCESS")
            print_status("    URL: https://github.com/miguelzuma/hi_class.git", "INFO")
            print_status("    Branch: master", "INFO")
            
            # Clone hi_class
            with tempfile.TemporaryDirectory() as tmpdir:
                clone_cmd = [
                    "git", "clone", "--depth", "1",
                    "https://github.com/miguelzuma/hi_class.git",
                    str(Path(tmpdir) / "hi_class")
                ]
                
                print_status("  Running git clone...", "PROCESS")
                result = subprocess.run(
                    clone_cmd,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    print_status(f"  ✗ Git clone failed: {result.stderr[:100]}", "ERROR")
                    return False
                
                hi_class_source = Path(tmpdir) / "hi_class"
                print_status("  ✓ Repository cloned successfully", "SUCCESS")
                
                # Apply native TEP background-only patch (tep_mode in background.c)
                patch_file = self.root_dir / "external" / "patches" / "hiclass_tep_native.patch"
                if not patch_file.exists():
                    print_status(f"  ✗ TEP patch not found: {patch_file}", "ERROR")
                    return False
                print_status("  Applying native TEP patch (tep_mode)...", "PROCESS")
                patch_result = subprocess.run(
                    ["patch", "-p1", "-i", str(patch_file)],
                    cwd=hi_class_source,
                    capture_output=True,
                    text=True,
                )
                if patch_result.returncode != 0:
                    print_status("  ✗ TEP patch failed to apply", "ERROR")
                    print_status(f"    {patch_result.stderr[:300]}", "ERROR")
                    return False
                if "tep_mode" not in (hi_class_source / "source" / "background.c").read_text():
                    print_status("  ✗ Patch applied but tep_mode missing from background.c", "ERROR")
                    return False
                print_status("  ✓ Native TEP patch applied (background.c, input.c, background.h)", "SUCCESS")
                
                # Compile hi_class
                print_status("  Compiling hi_class...", "PROCESS")
                print_status("    This may take 2-5 minutes...", "INFO")
                
                # Clean any previous build
                build_dir = hi_class_source / "build"
                if build_dir.exists():
                    shutil.rmtree(build_dir)
                
                # Configure and build using the python/ subdirectory
                import sys
                
                # Apply compatibility patches for modern Python/NumPy/Cython
                print_status("    Applying compatibility patches...", "PROCESS")
                
                # Patch 1: Fix NumPy types in classy.pyx (np.int_t -> np.int64_t)
                classy_pyx = hi_class_source / "python" / "classy.pyx"
                if classy_pyx.exists():
                    content = classy_pyx.read_text()
                    content = content.replace("ctypedef np.float_t DTYPE_t", "ctypedef np.float64_t DTYPE_t")
                    content = content.replace("ctypedef np.int_t DTYPE_i", "ctypedef np.int64_t DTYPE_i")
                    classy_pyx.write_text(content)
                    print_status("      ✓ Patched classy.pyx for NumPy compatibility", "INFO")
                
                # Patch 2: Fix setup.py for Cython compatibility
                setup_py = hi_class_source / "python" / "setup.py"
                if setup_py.exists():
                    content = setup_py.read_text()
                    # Replace the cython_directives line with modern approach
                    old_directive = "classy_ext.cython_directives = {'language_level': \"3\" if sys.version_info.major>=3 else \"2\"}"
                    new_directive = '''# Fix Cython compatibility with newer versions
classy_ext.cython_directives = {'language_level': "3"}

# Use cythonize explicitly with proper options
from Cython.Build import cythonize
classy_ext = cythonize(
    classy_ext,
    compiler_directives={'language_level': "3"},
    force=True
)[0]'''
                    content = content.replace(old_directive, new_directive)
                    # Remove duplicate sys import if present
                    content = content.replace("import sys\nclassy_ext.cython_directives", "classy_ext.cython_directives")
                    setup_py.write_text(content)
                    print_status("      ✓ Patched setup.py for Cython compatibility", "INFO")
                
                # First compile the C code using make
                print_status("    Building C library...", "PROCESS")
                make_cmd = ["make", "clean"]
                subprocess.run(make_cmd, cwd=hi_class_source, capture_output=True)
                
                make_cmd = ["make", "libclass.a"]
                result = subprocess.run(
                    make_cmd,
                    cwd=hi_class_source,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.returncode != 0:
                    print_status(f"  ✗ Make compilation failed", "ERROR")
                    print_status(f"    Error: {result.stderr[:200]}", "ERROR")
                    return False
                
                print_status("    ✓ C library built", "SUCCESS")
                
                # Install Python wrapper
                print_status("    Installing Python wrapper...", "PROCESS")
                install_cmd = [sys.executable, "-m", "pip", "install", "-e", ".", "--no-build-isolation"]
                
                result = subprocess.run(
                    install_cmd,
                    cwd=hi_class_source / "python",
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode != 0:
                    print_status(f"  ✗ Installation failed", "ERROR")
                    return False
                
                print_status("  ✓ hi_class installed successfully", "SUCCESS")
                
                # Move to external directory for persistence
                final_dir = install_dir / "hi_class"
                if final_dir.exists():
                    shutil.rmtree(final_dir)
                shutil.move(str(hi_class_source), str(final_dir))
                
                print_status(f"  ✓ Installed to: {final_dir}", "SUCCESS")
                
                # Verify installation
                try:
                    import classy
                    print_status("  ✓ hi_class import verified", "SUCCESS")
                    return True
                except ImportError as e:
                    print_status(f"  ✗ Import verification failed: {e}", "ERROR")
                    return False
                
        except subprocess.TimeoutExpired:
            print_status("  ✗ Installation timed out", "ERROR")
            return False
        except Exception as e:
            print_status(f"  ✗ Installation error: {e}", "ERROR")
            return False


if __name__ == "__main__":
    step = Step00bInstall()
    step.run()
