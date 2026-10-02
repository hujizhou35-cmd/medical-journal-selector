#!/usr/bin/env python3
"""Read an answer-free campaign checkpoint without running a model."""
import argparse
import json
from pathlib import Path

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))

def inspect(corpus,runs,split='development'):
    manifest=read(Path(corpus)/'manifest.json')
    records=[]
    for case in manifest['cases']:
        if case['split']!=split:continue
        work=Path(runs)/case['case_id']
        ledger=read(work/'ledger.json') if (work/'ledger.json').exists() else {}
        completed=(ledger.get('status')=='completed' and
                   (split=='holdout' or ledger.get('lesson_status')=='completed'))
        calls=[]
        for path in sorted(work.glob('*.record.json')):
            call=read(path)
            calls.append({'role':path.name.removesuffix('.record.json'),
                          'status':call.get('status'),'elapsed_seconds':call.get('elapsed_seconds'),
                          'usage_available':bool(call.get('usage'))})
        # A request file proves a request was prepared, not that a model
        # completed it or that the external process is still running.
        unfinished_requests=[p.name.removesuffix('.input.txt') for p in work.glob('*.input.txt')
                             if not p.with_name(p.name.removesuffix('.input.txt')+'.record.json').exists()]
        if ledger or calls or unfinished_requests:
            records.append({'case_id':case['case_id'],'stratum':case['stratum'],
                            'state':ledger.get('status','request_checkpoint'),
                            'lesson_status':ledger.get('lesson_status'),
                            'distinct_case_completed':completed,'calls':calls,
                            'requests_without_terminal_record':unfinished_requests,
                            'failure':ledger.get('failure')})
    return {'split':split,'allocated':sum(c['split']==split for c in manifest['cases']),
            'completed':sum(r['distinct_case_completed'] for r in records),
            'paused_at_boundary':(Path(runs)/'PAUSE').exists(),'cases':records,
            'interpretation':'Request checkpoints may be in progress or interrupted; only complete generation, review, reveal and development-decision records count. No publishing answers are read.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',type=Path,required=True)
    p.add_argument('--runs',type=Path,required=True)
    p.add_argument('--split',choices=('development','holdout'),default='development')
    p.add_argument('--output',type=Path)
    args=p.parse_args()
    result=inspect(args.corpus,args.runs,args.split)
    text=json.dumps(result,ensure_ascii=False,indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(text,encoding='utf-8')
    print(text)

if __name__=='__main__':main()
