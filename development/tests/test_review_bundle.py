"""Synthetic four-object review and answer-free integrity regressions."""
import copy
import hashlib
import itertools
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import review_bundle as bundle


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def inputs():
    packet = {'literature': [
        {'journal_id': jid, 'journal': title, 'title': 'Synthetic study '+jid,
         'abstract': 'Synthetic design and study findings', 'record_url': 'https://example.invalid/paper/'+jid,
         'checked_at': '2026-10-03T00:00:00+00:00', 'source_type': 'bibliographic',
         'read_extent': 'Supplied title and abstract'}
        for jid, title in (('j-one', 'Journal One'), ('j-two', 'Journal Two'))],
        'policies': [{'url': 'https://example.invalid/journal/policy', 'text': 'Actual supplied policy text',
                      'source_type': 'official', 'checked_at': '2026-10-03T00:00:00+00:00'}]}
    baselines = {'keyword': [{'journal_id': 'j-two', 'score': 4.25}, {'journal_id': 'j-one', 'score': 2.0}],
                 'abstract': [{'journal_id': 'j-one', 'score': 0.82}]}
    outputs = {}
    for variant in ('v1', 'v2'):
        outputs[variant] = {'evidence': {'schema_version': '1.0',
            'run': {'model': 'gpt-synthetic-generation', 'skill_name': 'medical-journal-selector',
                    'skill_version': variant, 'context_id': 'private-'+variant},
            'profile': {'field': 'Medicine', 'model': 'Cox regression', 'version': 'clinical software 2'},
            'constraints': {'time_endpoint': 'acceptance'},
            'journals': [{'id': 'j-one', 'title': 'Journal One', 'ranking_category': 'suggested',
                          'facts': {'scope': {'status': 'unverified', 'value': None, 'evidence': [],
                                             'reason': 'No scope snapshot supplied'},
                                    'method_policy': {'status': 'verified',
                                                      'value': {'model': 'Cox regression', 'version': '2', 'provider': 'University'},
                                                      'evidence': [{'url': 'https://example.invalid/journal/policy',
                                                                    'checked_at': '2026-10-03T00:00:00+00:00',
                                                                    'source_type': 'official', 'support': 'Actual supplied policy text'}]}}}]},
                            'fit_sequence': ['j-one'],
                            'report_notes': ['Skill '+variant+' used gpt-synthetic-generation.']}
    return packet, baselines, outputs


def review_for(private, winner='v2'):
    mapping = private['label_to_comparator']
    inverse = {variant: label for label, variant in mapping.items()}
    value = {'systems': {label: {'hard_failures': [], 'usable_journal_ids': ['j-one'],
                                 'quality_notes': ['Check the actual supplied sources.'],
                                 'ranking_assessment': {'judgment': 'partly_supported',
                                                        'reason': 'Shared study design matches the actual bibliographic sources.',
                                                        'sources': ['https://example.invalid/paper/j-one']}}
                         for label in bundle.LABELS},
             'pairwise_decisions': []}
    for left, right in itertools.combinations(bundle.LABELS, 2):
        variants = {mapping[left], mapping[right]}
        # An abstract comparator may win all its pairs, while the separately
        # evaluated V1/V2 pair still favors V2. No overall-winner inference.
        decision = inverse['abstract'] if 'abstract' in variants else (
            inverse[winner] if {'v1', 'v2'} == variants else 'tie')
        value['pairwise_decisions'].append({'left': left, 'right': right, 'decision': decision,
                                           'reason': 'Synthetic source-grounded pair assessment.'})
    return value


def sealed_fixture(root):
    work = Path(root)/'synthetic-case-001'
    work.mkdir()
    packet, baselines, outputs = inputs()
    preparation = {'path': str(work/'preparation-seal.json'), 'manifest_hash': 'synthetic-original-binding'}
    write(work/'preparation-seal.json', {'synthetic': 'already sealed shared preparation'})
    write(work/'generator-packet.json', packet)
    write(work/'fixed-baselines.json', baselines)
    for variant in ('v1', 'v2'):
        write(work/(variant+'-selection.json'), outputs[variant])
    binding, entries = bundle.seal_review_bundles(work, work.name, packet, baselines, outputs, preparation)
    ledger = {'case_id': work.name, 'review_bundle_contract': bundle.CONTRACT,
              'review_bundle_seal': binding, 'review_bundles': entries, 'preparation_seal': preparation, 'reviews': []}
    for index in (1, 2):
        public = json.loads((work/f'review-{index}.bundle.json').read_text(encoding='utf-8'))
        private = json.loads((work/f'review-{index}.identity-map.json').read_text(encoding='utf-8'))
        output = work/f'review-{index}.json'
        write(output, review_for(private))
        prompt = 'Synthetic independent blind review\n'+json.dumps(packet, ensure_ascii=False)+'\n'+json.dumps(public, ensure_ascii=False)
        prompt_path = output.with_suffix(output.suffix+'.input.txt')
        prompt_path.write_text(prompt, encoding='utf-8')
        model, effort = 'synthetic-model', 'synthetic-effort'
        identity = hashlib.sha256(prompt_path.read_bytes()+model.encode()+effort.encode()+
                                  b'controlled-packet-env-closed-tools-disabled-v3').hexdigest()
        write(output.with_suffix(output.suffix+'.record.json'), {'model': model, 'effort': effort, 'input_hash': identity,
                                                               'started_at': datetime.now(timezone.utc).isoformat()})
        sealed = (datetime.now(timezone.utc)+timedelta(seconds=index)).isoformat()
        ledger['reviews'].append({'path': str(output), 'output_hash': hashlib.sha256(output.read_bytes()).hexdigest(),
                                  'sealed_at': sealed})
    return work, ledger


class FourComparatorReviewTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.baselines, self.outputs = inputs()
        self.cards = bundle.build_result_cards(self.packet, self.baselines, self.outputs)

    def test_fixed_rankings_keep_existing_order_without_borrowed_facts(self):
        self.assertEqual([item['journal_id'] for item in self.cards['keyword']['ranked_candidates']], ['j-two', 'j-one'])
        for variant in ('keyword', 'abstract'):
            card = self.cards[variant]
            self.assertEqual(card['claims'], {'journals': [], 'profile': None, 'constraints': None})
            self.assertNotIn('verified', json.dumps(card['claims']))
            self.assertNotIn('routes', card)
            self.assertIn('No independent policy assessment', card['notes'][0])
            self.assertEqual(card['bibliographic_sources'][0]['records'][0]['source_type'], 'bibliographic')
            self.assertIn('record_url', card['bibliographic_sources'][0]['records'][0])
        self.assertEqual(self.baselines['keyword'][0]['score'], 4.25)

    def test_unknown_baseline_candidate_is_rejected_without_inventing_identity(self):
        self.baselines['keyword'][0]['journal_id'] = 'never-discovered'
        with self.assertRaises(bundle.ReviewBundleError):
            bundle.build_result_cards(self.packet, self.baselines, self.outputs)

    def test_undiscovered_generated_claim_is_retained_for_hard_failure_review(self):
        self.outputs['v1']['fit_sequence'] = ['never-discovered']
        self.outputs['v1']['evidence']['journals'].append({'id': 'never-discovered', 'title': 'Generated assertion'})
        card = bundle.build_result_cards(self.packet, self.baselines, self.outputs)['v1']
        self.assertFalse(card['ranked_candidates'][0]['present_in_shared_candidate_pool'])
        self.assertEqual(card['ranked_candidates'][0]['title'], 'Generated assertion')
        self.assertEqual(card['bibliographic_sources'][0]['records'], [])

    def test_anonymity_removes_generation_identity_preserves_scientific_content(self):
        text = json.dumps(self.cards['v1'])
        for hidden in ('gpt-synthetic-generation', 'private-v1', 'Skill v1', 'medical-journal-selector'):
            self.assertNotIn(hidden, text)
        self.assertNotIn('run', self.cards['v1']['claims'])
        self.assertEqual(self.cards['v1']['claims']['profile']['model'], 'Cox regression')
        self.assertEqual(self.cards['v1']['claims']['profile']['version'], 'clinical software 2')
        value = self.cards['v1']['claims']['journals'][0]['facts']['method_policy']['value']
        self.assertEqual(value, {'model': 'Cox regression', 'version': '2', 'provider': 'University'})

    def test_scientific_model_names_and_exact_support_are_never_redacted(self):
        outputs = copy.deepcopy(self.outputs)
        outputs['v1']['evidence']['profile']['summary'] = 'The study evaluates GPT-4 in clinical decisions.'
        fact = outputs['v1']['evidence']['journals'][0]['facts']['method_policy']
        fact['value'] = {'model': 'GPT-4', 'quote': 'We evaluated GPT-4 clinical decision support.'}
        fact['evidence'][0]['support'] = 'We evaluated GPT-4 clinical decision support.'
        cards = bundle.build_result_cards(self.packet, self.baselines, outputs)
        self.assertEqual(cards['v1']['claims']['profile']['summary'], outputs['v1']['evidence']['profile']['summary'])
        self.assertEqual(cards['v1']['claims']['journals'][0]['facts']['method_policy'], fact)

    def test_each_reviewer_order_is_fixed_distinct_and_publicly_unidentified(self):
        orders = []
        for index in (1, 2, 3):
            public, private = bundle.make_review_bundle(self.cards, 'synthetic-case', index)
            self.assertEqual((public, private), bundle.make_review_bundle(self.cards, 'synthetic-case', index))
            self.assertEqual(set(public['systems']), set(bundle.LABELS))
            self.assertNotIn('label_to_comparator', public)
            self.assertNotIn('reviewer_index', public)
            self.assertNotIn('seed_hash', public)
            self.assertNotIn('case_id', public)
            orders.append(tuple(private['displayed_comparators']))
        self.assertEqual(len(set(orders)), 3)

    def test_complete_pair_contract_rejects_missing_duplicate_and_foreign_winner(self):
        _, private = bundle.make_review_bundle(self.cards, 'synthetic-case', 1)
        good = review_for(private)
        self.assertEqual(bundle.review_contract(good), [])
        mutations = []
        missing = copy.deepcopy(good); missing['pairwise_decisions'].pop(); mutations.append(missing)
        duplicate = copy.deepcopy(good); duplicate['pairwise_decisions'][-1] = duplicate['pairwise_decisions'][0]; mutations.append(duplicate)
        wrong = copy.deepcopy(good); wrong['pairwise_decisions'][0]['decision'] = 'D'; mutations.append(wrong)
        global_only = copy.deepcopy(good); del global_only['pairwise_decisions']; global_only['paired_decision'] = 'A'; mutations.append(global_only)
        absent = copy.deepcopy(good); del absent['systems']['D']; mutations.append(absent)
        bad_id = copy.deepcopy(good); bad_id['systems']['A']['usable_journal_ids'] = [{}]; mutations.append(bad_id)
        no_ranking = copy.deepcopy(good); del no_ranking['systems']['A']['ranking_assessment']; mutations.append(no_ranking)
        for value in mutations:
            with self.subTest(value=value):
                self.assertTrue(bundle.review_contract(value))

    def test_usable_ids_cannot_be_added_by_reviewer(self):
        _, private = bundle.make_review_bundle(self.cards, 'synthetic-case', 1)
        value = review_for(private)
        allowed = {label: ['j-one'] for label in bundle.LABELS}
        value['systems']['C']['usable_journal_ids'] = ['unranked']
        self.assertTrue(bundle.review_contract(value, allowed_journal_ids=allowed))

    def test_two_different_label_maps_normalize_to_the_same_four_results(self):
        values, maps = [], []
        for index in (1, 2):
            _, private = bundle.make_review_bundle(self.cards, 'synthetic-case', index)
            values.append(review_for(private)); maps.append(private)
        self.assertEqual(bundle.normalize_review(values[0], maps[0]), bundle.normalize_review(values[1], maps[1]))
        self.assertEqual(bundle.review_conflicts(values, maps), [])

    def test_v1_v2_pair_extracted_independently_of_other_winners(self):
        _, private = bundle.make_review_bundle(self.cards, 'synthetic-case', 1)
        value = review_for(private)
        self.assertEqual(bundle.extract_pairwise_decision(value, private), 'v2')
        self.assertEqual(bundle.extract_pairwise_decision(value, private, 'abstract', 'v2'), 'abstract')

    def test_conflicts_cover_all_four_systems_and_all_six_pairs(self):
        maps = [bundle.make_review_bundle(self.cards, 'synthetic-case', index)[1] for index in (1, 2)]
        values = [review_for(private) for private in maps]
        keyword_label = next(label for label, variant in maps[1]['label_to_comparator'].items() if variant == 'keyword')
        values[1]['systems'][keyword_label]['hard_failures'] = [{'claim': 'Unsupported claim', 'source': 'Actual URL', 'reason': 'Absent passage'}]
        values[1]['systems'][keyword_label]['usable_journal_ids'] = []
        pair = values[1]['pairwise_decisions'][0]
        pair['decision'] = 'unresolved' if pair['decision'] != 'unresolved' else 'tie'
        conflicts = bundle.review_conflicts(values, maps)
        self.assertIn({'system': 'keyword', 'field': 'hard_failures'}, conflicts)
        self.assertIn({'system': 'keyword', 'field': 'usable_journal_ids'}, conflicts)
        self.assertTrue(any(item['field'] == 'pairwise_decision' for item in conflicts))

    def test_different_failure_claims_cannot_be_hidden_by_same_boolean(self):
        normalized = [bundle.normalize_review(review_for(bundle.make_review_bundle(self.cards, 'x', index)[1]),
                                               bundle.make_review_bundle(self.cards, 'x', index)[1]) for index in (1, 2)]
        for index, value in enumerate(normalized):
            value['systems']['v1']['hard_failures'] = [{'claim': 'Claim '+str(index), 'source': 'Source', 'reason': 'Reason'}]
        self.assertIn({'system': 'v1', 'field': 'hard_failures'}, bundle.review_conflicts(normalized))

    def test_adjudication_remaps_prior_reviews_without_revealing_comparators(self):
        private = bundle.make_review_bundle(self.cards, 'x', 1)[1]
        normalized = bundle.normalize_review(review_for(private), private)
        third = bundle.make_review_bundle(self.cards, 'x', 3)[1]
        blinded = bundle.anonymize_normalized_reviews([normalized], third)[0]
        self.assertEqual(set(blinded['systems']), set(bundle.LABELS))
        self.assertEqual(bundle.normalize_review(blinded, third), normalized)


class FourComparatorSealTests(unittest.TestCase):
    def test_complete_bundle_and_actual_four_object_requests_pass_without_answers(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            (work/'answer.json').write_text('INVALID SENTINEL MUST NEVER BE READ', encoding='utf-8')
            self.assertTrue(bundle.require_final_review_bundles([ledger], root, expected_count=1))
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.require_final_review_bundles([ledger], root)

    def test_changed_card_map_ranking_output_or_preparation_invalidates_original_seal(self):
        names = ['keyword-review-result.json', 'review-2.identity-map.json', 'review-1.bundle.json',
                 'fixed-baselines.json', 'v2-selection.json', 'preparation-seal.json']
        for name in names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as root:
                work, ledger = sealed_fixture(root)
                (work/name).write_text('{}', encoding='utf-8')
                with self.assertRaises(bundle.ReviewBundleError):
                    bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_changed_original_preparation_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            _, ledger = sealed_fixture(root)
            ledger['preparation_seal']['manifest_hash'] = 'new binding after execution'
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_two_system_actual_review_cannot_satisfy_four_object_gate(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            path = work/'review-1.json'
            write(path, {'systems': {'A': {}, 'B': {}}, 'paired_decision': 'A'})
            ledger['reviews'][0]['output_hash'] = hashlib.sha256(path.read_bytes()).hexdigest()
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_swapped_review_artifacts_cannot_reuse_wrong_private_map(self):
        with tempfile.TemporaryDirectory() as root:
            _, ledger = sealed_fixture(root)
            ledger['reviews'].reverse()
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_missing_public_payload_in_actual_request_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            (work/'review-2.json.input.txt').write_text('Only two hidden results were supplied', encoding='utf-8')
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_added_payload_after_call_fails_original_request_hash(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            path = work/'review-2.json.input.txt'
            path.write_text(path.read_text(encoding='utf-8')+'\nModified after the call', encoding='utf-8')
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_same_four_results_without_shared_source_packet_is_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            path = work/'review-2.json.input.txt'
            payload = json.loads((work/'review-2.bundle.json').read_text(encoding='utf-8'))
            path.write_text(json.dumps(payload, ensure_ascii=False), encoding='utf-8')
            receipt_path = work/'review-2.json.record.json'
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            receipt['input_hash'] = hashlib.sha256(path.read_bytes()+receipt['model'].encode()+receipt['effort'].encode()+
                b'controlled-packet-env-closed-tools-disabled-v3').hexdigest()
            write(receipt_path, receipt)
            with self.assertRaisesRegex(bundle.ReviewBundleError, 'common manuscript/source'):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_actual_review_cannot_start_before_bundle_seal(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            receipt_path = work/'review-1.json.record.json'
            receipt = json.loads(receipt_path.read_text(encoding='utf-8'))
            receipt['started_at'] = '2000-01-01T00:00:00+00:00'
            write(receipt_path, receipt)
            with self.assertRaisesRegex(bundle.ReviewBundleError, 'began before'):
                bundle.require_final_review_bundles([ledger], root, expected_count=1)

    def test_seal_cannot_be_recreated_after_any_review_request(self):
        with tempfile.TemporaryDirectory() as root:
            work, ledger = sealed_fixture(root)
            (work/bundle.MANIFEST_NAME).unlink()
            packet, baselines, outputs = inputs()
            with self.assertRaises(bundle.ReviewBundleError):
                bundle.seal_review_bundles(work, work.name, packet, baselines, outputs, ledger['preparation_seal'])


if __name__ == '__main__':
    unittest.main()
