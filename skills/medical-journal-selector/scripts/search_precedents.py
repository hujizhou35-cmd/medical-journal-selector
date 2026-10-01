#!/usr/bin/env python3
"""Query Europe PMC metadata. No API key; no manuscript upload; no fit scoring."""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def search(query, start, end, limit=30):
    # Explicit publication window; never call these dates submission/acceptance dates.
    combined = f"({query}) AND FIRST_PDATE:[{start} TO {end}]"
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({
        "query": combined, "format": "json", "pageSize": limit, "resultType": "core"})
    checked = datetime.now(timezone.utc).isoformat()
    request = Request(url, headers={"User-Agent": "MedicalJournalSelector/1.0 (public metadata research)"})
    with urlopen(request, timeout=30) as response:
        data = json.load(response)
    articles = []
    for item in data.get("resultList", {}).get("result", []):
        journal = item.get("journalInfo", {}).get("journal", {})
        articles.append({"title": item.get("title"), "doi": item.get("doi"),
                         "pmid": item.get("pmid"), "journal": journal.get("title"),
                         "issn": journal.get("issn"), "eissn": journal.get("essn"),
                         "publication_date": item.get("firstPublicationDate"),
                         "publication_types": item.get("pubTypeList", {}).get("pubType", []),
                         "is_open_access": item.get("isOpenAccess"),
                         "url": "https://europepmc.org/article/" + item.get("source", "MED") + "/" + item.get("id", "")})
    return {"source": "Europe PMC", "source_status": "succeeded", "query": combined,
            "url": url, "checked_at": checked, "hit_count": data.get("hitCount"),
            "returned": len(articles), "articles": articles,
            "limit": "First page only; counts and metadata do not establish methodological fit or acceptance rates."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Non-identifying topic/design terms, not a full manuscript")
    parser.add_argument("--from-date", required=True)
    parser.add_argument("--to-date", required=True)
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("--limit must be 1..100")
    try:
        start = datetime.strptime(args.from_date, "%Y-%m-%d")
        end = datetime.strptime(args.to_date, "%Y-%m-%d")
        if start > end:
            parser.error("from-date must not follow to-date")
        result = search(args.query, args.from_date, args.to_date, args.limit)
        code = 0
    except Exception as exc:
        result = {"source_status": "attempted", "reason": str(exc), "display": "未核到"}
        code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k != "articles"}, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
