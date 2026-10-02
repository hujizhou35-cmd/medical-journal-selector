---
name: medical-journal-selector-skill-trainer
description: Evaluate and improve the medical-journal-selector Skill with masked published manuscripts, sealed recommendations, current journal evidence, independent AI review, and untouched final tests. Use for journal-selector iteration, benchmarking, or batch evaluation; ordinary manuscript journal selection uses medical-journal-selector.
---

# Medical Journal Selector Skill Trainer v1.0.0

Improve reusable journal-selection decisions, not a single answer. Follow the user's language. This is workflow and instruction development, not model fine-tuning. A journal that published a paper is one known outlet, not the only correct recommendation or an acceptance-probability label.

## Establish the experiment

Record the target Skill snapshot and hash, model and reasoning settings, current-versus-historical evidence mode, sample strata, development/final-test allocation, random seed, tool budget, and release gates before examining results. Preserve the selector's name and its three production routes. Do not alter a production Skill or publish merely because the Trainer was invoked: execute only changes and publication already authorized by the user.

For the project V2 campaign, use 100 distinct development cases and 50 untouched final cases, ten primary article classes, and current policies. At most one failed-gate extension adds 100 development cases and 50 new final cases. Each class has 10 development and 5 final cases per stage. Record additional method labels. Maximum journal representation is five development and three final cases per stage. Verify licenses individually; unavailable JCR/SCIE records remain unknown, not invented sample labels. Read [protocol.md](references/protocol.md).

In current-fit retrospective evaluation, assess the study as hypothetical original, never-submitted and unpublished work under today's policies. The source text is a published final article used to supply study content. Keep these two states explicit in generation, review and diagnosis; the source article's publication history alone must not disqualify every candidate. Substantive method, article-type, ethics and originality requirements still apply.

## Separate inputs and answers

The corpus preparation role may know the answer. The selection generator and recommendation reviewers must not. Give each generation a fresh context containing only the complete frozen target Skill, masked research materials, stated constraints, and filtered current evidence. Do not inherit the development conversation, evaluator lessons, answer map, user memories, or previous responses.

Remove journal headers, exact title, authors, publication identifiers, publication history, journal references in metadata, filenames and supplements. Retain research question, methods, findings and scientific link labels. Preserve public dataset provenance unless the experiment explicitly uses consistent accession pseudonyms; mask study trial registry numbers without erasing registration facts. Group preprints and near duplicates with their study, keeping a study family in one split. Filter target and duplicate publications BEFORE search excerpts reach the generator. Do not search the exact title, distinctive long manuscript passages or study-specific research identifiers for the answer. Keep the true journal eligible for ordinary discovery; never insert it using the answer.

Host-enforced restricted inputs are different from a prompt that merely asks an unrestricted agent not to read answers. Record the actual isolation achieved. With only a shared chat, prepare and explain the protocol but do not claim an auditable blind test. Public-paper model memory and post-review manuscript changes remain limitations even with tool isolation. Read [isolation-and-records.md](references/isolation-and-records.md).

## Complete one development case

1. Check masked inputs, license, split and search exclusions.
2. Generate recommendations in a fresh answer-free context. Use the selector's ordinary profile, three routes, current fact checks and gaps. Keep a separate evaluation-only fit sequence of up to ten supported candidates; do not force ten or change the production three-per-route limit.
3. Seal outputs with hashes and timestamps before review or reveal.
4. Have two separate reviewer contexts inspect source support, scope, article type, methods, user constraints, missing evidence and useful recommendations WITHOUT the answer or version labels. Randomize version presentation. A third reviewer resolves disagreements where the evidence permits; preserve unresolved disagreements.
5. Seal reviews, then reveal the publishing journal and compute discovery and Hit@3/5/10 results. Diagnose non-hits rather than calling them all errors. Current policies may legitimately exclude a historical outlet.
6. Propose only transferable changes supported by observed failures. Record hypothesis, supporting cases, counterexamples, changed rules and regression risks. No change is a valid outcome.
7. Test a changed complete candidate in another fresh generation context, without revealing evaluator prose. Run affected cases and protected methods. Accept or revert with evidence; at most two candidate repairs per case.

Retries, repaired responses and regressions do not increment the distinct-case count. Infrastructure failures, contamination and bad model recommendations have separate statuses. Retain all model failures in reported denominators; do not replace hard cases after seeing results. Missing facts remain 未核到 / Not verified（未核到）. Sources are not verified merely because a URL exists.

For the project parallel campaign, use ten primary-class queues. A wave handles at most one case per class, with a frozen input/protocol/Skill bundle and independent case directories. Default ceilings are ten case workers and ten simultaneous model calls. Start with a smaller real wave before increasing concurrency. Seal and inspect the entire wave before adopting changes; the next wave receives a newly registered snapshot. Reporting groups of twenty do not change the per-wave decision barrier. Never share case answers or review lessons with a still-running generator. A failed worker preserves its records and cannot be counted as complete.

## Final evaluation and promotion

Freeze both the final candidate and original baseline before running the untouched final set. Final execution requires the exact allocated 100 development cases to have genuine completed generation, review, diagnosis and decision records. Compare fixed keyword, fixed TF-IDF abstract similarity, original V1, and candidate V2 with equal data-source/window/tool budgets. The two ranking algorithms are deterministic, but their queries and abstract summary come from shared model-assisted preparation; the abstract baseline does not use the unmasked author abstract. Shared case snapshots preserve actual acquisition times; they are experimental inputs, not a reusable claim of today's facts. Keyword and abstract baselines are discovery/ranking comparators, not complete evidence-audited reports.

Both independent final reviewer contexts inspect all four results under anonymous labels. Randomize each reviewer's presentation order and remove model/Skill/version metadata. Evaluate ranking fit and source support for every comparator; keep full-report completeness separate from what a ranking-only comparator claims. Do not invent baseline facts or copy candidate V2 judgments into its baselines. Record all pairwise judgments and extract the V1/V2 result using the private label map. Adjudicate genuine disagreements and preserve unresolved splits.

Before the first recommendation, seal the fixed rankings and shared preparation files with their actual hashes and completion records. Check those original bindings before generation, review, diagnosis and reveal; never add a seal after those activities began. Seal ALL final-set generations, four-comparator review inputs and blind reviews before aggregate answers are revealed. The reveal/scoring role must validate the whole fifty-case set before reading any final answer; the isolated preparation/exclusion role may know identities to mask and filter them. Once a test's results inform a rule change, it becomes exposed data; new claims require a new untouched final set. Do not repeatedly tune against it.

Report numerator, denominator, failures, missingness, by-stratum results, Hit@k and Wilson intervals, true-journal rank, V2/V1 wins/ties/losses, eligible-candidate coverage, evidence violations, timing and available token usage. AI sessions are not medical experts; same-model judgments are not independent human validation. Neither journal matches nor precedents estimate acceptance probability. Read [review-and-promotion.md](references/review-and-promotion.md).

Project promotion requires complete case records, no unresolved V2 hard failures in final tests, wins at least losses, non-decreasing evidence-supported usable coverage, protected behavior tests, bilingual output, package checks and observed installation compatibility. Do not invent a success threshold or claim a significant gain without statistical evidence. If stage one fails, perform only the authorized one-stage extension. If stage two fails, keep the candidate and truthful results without a stable release.

## Execution and portability

The scripts in `scripts/` assist with corpus preparation, masked packets, hashes, model-run records, fixed baselines and aggregation. Python 3.10+ is required for these helpers. The host supplies its existing model access; no GPT API key is required by this Skill. `runner.py` uses fresh Codex CLI calls for the project campaign, not a transferable API credential.

For another Agent, apply the same workflow using its own isolated contexts and controlled retrieval. If scripting or isolation is unavailable, do not simulate successful automation. Record the limit and perform only the supported manual steps. See [commands.md](references/commands.md).

Keep raw papers, answer maps, credentials and full model logs out of the public repository and release archives. Public reports contain permitted identifiers, derived decisions and concise paraphrased lessons; do not reproduce full papers. Deliver the candidate Skill, case ledger, change ledger, review/metrics report, actual isolation record, final gate decision and one stopping reason.


# Portable edition: inlined references

All references below are included in this file. If a relative reference cannot be opened, read its matching section below. Executable helpers are optional and are shipped only in the full bundles; apply their documented rules manually when unavailable.

---

## Inlined reference: commands.md

# Helper commands

Python 3.10+; standard library only. Start in the editable Trainer folder. Replace the example paths, `YYYY-MM-DD` and case IDs with the registered experiment values. On Windows, use an actual Python 3 interpreter and quote paths containing spaces. Keep the corpus, answers and full logs in an ignored private directory outside release packages.

## Prepare and freeze

```text
python scripts/corpus.py --output /private/run/corpus --date YYYY-MM-DD
python scripts/freeze.py /private/run/selector-v1 --source /path/to/original-v1-source
python scripts/freeze.py /private/run/selector-v2-r1 --source /path/to/candidate-selector
python scripts/freeze.py /private/run/trainer-r1 --source .
python scripts/freeze.py /private/run/selector-v1 --verify
python scripts/freeze.py /private/run/selector-v2-r1 --verify
python scripts/freeze.py /private/run/trainer-r1 --verify
```

Use the original V1 source for the comparator. If its snapshot already exists, verify it rather than freezing or overwriting it again. Freeze the corpus allocation, permission checks, primary classes and duplicate groups before generation. Run the scheduler from the **frozen Trainer's `scripts/parallel_campaign.py`**; it rejects an editable execution script or imported helpers from another folder.

## Ten article-class queues

The scheduler holds ten logical class queues and takes at most one case from a class in each wave. `--case-workers` controls simultaneous case workers; `--model-call-limit` caps all model operations together, including the two reviewers within each case. Defaults are **10 cases and 10 model calls**. Setting ten case workers does not permit twenty simultaneous reviewer calls. No fixed speedup is promised.

Start with a two-case/four-call smoke wave:

```text
python /private/run/trainer-r1/scripts/parallel_campaign.py --corpus /private/run/corpus --runs /private/run/development --trainer-snapshot /private/run/trainer-r1 --selector-skill /private/run/selector-v2-r1 --eval-version dev-smoke-2x4 --date YYYY-MM-DD --limit 2 --case-workers 2 --model-call-limit 4
```

After the wave is sealed and its decisions recorded, register the concurrency change and use a **new epoch name** for five cases/ten calls:

```text
python /private/run/trainer-r1/scripts/parallel_campaign.py --corpus /private/run/corpus --runs /private/run/development --trainer-snapshot /private/run/trainer-r1 --selector-skill /private/run/selector-v2-r1 --eval-version dev-smoke-5x10 --date YYYY-MM-DD --limit 5 --case-workers 5 --model-call-limit 10
```

When observed complete-case receipts, schemas, isolation and provider behavior justify the next ramp, register ten cases/ten calls:

```text
python /private/run/trainer-r1/scripts/parallel_campaign.py --corpus /private/run/corpus --runs /private/run/development --trainer-snapshot /private/run/trainer-r1 --selector-skill /private/run/selector-v2-r1 --eval-version dev-wave-10x10 --date YYYY-MM-DD --limit 10 --case-workers 10 --model-call-limit 10
```

The date, model/effort, corpus, Trainer, Selector and concurrency settings are bound to the registered epoch. Changing them requires a dated protocol amendment and new `--eval-version`; a new epoch does not create another case count. Smoke cases count only after a complete authorized case loop. Synthetic tests and short authenticated model-call tests are separate transport checks, not completed paper iterations or proof that a full ten-paper wave passes.

## Decisions at the wave barrier

Each case keeps its ordered preparation, selection, blind review, reveal and diagnosis chain. The parent waits for **all workers in the wave** before reading their completed ledgers and writing shared summaries. The scheduler stops at `decision_pending`; it never automatically accepts a rule or records `no_change`. A new development wave cannot start while any preceding diagnosis remains undecided. Twenty-case reporting groups only aggregate results; they do not control when rules change.

Inspect the sealed diagnosis and sources, then record an evidence-based decision for every diagnosed case. For example:

```text
python /private/run/trainer-r1/scripts/record_decision.py /private/run/development/CASE_ID --decision no_change --reason "The sealed diagnosis and source review show that existing rules already cover the observed issue."
python /private/run/trainer-r1/scripts/record_decision.py /private/run/development/CASE_ID --decision accepted_change --reason "Recorded generalizable issue and observed regression result." --changed-file /path/to/changed-rule.md --regression-record /private/run/actual-regression.json
```

Use `retrieval_repair` or `rejected_change` when that is the actual assessed outcome. Accepted changes require actual changed files and genuine regression evidence. No example reason substitutes for a real review. If rules change, freeze a new Selector snapshot after the barrier and pass that new path with a new epoch on the next wave. If Trainer helpers change, freeze a new Trainer too. Workers already running never receive edits. Replays and regressions do not increase the distinct-case total.

## Pause, failures and resume

A `PAUSE` file in the run directory prevents the next wave; it does not kill active calls. The scheduler retains failed calls, contract-invalid responses, attempt archives and incomplete ledgers. A failure pauses further dispatch, leaves other wave outcomes intact, and does not count as completion. Inspect and resolve the failure before retrying the affected case with the same masked input, frozen snapshots and registered settings; append `--case-id CASE_ID` to restrict a retry to that case. Changed inputs require a separate output path/context and recorded protocol handling, never a silent overwrite.

Per-case exclusive claims prevent duplicate execution. The central scheduler also has an exclusive claim so two parents cannot write the shared summary together. A process crash can leave a claim behind; the scheduler does not guess that an owner is dead or steal its claim. After independently confirming the owner stopped, release the exact observed token with a retained reason:

```text
python /private/run/trainer-r1/scripts/parallel_campaign.py --runs /private/run/development --release-claim CASE_ID --claim-token OBSERVED_TOKEN --reason "Confirmed the recorded owner process has stopped; retained its interrupted receipts."
```

Use `--release-claim scheduler` for the central claim. Do not release a live owner's claim. Repeated provider failures require visible diagnosis and a recorded lower concurrency setting under a new epoch; do not switch models or treat unavailable usage as zero.

`status.py` reads checkpoints without a model call or parsing the answer map. A request without a terminal record may be active or interrupted; this tool does not establish process liveness.

```text
python /private/run/trainer-r1/scripts/status.py --corpus /private/run/corpus --runs /private/run/development
```

## Untouched final comparison

After all 100 allocated development cases and required regressions finish, freeze the final V2 candidate and final Trainer once. Bind the authoritative development run directory explicitly; the final entry verifies actual per-case seals, terminal receipts and decisions rather than trusting a summary count. Run all fifty holdout cases with the same V1/V2, model, source limits and concurrency settings. Both model variants use the shared case preparation; the two fixed discovery baselines remain unchanged. Their ranking algorithms are fixed, while their shared preparation includes model-generated search concepts and a masked abstract summary.

```text
python /private/run/final-trainer/scripts/parallel_campaign.py --corpus /private/run/corpus --runs /private/run/final --development-runs /private/run/development --trainer-snapshot /private/run/final-trainer --selector-skill /private/run/final-v2 --baseline-skill /private/run/selector-v1 --eval-version final-10x10 --date YYYY-MM-DD --split holdout --limit 50 --case-workers 10 --model-call-limit 10
```

Holdout waves stop at reviewed, sealed outputs and never reveal their answers individually. Before the first selection, each new case seals fixed-baselines and shared profile, literature, policies and source packets. Both final reviewers inspect all four comparators; ranking-only baselines do not pretend to contain complete reports. Once **all fifty** have actual unchanged preparation, generation and independent review seals, run the separate global reveal command with identical bindings:

```text
python /private/run/final-trainer/scripts/parallel_campaign.py --corpus /private/run/corpus --runs /private/run/final --development-runs /private/run/development --trainer-snapshot /private/run/final-trainer --selector-skill /private/run/final-v2 --baseline-skill /private/run/selector-v1 --eval-version final-10x10 --date YYYY-MM-DD --split holdout --reveal-final --case-workers 10 --model-call-limit 10
```

The reveal gate preserves the original all-case output/hash/context checks and additionally verifies the original preparation manifests, four-comparator review inputs and actual frozen Skill/execution-script hashes. It checks the whole batch before the reveal/scoring role reads any answer. A partial set, changed baseline or running worker cannot pass. Final results must not be used to tune the frozen candidate before reveal. Running these commands does not itself establish the publication gates; incomplete, contaminated or failed records remain visible. Earlier development records are not retroactively given preparation seals; their actual older seal boundary remains disclosed.

## Other helpers and manual hosts

```text
python /private/run/trainer-r1/scripts/runner.py prompt.txt --output /private/run/response.json
python /private/run/trainer-r1/scripts/evaluation.py records.json --output summary.json
```

Each campaign model turn has a 1,800-second wall-time ceiling; the standalone runner defaults to 900 seconds. Record actual elapsed time and all failed attempts. Keep identical limits for final V1/V2 calls. A timeout without a genuine terminal completion is incomplete.

The original serial `campaign.py` remains available for a single ordered workflow. Its optional `--auto-no-rule` bookkeeping switch is not an option in the parallel scheduler and does not replace the wave decision review.

When preselected reserves cannot fill a demonstrated unevaluated-input eligibility gap, `corpus.py --output /private/run/corpus --extend-reserves STRATUM --reserve-count 3 --seed RECORDED_SEED` appends licensed, nonduplicate reserves. Record the dated cohort amendment, retain exposed protocol-trial outputs, check split quotas/journal caps and freeze the replacement allocation before execution. Never replace a scored poor recommendation to improve metrics.

Other hosts can follow the same controlled workflow manually. Without auditable fresh contexts and filtered inputs, record the lower isolation level and do not claim this campaign's blind-test gates passed.

---

## Inlined reference: isolation-and-records.md

# Isolation and records

Current journal registry records may verify title/ISSN identity, with explicit identity-only provenance. They cannot verify scope, method permission, indexing, JCR, JIF, fees or timelines. The project source collector prioritizes at most six coherent dossiers: up to twelve official web leads and six registry endpoints share eighteen initial slots, followed by at most twelve actual policy links. Missing registry records remain unknown. All variants use the same prepared evidence and resource ceiling.

Preserve each supplied record's `source_type` in the corresponding evidence envelope. A registry's own journal record is primary (`official`) identity evidence; article/abstract metadata is `bibliographic`. A shared domain does not give both records the same authority. Never silently relabel an original model output to erase a provenance error: retain the failure, record any diagnostic replay separately, then test the clarified rule with fresh generation and independent reviews.

Keep original papers and answers in a preparation-only store. Generator packets contain masked body text, constraints, target-Skill text and filtered source excerpts. They contain no target paper IDs, answer file paths, author names or exact manuscript title. Retain a private exclusion fingerprint containing DOI/PMID/PMCID, title tokens, authors and duplicate-family hashes; filter retrieved content before delivery.

Extract research text recursively: publishing notes, nested reference lists, self-citation instructions, transparency declarations and review histories can occur inside the XML body. Removing a citation or link must preserve its following XML tail, including methods and results. Audit known identity strings and publishing-history patterns before freezing masked inputs. A changed extractor requires a recorded input-hash amendment before generation; exposed cases affected by a protocol defect remain protocol-only records. Recheck near-duplicate families and identifier-based journal caps after changing extracted text.

Preserve visible research link labels and ordinary biomedical terms. Removing an external link must not remove its dataset accession, measurement or method. A journal named Blood/Cells/Medicine does not justify removing blood/cells/medicine from the research narrative; hide explicit publishing contexts and headers. By default retain public dataset accessions, mask trial registry numbers consistently while preserving the registration statement, and reject trial/dataset identifier lookups in journal discovery. Optional consistent accession pseudonyms preserve reuse comparisons but prevent independent checks of the real data source; record that limit and freeze the chosen policy before generation.

Keep ethics approval, patient/publication consent, registration and data/code availability even when placed under Declarations or in XML back matter. Remove identifying publication/author sections recursively rather than discarding that entire container. State which figure pixels or supplements were not inspected. Concealed links or identifiers are different from absent declarations.

Editorial footnotes naming the handling editor or reviewers and publisher-generated image-alt-text credits are publication clues, even inside the research-body container. Remove those notes while keeping scientific footnotes, consent/data declarations and the authors' own AI-use statement. Retain a failed preparation request when masking changes; use a fresh context and record the amended input hash rather than overwriting that request.

Study registrations include NCT, ISRCTN, PROSPERO CRD, ChiCTR, ACTRN, UMIN, DRKS, IRCT and KCT identifiers. Preserve the fact and timing of registration while replacing repeat occurrences with the same local label. Apply the same identifier guard to retrieval queries. If an unseen input needs a masking correction, record its old/new hash before generation; completed unaffected inputs and scores remain unchanged.

Recommended project runner: fresh ephemeral Codex processes in an empty workspace, user config/memories/hooks/MCP loading disabled, explicit frozen model/effort, shell and direct web tools disabled. All input is supplied by the orchestrator; retrieval requests are serviced outside the model and filtered before the next generation. Inspect events for unexpected tools. A prompt-only prohibition is not equivalent. Test attempted answer reads and injected search titles with synthetic sentinel inputs before real cases.

The local record contains `case_id`, `stage`, `split`, `stratum`, `license`, `study_family`, `input_hash`, `skill_hash`, `model`, `effort`, `context_id`, `evidence_hash`, `output_hash`, `sealed_at`, `review_context_ids`, `review_hashes`, `reviews_sealed_at`, `revealed_at`, `status`, `failure_kind`, and `changes`. Timestamps are real ISO values including timezone. Hashes identify artifacts; they alone are not a tamper-proof remote audit.

Statuses include prepared, generated, reviewed, revealed, diagnosed, completed, infrastructure_failed, model_failed and contamination_failed. Recommendation errors are scored results, not infrastructure failures. Save a checkpoint after every completed phase and refuse reuse if input/Skill/settings differ. Never label a failed or skipped model call successful. A diagnosed development case is incomplete until its explicit decision is recorded.

New execution epochs create an original preparation seal before the first selection, covering both fixed baselines, shared profile/literature/policies/packet files and recorded preparation completions. Validate hashes and time ordering before later phases. Refuse late or replacement seals; retain the original binding across retries. Legacy development cases keep their real older boundary rather than receiving a fictitious prior seal. Every final case requires the stronger seal. The reveal/scoring role validates all fifty preparation, generation and review seals before reading final answers; this does not prevent the isolated preparation role from knowing identities for masking and exclusions.

Actual isolation values: `CONTROLLED_PACKET_FRESH_CONTEXT`, `FRESH_CONTEXT_UNRESTRICTED_TOOLS`, `SHARED_CONTEXT_EXPOSED`, `UNVERIFIED`. Only the first can satisfy this campaign's blind-evaluation gate after event inspection. It still does not exclude prior model memory of public text.

---

## Inlined reference: protocol.md

# Sampling and experiment protocol

Primary strata: clinical/nursing original; laboratory experiment; public-database secondary; bioinformatics; prediction model; network pharmacology/toxicology; systematic review/Meta-analysis; other review; bibliometrics; case report/series. Assign each paper one primary stratum plus overlapping method labels. Check the actual manuscript before claiming the search classifier is correct.

The project seed is `20261002`; stage-two seed is `20261003`. Select ten development and five final cases per stratum, with journal caps of five/three per split per stage. Search results are shuffled with the stored seed before allocation, not sorted by later model performance. Store preselected reserves. Ordinary replacements are permitted only for pre-generation eligibility/access/duplicate problems and must come from the same stratum with a recorded reason. Once the model has been evaluated on a valid input under the registered protocol, keep its bad result in that protocol's denominator. A demonstrated protocol defect follows the cohort-amendment rule below.

Use the CC0 or CC BY subset for this campaign, with methods and accessible supplements. Record the individual article license and retrieval path, including linked license URLs. Do not mistake Attribution-Non Commercial, NoDerivs or ShareAlike for plain CC BY; mixed or ambiguous permissions need eligibility review before generation. PMC accessibility alone does not establish reuse permission. Keep originals private; share identifiers and scores. Check clinical/medical relevance; classifications based solely on retrieval queries are provisional. Unknown JCR/SCIE cannot be called verified SCI. Record journal concentration and field coverage rather than claiming population representativeness.

Current mode measures hypothetical unpublished-submission compatibility under current scope and method policy. A published final article supplies the study content only. For selection, review and diagnosis, assume this study has never been submitted or published and is not under consideration elsewhere; keep its research question, methods, results and data provenance unchanged. Publication history of this benchmark source alone cannot disqualify a destination journal. Real article-type, method, data-reuse, novelty, ethics, consent and other substantive restrictions still apply; ordinary unpublished/no-simultaneous-submission declarations remain conditions for a real submission. Record this assessment target and assumption in every generator and reviewer packet. The final text may differ from the original submitted manuscript, and public-paper model memory remains a limitation. This mode does not reconstruct the historical submission or estimate acceptance probability.

Public-database/rapid computational discovery uses 24 months; other designs use five years with recent emphasis. Record any expansion. The published target is excluded from all retrieval windows even if it falls inside them. Historical mode, when separately requested, needs time-cutoff evidence and must not borrow later policies or papers.

Freeze input IDs, split, reserve order, model settings and tool bounds in `manifest.json` before generation. Ten development cases and five final cases per stratum are minimum required valid-input records, not a license to discard unfavorable recommendations. Access failures and contamination are explicit incomplete outcomes and cannot satisfy completion gates.

A demonstrated protocol defect needs a dated, hashed amendment before further formal generation. Define the affected cohort by the defect and exposure time, independently of good or bad scores. Preserve every original output, review, score, failure and resource receipt as protocol-trial evidence; do not pool that cohort into the amended target's formal estimate or count its replay as a new blind case. Refill formal slots only from unexposed same-stratum reserves in the recorded order after eligibility checks. Record any reserve augmentation and its seed before promotion; never borrow final-test cases. Unaffected completed cases retain their original scores. This narrow protocol correction does not authorize replacing poor recommendations.

Parallel development uses ten logical queues, one per primary stratum. The default wave takes one available case per queue, up to ten cases; groups of twenty are reporting units only. Start with real two-case and then five-case smoke waves before using ten, and cap all simultaneous model calls at ten across workers and reviewers. Freeze corpus, assessment target, prompts/configuration, source bounds and Skill snapshot for each wave. Seal all worker records at the wave barrier before a central decision accepts changes and freezes the next wave. Final evaluation uses one fixed baseline/candidate pair; every final generation and blind review is sealed before any final answer is revealed. See the project's bilingual parallel execution plan for scheduling and failure handling.

Check the answer's outlet identity in the preparation role before generation. A full-text XML journal block may omit ISSNs; reconcile them against an exact article-matched bibliographic or primary record and retain that provenance privately. The supplied helpers require reconciled identifiers for formal inputs. Keep answer metadata outside blind packets. Discovery, delivery and pending assessment are distinct from eligible recommendation: a discovered but policy-pending original outlet is not a hit in the supported fit sequence. Missing identity cannot silently become a non-hit.

## Shared-input interpretation

If the implementation shares a manuscript profile, retrieved journal pool and official snapshots between V1 and V2, describe the comparison as recommendation quality on shared prepared evidence. It does not measure differences in autonomous end-to-end search or discovery. Record the preparation model, queries, curation limits, page budget, clipping extent and time ceiling. Use identical bounds and snapshots for paired final variants; do not hide a retrieval repair's extra requests in the original case budget.

---

## Inlined reference: review-and-promotion.md

# Review, metrics and release gates

Review before answer reveal. Judges receive masked study materials, recommendations and sources, no version IDs, answer, previous judgments or change hypotheses. Journal names in the recommendation are visible because they are the object of review; the true publishing journal identity is hidden.

In current mode, judge the hypothetical never-submitted, unpublished study described by the packet. The published final article is the source of its scientific content, not the submission status being evaluated. A journal's ordinary unpublished/no-simultaneous-submission clause is therefore a declaration condition, not a failure caused by the benchmark source's publication. Continue to enforce actual article-type, method, data-reuse, novelty, ethics, consent and other substantive restrictions. Do not turn this benchmark assumption into advice to resubmit a published paper.

Check each recommended journal's identity, exact scope quote and manuscript-specific connection, article-type admission, actual method-policy evidence, hard constraints, and source support for every changing fact. Separate verified policy from a reasoned methodological assessment. Missing scope/admission evidence cannot become an eligible journal just because the manuscript resembles a published paper. Missing non-hard JCR/time data can empty those routes without invalidating a supported fit route.

Hard failures: fabricated/unsupported verified fact, wrong journal identity, fabricated scope quote, known article/method prohibition bypassed, user hard gate ignored, target-answer leakage, or individual acceptance guarantee. Record the precise claim, source and repair needed. Unavailable fields correctly marked unknown are not failures. An empty report avoids fabrication but does not count as usable coverage.

For final comparison, both judges inspect four anonymous results, with an independently randomized presentation order. Remove embedded model/Skill/version metadata. Evaluate supported ranking fit for every comparator and assess complete-report fields only when those fields are claimed; deterministic ranking baselines cannot acquire invented verification or V2-derived judgments. The fixed algorithms use shared model-assisted concepts and an abstract summary, not an unmasked author abstract.

Record judgments for all six pairs, with source-based explanations. Extract the V1/V2 pair using the private label map, based on supported useful recommendations, method reasoning, evidence calibration and unnecessary burden. Two agreeing votes decide; otherwise a third judge reviews independently. An unresolved split remains unresolved and is reported, not assigned to the favored version. Full-output differences may still let a reviewer infer a comparator's type despite hidden labels; do not claim perfect version blinding.

Compute Hit@k against the evaluation-only fit sequence and record whether the target journal was discovered at all. Use all evaluated valid-input cases as denominator; do not drop non-hits or empty reports. Provide Wilson 95% intervals, per-stratum denominators, policy-change notes, and raw counts. Also report evidence-supported usable coverage (at least one eligible journal), unknown-field coverage, hard failures, independent-review disagreement, tokens and timing when observed.

Keep repeated source/reviewer error flags separately from affected-case counts; do not call two reports of one claim two distinct errors. Include actual retry/regression and unfinished-case receipts in observed resource totals, deduplicating copied receipts by context/input/start time. They never increase distinct completed cases. Preserve original development scores after repair and label regressions separately.

Report protocol-trial cohorts separately from amended formal development results, with the original denominator, scores and reason for the amendment still visible. A cohort identified by a demonstrated protocol defect includes every affected exposed case, including favorable scores and generated-but-unrevealed attempts. Their replays are diagnostic regressions only. Formal replacements require previously unexposed same-stratum inputs and recorded eligibility; no recommendation error by itself permits replacement.

Parallel workers may seal independent outputs and reviews without sharing answers or lessons. Two reviewers can run together only within the global ten-model-call cap; adjudication waits for both. A central wave barrier reviews diagnoses and records accept/reject/retrieval-repair/no-change decisions before any changed Skill snapshot is used. Twenty-case report groups do not control rule updates. During final tests the barrier covers the entire final set before answer reveal, and no worker diagnosis may change the fixed candidate.

Report verified, unverified and invalid-status envelope counts for each fact/timeline field in the original sealed output. A model's verified label is not an independent correctness result; source and reviewer failures remain separate. Missing coverage records are unknown, not zero missing facts.

Stage promotion gates: 100 completed development and 50 untouched final records; every final V1/V2 generation and two blind reviews sealed before reveal; zero unresolved V2 hard failures; V2 paired wins >= losses; V2 usable coverage >= V1; protected behavior/language/package/installation checks passed. No statistical-improvement claim follows from a non-inferiority gate alone. The model/provider and AI-only judgments limit external validity.

Failure at stage one permits exactly one authorized extension (100 new development + 50 new final). Exposed test cases can diagnose defects but are not new blind evidence. Failure at stage two stops with `GATES_NOT_PASSED`; model connectivity exhaustion stops with `RUNNER_UNAVAILABLE`; no publication claims either outcome succeeded. General Trainer use may have other user-agreed bounds recorded in its manifest.
