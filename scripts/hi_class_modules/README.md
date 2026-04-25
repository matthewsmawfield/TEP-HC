# TEP hi_class Module

This directory contains the C source code for integrating the Temporal Equivalence Principle (TEP) into hi_class.

## Files

- `tep.c`: Main implementation with Bellini-Sawicki alpha functions
- `tep.h`: Header file with function prototypes

## Installation

1. Copy `tep.c` and `tep.h` to your hi_class installation:
   ```bash
   cp tep.c tep.h /path/to/hi_class/source/models/
   ```

2. Modify hi_class build files to include the TEP model (see main paper Appendix A)

3. Recompile hi_class:
   ```bash
   cd /path/to/hi_class
   make clean && make
   ```

## Key Physics

The TEP model implements:
- Conformal factor: $A(\phi) = \exp(2\beta\phi/M_{\rm Pl})$
- Disformal term: $B(\phi)$ (suppressed at late times)
- Bellini-Sawicki alphas: $\alpha_M, \alpha_T, \alpha_B, \alpha_K$
- Radiation-domination freezing: $T^\mu_\mu \approx 0$ at $z \sim 1100$

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `tep_alpha_eff` | 1e6 | TEP clock-sector coupling |
| `tep_phi_init` | 0.0 | Initial field value |
| `tep_B_coeff` | 0.0 | Disformal coupling |
| `tep_beta` | 1.0 | Conformal coupling |

## References

- Bellini & Sawicki 2014, JCAP 07, 050
- Lagos et al. 2018, JCAP 03, 021 (hi_class)
