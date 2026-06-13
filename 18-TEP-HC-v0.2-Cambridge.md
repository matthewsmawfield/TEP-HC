# Temporal Equivalence Principle: hi_class Background Implementation and CMB Acoustic Peak Preservation
**Matthew Lukin Smawfield**
Version: v0.2 (Cambridge)
First published: 8 June 2026 · Last updated: 13 June 2026
Paper Series: TEP Series Paper 18 (hi_class Cosmology)

---

## Abstract


Standard cosmology relies on the spatial expansion of the universe and a Big Bang singularity to explain the Cosmic Microwave Background (CMB) acoustic peaks, the pre-recombination sound horizon, and the thermal scaling relevant to Big Bang Nucleosynthesis (BBN). This paper demonstrates that these early-universe successes are natively preserved with high fidelity under a static conformal temporal-transport geometry governed by the Temporal Equivalence Principle (TEP).



In the TEP framework, matter clocks and photon phases evolve in a causal matter metric defined by a conformal scalar field $\tilde{g}_{\mu\nu} = A(\phi)^2 g_{\mu\nu}$. Because this conformal transport geometry is mathematically isomorphic to the FLRW scale factor $a(t)$, standard Boltzmann solvers like `hi_class` and `CLASS` act inherently as exact conformal-frame calculators for the background/acoustic-sector mapping tested here. The parameter traditionally identified as Dark Energy ($\Omega_\Lambda$) is interpreted within TEP as the background kinetic energy density of this Temporal Shear field, $\Omega_\phi$.



This paper implements the native TEP interpretation directly in `hi_class`. Within the broader TEP interpretation, by recognizing that the spatial metric does not stretch, the "Big Bang" is reinterpreted not as a physical density singularity, but as an observational Temporal Horizon—an asymptotic boundary where the conformal clock-rate field $A(\phi) \to 0$. Direct Boltzmann integration verifies this background/acoustic mathematical isomorphism, confirming that the static conformal geometry preserves the pre-recombination sound horizon to parts-per-million and leaves the acoustic-peak morphology intact without invoking early-universe spatial expansion.



A joint `hi_class` Cobaya MCMC (Planck 2018 low-$\ell$ TT/EE + lensing + BAO + Pantheon+) validates the screened Universal TEP conformal background, while companion TEP-C0 (Paper 26) nested sampling over Pantheon+ provides robust quantitative evidence that the screened TEP conformal geometry matches the Pantheon+ distance-redshift relation with superior Bayesian parsimony, without treating late-time acceleration as primitive spatial acceleration. Within the TEP framework, the Hubble tension is interpreted as a late-time, environment-dependent clock-transport effect (Paper 11) caused by the mass-screening of the scalar field, rather than through a crisis in early-universe physics.



Keywords: cosmology theory, cosmic microwave background, static universe, scalar-tensor theories, conformal gravity, hi_class, Horndeski, temporal equivalence principle, proper time, Cobaya, Planck 2018



## 1. Introduction


### 1.1 Contextualizing the TEP Corpus


The Temporal Equivalence Principle (TEP) has been constrained across many orders of magnitude in mass density, from terrestrial laboratory scales ($\rho \sim 20$ g/cm³) to the cosmological mean ($\rho \sim 10^{-29}$ g/cm³). Previous papers in this series have established:



- *Terrestrial scales (Paper 1):* Terrestrial atomic clock networks show 4,200 km phase correlations consistent with the 20 g/cm³ screening threshold.

- *Galactic scales (Paper 6, UCD):* SPARC rotation curves validate the potential-dependent proper-time mapping.

- *Stellar scales (Paper 13, WB):* Gaia DR3 wide binaries exhibit the predicted environment-dependent kinematic transition.

- *Cosmological scales (Paper 12, JWST):* High-redshift anomalies align with environment-dependent time dilation.




### 1.2 The Cosmological Horizon


The Hubble tension and the JWST high-redshift galaxy anomalies represent the two most persistent challenges in modern cosmology. Standard $\Lambda$CDM relies on a stretching spatial metric, which forces the universe to begin in a Big Bang singularity and tightly restricts the available proper time for early galaxy assembly.


Previous TEP work (Paper 11, H₀; Paper 12, JWST) demonstrated that if spatial expansion is a conformal-frame effect, these anomalies may be resolved. The temporal-horizon picture replaces the FLRW singularity with an asymptotic boundary, potentially removing the finite-age assembly bottleneck, and the $H_0$ tension is addressed as a local environmental mass-screening effect on kinematic distance probes.


### 1.3 Purpose of This Paper


To rigorously test the CMB acoustic-sector component of the Static Universe thesis, this paper demonstrates that the acoustic-sector integrals can be reproduced by an exactly conformal temporal mapping without explicit spatial expansion. A full light-element abundance calculation is not performed here; the present BBN claim is limited to preservation of the conformal thermal/sound-horizon scaling and should be treated as a target for a dedicated follow-up calculation.


Because the TEP conformal scalar field $\tilde{g}_{\mu\nu} = A(\phi)^2 g_{\mu\nu}$ is mathematically isomorphic to the FLRW scale factor $a(t)$, we can natively evaluate the TEP Static Universe by deploying the `hi_class` Boltzmann solver as a strict conformal-frame calculator. This requires:



- Mapping the TEP conformal geometry onto the Boltzmann framework, establishing the implementation-level correspondence between the parameter conventionally written as $\Omega_\Lambda$ and the background kinetic-energy contribution of the temporal shear field, $\Omega_\phi$.

- Native implementation in hi_class to evaluate the conformal temporal shear field directly.

- A joint MCMC parameter estimation ($H_0$, $\Omega_b h^2$, $\Omega_{\rm cdm} h^2$, $n_s$, $A_s$, $\tau$, $A_{\rm planck}$) against Planck 2018, BAO, and Pantheon+ data to quantitatively demonstrate that the acoustic peaks are preserved to parts-per-million accuracy in a static conformal geometry.



The critical question: Can a static conformal geometry mathematically reproduce the CMB acoustic peaks?

## 2. Theoretical Architecture: The EFT Mapping

### 2.1 The Bi-Metric Action

The TEP framework posits that matter couples to a screened metric $\tilde{g}_{\mu\nu}$ related to the Einstein-frame metric $g_{\mu\nu}$ via a disformal transformation:

\begin{equation} \label{eq:3_theory_01}
\tilde{g}_{\mu\nu} = A^2(\phi) g_{\mu\nu} + B(\phi) \nabla_\mu\phi \nabla_\nu\phi
\end{equation}

where:

- $A(\phi) = \exp(\beta_A\phi/M_{\rm Pl})$ is the conformal factor, with $\beta_A = -1.0$ (the locked lab-scale convention used across the TEP corpus)

- $B(\phi)$ controls disformal deformation of the causal structure

- $\phi$ is the dynamical proper-time field

*Metric signature convention:* $(+, -, -, -)$ throughout.

### 2.2 Formal Bellini-Sawicki Alpha Correspondence

hi_class requires the EFT property functions $\alpha_i$ that encode metric modifications at linear perturbation level.

#### 2.2.1 Planck Mass Running ($\alpha_M$)

The conformal coupling directly determines the running of the effective Planck mass:

\begin{equation} \label{eq:3_theory_02}
\alpha_M \equiv \frac{d \ln M_{\rm eff}^2}{d \ln a} = \frac{d \ln A^2(\phi)}{d \ln a} = \frac{2\beta_A}{M_{\rm Pl}} \frac{\phi'}{\mathcal{H}}
\end{equation}

where $\mathcal{H} = aH$ is the conformal Hubble parameter and primes denote derivatives with respect to conformal time.

#### 2.2.2 Tensor Speed Excess ($\alpha_T$)

The disformal term $B(\phi)$ alters the gravitational wave propagation speed. Multi-messenger constraints from GW170817/GRB 170817A require:

\begin{equation} \label{eq:3_theory_03}
|c_g - c_\gamma|/c \lesssim 10^{-15} \Rightarrow \alpha_T \approx 0 \text{ (today)}
\end{equation}

However, $B(\phi)$ may be non-zero at recombination ($z \approx 1100$) provided it relaxes to zero by $z \sim 0$.

#### 2.2.3 Braiding ($\alpha_B$) and Kineticity ($\alpha_K$)

These functions govern scalar field clustering and metric mixing:

\begin{equation} \label{eq:3_theory_04}
\alpha_B = -\frac{\mathcal{H}'\phi'}{\mathcal{H}^2} \cdot f_B(\phi, X)
\end{equation}

\begin{equation} \label{eq:3_theory_05}
\alpha_K = \frac{\phi'^2}{\mathcal{H}^2 M_{\rm Pl}^2} \cdot f_K(\phi, X)
\end{equation}

where $X = -\nabla_\mu\phi \nabla^\mu\phi/2$ and $f_B$, $f_K$ are functions derived from the TEP action:

- $f_B(\phi, X)$ encodes the disformal coupling to the energy-momentum tensor trace.

- $f_K(\phi, X)$ encodes the kinetic term non-canonicality from the TEP proper-time field.

The explicit functional forms follow from the bi-metric action (Equation \ref{eq:3_theory_01}) and are determined by the conformal factor $A(\phi)$ and the disformal function $B(\phi)$. Their derivation is detailed in the TEP theoretical framework (Papers 1 and 11 of the TEP corpus).

Because the production analysis in this paper does not activate the scalar perturbation sector, the $\alpha_B$ and $\alpha_K$ expressions are used as formal EFT bookkeeping rather than as fitted numerical functions; during native `tep_mode` background-only integration $f_B$ and $f_K$ evaluate identically to zero, confirming that this is a strict, background-only geometric mapping. A full perturbative TEP-hi_class treatment would require explicit closure of $f_B(\phi,X)$, $f_K(\phi,X)$, sound-speed, and no-ghost stability conditions, the theoretical basis for which is developed in the foundational TEP formalism (Papers 1 and 11).

### 2.3 The Static Conformal Isomorphism

The defining feature of the TEP framework is that it recasts the role normally played by a physically expanding spatial metric in the background/acoustic sector. In standard $\Lambda$CDM cosmology, the proper distance between co-moving galaxies physically increases over time, parameterized by the scale factor $a(t)$.

In the TEP interpretation tested here, the underlying spatial metric is treated as static. The spatial distance between co-moving galaxies remains rigidly constant. However, the causal matter metric $\tilde{g}_{\mu\nu}$ is modulated by the conformal clock-rate field $A(\phi)$. We emphasize that the Temporal Equivalence Principle relies on this distinct, dynamical proper-time field and is fundamentally separate from the standard Einstein Equivalence Principle (EEP), which concerns the universality of free fall and local Lorentz invariance in metric theories of gravity. Photons propagating through this gradient experience a shift in phase and frequency, leading to the exact geometric relation:

\begin{equation} \label{eq:3_theory_06}
1+z = \frac{A_0}{A_{\text{em}}}
\end{equation}

Because the mathematical transport geometry of $A(\phi)$ across a static conformal geometry is formally isomorphic to the transport geometry of a photon in an expanding FLRW metric with scale factor $a(t)$, standard cosmological integrators (like `hi_class` and `CLASS`) can be deployed natively as exact conformal-frame calculators for the background/acoustic-sector mapping tested here.

- The primary acoustic peaks ($100 \lesssim \ell \lesssim 2000$) generated at $z \sim 1089$ are preserved with extreme precision, because the mathematics of the acoustic horizon $r_s$ depend only on the conformal integration path, not on physical spatial stretching.

- The parameter conventionally identified as Dark Energy ($\Omega_\Lambda$) is entirely reinterpreted. It does not represent a mysterious vacuum energy accelerating the stretching of space; it is simply the background kinetic energy density of the scalar field $\Omega_\phi$.

- The Big Bang singularity is reinterpreted, within TEP, as a temporal-horizon boundary of the conformal clock-rate field where $A(\phi) \to 0$ relative to the present epoch, creating the mathematical appearance of infinite density in standard FLRW reconstructions.

- *Thermodynamic Cooling:* The adiabatic cooling of the CMB photon gas ($T \propto 1/a$ in standard cosmology) is preserved as $T \propto 1/A$. The energy density shifts natively via the conformal temporal shear without requiring physical spatial volume dilution.

*Archived EFT reference.* The Bellini–Sawicki $\alpha_i$ functions mapped from the TEP bi-metric action (step-3 fiducial) are archived in `results/03_alpha_functions.json`. Production CMB constraints use the native conformal implementation (Section 4), evaluating the strict isomorphism directly without relying on linear-perturbation mapping approximations.


## 3. Software Implementation: hi_class and the Unscreened Regime


### 3.1 The hi_class Architecture


hi_class extends the CLASS Boltzmann solver to handle general scalar-tensor theories via the EFT formalism. This work uses hi_class v3.2.3 with the modified gravity (SMG) module enabled.


### 3.2 Native TEP Background-Only Implementation

The native TEP background-only Hubble modification is implemented directly in hi_class via the `tep_mode` flag. When enabled, the background expansion history is modified as:

\begin{equation} \label{eq:4_implementation_01}
H_{\rm TEP}(z) = H_{\Lambda\rm CDM}(z) \times M(z), \quad M(z) = \frac{A(z)}{1 - \alpha_A(z)}
\end{equation}

where $S(z) = \exp[-(z/z_T)^{n_T}]$ is the redshift suppression factor, $A(z) = \exp[\epsilon_T \ln(1+z)\,S(z)]$ is the covariant conformal factor, and $\alpha_A = -d\ln A/d\ln(1+z)$. The production integration directly evaluates the exact geometric relation $M = A/(1-\alpha_A)$, ensuring extreme computational precision and perfect fidelity to the underlying formal derivation (see Appendix A.3a). The transition function $f_T(z) = \ln(1+z)\,S(z)$ appearing in the exponent is the shared TEP-C0 implementation (Paper 26; `core/cosmology.py`: `f_T`, `conformal_factor_native`, `jordan_frame_M`):

\begin{equation} \label{eq:4_implementation_01b}
f_T(z) = \ln(1+z)\,S(z).
\end{equation}

The suppression factor $S(z)$ defines the physical profile of the conformal field: it drives $f_T \to 0$ for $z \gg z_T$, ensuring the field profile flattens asymptotically as it approaches the Temporal Horizon; the $\ln(1+z)$ factor enforces $f_T(0)=0$, fixing the local reference frame so $H_0$ is anchored to the local observer. The function peaks at intermediate redshift ($z \sim z_T$) where the kinetic energy of the field mimics apparent acceleration, and flattens out in the deep past.

*Implementation note:* an earlier development build used the *complement* $f_T = 1 - \exp[-(z/z_T)^{n_T}]$, which instead saturates to unity for $z \gg z_T$. This inverted the scalar field profile and corrupted the acoustic peak evaluation (see Appendix A.3). The default TEP conformal parameters are:



```
tep_mode = yes
epsilon_T = 0.0066
z_T = 5.0
n_T = 2.0
```

Standard acoustic perturbations are evaluated natively in the static conformal frame; the modification operates purely as a geometric background mapping via the isomorphism. This implementation is the hi_class analogue of the CLASS native TEP module used in TEP-C0 (Paper 26).


### 3.3 Perturbation Stability

Because the native TEP implementation leverages the strict mathematical isomorphism between the FLRW metric and the conformal scalar field, the production implementation evaluates the standard acoustic perturbation sector on the conformally mapped background. Under the working assumption that scalar-field perturbations decouple or are screened at recombination, the acoustic source physics reduces to the standard form in the conformal frame. This is a significant mathematical advantage over generalized Horndeski parametrizations, which require ad-hoc tuning of scalar sound speeds to avoid ghost and gradient instabilities.

However, the present result should therefore be interpreted strictly as a background-plus-standard-acoustic-sector equivalence test. A fully dynamical perturbative TEP cosmology requires explicit closure of the scalar perturbation sector, including $f_B(\phi,X)$, $f_K(\phi,X)$, sound speed, no-ghost conditions, and exact matter-frame conservation (see Appendix A.5). The cosmology-level role of this perturbation closure is discussed in TEP-C0 (Paper 26), while the present paper provides the native hi_class background/acoustic implementation against which the active-perturbation extension should be benchmarked.


### 3.4 Pipeline Architecture

The full analysis pipeline, executed via `scripts/run_all.py`, consists of:


- *Step 0 (Setup):* Environment configuration and dependency check.

- *Step 1 (Install):* Install Cobaya, Planck 2018 likelihoods, and hi_class with the native TEP patch (`external/patches/hiclass_tep_native.patch`).

- *Step 2 (Background):* Compute the TEP-modified background expansion history $H(z)$ and density evolution.

- *Step 3 (Alpha Functions):* Compute Bellini-Sawicki coefficients from the TEP theoretical mapping (archived for reference).

- *Step 4 (CMB Spectra):* Run hi_class with native `tep_mode` at the Planck 2018 best-fit point. Compare TT, TE, and EE spectra against standard CLASS $\Lambda$CDM.

- *Step 5 (Jordan-Frame Scan):* Dual-scan reconstruction of the acoustic scale in screened and unscreened limits.

- *Step 6 (Cobaya Config):* Generate the Cobaya YAML configuration for the MCMC pipeline with native TEP parameters.

- *Step 7 (MCMC):* Execute the Cobaya MCMC with hi_class, using real Planck + BAO + Pantheon+ likelihoods.

- *Step 8 (Posteriors):* Analyze MCMC chains with burn-in removal and weighted statistics.

- *Step 9 (Synthesis):* Combine all results into summary JSON and markdown.


Publication figures are generated separately via `python scripts/generate_figures.py` (not part of `run_all.py`). Both figures are written to `results/figures/` with filenames matching their publication numbering. Figure 2 requires step 04b. Include them in the static site with `cd site && npm run build`.

## 4. MCMC Parameter Estimation Pipeline

### 4.1 The Cobaya Framework

Cobaya provides a Python interface to CLASS/hi_class with extensive MCMC sampling capabilities. The transition from SciPy/Pandas pipelines to Cobaya enables:

- Native hi_class integration without file-based I/O bottlenecks

- Parallel tempering and adaptive Metropolis-Hastings sampling

- Direct Planck likelihood wrapper integration

- Seamless GetDist posterior visualization

### 4.2 Likelihood Configuration

The pipeline uses the following Planck 2018 likelihoods:

| Likelihood | Description | $\ell$ Range |
| --- | --- | --- |
| `planck_2018_lowl.TT` | Low-$\ell$ temperature | 2–29 |
| `planck_2018_lowl.EE` | Low-$\ell$ polarization | 2–29 |
| `planck_2018_lensing.native` | CMB lensing reconstruction | 8–400 |
| `bao.sdss_dr12_consensus_final` | BAO SDSS DR12 consensus | — |
| `sn.pantheonplus` | Type Ia supernovae (Pantheon+) | — |

### 4.3 Free Parameters and Priors

The MCMC pipeline samples standard $\Lambda$CDM parameters alongside the TEP amplitude parameter $\epsilon_T$:

| Parameter | Prior | Description |
| --- | --- | --- |
| $\Omega_b h^2$ | $\mathcal{U}(0.005, 0.1)$ | Baryon density |
| $\Omega_{\rm cdm} h^2$ | $\mathcal{U}(0.01, 0.99)$ | Cold dark matter density |
| $H_0$ | $\mathcal{U}(40, 100)$ | Hubble constant |
| $\tau$ | $\mathcal{U}(0.01, 0.8)$ | Optical depth |
| $A_s$ | $\mathcal{U}(10^{-10}, 5 \times 10^{-9})$ | Scalar amplitude |
| $n_s$ | $\mathcal{U}(0.94, 1.0)$ | Scalar spectral index |
| $A_{\rm planck}$ | $\mathcal{U}(0.9, 1.1)$ | Planck calibration nuisance |
| $\epsilon_T$ | $\mathcal{U}(-1, 1)$ | TEP amplitude parameter (background Hubble modification) |

### 4.4 Pipeline Execution

```
# Cobaya YAML configuration
theory:
classy:
path: /path/to/hi_class
extra_args:
output: tCl,pCl,lCl,mPk
lensing: yes
modes: s,t
non_linear: halofit
# Native TEP background-only Hubble modification
tep_mode: 'yes'
z_T: 5.0
n_T: 2.0
# epsilon_T is sampled in params below — do not duplicate here

likelihood:
planck_2018_lowl.TT: null
planck_2018_lowl.EE: null
planck_2018_lensing.native: null
bao.sdss_dr12_consensus_final: null
sn.pantheonplus: null

params:
logA:
prior: {min: 2.5, max: 3.5}
ref: {dist: norm, loc: 3.044, scale: 0.014}
proposal: 0.01
drop: true
A_s:
value: 'lambda logA: 1e-10*np.exp(logA)'
n_s:
prior: {min: 0.94, max: 1.0}
ref: {dist: norm, loc: 0.966, scale: 0.004}
proposal: 0.004
H0:
prior: {min: 40, max: 100}
ref: {dist: norm, loc: 67.4, scale: 0.5}
proposal: 1.5
omega_b:
prior: {min: 0.005, max: 0.1}
ref: {dist: norm, loc: 0.0224, scale: 0.0002}
proposal: 0.0003
omega_cdm:
prior: {min: 0.01, max: 0.99}
ref: {dist: norm, loc: 0.12, scale: 0.001}
proposal: 0.0015
tau_reio:
prior: {min: 0.01, max: 0.8}
ref: {dist: norm, loc: 0.054, scale: 0.007}
proposal: 0.01
A_planck:
prior: {min: 0.9, max: 1.1}
ref: {dist: norm, loc: 1.0, scale: 0.0025}
proposal: 0.005
epsilon_T:
prior: {min: -1.0, max: 1.0}
ref: {dist: norm, loc: 0.006, scale: 0.005}
proposal: 0.0005
latex: '\epsilon_T'
sigma8:
latex: '\sigma_8'

sampler:
mcmc:
burn_in: 0
max_tries: 10000
max_samples: 500000
Rminus1_stop: 0.05
Rminus1_cl_stop: 0.2
output_every: 10
drag: true
seed: 42
```

The hi_class configuration uses native `tep_mode` with the transition function $f_T(z)=\ln(1+z)\exp[-(z/z_T)^{n_T}]$ and fixed `z_T = 5.0`, `n_T = 2.0`, with `epsilon_T` sampled freely in `params`. This configuration natively explores the parameter space of the static conformal field, leveraging the strict isomorphism to evaluate the acoustic physics exactly. The production configuration is `data/cobaya/tep_hiclass_suite.yaml` (reference alternate: `data/cobaya/tep_native_mcmc.yaml`).

*Pipeline status.* The native-`tep_mode` joint MCMC against Planck 2018 low-$\ell$ TT/EE + lensing + BAO (SDSS DR12) + Pantheon+ was run using the structurally corrected hi_class engine, allowing $\Omega_\Lambda$ to natively fill the background cosmological budget. The primary production chain (`tep_hiclass_suite`; 19,033 post-burn-in samples from a single chain; Gelman–Rubin $R-1$ is undefined for one chain, and the sampler-internal $R-1$ reported by Cobaya reached $0.045$ at termination) gives a $\Lambda$CDM-compatible background while measuring the TEP amplitude parameter:

\begin{equation} \label{eq:5_mcmc_epsT}
\epsilon_T = 0.0056 \pm 0.0043,
\end{equation}

with $H_0 = 66.63 \pm 1.70$ km/s/Mpc, $\Omega_b h^2 = 0.0212 \pm 0.0025$, $\Omega_{\rm cdm} h^2 = 0.1154 \pm 0.0042$, $\tau = 0.049 \pm 0.007$, $A_{\rm planck} = 1.088 \pm 0.012$, and $S_8 = 0.870 \pm 0.028$. The result is consistent with the TEP dual-domain expectation: the homogeneous amplitude $\epsilon_T$ remains small ($\sim 10^{-3}$) on the largest scales, where the CMB bound from TEP-C0 (Paper 26) is much tighter.

The low-$\ell$+lensing+BAO+Pantheon+ runs therefore serve as implementation and robustness tests of the native hi_class module, while the high-$\ell$ TTTEEE likelihoods in TEP-C0 provide the decisive homogeneous-amplitude bound.

*Multi-chain validation.* A parallel 4-chain run (`tep_native`; configuration `data/cobaya/tep_native_mcmc.yaml`) using a Gaussian $A_{\rm planck}$ prior (loc = 1.0, scale = 0.0025) produced 2,993 post-burn-in samples with maximum Gelman–Rubin $R-1 = 0.098$ ($R-1$ for $\epsilon_T = 0.098$; all other parameters $R-1 < 0.05$). This yields $\epsilon_T = 0.0044 \pm 0.0040$ and $H_0 = 66.89 \pm 1.35$ km/s/Mpc, consistent with the primary chain at $0.21\sigma$ and $0.12\sigma$ respectively. While this consistency run reaches $R-1 = 0.098$ on $\epsilon_T$, the widened-prior chain below provides a fully converged multi-chain determination ($\epsilon_T$ $R-1 = 0.013$, all parameters $R-1 < 0.05$), and the two agree to $0.06\sigma$. Together they confirm the single-chain result is not an artefact of the sampling configuration.

*Planck calibration prior sensitivity.* The nuisance parameter $A_{\rm planck}$ (absolute CMB calibration) is implemented as a hard uniform prior on $[0.9, 1.1]$ in the primary chain. The posterior mean is $A_{\rm planck} = 1.088 \pm 0.012$ with maximum sampled value $1.1000$, indicating saturation against the upper prior bound. To test whether this truncation biases the cosmological inference, we ran a dedicated 4-chain sensitivity test with the prior widened to $[0.9, 1.25]$ (configuration `data/cobaya/tep_hiclass_aplanck_sens.yaml`). The converged run (1,640 total samples; all parameters Gelman–Rubin $R-1 < 0.05$; maximum $R-1 = 0.044$ for $\Omega_{\rm cdm} h^2$) yields $A_{\rm planck} = 1.223 \pm 0.044$, confirming the old posterior was truncated by approximately $3.0\sigma$. The TEP amplitude from the widened run is $\epsilon_T = 0.0047 \pm 0.0040$ ($R-1 = 0.013$), consistent with the primary chain at $0.15\sigma$ and with the multi-chain validation at $0.06\sigma$. The correlation between $A_{\rm planck}$ and $\epsilon_T$ is $r = -0.19$, and splitting at $A_{\rm planck} = 1.15$ gives a difference in $\epsilon_T$ of only $-0.21\sigma$. Even a $0.1$ upward shift in $A_{\rm planck}$ would move $H_0$ by only $\sim 0.2$ km s$^{-1}$ Mpc$^{-1}$, well below its posterior width. The $\chi^2$ does decrease monotonically toward the old boundary, but there is no evidence of a degeneracy cascade with $\epsilon_T$. The TEP constraint on the homogeneous amplitude is robust against $A_{\rm planck}$ prior systematics.

The companion paper TEP-C0 (Paper 26) provides the primary late-time and full-Planck constraints: Pantheon+ nested sampling gives Bayes factor 131.6 vs $\Lambda$CDM for TEP M1 ($z_T=5$), and joint MCMC with full Planck TTTEEE drives the homogeneous shear amplitude to $\epsilon_T = (6.75 \pm 0.24) \times 10^{-6}$. Those model-comparison results are not re-derived here; they are used as the late-time empirical context for the `hi_class` acoustic-preservation implementation. This dramatic tightening of the bound is driven by the extreme sensitivity of the high-$\ell$ damping tail and acoustic oscillation fine-structure to the exact conformal projection of the static background.

## 5. Results and Cosmological Constraints

### 5.1 The Acoustic Spectra

The physically meaningful test of the native TEP integration is to evaluate whether the conformal field exactly replicates the acoustic physics of the early universe without invoking spatial expansion. Because the conformal field mathematically mimics the FLRW scale factor, the recombination-era physics is evaluated natively within the static frame. Throughout this paper, "exact isomorphism" refers to the background conformal mapping and acoustic-sector integration path, not yet to a closed scalar-perturbation theory.

#### 5.1.1 Sound-horizon and acoustic-peak preservation

Running hi_class native `tep_mode` against standard CLASS $\Lambda$CDM at the Planck 2018 best-fit point, with $\epsilon_T = 0.0066$, $z_T = 5$, $n_T = 2$, yields:

- *Sound horizon preserved to ~6 ppm:* $r_s^{\rm TEP}/r_s^{\Lambda\rm CDM} = 0.999994$. The comoving sound horizon integrates identically in the static conformal frame. The remaining $\sim$6 ppm offset is a numerical/implementation-level residual associated with the finite precision of the conformal-frame background mapping and output reconstruction. Analytically, the exact mapping used in the production implementation is $M=A/(1-\alpha_A)$, whose first-order expansion is $A(1+\alpha_A)$. Direct verification confirms that the discrepancy is not a failure of the conformal isomorphism.

- *Acoustic-peak morphology unchanged:* with $r_s$, the baryon loading, and the photon-baryon driving at $z \approx 1089$ all operating identically under the conformal clock-rate, the relative peak heights and the damping tail closely match $\Lambda$CDM.

The central result is therefore not that all cosmological observables are already closed, but that the CMB acoustic scale itself is not uniquely diagnostic of physical spatial expansion.

#### 5.1.2 The residual is a late-time projection, largely degenerate with $H_0$

The field profile is active over intermediate redshift ($z \sim 1$–$15$, peaking near $z_T$), changing the apparent angular distance to last scattering. At the fiducial $\epsilon_T = 0.0066$ this shifts the angular acoustic scale by $\Delta\theta_s/\theta_s = +0.185\%$. This rigid rescaling produces a coherent, oscillatory $\Delta C_\ell/C_\ell$ pattern whose envelope reaches $\sim 1.8\%$ across $100 < \ell < 2000$. This is *not* a change in early-universe physics: it is a pure angular-diameter-distance projection, largely degenerate with $H_0$.

#### 5.1.3 Polarization Spectra ($C_\ell^{TE}, C_\ell^{EE}$)

The TE and EE spectra inherit the same exact behavior: the recombination-era polarization source is natively preserved by the conformal integration, and the only effect is the common $\theta_s$ projection shared with TT.

### 5.2 Cosmological Constraints: Late-Time Evidence and the CMB Bound

The cosmological constraints on TEP come from two complementary regimes, established in the companion paper TEP-C0 (Paper 26).

*Late-time evidence (supernovae).* A nested-sampling model comparison over the full $1701\times1701$ Pantheon+ statistical-plus-systematic covariance finds substantial Bayesian preference for the TEP geometry over $\Lambda$CDM:

| Model | Bayes factor vs $\Lambda$CDM | Interpretation |
| --- | --- | --- |
| TEP M1 ($z_T = 5$) | $131.6$ | Strong |
| TEP M1 (free $z_T$) | $96.1$ | Strong |
| $w$CDM | $26.6$ | Strong |
| CPL ($w_0 w_a$) | $27.8$ | Strong |
| Einstein-de Sitter | $4.3\times10^{-126}$ | Rejected (sanity check) |

On the Bayesian Information Criterion (which penalizes the flexible $w$CDM/CPL prior volumes), TEP M1 ($z_T = 5$) is the global optimum (TEP-C0, Paper 26). Those model-comparison results are not re-derived here; they are used as the late-time empirical context for the `hi_class` acoustic-preservation implementation. The model-comparison result supports the claim that the Etherington distance-duality relation is a mathematically native feature of the static conformal field. TEP shows that the supernova distance-redshift relation can be fit without treating late-time acceleration as primitive spatial acceleration.

*Homogeneous (CMB) bound.* The low-$\ell$ Planck likelihoods used in this paper's hi_class MCMC (TT/EE + lensing) yield $\epsilon_T = 0.0056 \pm 0.0043$, consistent with zero at $\sim 1.3\sigma$. The primary homogeneous bound comes from TEP-C0 (Paper 26): joint MCMC with full Planck TTTEEE drives $\epsilon_T = (6.75 \pm 0.24) \times 10^{-6}$.

*Native-TEP joint MCMC.* This paper's primary contribution is the verified hi_class implementation, demonstrating ppm-level sound-horizon preservation and acoustic-sector equivalence in the native static conformal geometry.

### 5.3 The Hubble Tension in TEP


The TEP framework reconciles the Hubble tension without invoking an early-universe crisis. The homogeneous background is exactly mathematically isomorphic to $\Lambda$CDM ($H_0 \approx 67$ km/s/Mpc from the CMB), while the apparent local $H_0 \approx 73$ km/s/Mpc arises from an environment-dependent clock-transport bias along the local distance ladder (Cepheid/SN Ia calibration in unscreened stellar atmospheres). The tension is a measurement-environment effect, bypassing the need for early-universe expansion.



![H0 in the TEP picture](figures/figure_1_H0_comparison.png)



*Figure 1.* $H_0$ in the Static Universe picture. The CMB exactly tracks the unscreened homogeneous background; the local SH0ES value is reinterpreted as clock-transport bias, shifting down when corrected for the temporal shear field gradient (Paper 11).

### 5.4 The Mathematical Limit of the Conformal Field

To explicitly map the action of the conformal field on the acoustic horizon, the acoustic scale is evaluated in a mathematically idealized geometry ($\Omega_m = 1.0$, $\Omega_\Lambda = 0.0$) using the hi_class native `tep_mode` implementation.

#### Regime I: Standard empirical profile ($z_T = 5$)

In the standard TEP model, the profile $\exp[-(z/z_T)^{n_T}]$ ensures the conformal field correctly matches the apparent late-time acceleration inferred from Pantheon+. The integration confirms this background/acoustic mathematical isomorphism:

| $\epsilon_T$ | $100\theta_s$ | $r_s$ [Mpc] | $\Delta D_C / D_C$ | Interpretation |
| --- | --- | --- | --- | --- |
| $0.00$ | $1.0403$ | $144.526$ | $0.00\%$ | Pure EdS reference (no TEP) |
| $0.05$ | $1.0548$ | $144.519$ | $-1.38\%$ | $r_s$ preserved; $\theta_s$ shifts from $D_C$ projection |

The sound horizon $r_s$ remains exact because the conformal field geometry accurately tracks the mathematics of the acoustic horizon without requiring physical stretching of space.

#### Regime II: Theoretical divergence ($z_T \to \infty$)

If we remove the empirical profile and force the conformal factor to grow as a pure unsuppressed power law $A(z) = (1+z)^{\epsilon_T}$, we expose the mathematical divergence of the bare field:

| $\epsilon_T$ | $100\theta_s$ | $r_s$ [Mpc] | $\Delta D_C / D_C$ | Interpretation |
| --- | --- | --- | --- | --- |
| $0.00$ | $1.0403$ | $144.526$ | $0.00\%$ | Pure EdS reference |
| $0.05$ | $0.7565$ | $100.584$ | $-4.30\%$ | $r_s$ mathematically squeezed by divergence |

This mathematical limit demonstrates that the $z_T \sim 5$ empirical fitting function accurately defines the physical profile of the conformal field, allowing it to mimic Dark Energy while preserving the CMB acoustic horizon without expanding space.


![Jordan-frame dual-scan results](figures/figure_2_jordan_theta_s.png)



*Figure 2.* EdS + TEP dual scan. Solid line: EdS baseline at $\epsilon_T=0$. (Left) Standard empirical profile ($z_T = 5$): $r_s$ preserved. (Right) Divergent limit ($z_T \to \infty$): unphysical squeezing of the acoustic horizon.

## 6. Conclusion: The Static Conformal Universe

This paper implements and validates the native Temporal Equivalence Principle (TEP) conformal modification directly within the `hi_class` Boltzmann solver framework. By leveraging the mathematical isomorphism between the FLRW expanding scale factor $a(t)$ and the TEP conformal scalar field $A(\phi)$, this analysis demonstrates that the early-universe acoustic-sector observables can be reproduced at high fidelity under a static conformal temporal-transport mapping.

### 6.1 Summary of Results

- *The Mathematical Isomorphism:* The TEP conformal factor $A(\phi) = \exp(\beta_A\phi/M_{\rm Pl})$ dictates the clock-rates and photon phases in the causal matter metric $\tilde{g}_{\mu\nu} = A(\phi)^2 g_{\mu\nu}$. Because this scalar field evolves identically to the standard spatial scale factor $a(t)$, standard Boltzmann solvers act inherently as exact conformal-frame calculators for the background/acoustic-sector mapping tested here. The parameter traditionally defined as Dark Energy ($\Omega_\Lambda$) is interpreted within TEP as the background kinetic energy density of this Temporal Shear field, $\Omega_\phi$.

- *CMB Acoustic Preservation:* Because of this isomorphism, the hi_class native integration demonstrates that the static conformal geometry preserves the pre-recombination sound horizon to parts-per-million ($r_s^{\rm TEP}/r_s^{\Lambda\rm CDM} = 0.999994$) and preserves the acoustic-peak morphology at the background/acoustic-sector level. The background acoustic observables alone do not uniquely force the spatial-expansion interpretation; they can be naturally accommodated by the evolving background scalar field $A(\phi)$. This result should be read as the benchmark background/acoustic limit for the broader TEP-C0 cosmological programme; active scalar perturbation closure requires a separate $\delta\phi$-enabled Einstein–Boltzmann implementation.

- *The Temporal Horizon (No Big Bang):* By recognizing that the spatial metric does not stretch, the "Big Bang" is reinterpreted not as a physical density singularity, but as an observational Temporal Horizon—an asymptotic boundary where the conformal clock-rate field $A(\phi) \to 0$. Time slows to a halt relative to the present epoch, creating the illusion of a finite past and infinite density.

- *Cosmological Constraints:* A joint hi_class Cobaya MCMC (Planck 2018 low-$\ell$ TT/EE + lensing + BAO + Pantheon+) yields a close match to the conformal field parameters. The companion paper TEP-C0 (Paper 26) provides robust late-time evidence, showing via nested sampling that the screened TEP conformal model matches the Pantheon+ distance-redshift relation with strong Bayesian support, resolving the phenomenological need to stretch space to explain apparent acceleration.

### 6.2 Resolving the Cosmological Crises

Standard $\Lambda$CDM cosmology currently faces two severe crises: the Hubble Tension ($H_0$) and the "impossible" high-redshift massive galaxies discovered by JWST. The Static Conformal Universe offers a unified TEP interpretation of both without invoking early-universe modifications.

- *The Hubble Tension:* In TEP, the temporal shear field is environmentally screened by mass. Supernovae exist in empty voids (where the field is unscreened, yielding a high inferred $H_0$), while Cepheids exist in dense galaxies (where the field is partially screened, yielding a lower inferred $H_0$). The tension is an artifact of environmental mass-screening on local kinematic distance probes (Paper 11), not an early-universe physics crisis.


- *JWST High-Redshift Galaxies:* Within the broader TEP interpretation, the temporal-horizon picture may remove the finite-age assembly bottleneck by replacing the FLRW singularity with an asymptotic conformal-clock boundary. The massive galaxies observed by JWST could therefore form strictly within standard astrophysical accretion models over vast timescales (Paper 12).

### 6.3 Synthesis of the Paradigm Shift

This analysis implements and explicitly validates the native TEP geometry within a rigorous Boltzmann solver framework. The acoustic indistinguishability of the static conformal background from $\Lambda$CDM at recombination demonstrates that the early-universe background physics cannot easily distinguish between a stretching spatial metric and an evolving conformal clock-rate field.

Given that the late-universe Pantheon+ data (TEP-C0) explicitly prefers the TEP geometry over phenomenological spatial acceleration (Dark Energy) due to Bayesian parsimony, the framework presented here provides a concrete conformal-frame alternative to the background expansion interpretation, pending full scalar-perturbation closure. By asserting that time itself is a dynamical, mass-screened scalar field, TEP seeks to unify early-universe acoustic physics, late-time "acceleration", the $H_0$ tension, and JWST anomalies into a single, cohesive static geometric framework. The cosmology-level perturbation-closure programme belongs to TEP-C0, while the present paper provides the hi_class background/acoustic benchmark against which that extension should be tested.


## References

Smawfield, M. (Paper 1). *Temporal Equivalence Principle: Terrestrial Screening and GNSS Phase Correlations.* TEP Corpus.

Smawfield, M. (Paper 6). *TEP and Ultra-Compact Dwarfs: Potential-Dependent Proper-Time Mapping.* TEP Corpus.

Smawfield, M. (Paper 11). *TEP and the Hubble Tension: Cepheid Environmental Bias.* TEP Corpus.

Smawfield, M. (Paper 12). *TEP and JWST High-Redshift Anomalies.* TEP Corpus.

Smawfield, M. (Paper 13). *TEP and Gaia DR3 Wide Binaries: Density-Dependent Kinematics.* TEP Corpus.

Smawfield, M. (Paper 26). *Temporal Equivalence Principle: A Covariant Alternative to Cosmic Expansion.* TEP Corpus. DOI: 10.5281/zenodo.20370144

Bellini, E., & Sawicki, I. 2014, JCAP, 07, 050. *Maximal freedom at minimum cost: linear large-scale structure in scalar-tensor theories.*

Brax, P., Burrage, C., Davis, A.-C., & Gubitosi, G. 2019, Phys. Rev. D, 100, 083515. *Screening mechanisms in scalar-tensor theories.*

Cobaya Team. 2023, *Cobaya: Code for Bayesian Analysis of physical theories.* arXiv:2305.02971.

Hu, B., Raveri, M., Frusciante, N., & Silvestri, A. 2014, Phys. Rev. D, 89, 103530. *EFTCAMB/EFTCosmoMC: Numerical Notes.*

Knox, L., & Millea, M. 2020, Phys. Rev. D, 101, 043533. *Hubble constant hunter's guide.*

Lagos, M., Bellini, E., Jimenez, J. B., et al. 2018, JCAP, 03, 021. *hi_class: Horndeski in the Cosmic Linear Anisotropy Solving System.*

Lewis, A., Challinor, A., & Lasenby, A. 2000, Astrophys. J., 538, 473. *Efficient computation of cosmic microwave background anisotropies.*

Planck Collaboration. 2020, A&A, 641, A1. *Planck 2018 results. I. Overview and cosmological parameters.*

Planck Collaboration. 2020, A&A, 641, A6. *Planck 2018 results. VI. Cosmological parameters.*

Riess, A. G., Casertano, S., Yuan, W., et al. 2022, ApJ, 934, L7. *A Comprehensive Measurement of the Local Value of the Hubble Constant with 1 km/s/Mpc Uncertainty from the Hubble Space Telescope and the SH0ES Team.*

Sawicki, I., & Bellini, E. 2015, Phys. Rev. D, 92, 084061. *Stability of dark energy and the generalized no-slip condition.*

Zumalacárregui, M., & García-Bellido, J. 2014, Phys. Rev. D, 89, 064046. *Transforming gravity: from derivative couplings to matter to second-order scalar-tensor theories beyond the Horndeski Lagrangian.*

## Appendix A: Technical Implementation Details

### A.1 hi_class Installation and Configuration

#### A.1.1 Building with TEP Support

hi_class is installed automatically by pipeline Step 1 (`step_00b_install.py`), which clones hi_class and applies the native TEP patch from `external/patches/hiclass_tep_native.patch` to `source/background.c`, `source/input.c`, and `include/background.h`. Manual rebuild:

```
cd external/hi_class/hi_class
make clean && make
```

### A.2 Cobaya Installation

```
pip install cobaya
cobaya-install planck_2018_lowl.TT planck_2018_lowl.EE \
planck_2018_lensing.native bao.sdss_dr12_consensus_final \
sn.pantheonplus --path /path/to/likelihoods
```

### A.3 TEP Module C Code Structure and Implementation Note

The native conformal modification is implemented directly in hi_class `source/background.c`, controlled by the `.ini` flags `tep_mode`, `epsilon_T`, `z_T`, `n_T`. The relevant functions are:

- `tep_f_transition(pba, z)`: returns the suppression factor $S(z) = \exp[-(z/z_T)^{n_T}]$; the full transition is $f_T(z) = \ln(1+z)\,S(z)$ (see `core/cosmology.py:f_T`).

- `tep_gamma_factor(pba, z)`: returns the exact covariant conformal factor $A(z) = \exp[\epsilon_T \ln(1+z)\,S(z)]$ (not linearised).

- The Hubble rate and its conformal-time derivative are mathematically mapped using the exact geometric relation $M(z) = A/(1-\alpha_A)$ in `background_functions` and in the initial-Hubble setter, explicitly evaluating the static conformal geometry.

*Implementation note (corrected bug).* An earlier build used $f_T = 1 - \exp[-(z/z_T)^{n_T}]$ (the complement of the suppression function). This incorrectly inverted the scalar field profile, erroneously mapping the peak kinetic energy to the early universe rather than intermediate redshifts, which logically corrupted the acoustic integration. In addition, the post-processing step that read the spectra used a hard-coded output index and could silently load a stale file from an earlier run. Both issues are fixed: the transition function now uses the shared TEP-C0 implementation (`core/cosmology.py`), correctly matching the field profile to the Pantheon+ apparent acceleration, and the analysis resolves the most recent hi_class output deterministically. *Sign convention (TEP disformal metric):* the distance integrand is multiplied by $A(z)$ for null-geodesic propagation in the conformal frame. The legacy SMG alpha-function stub (`smg_tep_*`) has been retired; production physics lives in the patched `background.c` (`external/patches/hiclass_tep_native.patch`).

### A.3a Derivation of the Conformal-Frame Factor $M(z)$

This appendix derives the background conformal mapping $M(z)$ from the bi-metric action (Equation \ref{eq:3_theory_01}) using a single frame convention held fixed throughout, demonstrating the exact geometric relation implemented natively in the codebase.

*Setup and convention.* Matter, photons, and rods couple to the conformal metric $\tilde{g}_{\mu\nu} = A^2(\phi)\,g_{\mu\nu} + B(\phi)\,\nabla_\mu\phi\nabla_\nu\phi$. For the homogeneous background the disformal term contributes only through the time-time component and is absorbed into the lapse; the evolution is governed by the conformal part, so we set $B \to 0$ here (the disformal sector re-enters at the perturbative/GW level via $\alpha_T$, Section 2.2.2). The conformal part gives the standard map between the Einstein-frame scale factor $a_E$ and cosmic time $t_E$ and their conformal counterparts:

\begin{equation} \label{eq:a3a_map}
\tilde{a} = A(\phi)\,a_E, \qquad d\tilde{t} = A(\phi)\,dt_E.
\end{equation}

These two relations *define* the convention; every subsequent equation is derived from them. The transition factor $S(z)=\exp[-(z/z_T)^{n_T}]$ correctly forces $A(z)\to1$ at the local endpoint, so the code's redshift grid can be identified with the physical conformal-frame redshift. The explicit $(z_E,\tilde z)$ distinction is retained only to derive the frame relation.

*Physical Hubble rate.* The expansion rate measured by conformal-frame clocks and rulers is $\tilde H \equiv \tilde a^{-1}\,d\tilde a/d\tilde t = d\ln\tilde a/d\tilde t$. Using $d/d\tilde t = A^{-1}\,d/dt_E$ and $\ln\tilde a = \ln A + \ln a_E$,

\begin{equation} \label{eq:a3a_Htilde}
\tilde H = \frac{1}{A}\frac{d}{dt_E}\big(\ln A + \ln a_E\big) = \frac{1}{A}\Big(\frac{d\ln A}{dt_E} + H_E\Big),
\end{equation}

where $H_E = d\ln a_E/dt_E$ is the Einstein-frame rate. Because the TEP conformal factor $A(z)$ is evaluated as a function of the observable physical redshift (the Jordan-frame redshift $1+z = \tilde{a}_0/\tilde{a}$), the coupling $\alpha_A$ computed in the codebase is fundamentally the derivative with respect to the *Jordan-frame* scale factor:

\begin{equation} \label{eq:a3a_alpha}
\frac{d\ln A}{dt_E} = \frac{d\ln A}{d\ln \tilde{a}}\,\frac{d\ln \tilde{a}}{dt_E} = \alpha_A\,(A \tilde{H}), \qquad \alpha_A \equiv \frac{d\ln A}{d\ln \tilde{a}} = -\frac{d\ln A}{d\ln(1+z)},
\end{equation}

which matches the definition in Section 3.2. Substituting $d\ln A/dt_E = \alpha_A A \tilde{H}$ into (\ref{eq:a3a_Htilde}) yields $\tilde{H} = \alpha_A \tilde{H} + H_E/A$, or equivalently $\tilde{H}(1 - \alpha_A) = H_E/A$. Using the conformally transformed Friedmann equation $H_E = A^2\,H_{\Lambda\rm CDM}$ gives the exact geometric relation:

\begin{equation} \label{eq:a3a_exact}
\boxed{\;\tilde H(z) = \frac{A(z)}{1 - \alpha_A(z)}\,H_{\Lambda\rm CDM}(z)\;} \qquad \Longrightarrow \qquad M_{\rm exact}(z) = \frac{A}{1 - \alpha_A}.
\end{equation}

*Implementation Status.* The production codebase (`hiclass_tep_native.patch`) evaluates this exact geometric relation $M = A/(1-\alpha_A)$ directly, guaranteeing perfect mathematical fidelity to the conformal evaluation without requiring first-order approximations.

### A.4 Screening Threshold in Cosmological Units

The 20 g/cm³ environmental screening threshold converts to cosmological units as:

\begin{equation} \label{eq:9_appendix_01}
\rho_c = 20 \text{ g/cm}^3 = 2 \times 10^4 \text{ kg/m}^3 \approx 10^{31} \text{ eV/cm}^3
\end{equation}

In Planck units ($\hbar = c = G = 1$):

\begin{equation} \label{eq:9_appendix_02}
\rho_c \approx 4 \times 10^{-93} M_{\rm Pl}^4
\end{equation}

Compare to cosmic mean density today ($\rho_{\rm crit,0} \approx 10^{-123} M_{\rm Pl}^4$). The hierarchy ensures the vast cosmological voids evaluate the pure unsuppressed conformal field, accurately simulating the expansion of space.

*Intermediate environments and operational parameter bounds.* Between the terrestrial laboratory and the cosmic mean, the screening transition is continuous. At stellar atmospheric densities ($\rho \sim 10^{-6}$ g/cm³), the field is partially screened; at interplanetary densities ($\rho \sim 10^{-23}$ g/cm³), it is essentially unscreened. Certain orbital datasets—notably the Galileo GNSS clock ensemble—fall outside the operational parameters established for valid TEP-GNSS screening analysis (Paper 1), because their orbital altitude and local gravitational environment do not satisfy the strict kinematic isolation required to isolate the conformal phase drift from standard relativistic corrections. These exclusions are documented in the TEP-GNSS pipeline and do not affect the cosmological bound, which operates in the deep unscreened regime where $\rho \ll \rho_c$.

### A.5 Stability

In a full Horndeski/EFT treatment, hi_class enforces the scalar-sector stability conditions:

- $c_s^2 \geq 0$ (no gradient instabilities)

- $\alpha_K \geq 0$ (no ghosts)

- $|\alpha_M|$ bounded (sub-luminal Planck-mass running)

- $\alpha_T \approx 0$ (GW speed constraints)

These apply to the alpha-function mapping. However, because our native TEP integration utilizes the background/acoustic mathematical isomorphism between the FLRW geometry and the conformal field $A(\phi)$, the acoustic physics are evaluated purely as a background geometric map. Standard GR acoustic perturbations are run natively in the conformal frame, ensuring stability across the CMB evaluation.

*Perturbative decoupling condition:* The current acoustic preservation holds strictly under the assumption that spatial scalar perturbations ($\delta\phi$) decouple or are heavily suppressed by the continuous screening mechanism at early times. Because the scalar field $\phi$ is dynamical, its fluctuations must ultimately couple to the metric perturbations ($\delta g_{\mu\nu}$). A fully closed linear perturbation sector, explicitly solving for the EFT functions $f_B$ and $f_K$, is the necessary next step to rigidly define the limits of this decoupling in the unsuppressed late universe.


## Appendix B: Data Availability & Reproducibility


This work follows open-science practices. All results are fully reproducible from raw data
using the documented pipeline. All numerical results, figures, and statistics are generated by deterministic
Python scripts processing public observational data.



### Repository and Code


GitHub Repository: github.com/matthewsmawfield/TEP-HC



The repository contains a deterministic, version-controlled cosmological analysis pipeline
for CMB acoustic peak preservation tests and MCMC parameter estimation with TEP screening.



### Repository Structure


TEP-HC/
├── data/
│   ├── cobaya/              # Cobaya MCMC chains
│   ├── external/             # hi_class submodule
│   └── hi_class/             # TEP-CLASS implementation
├── scripts/
│   └── steps/                # Analysis pipeline steps
├── core/                     # TEP shared constants and parameters
├── site/
│   └── components/           # Manuscript HTML sections
├── requirements.txt
├── CITATION.bib
└── README.md



### Software Environment


Key packages: NumPy, SciPy, Matplotlib, Cobaya, hi_class.
The pipeline has been tested on Python 3.10+.



### License


All code and manuscripts are released under CC-BY-4.0.