# Evidence comparison and numerical diagnostics

The existing remote jobs are not changed by these local edits. Do not replace a
running deployment or resume its checkpoint with changed model settings merely
to obtain these diagnostics.

When both remote result files have been copied back, run from TEP-HC:

```sh
python scripts/compare_evidence.py results/evidence_lcdm.json results/evidence_tep_ttteee.json --output results/evidence_comparison.json
```

The command is read-only except for the requested report. Missing files produce
`pending`; missing metadata, failures or incompatible settings produce
`review_required` and exit code 2. It computes ΔlnZ = lnZ_TEP - lnZ_LCDM, the
quadrature combination of independent-run reported errors, log10(Bayes factor),
and posterior ESS = 1/sum(normalized weights squared). It checks recorded shared
priors, likelihoods, theory options and fixed/derived parameter definitions.
No blanket ESS threshold or automatic scientific-significance label is applied.
`automatic_checks_passed` is not a certification of model correctness or adequate
sampling. A runtime code/data/build identity comparison remains a manual check.

The current configs compare a background TEP modification with a matched LCDM
baseline. Both contain a nonzero CDM density parameter. A positive ΔlnZ supports
that configured comparison, not every TEP sector or a fully CDM-free replacement.

For subsequent local invocations, evidence_dynesty.py records a YAML hash and
configuration snapshot, a runner hash, weight-based ESS, and per-worker JSONL
evaluation records under results/evidence_evaluations/<invocation-id>/.
--evaluation-log-dir can change the root. Records distinguish finite evaluations,
model-returned minus infinity, NaN/+infinity, exceptions, timeouts and child
failures; unsuccessful records retain the sampled parameters for diagnosis.
Model-returned minus infinity is not automatically a physical exclusion: the
underlying solver may itself convert numerical failures to rejection.
The likelihood score and prior definitions are unchanged. Numerical failures
still receive -infinity, but are now visible and require investigation before a
scientific evidence claim. Audit write failures are not silently ignored.

On resumed runs the audit is labelled current_invocation_only. The missing past
history is not certified. Existing remote output weights allow ESS recomputation,
but final JSONs cannot reveal the causes or locations of past timeouts/errors.
Use original logs and targeted evaluations to investigate; a rerun is needed
only if that review demonstrates an unresolved material numerical bias.

The old runner's n_eff field was an efficiency-derived count, not posterior ESS.
The new n_eff and ess both use importance weights; sampling_efficiency_percent
preserves the separate computational-efficiency diagnostic.

Tests (no production inference or remote access):

```sh
python -m unittest discover -s tests -p test_evidence_review.py -v
```
