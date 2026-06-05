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

Generates `18-TEP-HC-v0.1-Geneva.md` at the repository root.

## Figure generation

Figures are not produced by `run_all.py`. After the pipeline completes, run:

```bash
python scripts/generate_figures.py
```

This writes publication figures to `results/figures/`. The static site build (`cd site && npm run build`) copies them into `site/dist/figures/`.
