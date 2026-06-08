# TEP-HC Scripts

## Full pipeline

```bash
python scripts/run_all.py
```

Runs steps `00`–`09` (environment check through results synthesis). Step `01` installs Cobaya, Planck 2018 likelihoods, and hi_class with the native `tep_mode` patch when missing.

## Step modules

Individual steps live in `scripts/steps/`. See `run_all.py` for the canonical order and CLI flags (`--start-step`, `--stop-step`, `--skip-steps`).

## hi_class native TEP patch

The production physics is the native `tep_mode` background modification patched into hi_class core files (`background.c`, `input.c`, `background.h`). The patch file is `external/patches/hiclass_tep_native.patch` and is applied automatically during step `01` (00b_install).

## Site build

```bash
cd site && npm ci && npm run build:markdown
```

Generates `18-TEP-HC-v0.1-Cambridge.md` at the repository root.

## Figure generation

Figures are not produced by `run_all.py`. After the pipeline completes, run:

```bash
python scripts/generate_figures.py
```

This writes both publication figures to `results/figures/`.

**Inputs:**
- Figure 1 (MCMC point + literature benchmarks): `results/07_mcmc_summary_full.json` and `data/references/literature_benchmarks.json`
- Figure 2: `results/04b_jordan_frame_scan.json` (run step 04b first)

The static site build (`cd site && npm run build`) copies them into `site/dist/figures/`.

## Exact-M acoustic verification (optional)

To confirm that the exact Jordan-frame factor `M_exact = A*(1+alpha_A)` gives the same acoustic result as the implemented `M_code = A/(1-alpha_A)` in the screened CMB regime:

```bash
python scripts/steps/step_04c_exact_m_verification.py
```

**Prerequisites:** step `04b` must have been run first to generate the reference scan.

**What it does:**
1. Temporarily patches `external/hi_class/hi_class/source/background.c` to use `M_exact`
2. Recompiles hi_class
3. Runs the standard `z_T = 5` Jordan scan with `M_exact`
4. Compares `r_s` and `theta_s` against the existing `04b` reference
5. Restores the original code and recompiles

**Output:** `results/04c_exact_m_verification.json`

This step is **not** included in the default `run_all.py` pipeline because it modifies and recompiles the C codebase. Run it manually when you want to remove the last `O(alpha_A^2)` caveat from the manuscript.
