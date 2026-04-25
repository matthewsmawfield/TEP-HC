---
description: Audit the codebase for integrity, statistical rigor, and fabrications
---

1. **Check for Fabricated or Synthetic Data**
   - Verify that all synthetic data generation is explicit, labeled, and not mixed with empirical results.

2. **Audit Data Cleaning & Cherry-Picking**
   - Ensure data loading scripts do not secretly exclude and include valid data points to improve correlations.

3. **Verify Statistical Rigor**
   - Ensure p-values and statistical tests (Fisher's method, Steiger Z-test) are implemented correctly and not hardcoded.

4. **Check for "Magic Numbers" & Tuning**
   - Ensure the model parameters  are constant and not tuned per-script to fit the data.

5. **Reproducibility Check**
   - Ensure all random processes (bootstrapping, MC simulations) use fixed seeds.
