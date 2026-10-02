import hashlib
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"skills/medical-journal-selector-skill-trainer/scripts"))
from runner import completed_message,recover_terminal_output,persist_completed_message,collect_call_records,run,mark_output_contract_failed
from campaign import model_json,selection_contract,ModelOutputError
from broker import canonical_url,permitted_url,normalize_journal_ids
from evaluation import summarize


class FinishedFixtureProcess:
    """A completed CLI fixture; tests never start Codex or contact a model."""
    returncode = 0

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        return self.returncode


def fixture_cli(messages):
    pending = iter(messages)

    def spawn(command, **kwargs):
        context, message, usage, terminal = next(pending)
        events = [{'type': 'thread.started', 'thread_id': context}]
        if message is not None:
            events.append({'type': 'item.completed',
                           'item': {'type': 'agent_message', 'text': message}})
        events.append({'type': terminal, 'usage': usage})
        kwargs['stdout'].write('\n'.join(json.dumps(event) for event in events))
        kwargs['stdout'].flush()
        return FinishedFixtureProcess()

    return spawn


class RunnerJsonContractTests(unittest.TestCase):
    def run_fixture(self, output, messages, **settings):
        with patch('runner.shutil.which', return_value='fixture-codex'), \
             patch('runner.subprocess.Popen', side_effect=fixture_cli(messages)) as process:
            result = run('Fixed synthetic manuscript packet', output,
                         require_json=True, **settings)
        return result, process.call_count

    def test_completed_malformed_response_is_model_failure_and_retains_usage(self):
        invalid = ('{partial', '{"value": 1} trailing prose', '{"a": 1}{"b": 2}',
                   '```json\n{"value": 1}', '{"value": NaN}', '{"value": Infinity}')
        for message in invalid:
            with self.subTest(message=message), tempfile.TemporaryDirectory() as folder:
                output = Path(folder)/'result.json'
                usage = {'input_tokens': 11, 'output_tokens': 7}
                result, calls = self.run_fixture(output, [('invalid-context', message, usage, 'turn.completed')])
                self.assertEqual(calls, 1)
                self.assertEqual(result['status'], 'model_failed')
                self.assertTrue(result['model_turn_completed'])
                self.assertEqual(result['usage'], usage)
                # A bad payload is still a genuine completed model response;
                # preserve its receipt without accepting it as a usable result.
                self.assertEqual(result['output_hash'], hashlib.sha256(output.read_bytes()).hexdigest())
                self.assertTrue(result['terminal_output_matches'])
                self.assertEqual(output.read_text(encoding='utf-8'), message)

    def test_schema_path_does_not_reclassify_malformed_json_as_transport_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'result.json'
            schema = Path(folder)/'contract.json'
            schema.write_text('{"type":"object"}', encoding='utf-8')
            result, _ = self.run_fixture(output, [('schema-context', '{broken', {'output_tokens': 4}, 'turn.completed')], schema=schema)
            self.assertEqual(result['status'], 'model_failed')
            self.assertEqual(result['usage']['output_tokens'], 4)

    def test_complete_fenced_json_is_compatible_without_changing_raw_sealed_bytes(self):
        for message in ('```json\n{"result": []}\n```', '```\n{"result": []}\n```'):
            with self.subTest(message=message), tempfile.TemporaryDirectory() as folder:
                output = Path(folder)/'result.json'
                result, _ = self.run_fixture(output, [('fenced-context', message, {'output_tokens': 5}, 'turn.completed')])
                self.assertEqual(result['status'], 'completed')
                self.assertEqual(output.read_text(encoding='utf-8'), message)
                self.assertEqual(result['output_hash'], hashlib.sha256(output.read_bytes()).hexdigest())
                # Reusing a genuine valid checkpoint must not make another call.
                with patch('runner.subprocess.Popen') as process:
                    cached = run('Fixed synthetic manuscript packet', output, require_json=True)
                process.assert_not_called()
                self.assertEqual(cached['context_id'], 'fenced-context')

    def test_retry_archives_bad_model_output_and_counts_both_calls(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'result.json'
            invalid = '{partial'
            first, _ = self.run_fixture(output, [('first-context', invalid, {'output_tokens': 5}, 'turn.completed')])
            second, calls = self.run_fixture(output, [('retry-context', '{"valid": true}', {'output_tokens': 9}, 'turn.completed')])
            self.assertEqual(first['status'], 'model_failed')
            self.assertEqual(second['status'], 'completed')
            self.assertEqual(calls, 1)
            archive = output.parent/'result.attempts'/'attempt-01'
            self.assertEqual((archive/'result.json').read_text(encoding='utf-8'), invalid)
            archived_record = json.loads((archive/'result.json.record.json').read_text(encoding='utf-8'))
            self.assertEqual(archived_record['status'], 'model_failed')
            self.assertEqual(archived_record['context_id'], 'first-context')
            report = summarize([{'status': 'completed', 'scores': {},
                                 'calls': collect_call_records(output.parent)}])
            self.assertEqual(report['model_calls'], 2)
            self.assertEqual(report['usage']['output_tokens'], 14)
            self.assertEqual(report['call_outcomes'], {'model_failed': 1, 'completed': 1})

    def test_no_completed_turn_remains_infrastructure_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            result, _ = self.run_fixture(Path(folder)/'result.json',
                                         [('disconnected-context', '{"partial": true}', None, 'turn.failed')])
            self.assertEqual(result['status'], 'infrastructure_failed')
            self.assertFalse(result['model_turn_completed'])
            self.assertIsNone(result['usage'])

    def test_a_previous_completed_non_json_checkpoint_is_retried_under_json_contract(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'result.json'
            with patch('runner.shutil.which', return_value='fixture-codex'), \
                 patch('runner.subprocess.Popen', side_effect=fixture_cli([('free-text-context', 'Plain prose', {'output_tokens': 3}, 'turn.completed')])):
                original = run('Fixed synthetic manuscript packet', output)
            self.assertEqual(original['status'], 'completed')
            result, calls = self.run_fixture(output, [('strict-context', '{"valid": true}', {'output_tokens': 6}, 'turn.completed')])
            self.assertEqual(calls, 1)
            self.assertEqual(result['context_id'], 'strict-context')
            self.assertEqual(result['status'], 'completed')
            self.assertEqual((output.parent/'result.attempts'/'attempt-01'/'result.json').read_text(encoding='utf-8'), 'Plain prose')

    def test_valid_json_with_wrong_role_shape_is_rejected_and_retried(self):
        valid = {'evidence': {'run': {}, 'profile': {}, 'constraints': {}, 'journals': []},
                 'fit_sequence': [], 'report_notes': []}
        wrong_shapes = ([], {'evidence': []},
                        {**valid, 'fit_sequence': ['journal', 7]},
                        {**valid, 'report_notes': 'prose instead of a list'},
                        {**valid, 'evidence': {**valid['evidence'], 'journals': ['not a dossier']}})
        for value in wrong_shapes:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as folder:
                output = Path(folder)/'result.json'
                messages = [('bad-shape-context', json.dumps(value), {'output_tokens': 4}, 'turn.completed'),
                            ('retry-shape-context', json.dumps(valid), {'output_tokens': 8}, 'turn.completed')]
                with patch('runner.shutil.which', return_value='fixture-codex'), \
                     patch('runner.subprocess.Popen', side_effect=fixture_cli(messages)) as process:
                    with self.assertRaises(ModelOutputError):
                        model_json('Fixed synthetic manuscript packet', output, contract=selection_contract)
                    record = json.loads(output.with_suffix('.json.record.json').read_text(encoding='utf-8'))
                    self.assertEqual(record['status'], 'completed')
                    self.assertEqual(record['output_contract_status'], 'failed')
                    self.assertEqual(record['usage']['output_tokens'], 4)
                    result, retry = model_json('Fixed synthetic manuscript packet', output, contract=selection_contract)
                self.assertEqual(result, valid)
                self.assertEqual(process.call_count, 2)
                self.assertEqual(retry['context_id'], 'retry-shape-context')
                archived = output.parent/'result.attempts'/'attempt-01'/'result.json.record.json'
                self.assertEqual(json.loads(archived.read_text(encoding='utf-8'))['output_contract_status'], 'failed')
                calls = collect_call_records(output.parent)
                self.assertEqual(len(calls), 2)
                self.assertEqual(sum(c['usage']['output_tokens'] for c in calls), 12)

    def test_contract_failure_cannot_be_attached_to_tampered_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)/'result.json'
            result, _ = self.run_fixture(output, [('genuine-context', '{"genuine": true}', {'output_tokens': 5}, 'turn.completed')])
            record_path = output.with_suffix('.json.record.json')
            original = record_path.read_bytes()
            output.write_text('{"replacement": true}', encoding='utf-8')
            with self.assertRaises(ValueError):
                mark_output_contract_failed(output, 'synthetic shape violation')
            self.assertEqual(record_path.read_bytes(), original)
            self.assertEqual(result['status'], 'completed')

class TerminalRecordTests(unittest.TestCase):
    def test_successful_retry_does_not_erase_failed_call_count(self):
        report=summarize([{'status':'completed','lesson_status':'completed','stratum':'fixture','scores':{},
                          'calls':[{'status':'infrastructure_failed','usage':None,'elapsed_seconds':7},
                                   {'status':'completed','usage':{'output_tokens':2},'elapsed_seconds':10}]}])
        self.assertEqual(report['completed'],1)
        self.assertEqual(report['infrastructure_failed'],0)
        self.assertEqual(report['call_outcomes'],{'infrastructure_failed':1,'completed':1})
        self.assertEqual(report['usage_unavailable_calls'],1)
        self.assertEqual(report['elapsed_seconds'],17)
    def test_call_accounting_includes_regression_and_deduplicates_copied_receipts(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            first={'context_id':'fixture-original','started_at':'t1','input_hash':'h1','usage':{'output_tokens':10}}
            regression={'context_id':'fixture-regression','started_at':'t2','input_hash':'h2','usage':{'output_tokens':20}}
            (root/'selection.json.record.json').write_text(json.dumps(first),encoding='utf-8')
            (root/'archive').mkdir()
            (root/'archive/selection.json.record.json').write_text(json.dumps(first),encoding='utf-8')
            (root/'regression').mkdir()
            (root/'regression/selection.json.record.json').write_text(json.dumps(regression),encoding='utf-8')
            records=collect_call_records(root)
            self.assertEqual(len(records),2)
            self.assertEqual(sum(r['usage']['output_tokens'] for r in records),30)
    def test_name_only_journal_is_merged_only_with_unambiguous_retrieved_identity(self):
        papers=[{'journal_id':'2405-8440','journal':'Heliyon','url':'source-known'},
                {'journal_id':'heliyon','journal':'Heliyon','url':'source-missing'}]
        normalized,audit=normalize_journal_ids(papers)
        self.assertEqual([p['journal_id'] for p in normalized],['2405-8440','2405-8440'])
        self.assertEqual(audit[0]['identity_basis_url'],'source-known')
        self.assertEqual(papers[1]['journal_id'],'heliyon')
        papers.append({'journal_id':'1111-2222','journal':'Heliyon','url':'ambiguous'})
        normalized,audit=normalize_journal_ids(papers)
        self.assertEqual(normalized[1]['journal_id'],'heliyon')
        self.assertEqual(audit,[])
    def test_stale_retry_output_cannot_be_sealed_as_new_response(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'result.json'
            output.write_text('{"old":true}',encoding='utf-8')
            actual='{"new":true}'
            events=[{'type':'item.completed','item':{'type':'agent_message','text':actual}},
                    {'type':'turn.completed'}]
            persist_completed_message(output,events)
            self.assertEqual(output.read_text(encoding='utf-8'),actual)
            backups=list(output.parent.glob('result.json.conflicting-output-*'))
            self.assertEqual(len(backups),1)
            self.assertEqual(backups[0].read_text(encoding='utf-8'),'{"old":true}')
    def test_persist_refuses_partial_events_without_overwriting_output(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'result.json'
            output.write_text('old checkpoint',encoding='utf-8')
            with self.assertRaises(ValueError):
                persist_completed_message(output,[{'type':'item.completed','item':{'type':'agent_message','text':'{}'}}])
            self.assertEqual(output.read_text(encoding='utf-8'),'old checkpoint')
    def test_partial_or_failed_turn_is_not_completed(self):
        message={"type":"item.completed","item":{"type":"agent_message","text":"{\"result\":true}"}}
        self.assertIsNone(completed_message([message]))
        self.assertIsNone(completed_message([message,{"type":"turn.completed"},{"type":"turn.failed"}]))
    def test_unexpected_tool_use_prevents_recovery(self):
        events=[{"type":"item.completed","item":{"type":"mcp_tool_call"}},{"type":"item.completed","item":{"type":"agent_message","text":"{}"}},{"type":"turn.completed"}]
        self.assertIsNone(completed_message(events))
    def test_recovery_retains_transport_failure_and_exact_message(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"result.json"
            record_path=output.with_suffix(".json.record.json")
            record_path.write_text(json.dumps({"status":"infrastructure_failed","context_id":"actual-event-context","failure":"timeout","completed_at":"2026-01-01T00:00:00+00:00"}),encoding="utf-8")
            message='{ "recommendation": [] }'
            events=[{"type":"item.completed","item":{"type":"agent_message","text":message}},{"type":"turn.completed"}]
            output.with_suffix(".json.events.jsonl").write_text("\n".join(json.dumps(e) for e in events),encoding="utf-8")
            result=recover_terminal_output(output)
            self.assertEqual(output.read_text(encoding="utf-8"),message)
            self.assertEqual(result["output_hash"],hashlib.sha256(message.encode()).hexdigest())
            self.assertEqual(result["transport_failure"],"timeout")
            self.assertTrue(record_path.with_suffix(".json.transport-failed-original").exists())
    def test_recovery_refuses_incomplete_json(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/"result.json"
            output.with_suffix(".json.record.json").write_text(json.dumps({"status":"infrastructure_failed","context_id":"ctx"}),encoding="utf-8")
            events=[{"type":"item.completed","item":{"type":"agent_message","text":"{partial"}},{"type":"turn.completed"}]
            output.with_suffix(".json.events.jsonl").write_text("\n".join(json.dumps(e) for e in events),encoding="utf-8")
            with self.assertRaises(ValueError):recover_terminal_output(output)
            self.assertFalse(output.exists())
    def test_canonical_urls_keep_functional_parameters(self):
        self.assertEqual(canonical_url("https://link.springer.com/journal/1?error=cookies_not_supported&code=abc&utm_source=x&article=7#scope"),"https://link.springer.com/journal/1?article=7")
    def test_verified_hosts_do_not_allow_lookalike_domains(self):
        self.assertTrue(permitted_url('https://journals.healio.com/journal/jne'))
        self.assertTrue(permitted_url('https://www.fnjn.org/index.php/pub/about'))
        self.assertTrue(permitted_url('https://www.alternative-therapies.com/'))
        self.assertTrue(permitted_url('https://www.wolterskluwer.com/en/solutions/ovid/nursing-education-perspectives-241'))
        self.assertFalse(permitted_url('https://journals.healio.com.untrusted.example/'))
        self.assertFalse(permitted_url('http://www.fnjn.org/'))

if __name__=="__main__":unittest.main()
