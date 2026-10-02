# V2 evaluation

[简体中文](README.zh-CN.md) · [Trainer guide](../trainer-guide.md) · [Parallel plan](parallel-execution-plan.md) · [Candidate validation](../validation-v2.md)

**Status: workflow validation and development are in progress. There is no final V2 accuracy result or stable V2 release.**

## Registered experiment

Stage one requires 100 distinct development cases and 50 untouched final cases, stratified into ten primary article classes. Class follows the main research objective; secondary methods remain labels. Compare fixed keyword and TF-IDF abstract baselines, frozen V1, and frozen V2. One authorized failed-gate extension may add 100 development and 50 new final cases.

Assess **current journal fit for a hypothetical original, never-submitted, unpublished manuscript**. Published final articles provide study content only. Their publication history alone is not an exclusion; substantive originality, article-type, methods, ethics and current policy requirements still apply. The final text may contain revisions, and model memory of public papers cannot be ruled out.

Generation and two AI reviewer contexts receive masked research content and controlled source snapshots. Recommendations and reviews are sealed before answers are revealed. All final cases must be sealed before any final answer is revealed. Reviewers are separate contexts of the same model, not medical experts or independent-model validation.

## Preserved protocol trials

**Seventeen distinct protocol trials are retained outside the required 100.** Eleven exposed preparation defects: missing answer identity, nested publication metadata, deleted research link labels, missing scientific declarations and editorial clues. Five subsequent completed pilots and one interrupted pilot exposed an ambiguous published-final task definition. One reviewer adjudication excluded the only fit because the evaluation source was already published. The scenario was corrected uniformly across all six cases, irrespective of performance, and same-stratum reserves restored the 100/50 allocation.

[Protocol trials](protocol-trials.json) retain original negative recommendations, source-classification errors, review disagreements, partial executions, adopted lessons and actual model receipts. Corrected regressions do not overwrite those scores or increase distinct-case counts. [Formal records and release gates](results.json) report the fresh campaign separately.

Six unevaluated license-ineligible records and four records with unresolved answer identity were excluded before recommendation generation. Active input licenses, extraction hashes, study-family similarity and journal identity caps were checked again; no active near-duplicate pair or cap violation was found. Replacements still pass full-text primary-class eligibility before selection.

## Parallel execution

Ten class queues feed waves with at most one manuscript per class. Case directories and model contexts are independent. A wave uses one frozen protocol and Skill snapshot; central decisions happen only after its workers finish. Default ceilings are ten cases and ten simultaneous model calls. Reporting groups of twenty do not change that decision barrier. Failed workers retain their receipts and remain incomplete.

The authenticated infrastructure smoke completed ten small requests in ten unique contexts without a connection failure, in about 101 seconds. This is not a manuscript-case result. Real cases start at lower concurrency before moving to five and ten. Retrieval uses shared request-entry-host pacing; redirect behavior and the existing source-count limits remain documented limitations.

## Evidence and interpretation

Published-outlet discovery and Hit@3/5/10 are separate from today's usable recommendations. Unknown JCR/SCIE data remains unverified. Similar papers do not prove current article admission. Journal identities, scope quotations, method policy and every changing field are checked against the captured sources; Crossref journal metadata supports identity only.

Preparation supplies shared profiles, candidate literature and sources for the paired V1/V2 comparison. It measures recommendation decisions on shared inputs, rather than different autonomous searches. Supplement links are recorded; uninspected supplementary content and figure pixels remain explicit evidence limits. The OA convenience sample is stratified but does not represent all medical submissions.

Reports give numerators, denominators, failures, missingness, by-class results, Wilson intervals, paired wins/ties/losses, usable coverage and observed resource use. Model-labelled verified fields are not automatically source-correct. Missing usage is unknown rather than zero; summed call durations include concurrent reviews and differ from wall time. Raw manuscripts, answer maps and full logs stay outside public bundles. Journal hits and published precedents never become acceptance probabilities.

Release requires complete 100/50 records, zero unresolved final V2 hard failures, paired wins at least losses, usable coverage at least V1, and observed behavior/language/package/install checks. No significant-improvement claim follows from those gates alone.
