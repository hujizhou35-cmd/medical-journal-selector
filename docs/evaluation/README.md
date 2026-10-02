# V2 evaluation

[简体中文](README.zh-CN.md) · [Trainer guide](../trainer-guide.md) · [Homepage](../../README.md)

**Status: real workflow pilots are in progress. No final V2 accuracy result or stable V2 release is claimed.**

Workflow pilots exposed preparation defects: missing-ISSN scoring, nested publishing metadata, deleted scientific link labels, and omitted ethics, consent and data-availability statements in back matter. **Eleven protocol-only cases, including interrupted executions, are preserved and excluded from the required 100.** Publication clues are removed while research labels, citation tails, ordinary biomedical terms and essential scientific declarations are retained. Public dataset accessions remain visible; study trial numbers are consistently masked and research-ID answer searches are prohibited. Input hashes and the 100/50 allocation are fixed again after preparation audits. [Preserved protocol trials](protocol-trials.json) and [formal case records and current gate decision](results.json) keep the two counts separate. Six unevaluated license-ineligible records and four unevaluated records with unresolved answer identity were excluded under eligibility rules; same-stratum reserves preserve the allocation. Actual timeouts and interruptions remain recorded; retries retain the 1,800-second ceiling and unchanged model/settings.

The repaired clinical pilot illustrates the distinction: the original outlet was discovered, delivered and assessed, but current admission remained pending, so it did not enter the eligible fit sequence. Its abstract baseline ranked the outlet second. This is a protocol check, not a formal accuracy result or a rule requiring recommendation of that outlet. Original scores and the subsequent reconciliation remain preserved privately.

The first stage requires 100 distinct development cases and 50 untouched final tests. It compares fixed keyword/abstract baselines, original V1 and a frozen V2 candidate. Recommendations and independent AI reviews are sealed before answer reveal. If gates fail, at most one extension adds 100 development papers and 50 new tests.

Published journal matches are reported separately from current recommendation fitness. Missing JCR/SCIE information stays unverified. Reviewers are AI sessions, not medical experts. The corpus is an OA convenience sample with stratification, not a representative sample of all medical submissions.

The paired comparison uses a shared preparation stage for manuscript profiles, retrieved journals and current source snapshots. It tests recommendation decisions on those inputs; it does not measure differences between fully autonomous V1 and V2 searches. Supplement links are recorded, but supplements not inspected remain an explicit method-evidence limit.

The completed report will include actual case counts, failures, by-stratum results, Hit@3/5/10 with uncertainty intervals, usable coverage, evidence errors, paired judgments, rule changes and observed time/usage. Raw papers, answer maps and full logs remain excluded from public packages.

The checkpoint is a development log, not an accuracy estimate. Available token totals do not include unreported usage from incomplete calls; summed model-call durations include parallel reviews and are not the experiment's wall-clock time. Final article identifiers and answers stay private until all final recommendations and reviews are sealed.

`call_outcomes` reports actual call statuses separately from case completion. A successful retry can complete one case while its earlier infrastructure failure remains counted. Unknown usage is not zero usage.

Two independent reviewers flagged one unsupported design-exclusion claim in a real development case. A general manuscript-comparison audit was added and tested with fresh generation and two new reviews; the original error and negative result remain recorded. This regression is not proof of a causal performance gain. `hard_failures` counts retained flags, which can repeat the same error; `hard_failure_cases` counts affected cases. Usage includes actual regression and unfinished-case receipts without increasing completed-case counts.

Field coverage counts come from the original sealed fact and timeline envelopes. They show declared verified, unverified and invalid statuses; they do not replace independent source checks. Repairs do not overwrite these original counts.

The first two formal development cases completed without a usable recommendation. Both negative outcomes are retained. Bounded acquisition regressions repaired official-host coverage, applicable article-type links and current title/ISSN lookup. Six coherent journal dossiers share the unchanged ceiling of eighteen initial and twelve followed endpoints. Crossref journal metadata supports identity only, not admission, indexing or metrics. These acquisition checks do not establish improved recommendation scores; subsequent fresh cases must test that.

Before generation, eight remaining inputs required additional study-registration masking. The amendment preserves registration facts, the 100/50 allocation and both completed inputs. The same query guard covers the added registries. Historical protocol records remain unchanged.
