# Temporal Equivalence Principle: Native hi_class Conformal Implementation, Linear Perturbation Closure, and CMB Acoustic Peak Preservation

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20682752.svg)](https://doi.org/10.5281/zenodo.20682752)
[![License: CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)

![TEP-HC: Native hi_class Conformal Implementation, Linear Perturbation Closure, and CMB Acoustic Peak Preservation](site/public/image.webp)

**Author:** Matthew Lukin Smawfield  
**Version:** v0.3 (Cambridge)  
**First published:** 8 June 2026  
**Website:** [https://mlsmawfield.com/tep/hc](https://mlsmawfield.com/tep/hc)  
**Paper Series:** TEP Series: Paper 18 (hi_class Cosmology)

## Abstract

Standard cosmology explains the Cosmic Microwave Background (CMB) acoustic peaks, the pre-recombination sound horizon, and the thermal scaling relevant to Big Bang Nucleosynthesis (BBN) within an FLRW expansion history conventionally extrapolated toward a Big Bang singularity. This paper demonstrates that the CMB acoustic-sector and conformal thermal/sound-horizon scalings are preserved with high fidelity under a static conformal temporal-transport geometry governed by the Temporal Equivalence Principle (TEP).

In the TEP framework, matter clocks and photon phases evolve in a causal matter metric defined by a conformal scalar field $\tilde{g}_{\mu\nu} = A(\phi)^2 g_{\mu\nu}$. Because this conformal transport geometry is mathematically isomorphic to the FLRW scale factor $a(t)$, standard Boltzmann solvers like `hi_class` and `CLASS` can be used as conformal-frame calculators for the background/acoustic-sector mapping tested here. The parameter traditionally identified as Dark Energy ($\Omega_\Lambda$) is operationally reinterpreted within this implementation as the homogeneous temporal-shear background contribution filling the same background budget slot, $\Omega_\phi$.

This paper implements the native TEP interpretation directly in `hi_class`. Within the broader TEP interpretation, by recognizing that the spatial metric does not stretch, the "Big Bang" is reinterpreted not as a physical density singularity, but as an observational Temporal Horizon—an asymptotic boundary where the conformal clock-rate field $A(\phi) \to 0$. Direct Boltzmann integration verifies this background/acoustic mathematical isomorphism, confirming that the static conformal geometry preserves the pre-recombination sound horizon to parts-per-million and leaves the acoustic-peak morphology intact without invoking early-universe spatial expansion.

Beyond the background mapping, the paper closes the linear pure-conformal scalar perturbation sector by deriving the runtime Bellini–Sawicki functions $\alpha_M=-2\alpha_A$, $\alpha_B=2\alpha_A$, $\alpha_K=-5\alpha_A^2$, and $\alpha_T=0$, for which the physical no-ghost discriminant satisfies $D=\alpha_K+\frac{3}{2}\alpha_B^2=\alpha_A^2$. An active-perturbation hi_class run evolving $\delta\phi$ through the full Einstein–Boltzmann hierarchy produces posteriors statistically indistinguishable from the background-only chain, demonstrating that the implemented linear pure-conformal scalar perturbation sector is stable and observationally negligible at the current homogeneous-amplitude bound.

A joint `hi_class` Cobaya MCMC (Planck 2018 low-$\ell$ TT/EE + lensing + BAO + Pantheon+) tests the screened TEP conformal background within the native hi_class implementation, while companion TEP-C0 (Paper 26) nested sampling over Pantheon+ provides robust quantitative evidence that the screened TEP conformal geometry matches the Pantheon+ distance-redshift relation with a Bayes factor of 131.6 in favour of TEP M1, without treating late-time acceleration as primitive spatial acceleration. Within the TEP framework, the Hubble tension is interpreted as a late-time, environment-dependent clock-transport effect (Paper 11) caused by the mass-screening of the scalar field, rather than through a crisis in early-universe physics.

## Key Results

1. **Native `tep_mode`:** $H_{\rm TEP}(z) = H_{\Lambda\rm CDM}(z)\,M(z)$ with $f_T(z)=\ln(1+z)\exp[-(z/z_T)^{n_T}]$, patched into hi_class `background.c`.
2. **Sound horizon:** $r_s^{\rm TEP}/r_s^{\Lambda\rm CDM} = 0.999994$; acoustic-peak morphology unchanged at recombination.
3. **Joint MCMC:** $\epsilon_T = 0.0056 \pm 0.0043$, $H_0 = 66.63 \pm 1.70$ km/s/Mpc, $S_8 = 0.870 \pm 0.028$ (19,033 post-burn-in samples; primary chain `results/mcmc_chains/tep_hiclass_suite.*`).
4. **Hubble tension:** Homogeneous background stays Planck-compatible; local $H_0 \approx 73$ km/s/Mpc is interpreted as environment-dependent clock-transport bias (Paper 11).

---

## The TEP Research Program

| Paper | Repository | Title | DOI |
|-------|-----------|-------|-----|
| **Paper 0** | [TEP](https://github.com/matthewsmawfield/TEP) | Temporal Equivalence Principle: Dynamic Time & Emergent Light Speed | [10.5281/zenodo.16921911](https://doi.org/10.5281/zenodo.16921911) |
| **Paper 15** | [TEP-EFA](https://github.com/matthewsmawfield/TEP-EFA) | Temporal Shear in the Earth Flyby Anomaly | [10.5281/zenodo.19454863](https://doi.org/10.5281/zenodo.19454863) |
| **Paper 17** | [TEP-LLR](https://github.com/matthewsmawfield/TEP-LLR) | Lunar Laser Ranging and the Nordtvedt Effect | [10.5281/zenodo.19446029](https://doi.org/10.5281/zenodo.19446029) |
| **Paper 18** | **TEP-HC** (This repo) | Native hi_class Conformal Implementation, Linear Perturbation Closure, and CMB Acoustic Peak Preservation | [10.5281/zenodo.20682752](https://doi.org/10.5281/zenodo.20682752) |
| **Paper 26** | [TEP-C0](https://github.com/matthewsmawfield/TEP-C0) | Covariant Alternative to Cosmic Expansion (Pantheon+ + full Planck) | [10.5281/zenodo.20370144](https://doi.org/10.5281/zenodo.20370144) |
| **Paper 19** | [TEP-LENS](https://github.com/matthewsmawfield/TEP-LENS) | Geometric Route-Closure Test in Multiply-Imaged Supernovae | — |

## Repository Structure

```text
TEP-HC/
├── data/
│   └── cobaya/              # Cobaya MCMC configuration (regenerated by step 06)
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
# Output: 18-TEP-HC-v0.3-Cambridge.md

# Build static site (figures copied from results/figures/)
cd site && npm ci && npm run build
```

MCMC chains (`results/mcmc_chains/`) are gitignored because each run is ~5.5 h on a typical workstation. Reproduce with `python scripts/run_all.py` (or `--start-step 6 --stop-step 8` after a prior full install). Summary statistics are committed in `results/07_mcmc_summary_full.json`.

## Pipeline Steps

| Step | Module | Description |
|------|--------|-------------|
| 00 | `step_00_setup` | Environment check |
| 01 | `step_00b_install` | Install Cobaya + Planck 2018 likelihoods + hi_class (native TEP patch) |
| 02 | `step_02_background` | TEP-modified background evolution $H(z)$ |
| 03 | `step_03_alphas` | Bellini–Sawicki $\alpha_i$ mapping (archived reference) |
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
  title={Temporal Equivalence Principle: Native hi_class Conformal Implementation, Linear Perturbation Closure, and CMB Acoustic Peak Preservation},
  author={Smawfield, Matthew Lukin},
  year={2026},
  note={Preprint v0.3 (Cambridge)},
  url={https://mlsmawfield.com/tep/hc}
}
```

---

## Open Science Statement

These are working preprints shared in the spirit of open science—all manuscripts, analysis code, and configuration files are openly available under Creative Commons licenses to encourage replication. Feedback and collaboration are warmly invited.

---

**Contact:** matthew@mlsmawfield.com  
**ORCID:** [0009-0003-8219-3159](https://orcid.org/0009-0003-8219-3159)