"""Synthetic source/export regressions; no allocated holdout answers are read."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'development'))
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import export_evaluation
from campaign import source_audit


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8')


class ExportRevealContractTests(unittest.TestCase):
    def make_case(self, folder, split='development', reveal=True):
        root = Path(folder)
        corpus, development, final = root/'corpus', root/'development-runs', root/'final-runs'
        case = {'case_id': 'synthetic-case', 'stratum': 'fixture', 'split': split,
                'pmcid': 'SYNTHETIC-IDENTIFIER'}
        write_json(corpus/'manifest.json', {'cases': [case], 'seed': 17, 'as_of': '2026-10-02'})
        work = (final if split == 'holdout' else development)/case['case_id']
        work.mkdir(parents=True)
        generations, reviews = [], []
        for role, variant, when in (
                ('generation-v1', 'v1', '2026-10-02T00:00:00+00:00'),
                ('generation-v2', 'v2', '2026-10-02T00:00:00+00:00'),
                ('review-1', 'review', '2026-10-02T00:01:00+00:00'),
                ('review-2', 'review', '2026-10-02T00:02:00+00:00')):
            path = work/(role+'.json')
            write_json(path, {'evidence': {'journals': []}})
            artifact = {'path': str(path), 'variant': variant,
                        'output_hash': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'sealed_at': when, 'context_id': 'synthetic-'+role,
                        'status': 'completed', 'isolation': 'CONTROLLED_PACKET_FRESH_CONTEXT',
                        'model': 'fixture-model', 'effort': 'fixture-effort'}
            (reviews if role.startswith('review') else generations).append(artifact)
        ledger = {'case_id': case['case_id'], 'stratum': 'fixture', 'split': split,
                  'status': 'diagnosed', 'generations': generations, 'reviews': reviews,
                  'scores': {}, 'changes': [],
                  'lesson_record': {'status': 'completed'},
                  'diagnosis': {'diagnosis': 'Synthetic post-reveal explanation',
                                'no_change_reason': 'No rule change is supported.',
                                'stratum_confirmed': True,
                                'classification_reason': 'Synthetic study design.',
                                'hypotheses': [{'private': 'must not be included'}]}}
        if reveal:
            ledger['revealed_at'] = '2026-10-02T00:03:00+00:00'
        write_json(work/'ledger.json', ledger)
        write_json(corpus/case['case_id']/'answer.json',
                   {'journal': 'Synthetic Sealed Journal', 'license_urls': [], 'permission_basis': 'fixture'})
        return corpus, development, final, work, ledger

    def export_case(self, corpus, development, final, folder):
        return export_evaluation.export(corpus, development, final, Path(folder)/'public.json', {})

    def test_unrevealed_diagnosis_and_identifiers_are_withheld_without_reading_answer(self):
        for split in ('development', 'holdout'):
            with self.subTest(split=split), tempfile.TemporaryDirectory() as folder:
                corpus, development, final, work, _ = self.make_case(folder, split, reveal=False)
                answer = corpus/'synthetic-case'/'answer.json'
                answer.write_text('UNREVEALED ANSWER MUST NEVER BE READ', encoding='utf-8')
                result = self.export_case(corpus, development, final, folder)
                entry = result['cases'][0]
                self.assertNotIn('post_reveal_diagnosis', entry)
                self.assertNotIn('original_outlet', entry)
                self.assertNotIn('pmcid', entry)
                self.assertIsNone(entry['scores'])
                self.assertNotIn('Synthetic post-reveal explanation', json.dumps(result))
                self.assertNotIn('SYNTHETIC-IDENTIFIER', json.dumps(result))

    def test_sealed_revealed_diagnosis_exports_only_public_whitelist(self):
        for split in ('development', 'holdout'):
            with self.subTest(split=split), tempfile.TemporaryDirectory() as folder:
                corpus, development, final, work, _ = self.make_case(folder, split)
                original_ledger = (work/'ledger.json').read_bytes()
                result = self.export_case(corpus, development, final, folder)
                entry = result['cases'][0]
                self.assertEqual(entry['original_outlet'], 'Synthetic Sealed Journal')
                self.assertEqual(entry['pmcid'], 'SYNTHETIC-IDENTIFIER')
                self.assertEqual(entry['post_reveal_diagnosis'], {
                    'diagnosis': 'Synthetic post-reveal explanation',
                    'no_change_reason': 'No rule change is supported.',
                    'stratum_confirmed': True,
                    'classification_reason': 'Synthetic study design.'})
                self.assertNotIn('must not be included', json.dumps(result))
                self.assertEqual((work/'ledger.json').read_bytes(), original_ledger)
                self.assertFalse(result['final_gate']['publish_allowed'])

    def test_revealed_label_does_not_bypass_seals_and_answer_is_not_opened(self):
        for defect in ('missing_review', 'changed_artifact', 'reused_context'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as folder:
                corpus, development, final, work, ledger = self.make_case(folder)
                if defect == 'missing_review':
                    ledger['reviews'] = ledger['reviews'][:1]
                elif defect == 'changed_artifact':
                    Path(ledger['generations'][0]['path']).write_text('{}', encoding='utf-8')
                else:
                    ledger['reviews'][1]['context_id'] = ledger['reviews'][0]['context_id']
                write_json(work/'ledger.json', ledger)
                actual_read = export_evaluation.read
                opened = []

                def recording_read(path):
                    opened.append(Path(path))
                    return actual_read(path)

                with patch('export_evaluation.read', side_effect=recording_read):
                    with self.assertRaises(ValueError):
                        self.export_case(corpus, development, final, folder)
                self.assertFalse(any(p.name == 'answer.json' for p in opened))
                self.assertFalse((Path(folder)/'public.json').exists())

    def test_reveal_timestamp_must_follow_reviews_even_for_development(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus, development, final, work, ledger = self.make_case(folder)
            ledger['revealed_at'] = '2026-10-02T00:00:30+00:00'
            write_json(work/'ledger.json', ledger)
            actual_read, opened = export_evaluation.read, []

            def recording_read(path):
                opened.append(Path(path))
                return actual_read(path)

            with patch('export_evaluation.read', side_effect=recording_read):
                with self.assertRaisesRegex(ValueError, 'reveal|sealed'):
                    self.export_case(corpus, development, final, folder)
            self.assertFalse(any(p.name == 'answer.json' for p in opened))
            self.assertFalse((Path(folder)/'public.json').exists())

    def test_reveal_order_uses_instants_across_timezone_offsets(self):
        for when, allowed in (('2026-10-02T08:03:00+08:00', True),
                              ('2026-10-02T07:59:00+08:00', False)):
            with self.subTest(when=when), tempfile.TemporaryDirectory() as folder:
                corpus, development, final, work, ledger = self.make_case(folder)
                ledger['revealed_at'] = when
                write_json(work/'ledger.json', ledger)
                if allowed:
                    self.assertIn('post_reveal_diagnosis', self.export_case(corpus, development, final, folder)['cases'][0])
                else:
                    with self.assertRaises(ValueError):
                        self.export_case(corpus, development, final, folder)
                    self.assertFalse((Path(folder)/'public.json').exists())

    def test_final_reveal_before_whole_batch_seal_cannot_export(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus, development, final, work, ledger = self.make_case(folder, 'holdout')
            ledger['revealed_at'] = '2026-10-02T00:01:30+00:00'
            write_json(work/'ledger.json', ledger)
            with self.assertRaisesRegex(ValueError, 'reveal|sealed'):
                self.export_case(corpus, development, final, folder)
            self.assertFalse((Path(folder)/'public.json').exists())


class SourceAuditContractTests(unittest.TestCase):
    def fixture(self):
        url, when, support = 'https://publisher.example/journal/scope', '2026-10-02T00:00:00+00:00', 'Original observational studies are considered.'
        ev = {'url': url, 'checked_at': when, 'source_type': 'official', 'support': support}
        value = {'evidence': {'constraints': {}, 'journals': [{'id': '9000-0005',
                  'facts': {'scope': {'status': 'verified', 'value': {'quote': support}, 'evidence': [ev]}}}]},
                 'fit_sequence': []}
        packet = {'policies': [{'url': url, 'checked_at': when, 'source_type': 'official',
                              'status': 'readable_snapshot', 'text': support}],
                  'literature': [{'journal_id': '9000-0005'}]}
        selector = SimpleNamespace(validate=lambda b: [], eligibility=lambda j, c: ('eligible', []))
        return value, packet, selector

    def test_retrieval_timestamp_is_evidence_not_model_supplied_date(self):
        value, packet, selector = self.fixture()
        self.assertEqual(source_audit(value, packet, selector), [])
        value['evidence']['journals'][0]['facts']['scope']['evidence'][0]['checked_at'] = '2026-10-03T00:00:00+00:00'
        self.assertIn('acquisition timestamp changed', ' '.join(source_audit(value, packet, selector)))

    def test_failed_source_capture_never_supports_verified_policy(self):
        value, packet, selector = self.fixture()
        packet['policies'][0]['status'] = 'retrieval_failed'
        self.assertIn('supporting passage absent', ' '.join(source_audit(value, packet, selector)))

    def test_claimed_scope_quote_and_evidence_passage_both_need_support(self):
        value, packet, selector = self.fixture()
        value['evidence']['journals'][0]['facts']['scope']['value']['quote'] = 'All NHANES papers are guaranteed acceptance.'
        self.assertIn('scope quotation absent', ' '.join(source_audit(value, packet, selector)))

    def test_schema_validation_errors_are_preserved_and_unknowns_are_not_promoted(self):
        value, packet, selector = self.fixture()
        sentinel = 'fixture/schema: invalid journal envelope'
        selector.validate = lambda b: [sentinel]
        failures = source_audit(value, packet, selector)
        self.assertEqual(failures, [sentinel])
        value['evidence']['journals'][0]['facts']['jcr'] = {'status': 'unverified', 'value': None, 'evidence': []}
        before = copy.deepcopy(value)
        self.assertEqual(source_audit(value, packet, selector), [sentinel])
        self.assertEqual(value, before)

    def test_bibliographic_record_cannot_verify_journal_policy(self):
        value, packet, selector = self.fixture()
        packet['policies'][0]['source_type'] = 'bibliographic'
        value['evidence']['journals'][0]['facts']['scope']['evidence'][0]['source_type'] = 'bibliographic'
        self.assertIn('bibliographic-only record', ' '.join(source_audit(value, packet, selector)))

    def test_identity_metadata_cannot_be_promoted_to_scope_permission(self):
        value, packet, selector = self.fixture()
        packet['policies'][0]['allowed_fact_fields'] = ['identity']
        self.assertIn('restricted to journal identity metadata', ' '.join(source_audit(value, packet, selector)))

    def test_source_classification_is_fixed_by_capture_provenance(self):
        value, packet, selector = self.fixture()
        value['evidence']['journals'][0]['facts']['scope']['evidence'][0]['source_type'] = 'bibliographic'
        self.assertIn('source classification changed', ' '.join(source_audit(value, packet, selector)))

    def test_undiscovered_candidate_cannot_enter_verified_fit_sequence(self):
        value, packet, selector = self.fixture()
        value['evidence']['journals'][0]['id'] = 'fabricated-journal'
        value['fit_sequence'] = ['fabricated-journal']
        self.assertIn('Undiscovered candidate inserted', ' '.join(source_audit(value, packet, selector)))


if __name__ == '__main__':
    unittest.main()
