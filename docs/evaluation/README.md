# V2 evaluation

[简体中文](README.zh-CN.md) · [Trainer guide](../trainer-guide.md) · [Parallel plan](parallel-execution-plan.md) · [Candidate validation](../validation-v2.md)

**Status: workflow validation and development are in progress. There is no final V2 accuracy result or stable V2 release.**

Thirteen distinct valid development loops have passed central decisions; no final case has been evaluated. The first ten-class wave remains recorded as failed: seven chains reached diagnosis, one used notice-only material and is invalid, and the other six have now passed central decisions. Three chains failed before selection. Original sealed reports had usable candidates in 7/13 cases and matched the published outlet in 2/13; repaired outputs do not replace those scores. These development checks do not establish V2 accuracy or improvement over V1.

## Registered experiment

Stage one requires 100 distinct development cases and 50 untouched final cases, stratified into ten primary article classes. Class follows the main research objective; secondary methods remain labels. Compare fixed keyword and TF-IDF abstract baselines, frozen V1, and frozen V2. One authorized failed-gate extension may add 100 development and 50 new final cases.

The keyword/BM25 and TF-IDF baselines use the shared LLM-generated profile's keywords and `abstract_summary`, not independent author-supplied keywords or the verbatim author abstract. They are **LLM-assisted discovery comparators**. The completed development cases did not include baseline policy review, so their baseline usable-journal metric is unknown. Final evaluation requires both reviewers to assess all four anonymous results; ranking-only baselines do not claim complete reports.

Assess **current journal fit for a hypothetical original, never-submitted, unpublished manuscript**. Published final articles provide study content only. Their publication history alone is not an exclusion; substantive originality, article-type, methods, ethics and current policy requirements still apply. The final text may contain revisions, and model memory of public papers cannot be ruled out.

Generation and two AI reviewer contexts receive masked research content and controlled source snapshots. Recommendations and reviews are sealed before answers are revealed. All final cases must be sealed before any final answer is revealed. Reviewers are separate contexts of the same model, not medical experts or independent-model validation.

## Preserved protocol trials

**Eighteen distinct protocol trials are retained outside the required 100.** The original seventeen exposed preparation defects and an ambiguous published-final task definition. Their original results remain intact. One additional diagnosed chain used a notice rather than a complete study; it is preserved as a protocol trial instead of receiving development credit.

[Protocol trials](protocol-trials.json) retain original negative recommendations, source-classification errors, review disagreements, partial executions, adopted lessons and actual model receipts. Corrected regressions do not overwrite those scores or increase distinct-case counts. [Formal records and release gates](results.json) report the fresh campaign separately.

The same material-eligibility audit was applied across the corpus, independently of recommendation outcomes. It identified six allocated records that were notices, abstracts, editorials or commentaries rather than complete studies: the scored notice and five pre-selection or unexposed records. Same-class reserves restored the allocation, including replacement of one unseen final abstract before any final model evaluation. Final identifiers remain withheld.

The corrected allocation contains 100 development and 50 final studies, with ten development and five final studies per class. Source genre, extraction, licenses, duplicates and journal identity caps were rechecked; no active near-duplicate pair or cap violation was found. One pre-selection network-labelled study was reassigned to laboratory research by its main objective; its identity and scientific text were retained, with network and docking kept as secondary labels. Earlier license and unresolved-identity exclusions remain preserved. Replacements still require full-text primary-class checks before selection.

## Parallel execution

Ten class queues feed waves with at most one manuscript per class. Case directories and model contexts are independent. A wave uses one frozen protocol and Skill snapshot; central decisions happen only after its workers finish. Default ceilings are ten cases and ten simultaneous model calls. Reporting groups of twenty do not change that decision barrier. Failed workers retain their receipts and remain incomplete.

The terminal ten-class wave used ten workers and a ten-call ceiling. Both the scheduler measurement and actual CLI receipt intervals show a peak of ten. All 45 CLI calls completed transport, but this does not mean 45 successful cases: two chains failed the primary-class check and one profile broke the query-length contract. Of the seven diagnosed chains, one was subsequently invalidated by the uniform material audit. [Execution failures](execution-failures.json) preserve the original failures separately from any resumed outcome.

The earlier ten-request infrastructure smoke and completed two-case and five-case waves remain separate evidence. Retrieval still has host, redirect and source-count limits. [Navigation repair regressions](execution-repairs.json) preserve real acquisition counts and original-score checks, with no new case credit. An inaccurate Scope word-count annotation remains recorded alongside its accurate quotation.

The r21 workflow, including material-eligibility and profile prompt guards, passed 242 synthetic checks. Both real exposed-input replays passed the specified regressions: each had 20 integrity checks, 24 timeline envelopes audited and a negative control on a real hard requirement. [Instruction repair regressions](instruction-repairs.json) retain the sealed audit. The replays reused source snapshots, added zero new blind cases and did not replace original scores or establish an accuracy improvement. The systematic-review replay retained one transport reconnect; disconnected-attempt usage is unknown, so available terminal-token totals are not complete cost. The next ordinary wave has not yet been registered.

[Two preparation renewals](preparation-renewals.json) passed fresh profile requests and 42 file-hash checks. Original failures, profiles and usage are retained; validated new profiles can be resumed in the next ordinary wave. These two preparation calls add no completed-case credit.

## Evidence and interpretation

Published-outlet discovery and Hit@3/5/10 are separate from today's usable recommendations. Unknown JCR/SCIE data remains unverified. Similar papers do not prove current article admission. Journal identities, scope quotations, method policy and every changing field are checked against the captured sources; Crossref journal metadata supports identity only.

Preparation supplies shared profiles, candidate literature and sources for the paired V1/V2 comparison. It measures recommendation decisions on shared inputs, rather than different autonomous searches. Supplement links are recorded; uninspected supplementary content and figure pixels remain explicit evidence limits. The OA convenience sample is stratified but does not represent all medical submissions.

The final-review implementation now gives both reviewers four anonymous cards with independent presentation orders and all six pairwise judgments. Baselines keep their original ranking and acquire no invented fact envelopes; their policy fit is assessed independently against shared sources. The V1/V2 pair is extracted through the private map. These guards passed synthetic tests; no real final case has run. Shared preparation cost is separate from each comparator's additional model calls. The two representative papers per journal do not always include its highest-scoring support paper for both baselines; that limits how completely a reviewer can inspect the ranking evidence.

New protocol snapshots seal the baseline lists, shared preparation files and source hashes before the first recommendation request. Final reveal additionally verifies those seals for all 50 cases. Existing r19 development records retain their original seal boundary and scores; new preparation manifests must not be added after their execution and described as prior freezing.

Reports give numerators, denominators, failures, missingness, by-class results, Wilson intervals, paired wins/ties/losses, usable coverage and observed resource use. Model-labelled verified fields are not automatically source-correct. Missing usage is unknown rather than zero; summed call durations include concurrent reviews and differ from wall time. Raw manuscripts, answer maps and full logs stay outside public bundles. Journal hits and published precedents never become acceptance probabilities.

Release requires complete 100/50 records, zero unresolved final V2 hard failures, paired wins at least losses, usable coverage at least V1, and observed behavior/language/package/install checks. No significant-improvement claim follows from those gates alone.
