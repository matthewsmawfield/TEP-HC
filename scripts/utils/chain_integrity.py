"""Validate the saved Cobaya collection against its checkpoint/progress state."""
from pathlib import Path
import hashlib
import re
import numpy as np
import yaml


def inspect_chain_prefix(output_prefix, expected_ranks=None):
    """Return provenance accounting; never infer convergence from file freshness.

    Cobaya MCMC n() is len(collection), after any output thinning. Its final
    progress N is the sum of those lengths across ranks, not frequency weights.
    A completed run must therefore retain at least that many collection rows.
    """
    base = Path(output_prefix)
    issues = []
    checkpoint_path = base.with_suffix('.checkpoint')
    checkpoint = {}
    if checkpoint_path.exists():
        try:
            checkpoint = (yaml.safe_load(checkpoint_path.read_text()) or {}).get('sampler', {}).get('mcmc', {})
        except (ValueError, AttributeError, yaml.YAMLError) as exc:
            issues.append(f'Cannot read checkpoint: {exc}')
    else:
        issues.append('Checkpoint missing')
    ranks = int(checkpoint.get('mpi_size') or expected_ranks or 1)
    if expected_ranks is not None and ranks != expected_ranks:
        issues.append(f'Checkpoint has {ranks} ranks; launch requested {expected_ranks}')
    files = sorted((p for p in base.parent.glob(base.name + '.*.txt')
                    if re.fullmatch(re.escape(base.name) + r'\.\d+\.txt', p.name)),
                   key=lambda p: int(p.name.rsplit('.', 2)[1]))
    found = [int(p.name.rsplit('.', 2)[1]) for p in files]
    if found != list(range(1, ranks + 1)):
        issues.append(f'Expected ranks 1..{ranks}; found {found}')
    chains = []
    header = None
    for path in files:
        try:
            with path.open() as handle:
                columns = handle.readline().lstrip('#').split()
            if header is None:
                header = columns
            elif columns != header:
                issues.append(f'Column mismatch: {path.name}')
            data = np.loadtxt(path, ndmin=2)
            if not len(data) or data.shape[1] != len(columns):
                issues.append(f'Empty or malformed collection: {path.name}')
            if not np.all(np.isfinite(data)):
                issues.append(f'Nonfinite collection: {path.name}')
            w = data[:, columns.index('weight')]
            if np.any(w <= 0) or not np.allclose(w, np.rint(w), rtol=0, atol=1e-8):
                issues.append(f'Invalid frequency counts: {path.name}')
            chains.append({'path': str(path), 'rank': int(path.name.rsplit('.', 2)[1]),
                           'rows': len(data), 'frequency_count': float(w.sum()),
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        except (OSError, ValueError, IndexError) as exc:
            issues.append(f'Cannot load {path.name}: {exc}')
    rows = sum(c['rows'] for c in chains)
    progress = {}
    progress_path = base.with_suffix('.progress')
    if progress_path.exists():
        lines = progress_path.read_text().splitlines()
        headers = next((line.lstrip('#').split() for line in lines if line.startswith('#')), [])
        entries = [line.split() for line in lines if line.strip() and not line.startswith('#')]
        if entries:
            progress = dict(zip(headers, entries[-1]))
            try:
                n = float(progress['N'])
                if not np.isfinite(n) or n < 0 or n > rows:
                    issues.append(f'Progress records N={n:g}, but collections retain {rows} rows')
            except (KeyError, ValueError):
                issues.append('Unreadable progress collection count')
    else:
        issues.append('Progress file missing')
    if not checkpoint.get('converged', False):
        issues.append('Sampler has not certified convergence')
    return {'output_prefix': str(base), 'mpi_size': ranks, 'raw_rows': rows,
            'chains': chains, 'checkpoint': checkpoint, 'last_progress': progress,
            'issues': issues, 'valid_completed_run': not issues}


def require_completed_chains(output_prefix, expected_ranks=None):
    report = inspect_chain_prefix(output_prefix, expected_ranks)
    if report['issues']:
        raise RuntimeError('Saved MCMC output is incomplete or inconsistent: ' +
                           '; '.join(report['issues']))
    return report


def assert_no_active_writer(output_prefix):
    """Do not move output that a live Cobaya sampler has locked."""
    lock = Path(str(output_prefix) + '.input.yaml.locked')
    if not lock.exists():
        return
    from cobaya.output import use_portalocker
    if not use_portalocker():
        raise RuntimeError(f'Cannot safely distinguish an active/stale output lock: {lock}')
    import portalocker
    with lock.open('rb') as handle:
        try:
            portalocker.lock(handle, portalocker.LOCK_EX | portalocker.LOCK_NB)
        except portalocker.exceptions.BaseLockException as exc:
            raise RuntimeError(f'Live sampler holds output lock: {lock}') from exc
        else:
            portalocker.unlock(handle)
