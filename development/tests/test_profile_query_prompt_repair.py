"""Synthetic query-limit and fresh-path repair checks; no real model requests."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import campaign
from corpus import parse_article
from runner import collect_call_records
from test_profile_query_contract import PROFILE, make_case, fixture_cli

LONG_BROAD_QUERY = ('TITLE_ABS:(delirium OR "acute confusion") AND TITLE_ABS:(elderly OR "older adults") '
                    'AND TITLE_ABS:("hip fracture" OR "fragility fracture" OR "orthopaedic surgery" OR "orthopedic surgery")')
SHORT_BROAD_QUERY = ('TITLE_ABS:(delirium OR "acute confusion") AND TITLE_ABS:(elderly OR "older adults") '
                     'AND TITLE_ABS:("hip fracture" OR "fragility fracture")')


def original_research_case(root):
    case, corpus, runs = make_case(root)
    source = corpus/case['case_id']
    xml = (source/'source.xml').read_text(encoding='utf-8').replace('<article>', '<article article-type="research-article">', 1)
    _, masked = parse_article(xml)
    (source/'source.xml').write_text(xml, encoding='utf-8')
    (source/'masked.txt').write_text(masked, encoding='utf-8')
    case['input_hash'] = hashlib.sha256(masked.encode()).hexdigest()
    return case, corpus, runs


class ProfileQueryPromptRepairTests(unittest.TestCase):
    def test_actual_profile_prompt_states_word_and_phrase_limits(self):
        with tempfile.TemporaryDirectory() as root:
            case, corpus, runs = original_research_case(root)
            work = runs/case['case_id']
            with patch('campaign.model_json', return_value=(copy.deepcopy(PROFILE), {})) as model, \
                 patch('campaign.discover', side_effect=RuntimeError('Synthetic stop before any retrieval')) as retrieval:
                with self.assertRaisesRegex(RuntimeError, 'Synthetic stop'):
                    campaign.prepare_case(case, corpus, work, '2026-10-03')
            prefix = model.call_args.args[0].split('MANUSCRIPT DATA:', 1)[0]
            self.assertIn('no more than 18 whitespace-delimited words', prefix)
            self.assertIn('counting Boolean operators and words inside quoted phrases', prefix)
            self.assertIn('Every quoted phrase must contain no more than six words', prefix)
            self.assertIn('never meet the limit by shortening a manuscript title', prefix)
            self.assertEqual(retrieval.call_count, 1)

    def test_broad_query_can_preserve_role_without_truncating_identifiers_or_titles(self):
        self.assertEqual(len(LONG_BROAD_QUERY.split()), 21)
        self.assertLessEqual(len(SHORT_BROAD_QUERY.split()), 18)
        value = copy.deepcopy(PROFILE)
        value['queries'][2] = LONG_BROAD_QUERY
        self.assertIn('queries[2] exceeds the 18-word discovery limit', campaign.profile_contract(value))
        value['queries'][2] = SHORT_BROAD_QUERY
        self.assertEqual(campaign.profile_contract(value), [])
        # Both versions remain topic/readership queries; fewer ordinary synonyms
        # remove no study code, title fragment or clinically narrower method.
        self.assertIn('delirium', SHORT_BROAD_QUERY)
        self.assertIn('older adults', SHORT_BROAD_QUERY)
        self.assertIn('fragility fracture', SHORT_BROAD_QUERY)

    def test_explicit_new_prompt_cannot_overwrite_old_same_path_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            path = work/'profile.json'
            bad = copy.deepcopy(PROFILE)
            bad['queries'][2] = LONG_BROAD_QUERY
            with patch('runner.shutil.which', return_value='synthetic-codex'), \
                 patch('runner.subprocess.Popen', side_effect=fixture_cli([
                    ('synthetic-original-context', json.dumps(bad), {'input_tokens': 13, 'output_tokens': 17})])):
                with self.assertRaises(campaign.ModelOutputError):
                    campaign.model_json('Original synthetic profile prompt', path, contract=campaign.profile_contract)
            names = ('profile.json', 'profile.json.record.json', 'profile.json.events.jsonl', 'profile.json.input.txt')
            originals = {name: (work/name).read_bytes() for name in names}
            with patch('runner.subprocess.Popen') as model:
                with self.assertRaisesRegex(ValueError, 'different inputs/settings'):
                    campaign.model_json('New constrained profile prompt with at most 18 words per query', path,
                                        contract=campaign.profile_contract)
            model.assert_not_called()
            self.assertEqual(originals, {name: (work/name).read_bytes() for name in names})

    def test_fresh_constrained_path_retains_original_failure_and_both_usages(self):
        with tempfile.TemporaryDirectory() as root:
            work = Path(root)
            original = work/'profile.json'
            repaired = work/'profile-contract-retry-01'/'profile.json'
            bad = copy.deepcopy(PROFILE)
            bad['queries'][2] = LONG_BROAD_QUERY
            good = copy.deepcopy(PROFILE)
            good['queries'][2] = SHORT_BROAD_QUERY
            with patch('runner.shutil.which', return_value='synthetic-codex'), \
                 patch('runner.subprocess.Popen', side_effect=fixture_cli([
                    ('synthetic-failed-context', json.dumps(bad), {'input_tokens': 13, 'output_tokens': 17}),
                    ('synthetic-fresh-context', json.dumps(good), {'input_tokens': 19, 'output_tokens': 23})])) as model:
                with self.assertRaises(campaign.ModelOutputError):
                    campaign.model_json('Original synthetic profile prompt', original, contract=campaign.profile_contract)
                names = ('profile.json', 'profile.json.record.json', 'profile.json.events.jsonl', 'profile.json.input.txt')
                original_bytes = {name: (work/name).read_bytes() for name in names}
                value, receipt = campaign.model_json('Fresh constrained synthetic profile prompt: each query <=18 words; '
                    'each quoted phrase <=6 words; ordinary concepts only.', repaired, contract=campaign.profile_contract)
            self.assertEqual(model.call_count, 2)
            self.assertEqual(value['queries'][2], SHORT_BROAD_QUERY)
            self.assertEqual(receipt['context_id'], 'synthetic-fresh-context')
            self.assertEqual(receipt['status'], 'completed')
            self.assertEqual(original_bytes, {name: (work/name).read_bytes() for name in names})
            first = json.loads((work/'profile.json.record.json').read_text(encoding='utf-8'))
            self.assertEqual(first['output_contract_status'], 'failed')
            self.assertEqual(first['usage'], {'input_tokens': 13, 'output_tokens': 17})
            calls = collect_call_records(work)
            self.assertEqual(len(calls), 2)
            self.assertEqual({call['context_id'] for call in calls}, {'synthetic-failed-context', 'synthetic-fresh-context'})
            self.assertEqual(sum(call['usage']['output_tokens'] for call in calls), 40)
            self.assertEqual(sum(call['usage']['input_tokens'] for call in calls), 32)


if __name__ == '__main__':
    unittest.main()
