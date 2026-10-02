#!/usr/bin/env python3
"""Seeded Europe PMC OA corpus acquisition and answer-free XML body packets."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import random
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://www.ebi.ac.uk/europepmc/webservices/rest/"
STRATA = {
 "clinical_nursing": '(TITLE_ABS:"clinical trial" OR TITLE_ABS:"nursing" OR TITLE_ABS:"cohort study") NOT (TITLE_ABS:review OR TITLE_ABS:NHANES OR TITLE_ABS:MIMIC)',
 "laboratory": '(TITLE_ABS:"mouse" OR TITLE_ABS:"mice") AND (TITLE_ABS:"experiment" OR TITLE_ABS:"mechanism") NOT TITLE_ABS:review',
 "public_database": '(TITLE_ABS:NHANES OR TITLE_ABS:MIMIC OR TITLE_ABS:"UK Biobank") NOT TITLE_ABS:review',
 "bioinformatics": '(TITLE_ABS:bioinformatics OR TITLE_ABS:"single-cell" OR TITLE_ABS:"transcriptomic") NOT (TITLE_ABS:review OR TITLE_ABS:"network pharmacology")',
 "prediction": '(TITLE_ABS:"prediction model" OR TITLE_ABS:"risk prediction" OR TITLE_ABS:nomogram) NOT TITLE_ABS:review',
 "network": '(TITLE_ABS:"network pharmacology" OR TITLE_ABS:"network toxicology") NOT TITLE_ABS:review',
 "systematic_meta": '(TITLE:"systematic review" OR TITLE:"meta-analysis")',
 "other_review": '(TITLE:"scoping review" OR TITLE:"narrative review" OR (PUB_TYPE:review AND TITLE_ABS:medicine)) NOT (TITLE:"systematic review" OR TITLE:"meta-analysis" OR TITLE:bibliometric)',
 "bibliometrics": '(TITLE:bibliometric OR TITLE:"scientometric") AND (TITLE_ABS:health OR TITLE_ABS:disease OR TITLE_ABS:clinical OR TITLE_ABS:medicine)',
 "case_report": '(TITLE:"case report" OR TITLE:"case series") NOT TITLE:review'
}

def stamp():
    return datetime.now(timezone.utc).isoformat()

def get(url, timeout=40, attempts=3):
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={"User-Agent":"MedicalJournalSelectorResearch/2.0 (+https://github.com/hujizhou35-cmd/medical-journal-selector)"})
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read()
        except Exception:
            if attempt + 1 == attempts:
                raise
            time.sleep(min(2 ** attempt, 4))

def search(query, size=100, cursor="*", result_type="core"):
    url = BASE + "search?" + urllib.parse.urlencode({"query":query,"format":"json","pageSize":size,"resultType":result_type,"cursorMark":cursor})
    return json.loads(get(url)), url

def text_of(node):
    return re.sub(r"\s+", " ", " ".join(node.itertext())).strip() if node is not None else ""

PUBLICATION_NOTE = re.compile(
    r"how to cite (?:this|the) (?:article|paper)|"
    r"time of (?:primary|first|initial|peer) review|"
    r"(?:article|publication) history|"
    r"(?:received|accepted|published online)\s*(?::|on)?\s*\d{1,2}[\s/-]+(?:[A-Za-z]{3,9}|\d{1,2})[\s,/-]+\d{4}", re.I)
NON_RESEARCH_HEADING = re.compile(
    r"^(?:references?|bibliography|acknowledg\w*|author\w* contribut\w*|"
    r"competing\w*|conflict\w*|funding\w*|declaration\w*|disclosure\w*|"
    r"transparency statement|copyright\w*|publisher.?s note|article information)(?:\b|$)", re.I)

def remove_keep_tail(parent, child):
    """Removing an XML citation must not delete the research after </xref>."""
    siblings = list(parent)
    position = siblings.index(child)
    if child.tail:
        if position:
            previous = siblings[position-1]
            previous.tail = (previous.tail or "") + child.tail
        else:
            parent.text = (parent.text or "") + child.tail
    parent.remove(child)

def research_text(node):
    """Read research content recursively, excluding nested publishing metadata."""
    if node is None:
        return ""
    node = copy.deepcopy(node)
    def clean(parent):
        for child in list(parent):
            tag = child.tag.rsplit('}',1)[-1]
            heading = text_of(child.find('title'))
            blocked = (tag in ('ref-list','ref','ack','permissions','history','article-meta',
                               'journal-meta','contrib-group','author-notes','corresp','email')
                       or (tag == 'xref' and child.get('ref-type')=='bibr')
                       or (tag == 'sec' and (NON_RESEARCH_HEADING.search(heading)
                                            or child.get('sec-type','').lower() in
                                            ('references','ref-list','ack','author-contributions','conflict-of-interest'))))
            # Short metadata notes, not paragraphs describing patients receiving
            # treatment or results being published by other researchers.
            if tag in ('p','fn') and len(text_of(child)) < 1800 and PUBLICATION_NOTE.search(text_of(child)):
                blocked = True
            if blocked:
                remove_keep_tail(parent,child)
            elif tag in ('ext-link','uri'):
                # External bibliographic links can reveal answers. Keep their
                # following narrative; their visible label is not needed here.
                remove_keep_tail(parent,child)
            else:
                clean(child)
    clean(node)
    return text_of(node)

def license_eligibility(text):
    """Use the protocol's CC BY/CC0 subset; do not infer rights from 'open access'."""
    lower = text.lower()
    normalized = re.sub(r"[^a-z0-9]+", " ", lower)
    restrictive = (re.search(r"creativecommons\.org/licenses/by-(?:nc|nd|sa)(?:-|/)", lower)
                   or re.search(r"\bnon\s*commercial\b|\bno\s*deriv(?:ative|atives|s)?\b|\bshare\s*alike\b", normalized)
                   or re.search(r"\b(?:cc\s*)?by\s+(?:nc|nd|sa)\b", normalized))
    if restrictive:
        return False, "restricted_or_mixed_license_not_in_CC_BY_CC0_subset"
    known = (re.search(r"creativecommons\.org/(?:licenses/by/|publicdomain/zero/)", lower)
             or "creative commons attribution" in normalized
             or re.search(r"\bcc\s*0\b", normalized))
    return (True, "CC_BY_or_CC0_recorded") if known else (False, "permission_not_established")

def attach_journal_identity(target, item, pmcid, url, checked_at):
    """Preparation-only answer metadata. Never include this record in a blind packet."""
    if item.get('pmcid')!=pmcid and not (item.get('source')=='PMC' and item.get('id')==pmcid):
        raise ValueError('Identity API record does not identify the allocated article')
    if target.get('ids',{}).get('doi') and item.get('doi') and target['ids']['doi'].casefold()!=item['doi'].casefold():
        raise ValueError('Publication DOI conflict in identity metadata')
    journal=item.get('journalInfo',{}).get('journal',{})
    issns=[journal.get(k) for k in ('issn','essn') if journal.get(k)]
    target['issns']=sorted(set(target.get('issns',[])+issns))
    target['journal_aliases']=sorted(set([target.get('journal','')]+target.get('journal_aliases',[])+[journal.get('title','')])-{''})
    target['journal_identity_record']={'url':url,'checked_at':checked_at,'source_type':'bibliographic',
                                       'matched_pmcid':pmcid,'issns':issns,'title':journal.get('title')}
    return target

def parse_article(xml):
    root = ET.fromstring(xml)
    meta = root.find("./front/article-meta")
    journal = root.find("./front/journal-meta")
    title = text_of(meta.find("title-group/article-title"))
    ids = {node.get("pub-id-type"):text_of(node) for node in meta.findall("article-id")}
    authors = []
    for name in meta.findall("contrib-group/contrib/name"):
        surname,given=text_of(name.find('surname')),text_of(name.find('given-names'))
        authors.extend([text_of(name), (given+' '+surname).strip(), (surname+' '+given).strip()])
    authors=sorted(set(authors)-{''})
    aliases=[text_of(node) for node in journal.iter()
             if node.tag in ('journal-title','abbrev-journal-title')]
    licenses = [text_of(node) for node in meta.findall("permissions/license")]
    license_urls = sorted({n.attrib["{http://www.w3.org/1999/xlink}href"]
                          for license_node in meta.findall("permissions/license")
                          for n in license_node.iter()
                          if "{http://www.w3.org/1999/xlink}href" in n.attrib})
    license_text = " ".join(licenses + license_urls)
    permitted, permission_basis = license_eligibility(license_text)
    body = root.find("body")
    research = []
    abstract = research_text(meta.find("abstract"))
    if abstract:
        research.append("Abstract\n" + abstract)
    if body is not None:
        research.append(research_text(body))
    supplement_links = []
    for node in root.iter("supplementary-material"):
        for child in node.iter():
            href = child.attrib.get("{http://www.w3.org/1999/xlink}href")
            if href:
                supplement_links.append(href)
    target = {"title":title,"journal":text_of(journal.find("journal-title-group/journal-title")),
              "journal_aliases":sorted(set(aliases)-{''}),
              "issns":[text_of(x) for x in journal.findall("issn")],"ids":ids,"authors":authors,
              "license_text":license_text,"license_urls":license_urls,"permitted":permitted,
              "permission_basis":permission_basis,
              "supplement_links":supplement_links}
    masked = mask_text("\n\n".join(research), target)
    return target, masked

def mask_text(text, target):
    # Do not strip an ordinary biomedical word just because a surname matches it.
    secrets = [target.get("title", ""), target.get("journal", "")]
    secrets += target.get('journal_aliases',[])
    secrets += [v for k,v in target.get("ids", {}).items() if k in ("doi", "pmid", "pmc", "publisher-id") and len(v) > 4]
    secrets += [a for a in target.get("authors", []) if len(a.split()) > 1]
    for secret in sorted(set(secrets), key=len, reverse=True):
        if secret:
            text = re.sub(re.escape(secret), "[masked publication metadata]", text, flags=re.I)
    text = re.sub(r"https?://\S+|\b10\.\d{4,9}/\S+|\bPM(?:ID|CID)\s*[:=]?\s*\w+", "[masked identifier]", text, flags=re.I)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[masked contact]", text)
    return text

def fingerprint(text):
    tokens = re.findall(r"[a-z]{3,}", text.lower())
    shingles = {" ".join(tokens[i:i+7]) for i in range(max(0,len(tokens)-6))}
    return shingles

def near_duplicate(a, b, threshold=.65):
    if not a or not b:
        return False
    return len(a & b) / min(len(a),len(b)) >= threshold

def prepare(output, seed=20261002, date="2026-10-02", development=10, holdout=5, reserves=3):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    frozen = output / "manifest.json"
    if frozen.exists():
        existing = json.loads(frozen.read_text(encoding="utf-8"))
        if existing["seed"] != seed or existing["as_of"] != date:
            raise ValueError("Existing frozen corpus configuration differs")
        # Never overwrite amended frozen allocation from an old acquisition checkpoint.
        return existing
    state_path = output / "manifest.in-progress.json"
    state = json.loads(state_path.read_text(encoding="utf-8")) if state_path.exists() else {"seed":seed,"as_of":date,"cases":[],"acquisition_failures":[],"queries":[],"status":"acquiring"}
    if state["seed"] != seed:
        raise ValueError("Existing corpus seed differs")
    seen = {c["pmcid"] for c in state["cases"]}
    rng = random.Random(seed)
    hashes = []
    for c in state["cases"]:
        packet = output / c["case_id"] / "masked.txt"
        if packet.exists():
            hashes.append(fingerprint(packet.read_text(encoding="utf-8")))
    def save():
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    for stratum, query in STRATA.items():
        existing = [c for c in state["cases"] if c["stratum"] == stratum]
        needed = development + holdout + reserves
        if len(existing) >= needed:
            continue
        full_query = f'({query}) AND OPEN_ACCESS:y AND IN_EPMC:y AND FIRST_PDATE:[2024-01-01 TO {date}]'
        found, url = search(full_query, size=100)
        state["queries"].append({"stratum":stratum,"url":url,"checked_at":stamp(),"hit_count":found.get("hitCount"),"limit":100})
        items = found.get("resultList",{}).get("result",[])
        rng.shuffle(items)
        for item in items:
            if len(existing) >= needed:
                break
            pmcid = item.get("pmcid")
            if not pmcid or pmcid in seen:
                continue
            try:
                xml = get(BASE + pmcid + "/fullTextXML")
                target, masked = parse_article(xml)
                if not target["permitted"] or len(masked) < 2500:
                    continue
                attach_journal_identity(target,item,pmcid,url,stamp())
                fp = fingerprint(masked)
                if any(near_duplicate(fp, old) for old in hashes):
                    continue
                title = target["journal"].casefold()
                split = "development" if sum(c["split"] == "development" for c in existing) < development else ("holdout" if sum(c["split"] == "holdout" for c in existing) < holdout else "reserve")
                cap = 5 if split == "development" else 3
                if split != "reserve" and sum(c["journal_key"] == title and c["split"] == split for c in state["cases"]) >= cap:
                    continue
                case_id = f"s{1 if seed == 20261002 else 2}-{stratum}-{len(existing)+1:03d}"
                folder = output / case_id
                folder.mkdir(exist_ok=True)
                (folder / "source.xml").write_bytes(xml)
                (folder / "answer.json").write_text(json.dumps(target,ensure_ascii=False,indent=2),encoding="utf-8")
                (folder / "masked.txt").write_text(masked,encoding="utf-8")
                case = {"case_id":case_id,"pmcid":pmcid,"stratum":stratum,"split":split,"journal_key":title,
                        "input_hash":hashlib.sha256(masked.encode()).hexdigest(),"license":target["license_text"],
                        "source_url":BASE+pmcid+"/fullTextXML","retrieved_at":stamp(),"classification_status":"query_assigned_pending_fulltext_review",
                        "supplements":"links recorded; not yet inspected" if target["supplement_links"] else "none identified",
                        "jcr":"Not verified（未核到）","scie":"Not verified（未核到）","status":"prepared"}
                state["cases"].append(case)
                existing.append(case)
                seen.add(pmcid)
                hashes.append(fp)
                save()
                print(f"Prepared {case_id} ({split})",flush=True)
                time.sleep(.15)
            except Exception as exc:
                state["acquisition_failures"].append({"pmcid":pmcid,"stratum":stratum,"error":str(exc),"at":stamp()})
                save()
        if sum(c["split"] == "development" for c in existing) < development or sum(c["split"] == "holdout" for c in existing) < holdout:
            save()
            raise RuntimeError(f"Incomplete stratum {stratum}; obtain more pre-generation candidates without inspecting outcomes")
    state["status"] = "input_allocation_frozen"
    state["frozen_at"] = stamp()
    final = output / "manifest.json"
    final.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding="utf-8")
    return state

def extend_reserves(output, stratum, number=3, seed=20261002):
    """Add eligible reserves before generation, without changing any existing split."""
    root=Path(output)
    file=root/"manifest.json"
    original=file.read_bytes()
    state=json.loads(original)
    if stratum not in STRATA or number < 1:
        raise ValueError("A known stratum and positive reserve count are required")
    seen={c['pmcid'] for c in state['cases']}
    hashes=[fingerprint((root/c['case_id']/'masked.txt').read_text(encoding='utf-8')) for c in state['cases']]
    rng=random.Random(seed)
    query=f'({STRATA[stratum]}) AND OPEN_ACCESS:y AND IN_EPMC:y AND FIRST_PDATE:[2024-01-01 TO {state["as_of"]}]'
    cursor='*'
    added=[]
    # Exclude journals already at the required development cap when augmenting for eligibility.
    capped={c['journal_key'] for c in state['cases'] if sum(x['split']=='development' and x['journal_key']==c['journal_key'] for x in state['cases'])>=5}
    for page in range(3):
        found,url=search(query,size=100,cursor=cursor)
        state['queries'].append({'stratum':stratum,'url':url,'checked_at':stamp(),'hit_count':found.get('hitCount'),'limit':100,'purpose':'eligibility_reserve_augmentation','seed':seed})
        items=found.get('resultList',{}).get('result',[])
        rng.shuffle(items)
        for item in items:
            if len(added)>=number:
                break
            pmcid=item.get('pmcid')
            if not pmcid or pmcid in seen:
                continue
            seen.add(pmcid)
            try:
                xml=get(BASE+pmcid+'/fullTextXML')
                target,masked=parse_article(xml)
                if not target['permitted'] or len(masked)<2500 or target['journal'].casefold() in capped:
                    continue
                attach_journal_identity(target,item,pmcid,url,stamp())
                fp=fingerprint(masked)
                if any(near_duplicate(fp,old) for old in hashes):
                    continue
                serial=max(int(c['case_id'].rsplit('-',1)[1]) for c in state['cases'] if c['stratum']==stratum)+1
                case_id=f's{1 if state["seed"]==20261002 else 2}-{stratum}-{serial:03d}'
                folder=root/case_id
                folder.mkdir(exist_ok=False)
                (folder/'source.xml').write_bytes(xml)
                (folder/'answer.json').write_text(json.dumps(target,ensure_ascii=False,indent=2),encoding='utf-8')
                (folder/'masked.txt').write_text(masked,encoding='utf-8')
                case={'case_id':case_id,'pmcid':pmcid,'stratum':stratum,'split':'reserve','journal_key':target['journal'].casefold(),
                      'input_hash':hashlib.sha256(masked.encode()).hexdigest(),'license':target['license_text'],
                      'source_url':BASE+pmcid+'/fullTextXML','retrieved_at':stamp(),'classification_status':'query_assigned_pending_fulltext_review',
                      'supplements':'links recorded; not yet inspected' if target['supplement_links'] else 'none identified',
                      'jcr':'Not verified（未核到）','scie':'Not verified（未核到）','status':'prepared','augmentation_seed':seed}
                state['cases'].append(case)
                hashes.append(fp)
                added.append(case_id)
                print('Added unevaluated reserve '+case_id,flush=True)
            except Exception as exc:
                state['acquisition_failures'].append({'pmcid':pmcid,'stratum':stratum,'error':str(exc),'at':stamp()})
        if len(added)>=number:
            break
        next_cursor=found.get('nextCursorMark')
        if not next_cursor or next_cursor==cursor:
            break
        cursor=next_cursor
    amendment={'at':stamp(),'reason':'Additional unevaluated same-stratum reserves after license eligibility correction; no scored outcome used.',
               'seed':seed,'added':added,'requested':number,'original_manifest_sha256':hashlib.sha256(original).hexdigest()}
    state.setdefault('reserve_augmentations',[]).append(amendment)
    (root/f'manifest.before-reserves-{stratum}-{seed}.json').write_bytes(original)
    file.write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
    if len(added)<number:
        raise RuntimeError(f'Only {len(added)} of {number} additional reserves acquired; retained actual records')
    return added

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--seed",type=int,default=20261002)
    p.add_argument("--date",default="2026-10-02")
    p.add_argument("--development-per-stratum",type=int,default=10)
    p.add_argument("--holdout-per-stratum",type=int,default=5)
    p.add_argument("--extend-reserves",choices=tuple(STRATA),help="Add unevaluated same-stratum reserves without changing existing allocation")
    p.add_argument("--reserve-count",type=int,default=3)
    args=p.parse_args()
    if args.extend_reserves:
        extend_reserves(args.output,args.extend_reserves,args.reserve_count,args.seed)
    else:
        prepare(args.output,args.seed,args.date,args.development_per_stratum,args.holdout_per_stratum)

if __name__ == "__main__":
    main()
