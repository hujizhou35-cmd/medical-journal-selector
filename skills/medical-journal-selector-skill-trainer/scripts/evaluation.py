#!/usr/bin/env python3
"""Deterministic discovery baselines, reveal gates, counts and Wilson intervals."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path

STOP = set("the a an and or of to in on for with by from as is was were are this that these those study studies analysis results methods patients using based between among into associated association conclusion objective background method result however compared effect effects disease diseases clinical medical health treatment including could can may more also not all both we our their it its has have had such than then under over through during after before which been new risk model data models review systematic meta report case reports".split())

def journal_match(answer, journal_id='', title='', issns=()):
    """Match known outlet identity, not scope or policy; missing IDs are not an automatic miss."""
    def ids(values):
        return {re.sub(r'\s+','',str(v)).upper() for v in values if re.fullmatch(r'\d{4}-\d{3}[\dXx]',str(v).strip())}
    target_ids=ids(answer.get('issns',[]))
    observed_ids=ids([journal_id]+list(issns))
    if target_ids and observed_ids:
        return bool(target_ids & observed_ids)
    def canonical(value):
        return re.sub(r'[^a-z0-9]+',' ',value.casefold()).strip()
    names={canonical(n) for n in [answer.get('journal','')]+answer.get('journal_aliases',[]) if n}
    if names and title:
        return canonical(title) in names
    return None

def tokens(text):
    return [w for w in re.findall(r"[a-z][a-z-]{2,}", text.lower()) if w not in STOP]

def fixed_baselines(abstract, keywords, precedents, limit=10):
    """Cosine TF-IDF abstracts; BM25 keyword query; max per journal, not counts."""
    docs = [tokens(p.get("title", "") + " " + p.get("abstract", "")) for p in precedents]
    n = len(docs)
    if not n:
        return {"keyword":[],"abstract":[]}
    df = collections.Counter(w for doc in docs for w in set(doc))
    idf = {w:math.log((1+n)/(1+c))+1 for w,c in df.items()}
    def vector(words):
        c = collections.Counter(words)
        raw = {w:(1+math.log(v))*idf.get(w,math.log(1+n)+1) for w,v in c.items()}
        norm = math.sqrt(sum(v*v for v in raw.values())) or 1
        return {w:v/norm for w,v in raw.items()}
    q = vector(tokens(abstract))
    query = sorted(set(tokens(" ".join(keywords))))
    avg = sum(map(len,docs))/n or 1
    scored = {"keyword":{},"abstract":{}}
    for p,doc in zip(precedents,docs):
        counts = collections.Counter(doc)
        vec = vector(doc)
        cosine = sum(q.get(w,0)*v for w,v in vec.items())
        bm25 = 0.0
        for w in query:
            f = counts.get(w,0)
            if f:
                c = df[w]
                bm25 += math.log(1+(n-c+.5)/(c+.5))*f*2.2/(f+1.2*(.25+.75*len(doc)/avg))
        key = p["journal_id"]
        for kind,value in (("keyword",bm25),("abstract",cosine)):
            if value > 0:
                scored[kind][key] = max(value,scored[kind].get(key,0))
    return {kind:[{"journal_id":key,"score":value} for key,value in sorted(vals.items(),key=lambda x:(-x[1],x[0]))[:limit]] for kind,vals in scored.items()}

def candidate_handoff(abstract,keywords,papers,delivered,source_plan):
    """Preparation-only trace of every discovered outlet; never consult answers."""
    complete=fixed_baselines(abstract,keywords,papers,limit=None)
    ranks={kind:{p['journal_id']:{'rank':i,'score':p['score']} for i,p in enumerate(rows,1)}
           for kind,rows in complete.items()}
    planned={j['journal_id']:j.get('official_urls',[]) for j in source_plan['journals']}
    handed=collections.Counter(p['journal_id'] for p in delivered)
    names={p['journal_id']:p['journal'] for p in papers}
    result=[]
    for jid in sorted(names):
        row={'journal_id':jid,'journal':names[jid],
             'baseline_positions':{kind:items.get(jid) for kind,items in ranks.items()},
             'delivered_papers':handed[jid],'initial_source_urls':planned.get(jid,[])}
        row['curation_reason']=('Retained by the fixed top-ten baseline union' if handed[jid]
                                else 'Outside both fixed positive-score top-ten baseline lists')
        result.append(row)
    return result

def wilson(hits, total, z=1.959963984540054):
    if not total:
        return None
    p=hits/total
    d=1+z*z/total
    mid=(p+z*z/(2*total))/d
    delta=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/d
    return [max(0,mid-delta),min(1,mid+delta)]

def sealed(path, expected_hash):
    return Path(path).exists() and hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected_hash

def require_reveal(records, final=False):
    """Validate actual output/review seals before any answer read."""
    contexts = []
    for r in records:
        generations = r.get("generations",[])
        reviews = r.get("reviews",[])
        if not generations or len(reviews)<2:
            raise ValueError("Missing generation or two blind review seals")
        for artifact in generations+reviews:
            if not artifact.get("sealed_at") or not artifact.get("context_id"):
                raise ValueError("Missing genuine context/timestamp")
            if artifact.get("status") != "completed" or artifact.get("isolation") != "CONTROLLED_PACKET_FRESH_CONTEXT":
                raise ValueError("Failed/unverified isolation cannot pass reveal gate")
            if not sealed(artifact["path"],artifact["output_hash"]):
                raise ValueError("Artifact changed after sealing")
            contexts.append(artifact["context_id"])
        first_review=min(datetime.fromisoformat(x["sealed_at"]) for x in reviews)
        last_output=max(datetime.fromisoformat(x["sealed_at"]) for x in generations)
        if first_review < last_output:
            raise ValueError("Review was sealed before its generations")
        if final and {g["variant"] for g in generations} != {"v1","v2"}:
            raise ValueError("Final case must include both frozen model variants")
    if len(contexts)!=len(set(contexts)):
        raise ValueError("A generator/reviewer context was reused")
    return True

def evidence_coverage(evidence):
    """Count original fact envelopes, not independent verification successes."""
    fields={}
    for journal in evidence.get('journals',[]):
        for block in ('facts','timelines'):
            values=journal.get(block,{})
            if not isinstance(values,dict):
                continue # Schema failures are reported by the source audit.
            for field,envelope in values.items():
                key=field if block=='facts' else 'timeline:'+field
                counts=fields.setdefault(key,{'verified':0,'unverified':0,'invalid_status':0})
                status=envelope.get('status') if isinstance(envelope,dict) else None
                counts[status if status in ('verified','unverified') else 'invalid_status']+=1
    return fields


def summarize(records):
    out={"cases":len(records),"completed":0,"infrastructure_failed":0,"contamination_failed":0,"model_failed":0,"variants":{},"strata":{},"elapsed_seconds":0,"usage":{},"model_calls":0,"usage_reported_calls":0,"usage_unavailable_calls":0}
    def add_score(aggregate,value):
        aggregate["n"]+=1
        rank=value.get("true_rank")
        for k in (3,5,10):
            aggregate[f"hit{k}"]+=int(rank is not None and rank<=k)
        aggregate["usable_known"]+=int(value.get("usable") is not None)
        aggregate["usable"]+=int(value.get("usable") is True)
        aggregate["discovered_known"]+=int(value.get("discovered") is not None)
        aggregate["discovered"]+=int(value.get("discovered") is True)
        aggregate["hard_failures"]+=len(value.get("hard_failures",[]))
        aggregate['hard_failure_cases']+=int(bool(value.get('hard_failures',[])))
        coverage=value.get('source_coverage')
        if coverage is not None:
            aggregate['source_coverage_cases']+=1
            for field,counts in coverage.items():
                target=aggregate['source_coverage'].setdefault(field,{'verified':0,'unverified':0,'invalid_status':0})
                for status,count in counts.items():
                    target[status]=target.get(status,0)+count
    def blank():
        return {"n":0,"hit3":0,"hit5":0,"hit10":0,"usable":0,"usable_known":0,"discovered":0,"discovered_known":0,"hard_failures":0,'hard_failure_cases':0,'source_coverage_cases':0,'source_coverage':{}}
    for r in records:
        state=r.get("status","incomplete")
        out[state]=out.get(state,0)+1
        stratum=r.get("stratum","unknown")
        group=out["strata"].setdefault(stratum,{"cases":0,"completed":0,"states":{},"variants":{}})
        group["cases"]+=1
        group["states"][state]=group["states"].get(state,0)+1
        calls=r.get("calls")
        if calls is None:
            calls=r.get("generations",[])+r.get("reviews",[])+r.get("attempts",[])+([r["lesson_record"]] if r.get("lesson_record") else [])
        for artifact in calls:
            out["model_calls"]+=1
            if artifact.get("usage") is None:
                out["usage_unavailable_calls"]+=1
            else:
                out["usage_reported_calls"]+=1
            out["elapsed_seconds"]+=artifact.get("elapsed_seconds",0)
            for key,value in (artifact.get("usage") or {}).items():
                if isinstance(value,(int,float)):
                    out["usage"][key]=out["usage"].get(key,0)+value
        if state != "completed":
            continue
        group["completed"]+=1
        for name,value in r["scores"].items():
            add_score(out["variants"].setdefault(name,blank()),value)
            add_score(group["variants"].setdefault(name,blank()),value)
    for value in list(out["variants"].values())+[v for g in out["strata"].values() for v in g["variants"].values()]:
        for k in (3,5,10):
            value[f"hit{k}_wilson95"]=wilson(value[f"hit{k}"],value["n"])
    out["unscored"]=len(records)-out["completed"]
    out["time_interpretation"]="Sum of recorded model-call elapsed times, including parallel reviews; not end-to-end wall-clock runtime."
    out["usage_interpretation"]="Available CLI usage only. Calls with unavailable usage are counted separately, not assumed to consume zero."
    out["interval_interpretation"]="Conditional on completed, scored cases; unscored cases are separately retained, not claimed as successful runs."
    out['hard_failure_interpretation']='hard_failures counts retained source/reviewer flags, which can repeat one underlying error. hard_failure_cases counts affected cases out of n; original development errors remain after regression.'
    out['source_coverage_interpretation']='Counts of original model fact/timeline envelopes by field and declared status; verified labels remain subject to source/reviewer audits. They are not independent proof of correctness. Cases without recorded envelopes are not assumed fully verified or fully missing.'
    return out

def promotion(development, final, checks):
    summary=summarize(final)
    failures=[]
    for label,records in (("development",development),("final",final)):
        ids=[r.get("case_id") for r in records]
        if len(ids)!=len(set(ids)):
            failures.append(f"Duplicate distinct-case IDs: {label}")
    if {r.get("case_id") for r in development}&{r.get("case_id") for r in final}:
        failures.append("Development/final case overlap")
    if {r.get("masked_input_hash") for r in development if r.get("masked_input_hash")}&{r.get("masked_input_hash") for r in final if r.get("masked_input_hash")}:
        failures.append("Development/final manuscript overlap")
    if sum(x.get("status")=="completed" and x.get("lesson_status")=="completed" for x in development)<100:
        failures.append("Development cases incomplete")
    if summary.get("completed",0)<50:
        failures.append("Untouched final cases incomplete")
    from corpus import STRATA
    for stratum in STRATA:
        if sum(r.get("status")=="completed" and r.get("stratum")==stratum for r in development)<10 or sum(r.get("status")=="completed" and r.get("stratum")==stratum for r in final)<5:
            failures.append(f"Stratum coverage incomplete: {stratum}")
    v1=summary["variants"].get("v1",{})
    v2=summary["variants"].get("v2",{})
    if v1.get("n",0)!=summary.get("completed",0) or v2.get("n",0)!=summary.get("completed",0):
        failures.append("Missing paired variant scores")
    if any(summary["variants"].get(name,{}).get("n",0)!=summary.get("completed",0) for name in ("keyword","abstract")):
        failures.append("Missing fixed-baseline scores")
    completed=[r for r in final if r.get("status")=="completed"]
    if completed:
        try:
            require_reveal(completed,final=True)
            last_batch_review=max(datetime.fromisoformat(a["sealed_at"]) for r in completed for a in r["reviews"])
            for r in completed:
                if not r.get("revealed_at") or datetime.fromisoformat(r["revealed_at"])<last_batch_review:
                    raise ValueError("Answer reveal preceded whole-batch review sealing")
        except (ValueError,KeyError,TypeError) as exc:
            failures.append("Final artifact/reveal gate: "+str(exc))
        for name in ("v1","v2"):
            hashes={r.get("skill_hashes",{}).get(name) for r in completed}
            if None in hashes or len(hashes)!=1:
                failures.append("Final Skill snapshot changed or unrecorded: "+name)
        configurations={(a.get("model"),a.get("effort")) for r in completed for a in r.get("generations",[])+r.get('reviews',[])}
        if any(None in pair for pair in configurations) or len(configurations)!=1:
            failures.append("Final model configuration changed or unrecorded")
        protocols={json.dumps(r.get('protocol_hashes'),sort_keys=True) for r in completed}
        if 'null' in protocols or len(protocols)!=1:
            failures.append('Final execution protocol changed or unrecorded')
    if not v2 or v2.get("hard_failures",1):
        failures.append("Unresolved V2 hard failures or missing scores")
    if v2.get("usable",-1)<v1.get("usable",0):
        failures.append("Usable coverage decreased")
    votes=collections.Counter(r.get("paired_decision") for r in final if r.get("status")=="completed")
    if votes["v2"]<votes["v1"]:
        failures.append("V2 has more paired losses than wins")
    if votes.get("unresolved",0):
        failures.append("Unresolved paired review decisions")
    for key in ("protected_behavior","languages","packages","installations","isolation"):
        if checks.get(key) is not True:
            failures.append(f"Check not observed passed: {key}")
    return {"publish_allowed":not failures,"failures":failures,"summary":summary,"paired":dict(votes)}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("records",type=Path)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.output.write_text(json.dumps(summarize(json.loads(a.records.read_text(encoding="utf-8"))),indent=2),encoding="utf-8")

if __name__=="__main__":
    main()
