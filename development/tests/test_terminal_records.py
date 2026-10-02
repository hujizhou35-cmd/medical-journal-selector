import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"skills/medical-journal-selector-skill-trainer/scripts"))
from runner import completed_message,recover_terminal_output
from broker import canonical_url

class TerminalRecordTests(unittest.TestCase):
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

if __name__=="__main__":unittest.main()
