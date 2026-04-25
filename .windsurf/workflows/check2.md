---
description: Audit the codebase for integrity, statistical rigor, and fabrications, and check manuscript quality
---

1. **Check for Fabricated or Synthetic Data**
   - Verify that all synthetic data generation is explicit, labeled, and not mixed with empirical results.
   - Ensure no data is fabricated or synthetic erroneously. 

2. **Audit Data Cleaning & Cherry-Picking**
   - Ensure data loading scripts do not secretly exclude and include valid data points to improve correlations.

3. **Verify Statistical Rigor**
   - Ensure p-values and statistical tests (Fisher's method, Steiger Z-test) are implemented correctly and not hardcoded.

4. **Check for "Magic Numbers" & Tuning**
   - Ensure the model parameters are constant and not tuned per-script to fit the data.

5. **Reproducibility Check**
   - Ensure all random processes (bootstrapping, MC simulations) use fixed seeds.

6. **Verify Data Integrity:** rigorously check all raw data, calculations, and derived values to ensure there are absolutely no errors, fabrications, or inconsistencies.
7. **Confirm Reproducibility:** Ensure that every step of the analysis can be repeated by an independent researcher to yield the exact same results.
8. **Audit for Accuracy:** Review every factual claim, equation, and scientific statement to guarantee it is strictly correct and valid.
9. **Adopt Professional Tone:** Ensure the language is objective, formal, and precise, avoiding exaggeration, emotive language, or informal phrasing.
10. **Strengthen the Argument:** Review the logical flow to ensure the central thesis is compelling and that the evidence directly supports the conclusions without logical leaps.
11. **Eliminate Mechanical Errors:** Thoroughly proofread the text to remove all typos, grammatical mistakes, and formatting inconsistencies.
12. **Validate References:** Check every citation to ensure the source exists, is relevant, and accurately supports the statement it is attached to.
13. **Clarify Visuals:** Inspect all figures, tables, and charts to ensure they are legible, correctly labeled, and accurately represent the underlying data.
14. **Standardize Terminology:** Ensure that all technical terms, variables, and acronyms are defined clearly and used consistently throughout the entire document. Ensure consistency with other papers in @manuscripts folder.
15. **State Limitations Clearly:** Be transparent about the study’s constraints and uncertainties to ensure the findings are not overstated or misleading.
16. **Test Alternative Explanations:** rigorously review the "Alternative Explanations" section to ensure the rejection of standard physics models is fair and mathematically sound.
17. Do not use 'we'.
18. Ensure appropriate humble tone throughout, no overly self-aggrandizing language or hyperbole.
19. Make sure the paper is strong and presents a good compelling argument.
20. The manuscript should be a pleasure to read and easy to understand and engaging.
21. Ensure consistency throughout
22. we should not use 'we'. 
23. we should not set timelines for future years and future research. we are one independent researcher without institutional backing so should not set unachievable plans.

ALWAYS MAKE CHANGES TO THE MANUSCRIPT SOURCE @COMPONENTS HTML FILES AND NOT THE MARKDOWN DIRECTLY. 