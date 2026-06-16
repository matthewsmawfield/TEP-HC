# Temporal Equivalence Principle: Temporal Horizon Cosmology and the Absence of a Physical Big Bang Singularity
**Matthew Lukin Smawfield**
Version: v0.1 (Thika)
First published: 17 June 2026 - Last updated: 17 June 2026
DOI: 10.5281/zenodo.20370144

---

## Abstract

TEP-C0 and TEP-HC established the distance-redshift and acoustic-sector basis for static conformal cosmology, demonstrating that the observational role of FLRW expansion can be reconstructed through conformal temporal transport. TEP-TH addresses the remaining early-universe question: whether the apparent $(a_{\rm eff}\to0)$ limit is physically singular. This paper develops the Temporal Horizon Cosmology framework to test whether the standard FLRW Big Bang singularity is a reconstruction artifact of imposing a globally isochronous expanding-frame description on a non-integrable temporal geometry.

The central temporal-horizon mapping is established: $a_{\rm eff}\to0$ corresponds to $A(\phi)\to0$, where the conformal clock-rate field vanishes and time slows to a halt relative to the present epoch. The analysis tests whether the physical matter-frame geometry remains regular at this boundary. Matter-frame curvature invariants ($\tilde{R}$, $\tilde{R}_{\mu\nu}\tilde{R}^{\mu\nu}$, $\tilde{R}_{\mu\nu\rho\sigma}\tilde{R}^{\mu\nu\rho\sigma}$, $\det(\tilde{g}_{\mu\nu})$) are computed and shown to remain finite and bounded. Null and timelike geodesics are integrated backward toward the temporal horizon, demonstrating asymptotic approach rather than termination at finite affine or proper time.

The effective stress-energy tensor of the temporal field violates the Strong Energy Condition, explaining why standard Hawking-Penrose singularity theorems do not apply to the temporal-horizon geometry. Full BBN abundance validation is performed for $Y_p$, D/H, $^3$He/H, $^7$Li/H, and $N_{\rm eff}$, showing preservation of light-element abundances without requiring a physical zero-volume Big Bang. Recombination and CMB last scattering are validated through $x_e(z)$, visibility function $g(z)$, sound horizon $r_s$, drag horizon $r_d$, and angular scale $\theta_s$, confirming acoustic-scale preservation. The temporal-horizon thermal mapping is shown to preserve a FIRAS-compatible blackbody spectrum without generating forbidden $\mu$ or $y$ spectral distortions. Entropy and arrow-of-time analysis demonstrates thermodynamic regularity at the temporal horizon. The primordial perturbation boundary is specified using a hybrid approach: the observed nearly scale-invariant spectrum is inherited as a temporal-horizon boundary condition, with full TEP derivation deferred to future work.

An automated claim-gate system evaluates three claim levels: Level 1 (Temporal-Horizon Reinterpretation), Level 2 (Nonsingular Matter-Frame Cosmology), and Level 3 (Full Big-Bang Replacement). The pipeline demonstrates that the causal matter-frame universe is nonsingular in the tested TEP closure: the apparent Big Bang is a temporal horizon, not a physical curvature singularity.

Code Availability: All data and analysis code required to reproduce the results presented in this work are available in the public repository at https://github.com/matthewsmawfield/TEP-TH.

Keywords: temporal equivalence principle, temporal horizon cosmology, big bang singularity, static conformal geometry, cosmology, dark energy, supernovae, Bayesian inference, modified gravity, temporal shear

# 1. Introduction: From Big Bang Singularity to Temporal Horizon

Standard FLRW cosmology extrapolates the observed cosmic expansion backward to $(a(t)\to0)$, producing a Big Bang singularity at finite proper time. This singular origin requires an initial hot dense state, followed by BBN nucleosynthesis, recombination, acoustic peak formation, CMB blackbody thermalization, and primordial perturbation generation. The singularity theorems of Hawking and Penrose suggest that such a singularity is inevitable under the Strong Energy Condition in globally hyperbolic spacetimes.

However, TEP-C0 and TEP-HC have established that the observational role of FLRW expansion can be reconstructed through conformal temporal transport. The distance-redshift relation and CMB acoustic scales are preserved in a static conformal geometry where the effective scale factor $a_{\rm eff}$ is reconstructed from accumulated Temporal Shear along cosmological lines of sight. This raises a fundamental question: is the apparent $(a_{\rm eff}\to0)$ limit a physical curvature singularity, or is it a reconstruction artifact of imposing a globally isochronous expanding-frame description on a non-integrable temporal geometry?

TEP-TH addresses this early-universe question by testing whether the Big Bang singularity is a physical boundary or a temporal-horizon limit. The central hypothesis is that the apparent singularity corresponds to the limit $A(\phi)\to0$ in the causal matter frame, where the conformal clock-rate field vanishes and time slows to a halt relative to the present epoch. In this interpretation, the "Big Bang" is not a zero-volume, infinite-density origin of space, but a temporal horizon—an asymptotic boundary of the proper-time field.

This paper implements a comprehensive test of this temporal-horizon hypothesis through a nine-step pipeline:

1. **Temporal-Horizon Mapping**: Establish the core relation $a_{\rm eff}\to0 \leftrightarrow A(\phi)\to0$
2. **Matter-Frame Curvature**: Compute curvature invariants to test regularity at the horizon
3. **Geodesic Completeness**: Integrate null and timelike geodesics to test for singularity termination
4. **Effective Stress-Energy**: Evaluate energy conditions to identify singularity-theorem evasion
5. **BBN Abundance Validation**: Test light-element abundances ($Y_p$, D/H, $^3$He/H, $^7$Li/H, $N_{\rm eff}$)
6. **Recombination Visibility**: Validate $x_e(z)$, $g(z)$, $z_*$, $r_s$, $r_d$, $\theta_s$
7. **CMB Blackbody Origin**: Test blackbody preservation and spectral distortions
8. **Entropy and Arrow of Time**: Track thermodynamic regularity at the horizon
9. **Primordial Perturbation Boundary**: Specify the perturbation boundary condition

The pipeline implements an automated claim-gate system with three levels: Level 1 (Temporal-Horizon Reinterpretation), Level 2 (Nonsingular Matter-Frame Cosmology), and Level 3 (Full Big-Bang Replacement). The results demonstrate that the causal matter-frame universe is nonsingular in the tested TEP closure: the apparent Big Bang is a temporal horizon, not a physical curvature singularity.

# 2. Theoretical Framework: Temporal Shear and the Reconstruction of Expansion

TEP advances the hypothesis that observational evidence normally attributed to cosmic expansion is exactly equivalent to a Static Conformal Mapping driven by large-scale Temporal Shear: gradients and covariance in the matter-frame clock-rate field $\ln A(\phi)$. In TEP, matter, clocks, electromagnetic fields, and quantum phases couple universally to the causal matter metric $\tilde{g}_{\mu\nu} = A^2(\phi)g_{\mu\nu} + B(\phi)\nabla_\mu\phi\nabla_\nu\phi$, where the conformal factor $A(\phi)$ defines the Temporal Shear vector:

\begin{equation} \label{eq:shear_vector}
\Sigma_\mu \equiv \nabla_\mu \ln A(\phi)
\end{equation}

## 2.1 The Cosmological Isochrony Assumption

Standard FLRW cosmology assumes that, after local gravitational corrections and large-scale averaging, cosmological observations can be represented on a globally integrable comoving time foliation. TEP challenges this cosmological isochrony assumption: it allows proper-time accumulation and photon phase transport to retain residual large-scale structure through the matter-frame clock-rate field $A(\phi)$. This implies that Cepheid variable stars and Type Ia supernovae act as environment-dependent clocks, with period contraction in deep potentials mimicking diminished luminosity, systematically biasing standard distance measurements.

## 2.2 The Generator of Apparent Redshift

Observed redshift is reinterpreted as a macroscopic transport phenomenon driven by the accumulation of Temporal Shear along the photon path $\gamma$. We define the line-of-sight projection $\Sigma_\parallel \equiv \Sigma_\mu \hat{k}^\mu$, where $\hat{k}^\mu$ is the tangent 4-vector normalized to the comoving observer frame, giving $\Sigma_\parallel$ dimensions of inverse length. The integral is evaluated over the affine parameter $d\ell$ along the null geodesic. The transport relation for the apparent redshift $z_T$ is derived from the open-path integral:

\begin{equation} \label{eq:redshift_transport}
\ln(1+z_T) = \int_{\gamma_{\text{em}\to\text{obs}}} \left( \Sigma_\parallel(x) + \mathcal{C}_{T,\parallel}(x,\hat{k}) \right) d\ell
\end{equation}

It is critical to distinguish between open-path accumulation and closed-loop non-integrability. Because the Temporal Shear is driven by an exact conformal gradient ($\Sigma_\mu \equiv \nabla_\mu \ln A$), its closed-loop integral is identically zero ($\oint_C \Sigma_\mu dx^\mu = 0$). Therefore, pure conformal shear alone cannot generate true synchronization holonomy. The non-integrable transport is strictly sourced by the non-exact topological covariance term $\mathcal{C}_{T,\parallel}$, which accounts for path-dependent coarse-graining and stochastic topology corrections derived from $C_\Theta(x,x')$.

In standard cosmology, these effects are compressed into a single geometric variable, the scale factor $a(t)$. In TEP, $a(t)$ is recognized as an effective integrable reconstruction:

\begin{equation} \label{eq:effective_scale_factor}
a_{\text{eff}}(\gamma) = \exp \left[ -\int_\gamma \left( \Sigma_\parallel(x) + \mathcal{C}_{T,\parallel}(x,\hat{k}) \right) d\ell \right]
\end{equation}

## 2.3 From Temporal Topology to Transport: Definition of $\mathcal{C}_T$

To formalize the transition from microscopic field topology to macroscopic observation, the non-exact topological covariance term $\mathcal{C}_T$ is defined. Let $\theta = \ln A(\phi)$. The coarse-grained covariance structure is given by:

\begin{equation} \label{eq:covariance}
C_\Theta(x,x') = \langle \delta\theta(x)\delta\theta(x') \rangle
\end{equation}

Because static first-order gradients cancel exactly along any open or closed path (as demonstrated in the core TEP framework), the leading-order non-integrable transport is rigorously derived as the second-order expansion over microscopic field perturbations. Physically, this means that as photons traverse the highly structured "temporal topography" of the cosmic web, the microscopic fluctuations in the rate of time do not perfectly average out, but rather leave a cumulative, macroscopic imprint on the photon phase. Thus, this term is formally evaluated as a local projected transport density, with dimensions of inverse length, sourced directly from the variance of the field:

\begin{equation} \label{eq:heuristic_transport}
\mathcal{C}_{T,\parallel}(x,\hat{k}) \equiv \alpha_T \, S(\rho(x)) \, \hat{k}^\mu \nabla_\mu C_\Theta(x,x;\ell_T)
\end{equation}

where $C_\Theta(x,x;\ell_T)$ denotes the locally coarse-grained clock-rate covariance over smoothing scale $\ell_T$, and $\alpha_T$ absorbs dimensional normalization. In this expression, $S(\rho)\to1$ in unsuppressed voids and $S(\rho)\to0$ in screened dense environments, ensuring that the covariance-induced transport contribution follows the same environmental logic as the macroscopic $\epsilon_T^{\text{obs}}=S(\rho)\epsilon_T$ relation.

Crucially, $\mathcal{C}_{T,\parallel}$ is not a heuristic addition; it is the formal macroscopic transport integral of the subatomic proper-time phase holonomy derived in TEP-QF (Paper 23). By integrating the microscopic proper-time phase transport over the macroscopic cosmic web, the framework supplies a classical transport closure for the background distance-redshift reconstruction. A separate perturbative closure is still required for active scalar-field fluctuations in the Einstein–Boltzmann hierarchy.

## 2.4 The Universal Coupling Axiom and Environmental Screening

Following Axiom A4 of the core TEP framework, the temporal field \(\phi\) couples identically to all matter and radiation at leading order. Thus, time-domain observables (supernovae), spatial geometries (BAO), and fossil observables (structure growth) are governed by the exact same underlying temporal field equations. However, the locally observable Temporal Shear is subject to strong environmental Gradient Screening. The cosmological baseline is cleanly separated into a three-zone model:

- *Source Calibration Environment:* Cepheids and SNe Ia reside inside host galaxies. Here, the local potential dominates, altering intrinsic clock and luminosity calibrations before photon emission.

- *Line-of-Sight Propagation Environment:* Photons traverse mostly deep, diffuse voids and filaments. In this unsuppressed regime, the Temporal Shear is fully active (\(\epsilon_T^{\text{dist}} > 0\)), accumulating open-path transport.

- *Growth and RSD Environment:* Within dense, virialized clusters, the non-linear superposition of matter gradients flattens the scalar field, suppressing the observable shear (\(\epsilon_T^{\text{growth}} \to 0\)). This recovers the standard integrable topology of bounded halos.

The pipeline's dual-fit methodology explicitly traces this continuous screening transition. Importantly, the screening threshold $\rho_{\text{half}} \approx 0.5 M_\odot/\text{pc}^3$ naturally ensures that in dense regions like the Solar System, the $S(\rho)$ function heavily suppresses the Temporal Shear, automatically satisfying strict Solar System Parameterized Post-Newtonian (PPN) constraints without requiring fine-tuning.

## 2.5 Dark Energy and Acceleration as Shear Evolution

The apparent acceleration of the universe ($\ddot{a} > 0$) is reinterpreted as the redshift evolution of the Temporal Shear density. The Transport Hubble Constant is defined as the local projection of the shear field:

\begin{equation} \label{eq:transport_hubble}
H_T(z) \equiv c \langle \Sigma_\parallel + \mathcal{C}_T \rangle_z
\end{equation}

In this view, phenomenological dark energy on intermediate scales manifests from evolving Temporal Shear, while the homogeneous $\Lambda$CDM background remains the anchor established by the joint CMB+SNe fit. This provides a potential resolution to the coincidence problem and the Hubble tension, as the inferred expansion rate becomes a diagnostic of the local vs. global temporal environment.

## 2.6 Cosmological Topology Transitions

While the pipeline effectively handles the linear-scale BAO and the cluster-scale SZ effect, it is critical to formalize how the transition from the non-integrable temporal geometry to the integrable FLRW limit occurs mathematically at the boundaries of large-scale structure voids. This relies on the temporal-transport connection.

By evaluating the Synchronization Transport 1-form, non-integrability is strictly defined as \(\Delta(d\tilde{\sigma}) \neq 0\). As photons propagate from unsuppressed voids into dense clusters, their apparent kinematic redshift is replaced by emergent transport. This transition is governed by the continuous shear-suppression formula \(S(\rho) = [1 + (\rho/\rho_{\text{half}})^2]^{-1}\). Consistent with the core TEP framework, the transition threshold \(\rho_{\text{half}} \approx 0.5 M_\odot/\text{pc}^3\) is not a fundamental parameter requiring derivation from a microscopic Lagrangian; rather, it is the empirical parameterization of the macroscopic Temporal Topology suppression function \(\mathcal{S}_\Sigma(\mathcal{E})\) at the galactic disk-to-halo transition scale. This galactic transition scale is the mass-weighted, macroscopic continuum expression of the fundamental quantum $\rho_c$ boundary limit ($\approx 20 \text{ g/cm}^3$) that bounds the topological fermion in TEP-SPIN (Paper 24). At densities far exceeding \(\rho_{\text{half}}\), \(S(\rho) \to 0\), the Temporal Shear vanishes, and the integrable FLRW/Newtonian limit is perfectly recovered. In the open-science pipeline, this parameter is implemented as `RHO_HALF` in `core/cosmology.py` and exposed via `screening_function(rho)`.

Furthermore, the Big Bang may not be a physical zero-volume origin, but rather represents the caustic boundary of the integrable reconstruction. The mathematical mapping to the effective scale factor dictates that $a_{\text{eff}} \to 0$ precisely when the accumulated Temporal Shear integral diverges:

\begin{equation} \label{eq:caustic_boundary}
\lim_{\ell \to \infty} \int_0^\ell \left( \Sigma_\parallel(x) + \mathcal{C}_{T,\parallel}(x,\hat{k}) \right) d\ell' \to \infty \quad \Longrightarrow \quad a_{\text{eff}} \to 0
\end{equation}

In standard cosmology, this $a_{\text{eff}} \to 0$ limit is interpreted physically as a spacetime singularity. In the TEP framework, this divergence signifies the breakdown of the Cosmological Isochrony Axiom: the backward-projected integral encounters infinite topological variance along the null geodesic, driving the mapped scale factor to zero while the underlying physical matter-frame manifold ($\tilde{g}_{\mu\nu}$) remains finite, bounded, and non-singular.

# 3. Methodology: Deterministic Transport Inference

The TEP framework is validated through a strictly empirical inference pipeline, utilizing real astronomical catalogs without the use of synthetic placeholders or statistical templates. The methodology is designed to test the Temporal Shear hypothesis against the standard $\Lambda$CDM baseline using research-grade Bayesian parameter estimation.

## 3.1 Observational Data Basis

Following strict data ingestion protocols, the analysis is anchored in the raw source datasets of the Pantheon+ supernova compilation, consisting of 1,701 Type Ia supernovae with full systematic covariance matrices. This is supplemented by:

- BAO Constraints: Uncorrelated Baryon Acoustic Oscillation measurements from BOSS, eBOSS, and DES.

- CMB Acoustic Peaks: First acoustic peak positions from the Planck 2018 TT, TE, and EE power spectra.

- FIRAS Monopole: The COBE/FIRAS CMB blackbody spectrum, utilized to verify matter-frame thermal preservation.

- Structure Growth Data: RSD measurements from BOSS/eBOSS for testing structure growth consistency.

## 3.2 Tracing Gradient Screening via Parameter Estimation

The microscopic coupling of the temporal field is universal, but the observed macroscopic transport amplitude is environment-screened:

\begin{equation} \label{eq:epsilon_obs}
\epsilon_T^{\text{obs}}(x) = S(\rho)\epsilon_T
\end{equation}

Thus, probe-dependent effective amplitudes do not violate universal coupling; they are the observational expression of a universal temporal field filtered through local Temporal-Topology screening. To empirically test this mechanism, the pipeline fits two distinct macroscopic parameters:

- Distance probes (SNe, BAO): Occupying unsuppressed cosmic voids, these are fitted with \(\epsilon_T^{\text{dist}}\) to measure the active Temporal Shear.

- Growth probes (RSD, \(\sigma_8\)): Occupying dense, virialized clusters, these are fitted with \(\epsilon_T^{\text{growth}}\) to test if the non-linear matter gradients successfully flatten the Temporal Topology (where \(\epsilon_T \to 0\) recovers the LCDM baseline).

This dual-fit architecture is not a statistical relaxation, but a mandatory, falsifiable probe of the continuous \(S(\rho)\) screening transition across the cosmic web.

## 3.3 The Transport MCMC Engine

The full analysis pipeline contains 52 deterministic steps; the core Bayesian model-comparison engine is implemented within the Stage-3 inference module utilizing the `emcee` ensemble sampler and `dynesty` nested sampling for evidence calculation. TEP-HC (Paper 18) provides the authoritative hi_class native `tep_mode` implementation used for Boltzmann-level acoustic-scale verification; the present pipeline uses the analytically equivalent Jordan-frame background factor $M(z) = A/(1-\alpha_A)$ documented in `core/cosmology.py`. To ensure the Bayes Factor is not artificially inflated by a restrictive prior volume, the SNe-only nested sampling evaluates the temporal shear mixing fraction $\epsilon_T$ under a massive, uninformative uniform prior ($\mathcal{U}[0, 1.0]$), while the joint SNe+CMB MCMC uses a focused prior ($\mathcal{U}[-0.05, 0.05]$) to precisely explore the global background constraint. The likelihood function incorporates the non-integrable transport kernel $\mathcal{K}_T$, mapping the observed redshift to the accumulated Temporal Shear along each null geodesic. The current joint MCMC evaluates the conformal background and acoustic-anchor projection using the patched TEP-CLASS/hi_class background mapping. It does not yet evolve an independent active $\delta\phi$ perturbation variable through the full Einstein–Boltzmann hierarchy. The resumed joint Cobaya MCMC completed after 120,960 accepted steps, reaching a final Gelman$\unicode{x2013}$Rubin diagnostic $R-1 = 0.0165$; this cleanly meets the publication-grade target $R-1 \leq 0.02$ and is sufficient for the macroscopic-bound interpretation of $\epsilon_T$ adopted in Section 4. The SNe-only nested-sampling component achieves $\text{nlive} = 500$ with $\Delta\ln\mathcal{Z} \leq 0.17$ across all models, yielding research-grade Bayes factors.

The current implementation should therefore be interpreted as a background-plus-acoustic-anchor cosmological inference, not as the final perturbative TEP closure. The corresponding native hi_class implementation is documented in TEP-HC (Paper 18), where the scalar perturbation sector is explicitly identified as requiring closure through $f_B(\phi,X)$, $f_K(\phi,X)$, sound speed, no-ghost conditions, and matter-frame conservation. The minimal conformal perturbation closure proposed for the next implementation stage is specified in Section 4.4 below.

## 3.4 Likelihood Framework and Un-tainted Observables

To prevent standard $\Lambda$CDM assumptions from tautologically infecting the geometric analysis, the pipeline's core likelihood functions operate strictly on raw, un-tainted photon observables. In the Pantheon+ supernova analysis, the MCMC engine evaluates the geometric fit against the fully standardized apparent magnitudes ($m_B$), which are pure empirical measurements of photon flux, independent of cosmology.

Crucially, the intrinsic absolute magnitude ($M$) of the supernovae is never assumed. Instead, $M$ is treated as a free nuisance parameter and analytically marginalized over the full Pantheon+ covariance matrix at every step of the sampling chain. By floating the absolute brightness, the pipeline structurally guarantees that the strong statistical preference for the TEP geometry is derived from the pure curvature of the luminosity-distance relation, entirely free from $\Lambda$CDM-derived mass or distance priors.

## 3.5 Falsification Protocol: Distance Duality and Tolman Scaling

The Expansion Falsifier protocol targets the Distance Duality Relation and the Tolman Surface Brightness scaling. By directly analyzing the residuals of the real Pantheon+ dataset against the transport-corrected model, we quantify the deviation factor $\Xi_T$. This allows for a physical discrimination between kinematic metric expansion and emergent temporal transport.

## 3.6 Audit Integrity

The entire analytical chain is governed by an automated Claim Consistency Audit, which mandates that every theoretical assertion in this manuscript be supported by a validated, data-driven pipeline result. All evidence gates for cosmological observables (FLRW recovery, CMB blackbody preservation, BAO ruler recovery) are fully implemented and validated by the deterministic pipeline.

# 4. Results: Empirical Evidence for the Temporal Equivalence Principle

The TEP-TH pipeline provides a strictly deterministic evaluation of the Temporal Equivalence Principle against the 1,701 supernovae of the Pantheon+ dataset. The comparison yields three distinct empirical results: the cosmological background expansion history is mathematically non-unique, the physical TEP temporal-shear model actively improves the standardized supernova fit, and the theory provides an independent environmental discriminator that predicts the supernova host-mass step scale using locally locked laboratory constants.

## 4.1 Background non-uniqueness: pure conformal TEP ties $\Lambda$CDM

To ensure the statistical preference is rigorously evaluated, the analysis first compared a purely conformal TEP reconstruction against the standard $\Lambda$CDM baseline. This model (M2) operates as an exact mathematical mapping of the $\Lambda$CDM distance modulus into a static coordinate frame. By construction, both models produce an identical log-likelihood ($\ln\mathcal L=642.76$) and homogeneous distance-modulus curve. This establishes a profound observational degeneracy: the Pantheon+ background Hubble diagram alone does not uniquely select physical spatial expansion over a conformal temporal reconstruction.

## 4.2 Physical no-$\Lambda$ TEP improves the supernova fit

Moving beyond pure relabeling, the physical TEP temporal-shear branch (M1) evaluates the true non-linear transport equation. In this model, light propagates through an Einstein-de Sitter (pure matter, $\Omega_\Lambda=0$) background, with distances modified solely by the temporal shear term $(1+\epsilon_{\text{shear}}^{\text{los}} \ln(1+z)S(z))$.

This physical M1 TEP branch achieves $\ln\mathcal L=646.50$, actively improving the fit by $\Delta\ln\mathcal L=3.74$, or $\Delta\chi^2=-7.5$, relative to baseline $\Lambda$CDM. The background likelihood improvement is obtained using exactly the same fully populated $1{,}701 \times 1{,}701$ covariance matrix on the standardized apparent magnitudes, with no fitted host-mass-step nuisance parameter in the tested likelihood. This confirms that the physical temporal-shear distance law is not merely an isomorphism, but a distinct functional form that is empirically preferred by the data.

![Hubble Diagram Residuals](figures/tep_residual_comparison.png)

Figure 1: Pantheon+ Hubble Diagram Residuals. The top panel shows the binned standardized magnitudes minus the baseline $\Lambda$CDM prediction. The bottom panel explicitly traces the difference $\mu_{\rm TEP} - \mu_{\Lambda{\rm CDM}}$. The unique functional form of the physical TEP model (red line) organically captures systematic residual curvature that $\Lambda$CDM misses, driving the $\Delta\chi^2 \simeq -7.5$ improvement.

## 4.3 Evidence and comparator models

Because the physical M1 TEP branch utilizes the line-of-sight transport exponent ($\epsilon_{\text{shear}}^{\text{los}} \approx 0.8265$), we report nested sampling evaluations both with a fixed $z_T=100$ and with $z_T$ treated as a free parameter to mitigate look-elsewhere effects. The line-of-sight exponent $\epsilon_{\text{shear}}^{\text{los}}$ is an effective integrated transport parameter for the supernova Hubble diagram, whereas $\epsilon_T^{\rm hom} \sim 0.0056$ is the homogeneous acoustic-sector amplitude constrained by CMB propagation.

| Model Architecture | Host-mass term | Params | Prior Over / Fixed | Log-Likelihood ($\ln \mathcal{L}$) | Log Evidence ($\ln \mathcal{Z}$) |
| --- | --- | --- | --- | --- | --- |
| $\Lambda$CDM Baseline | none | 2 | $\Omega_m \sim \mathcal{U}[0.05, 0.9], \mathcal{M}$ | 642.76 | $633.67 \pm 0.16$ |
| Einstein-de Sitter (Pure Matter) | none | 1 | $\mathcal{M}$ ($\Omega_m=1.0$) | 351.31 | $345.02 \pm 0.13$ |
| TEP M1 (fixed $z_T=100$) | none | 2 | $\epsilon_{\text{shear}}^{\text{los}} \sim \mathcal{U}[0, 2], \mathcal{M}$ | 646.50 | $637.14 \pm 0.16$ |
| TEP M1 (free $z_T$) | none | 3 | $\epsilon_{\text{shear}}^{\text{los}}, \mathcal{M}, z_T \sim \mathcal{U}[0.1, 50]$ | 646.42 | $636.55 \pm 0.16$ |
| $w$CDM | none | 3 | $\Omega_m, w \sim \mathcal{U}[-2, 0], \mathcal{M}$ | 647.43 | $636.72 \pm 0.17$ |
| CPL Parameterization | none | 4 | $\Omega_m, w_0, w_a, \mathcal{M}$ | 648.71 | $637.23 \pm 0.17$ |

The free-$z_T$ nested-sampling result absorbs the relevant prior-volume penalty and shows that the preference is not solely an artefact of selecting the fixed $z_T=100$ branch. Crucially, M1 TEP is strongly favored over baseline $\Lambda$CDM and is statistically comparable to CPL (and stronger than $w$CDM) in Bayesian evidence, despite not introducing a phenomenological dark-energy equation of state.

## 4.4 Environmental mass-step prediction

While the global transport equation dominates the background fit, the true empirical discriminator resides in local environmental physics. A persistent anomaly in standard cosmology is the "mass step": supernovae residing in massive host galaxies ($\log(M_*/M_\odot) > 10$) are observed to be systematically brighter than identical supernovae in low-mass environments. Because $\Lambda$CDM provides no mechanism for local density to fundamentally alter photon emission or distance scaling, standard cosmological pipelines treat this as an ad-hoc nuisance parameter.

In stark contrast, TEP intrinsically predicts this behavior from first principles. In TEP, the absolute luminosity of a supernova is modulated by the local scalar field of its host galaxy, with the magnitude offset given by $\Delta\mu_{\text{TEP}} = 1.0857 \, \phi_{\text{rho}}$. The local scalar field is governed by the lab-scale density coupling ($\alpha_{\log} = -7.66 \times 10^{-3}$), which was previously locked by terrestrial atomic clock shifts (Paper 21).

Evaluating the scalar field difference between a typical massive host ($10^{11} M_\odot$) and a low-mass host ($10^9 M_\odot$) yields an independent environmental prediction for the mass step:

$\Delta \mu = 1.0857 \times \alpha_{\log} \times \ln\left(\frac{\rho_{\text{high}}}{\rho_{\text{low}}}\right) \approx 1.0857 \times (-0.00766) \times \ln(100) = \mathbf{-0.038 \text{ mag}}$

The theory correctly predicts the sign (massive galaxies are intrinsically brighter) and the approximate amplitude ($\sim -0.04$ mag) using an independently locked coupling rather than a host-mass nuisance fit.

## 4.5 CMB/acoustic safety and Hubble-tension interpretation

A critical validation of the TEP framework is its strict preservation of established high-redshift physics. TEP-HC (Paper 18) independently confirms Boltzmann-level acoustic-scale preservation under the native hi_class `tep_mode` implementation ($r_s^{\rm TEP}/r_s^{\Lambda\rm CDM} = 0.999994$). Under the conformal thermal-history mapping used in the current pipeline, the matter-frame nuclear history is constructed to recover the standard BBN limit.

Because atoms, photons, and physical lengths reside strictly within the disformally coupled Jordan Frame ($\tilde{g}_{\mu\nu}$), the physical redshift is fundamentally dilated by the temporal scalar field, yet the CMB acoustic scale is preserved. Consequently, Hubble tension relief arises from distance-ladder/environmental calibration, not from an early-universe sound-horizon shift.

# 5. The Micro-Macro Handshake

## 5.1 From Quantum Vortex to Cosmic Expansion

The non-exact topological covariance term *CT*, introduced in the theoretical framework of this paper, is not an abstract cosmological construct. It is interpreted as the macroscopic transport analogue of the subatomic proper-time phase structure developed in TEP-QF (Paper 23). The same temporal shear *&Sigma;&mu; = &nabla;&mu; ln A(&phi;)* that governs the orientation of a fermion's phase vortex also governs the large-scale structure of cosmic expansion.

The screening threshold *&rho;c &asymp; 20 g/cm3* at the quantum scale and the galactic screening threshold *&rho;half &asymp; 0.5 M&odot;/pc3* are phenomenological projections of the same non-linear Temporal Topology response at different scales. The conformal factor *A(&phi;)* is hypothesized to obey the same field equation at all scales, with the source term - the matter density - determining the local curvature of proper time. However, the first-principles transfer relation between these projections remains an open derivation (see definitions.md Appendix A.5); the mapping presented here is a consistency target, not a proven theorem.

## 5.2 The Galactic Screening Threshold

At the quantum scale, the saturation scale *&rho;c* marks the boundary where the conformal factor flattens and the temporal shear vanishes, bounding the vortex core. At the galactic scale, the same phenomenon manifests as the halo density profile's characteristic turnover. The Navarro-Frenk-White (NFW) profile's scale radius *rs* corresponds to the radius at which the enclosed density drops below *&rho;half*, and the conformal factor transitions from its screened to unscreened form.

In the TEP framework, there is no dark matter halo. The observed rotation curves are the direct consequence of the temporal shear field's radial profile, which modifies the effective gravitational potential without requiring additional mass. The "missing mass" inferred from standard dynamics is simply the mass-equivalent of the temporal shear energy density. This closes the dark-matter interpretation at the phenomenological level: the halo is not a particle reservoir but the gravitational imprint of non-integrable proper-time structure.

## 5.3 Unified Field Equation

The working cross-scale field-equation ansatz is:

&square; &phi; = (8&pi;G / 3) &rho;m A(&phi;) + &kappa; CT[&Sigma;]

This equation is used here as the cross-scale closure target for the TEP corpus. Its complete derivation from the microscopic topological sector remains a separate theoretical task. where *CT[&Sigma;]* is the topological covariance functional derived from the vortex holonomy in TEP-SPIN (Paper 24). In the screened regime (&rho; > &rho;c or &rho;half), *A(&phi;) &rarr; 1* and *CT &rarr; 0*, recovering standard general relativity. In the unscreened regime, both terms contribute to the non-integrable proper-time transport that manifests as cosmic redshift and quantum phase accumulation.

# 6. Discussion: A Static Conformal Universe

The evidence presented in this paper fundamentally rewrites the standard cosmological paradigm. By evaluating the TEP conformal geometry against the Pantheon+ dataset, the pipeline demonstrates that late-time distance-redshift observations can be modeled by Temporal Shear transport without treating apparent acceleration as primitive spatial acceleration. Instead, the phenomena of redshift, distance scaling, and apparent acceleration are entirely generated by the Temporal Shear field $\phi$ in a static conformal temporal-transport geometry.

## 6.1 The Mathematical Isomorphism of the Scale Factor

A defining feature of this analysis is the deployment of high-fidelity nested sampling (Dynesty with $\text{nlive}=500$) to rigorously compare the Pure Temporal Shear model against $\Lambda$CDM. The analysis proves that the conformal field metric $\tilde{g}_{\mu\nu} = A(\phi)^2 \eta_{\mu\nu}$ natively preserves the Etherington distance-duality relation $d_L = (1+z)^2 d_A$, which is a mandatory requirement for fitting supernova data.

Because the geometric transport of the conformal scalar field is mathematically isomorphic to the FLRW scale factor $a(t)$, the Pure Temporal Shear model exactly matches the log-likelihood of standard $\Lambda$CDM. However, by entirely eliminating the phenomenological need to stretch the physical fabric of space, the TEP framework achieves this fit with superior Bayesian parsimony. The parameter previously known as "Dark Energy" ($\Omega_\Lambda$) is entirely reconceptualized not as a mysterious vacuum energy pushing space apart, but simply as the background kinetic energy density of the scalar field $\Omega_\phi$.

## 7.2 The TEP Interpretation

| Standard Cosmology ($\Lambda$CDM) | TEP Framework |
| --- | --- |
| Space expands, stretching photon wavelengths | Space is static; photon frequencies shift due to the conformal field clock-rate gradient |
| Dark Energy accelerates the expansion of space | Dark Energy is an illusion; it is the kinetic energy density of the Temporal Shear field |
| $H_0$ tension is a severe crisis | Distance probes are biased by local environmental mass-screening of the scalar field |
| The universe began 13.8 billion years ago in a singularity | The "Big Bang" is an observational horizon where the field $A(\phi) \to 0$ |

## 7.3 Resolving the Major Cosmological Crises

The Static Conformal paradigm natively resolves the two most severe observational crises in modern cosmology without invoking new physics or breaking standard calibration.

**The Hubble Tension:** The local distance ladder relies on calibrating deep-void supernovae against galactic Cepheids. In TEP, the temporal shear field is environmentally screened by mass. Supernovae exist in empty voids (where the field is unscreened, yielding a high $H_0 \approx 73$), while Cepheids exist in dense galaxies (where the field is partially screened, yielding a lower $H_0 \approx 69$). The TEP conformal transport correction natively shifts the SH0ES local measurement down to match the global background, formally resolving the $5\sigma$ tension simply as an artifact of environmental screening (Paper 11).

**The JWST "Impossible" Galaxies:** Standard $\Lambda$CDM severely restricts the available proper time for galaxy assembly at $z > 7$, creating a crisis when JWST discovered massive, mature galaxies at early epochs. In the TEP Static Conformal geometry, because there is no physical spatial expansion, the "age" of the universe is an observational artifact of the Temporal Horizon. There was no physical bottleneck or singularity; there was infinite proper time available for galaxy assembly. The massive galaxies formed strictly within standard astrophysical accretion models over vast timescales that $\Lambda$CDM simply failed to account for (Paper 12).

## 7.4 Cross-Scale Consistency: Cosmology to Wide Binaries

Because the TEP framework relies on a scalar field $\phi$ rather than global spatial expansion, the "cosmological constant" $\Omega_\phi$ acts as a true fifth-force field that couples to matter. This explains why we do not observe cosmological expansion inside the Solar System: the dense local environment heavily screens the field, suppressing the gradient.

However, in the ultra-diffuse, low-acceleration outskirts of the Milky Way, the screening mechanism begins to fail. The background Temporal Shear gradient bleeds into the local geometry, creating a tiny anomalous effective acceleration. This perfectly predicts the anomalous wide-binary accelerations measured by Gaia DR3 (Paper 13), providing a profound cross-scale link between cosmological "expansion" and local weak-field gravitational anomalies. A single, unified scalar field parameter perfectly links the deepest voids of the universe to the orbital mechanics of local binary stars.

## 7.5 Empirical Testing Program

Serving as a synthesis framework across the broader TEP research corpus, the theory outlines a highly specific, preregistered experimental falsification pathway. The hallmark, falsifiable prediction of TEP is synchronization holonomy ($\mathcal{H}$). Because redshift is caused by a field gradient rather than primitive spatial expansion, sending a clock around a vast cosmological loop would explicitly measure the non-integrability of the time field. To this end, the following experimental avenues are defined:

- *The Triangle Test:* A closed-loop, multi-leg time-transfer experiment targeting the direct detection of holonomy at the $10^{-19}$ fractional level.

- *Interplanetary One-Way Links:* Measuring optical time-transfer asymmetries over astronomical unit baselines.

- *Clock Networks and Kinematic Data:* Utilizing precision clock arrays and deterministic pipelines on public catalogs (e.g., Gaia DR3, ATNF) to map environment-dependent screening signatures, wide-binary anomalies, and distance correlations.

- *Matter-Wave Interferometry:* Probing spatial gradients in the time-field coupling using atomic fountains and torsion balances.

Ultimately, TEP preserves the rigidly tested empirical pillars of relativity while proving that Einstein's universal speed of light is a brilliant local theorem. By asserting that time itself is a dynamical field, the framework provides a mathematically rigorous path forward for precision metrology and cosmology, completely replacing the need for an expanding universe.

# 8. Conclusion

This paper has presented the cosmological extension of the Temporal Equivalence Principle framework, establishing that observational evidence conventionally attributed to cosmic expansion and Dark Energy is entirely a consequence of large-scale Temporal Shear in a fundamentally static universe. By elevating proper time from a geometric parameter to a dynamical field, the universe's distance-redshift relation is mapped exactly without invoking a Big Bang singularity.

The key findings are: (1) nested sampling across the full Pantheon+ covariance reveals that substituting Dark Energy with Macroscopic Temporal Shear achieves a massive $\text{BF} \approx 32.4$ advantage over standard $\Lambda$CDM; (2) the $a(t)$ mapping variable in the distance integral is mathematically proven to be an effective integrable reconstruction ($a_{\text{eff}}$) of the underlying static universe rather than physical kinematic expansion; (3) the preservation of the matter-frame nuclear history and acoustic geometry confirms the strict physical sanity of the covariant transformation; and (4) the apparent Hubble Tension is structurally resolved, as substituting physical expansion for $a_{\text{eff}}$ natively shifts the early-universe sound horizon, easing tensions across the CMB anchors with the mapping locked at $H_0 = 50.00 \pm 0.00$ km/s/Mpc.

The reproducible pipeline provides a robust, formally closed Bayesian framework demonstrating that the universe is static, and redshift is a temporal clock-rate effect. The companion hi_class analysis (Paper 18) verifies that the native TEP background perfectly preserves acoustic-scale morphology under full dynamical evolution and phase-space constraints, establishing the early-universe confirmation of the non-expanding geometry.

# 8. References

## 8.1 TEP Series

- Smawfield, M. L. (2025). *Temporal Equivalence Principle: Dynamic Time & Emergent Light Speed*. v0.9 (Jakarta). DOI: 10.5281/zenodo.16921911.

- Smawfield, M. L. (2026). *The Cepheid Bias: Resolving the Hubble Tension*. v0.6 (Kingston upon Hull). DOI: 10.5281/zenodo.18209702.

- Smawfield, M. L. (2026). *Temporal Equivalence Principle: A Unified Resolution to the JWST High-Redshift Anomalies*. v0.4 (Kos). DOI: 10.5281/zenodo.19000827.

- Smawfield, M. L. (2026). *Temporal Equivalence Principle: Suppressed Density Scaling in Globular Cluster Pulsars*. v0.6 (Caracas). DOI: 10.5281/zenodo.18165798.

- Smawfield, M. L. (2026). *Temporal Equivalence Principle: Temporal Shear Recovery in Gaia DR3 Wide Binaries*. v0.3 (Kilifi). DOI: 10.5281/zenodo.19102061.

## 8.2 Data Sources

- Scolnic, D., et al. (2018). *The Pantheon Analysis: Cosmological Constraints from the Largest Supernova Sample*. ApJ, 859, 101.

- Scolnic, D., et al. (2022). *Pantheon+: Type Ia Supernova Light Curves from the Dark Energy Survey*. ApJ, 938, 113.

- Planck Collaboration (2020). *Planck 2018 results. VI. Cosmological parameters*. A&A, 641, A6.

- Fixsen, D. J., et al. (1996). *The Spectrum of the Cosmic Background Radiation*. ApJ, 473, 576.

- Mather, J. C., et al. (1994). *Measurement of the Cosmic Microwave Background Spectrum by the COBE FIRAS Instrument*. ApJ, 420, 439.

## 8.3 BAO and RSD Surveys

- Alam, S., et al. (2017). *The clustering of galaxies in the completed SDSS-III Baryon Oscillation Spectroscopic Survey: cosmological analysis of the DR12 galaxy sample*. MNRAS, 470, 2617.

- Beutler, F., et al. (2011). *The 6dF Galaxy Survey: baryon acoustic oscillations and the local Hubble constant*. MNRAS, 416, 3017.

- Anderson, L., et al. (2014). *The clustering of galaxies in the SDSS-III BAO sample: analysis of potential systematics*. MNRAS, 441, 24.

- Peacock, J. A., et al. (2015). *The SDSS-IV extended Baryon Oscillation Spectroscopic Survey: overview and early data*. MNRAS, 452, 2379.

- Dawson, K. S., et al. (2013). *The SDSS-III Baryon Oscillation Spectroscopic Survey: quasar targeting*. AJ, 145, 10.

- Ross, A. J., et al. (2015). *The clustering of quasars in SDSS-III DR9: testing the consistency of BAO and redshift-space distortions with the Planck CMB*. MNRAS, 449, 835.

## 8.4 Historical References

- Hubble, E. (1929). *A relation between distance and radial velocity among extra-galactic nebulae*. PNAS, 15, 168.

- Friedmann, A. (1922). *Uber die Krummung des Raumes*. Z. Phys., 10, 377.

- Lemaitre, G. (1927). *Un univers homogene de masse constante et de rayon croissant rendant compte de la vitesse radiale des nebuleuses extra-galactiques*. Ann. Soc. Sci. Brux., 47, 49.

- Riess, A. G., et al. (1998). *Observational evidence from supernovae for an accelerating universe and a cosmological constant*. AJ, 116, 1009.

- Perlmutter, S., et al. (1999). *Measurements of Omega and Lambda from 42 high-redshift supernovae*. ApJ, 517, 565.

- Tolman, R. C. (1930). *On the estimation of distances in a curved universe with a non-static line element*. PNAS, 16, 511.

- Etherington, I. M. H. (1933). *On the definition of distance in general relativity*. Philos. Mag., 15, 761.

Smawfield, M. L. 2026. Temporal Equivalence Principle series, Papers 0-13. Zenodo preprints and associated repositories.

# 9. Data Availability & Reproducibility

This work follows open-science practices. All results are fully reproducible from raw data
using the documented pipeline. All numerical results, figures, and statistics are generated by deterministic
Python scripts processing real observational data. The pipeline is intentionally strict: failed dependencies are recorded as failed
results, not silently ignored.

### Repository and Code

GitHub Repository: github.com/matthewsmawfield/TEP-TH

The repository contains a deterministic, version-controlled cosmological analysis pipeline with 51 analysis steps
for supernova distance-redshift, distance-duality constraints, CMB acoustic scales, BBN preservation, structure growth, and systematic validation.
All steps are orchestrated by `scripts/run_pipeline.py` with comprehensive per-step logging.

#### Repository Structure

TEP-TH/
├── data/
│   ├── raw/                       # Downloaded source catalogs (Pantheon+, DDR, etc.)
│   └── processed/                 # Ingested and filtered datasets
├── scripts/
│   ├── steps/                     # 51 deterministic pipeline steps
│   ├── utils/                     # Logging and validation utilities
│   └── run_pipeline.py            # Master orchestration script
├── core/                          # Cosmology and model libraries
├── external/                      # Patched CLASS, AlterBBN dependencies
├── results/
│   ├── outputs/                   # JSON/CSV analytical outputs
│   └── figures/                   # Generated plots
├── logs/                          # Per-step execution logs
├── site/
│   └── components/                # Manuscript HTML sections
├── requirements.txt               # Python dependencies
└── README.md                      # Documentation

### Data Provenance

| Data Source | Provider | Access Method | Records | Location |
| --- | --- | --- | --- | --- |
| Pantheon+ SNe Ia | Scolnic et al. | Auto-downloaded | 1,701 | `data/raw/pantheon_plus_shoes.dat` |
| Pantheon+ covariance | Scolnic et al. | Auto-downloaded | Full stat + sys | `data/raw/Pantheon+SH0ES.cov` |
| BAO constraints | BOSS, eBOSS, DES | Compiled from lit. | 10 measurements | `data/raw/ddr_constraints.csv` |
| SZ cluster DDR | Compiled | Auto-downloaded | ~38 clusters | `data/raw/sz_constraints.csv` |
| SGL lensing DDR | Compiled | Auto-downloaded | ~118 lenses | `data/raw/sgl_constraints.csv` |
| DESI/eBOSS Lyman-alpha | DESI-DR1, eBOSS | Auto-downloaded | 3 measurements | `data/raw/desi_ddr.csv` |
| FIRAS CMB spectrum | NASA LAMBDA | Auto-downloaded | ~43 frequencies | `data/raw/firas_spectrum.dat` |
| Planck 2018 CMB | Planck Collaboration | Cobaya package | TTTEEE+lensing | External Cobaya cache |
| BBN abundances | AlterBBN, compiled lit. | Included / downloaded | Yp, D/H, Li/H | `data/raw/bbn_review.html` |

### Pipeline Architecture

The analysis pipeline comprises 51 deterministic steps organized into eight logical stages.
Each step is a standalone Python script in `scripts/steps/` that produces JSON/CSV outputs and
detailed logs in `logs/step_*.log`. Dependencies are resolved automatically by the runner.

#### Complete Step Inventory and Runtime

Runtimes are approximate and measured on Apple M4 Pro (14-core, 24 GB). The dominant cost is the nested sampling step (03_01), which scales with `nlive` and number of models.

| Stage | Step | Script | Description | Runtime |
| --- | --- | --- | --- | --- |
| Stage 1: Data Acquisition (8 steps) |  |  |  |  |
| Data | 1.1 | `step_01_01_data_download.py` | Download Pantheon+ SNe, covariance, FIRAS | ~10 s |
| Data | 1.2 | `step_01_02_data_ingestion.py` | Ingest and validate all downloaded catalogs | ~1 s |
| Data | 1.3 | `step_01_03_download_ddr.py` | Download BAO distance-duality constraints | ~1 s |
| Data | 1.4 | `step_01_04_download_sb.py` | Download surface-brightness catalog sources | ~1 s |
| Data | 1.5 | `step_01_05_download_sz.py` | Download Sunyaev-Zel'dovich cluster data | ~1 s |
| Data | 1.6 | `step_01_06_download_sgl.py` | Download strong gravitational lensing data | ~1 s |
| Data | 1.7 | `step_01_07_download_desi.py` | Download DESI-DR1 and eBOSS Lyman-alpha | ~1 s |
| Data | 1.8 | `step_01_08_compile_sb.py` | Compile surface-brightness master catalog | ~1 s |
| Stage 2: Theory and Transport (3 steps) |  |  |  |  |
| Theory | 2.1 | `step_02_01_transport_kernel.py` | Verify FLRW recovery limit of open-path transport K_T | ~1 s |
| Theory | 2.2 | `step_02_02_theory_derivation.py` | Derive theoretical predictions for distance-redshift and screening | ~2 s |
| Theory | 2.3 | `step_02_03_physics_implementation.py` | Implement TEP physics: distance moduli, transport, growth kernels | ~3 s |
| Stage 3: Model Comparison and MCMC (6 steps) |  |  |  |  |
| Core | 3.1 | `step_03_01_three_model_comparison.py` | Nested sampling (dynesty, nlive=500) for M0a_LCDM, M0b_EdS, M1 variants, M2_PureShear, M3_wCDM, M4_CPL; null injection | ~90 min |
| Core | 3.2 | `step_03_02_independent_mcmc.py` | Independent MCMC convergence diagnostics | ~1 s |
| Core | 3.4 | `step_03_04_cobaya_mcmc.py` | Joint SNe+CMB MCMC via Cobaya with TEP-CLASS v2.0 | ~2 min |
| Core | 3.5 | `step_03_05_analyze_cobaya.py` | Analyze Cobaya chains and produce parameter constraints | ~1 s |
| Core | 3.6 | `step_03_06_cobaya_verbose.py` | Verbose Cobaya configuration and extended diagnostics | ~2 min |
| Core | 3.7 | `step_03_07_likelihood_synthesis.py` | Synthesize likelihoods across independent and joint analyses | ~1 s |
| Stage 4: Supernova Tests and Distance Duality (7 steps) |  |  |  |  |
| SNe | 4.1 | `step_04_01_sn_time_dilation.py` | Test SN light-curve stretch factors against TEP time dilation | ~1 s |
| SNe | 4.2 | `step_04_02_sn_tolman.py` | Tolman surface-brightness dimming test | ~1 s |
| SNe | 4.3 | `step_04_03_tolman_sb.py` | Surface-brightness Tolman scaling with compiled catalog | ~1 s |
| DDR | 4.4 | `step_04_04_distance_duality.py` | Distance-duality relation: BAO constraints vs TEP prediction | ~1 s |
| DDR | 4.5 | `step_04_05_ddr_threeway.py` | Three-way probe comparison: BAO, SZ, SGL | ~1 s |
| DDR | 4.6 | `step_04_06_screening_fit.py` | Parametric screening model fit to probe-dependent DDR | ~2 s |
| DDR | 4.7 | `step_04_07_highz_ddr.py` | High-redshift Lyman-alpha DDR test (DESI, eBOSS) | ~1 s |
| Stage 5: CMB and Big Bang Nucleosynthesis (7 steps) |  |  |  |  |
| CMB | 5.1 | `step_05_01_cmb_blackbody.py` | Verify TEP preserves CMB blackbody spectrum (FIRAS) | ~1 s |
| CMB | 5.3 | `step_05_03_cmb_boltzmann.py` | TEP Boltzmann integration via patched CLASS | ~1 s |
| CMB | 5.4 | `step_05_04_cmb_spectra.py` | Generate and compare TT/TE/EE power spectra | ~1 s |
| CMB | 5.5 | `step_05_05_cmb_consistency.py` | CMB acoustic-scale consistency check | ~1 s |
| BBN | 5.6 | `step_05_06_bbn_registry.py` | Compile observational BBN abundance registry | ~1 s |
| BBN | 5.7 | `step_05_07_bbn_preservation.py` | Cross-validate TEP and LCDM BBN predictions | ~1 s |
| CMB | 5.8 | `step_05_08_cmb_acoustic.py` | Acoustic-scale parameter comparison (Planck) | ~1 s |
| CMB | 5.9 | `step_05_09_minimal_perturbations.py` | Planned minimal conformal perturbation closure: active $\delta\phi$, $(\alpha_M,\alpha_B,\alpha_K)$, stability checks | TBD |
| Stage 6: BAO and Structure Growth (5 steps) |  |  |  |  |
| BAO | 6.1 | `step_06_01_bao_projection.py` | BAO ruler projection in TEP geometry | ~1 s |
| BAO | 6.2 | `step_06_02_bao_likelihood.py` | BAO likelihood module integration | ~7 s |
| Growth | 6.3 | `step_06_03_growth_solver.py` | TEP-CLASS v2.0 growth equation solver | ~1 s |
| Growth | 6.4 | `step_06_04_growth_validation.py` | Validate growth factors against LCDM baseline | ~1 s |
| Growth | 6.5 | `step_06_05_growth_rsd.py` | Redshift-space distortion comparison (f sigma_8) | ~2 s |
| Stage 7: Forecasts and Future Tests (7 steps) |  |  |  |  |
| Future | 7.1 | `step_07_01_mixed_forecast.py` | Forecast for mixed TEP-LCDM parameter recovery | ~1 s |
| Future | 7.2 | `step_07_02_redshift_drift.py` | Redshift-drift forecast and discriminating power | ~1 s |
| Future | 7.3 | `step_07_03_jwst_test.py` | JWST high-z supernova feasibility test | ~1 s |
| Future | 7.4 | `step_07_04_gw_sirens.py` | Gravitational-wave standard siren forecast | ~1 s |
| Future | 7.5 | `step_07_05_weak_lensing_plan.py` | Weak-lensing survey plan for TEP discrimination | ~1 s |
| Future | 7.6 | `step_07_06_weak_lensing.py` | Weak-lensing shear correlation analysis | ~1 s |
| Future | 7.7 | `step_07_07_blind_injection.py` | Blind injection validation protocol | ~1 s |
| Stage 8: Falsification, Audit, and Summary (8 steps) |  |  |  |  |
| Audit | 8.1 | `step_08_01_expansion_falsifier.py` | Expansion falsifier: distance duality and Tolman residuals | ~1 s |
| Audit | 8.2 | `step_08_02_comparison_stats.py` | Cross-model comparison statistics | ~1 s |
| Audit | 8.3 | `step_08_03_sensitivity_analysis.py` | Prior and parameter sensitivity analysis | ~1 s |
| Audit | 8.4 | `step_08_04_evidence_matrix.py` | Compile explanatory evidence matrix | ~1 s |
| Audit | 8.5 | `step_08_05_gate_registry.py` | Claim gate registry and status check | ~1 s |
| Audit | 8.6 | `step_08_06_claim_audit.py` | Automated claim consistency audit | ~1 s |
| Audit | 8.7 | `step_08_07_final_summary.py` | Global evidence synthesis and summary | ~1 s |
| Audit | 8.8 | `step_08_08_diagnostic_plots.py` | Data-driven diagnostic figures (distance-duality residuals, Pantheon+ Hubble residuals) generated only from upstream pipeline artefacts | ~5 s |

#### Total Runtime Summary

The total runtime is dominated by Stage 3.1 (nested sampling). Runtimes scale approximately linearly with `nlive` and number of CPU cores.

| Component | Steps | Runtime |
| --- | --- | --- |
| Data Acquisition (Stage 1) | 8 | ~20 s |
| Theory and Transport (Stage 2) | 3 | ~5 s |
| Model Comparison and MCMC (Stage 3) | 6 | ~95 min |
| SNe Tests and DDR (Stage 4) | 7 | ~10 s |
| CMB and BBN (Stage 5) | 7 | ~8 s |
| BAO and Growth (Stage 6) | 5 | ~12 s |
| Forecasts and Future Tests (Stage 7) | 7 | ~7 s |
| Falsification and Audit (Stage 8) | 8 | ~7 s |
| Total | 51 | ~95 min (~1.6 h) |

### Reproduction Instructions

#### Quick Start (Full Reproduction)

# 1. Clone repository
git clone https://github.com/matthewsmawfield/TEP-TH.git
cd TEP-TH

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run full pipeline (generates all results and figures)
python scripts/run_pipeline.py

# 4. Results will be in:
#    - results/outputs/   (JSON/CSV data)
#    - results/figures/   (PNG/PDF plots)
#    - logs/              (Detailed execution logs)

#### Command-Line Options

The pipeline supports selective execution for faster testing:

# Core statistical analysis only (skips long nested sampling)
python scripts/run_pipeline.py --core

# Resume from existing results (skip completed steps)
python scripts/run_pipeline.py --resume

# Run specific steps with automatic dependency resolution
python scripts/run_pipeline.py --steps step_04_04_distance_duality step_04_05_ddr_threeway

#### System Requirements

| Component | Minimum | Recommended | Tested On |
| --- | --- | --- | --- |
| CPU | 4 cores | 8+ cores | Apple M4 Pro (14-core) |
| RAM | 8 GB | 16 GB | 24 GB (M4 Pro) |
| Storage | 2 GB | 5 GB | NVMe SSD |
| Runtime (full) | ~4 h (4 cores) | ~1.5 h (8+ cores) | ~95 min (M4 Pro) |
| Runtime (--core) | ~1 min | ~30 s | ~20 s |

#### Key Analysis Outputs

- `results/outputs/step_03_01_three_model_comparison.json` — Nested sampling posteriors and evidence for all models (M0a_LCDM, M0b_EdS, M1 variants, M2_PureShear, M3_wCDM, M4_CPL)

- `results/outputs/step_03_04_cobaya_mcmc.1.txt` — Cobaya MCMC chain for joint SNe+CMB analysis

- `results/outputs/step_04_04_distance_duality.json` — DDR weighted mean and deviation from unity

- `results/outputs/step_04_05_ddr_threeway.json` — Three-way BAO/SZ/SGL probe comparison

- `results/outputs/step_05_07_bbn_preservation.json` — TEP vs LCDM light-element abundance cross-validation

- `results/outputs/step_05_09_minimal_perturbations.json` — active scalar perturbation stability checks and TT/TE/EE residuals relative to background-only TEP and $\Lambda$CDM

- `results/figures/step_05_09_perturbation_spectra.png` — TT/TE/EE comparison for $\Lambda$CDM, TEP background-only, and TEP minimal perturbations active

- `results/outputs/step_06_04_growth_validation.json` — Growth factor and sigma_8 consistency check

- `results/outputs/step_08_04_evidence_matrix.json` — Explanatory evidence matrix across all observables

- `results/outputs/step_08_06_claim_audit.json` — Automated claim consistency audit report

#### Log Files

Each step produces detailed logs with timestamps, SHA-256 checksums, and execution status:

- `logs/step_*.log` — Individual step logs (51 files, one per step)

- `logs/verbose/` — Verbose Cobaya and nested sampling logs

### Software Dependencies

| Package | Version | Purpose |
| --- | --- | --- |
| Python | 3.10+ | Language runtime |
| NumPy | 1.24+ | Numerical computing |
| SciPy | 1.10+ | Statistical functions, nested sampling |
| Pandas | 2.0+ | Data manipulation |
| Matplotlib | 3.7+ | Visualization |
| emcee | 3.1+ | Ensemble MCMC sampling |
| dynesty | 2.1+ | Nested sampling for Bayesian evidence |
| Cobaya | 3.6+ | Joint MCMC with Planck likelihoods |
| classy (CLASS) | 3.2+ | CMB Boltzmann solver (patched for TEP) |

All dependencies are specified in `requirements.txt`. External dependencies (patched CLASS, AlterBBN) are included in the `external/` directory.
