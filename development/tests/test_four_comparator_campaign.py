"""Synthetic campaign integration only: no model calls or real holdout reads."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import campaign
import review_bundle
from test_preparation_seal import fixture, completed_call, write_json, SEALED_AT
from test_review_bundle import inputs, review_for


class FourComparatorCampaignTests(unittest.TestCase):
    def setup_case(self, root):
        corpus, runs, source, work, input_hash = fixture(root)
        case = {'case_id': 'synthetic-case-001', 'input_hash': input_hash,
                'stratum': 'clinical_nursing', 'split': 'holdout', 'license': 'synthetic fixture'}
        packet, baselines, outputs = inputs()
        shared = json.loads((work/'generator-packet.json').read_text(encoding='utf-8'))
        shared.update(packet)
        write_json(work/'generator-packet.json', shared)
        write_json(work/'fixed-baselines.json', baselines)
        write_json(work/'literature.json', {'papers': shared['literature'], 'records': shared['retrieval_records']})
        return corpus, runs, source, work, case, shared, baselines, outputs

    def execute_fixture(self, root, *, dispute=False, fail_second=False, configured=None):
        values = configured or self.setup_case(root)
        corpus, runs, source, work, case, packet, baselines, outputs = values
        observed = []

        def selected(packet, skill, path):
            variant = Path(path).name.split('-selection')[0]
            value = outputs[variant]
            completed_call(work, Path(path).name, value, case['case_id'],
                           started='2026-10-03T00:00:20+00:00', completed='2026-10-03T00:00:25+00:00')
            return value, campaign.read(str(path)+'.record.json')

        def reviewed(packet, anonymous, path, disputed=None):
            index = int(Path(path).stem.split('-')[1])
            observed.append((index, copy.deepcopy(anonymous), copy.deepcopy(disputed)))
            if fail_second and index == 2:
                raise RuntimeError('Synthetic interrupted second review')
            private = campaign.read(work/f'review-{index}.identity-map.json')
            value = review_for(private)
            if dispute and index == 2:
                label = next(label for label, variant in private['label_to_comparator'].items() if variant == 'keyword')
                value['systems'][label]['ranking_assessment']['judgment'] = 'unsupported'
            completed_call(work, Path(path).name, value, case['case_id'],
                           started='2026-10-03T00:00:30+00:00', completed='2026-10-03T00:00:35+00:00')
            prompt = 'Synthetic review request\n'+json.dumps(packet, ensure_ascii=False)+'\n'+json.dumps(anonymous, ensure_ascii=False)
            prompt_path = Path(str(path)+'.input.txt')
            prompt_path.write_text(prompt, encoding='utf-8')
            receipt = campaign.read(str(path)+'.record.json')
            receipt.update({'model': 'synthetic-model', 'effort': 'synthetic-effort'})
            receipt['input_hash'] = hashlib.sha256(prompt_path.read_bytes()+receipt['model'].encode()+
                receipt['effort'].encode()+b'controlled-packet-env-closed-tools-disabled-v3').hexdigest()
            write_json(Path(str(path)+'.record.json'), receipt)
            return value, receipt

        selector = SimpleNamespace(validate=lambda evidence: [])
        with patch('preparation_seal.stamp', return_value=SEALED_AT), \
             patch('review_bundle.stamp', return_value='2026-10-03T00:00:27+00:00'), \
             patch('campaign.prepare_case', return_value=(packet, baselines)), \
             patch('campaign.skill_packet', return_value='Synthetic frozen skill instructions'), \
             patch('campaign.select', side_effect=selected), patch('campaign.source_audit', return_value=[]), \
             patch('campaign.review', side_effect=reviewed):
            ledger = campaign.execute(case, corpus, runs, {'v1': root/'v1', 'v2': root/'v2'}, selector, '2026-10-03')
        return values, ledger, observed

    def test_two_fresh_review_inputs_each_cover_all_four_results(self):
        with tempfile.TemporaryDirectory() as folder:
            values, ledger, observed = self.execute_fixture(Path(folder))
            self.assertEqual(ledger['status'], 'reviewed', ledger.get('failure'))
            self.assertEqual(len(observed), 2)
            self.assertEqual(len(ledger['generations']), 2)
            for index, public, dispute in observed:
                self.assertEqual(set(public['systems']), set(review_bundle.LABELS))
                self.assertIsNone(dispute)
                self.assertNotIn('variant', public)
            self.assertNotEqual(observed[0][1], observed[1][1])
            self.assertNotIn('identity_map', ledger)
            self.assertNotIn('revealed_at', ledger)
            # setup_case's invalid synthetic answer sentinel was never opened.
            self.assertEqual((values[2]/'answer.json').read_text(encoding='utf-8'), 'SYNTHETIC ANSWER FILE MUST NOT BE OPENED')

    def test_one_conflict_creates_one_adjudication_in_its_own_four_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            values, ledger, observed = self.execute_fixture(Path(folder), dispute=True)
            self.assertEqual(ledger['status'], 'reviewed', ledger.get('failure'))
            self.assertEqual(len(ledger['reviews']), 3)
            third = next(item for item in observed if item[0] == 3)
            self.assertEqual(len(third[2]), 2)
            for quoted in third[2]:
                self.assertEqual(set(quoted['systems']), set(review_bundle.LABELS))
                self.assertEqual(set(quoted['quoted_narrative_label_translation']), set(review_bundle.LABELS))
                self.assertNotIn('keyword', quoted['systems'])

    def test_retry_preserves_original_four_result_bundle_binding(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            values, failed, _ = self.execute_fixture(root, fail_second=True)
            self.assertEqual(failed['status'], 'infrastructure_failed')
            manifest = (values[3]/review_bundle.MANIFEST_NAME).read_bytes()
            binding = copy.deepcopy(failed['review_bundle_seal'])
            _, retried, _ = self.execute_fixture(root, configured=values)
            self.assertEqual(retried['status'], 'reviewed', retried.get('failure'))
            self.assertEqual(retried['review_bundle_seal'], binding)
            self.assertEqual((values[3]/review_bundle.MANIFEST_NAME).read_bytes(), manifest)

    def test_reveal_preserves_raw_baseline_rank_and_extracts_actual_v1_v2_pair(self):
        with tempfile.TemporaryDirectory() as folder:
            values, ledger, _ = self.execute_fixture(Path(folder))
            corpus, runs, source, work, case, packet, baselines, outputs = values
            write_json(source/'answer.json', {'journal': 'Journal One', 'issns': []})
            reviews = [campaign.read(work/f'review-{index}.json') for index in (1, 2)]
            result = campaign.reveal_case(case, corpus, work, ledger, outputs, reviews, baselines, None)
            self.assertEqual(result['paired_decision'], 'v2')
            self.assertEqual(result['scores']['keyword']['true_rank'], 2)
            self.assertEqual(result['scores']['abstract']['true_rank'], 1)
            self.assertTrue(result['scores']['keyword']['usable'])
            self.assertEqual(result['scores']['keyword']['reviewed_usable_true_rank'], 2)
            self.assertEqual(len(result['scores']['keyword']['ranking_assessments']), 2)
            self.assertEqual(len(result['pairwise_decisions']), 6)
            self.assertEqual(next(pair['decision'] for pair in result['pairwise_decisions']
                                  if {pair['left'], pair['right']} == {'abstract', 'v2'}), 'abstract')

    def test_four_object_prompt_and_contract_require_ranking_reasonableness(self):
        packet, baselines, outputs = inputs()
        cards = review_bundle.build_result_cards(packet, baselines, outputs)
        public, private = review_bundle.make_review_bundle(cards, 'synthetic', 1)
        value = review_for(private)
        with patch('campaign.model_json', return_value=(value, {})) as model:
            campaign.review(packet, public, Path('synthetic-review.json'))
        prompt = model.call_args.args[0]
        self.assertIn('ranking_assessment', prompt)
        self.assertIn('six unordered pairs', prompt)
        self.assertIn(json.dumps(public, ensure_ascii=False), prompt)
        self.assertEqual(model.call_args.kwargs['contract'](value), [])


if __name__ == '__main__':
    unittest.main()
