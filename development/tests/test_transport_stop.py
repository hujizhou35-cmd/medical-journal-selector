"""Synthetic transport-stop checks; no actual Codex or network requests."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
import runner

def error(text):return {'type':'error','message':text}

class FakeProcess:
    def __init__(self,running):self.returncode=None if running else 1;self.killed=False
    def poll(self):return self.returncode
    def kill(self):self.killed=True;self.returncode=-9
    def wait(self,timeout=None):
        if self.returncode is None:self.returncode=0
        return self.returncode

class TransportStopTests(unittest.TestCase):
    def fixture(self,events,running=False):
        self.process=FakeProcess(running)
        def spawn(command,**kwargs):
            self.command=command
            kwargs['stdout'].write('\n'.join(json.dumps(e) for e in events))
            kwargs['stdout'].flush()
            return self.process
        return spawn

    def execute(self,events,running=False):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'result.json'
            with patch('runner.shutil.which',return_value='fixture-codex'),patch('runner.subprocess.Popen',side_effect=self.fixture(events,running)):
                record=runner.run('Fixed isolated synthetic packet',output,require_json=True)
            raw=output.with_suffix('.json.events.jsonl').read_text(encoding='utf-8')
            return record,raw

    def test_http_reconnect_numbers_and_urls_do_not_split_same_cause(self):
        events=[error(f'Reconnecting... {n}/5 (Connection failed: error sending request for url (https://example.test/{n}))') for n in range(1,4)]
        self.assertEqual(runner.transport_failure_counts(events),{'http_request_failure':3})
        self.assertIn('Further retries paused',runner.repeated_transport_failure(events))

    def test_different_causes_are_not_merged(self):
        events=[error('error sending request'),error('error sending request'),error('error decoding response body')]
        self.assertFalse(runner.repeated_transport_failure(events))

    def test_content_or_catalog_events_do_not_exhaust_primary_transport_limit(self):
        events=[error('invalid JSON schema')]*4+[{'type':'item.completed','item':{'type':'agent_message','text':'error sending request'}}]
        self.assertEqual(runner.transport_failure_counts(events),{})

    def test_running_three_error_process_is_killed_and_genuine_events_retained(self):
        events=[{'type':'thread.started','thread_id':'failing-context'}]+[error('Reconnecting: Connection failed: error sending request')]*3
        record,raw=self.execute(events,running=True)
        self.assertTrue(self.process.killed)
        self.assertEqual(record['status'],'infrastructure_failed')
        self.assertEqual(record['context_id'],'failing-context')
        self.assertIsNone(record['usage'])
        self.assertFalse(record['model_turn_completed'])
        self.assertIn('Further retries paused',record['failure'])
        self.assertEqual(len(raw.splitlines()),4)
        self.assertEqual(record['transport_failure_counts'],{'http_request_failure':3})

    def test_process_that_already_failed_is_still_labelled_with_repeated_cause(self):
        events=[error('stream disconnected before completion: error decoding response body')]*3
        record,_=self.execute(events)
        self.assertIn('response_decode_failure',record['failure'])
        self.assertIsNone(record['usage'])

    def test_actual_completed_terminal_takes_precedence_over_prior_errors(self):
        events=[{'type':'thread.started','thread_id':'completed-context'}]+[error('error sending request')]*3+[
            {'type':'item.completed','item':{'type':'agent_message','text':'{"ok":true}'}},
            {'type':'turn.completed','usage':{'input_tokens':10,'output_tokens':4}}]
        record,_=self.execute(events,running=True)
        self.assertFalse(self.process.killed)
        self.assertEqual(record['status'],'completed')
        self.assertEqual(record['usage']['output_tokens'],4)
        self.assertTrue(record['terminal_output_matches'])

    def test_cli_policy_disables_nested_http_retries_and_preserves_model(self):
        self.execute([{'type':'thread.started','thread_id':'policy-fixture'},{'type':'turn.failed'}])
        self.assertIn('model_providers.evaluation-http.request_max_retries=0',self.command)
        self.assertIn('model_providers.evaluation-http.stream_max_retries=2',self.command)
        self.assertEqual(self.command[self.command.index('-m')+1],'gpt-6.1-sol')
        self.assertIn('model_reasoning_effort="xhigh"',self.command)
        self.assertIn('model_providers.evaluation-http.requires_openai_auth=true',self.command)

    def execute_terminal_race(self,message):
        events=[{'type':'thread.started','thread_id':'terminal-race'}]+[error('error sending request')]*3
        spawn=self.fixture(events,True)
        def racing_spawn(command,**kwargs):
            process=spawn(command,**kwargs)
            original_kill=process.kill
            def racing_kill():
                kwargs['stdout'].write('\n'+json.dumps({'type':'item.completed','item':{'type':'agent_message','text':message}}))
                kwargs['stdout'].write('\n'+json.dumps({'type':'turn.completed','usage':{'input_tokens':11,'output_tokens':5}}))
                kwargs['stdout'].flush()
                original_kill()
            process.kill=racing_kill
            return process
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)/'result.json'
            with patch('runner.shutil.which',return_value='fixture-codex'),patch('runner.subprocess.Popen',side_effect=racing_spawn):
                return runner.run('Terminal race fixture',output,require_json=True)

    def test_completed_terminal_landing_during_kill_clears_infrastructure_failure(self):
        record=self.execute_terminal_race('{"ok":true}')
        self.assertEqual(record['status'],'completed')
        self.assertEqual(record['failure'],'')
        self.assertIn('Further retries paused',record['transport_stop_observation'])
        self.assertEqual(record['transport_failure_counts'],{'http_request_failure':3})
        self.assertEqual(record['usage']['output_tokens'],5)
        self.assertTrue(record['terminal_output_matches'])

    def test_invalid_json_terminal_after_stop_is_model_failure(self):
        record=self.execute_terminal_race('not JSON')
        self.assertEqual(record['status'],'model_failed')
        self.assertIn('not valid JSON',record['failure'])
        self.assertNotIn('Further retries paused',record['failure'])
        self.assertIn('Further retries paused',record['transport_stop_observation'])
        self.assertTrue(record['terminal_output_matches'])

if __name__=='__main__':unittest.main()
