# Parallel execution plan

[简体中文](parallel-execution-plan.zh-CN.md) · [Evaluation protocol](README.md)

Independent manuscripts can run together while preserving the evaluation design. Ten logical queues represent the ten primary article classes. Each queue contains ten development cases and five untouched final cases. This is a scheduling change: workers keep their answers and lessons private, and the Skill stays frozen throughout a wave.

The assessment is **current hypothetical unpublished-submission compatibility**. Published final articles supply scientific content. Selection and review assume the same study has never been submitted or published and is not under consideration elsewhere; methods, results and data provenance remain unchanged. The benchmark source's publication alone cannot disqualify a journal. Real article-type, method, data-reuse, novelty, ethics and consent restrictions still apply. Ordinary submission declarations are recorded as conditions. Final-text changes and possible public-paper model memory remain limitations; matches do not estimate acceptance probability.

## What stays serial

- One development case remains an ordered chain: eligibility and masking → profile and discovery → source capture → selection → two blind reviews (and adjudication when needed) → reveal → diagnosis. Its decision is recorded at the wave barrier.
- A case is counted only after its diagnosis and an explicit accepted change, rejected change, retrieval repair, or no-change decision are sealed.
- A diagnosed rule change is reviewed at the end of its wave. The next wave receives a newly frozen Skill snapshot; cases already running never receive that change.
- The 50 holdout cases use one frozen candidate. All generations and reviews must be sealed before any answer is revealed.

## What may run in parallel

- Independent case folders may run in the same wave. Each worker receives the same immutable corpus and Skill snapshot, but a fresh model context and a unique case directory.
- The two blind reviewers inside one case may continue to run concurrently. An adjudicator, if required, waits for both reviews.
- Preparation and current-source capture for different cases may overlap, subject to the retrieval host's rate limits.

The default development wave takes **one next unexposed case from each class queue, up to ten cases**. Start with a real two-case smoke wave, then a five-case smoke wave, then ten if receipts, isolation, schemas, recovery and provider behavior are reliable. Those smoke cases use the same registered evaluation and count only when fully completed; they are not extra iterations. Keep queue order fixed and balance later selection so smaller smoke waves do not omit classes.

The **global model-call concurrency cap is ten**, including profile/discovery planning, selections, reviewers, adjudicators and diagnoses. Ten case workers must not start twenty reviewer calls together: every model call uses the shared cap. Use the host's existing model access and registered model/effort. Reduce active calls and wave size after rate limits, timeouts or quota interruption, recording the actual settings and failures. Retrieval concurrency has its own host limits. Never start another wave merely to hide a failed case.

The development set may still appear in five groups of twenty cases for progress reporting. These groups are reporting units only; they do not freeze or change rules. The execution wave and its barrier determine when a new snapshot may be used.

## Checkpoints and files

Each worker writes only to `private/v2-run/<run>/<case-id>/`. The parent process aggregates completed ledgers after workers exit; it does not edit a worker ledger while a model call is active. Failed calls, partial records and quota interruptions remain in their case directory. A retry reuses the same masked input and frozen snapshot and writes a new attempt record. The worker reads a read-only `eval_bundle` containing the corpus hash, Skill hash, evidence-snapshot IDs, source limits, prompt/configuration hash and model/effort; a hash mismatch stops the batch.

At a wave boundary, workers finish or record a visible terminal failure and seal their records. They do not receive lessons from one another. The central coordinator then:

1. inspect every ledger and call receipt;
2. export the public derived result;
3. review diagnoses in a separate context;
4. run any required regression on a fresh case context;
5. accept or reject changes with `record_decision.py`;
6. freeze the next execution snapshot and start the next wave.

No worker may read another worker's answer, lesson, review or private log. The dispatch scheduler reads only status and hashes; a separate authorized evaluation/decision role inspects sealed records after the barrier. Preparation may know outlet identities but must filter target/duplicate evidence before it reaches any generator or reviewer. Per-case reveal is allowed only after that development case's generation and reviews are sealed. Final-set reveal waits for the entire final set.

The central evaluator reports Hit@3/5/10 and MRR separately from current usable-candidate rate, policy/evidence coverage, leakage rate, failure rate and token/time percentiles. A historical outlet match is never treated as an acceptance probability. Raw papers, answer maps and full model logs remain outside the public bundle.

## Failure and stopping rules

An infrastructure or model failure pauses that case and preserves its receipt. It does not consume a completed-case count, and it does not invalidate other completed cases in the same wave. Three repeated failures with the same external cause pause the affected queue for visible diagnosis before retrying. A recorded failure is never relabeled a successful call. A contaminated input or demonstrated protocol defect uses a dated cohort amendment and previously unexposed same-stratum reserves; poor recommendation performance is never replaced. Protocol-trial outputs, original scores and resource receipts remain visible, and exposed-case replays never count as new blind cases.

Each wave uses a registered model/configuration, corpus hash, assessment-target hash, source-limit profile and selector snapshot. A rule change creates a new `eval_version` and is applied only after a registered wave barrier; it is never adapted from one worker's result while other cases in that wave are running. The campaign still requires 100 completed development cases and 50 untouched final cases. Reports include per-wave snapshots, class counts, failures, unresolved records and all observed resource use, as well as the twenty-case progress groups.

## Current implementation status

A parallel scheduler first needs a synthetic dry run demonstrating unique directories, immutable snapshot hashes, no cross-case answer reads and resumable failures. Actual two-case, five-case and ten-case smoke receipts then establish the observed operating limit; documentation and synthetic checks alone do not prove reliable ten-call execution. Earlier cases affected by a recorded protocol defect remain protocol trials with their original outcomes preserved. Report which dry runs and real smoke waves actually completed before claiming parallel compatibility.
