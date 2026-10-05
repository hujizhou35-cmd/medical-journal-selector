#!/usr/bin/env python3
"""Anonymously verify release downloads against the selected public inventory."""
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO='hujizhou35-cmd/medical-journal-selector'

def verify(tag,directory,only=None):
    config=json.loads((ROOT/'development/releases/distribution.json').read_text(encoding='utf-8'))
    expected=config['releases'][tag]['assets']
    if only:
        expected={name:expected[name] for name in only}
    directory=Path(directory).resolve()
    for name,digest in expected.items():
        p=directory/name
        if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=digest:
            raise ValueError('Local hash mismatch: '+name)
    def download(item):
        name,digest=item
        url=f'https://github.com/{REPO}/releases/download/{tag}/{name}'
        for attempt in range(3):
            try:
                req=urllib.request.Request(url,headers={'User-Agent':'medical-journal-selector-public-verification'})
                with urllib.request.urlopen(req,timeout=45) as response:
                    payload=response.read();status=response.status
                observed=hashlib.sha256(payload).hexdigest()
                if observed!=digest or payload!=(directory/name).read_bytes():
                    raise ValueError('Downloaded bytes differ')
                return {'name':name,'sha256':observed,'bytes':len(payload),'status':status,'passed':True}
            except Exception as exc:
                if attempt==2:return {'name':name,'passed':False,'error':type(exc).__name__+': '+str(exc)}
                time.sleep(2)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(download,sorted(expected.items())))
    proof={'tag':tag,'checked_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'anonymous':True,'scope':'selected assets' if only else 'complete curated release inventory','passed':all(x['passed'] for x in records),'assets':records}
    output=directory.parent/(tag+('-selected' if only else '')+'-public-download-proof.json')
    output.write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    return proof

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('tag');parser.add_argument('directory',type=Path)
    parser.add_argument('--only',action='append')
    args=parser.parse_args()
    proof=verify(args.tag,args.directory,args.only)
    print(json.dumps(proof))
    if not proof['passed']:raise SystemExit(1)

if __name__=='__main__':main()
