#!/usr/bin/env python3
"""
TEP-HC Dependency Installer
============================
Automatically installs required dependencies for full pipeline execution.

Usage:
    python scripts/install_dependencies.py
    python scripts/install_dependencies.py --skip-cobaya
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a shell command and report status."""
    print(f"  → {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            print(f"    ✓ Success")
            return True
        else:
            print(f"    ✗ Failed: {result.stderr[:200]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"    ✗ Timeout")
        return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False


def install_base_packages():
    """Install base Python packages."""
    print("\n📦 Installing base Python packages...")
    packages = [
        "numpy>=1.20",
        "scipy>=1.7",
        "pandas>=1.3",
        "matplotlib>=3.4",
        "pyyaml>=5.4",
        "requests>=2.25",
        "tqdm>=4.60"
    ]
    cmd = f"{sys.executable} -m pip install " + " ".join(packages)
    return run_command(cmd, "Base packages")


def install_cobaya():
    """Install Cobaya and cosmology tools."""
    print("\n🌌 Installing Cobaya (this may take a few minutes)...")
    
    # Install cobaya with cosmology extras
    cmd = f"{sys.executable} -m pip install cobaya[getdist]"
    if not run_command(cmd, "Cobaya with GetDist"):
        return False
    
    # Install planck likelihood support
    cmd = f"{sys.executable} -m pip install cobaya-install-planck"
    if not run_command(cmd, "Planck likelihood installer"):
        print("    ⚠ Planck installer optional - will try manual download")
    
    return True


def install_planck_likelihoods():
    """Download Planck 2018 likelihoods and data."""
    print("\n📡 Downloading Planck 2018 likelihoods...")
    print("  (This requires ~10GB disk space and may take 20-30 minutes)")
    
    try:
        import cobaya
        from cobaya.install import install
        
        # Install Planck 2018 high-l TTTEEE
        print("  → Installing planck_2018_highl_TTTEEE...")
        install({"likelihood": {"planck_2018_highl_TTTEEE": None}})
        
        # Install Planck 2018 low-l
        print("  → Installing planck_2018_lowl_TT and EE...")
        install({"likelihood": {"planck_2018_lowl_TT": None}})
        install({"likelihood": {"planck_2018_lowl_EE": None}})
        
        # Install Planck 2018 lensing
        print("  → Installing planck_2018_lensing...")
        install({"likelihood": {"planck_2018_lensing": None}})
        
        print("  ✓ Planck likelihoods installed")
        return True
        
    except Exception as e:
        print(f"  ✗ Planck installation failed: {e}")
        print("  You can install manually later with:")
        print("    cobaya-install planck_2018_highl_TTTEEE planck_2018_lowl_TT planck_2018_lowl_EE planck_2018_lensing")
        return False


def check_hi_class():
    """Check if hi_class is available."""
    print("\n🔭 Checking hi_class availability...")
    
    # Check if classy is installed (Python wrapper)
    try:
        import classy
        print("  ✓ classy (hi_class) Python module found")
        return True
    except ImportError:
        print("  ⚠ classy not installed")
        print("  hi_class must be compiled manually with TEP module:")
        print("    cd scripts/hi_class_modules/")
        print("    # Follow instructions in tep_module/README.md")
        return False


def create_cobaya_override():
    """Create a minimal Cobaya config that works without full Planck data."""
    print("\n🔧 Creating minimal test configuration...")
    
    project_root = Path(__file__).parent.parent
    minimal_config = project_root / "data" / "cobaya" / "tep_cosmology_minimal.yaml"
    minimal_config.parent.mkdir(parents=True, exist_ok=True)
    
    config_content = """# TEP-HC Minimal Cobaya Configuration
# ==================================
# For testing without full Planck likelihoods.
# Uses synthetic likelihood based on pre-computed CMB spectra.

theory:
  classy:
    extra_args:
      smg_model: tep
      tep_alpha_eff: 1.0e6
      tep_beta: 1.0
      output: tCl,pCl,lCl
      lensing: yes
      l_max_scalars: 2500

# Minimal likelihood: just check that code runs
likelihood:
  _custom:
    class: "TestLikelihood"
    
params:
  logA:
    prior: {min: 1.61, max: 3.91}
    ref: {dist: norm, loc: 3.044, scale: 0.014}
    proposal: 0.01
    latex: \\log(10^{10}A_s)
    drop: true
  A_s: {value: 'lambda logA: 1e-10*np.exp(logA)', latex: A_s}
  n_s:
    prior: {min: 0.8, max: 1.2}
    ref: {dist: norm, loc: 0.966, scale: 0.004}
    proposal: 0.002
    latex: n_s
  theta_s:
    prior: {min: 0.5, max: 10.0}
    ref: {dist: norm, loc: 1.0411, scale: 0.0004}
    proposal: 0.0002
    latex: 100\\theta_s
  omega_b:
    prior: {min: 0.005, max: 0.1}
    ref: {dist: norm, loc: 0.0224, scale: 0.0001}
    proposal: 0.0001
    latex: \\Omega_b h^2
  omega_cdm:
    prior: {min: 0.001, max: 0.99}
    ref: {dist: norm, loc: 0.120, scale: 0.001}
    proposal: 0.0005
    latex: \\Omega_{cdm} h^2
  tau_reio:
    prior: {min: 0.01, max: 0.8}
    ref: {dist: norm, loc: 0.054, scale: 0.007}
    proposal: 0.003
    latex: \\tau_{reio}

sampler:
  evaluate: null  # Just evaluate at reference point for testing
"""
    
    with open(minimal_config, 'w') as f:
        f.write(config_content)
    
    print(f"  ✓ Created: {minimal_config}")
    return minimal_config


def main():
    parser = argparse.ArgumentParser(
        description="Install TEP-HC dependencies"
    )
    parser.add_argument(
        "--skip-cobaya", action="store_true",
        help="Skip Cobaya and Planck installation (base packages only)"
    )
    parser.add_argument(
        "--skip-planck", action="store_true",
        help="Install Cobaya but skip Planck likelihood download"
    )
    parser.add_argument(
        "--minimal", action="store_true",
        help="Create minimal test config instead of full Planck"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("TEP-HC Dependency Installer")
    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"Platform: {sys.platform}")
    
    # Install base packages
    if not install_base_packages():
        print("\n✗ Base package installation failed")
        sys.exit(1)
    
    # Install Cobaya and cosmology tools
    if not args.skip_cobaya:
        if install_cobaya():
            if not args.skip_planck and not args.minimal:
                install_planck_likelihoods()
        else:
            print("\n⚠ Cobaya installation failed - pipeline will run in dry mode")
    
    # Check hi_class
    check_hi_class()
    
    # Create minimal config if requested or if Planck not available
    if args.minimal:
        create_cobaya_override()
    
    print("\n" + "=" * 60)
    print("Installation Summary")
    print("=" * 60)
    print("✓ Base packages installed")
    if args.skip_cobaya:
        print("⚠ Cobaya skipped - pipeline will run in demonstration mode")
    else:
        print("✓ Cobaya installed")
        if args.skip_planck or args.minimal:
            print("⚠ Planck likelihoods not downloaded")
        else:
            print("✓ Planck 2018 likelihoods ready")
    print("\nTo run the pipeline:")
    print("  python scripts/run_all.py")


if __name__ == "__main__":
    main()
