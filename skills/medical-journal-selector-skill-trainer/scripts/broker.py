#!/usr/bin/env python3
"""Fetch, filter and capture scholarly/publisher evidence before model exposure."""
from __future__ import annotations
import hashlib
import ipaddress
import json
import re
import socket
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from corpus import get, search, stamp, fingerprint, near_duplicate, DATASET_ACCESSION, TRIAL_REGISTRY
from rate_limit import request_slot

class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hidden=0
        self.parts=[]
        self.links=[]
        self.journal_metadata=[]
    def handle_starttag(self,tag,attrs):
        if tag=='meta':
            attributes=dict(attrs)
            key=(attributes.get('name') or attributes.get('property') or '').casefold()
            if key in ('citation_journal_title','citation_issn','prism.issn','prism.publicationname') and attributes.get('content'):
                self.journal_metadata.append((key,attributes['content']))
        if tag=="a":
            href=dict(attrs).get("href")
            if href:
                self.links.append(href)
        if tag in ("script","style","noscript","svg"):
            self.hidden+=1
        if tag in ("p","div","section","h1","h2","h3","li","tr","br") and not self.hidden:
            self.parts.append("\n")
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript","svg"):
            self.hidden=max(0,self.hidden-1)
    def handle_data(self,data):
        if not self.hidden:
            self.parts.append(data)
    def text(self):
        visible="\n".join(re.sub(r"\s+"," ",line).strip() for line in "".join(self.parts).splitlines() if line.strip())
        metadata='\n'.join(key+' = '+value for key,value in dict(self.journal_metadata).items())
        return visible+('\nSelected explicit journal head metadata:\n'+metadata if metadata else '')

def permitted_url(url):
    parsed=urllib.parse.urlparse(url)
    if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None,443):
        return False
    host=parsed.hostname.lower()
    suffixes=("plos.org","biomedcentral.com","springer.com","springernature.com","frontiersin.org","mdpi.com","wiley.com","elsevier.com","sciencedirect.com","tandfonline.com","sagepub.com","lww.com","bmj.com","oup.com","nature.com","karger.com","thieme.com","liebertpub.com","clarivate.com","nlm.nih.gov","ncbi.nlm.nih.gov","doaj.org","casjournals.cn","cell.com","thelancet.com","aacrjournals.org","asm.org","rsc.org","acs.org","hindawi.com","scipress.com","journalofnursingstudies.com","onlinelibrary.wiley.com","cambridge.org","jstage.jst.go.jp","jsmrm.jp","endocrine.org")
    # Verified publisher/journal hosts exposed by genuine development runs.
    # These allow evidence retrieval, never a recommendation or endorsement.
    suffixes+=("healio.com","fnjn.org","alternative-therapies.com","ovid.com","wolterskluwer.com","haematologica.org",
               "amegroups.org","amegroups.com","jmir.org")
    return any(host==s or host.endswith("."+s) for s in suffixes)

def canonical_url(url):
    parsed=urllib.parse.urlsplit(url)
    pairs=[(k,v) for k,v in urllib.parse.parse_qsl(parsed.query,keep_blank_values=True) if k.lower() not in ("error","code","fbclid","gclid") and not k.lower().startswith("utm_")]
    return urllib.parse.urlunsplit((parsed.scheme,parsed.netloc,parsed.path,urllib.parse.urlencode(pairs),""))

class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,request,fp,code,msg,headers,newurl):
        if not permitted_url(newurl):
            raise ValueError("Redirect leaves the permitted official-source hosts: "+(urllib.parse.urlparse(newurl).hostname or "unknown host"))
        return super().redirect_request(request,fp,code,msg,headers,newurl)

def fetch_page(url):
    opener=urllib.request.build_opener(OfficialRedirect())
    request=urllib.request.Request(url,headers={"User-Agent":"MedicalJournalSelectorResearch/2.0 (+https://github.com/hujizhou35-cmd/medical-journal-selector)"})
    with request_slot(url):
        with opener.open(request,timeout=25) as response:
            mime=response.headers.get_content_type()
            if mime not in ("text/html","application/xhtml+xml","text/plain"):
                raise ValueError("Unsupported policy-page content type: "+mime)
            return response.read(),response.geturl(),mime

def excluded_paper(paper, answer, masked):
    ids={str(v).lower() for v in answer.get("ids",{}).values()}
    for name in ("id","pmid","pmcid","doi"):
        if str(paper.get(name,"")).lower() in ids:
            return True
    title=re.sub(r"\W+"," ",paper.get("title","").lower()).strip()
    target=re.sub(r"\W+"," ",answer.get("title","").lower()).strip()
    if title and target and (title==target or len(set(title.split()) & set(target.split()))/max(1,len(set(target.split())))>.85):
        return True
    abstract=paper.get("abstractText","")
    if abstract and near_duplicate(fingerprint(abstract),fingerprint(masked),.65):
        return True
    return False

def strip_target_mentions(text, answer):
    # Filter complete result/paragraph lines, not merely DOI strings, since
    # nearby journal text could reveal the answer.
    secrets=[answer.get("title","")]+[v for k,v in answer.get("ids",{}).items() if k in ("doi","pmid","pmc")]
    return "\n".join(line for line in text.splitlines() if not any(secret and len(secret)>5 and secret.casefold() in line.casefold() for secret in secrets))

def normalize_journal_ids(papers):
    """Resolve name-only IDs from an unambiguous same-title retrieved record.

    Do not fuzzy-match titles or consult the answer. Multiple known ISSNs for
    a title remain ambiguous here; this does not assume they are print/e-ISSNs.
    """
    known={}
    issn=re.compile(r'^\d{4}-\d{3}[\dXx]$')
    def name(value):return re.sub(r'\W+',' ',value.casefold()).strip()
    for p in papers:
        if issn.fullmatch(p['journal_id']):
            known.setdefault(name(p['journal']),{})[p['journal_id'].upper()]=p
    result=[]
    amendments=[]
    for original in papers:
        p=dict(original)
        if not issn.fullmatch(p['journal_id']):
            matches=known.get(name(p['journal']),{})
            if len(matches)==1:
                jid,evidence=next(iter(matches.items()))
                p['source_journal_id']=p['journal_id']
                p['journal_id']=jid
                amendments.append({'old_id':original['journal_id'],'new_id':jid,
                    'journal':p['journal'],'paper_url':p.get('url'),
                    'identity_basis_url':evidence.get('url'),
                    'basis':'Exact normalized title with one ISSN in the same retrieved pool; no answer used'})
            elif len(matches)>1:
                p['identity_normalization']='Ambiguous same-title ISSNs; no automatic merge'
        result.append(p)
    return result,amendments

def discover(queries, answer, masked, from_date, to_date, output):
    records=[]
    papers={}
    for query in queries[:3]:
        # A query is a short concept combination, never a copied long sentence.
        if len(query.split())>18 or answer.get("title","").casefold() in query.casefold() or any(len(phrase.split())>6 for phrase in re.findall(r'"([^"]+)"',query)) or DATASET_ACCESSION.search(query) or TRIAL_REGISTRY.search(query):
            raise ValueError("Rejected answer-bearing or long manuscript search")
        q=f'({query}) AND FIRST_PDATE:[{from_date} TO {to_date}]'
        data,url=search(q,size=70)
        checked_at=stamp()
        records.append({"url":url,"query":q,"checked_at":checked_at,"hit_count":data.get("hitCount"),"limit":70})
        for p in data.get("resultList",{}).get("result",[]):
            if excluded_paper(p,answer,masked):
                continue
            journal=p.get("journalInfo",{}).get("journal",{})
            name=journal.get("title") or journal.get("medlineAbbreviation")
            if not name:
                continue
            issn=journal.get("issn") or journal.get("essn") or name.casefold()
            key=p.get("doi") or p.get("pmcid") or p.get("id")
            papers[key]={"journal_id":issn,"journal":name,"title":p.get("title",""),
                         "abstract":strip_target_mentions(p.get("abstractText",""),answer),
                         "date":p.get("firstPublicationDate") or p.get("pubYear"),
                         "doi":p.get("doi"),"pmcid":p.get("pmcid"),"id":p.get("id"),"source":p.get("source"),
                         "url":"https://europepmc.org/article/"+p.get("source","MED")+"/"+p.get("id",""),
                         "record_url":url,"checked_at":checked_at,"source_type":"bibliographic",
                         "read_extent":"Bibliographic API title/abstract/metadata; original methods not independently inspected"}
    normalized,amendments=normalize_journal_ids(list(papers.values()))
    result={"records":records,"papers":normalized,"identity_normalization":amendments}
    Path(output).write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    return result

def capture(url,answer):
    captured={"url":url,"checked_at":stamp(),"status":"unverified","text":"","source_type":"official",
              "retrieval_attempt":{"status":"not_attempted"}}
    if any(value and len(value)>5 and value.casefold() in urllib.parse.unquote(url).casefold() for value in answer.get("ids",{}).values()):
        return {"url":"[filtered publication URL]","checked_at":stamp(),"status":"unverified","text":"",
                "failure":"Excluded target-publication source","retrieval_attempt":{"status":"not_attempted","reason":"Excluded target-publication source"}}
    if not permitted_url(url):
        captured["failure"]="URL is not on the permitted official-source host list"
        captured['retrieval_attempt']['reason']=captured['failure']
        return captured
    try:
        captured['retrieval_attempt']['status']='attempted'
        raw,final_url,mime=fetch_page(url)
        captured.update(final_url=final_url,content_type=mime)
        parser=TextHTML()
        parser.feed(raw.decode("utf-8",errors="replace"))
        text=strip_target_mentions(parser.text(),answer)
        captured['read_extent']='Complete extracted visible page text and selected explicit journal title/ISSN head metadata'
        if len(text)<200 or re.search(r"^(Access Denied|Just a moment|403 Forbidden|Checking your browser|Verify you are human)\b",text,re.I|re.M):
            raise ValueError("Page did not provide readable source content")
        # Preserve starts and relevant policy sections; never truncate before
        # extracting a scope sentence simply to satisfy a result.
        if len(text)>40000:
            text=policy_excerpt(text)
            captured['read_extent']='Selected visible page sections and explicit journal title/ISSN head metadata, clipped to 40,000 characters; omitted text was not supplied to the model'
        links=[]
        for href in parser.links:
            absolute=canonical_url(urllib.parse.urljoin(final_url,href))
            if permitted_url(absolute) and not any(v and len(v)>5 and v.casefold() in urllib.parse.unquote(absolute).casefold() for v in answer.get("ids",{}).values()):
                links.append(absolute)
        # Link metadata is not article content. Keep real policy leads even
        # when long journal navigation precedes them in the document.
        captured.update(status="readable_snapshot",text=text,content_hash=hashlib.sha256(raw).hexdigest(),links=list(dict.fromkeys(links)))
        captured['retrieval_attempt']['status']='readable_snapshot'
    except Exception as exc:
        captured["failure"]=str(exc)
        captured['retrieval_attempt'].update(status='unreadable' if captured.get('final_url') else 'failed',reason=str(exc))
    return captured

def policy_excerpt(text,limit=40000):
    """Prioritize admission rules before lengthy topic/navigation matches.

    The result remains an explicitly partial read; it is not evidence that no
    exception exists elsewhere in the page. Retain whole selected lines.
    """
    lines=text.splitlines()
    strong=re.compile(r'methodolog|validation|computational|public data|secondary analy|'
                      r'unsolicited|bibliometric|independent|experimental|'
                      r'(?:do not|will not|cannot|not considered) accept',re.I)
    ordinary=re.compile(r'scope|article type|submission|publication fee|processing charge|'
                        r'impact factor|review time|case report|review article',re.I)
    identity=re.compile(r'\bissn\b|citation_issn|citation_journal_title|prism\.publicationname',re.I)
    selected=set()
    used=0
    def add(indices):
        nonlocal used
        for i in indices:
            size=len(lines[i])+1
            if i not in selected and used+size<=limit:
                selected.add(i)
                used+=size
    add(range(min(15,len(lines))))
    for i,line in enumerate(lines):
        if identity.search(line):add(range(max(0,i-2),min(len(lines),i+4)))
    for pattern in (strong,ordinary):
        for i,line in enumerate(lines):
            if pattern.search(line):
                add(range(max(0,i-2),min(len(lines),i+16)))
    return '\n'.join(lines[i] for i in sorted(selected))

def capture_identity(journal_id):
    """Current Crossref journal metadata, usable only for title/ISSN identity."""
    url='https://api.crossref.org/journals/'+urllib.parse.quote(journal_id,safe='')
    captured={'url':url,'checked_at':stamp(),'status':'unverified','text':'',
              'source_type':'official','source_role':'journal_identity_registry',
              'allowed_fact_fields':['identity'],'links':[]}
    if not re.fullmatch(r'\d{4}-\d{3}[\dXx]',journal_id):
        captured['failure']='No ISSN identifier supplied; registry lookup not attempted'
        return captured
    try:
        raw=get(url,timeout=25,attempts=1)
        response=json.loads(raw)
        data=response.get('message',{})
        ids=data.get('ISSN',[])
        if response.get('status')!='ok' or not data.get('title') or journal_id.upper() not in [v.upper() for v in ids]:
            raise ValueError('Registry response did not resolve the requested title/ISSN')
        fields={key:data[key] for key in ('title','ISSN','publisher') if key in data}
        captured.update(checked_at=stamp(),status='readable_snapshot',
                        text=json.dumps(fields,ensure_ascii=False,indent=2),
                        content_hash=hashlib.sha256(raw).hexdigest(),
                        read_extent='Selected title/ISSN/publisher fields from the current Crossref journal endpoint; identity evidence only')
    except Exception as exc:
        captured['failure']=str(exc)
    return captured

def link_targets(url, article_type=''):
    """Classify genuine URL leads, never the facts established by their pages."""
    parsed=urllib.parse.urlparse(url)
    route=urllib.parse.unquote(parsed.path+('?'+parsed.query if parsed.query else '')).casefold()
    host=(parsed.hostname or '').casefold()
    targets=set()
    if re.search(r'aims|scope',route):targets.add('scope')
    if re.search(r'content[-_]?types|article[-_]?types|case[-_]?reports?|systematic[-_]?reviews?|review[-_]?articles?|/(?:research(?:[-_]articles?)?|original[-_](?:research|investigations?))(?:/|$)|methodolog',route):
        targets.add('article_type')
    general_policy=bool(re.search(r'editorial[-_]?polic|submission[-_]?(guide|guideline)|author[-_]?(guide|instruction)|publishing[-_]?(polic|ethic)|policies-and-publication-ethics|submission-checklist',route))
    specific_method=bool(re.search(r'data[-_]?(?:access|polic|sharing|availability)|public[-_]data|secondary[-_]analy|validation|statistic|reporting[-_]?guidelines?|clinical[-_]?trials?|research[-_]?ethics|computational[-_]research|network[-_]pharmacolog',route))
    if general_policy or specific_method:targets.add('method_policy')
    if general_policy:targets.add('article_type')
    if re.search(r'journal[-_]?metrics|impact[-_]?factor|journal[-_]?insights|citation[-_]?metrics|/metrics(?:/|$)',route):
        targets.add('journal_metrics')
    if host.startswith('jcr.') or re.search(r'(?:^|[/_?=&-])jcr(?:$|[/_?=&-])|journal[-_]?citation[-_]?reports?',route):
        targets.update(('jcr','journal_metrics'))
    if host.startswith('mjl.') or re.search(r'indexing|abstracting|indexed|nlmcatalog|journal[-_]?catalog|master[-_]?journal[-_]?list',route) or host=='doaj.org' or host.endswith('.doaj.org'):
        targets.add('indexing')
    if re.search(r'open[-_]?access|/oa(?:/|$)',route):targets.add('open_access')
    if re.search(r'processing[-_]?charges?|publication[-_]?(?:fees?|charges?)|publishing[-_]?(?:fees?|charges?)|/fees?(?:/|$)|/(?:apc|charges?)(?:/|$)',route):
        targets.add('fees')
    # A journal About page is a broad metrics/indexing/OA/fee lead, not proof
    # that any particular field (or JCR category) is actually present.
    if re.search(r'/about(?:[-_/]|$)',route):targets.update(('journal_metrics','indexing','open_access','fees'))
    applicable=False
    if re.search(r'case',article_type,re.I):
        applicable=bool(re.search(r'case[-_]?reports?',route))
    elif re.search(r'review|meta.?analys',article_type,re.I):
        applicable=bool(re.search(r'systematic[-_]?reviews?|review[-_]?articles?',route))
    elif re.search(r'methodolog',article_type,re.I):
        applicable=bool(re.search(r'methodolog',route))
    else:
        applicable=bool(re.search(r'/(?:research(?:[-_]articles?)?|original[-_](?:research|investigations?))(?:/|$)',route))
    critical=applicable or specific_method
    priority=0 if critical else (1 if general_policy else (2 if targets & {'scope','article_type'} and not re.search(r'methodolog',route) else 3))
    return sorted(targets),critical,priority

def journal_link_group(url):
    parsed=urllib.parse.urlparse(url)
    match=re.search(r'/(?:journal|journals)/[^/]+',parsed.path,re.I)
    return parsed.netloc.casefold()+(match.group(0).casefold() if match else parsed.path)

def plan_followed_links(records, initial_urls, answer, article_type='', source_journals=(), limit=12):
    """Balance real captured links while protecting specific admission/method leads."""
    associations={}
    for journal in source_journals:
        for url in journal.get('official_urls',[]):
            associations.setdefault(canonical_url(url),set()).add(journal['journal_id'])
    already={canonical_url(u) for u in initial_urls}
    already.update(canonical_url(p['final_url']) for p in records if p.get('final_url'))
    candidates={}
    for page in records:
        groups=associations.get(canonical_url(page.get('url','')),set())
        for original in page.get('links',[]):
            url=canonical_url(original)
            path=urllib.parse.urlparse(url).path
            if (url in already or not permitted_url(url) or re.search(r'\.(pdf|docx?|xlsx?|zip)$',path,re.I)
                    or any(v and len(v)>5 and v.casefold() in urllib.parse.unquote(url).casefold() for v in answer.get('ids',{}).values())):
                continue
            targets,critical,priority=link_targets(url,article_type)
            if not targets:continue
            # Journal navigation can link to unrelated journals' submission
            # types. Prefer the originating journal's concrete policy lead.
            parent_url=page.get('final_url') or page.get('url',url)
            if (re.search(r'/(?:journal|journals)/[^/]+',urllib.parse.urlparse(parent_url).path,re.I)
                    and re.search(r'/(?:journal|journals)/[^/]+',path,re.I)
                    and journal_link_group(url)!=journal_link_group(parent_url)):
                priority+=2
            lead=candidates.setdefault(url,{'url':url,'lead_categories':targets,'critical':critical,'priority':priority,'groups':set(),'lead_for_journal_ids':set()})
            lead['groups'].update(groups or {journal_link_group(page.get('final_url') or page.get('url',url))})
            lead['lead_for_journal_ids'].update(groups)
    selected=[]
    counts={}
    def take(pool,number):
        available=[p for p in pool if p not in selected]
        for _ in range(min(number,len(available))):
            lead=min(available,key=lambda p:(max((counts.get(g,0) for g in p['groups']),default=0),p['priority'],p['url']))
            selected.append(lead)
            available.remove(lead)
            for group in lead['groups']:counts[group]=counts.get(group,0)+1
    leads=list(candidates.values())
    critical=[p for p in leads if p['critical']]
    take(critical,limit)
    # Up to four supplemental dossiers compete only after all specific
    # admission/method leads fit. Unused reservations return to policy links.
    optional_categories=({'jcr','journal_metrics'},{'indexing'},{'open_access'},{'fees'})
    general=[p for p in leads if not p['critical'] and set(p['lead_categories']) & {'scope','article_type','method_policy'}]
    optional=[p for p in leads if set(p['lead_categories']) & set().union(*optional_categories)]
    reservation=min(4,len(optional),max(0,limit-len(selected)))
    take(general,max(0,limit-len(selected)-reservation))
    for category in optional_categories:
        if len(selected)>=limit:break
        # One broad About page can serve several lead categories without
        # consuming several endpoint slots.
        if any(set(p['lead_categories']) & category for p in selected):continue
        take([p for p in optional if set(p['lead_categories']) & category],1)
    take(general,limit-len(selected))
    take(optional,limit-len(selected))
    return selected,leads

def retrieval_coverage(records, planned_targets):
    categories=('identity','scope','article_type','method_policy','journal_metrics','jcr','indexing','open_access','fees')
    result={}
    for category in categories:
        pages=[p for p in records if category in p.get('lead_categories',[])]
        states=[p['retrieval_attempt']['status'] for p in pages]
        planned=sum(category in targets for targets in planned_targets)
        attempted=sum(s!='not_attempted' for s in states)
        readable=states.count('readable_snapshot')
        result[category]={'status':'readable_snapshot_available' if readable else ('attempted_without_readable_snapshot' if attempted else 'not_attempted'),
                          'planned_lead_count':planned,'selected_page_count':len(pages),'attempted_count':attempted,
                          'readable_snapshot_count':readable,'failed_count':states.count('failed'),'unreadable_count':states.count('unreadable'),
                          'not_attempted_count':max(0,planned-attempted)}
        if not attempted:
            result[category]['reason']='no_matching_official_lead' if not planned else ('endpoint_budget' if not pages else 'blocked_before_request')
    return {'interpretation':'Lead categories and actual retrieval attempts only. Readable snapshots do not verify identity, JCR, indexing or any other fact; a broad About lead does not establish field presence.',
            'endpoint_ceiling':30,'followed_endpoint_ceiling':12,'captured_record_count':len(records),'categories':result}

def capture_all(urls, answer, output, article_type='', identity_journals=()):
    # Identity requests occupy initial-source slots, rather than expanding the
    # 18 initial + 12 followed endpoint ceiling. Only discovered IDs are passed.
    identities=list(dict.fromkeys(j['journal_id'] for j in identity_journals))[:6]
    planned_urls=list(dict.fromkeys(canonical_url(u) for u in urls))
    urls=planned_urls[:18-len(identities)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(lambda u:capture(u,answer),urls))
    for index,jid in enumerate(identities):
        if index:time.sleep(.5)
        records.append(capture_identity(jid))
    # Only genuine links from captured official pages are followed. Specific
    # applicable admission/method pages precede optional metrics and fees.
    follow,leads=plan_followed_links(records,urls,answer,article_type,identity_journals,min(12,30-len(records)))
    for page,url in zip(records[:len(urls)],urls):
        page['lead_categories']=link_targets(url,article_type)[0]
    for page in records[len(urls):]:page['lead_categories']=['identity']
    with ThreadPoolExecutor(max_workers=3) as pool:
        additional=list(pool.map(lambda lead:capture(lead['url'],answer),follow))
    for page,lead in zip(additional,follow):
        page["retrieval_round"]=2
        page['lead_categories']=lead['lead_categories']
        page['lead_for_journal_ids']=sorted(lead['lead_for_journal_ids'])
    records+=additional
    for page in records:
        if 'retrieval_attempt' not in page:
            failure=page.get('failure','')
            state='readable_snapshot' if page.get('status')=='readable_snapshot' else ('not_attempted' if 'not attempted' in failure.casefold() else 'failed')
            page['retrieval_attempt']={'status':state}
            if failure:page['retrieval_attempt']['reason']=failure
    planned=[link_targets(u,article_type)[0] for u in planned_urls]+[['identity'] for _ in identities]+[p['lead_categories'] for p in leads]
    coverage=retrieval_coverage(records,planned)
    if records:records[0]['retrieval_attempt_coverage']=coverage
    Path(output).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
    Path(output).with_suffix('.retrieval.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2),encoding='utf-8')
    return records
