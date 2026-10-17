#!/usr/bin/env python3
"""
Bayesian evidence computation for TEP-HC (Paper 18)
====================================================
Runs dynesty static nested sampling directly on a cobaya model built
from a yaml config, so the likelihood is exactly the production
hi_class/TEP implementation used by the MCMC runs.

The cobaya model is constructed once per worker process (the wrapped
classy/theory objects are not picklable), the prior transform is built
from the yaml parameter priors (uniform and Gaussian priors supported),
and the evidence is saved as JSON.

Usage (repo root):
    mpirun-unaware; runs a multiprocessing pool itself:
    python scripts/evidence_dynesty.py data/cobaya/tep_native_mcmc_ttteee.yaml \
        --output results/evidence_tep_ttteee.json --nlive 800 --pool 6

Compare TEP vs LCDM by running the same script on the matched LCDM yaml
and taking Delta lnZ = lnZ_TEP - lnZ_LCDM.
"""

import argparse
import hashlib
import uuid
import json
import math
import os
import select
import sys
import time
from multiprocessing import Pool
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("VECLIB_MAXIMUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

import numpy as np
from scipy.special import ndtri

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_MODEL = None
_PARAM_INFO = None
_EVAL_TIMEOUT = 240.0
_EVALUATION_LOG_DIR = None


def _load_param_priors(yaml_path):
    """Extract sampled-parameter priors from the yaml (uniform / Gaussian)."""
    import yaml as _yaml

    with open(yaml_path) as f:
        info = _yaml.safe_load(f)
    out = {}
    for name, spec in (info.get("params") or {}).items():
        if not isinstance(spec, dict) or "prior" not in spec:
            continue
        pr = spec["prior"]
        if "min" in pr and "max" in pr:
            out[name] = ("uniform", float(pr["min"]), float(pr["max"]))
        elif pr.get("dist") == "norm":
            out[name] = ("norm", float(pr["loc"]), float(pr["scale"]))
        else:
            raise ValueError(f"Unsupported prior for {name}: {pr}")
    return out


def _init_worker(yaml_path, eval_timeout=None, evaluation_log_dir=None):
    """Build the cobaya model inside each pool worker."""
    global _MODEL, _PARAM_INFO, _EVAL_TIMEOUT, _EVALUATION_LOG_DIR
    import yaml as _yaml
    from cobaya.model import get_model

    with open(yaml_path) as f:
        info = _yaml.safe_load(f)
    info.setdefault(
        "packages_path",
        str(PROJECT_ROOT / "data" / "external" / "cobaya_packages"))
    _MODEL = get_model(info)
    _PARAM_INFO = _load_param_priors(yaml_path)
    if eval_timeout is not None:
        _EVAL_TIMEOUT = float(eval_timeout)
    _EVALUATION_LOG_DIR = evaluation_log_dir
    # cobaya keeps the sampled-parameter order in model.parameterization
    _PARAM_INFO["__order__"] = list(
        _MODEL.parameterization.sampled_params()
    )


def _prior_transform(u):
    order = _PARAM_INFO["__order__"]
    x = np.empty(len(order))
    for i, name in enumerate(order):
        kind, a, b = _PARAM_INFO[name]
        ui = min(max(float(u[i]), 1e-12), 1.0 - 1e-12)
        if kind == "uniform":
            x[i] = a + ui * (b - a)
        else:  # Gaussian prior: inverse CDF
            x[i] = a + b * ndtri(ui)
    return x


def _evaluate(pdict):
    """Keep a model rejection distinct from an evaluation failure."""
    try:
        ll, _derived = _MODEL.loglike(pdict)
        value = float(ll)
        if value == -np.inf:
            return {"status": "model_returned_minus_inf", "loglike": None}
        if not np.isfinite(value):
            return {"status": "nonfinite", "loglike": None}
        return {"status": "finite", "loglike": value}
    except Exception as exc:
        return {"status": "exception", "loglike": None,
                "exception_type": type(exc).__name__, "message": str(exc)[:1000]}


def _record_evaluation(result, pdict, started):
    if _EVALUATION_LOG_DIR is None:
        return
    record = dict(result, duration_seconds=time.monotonic() - started)
    if result["status"] != "finite":
        record["parameters"] = pdict
    # One append-only file per worker. Errors are intentionally not swallowed:
    # a run must not silently claim diagnostics when its log cannot be written.
    path = Path(_EVALUATION_LOG_DIR) / f"worker-{os.getpid()}.jsonl"
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, allow_nan=False) + "\n")


def _loglike(x):
    started = time.monotonic()
    order = _PARAM_INFO["__order__"]
    pdict = {name: float(v) for name, v in zip(order, x)}
    if _EVAL_TIMEOUT <= 0:
        result = _evaluate(pdict)
    else:
        import warnings
        r_fd, w_fd = os.pipe()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            pid = os.fork()
        if pid == 0:
            try:
                os.close(r_fd)
                payload = json.dumps(_evaluate(pdict), allow_nan=False).encode()
                while payload:
                    written = os.write(w_fd, payload)
                    payload = payload[written:]
            finally:
                os._exit(0)
        os.close(w_fd)
        buf = b""
        timed_out = False
        deadline = time.monotonic() + _EVAL_TIMEOUT
        try:
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    break
                if select.select([r_fd], [], [], min(5.0, remaining))[0]:
                    chunk = os.read(r_fd, 4096)
                    if not chunk:
                        break
                    buf += chunk
        finally:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass
            os.waitpid(pid, 0)
            os.close(r_fd)
        if timed_out:
            result = {"status": "timeout", "loglike": None}
        else:
            try:
                result = json.loads(buf)
            except (ValueError, UnicodeDecodeError):
                result = {"status": "child_failure", "loglike": None}
    _record_evaluation(result, pdict, started)
    return result["loglike"] if result["status"] == "finite" else -np.inf


def effective_sample_size(weights):
    weights = np.asarray(weights, dtype=float)
    if (weights.ndim != 1 or not len(weights) or not np.all(np.isfinite(weights))
            or np.any(weights < 0) or weights.sum() <= 0):
        raise ValueError("Importance weights must be finite, nonnegative and nonempty")
    weights = weights / weights.sum()
    return float(1.0 / np.sum(weights ** 2))


def evaluation_summary(directory, resumed):
    counts = {}
    for path in Path(directory).glob("worker-*.jsonl"):
        for line in path.read_text().splitlines():
            status = json.loads(line)["status"]
            counts[status] = counts.get(status, 0) + 1
    return {"log_directory": str(directory), "counts": counts,
            "coverage": "current_invocation_only" if resumed else "entire_run",
            "note": "A model-returned -inf is not independently certified as a physical exclusion."}


def run_evidence(yaml_path, nlive, dlogz, pool_size, seed,
                 checkpoint=None, resume=False, eval_timeout=None, evaluation_log_dir=None):
    import dynesty

    import yaml
    audit_root = Path(evaluation_log_dir or PROJECT_ROOT / "results" / "evidence_evaluations")
    audit_dir = audit_root / uuid.uuid4().hex
    audit_dir.mkdir(parents=True, exist_ok=False)
    yaml_bytes = Path(yaml_path).read_bytes()
    model_config = yaml.safe_load(yaml_bytes)
    priors = _load_param_priors(yaml_path)
    order = None
    # Build the order once on the main process as well (cheap sanity build).
    _init_worker(yaml_path, eval_timeout, str(audit_dir))
    order = _PARAM_INFO["__order__"]
    ndim = len(order)

    pool = Pool(pool_size, initializer=_init_worker,
                initargs=(yaml_path, eval_timeout, str(audit_dir)))
    if resume and checkpoint and Path(checkpoint).exists():
        sampler = dynesty.NestedSampler.restore(checkpoint, pool=pool)
        sampler.queue_size = pool_size
        sampler.rstate = np.random.default_rng(seed)
    else:
        sampler = dynesty.NestedSampler(
            _loglike,
            _prior_transform,
            ndim,
            bound="multi",
            sample="rwalk",
            nlive=nlive,
            pool=pool,
            queue_size=pool_size,
            rstate=np.random.default_rng(seed),
        )
    sampler.run_nested(dlogz=dlogz, print_progress=True,
                       checkpoint_file=checkpoint, resume=resume)
    res = sampler.results
    pool.close()
    pool.join()

    weights = res.importance_weights()
    out = {
        "provenance": {
            "yaml_sha256": hashlib.sha256(yaml_bytes).hexdigest(),
            "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "model_config": {k: model_config.get(k) for k in ("theory", "likelihood", "params", "prior")},
            "resumed": bool(resume),
        },
        "evaluation_diagnostics": evaluation_summary(audit_dir, resume),
        "yaml": str(yaml_path),
        "n_dim": ndim,
        "param_order": order,
        "nlive": nlive,
        "dlogz_stop": dlogz,
        "logz": float(res.logz[-1]),
        "logzerr": float(res.logzerr[-1]),
        "n_eff": effective_sample_size(weights),
        "sampling_efficiency_percent": float(res.eff),
        "n_call": int(res.ncall.sum()),
        "ess": effective_sample_size(weights),
        "param_priors": {
            k: list(v) for k, v in priors.items()
        },
        "weights": weights.tolist(),
        "samples": res.samples.tolist(),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("yaml", help="cobaya yaml config path")
    ap.add_argument("--output", required=True, help="output JSON path")
    ap.add_argument("--nlive", type=int, default=800)
    ap.add_argument("--dlogz", type=float, default=0.1)
    ap.add_argument("--pool", type=int, default=max(1, os.cpu_count() - 2))
    ap.add_argument("--seed", type=int, default=47)
    ap.add_argument("--checkpoint", default=None,
                    help="dynesty checkpoint file for periodic saves")
    ap.add_argument("--resume", action="store_true",
                    help="resume from --checkpoint if it exists")
    ap.add_argument("--eval-timeout", type=float, default=240.0,
                    help="seconds before a single likelihood evaluation is "
                         "killed and scored -inf (0 disables the guard)")
    ap.add_argument("--evaluation-log-dir", default=None,
                    help="root for per-invocation evaluation audit logs")
    args = ap.parse_args()

    result = run_evidence(
        args.yaml, args.nlive, args.dlogz, args.pool, args.seed,
        checkpoint=args.checkpoint, resume=args.resume,
        eval_timeout=args.eval_timeout, evaluation_log_dir=args.evaluation_log_dir)
    Path(args.output).write_text(json.dumps(result, indent=2, allow_nan=False))
    print(f"logZ = {result['logz']:.3f} +- {result['logzerr']:.3f} "
          f"(ncall={result['n_call']}) -> {args.output}")


if __name__ == "__main__":
    main()
