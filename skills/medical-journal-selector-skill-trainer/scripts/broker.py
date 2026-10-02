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
    captured={"url":url,"checked_at":stamp(),"status":"unverified","text":"","source_type":"official"}
    if any(value and len(value)>5 and value.casefold() in urllib.parse.unquote(url).casefold() for value in answer.get("ids",{}).values()):
        return {"url":"[filtered publication URL]","checked_at":stamp(),"status":"unverified","text":"","failure":"Excluded target-publication source"}
    if not permitted_url(url):
        captured["failure"]="URL is not on the permitted official-source host list"
        return captured
    try:
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
    except Exception as exc:
        captured["failure"]=str(exc)
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

def capture_all(urls, answer, output, article_type='', identity_journals=()):
    # Identity requests occupy initial-source slots, rather than expanding the
    # 18 initial + 12 followed endpoint ceiling. Only discovered IDs are passed.
    identities=list(dict.fromkeys(j['journal_id'] for j in identity_journals))[:6]
    urls=list(dict.fromkeys(urls))[:18-len(identities)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        records=list(pool.map(lambda u:capture(u,answer),urls))
    for index,jid in enumerate(identities):
        if index:time.sleep(.5)
        records.append(capture_identity(jid))
    # Follow policy links actually present in captured official pages, not
    # guessed URL grids. Preserve the total 30-page budget for every variant.
    follow=[]
    already={canonical_url(u) for u in urls}|{canonical_url(p["final_url"]) for p in records if p.get("final_url")}
    policy_path=re.compile(r"aims|scope|content[-_]?types|article[-_]?types|editorial[-_]?polic|submission[-_]?(guide|guideline)|author[-_]?(guide|instruction)|publishing[-_]?(polic|ethic)|methodolog|policies-and-publication-ethics|submission-checklist",re.I)
    for page in records:
        for link in page.get("links",[]):
            if canonical_url(link) not in already and link not in follow and policy_path.search(urllib.parse.urlparse(link).path) and not re.search(r"\.(pdf|docx?|xlsx?|zip)$",urllib.parse.urlparse(link).path,re.I):
                follow.append(link)
    def priority(url):
        path=urllib.parse.urlparse(url).path
        # Applicable admission pages come before generic publishing policies;
        # broad policy indexes must not consume every bounded follow-up slot.
        if re.search(r'case',article_type,re.I) and re.search(r'case[-_]?reports?',path,re.I):return (0,url)
        if re.search(r'review|meta.?analys',article_type,re.I) and re.search(r'systematic[-_]?review|review[-_]?articles?',path,re.I):return (0,url)
        if not re.search(r'case|review|meta.?analys',article_type,re.I) and re.search(r'/(?:research(?:[-_]articles?)?|original[-_](?:research|investigations?))(?:/|$)',path,re.I):return (0,url)
        if re.search(r'policies-and-publication-ethics|editorial[-_]?polic',path,re.I):return (1,url)
        if re.search(r'content[-_]?types|article[-_]?types|aims|scope',path,re.I):return (2,url)
        # Methodology is often a separate submission type. Its page must not
        # crowd out ordinary Research/Original Investigation instructions.
        if re.search(r'methodolog',path,re.I):return (4,url)
        if re.search(r'/journal[s]?/',path,re.I):return (3,url)
        return (5,url)
    follow.sort(key=priority)
    with ThreadPoolExecutor(max_workers=3) as pool:
        additional=list(pool.map(lambda u:capture(u,answer),follow[:min(12,30-len(records))]))
    for page in additional:
        page["retrieval_round"]=2
    records+=additional
    Path(output).write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding="utf-8")
    return records
