"""Export derived evaluation records; never release raw manuscripts or unrevealed answers."""
import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'skills/medical-journal-selector-skill-trainer/scripts'))
from corpus import stamp
from evaluation import require_reveal,promotion,summarize,evidence_coverage
from runner import collect_call_records


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def export(corpus,development_runs,final_runs,output,checks):
    corpus=Path(corpus)
    manifest=read(corpus/'manifest.json')
    records={'development':[],'holdout':[]}
    public=[]
    for case in manifest['cases']:
        split=case['split']
        if split not in records:
            continue
        runs=Path(development_runs if split=='development' else final_runs)
        file=runs/case['case_id']/'ledger.json'
        if not file.exists() and not file.parent.exists():
            continue
        ledger=read(file) if file.exists() else {'case_id':case['case_id'],'stratum':case['stratum'],'split':split,'status':'request_checkpoint'}
        # Read actual receipts at export time, including post-decision
        # regressions and unfinished-case preparation. Never mark them as a
        # completed case or rewrite the underlying ledger.
        ledger['calls']=collect_call_records(file.parent)
        if ledger.get('revealed_at'):
            require_reveal([ledger],final=split=='holdout')
            # Read only the original sealed generations, never regressions.
            # Enrich the exported copy; do not change historical ledger scores.
            for artifact in ledger['generations']:
                score=ledger.get('scores',{}).get(artifact['variant'])
                if score is not None:
                    score['source_coverage']=evidence_coverage(read(artifact['path'])['evidence'])
        records[split].append(ledger)
        entry={'case_id':case['case_id'],'stratum':case['stratum'],'split':split,
               'status':ledger.get('status'),'lesson_status':ledger.get('lesson_status'),
               'failure':ledger.get('failure'),'scores':ledger.get('scores') if ledger.get('revealed_at') else None}
        if ledger.get('revealed_at'):
            # No identifier, original outlet or result before actual blind seals.
            require_reveal([ledger],final=split=='holdout')
            answer=read(corpus/case['case_id']/'answer.json')
            entry.update(pmcid=case['pmcid'],original_outlet=answer['journal'],revealed_at=ledger['revealed_at'],
                         license_urls=case.get('license_audit',{}).get('license_urls',answer.get('license_urls',[])),
                         license_basis=case.get('license_audit',{}).get('permission_basis',answer.get('permission_basis')),
                         paired_decision=ledger.get('paired_decision'),
                         post_reveal_diagnosis={k:ledger.get('diagnosis',{}).get(k) for k in
                                               ('diagnosis','no_change_reason','stratum_confirmed','classification_reason')}
                                               if ledger.get('lesson_record') else None,
                         generation_seals=[{k:a.get(k) for k in ('variant','context_id','output_hash','sealed_at','model','effort')} for a in ledger['generations']],
                         review_seals=[{k:a.get(k) for k in ('context_id','output_hash','sealed_at','model','effort')} for a in ledger['reviews']],
                         changes=[{'decision':c['decision'],'reason':c['reason'],'at':c.get('at'),
                                   'files':[{'name':Path(f['path']).name,'sha256':f['sha256']} for f in c.get('files',[])],
                                   'regression_sha256':c.get('regression',{}).get('sha256')} for c in ledger.get('changes',[])])
        public.append(entry)
    revealed=[r for r in records['holdout'] if r.get('revealed_at')]
    if revealed:
        allocated=sum(c['split']=='holdout' for c in manifest['cases'])
        if len(records['holdout'])!=allocated:
            raise ValueError('Refusing export of a partially exposed final test batch')
        require_reveal(records['holdout'],final=True)
        last_seal=max(datetime.fromisoformat(a['sealed_at']) for r in records['holdout'] for a in r['reviews'])
        if any(datetime.fromisoformat(r['revealed_at'])<last_seal for r in revealed):
            raise ValueError('Final answer revealed before the whole batch was sealed')
    decision=promotion(records['development'],records['holdout'],checks)
    result={'exported_at':stamp(),'status':'passed' if decision['publish_allowed'] else 'incomplete_or_failed',
            'input_manifest_sha256':hashlib.sha256((corpus/'manifest.json').read_bytes()).hexdigest(),
            'seed':manifest['seed'],'as_of':manifest['as_of'],'protocol_revision':manifest.get('protocol_revision'),
            'allocated_development':sum(c['split']=='development' for c in manifest['cases']),
            'allocated_final':sum(c['split']=='holdout' for c in manifest['cases']),
            'completed_development':sum(r.get('status')=='completed' and r.get('lesson_status')=='completed' for r in records['development']),
            'completed_final':sum(r.get('status')=='completed' for r in records['holdout']),
            'development_summary':summarize(records['development']),'final_gate':decision,
            'interpretation':'AI workflow development; public-paper memory remains possible. Journal hits are not acceptance probabilities. Unrevealed final identifiers and answers are withheld.',
            'cases':public}
    output=Path(output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8',newline='\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--corpus',type=Path,required=True)
    p.add_argument('--development-runs',type=Path,required=True)
    p.add_argument('--final-runs',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--checks',type=Path,help='Observed compatibility/check outcomes; absent checks stay unpassed')
    args=p.parse_args()
    result=export(args.corpus,args.development_runs,args.final_runs,args.output,read(args.checks) if args.checks else {})
    print(json.dumps({k:result[k] for k in ('status','completed_development','completed_final')},indent=2))
