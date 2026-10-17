# hi_class Native TEP Patches

Two patches, applied in sequence to vanilla [hi_class](https://github.com/miguelzuma/hi_class) (upstream `hi_class` branch, base commit `50f447c`):

1. `hiclass_tep_native.patch` — production **native `tep_mode`** background modification.
2. `hiclass_tep_perturbation_closure.patch` — **active SMG scalar-perturbation closure** (`gravity_model = tep`, regular `delta_phi` variable, screened kineticity branch). Must be applied *after* the native patch; its hunks on shared files assume the native state.

## Patched files

### `hiclass_tep_native.patch` (background sector)

- `source/background.c` — `tep_f_transition`, `tep_gamma_factor`, `tep_M_factor`, `tep_hubble_rate`
- `source/input.c` — `tep_mode`, `epsilon_T`, `z_T`, `n_T` parameter parsing
- `include/background.h` — struct fields and function declarations

### `hiclass_tep_perturbation_closure.patch` (perturbation sector)

- `gravity_smg/tep.c`, `gravity_smg/include/tep.h` — TEP alpha-function evaluation (`smg_tep_get_alphas`, `smg_tep_get_Gs`), screened kineticity map `w_c = Z_E - 6 beta_A^2`, `tep_kin_boost`, `tep_screening_s`
- `gravity_smg/gravity_functions_smg.c` — pure-conformal `cs2 = 1` override for `gravity_model == tep`
- `gravity_smg/gravity_models_smg.c`, `gravity_smg/input_smg.c` — `gravity_model = tep` registration and parameter parsing
- `gravity_smg/background_smg.c` — scalar-sector background columns (`phi`, `phi'`, `phi''`, `U_phi`) for the analytically prescribed tep scalar
- `gravity_smg/perturbations_smg.c`, `gravity_smg/include/perturbations_smg.h` — `delta_phi` SMG perturbation equations
- `source/perturbations.c` — SMG scalar source wiring
- `source/background.c`, `source/input.c`, `include/background.h` — closure-sector hunks on top of the native patch
- `source/models/tep.c`, `source/models/tep.h` — native background model helpers
- `python/classy.pyx` — Python-interface parameters
- `Makefile` — build adjustments for paths with spaces

## Application

Both patches are applied automatically by `scripts/steps/step_00b_install.py` during hi_class installation.

Manual apply (from a vanilla hi_class clone root, in order):

```bash
patch -p1 -i /path/to/TEP-HC/external/patches/hiclass_tep_native.patch
patch -p1 -i /path/to/TEP-HC/external/patches/hiclass_tep_perturbation_closure.patch
```

## Physics

Authoritative TEP-C0 transition function:

\[
f_T(z) = \ln(1+z)\,\exp\!\left[-(z/z_T)^{n_T}\right]
\]

Hubble modification: \(H_{\rm TEP}(z) = H_{\Lambda{\rm CDM}}(z)\,M(z)\) with the exact Jordan-frame factor \(M(z) = A(z)/(1-\alpha_A(z))\).

The closure patch implements the active linear scalar sector: Bellini–Sawicki functions \(\alpha_M = -2 S_\Sigma \alpha_A\), \(\alpha_B = 2 S_\Sigma \alpha_A\), \(\alpha_K = w_c\,\alpha_A^2\), \(\alpha_T = 0\) evolved through the regular \(\delta\phi\) variable (the \(x_{\rm smg} = \delta\phi/\phi'\) variable is singular at the \(\alpha_A=0\) turnover). The production branch is the screened kineticity regime \(w_c = +700\) (`tep_kin_boost = 10`); the canonical Einstein-frame image \(w_c = -5\) is linearly unstable (see `results/closure_response_scan.json`).
