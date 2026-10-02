"""Synthetic preparation and 50-case gate fixtures; no real holdout is accessed."""
import copy
import hashlib
import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from preparation_seal import (MANIFEST_NAME, REQUIRED_FILES, PreparationSealError,
                              seal_preparation, verify_preparation_seal, require_final_preparation)
import campaign

SEALED_AT = '2026-10-03T00:00:10+00:00'


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding='utf-8', newline='\n')


def completed_call(work, name, value, case_id, started='2026-10-03T00:00:00+00:00',
                   completed='2026-10-03T00:00:05+00:00'):
    output = work/name
    write_json(output, value)
    message = output.read_text(encoding='utf-8')
    context = case_id+'-'+name
    record = {'status': 'completed', 'context_id': context, 'started_at': started,
              'completed_at': completed, 'output_hash': hashlib.sha256(output.read_bytes()).hexdigest(),
              'model_turn_completed': True, 'terminal_output_matches': True,
              'isolation': 'CONTROLLED_PACKET_FRESH_CONTEXT'}
    write_json(work/(name+'.record.json'), record)
    events = [{'type': 'thread.started', 'thread_id': context},
              {'type': 'item.completed', 'item': {'type': 'agent_message', 'text': message}},
              {'type': 'turn.completed', 'usage': {'output_tokens': 1}}]
    (work/(name+'.events.jsonl')).write_text('\n'.join(json.dumps(e) for e in events), encoding='utf-8', newline='\n')
    (work/(name+'.input.txt')).write_text('Synthetic input, never a manuscript answer', encoding='utf-8')
    return {'path': str(output.resolve()), 'variant': name.split('-selection')[0],
            'context_id': context, 'output_hash': record['output_hash'],
            'status': 'completed', 'sealed_at': completed,
            'isolation': 'CONTROLLED_PACKET_FRESH_CONTEXT'}


def fixture(root, case_id='synthetic-case-001'):
    corpus, runs = root/'corpus', root/'runs'
    source, work = corpus/case_id, runs/case_id
    source.mkdir(parents=True)
    work.mkdir(parents=True)
    (source/'source.xml').write_text('<fixture>RAW SYNTHETIC PAPER MUST NEVER BE EXPORTED</fixture>', encoding='utf-8')
    masked = 'SYNTHETIC MANUSCRIPT CONTENT MUST NEVER APPEAR IN THE SEAL'
    (source/'masked.txt').write_text(masked, encoding='utf-8')
    (source/'answer.json').write_text('SYNTHETIC ANSWER FILE MUST NOT BE OPENED', encoding='utf-8')
    profile = {'keywords': ['synthetic', 'cohort'], 'abstract_summary': 'Synthetic summary.'}
    plan = {'journals': []}
    completed_call(work, 'profile.json', profile, case_id)
    completed_call(work, 'source-plan.json', plan, case_id)
    retrieval = [{'url': 'https://www.ebi.ac.uk/fixture', 'checked_at': '2026-10-03T00:00:06+00:00'}]
    write_json(work/'literature.json', {'papers': [], 'records': retrieval})
    write_json(work/'policies.json', [])
    write_json(work/'fixed-baselines.json', {'keyword': [], 'abstract': []})
    write_json(work/'candidate-handoff.json', [])
    write_json(work/'policies.retrieval.json', {'captured_record_count': 0})
    write_json(work/'generator-packet.json', {'manuscript': masked, 'profile': profile, 'source_plan': plan,
                                            'literature': [], 'policies': [], 'retrieval_records': retrieval,
                                            'started_at': '2026-10-03T00:00:00+00:00'})
    input_hash = hashlib.sha256(masked.encode()).hexdigest()
    return corpus, runs, source, work, input_hash


def make_seal(work, source, case_id, input_hash):
    with patch('preparation_seal.stamp', return_value=SEALED_AT):
        return seal_preparation(work, source, case_id, expected_masked_hash=input_hash)


def execution_ledger(work, case_id, binding, input_hash):
    generations = [completed_call(work, name+'-selection.json', {'fit_sequence': []}, case_id,
                                  started='2026-10-03T00:00:20+00:00', completed='2026-10-03T00:00:25+00:00')
                   for name in ('v1', 'v2')]
    reviews = [completed_call(work, 'review-'+str(i)+'.json', {'systems': {}}, case_id,
                             started='2026-10-03T00:00:30+00:00', completed='2026-10-03T00:00:35+00:00')
               for i in (1, 2)]
    return {'case_id': case_id, 'split': 'holdout', 'status': 'reviewed',
            'preparation_seal': binding, 'masked_input_hash': input_hash,
            'generations': generations, 'reviews': reviews,
            'scores': {'v2': {'usable': False, 'true_rank': None}}}


class PreparationSealTests(unittest.TestCase):
    def test_seal_pins_all_four_comparator_inputs_without_raw_contents(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            manifest = verify_preparation_seal(work, binding, case_id='synthetic-case-001',
                                               source_case_dir=source, expected_masked_hash=input_hash)
            self.assertEqual(binding['sealed_at'], SEALED_AT)
            self.assertEqual(set(manifest['files']), set(REQUIRED_FILES))
            self.assertEqual(set(manifest['source_files']), {'source.xml', 'masked.txt'})
            self.assertEqual(manifest['comparators'], ['keyword', 'abstract', 'v1', 'v2'])
            text = (work/MANIFEST_NAME).read_text(encoding='utf-8')
            self.assertNotIn('RAW SYNTHETIC PAPER', text)
            self.assertNotIn('SYNTHETIC MANUSCRIPT CONTENT', text)
            self.assertNotIn('answer.json', text)

    def test_every_shared_file_source_or_manifest_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            paths = [work/name for name in REQUIRED_FILES]+[source/'source.xml', source/'masked.txt', work/MANIFEST_NAME]
            for path in paths:
                with self.subTest(path=path.name):
                    original = path.read_bytes()
                    path.write_bytes(original+b' tampered')
                    try:
                        with self.assertRaises(PreparationSealError):
                            verify_preparation_seal(work, binding, case_id='synthetic-case-001',
                                                    source_case_dir=source, expected_masked_hash=input_hash)
                    finally:
                        path.write_bytes(original)

    def test_missing_input_cannot_create_a_seal(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            (work/'policies.retrieval.json').unlink()
            with self.assertRaises(PreparationSealError):
                make_seal(work, source, 'synthetic-case-001', input_hash)
            self.assertFalse((work/MANIFEST_NAME).exists())

    def test_seal_reuse_requires_original_binding_and_preserves_time_and_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            original = (work/MANIFEST_NAME).read_bytes()
            execution_ledger(work, 'synthetic-case-001', binding, input_hash)
            with self.assertRaises(PreparationSealError):
                seal_preparation(work, source, 'synthetic-case-001', expected_masked_hash=input_hash)
            with patch('preparation_seal.stamp', return_value='2026-10-03T10:00:00+00:00'):
                reused = seal_preparation(work, source, 'synthetic-case-001', expected_masked_hash=input_hash,
                                          existing_binding=binding)
            self.assertEqual(reused, binding)
            self.assertEqual((work/MANIFEST_NAME).read_bytes(), original)

    def test_missing_pinned_manifest_is_not_recreated(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            (work/MANIFEST_NAME).unlink()
            with self.assertRaises(PreparationSealError):
                seal_preparation(work, source, 'synthetic-case-001', existing_binding=binding)
            self.assertFalse((work/MANIFEST_NAME).exists())

    def test_no_late_seal_after_request_failed_attempt_review_lesson_or_reveal(self):
        for marker in ('v1-selection.json.input.txt', 'v2-selection.json.record.json',
                       'review-1.json.events.jsonl', 'lesson.json', 'revealed_ledger'):
            with self.subTest(marker=marker), tempfile.TemporaryDirectory() as folder:
                _, _, source, work, input_hash = fixture(Path(folder))
                if marker == 'revealed_ledger':
                    write_json(work/'ledger.json', {'revealed_at': '2026-10-03T00:00:07+00:00'})
                else:
                    (work/marker).write_text('retained genuine execution marker', encoding='utf-8')
                with self.assertRaisesRegex(PreparationSealError, 'after|retrofit'):
                    make_seal(work, source, 'synthetic-case-001', input_hash)
                self.assertFalse((work/MANIFEST_NAME).exists())

    def test_preparation_must_really_complete_before_seal(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            record = json.loads((work/'source-plan.json.record.json').read_text(encoding='utf-8'))
            record['completed_at'] = '2026-10-03T00:00:30+00:00'
            write_json(work/'source-plan.json.record.json', record)
            with self.assertRaisesRegex(PreparationSealError, 'completed after'):
                make_seal(work, source, 'synthetic-case-001', input_hash)
            self.assertFalse((work/MANIFEST_NAME).exists())

    def test_forged_terminal_message_does_not_establish_preparation_completion(self):
        with tempfile.TemporaryDirectory() as folder:
            _, _, source, work, input_hash = fixture(Path(folder))
            (work/'profile.json.events.jsonl').write_text(json.dumps({'type': 'turn.completed'}), encoding='utf-8')
            with self.assertRaisesRegex(PreparationSealError, 'terminal event'):
                make_seal(work, source, 'synthetic-case-001', input_hash)

    def test_wrong_case_source_or_allocation_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            _, _, source, work, input_hash = fixture(root)
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            _, _, other_source, _, _ = fixture(root, 'synthetic-case-002')
            for args in ({'case_id': 'synthetic-case-002', 'source_case_dir': source},
                         {'case_id': 'synthetic-case-001', 'source_case_dir': other_source},
                         {'case_id': 'synthetic-case-001', 'source_case_dir': source, 'expected_masked_hash': 'wrong'}):
                with self.subTest(args=args), self.assertRaises(PreparationSealError):
                    verify_preparation_seal(work, binding, **args)


class FinalPreparationGateTests(unittest.TestCase):
    def test_all_fifty_are_verified_before_any_answer_can_be_opened(self):
        with tempfile.TemporaryDirectory() as folder:
            root, records = Path(folder), []
            for i in range(50):
                case_id = 'synthetic-case-'+str(i).zfill(3)
                corpus, runs, source, work, input_hash = fixture(root, case_id)
                binding = make_seal(work, source, case_id, input_hash)
                records.append(execution_ledger(work, case_id, binding, input_hash))
            original = copy.deepcopy(records)
            actual_open, answers = Path.open, []

            def guard_open(path, *args, **kwargs):
                if path.name == 'answer.json':
                    answers.append(path)
                    raise AssertionError('Final validation must not read an answer')
                return actual_open(path, *args, **kwargs)

            with patch.object(Path, 'open', autospec=True, side_effect=guard_open):
                self.assertTrue(require_final_preparation(records, corpus, runs))
                (runs/records[-1]['case_id']/'fixed-baselines.json').write_text('{}', encoding='utf-8')
                with self.assertRaisesRegex(PreparationSealError, 'fixed-baselines'):
                    require_final_preparation(records, corpus, runs)
            self.assertEqual(answers, [])
            self.assertEqual(records, original)
            self.assertFalse(records[0]['scores']['v2']['usable'])

    def test_partial_duplicate_and_unsealed_batches_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus, runs, source, work, input_hash = fixture(Path(folder))
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            ledger = execution_ledger(work, 'synthetic-case-001', binding, input_hash)
            for records, count in (([ledger], 50), ([ledger, ledger], 2),
                                   ([{**ledger, 'preparation_seal': None}], 1)):
                with self.subTest(count=count), self.assertRaises(PreparationSealError):
                    require_final_preparation(records, corpus, runs, expected_count=count)

    def test_seal_after_model_start_is_rejected_using_actual_receipt_time(self):
        with tempfile.TemporaryDirectory() as folder:
            corpus, runs, source, work, input_hash = fixture(Path(folder))
            binding = make_seal(work, source, 'synthetic-case-001', input_hash)
            ledger = execution_ledger(work, 'synthetic-case-001', binding, input_hash)
            path = work/'v1-selection.json.record.json'
            record = json.loads(path.read_text(encoding='utf-8'))
            record['started_at'] = '2026-10-03T00:00:09+00:00'
            write_json(path, record)
            with self.assertRaisesRegex(PreparationSealError, 'execution began'):
                require_final_preparation([ledger], corpus, runs, expected_count=1)

    def test_executed_receipt_must_match_the_artifact_and_terminal_event(self):
        for defect in ('context', 'terminal', 'contract'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as folder:
                corpus, runs, source, work, input_hash = fixture(Path(folder))
                binding = make_seal(work, source, 'synthetic-case-001', input_hash)
                ledger = execution_ledger(work, 'synthetic-case-001', binding, input_hash)
                path = work/'review-2.json.record.json'
                record = json.loads(path.read_text(encoding='utf-8'))
                if defect == 'context':
                    record['context_id'] = 'wrong-context'
                elif defect == 'contract':
                    record['output_contract_status'] = 'failed'
                else:
                    (work/'review-2.json.events.jsonl').write_text('{"type":"turn.failed"}', encoding='utf-8')
                write_json(path, record)
                with self.assertRaises(PreparationSealError):
                    require_final_preparation([ledger], corpus, runs, expected_count=1)


class CampaignPreparationIntegrationTests(unittest.TestCase):
    def mock_calls(self, work, case_id, damage_after_first=False):
        selected = []

        def select(packet, skill, output):
            ledger = json.loads((work/'ledger.json').read_text(encoding='utf-8'))
            self.assertEqual(ledger['preparation_seal']['sealed_at'], SEALED_AT)
            value = {'evidence': {'constraints': {}, 'journals': []}, 'fit_sequence': [], 'report_notes': []}
            completed_call(work, Path(output).name, value, case_id,
                           started='2026-10-03T00:00:20+00:00', completed='2026-10-03T00:00:25+00:00')
            selected.append(Path(output).name)
            if damage_after_first:
                (work/'fixed-baselines.json').write_text('{}', encoding='utf-8')
            return value, json.loads(Path(str(output)+'.record.json').read_text(encoding='utf-8'))

        def review(packet, anonymous, output, disputed=None):
            labels = list(anonymous['systems'])
            value = {
                'systems': {label: {
                    'hard_failures': [], 'usable_journal_ids': [], 'quality_notes': [],
                    'ranking_assessment': {'judgment': 'empty',
                                           'reason': 'Synthetic result has no ranked candidates.',
                                           'sources': []},
                } for label in labels},
                'pairwise_decisions': [
                    {'left': left, 'right': right, 'decision': 'tie',
                     'reason': 'Both synthetic results have empty candidate rankings.'}
                    for left, right in itertools.combinations(labels, 2)
                ],
            }
            completed_call(work, Path(output).name, value, case_id,
                           started='2026-10-03T00:00:30+00:00', completed='2026-10-03T00:00:35+00:00')
            # The production gate verifies the actual shared packet and the
            # four-result request against runner's original input identity.
            prompt = json.dumps(packet, ensure_ascii=False)+'\n'+json.dumps(anonymous, ensure_ascii=False)
            input_path = Path(str(output)+'.input.txt')
            input_path.write_text(prompt, encoding='utf-8', newline='\n')
            record_path = Path(str(output)+'.record.json')
            record = json.loads(record_path.read_text(encoding='utf-8'))
            record.update(model='gpt-6.1-sol', effort='xhigh')
            record['input_hash'] = hashlib.sha256(
                input_path.read_bytes()+record['model'].encode()+record['effort'].encode()+
                b'controlled-packet-env-closed-tools-disabled-v3').hexdigest()
            write_json(record_path, record)
            return value, record

        return select, review, selected

    def run_fixture(self, root, *, damage=False, retry=False):
        corpus, runs, source, work, input_hash = fixture(root)
        case_id = 'synthetic-case-001'
        case = {'case_id': case_id, 'input_hash': input_hash, 'stratum': 'clinical_nursing',
                'split': 'holdout', 'license': 'fixture'}
        original = None
        if retry:
            binding = make_seal(work, source, case_id, input_hash)
            original = (work/MANIFEST_NAME).read_bytes()
            write_json(work/'ledger.json', {'case_id': case_id, 'status': 'infrastructure_failed',
                                          'preparation_seal': binding, 'failure': 'retained fixture interruption',
                                          'scores': {'v2': {'usable': False}}})
        packet = json.loads((work/'generator-packet.json').read_text(encoding='utf-8'))
        baselines = json.loads((work/'fixed-baselines.json').read_text(encoding='utf-8'))
        select, review, selected = self.mock_calls(work, case_id, damage)
        selector = SimpleNamespace(validate=lambda evidence: [])
        with patch('preparation_seal.stamp', return_value=SEALED_AT), \
             patch('review_bundle.stamp', return_value='2026-10-03T00:00:27+00:00'), \
             patch('campaign.prepare_case', return_value=(packet, baselines)) as prepare, \
             patch('campaign.skill_packet', return_value='Synthetic frozen instructions'), \
             patch('campaign.select', side_effect=select), \
             patch('campaign.review', side_effect=review) as reviewer, \
             patch('campaign.model_json', side_effect=AssertionError('Synthetic fixture must never request a real model')) as model, \
             patch('runner.subprocess.Popen', side_effect=AssertionError('Synthetic fixture must never launch a model process')) as process:
            result = campaign.execute(case, corpus, runs, {'v1': root/'v1', 'v2': root/'v2'}, selector, '2026-10-03')
            model.assert_not_called()
            process.assert_not_called()
        return result, selected, prepare.call_count, reviewer.call_count, work, original

    def test_new_case_seals_and_saves_binding_before_first_model_selection(self):
        with tempfile.TemporaryDirectory() as folder:
            result, selected, prepared, reviews, _, _ = self.run_fixture(Path(folder))
            self.assertEqual(result['status'], 'reviewed', result.get('failure'))
            self.assertEqual(selected, ['v1-selection.json', 'v2-selection.json'])
            self.assertEqual(prepared, 1)
            self.assertEqual(reviews, 2)
            self.assertNotIn('revealed_at', result)

    def test_tamper_after_first_generation_blocks_second_and_reviews(self):
        with tempfile.TemporaryDirectory() as folder:
            result, selected, _, reviews, _, _ = self.run_fixture(Path(folder), damage=True)
            self.assertEqual(result['status'], 'contamination_failed')
            self.assertEqual(selected, ['v1-selection.json'])
            self.assertEqual(reviews, 0)
            self.assertIn('fixed-baselines', result['failure'])
            self.assertNotIn('revealed_at', result)

    def test_retry_reuses_original_packet_seal_and_retains_failed_ledger(self):
        with tempfile.TemporaryDirectory() as folder:
            result, _, prepared, _, work, original = self.run_fixture(Path(folder), retry=True)
            self.assertEqual(result['status'], 'reviewed', result.get('failure'))
            self.assertEqual(prepared, 0)
            self.assertEqual((work/MANIFEST_NAME).read_bytes(), original)
            archived = json.loads((work/'ledger-attempts'/'ledger-attempt-01.json').read_text(encoding='utf-8'))
            self.assertEqual(archived['status'], 'infrastructure_failed')
            self.assertFalse(archived['scores']['v2']['usable'])

    def test_old_completed_development_record_is_not_retrosealed_or_rescored(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            work = root/'runs'/'old-case'
            old = {'case_id': 'old-case', 'status': 'completed', 'lesson_status': 'completed',
                   'protocol_hashes': {'campaign.py': 'legacy'}, 'scores': {'v2': {'usable': False, 'true_rank': None}}}
            write_json(work/'ledger.json', old)
            original = (work/'ledger.json').read_bytes()
            with patch('campaign.prepare_case') as prepare:
                result = campaign.execute({'case_id': 'old-case', 'split': 'development'}, root/'corpus',
                                          root/'runs', {}, None, '2026-10-03')
            prepare.assert_not_called()
            self.assertEqual(result, old)
            self.assertEqual((work/'ledger.json').read_bytes(), original)
            self.assertFalse((work/MANIFEST_NAME).exists())

    def test_new_protocol_reveal_and_diagnosis_reject_missing_seal_before_answer_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            case = {'case_id': 'case', 'split': 'development'}
            ledger = {'protocol_hashes': {'preparation_seal.py': 'fixture'}}
            with patch('campaign.read') as reader, patch('campaign.model_json') as model:
                with self.assertRaises(PreparationSealError):
                    campaign.reveal_case(case, root/'corpus', root/'runs', ledger, {}, [], {}, None)
                with self.assertRaises(PreparationSealError):
                    campaign.diagnose(case, root/'corpus', root/'runs', ledger, {}, [], {})
            reader.assert_not_called()
            model.assert_not_called()


if __name__ == '__main__':
    unittest.main()
