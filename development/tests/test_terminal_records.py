import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"skills/medical-journal-selector-skill-trainer/scripts"))
from runner import completed_message,recover_terminal_output,persist_completed_message,collect_call_records
from broker import canonical_url,permitted_url,normalize_journal_ids
from evaluation import summarize

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
