#!/usr/bin/env python3
"""Fresh, tool-restricted Codex calls with persisted genuine outcome records."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

MODEL = "gpt-6.1-sol"
EFFORT = "xhigh"
TRANSPORT_FAILURE_LIMIT = 3

def transport_failure_counts(events):
    """Group observed primary transport errors, never model/content failures."""
    counts=Counter()
    for event in events:
        if event.get('type')!='error':continue
        message=event.get('message','').casefold()
        if 'error sending request' in message:
            counts['http_request_failure']+=1
        elif 'error decoding response body' in message:
            counts['response_decode_failure']+=1
        elif 'stream disconnected before completion' in message:
            counts['stream_disconnect']+=1
    return dict(counts)

def repeated_transport_failure(events):
    for cause,count in transport_failure_counts(events).items():
        if count>=TRANSPORT_FAILURE_LIMIT:
            return f'Repeated transport failure: {cause}; observed {count} same-cause errors (limit {TRANSPORT_FAILURE_LIMIT}). Further retries paused.'
    return ''

def stamp():
    return datetime.now(timezone.utc).isoformat()

def digest(data):
    return hashlib.sha256(data).hexdigest()


def parse_json_message(message):
    """Accept one JSON value, optionally wrapped in a single JSON fence."""
    value=message.strip()
    fenced=re.fullmatch(r"```(?:json)?\s*\n([\s\S]*?)\n```",value,re.IGNORECASE)
    if fenced:
        value=fenced.group(1)
    def reject_constant(token):
        raise ValueError("Non-finite JSON constant: "+token)
    return json.loads(value,parse_constant=reject_constant)


def mark_output_contract_failed(output,reason):
    """Keep the genuine completed call but prevent reuse of its invalid payload."""
    output=Path(output)
    record_path=output.with_suffix(output.suffix+".record.json")
    record=json.loads(record_path.read_text(encoding="utf-8"))
    if record.get("status")!="completed" or record.get("output_hash")!=digest(output.read_bytes()):
        raise ValueError("Cannot reject an output without a matching completed call")
    record["output_contract_status"]="failed"
    record["output_contract_failure"]=str(reason)
    record_path.write_text(json.dumps(record,indent=2),encoding="utf-8")

def collect_call_records(work):
    """Count genuine receipts, including failed attempts and regressions once."""
    records=[]
    seen=set()
    for path in sorted(Path(work).rglob("*.record.json")):
        data=json.loads(path.read_text(encoding='utf-8'))
        key=(data.get('context_id'),data.get('started_at'),data.get('input_hash'))
        if key in seen:continue
        seen.add(key)
        records.append({'role':path.name.removesuffix('.record.json'),'record_path':str(path.resolve()),**data})
    return records

def event_records(path):
    events=[]
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass # a partial, not-yet-flushed frame cannot establish completion
    return events

def completed_message(events):
    terminal=next((i for i in range(len(events)-1,-1,-1) if events[i].get("type")=="turn.completed"),None)
    if terminal is None or any(e.get("type")=="turn.failed" for e in events):
        return None
    if any(e.get("item",{}).get("type") in {"command_execution","mcp_tool_call","web_search","file_change"} for e in events):
        return None
    return next((e["item"].get("text") for e in reversed(events[:terminal]) if e.get("type")=="item.completed" and e.get("item",{}).get("type")=="agent_message"),None)

def persist_completed_message(output, events):
    """Store only the genuine terminal message, preserving a stale CLI output."""
    output=Path(output)
    message=completed_message(events)
    if message is None:
        raise ValueError("No genuine completed tool-free model message")
    if output.exists() and output.read_text(encoding="utf-8").strip()!=message.strip():
        previous=output.read_bytes()
        backup=output.with_name(output.name+".conflicting-output-"+digest(previous)[:16])
        if not backup.exists():
            backup.write_bytes(previous)
    output.write_text(message,encoding="utf-8")
    if output.read_text(encoding="utf-8")!=message:
        raise ValueError("Saved output differs from the actual terminal model message")
    return message

def recover_terminal_output(output):
    """Recover only an exact real terminal event; keep the failed transport record."""
    output=Path(output)
    record_path=output.with_suffix(output.suffix+".record.json")
    record=json.loads(record_path.read_text(encoding="utf-8"))
    events=event_records(output.with_suffix(output.suffix+".events.jsonl"))
    message=completed_message(events)
    if record.get("status")!="infrastructure_failed" or message is None or not record.get("context_id"):
        raise ValueError("No genuine completed tool-free model turn to recover")
    # This recovery is for structured campaign outputs, not a truncated response.
    parse_json_message(message)
    if output.exists() and output.read_text(encoding="utf-8").strip()!=message.strip():
        raise ValueError("Saved output conflicts with the actual model event")
    original=record_path.with_suffix(record_path.suffix+".transport-failed-original")
    if original.exists():
        raise ValueError("Recovery has already been attempted")
    shutil.copy2(record_path,original)
    if not output.exists():
        output.write_text(message,encoding="utf-8")
    record.update(status="completed",isolation="CONTROLLED_PACKET_FRESH_CONTEXT",output_hash=digest(output.read_bytes()),
                  model_turn_completed=True,transport_outcome="timeout after actual completed model event; original record retained",
                  transport_failure=record.get("failure"),failure="",recovered_at=stamp())
    record_path.write_text(json.dumps(record,indent=2),encoding="utf-8")
    return record

def run(prompt, output, schema=None, timeout=900, model=MODEL, effort=EFFORT, require_json=False):
    """Never resume an exposed thread. Reuse only an identical completed input."""
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    packet = prompt.encode("utf-8")
    identity = digest(packet + model.encode() + effort.encode() + b"controlled-packet-env-closed-tools-disabled-v3" +
                      (digest(Path(schema).read_bytes()).encode() if schema else b""))
    record_path = output.with_suffix(output.suffix + ".record.json")
    if record_path.exists():
        previous = json.loads(record_path.read_text(encoding="utf-8"))
        if (previous.get("input_hash") == identity and previous.get("status") == "completed" and
                previous.get("output_contract_status")!="failed" and output.exists()):
            if previous.get("output_hash") == digest(output.read_bytes()):
                actual=completed_message(event_records(output.with_suffix(output.suffix+".events.jsonl")))
                if actual is None or output.read_text(encoding="utf-8").strip()!=actual.strip():
                    raise ValueError("Completed checkpoint conflicts with its actual terminal events")
                if not require_json:
                    return previous
                try:
                    parse_json_message(output.read_text(encoding="utf-8"))
                except ValueError:
                    # A transport-complete but schema-invalid response is not
                    # reusable. The archive below preserves it as an attempt
                    # before the fresh call starts.
                    pass
                else:
                    return previous
        if previous.get("input_hash") != identity:
            raise ValueError("Refusing to overwrite a run with different inputs/settings")
        # A retry does not erase the failed call or create another case.
        archive=output.parent/(output.stem+".attempts")
        number=len(list(archive.glob("attempt-*")))+1 if archive.exists() else 1
        attempt=archive/f"attempt-{number:02d}"
        attempt.mkdir(parents=True,exist_ok=False)
        for source in (output,record_path,output.with_suffix(output.suffix+".events.jsonl"),output.with_suffix(output.suffix+".stderr.txt")):
            if source.exists():
                shutil.copy2(source,attempt/source.name)
    executable = shutil.which("codex")
    if not executable:
        raise RuntimeError("Codex CLI was not found")
    workspace = output.parent / (output.stem + ".empty-workspace")
    workspace.mkdir(exist_ok=True)
    command = [executable, "exec", "--ignore-user-config", "--ephemeral", "--skip-git-repo-check",
               "--sandbox", "read-only", "--disable", "shell_tool", "--disable", "memories",
               "--disable", "multi_agent", "--disable", "hooks", "--disable", "plugins",
               "--disable", "remote_plugin", "--disable", "apps", "--disable", "skill_search",
               "--enable", "skip_host_skill_discovery", "-c", "project_doc_max_bytes=0", "-c", 'web_search="disabled"',
               "-c", 'model_provider="evaluation-http"',
               "-c", 'model_providers.evaluation-http.name="OpenAI authenticated HTTP"',
               "-c", "model_providers.evaluation-http.requires_openai_auth=true",
               "-c", "model_providers.evaluation-http.supports_websockets=false",
               "-c", "model_providers.evaluation-http.request_max_retries=0",
               "-c", "model_providers.evaluation-http.stream_max_retries=2",
               "-c", "memories.use_memories=false", "-c", "memories.generate_memories=false",
               "-m", model, "-c", f'model_reasoning_effort="{effort}"', "--json",
               "-C", str(workspace.resolve()), "-o", str(output.resolve())]
    if schema:
        command.extend(["--output-schema", str(Path(schema).resolve())])
    command.append("-")
    started = stamp()
    before = time.monotonic()
    log_path = output.with_suffix(output.suffix + ".events.jsonl")
    status, events, failure, exitcode = "infrastructure_failed", [], "", None
    transport_stop_observation = ""
    try:
        # Desktop coordination variables can inject the parent thread's MCP
        # bridge and policies into a CLI child. Saved auth is still resolved
        # normally; do not inherit the parent's task/thread bridge.
        child_env={k:v for k,v in os.environ.items() if not k.startswith("CODEX_") or k=="CODEX_HOME"}
        stderr_path=output.with_suffix(output.suffix + ".stderr.txt")
        input_path=output.with_suffix(output.suffix+".input.txt")
        input_path.write_bytes(packet)
        with input_path.open("rb") as input_file,log_path.open("w",encoding="utf-8") as stdout_file,stderr_path.open("w",encoding="utf-8") as stderr_file:
            process=subprocess.Popen(command,stdin=input_file,stdout=stdout_file,stderr=stderr_file,
                                     text=True,encoding="utf-8",errors="replace",cwd=workspace,env=child_env)
            # Read the real terminal frame rather than waiting indefinitely on
            # the CLI's unrelated model-catalog refresh/shutdown tasks.
            deadline=time.monotonic()+timeout
            while process.poll() is None:
                streamed=event_records(log_path)
                message=completed_message(streamed)
                if message is not None:
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    break
                stop_reason=repeated_transport_failure(streamed)
                if stop_reason:
                    failure=stop_reason
                    transport_stop_observation=stop_reason
                    process.kill()
                    process.wait()
                    break
                if time.monotonic()>=deadline:
                    process.kill()
                    process.wait()
                    raise subprocess.TimeoutExpired(command,timeout)
                time.sleep(.25)
            exitcode=process.returncode
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
        tool_types = {"command_execution", "mcp_tool_call", "web_search", "file_change"}
        unexpected = [e for e in events if e.get("item", {}).get("type") in tool_types]
        finished = any(e.get("type") == "turn.completed" for e in events)
        if unexpected:
            status, failure = "contamination_failed", "Unexpected tool use outside controlled packets"
        elif finished and completed_message(events) is not None:
            # A terminal frame may land during stop/kill. Classify its real
            # outcome and retain the stop observation separately from failure.
            failure=""
            persist_completed_message(output,events)
            if require_json or schema:
                try:
                    parse_json_message(output.read_text(encoding="utf-8"))
                except ValueError as exc:
                    status = "model_failed"
                    failure = "Completed model response was not valid JSON: " + str(exc)
                else:
                    status = "completed"
            else:
                status = "completed"
        else:
            failure = failure or repeated_transport_failure(events) or "Model call did not complete successfully"
    except subprocess.TimeoutExpired:
        failure = f"Model call exceeded {timeout} seconds"
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                pass
    except (OSError, ValueError) as exc:
        failure = str(exc)
    record = {"status": status, "failure": failure, "exit_code": exitcode, "model": model,
              "timeout_seconds":timeout,
              "effort": effort, "transport": "OpenAI ChatGPT authentication / HTTPS", "input_hash": identity, "started_at": started, "completed_at": stamp(),
              "elapsed_seconds": round(time.monotonic()-before, 3),
              "context_id": next((e.get("thread_id") for e in events if e.get("type") == "thread.started"), None),
              "usage": next((e.get("usage") for e in reversed(events) if e.get("type") == "turn.completed"), None),
              "parent_bridge_inherited":False,
              "model_turn_completed":any(e.get("type")=="turn.completed" for e in events),
              "transport_outcome":"normal exit" if exitcode==0 else ("CLI stopped after observed model completion" if status in ("completed","model_failed") else "failed/incomplete"),
              "isolation": "CONTROLLED_PACKET_FRESH_CONTEXT" if status in ("completed","model_failed") else "UNVERIFIED",
              "output_hash": digest(output.read_bytes()) if status in ("completed","model_failed") and output.exists() else None}
    record['terminal_output_matches']=(status in ("completed","model_failed") and output.exists() and
        output.read_text(encoding='utf-8')==completed_message(events))
    retries=sum(e.get('type')=='error' and 'Reconnecting' in e.get('message','') for e in events)
    record['transport_retries']=retries
    record['transport_failure_counts']=transport_failure_counts(events)
    record['transport_stop_observation']=transport_stop_observation or None
    record['transport_retry_policy']={'http_request_retries':0,'stream_retries':2,
                                     'same_cause_failure_limit':TRANSPORT_FAILURE_LIMIT,
                                     'scope':'Per-call CLI overrides; user configuration is unchanged. Completed older checkpoints retain their original policy and receipt.'}
    record['usage_scope']=('Last completed turn only; usage from disconnected retry attempts is unavailable'
                           if retries else 'Available terminal-turn usage only')
    record_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("prompt", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--schema", type=Path)
    p.add_argument("--timeout", type=int, default=900)
    args = p.parse_args()
    result = run(args.prompt.read_text(encoding="utf-8"), args.output, args.schema, args.timeout)
    print(json.dumps(result, indent=2))
    if result["status"] != "completed":
        raise SystemExit(1)

if __name__ == "__main__":
    main()
