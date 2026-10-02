#!/usr/bin/env python3
"""Record an assessed post-reveal decision; never synthesize model/review records."""
import argparse
import hashlib
import json
from datetime import datetime
from pathlib import Path
from corpus import stamp
from evaluation import require_reveal, sealed
from runner import collect_call_records

def record(folder,decision,reason,changed_files=(),regression_record=None):
    folder=Path(folder)
    ledger=json.loads((folder/"ledger.json").read_text(encoding="utf-8"))
    if ledger["split"]!="development" or not ledger.get("revealed_at") or not ledger.get("lesson_record"):
        raise ValueError("An actual sealed/reviewed/revealed development case and diagnosis are required")
    require_reveal([ledger])
    lesson=ledger['lesson_record']
    previous_contexts={a['context_id'] for a in ledger['generations']+ledger['reviews']}
    if (lesson.get('status')!='completed' or lesson.get('isolation')!='CONTROLLED_PACKET_FRESH_CONTEXT'
        or not lesson.get('context_id') or lesson['context_id'] in previous_contexts
        or not sealed(lesson.get('path',''),lesson.get('output_hash'))
        or not lesson.get('sealed_at')
        or datetime.fromisoformat(lesson['sealed_at'])<datetime.fromisoformat(ledger['revealed_at'])):
        raise ValueError('Post-reveal diagnosis needs its own genuine completed context, timestamp and unchanged output')
    if not reason.strip():
        raise ValueError("An evidence-based decision reason is required")
    if decision=="accepted_change" and (not changed_files or not regression_record):
        raise ValueError("Accepted changes require actual files and regression output")
    change={"decision":decision,"reason":reason,"at":stamp(),"files":[]}
    for path in changed_files:
        file=Path(path)
        change["files"].append({"path":str(file),"sha256":hashlib.sha256(file.read_bytes()).hexdigest()})
    if regression_record:
        file=Path(regression_record)
        change["regression"]={"path":str(file),"sha256":hashlib.sha256(file.read_bytes()).hexdigest()}
    ledger["changes"].append(change)
    ledger["lesson_status"]="completed"
    ledger["status"]="completed"
    ledger["completed_at"]=stamp()
    ledger['calls']=collect_call_records(folder)
    (folder/"ledger.json").write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding="utf-8")
    return ledger

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("folder",type=Path)
    p.add_argument("--decision",choices=("no_change","retrieval_repair","rejected_change","accepted_change"),required=True)
    p.add_argument("--reason",required=True)
    p.add_argument("--changed-file",type=Path,action="append",default=[])
    p.add_argument("--regression-record",type=Path)
    args=p.parse_args()
    result=record(args.folder,args.decision,args.reason,args.changed_file,args.regression_record)
    print(result["case_id"]+": "+result["status"])

if __name__=="__main__":
    main()
