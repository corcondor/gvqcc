"""Small orchestration regressions, using synthetic reports only.

No quantum circuit is verified by these tests. Synthetic PASS fields exercise
the orchestration contract and are confined to temporary directories.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import build_kaggle_score_worker as builder
import reproduce_dqi_candidate as reproduce


def synthetic_factor_report():
    return {
        'status': 'COMPLETE', 'input_sha256': reproduce.CANDIDATE_SHA,
        'output_sha256': reproduce.CANDIDATE_480_SHA, 'window': 256,
        'total_current_block_rewrites': 384, 'static_ccx_reduction': 384,
        'static_cx_added': 768, 'binary_layout_validation': 'passed',
        'identity_proof': {'status': 'PASS'},
        'blocks': [{'condition_stack_depth': 0, 'verified_rewrite_count': 24,
                    'exact_polynomial_proof': {'status': 'PASS'}} for _ in range(16)],
        'fixture_notice': 'Synthetic orchestration fixture, not a verifier result.',
    }


class ReproductionVariants(unittest.TestCase):
    def test_default_preserves_v1_pipeline_and_candidate_path(self):
        work = Path('/synthetic-unused-work')
        commands = []
        with mock.patch.object(reproduce, 'check_pin') as pin:
            candidate, extra = reproduce.build_candidate(
                Path('/synthetic-baseline'), Path('/synthetic-source'), work,
                lambda *args: commands.append(args))
        self.assertEqual(candidate, work / 'dqi.kmb')
        self.assertEqual(extra, {})
        self.assertEqual([c[0] for c in commands], [
            'dqi_ccx_peephole.py', 'dqi_gauge_expand.py',
            'dqi_gauge_expand_verify.py', 'kmb_splice.py'])
        self.assertEqual(commands[-1][-1], candidate)
        pin.assert_called_once_with(candidate, reproduce.CANDIDATE_SHA)

    def test_v2_pins_v1_intermediate_then_adds_exact_factor_step(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            events = []

            def run(*args):
                events.append(('run', args))
                if args[0] == 'dqi_ccx_input_factor.py':
                    report = args[args.index('--report') + 1]
                    report.write_text(json.dumps(synthetic_factor_report()))

            with mock.patch.object(reproduce, 'check_pin',
                                   side_effect=lambda *args: events.append(('pin', args))):
                candidate, extra = reproduce.build_candidate(
                    Path('/synthetic-baseline'), Path('/synthetic-source'), work,
                    run, '480gauge128')
            self.assertEqual(events[4], ('pin', (work / 'dqi_96gauge128.kmb', reproduce.CANDIDATE_SHA)))
            factor_call = events[5][1]
            self.assertEqual(factor_call[0], 'dqi_ccx_input_factor.py')
            self.assertEqual(factor_call[1], work / 'dqi_96gauge128.kmb')
            self.assertEqual(factor_call[factor_call.index('--output') + 1], candidate)
            self.assertEqual(events[6], ('pin', (candidate, reproduce.CANDIDATE_480_SHA)))
            self.assertEqual(extra['input_factor']['additional_static_ccx_reduction'], 384)
            self.assertEqual(extra['input_factor']['report_sha256'],
                             reproduce.sha256(work / 'dqi_input_factor384.json'))

    def test_wrong_intermediate_stops_before_factorization(self):
        commands = []
        with mock.patch.object(reproduce, 'check_pin', side_effect=ValueError('wrong SHA')):
            with self.assertRaises(ValueError):
                reproduce.build_candidate(Path('/baseline'), Path('/source'), Path('/work'),
                                          lambda *args: commands.append(args), '480gauge128')
        self.assertNotIn('dqi_ccx_input_factor.py', [c[0] for c in commands])

    def test_partial_or_mismatched_factor_evidence_is_rejected(self):
        for key, value in [('status', 'TIME_BOUNDED_PARTIAL'),
                           ('static_ccx_reduction', 383),
                           ('input_sha256', reproduce.BASELINE_SHA),
                           ('output_sha256', reproduce.CANDIDATE_SHA),
                           ('total_current_block_rewrites', 0)]:
            with self.subTest(field=key):
                report = synthetic_factor_report()
                report[key] = value
                with self.assertRaises(RuntimeError):
                    reproduce.validate_input_factor_report(report)
        for replacement in [None, {'status': 'FAIL'}]:
            with self.subTest(proof=replacement):
                report = synthetic_factor_report()
                report['blocks'][0]['exact_polynomial_proof'] = replacement
                with self.assertRaises(RuntimeError):
                    reproduce.validate_input_factor_report(report)

    def test_bad_factor_count_does_not_claim_final_candidate_pin(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            report = synthetic_factor_report()
            report['static_ccx_reduction'] = 383

            def run(*args):
                if args[0] == 'dqi_ccx_input_factor.py':
                    args[args.index('--report') + 1].write_text(json.dumps(report))

            with mock.patch.object(reproduce, 'check_pin') as pin:
                with self.assertRaises(RuntimeError):
                    reproduce.build_candidate(Path('/baseline'), Path('/source'), work,
                                              run, '480gauge128')
            pin.assert_called_once_with(work / 'dqi_96gauge128.kmb', reproduce.CANDIDATE_SHA)

    def test_builder_v2_uses_distinct_artifacts_and_embeds_factor_script(self):
        v1 = builder.worker_settings(reproduce.DEFAULT_VARIANT)
        v2 = builder.worker_settings('480gauge128')
        self.assertEqual(v1['worker_filename'], 'kaggle_score_worker.py')
        self.assertEqual(v2['worker_filename'], 'kaggle_score_worker_v2.py')
        self.assertNotEqual(v1['build_filename'], v2['build_filename'])
        self.assertNotIn('dqi_ccx_input_factor.py', v1['scripts'])
        self.assertIn('dqi_ccx_input_factor.py', v2['scripts'])
        self.assertEqual(v1['candidate_sha256'], reproduce.CANDIDATE_SHA)
        self.assertEqual(v2['candidate_sha256'], reproduce.CANDIDATE_480_SHA)


if __name__ == '__main__':
    unittest.main()
