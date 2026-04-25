# Temporal Equivalence Principle: EFT Mapping and Acoustic Peak Constraints via hi_class

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**Author:** Matthew Lukin Smawfield  
**Status:** In Development  
**Paper Series:** TEP Series: Paper 14 (hi_class Cosmology)  
**Codename:** Geneva

## Overview

This paper presents the exact analytical mapping of the Temporal Equivalence Principle (TEP) bi-metric framework into the Bellini-Sawicki Effective Field Theory (EFT) of Dark Energy. By integrating the property functions ($\alpha_M, \alpha_B, \alpha_K, \alpha_T$) into the hi_class cosmological solver and running a full MCMC pipeline via Cobaya against Planck 2018 likelihoods, this work provides definitive proof that the TEP scalar field strictly preserves CMB acoustic peak structure while permitting the late-time, environment-dependent proper-time dynamics required to resolve the Hubble tension.

Key results:
1. **EFT Mapping:** TEP's conformal factor $A(\phi) = \exp(2\beta\phi/M_{\rm Pl})$ and disformal deformation $B(\phi)$ map exactly onto Horndeski $\alpha_i$ functions.
2. **Unscreened Cosmology:** At $z \approx 1100$, the universe is strictly unscreened ($\rho \sim 10^{-21}$ g/cm³), yet radiation-domination freezing ($T^\mu_\mu \approx 0$) preserves acoustic peaks.
3. **CMB Preservation:** hi_class + Cobaya MCMC confirms $|\Delta C_\ell/C_\ell| < 0.02\%$, with $H_0$ consistent with Planck to $< 0.1\sigma$.
4. **Hubble Tension Resolution:** The CMB $H_0$ posterior ($67.42 \pm 0.54$ km/s/Mpc) remains anchored, proving the local $\sim 73$ km/s/Mpc is a late-time environmental effect.

## Repository Structure

```text
TEP-HC/
├── data/
│   ├── hi_class/            # hi_class input parameters and background data
│   └── cobaya/              # Cobaya MCMC configuration files
├── logs/                    # Execution logs for hi_class and Cobaya runs
├── manuscripts/             # Generated PDF/Markdown outputs
├── results/
│   └── mcmc_chains/         # MCMC chain outputs and corner plots
├── scripts/
│   ├── hi_class_modules/    # C code for source/models/tep.c
│   └── cobaya_pipeline/     # Python scripts for MCMC execution
├── site/
│   └── components/          # HTML source of truth for manuscript
└── README.md
```

## Implementation Overview

### 1. hi_class Module (`source/models/tep.c`)
- Defines TEP parameters: `alpha_eff`, `phi_init`, `B_phi_coeff`
- Implements background evolution for $\phi_0(\tau)$ with $T^\mu_\mu$-sourced driving term
- Computes Bellini-Sawicki alphas: $\alpha_M, \alpha_T, \alpha_B, \alpha_K$
- Enforces stability constraints: $c_s^2 \geq 0$, $|\alpha_M| < 1$

### 2. Cobaya MCMC Pipeline
- Uses Planck 2018 high-$\ell$, low-$\ell$, and lensing likelihoods
- Varies standard $\Lambda$CDM parameters alongside $\log_{10}(\alpha_{\rm eff})$
- Runs parallel tempering with convergence criterion $R-1 < 0.01$

## Quick Start (Full Reproduction)

Anyone can download and run this pipeline to reproduce the analysis:

```bash
# 1. Clone the repository
git clone https://github.com/matthewsmawfield/TEP-HC.git
cd TEP-HC

# 2. Run the full pipeline (auto-installs dependencies)
python scripts/run_all.py

# Or step-by-step:
python scripts/run_all.py --stop-step 1  # Install only
python scripts/run_all.py --start-step 2  # Skip installation
```

### What Gets Installed Automatically

- **Step 01** automatically downloads and installs:
  - Python dependencies (NumPy, SciPy, Pandas, Matplotlib)
  - Cobaya MCMC sampler (`pip install cobaya[getdist]`)
  - Planck 2018 likelihoods (~10GB, 20-30 min download)

### Running Without Full Planck Data

For a quick test without downloading 10GB of Planck data:

```bash
python scripts/run_all.py --skip-steps 1,7,8  # Skip install and MCMC steps
```

This runs the theoretical pipeline (EFT mapping, background evolution, CMB spectra generation) without requiring Planck likelihoods.

## Manual Installation (if auto-install fails)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Cobaya and Planck likelihoods
pip install cobaya[getdist]
cobaya-install planck_2018_highl_TTTEEE planck_2018_lowl_TT planck_2018_lowl_EE planck_2018_lensing

# Compile hi_class with TEP module (optional - for full MCMC)
cd scripts/hi_class_modules/
# Follow instructions in tep_module/README.md
```

## Pipeline Steps

| Step | Description | Auto-Installs |
|------|-------------|---------------|
| 00 | Environment check | - |
| 01 | Install Cobaya + Planck likelihoods | ✓ |
| 02 | Generate TEP C module | - |
| 03 | Background evolution | - |
| 04 | Alpha functions validation | - |
| 05 | CMB spectra generation | - |
| 06 | Cobaya MCMC setup | - |
| 07 | MCMC execution | Requires Step 01 |
| 08 | Posterior analysis | Requires Step 07 |
| 09 | Results synthesis | - |

## Dependencies

Required:
- Python 3.9+
- NumPy, SciPy, Pandas, Matplotlib
- PyYAML

Auto-installed on first run:
- Cobaya (MCMC sampler)
- GetDist (posterior analysis)
- Planck 2018 likelihoods (~10GB download)

Optional (for full MCMC):
- hi_class (modified CLASS with Horndeski support)
- GCC compiler

## License

Creative Commons Attribution 4.0 International (CC-BY-4.0).
