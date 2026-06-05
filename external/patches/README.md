# hi_class Native TEP Patches

`hiclass_tep_native.patch` applies the production **native `tep_mode`** background modification to vanilla [hi_class](https://github.com/miguelzuma/hi_class).

## Patched files

- `source/background.c` — `tep_f_transition`, `tep_gamma_factor`, `tep_M_factor`, `tep_hubble_rate`
- `source/input.c` — `tep_mode`, `epsilon_T`, `z_T`, `n_T` parameter parsing
- `include/background.h` — struct fields and function declarations

## Application

Applied automatically by `scripts/steps/step_00b_install.py` during hi_class installation.

Manual apply (from a vanilla hi_class clone root):

```bash
patch -p1 -i /path/to/TEP-HC/external/patches/hiclass_tep_native.patch
```

## Physics

Authoritative TEP-C0 transition function:

\[
f_T(z) = \ln(1+z)\,\exp\!\left[-(z/z_T)^{n_T}\right]
\]

Hubble modification: \(H_{\rm TEP}(z) = H_{\Lambda{\rm CDM}}(z)\,M(z)\) with the exact Jordan-frame factor \(M(z) = A(z)/(1-\alpha_A(z))\).

This replaces the deprecated SMG alpha-table route (`gravity_model: tep`).
