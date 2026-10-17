"""Regression checks for lost collections and destructive/config-changing resumes."""
import sys, tempfile, unittest, json, yaml
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from scripts.utils.chain_integrity import inspect_chain_prefix, assert_no_active_writer
from scripts.steps.step_06_mcmc import Step06MCMC
from scripts.steps.step_05_cobaya import Step05Cobaya

class SavedRunTests(unittest.TestCase):
    def make_run(self, folder, n_progress=4):
        base=Path(folder)/'example'
        for rank in (1,2):
            base.with_suffix(f'.{rank}.txt').write_text('# weight value\n2 1\n3 2\n')
        base.with_suffix('.checkpoint').write_text('sampler:\n  mcmc:\n    converged: true\n    mpi_size: 2\n')
        base.with_suffix('.progress').write_text(f'# N timestamp Rminus1\n{n_progress} 2026-10-11 0.01\n')
        return base
    def test_progress_counts_collection_rows_not_frequency(self):
        with tempfile.TemporaryDirectory() as folder:
            base=self.make_run(folder)
            report=inspect_chain_prefix(base)
            self.assertTrue(report['valid_completed_run'],report)
            self.assertEqual(report['raw_rows'],4)
            self.assertEqual(sum(c['frequency_count'] for c in report['chains']),10)
    def test_new_checkpoint_cannot_certify_truncated_collections(self):
        with tempfile.TemporaryDirectory() as folder:
            report=inspect_chain_prefix(self.make_run(folder,10))
            self.assertFalse(report['valid_completed_run'])
            self.assertTrue(any('retain 4 rows' in issue for issue in report['issues']))
    def test_rank_mismatch_is_detected(self):
        with tempfile.TemporaryDirectory() as folder:
            report=inspect_chain_prefix(self.make_run(folder),1)
            self.assertFalse(report['valid_completed_run'])
    def test_missing_first_rank_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); nested=root/'example';nested.mkdir()
            base=self.make_run(nested);base.with_suffix('.1.txt').unlink()
            payload=base.with_suffix('.2.txt').read_bytes()
            step=object.__new__(Step06MCMC);step.chain_dir=root
            step.chain_prefix='example';step.pert_prefix='absent1';step.ttteee_prefix='absent2';step.lcdm_ttteee_prefix='absent3'
            with patch('scripts.steps.step_06_mcmc.print_status'):step._delete_old_chains()
            saved=list(root.glob('_preserved/*/example/example.2.txt'))
            self.assertEqual(len(saved),1)
            self.assertEqual(saved[0].read_bytes(),payload)
    def test_active_sampler_output_is_protected(self):
        import portalocker
        with tempfile.TemporaryDirectory() as folder:
            base=self.make_run(folder)
            lock=Path(str(base)+'.input.yaml.locked')
            with lock.open('wb') as handle:
                portalocker.lock(handle,portalocker.LOCK_EX | portalocker.LOCK_NB)
                with self.assertRaisesRegex(RuntimeError,'Live sampler'):
                    assert_no_active_writer(base)
                portalocker.unlock(handle)
            assert_no_active_writer(base)

    def test_setup_preserves_production_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            info={'theory':{'classy':{'path':'local/patched'}},'likelihood':{'sn.pantheonplus':None},'params':{'epsilon_T':{'prior':{'min':0,'max':.3}}},'sampler':{'mcmc':{}},'output':'my_production'}
            text=yaml.safe_dump(info)
            for filename in ['tep_hiclass_suite.yaml','lcdm_comparison.yaml','tep_hiclass_perturbations.yaml']:(root/filename).write_text(text)
            step=object.__new__(Step05Cobaya);step.cobaya_dir=root
            with patch('scripts.steps.step_05_cobaya.print_status'):result=step.run()
            self.assertEqual(len(result['configs_preserved']),3)
            self.assertEqual((root/'tep_hiclass_suite.yaml').read_text(),text)

if __name__=='__main__':unittest.main()
