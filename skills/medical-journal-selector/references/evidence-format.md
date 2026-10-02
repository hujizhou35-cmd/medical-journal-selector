# Evidence format (schema_version 1.0)

Use this format when machine-readable output or the helper is available. Otherwise deliver the same evidence in readable form. The helper validates declared evidence; it does not fetch or establish the truth of a source. Fabricated timestamps/URLs never count as verification.

## Root

```json
{
  "schema_version": "1.0",
  "run": {"mode": "live", "web_available": true, "started_at": "ISO timestamp", "completed_at": "ISO timestamp"},
  "profile": {"summary": "manuscript summary", "article_types": [], "methods": [], "validation": "actual independence", "queries": [], "limitations": []},
  "constraints": {"time_endpoint": "acceptance"},
  "journals": []
}
```

All timestamps include timezone. Record actual start/end/check times. `offline_fixture` explicitly labels fictional automated-test data, never a real recommendation. Offline operation (`web_available: false`) yields no rankings, even if journals were previously known.

Optional `run.report_language` is `en` or `zh-CN`, selected from the user's explicit request or conversation language. Existing 1.0 records without this field remain readable and preserve the helper's legacy Chinese rendering. `--language en` or `--language zh-CN` overrides rendering only; it does not translate manuscript-specific evidence prose, which the host must write in the requested language. Official source quotations remain in their original language. English unknown fields say `Not verified（未核到）`.

Supported hard constraints: `jcr_quartiles` (Q1–Q4 list), `jcr_category` (exact category), optional `jcr_year`, `scie_only`, `oa_required`, `max_fee` (`amount`, `currency`), `exclude_issns`, `exclude_warnings` with `warning_lists` (named list+year identifiers). `time_endpoint` is first_decision/acceptance/online/indexing. Omitted limits mean no hard limit. Do not encode preferences as hard constraints. Do not silently omit a user's condition the helper cannot represent: apply it manually and record the excluded/pending result before automated ranking, or deliver a manual report.

## Fact envelope

Verified:

```json
{"status":"verified","value":"field-specific value","evidence":[{"url":"https://official.example/journal","source_type":"official","checked_at":"actual ISO timestamp","support":"Short supporting text or precise section/table location"}]}
```

Unverified:

```json
{"status":"unverified","value":null,"reason":"Official page could not be read; 未核到","evidence":[]}
```

Use `bibliographic` for a paper/identifier record; journal policy/metrics require the appropriate authority. `third_party` may document an unresolved lead, never a verified critical field. Preserve failed-source URLs and reasons when useful. A support excerpt should not repeat the full scope quote in the human report; use a section locator to respect aggregate quotation limits.

## Journal

- `id`: stable local ID; `title`: official title; `ranking_category`: relevant JCR category or 未核到.
- `assessment`: `scope_fit` and `method_fit` (strong/moderate/weak), a manuscript-specific `reason`, and `limitations` list. These are explicit qualitative judgments, not observed probabilities.
- `facts`: ALL of the following envelopes, including unverified envelopes for missing fields.

| Field | Verified value |
|---|---|
| identity | `{ "issns": ["valid ISSN"] }` |
| scope | `{ "quote": "short exact quote", "fit_explanation": "specific connection; mark excerpts" }` |
| article_type | `{ "allowed": true, "notes": "official type and applicability" }` |
| method_policy | `{ "allowed": true, "notes": "current applicable rules, and what was checked" }` |
| indexing | `{ "collections": ["MEDLINE"], "wos_checked": false }`; only set wos_checked true after authoritative WoS collection verification; partial indexing evidence cannot prove SCIE absence |
| jcr | `{ "year": 2025, "categories": [{"name": "category", "quartile": "Q2"}] }` — example structure, not current data |
| jif | `{ "year": 2025, "number": 1.2 }` — example structure only |
| oa | `gold`, `hybrid`, `subscription`, `diamond` |
| fees | `{ "amount": 100, "currency": "USD", "option": "oa", "total_known": false, "notes": "article/option/tax/other charges/discounts" }` — set total_known true only when the applicable total is documented; no fee inference from OA mode |
| warnings | `{ "flags": [], "checked_lists": ["authority/list/year"], "coverage_note": "what was checked and not checked" }`; never claim universal safety |

- `timelines`: envelopes for ALL four endpoints: `first_decision`, `acceptance`, `online`, `indexing`. Verified values have `days`, `statistic` (mean/median), `start_event` (submission/acceptance), `cohort`, `period`, and boolean `ranking_usable`. Match source definitions exactly. Unknown definition components are `未核到`; in that case set `ranking_usable: false`. Only set it true after checking current applicability and the complete endpoint definition. Historical or superseded statistics remain visible but cannot rank current speed. The time route groups differing definitions/periods; missing target endpoint does not inherit first-decision time.
- `precedents`: zero or more fact envelopes. Each verified value includes `title`, `date`, `date_kind` (publication/acceptance/submission), `url`, `similarity`, `difference`. Empty list displays 未核到. Read beyond metadata before claiming methodological similarity.

## Commands

Run from the installed skill directory with Python 3.10+ (standard library only; Windows may use `py -3`):

```text
python scripts/selector.py evidence.json --report report.md
python scripts/selector.py evidence.json --report report.md --language en
python scripts/search_precedents.py --query "hypertension cohort" --from-date YYYY-MM-DD --to-date YYYY-MM-DD --output precedents.json
```

Only after the user selects a journal:

```text
python scripts/selector.py evidence.json --handoff-journal JOURNAL_ID --handoff-output cover-letter-handoff.json
```

The main report always contains all three routes, pending/excluded candidates and one detailed evidence card per unique journal. An empty route is an honest result. Handoff retains unresolved items and must not be presented as submission-ready merely because a journal was chosen.

High-quartile ranking does not mix JCR years: use the user's accepted year, otherwise only the most recent year actually verified in this pool and disclose older records. This does not prove that the pool contains the latest released edition. Equally assessed candidates may be displayed alphabetically without implying a meaningful difference in fit.
