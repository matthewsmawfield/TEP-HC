"""Evidence QA without Cobaya, CLASS, dynesty, remote access or production runs."""
import copy
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import evidence_dynesty as runner
from scripts.compare_evidence import compare

class Model:
    def __init__(self, value=0., error=False, delay=0.):
        self.value, self.error, self.delay = value, error, delay
    def loglike(self, params):
        time.sleep(self.delay)
        if self.error:
            raise RuntimeError('solver error')
        return self.value, []

class EvidenceTests(unittest.TestCase):
    def test_ess_is_weight_based(self):
        self.assertAlmostEqual(runner.effective_sample_size([1, 1, 1, 1]), 4)
        self.assertAlmostEqual(runner.effective_sample_size([9, 1]), 100/82)
        with self.assertRaises(ValueError): runner.effective_sample_size([np.nan])

    def test_failure_categories_and_parameter_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runner, '_PARAM_INFO', {'__order__': ['x']}), patch.object(runner, '_EVALUATION_LOG_DIR', tmp), patch.object(runner, '_EVAL_TIMEOUT', 0):
                for model in [Model(-2), Model(-np.inf), Model(np.nan), Model(error=True)]:
                    with patch.object(runner, '_MODEL', model): runner._loglike([3.])
            records=[json.loads(x) for p in Path(tmp).glob('*.jsonl') for x in p.read_text().splitlines()]
            self.assertEqual([x['status'] for x in records], ['finite','model_returned_minus_inf','nonfinite','exception'])
            self.assertNotIn('parameters', records[0])
            self.assertEqual(records[-1]['parameters'], {'x':3.})

    def test_fork_timeout_and_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(runner, '_PARAM_INFO', {'__order__':['x']}), patch.object(runner, '_EVALUATION_LOG_DIR', tmp), patch.object(runner, '_EVAL_TIMEOUT', .1):
                with patch.object(runner, '_MODEL', Model(-3)):
                    self.assertEqual(runner._loglike([1.]), -3)
                with patch.object(runner, '_MODEL', Model(delay=1)):
                    self.assertEqual(runner._loglike([1.]), -np.inf)
            self.assertEqual(runner.evaluation_summary(tmp, True)['coverage'], 'current_invocation_only')
            self.assertEqual(runner.evaluation_summary(tmp, False)['counts']['timeout'], 1)

    def pair(self):
        a={'logz':-10.,'logzerr':.2,'n_call':100,'weights':[.5,.5],'samples':[[1],[2]],'param_priors':{'x':['uniform',0,2]},'evaluation_diagnostics':{'coverage':'entire_run','counts':{'finite':100}},'provenance':{'model_config':{'likelihood':{'same':None},'params':{'x':{'prior':{'min':0,'max':2}}},'theory':{'classy':{'extra_args':{}}}}}}
        b=copy.deepcopy(a);b['logz']=-8.;b['logzerr']=.3;b['param_priors']['epsilon_T']=['uniform',-1,1]
        return a,b

    def test_comparison_and_uncertainty(self):
        r=compare(*self.pair());self.assertEqual(r['status'],'automatic_checks_passed');self.assertEqual(r['delta_logz_tep_minus_lcdm'],2);self.assertAlmostEqual(r['delta_logz_error_independent_runs'],np.sqrt(.13))

    def test_mismatches_and_old_output_never_pass(self):
        a,b=self.pair();b['param_priors']['x']=['uniform',0,3]
        self.assertEqual(compare(a,b)['status'],'review_required')
        a,b=self.pair();del b['provenance'];del b['evaluation_diagnostics']
        r=compare(a,b);self.assertEqual(r['status'],'review_required');self.assertEqual(r['delta_logz_tep_minus_lcdm'],2)

    def test_nan_evidence_not_reported(self):
        a,b=self.pair();b['logz']=float('nan');b['logzerr']=float('nan');r=compare(a,b)
        self.assertIsNone(r['delta_logz_tep_minus_lcdm']);json.dumps(r,allow_nan=False)

if __name__ == '__main__': unittest.main()
