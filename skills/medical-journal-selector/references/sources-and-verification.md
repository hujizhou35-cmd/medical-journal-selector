# Sources and live verification

## Source order

| Field | Preferred evidence | Common error to prevent |
|---|---|---|
| Identity | Exact journal masthead/publisher record and appropriate journal identity registry; Crossref `/journals/{issn}` can corroborate its recorded title/ISSN pairing | A journal-registry record classified as an ordinary paper citation, or identity metadata used to prove editorial policy or metrics |
| Scope / article type / method restrictions | Exact journal's official scope and author guidelines; applicable publisher policy | Publisher-wide text treated as a journal-specific exception, or old accepted papers overriding new rules |
| Indexing | Clarivate Master Journal List for WoS collections; NLM Catalog for MEDLINE; named database's own record | PubMed, PMC, MEDLINE and SCIE treated as synonyms |
| JCR/JIF | Current accessible JCR record; alternatively official publisher reporting an explicitly named JCR category/year or JIF/year | Unspecified year, promotional “real-time IF”, or SJR quartile presented as JCR |
| Timeline | Journal/publisher statistics defining start/end, cohort, period, mean/median | Author anecdotes or first-decision numbers treated as acceptance time |
| OA/fees | Journal's current publishing/fee page for the actual article and publishing option | Hybrid optional APC treated as mandatory; absent fee treated as zero |
| Warnings | Original named institution/list and year; official WoS/JCR/publisher notices for their own statuses | No search hit or access failure treated as no risk |
| Precedents | PubMed/Europe PMC metadata and original article; Crossref DOI/identity checks | Search rank, indexing date or keyword count treated as editorial acceptance evidence |

Useful entry points (discover the journal-specific record at run time):

- https://pubmed.ncbi.nlm.nih.gov/
- https://europepmc.org/ and https://www.ebi.ac.uk/europepmc/webservices/rest/search
- https://www.ncbi.nlm.nih.gov/nlmcatalog/
- https://mjl.clarivate.com/
- https://jcr.clarivate.com/
- https://api.crossref.org/
- https://doaj.org/ (OA directory evidence; not a substitute for current fee policy)

A paid JCR subscription is not assumed. Third-party aggregators may locate leads, but unconfirmed critical fields remain 未核到. Do not bypass paywalls, account limits, CAPTCHAs or access controls. Institution-specific acceptance of a category/year/list is the user's rule, not something to guess. CAS and other Chinese ranking systems are separate from JCR; V1.0 does not bundle or rely on them.

## Per-field verification

Resolve journal title, ISSN/eISSN and title history first. Read source content; search-result snippets are discovery only. Record an exact short supporting excerpt or precise table/section location. Mark `verified` only when the actual retrieved content supports the value, year, journal and applicable conditions. On a redirect, record the resolved URL.

Distinguish a registry's own journal record from an article's DOI metadata. A current, actually retrieved Crossref `/journals/{issn}` record may support its stated title/ISSN pairing as identity-only primary registry evidence (`source_type: official`). Crossref article records and abstract search records are `bibliographic`. Neither proves current title history, submission permission, indexing, JCR/JIF, fees or timelines. Preserve supplied field restrictions and source classifications when serializing evidence; do not promote all records from the same domain.

Use an ISO 8601 checked-at timestamp with timezone within the current run. A source's statistics year can be older than the run: report it, never relabel it as this year's data. A field without a required metric year is unverified. Reuse a fetch within the same run, not across runs. In a long run crossing a date boundary, retain actual timestamps rather than forcing one date.

If two sources conflict, check authority, year, category, ISSN and article/fee option. Prefer a clearly applicable authoritative source and explain material differences. If still unresolved, leave value null, status `unverified`, display 未核到, and preserve both references with a conflict reason. Never average conflicting fees or choose the highest quartile.

## Speed and fees

Record time endpoints separately: submission→first decision, submission→acceptance, acceptance→online, submission→online, and indexing if available. Accepted-only cohorts exclude rejected manuscripts. Compare like definitions; do not add medians, estimate an indexing delay or promise a graduation deadline. Self-computed timings from a disclosed sample must be labelled estimates with sample definition and never masquerade as publisher statistics; V1.0 automated speed ranking only uses comparable official metrics.

Match the endpoint named by the source. A statistic labelled acceptance→publication does not establish acceptance→online unless an authoritative source explicitly resolves that meaning. Otherwise keep the publication statistic, its period and definition in notes, and mark the online envelope unverified. A caveat or `ranking_usable: false` cannot repair a `verified` envelope whose endpoint is unsupported. Genuine evidence for an explicitly defined online endpoint remains usable subject to the other timing checks.

Record OA model and payment option separately. Costs include amount, currency, tax treatment if stated, article type, optional/mandatory status, page/color charges, and waiver/discount conditions. A budget hard filter requires the applicable payable total or an explicitly documented no-fee route. Currency mismatch requires a newly verified conversion or manual review; the helper deliberately does not guess exchange rates.

## Warning coverage

Record separately: appearance on a named warning list, current indexing removal/on-hold notice, JIF suppression, publisher policy concern, and ordinary uncertainty. A past warning stays dated; it does not prove current delisting. ESCI is a collection, not itself misconduct. A user's hard exclusion of warnings requires the named list coverage to be checked. If that coverage is absent, classify as pending.

## No web / blocked web

Attempt the official source and one appropriate alternate authoritative route. After at most two additional overall research rounds, preserve failures. Without web access, provide the manuscript profile, needed questions and reproducible queries only. A known-looking journal name does not authorize filling its numbers from memory.
