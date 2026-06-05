# Temporal Equivalence Principle: Native hi_class Implementation and CMB Acoustic Peak Preservation

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

**Author:** Matthew Lukin Smawfield  
**Version:** v0.1 (Geneva)  
**First published:** 24 May 2026  
**Status:** Preprint (Open for Collaboration)  
**Website:** [https://matthewsmawfield.github.io/TEP-HC/](https://matthewsmawfield.github.io/TEP-HC/)  
**Paper Series:** TEP Series: Paper 18 (hi_class Cosmology)

## Abstract

General Relativity is extensively validated in the deeply screened, high-density regime of the Solar System, but cosmological tensions—specifically the Hubble discrepancy—suggest a scale-dependent breakdown of the isochrony axiom. The Temporal Equivalence Principle (TEP) resolves these late-universe anomalies via a dynamical proper-time field, screened at densities $\rho > 20$ g/cm³. This paper implements the native TEP background modification directly in hi_class via `tep_mode`: the Jordan-frame factor $M(z) = A/(1-\alpha_A)$ modifies $H(z)$ while standard General Relativistic perturbations are preserved. Direct Boltzmann integration confirms sound-horizon preservation to parts-per-million ($r_s^{\rm TEP}/r_s^{\Lambda\rm CDM} = 0.999994$) and unchanged acoustic-peak morphology; the sole CMB effect of a non-zero homogeneous amplitude $\epsilon_T$ is a late-time angular-diameter-distance projection degenerate with $H_0$. A joint Cobaya MCMC against Planck 2018 low-$\ell$ TT/EE + lensing + BAO + Pantheon+ yields $\epsilon_T = 0.0051 \pm 0.0042$ and $H_0 = 66.73 \pm 1.60$ km/s/Mpc. The Bellini–Sawicki EFT mapping ($\alpha_M, \alpha_B, \alpha_K, \alpha_T$) is retained in step 3 as an archived theoretical reference.

## Key Results

1. **Native `tep_mode`:** $H_{\rm TEP}(z) = H_{\Lambda\rm CDM}(z)\,M(z)$ with $f_T(z)=\ln(1+z)\exp[-(z/z_T)^{n_T}]$, patched into hi_class `background.c`.
2. **Sound horizon:** $r_s^{\rm TEP}/r_s^{\Lambda\rm CDM} = 0.999994$; acoustic-peak morphology unchanged at recombination.
3. **Joint MCMC:** $\epsilon_T = 0.0051 \pm 0.0042$, $H_0 = 66.73 \pm 1.60$ km/s/Mpc, $S_8 = 0.867 \pm 0.025$ (4,480 samples; definitive chain `results/mcmc_chains/tep_hiclass_suite.*`).
4. **Hubble tension:** Homogeneous background stays Planck-compatible; local $H_0 \approx 73$ km/s/Mpc is interpreted as environment-dependent clock-transport bias (Paper 11).

---

## The TEP Research Program

| Paper | Repository | Title | DOI |
|-------|-----------|-------|-----|
| **Paper 0** | [TEP](https://github.com/matthewsmawfield/TEP) | Temporal Equivalence Principle: Dynamic Time & Emergent Light Speed | [10.5281/zenodo.16921911](https://doi.org/10.5281/zenodo.16921911) |
| **Paper 15** | [TEP-EFA](https://github.com/matthewsmawfield/TEP-EFA) | Temporal Shear in the Earth Flyby Anomaly | [10.5281/zenodo.19454863](https://doi.org/10.5281/zenodo.19454863) |
| **Paper 17** | [TEP-LLR](https://github.com/matthewsmawfield/TEP-LLR) | Lunar Laser Ranging and the Nordtvedt Effect | [10.5281/zenodo.19446029](https://doi.org/10.5281/zenodo.19446029) |
| **Paper 18** | **TEP-HC** (This repo) | EFT Mapping and CMB Acoustic Peak Preservation | — |
| **Paper 19** | [TEP-LENS](https://github.com/matthewsmawfield/TEP-LENS) | Geometric Route-Closure Test in Multiply-Imaged Supernovae | — |

## Repository Structure

```text
TEP-HC/
├── data/
│   ├── hi_class/            # hi_class input parameters
│   └── cobaya/              # Cobaya MCMC configuration
├── external/
│   ├── hi_class/hi_class/   # Compiled hi_class with native tep_mode
│   └── patches/             # hiclass_tep_native.patch (applied on install)
├── logs/                    # Execution logs
├── manuscripts/             # Series mirror + generated outputs
├── results/                 # MCMC chains, figures, synthesis
├── scripts/
│   ├── steps/               # Numbered pipeline (00–09)
│   ├── run_all.py           # Full pipeline orchestrator
│   ├── generate_figures.py  # Manual figure generation (post-pipeline)
│   └── generate_site_pdf.py
├── site/
│   └── components/          # HTML source of truth
├── README.md
├── CITATION.cff
├── VERSION.json
├── version.txt
├── zenodo.txt
└── requirements.txt
```

## Installation

```bash
git clone https://github.com/matthewsmawfield/TEP-HC.git
cd TEP-HC
pip install -r requirements.txt
```

## Reproduction Pipeline

```bash
# Full pipeline (auto-installs Cobaya + Planck likelihoods on step 01)
python scripts/run_all.py

# Quick smoke test: skip hi_class/Planck install (step 1), MCMC (7), posteriors (8)
python scripts/run_all.py --skip-steps 1,7,8

# Stop after Jordan-frame scan (no Cobaya/MCMC)
python scripts/run_all.py --stop-step 5

# Generate publication figures (requires pipeline results in results/)
python scripts/generate_figures.py

# Build manuscript from HTML
cd site && npm ci && npm run build:markdown
# Output: 18-TEP-HC-v0.1-Geneva.md

# Deploy static site
./deploy.sh
```

## Pipeline Steps

| Step | Module | Description |
|------|--------|-------------|
| 00 | `step_00_setup` | Environment check |
| 01 | `step_00b_install` | Install Cobaya + Planck 2018 likelihoods + hi_class (native TEP patch) |
| 02 | `step_02_background` | TEP-modified background evolution $H(z)$ |
| 03 | `step_03_alpha_functions` | Bellini–Sawicki $\alpha_i$ mapping (archived reference) |
| 04 | `step_04_cmb_spectra` | hi_class CMB spectra vs $\Lambda$CDM at Planck best-fit |
| 05 | `step_04b_jordan_frame` | Jordan-frame acoustic-scale dual scan |
| 06 | `step_05_cobaya` | Generate Cobaya YAML configs (`data/cobaya/`) |
| 07 | `step_06_mcmc` | Execute Cobaya MCMC |
| 08 | `step_07_posteriors` | Posterior analysis and Gelman–Rubin diagnostics |
| 09 | `step_08_synthesis` | Results synthesis JSON and summary markdown |

Figures are generated separately via `python scripts/generate_figures.py` and copied into the static site by `cd site && npm run build`.

## Citation

```bibtex
@article{tep_hc_paper,
  title={Temporal Equivalence Principle: EFT Mapping and CMB Acoustic Peak Preservation},
  author={Smawfield, Matthew Lukin},
  year={2026},
  note={Preprint v0.1 (Geneva)},
  url={https://github.com/matthewsmawfield/TEP-HC}
}
```

---

## Open Science Statement

These are working preprints shared in the spirit of open science—all manuscripts, analysis code, and configuration files are openly available under Creative Commons licenses to encourage replication. Feedback and collaboration are warmly invited.

---

**Contact:** matthew@mlsmawfield.com  
**ORCID:** [0009-0003-8219-3159](https://orcid.org/0009-0003-8219-3159)
