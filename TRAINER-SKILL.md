---
name: medical-journal-selector-skill-trainer
description: Evaluate and improve the medical-journal-selector Skill with masked published manuscripts, sealed recommendations, current journal evidence, independent AI review, and untouched final tests. Use for journal-selector iteration, benchmarking, or batch evaluation; ordinary manuscript journal selection uses medical-journal-selector.
---

# Medical Journal Selector Skill Trainer v1.0.0

Improve reusable journal-selection decisions, not a single answer. Follow the user's language. This is workflow and instruction development, not model fine-tuning. A journal that published a paper is one known outlet, not the only correct recommendation or an acceptance-probability label.

## Establish the experiment

Record the target Skill snapshot and hash, model and reasoning settings, current-versus-historical evidence mode, sample strata, development/final-test allocation, random seed, tool budget, and release gates before examining results. Preserve the selector's name and its three production routes. Do not alter a production Skill or publish merely because the Trainer was invoked: execute only changes and publication already authorized by the user.

For the project V2 campaign, use 100 distinct development cases and 50 untouched final cases, ten primary article classes, and current policies. At most one failed-gate extension adds 100 development cases and 50 new final cases. Each class has 10 development and 5 final cases per stage. Record additional method labels. Maximum journal representation is five development and three final cases per stage. Verify licenses individually; unavailable JCR/SCIE records remain unknown, not invented sample labels. Read [protocol.md](references/protocol.md).

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

## Final evaluation and promotion

Freeze both the final candidate and original baseline before running the untouched final set. Compare fixed keyword, fixed TF-IDF abstract similarity, original V1, and candidate V2 with equal data-source/window/tool budgets. Shared case snapshots preserve actual acquisition times; they are experimental inputs, not a reusable claim of today's facts. Keyword and abstract baselines are discovery/ranking comparators, not complete evidence-audited reports.

Seal ALL final-set generations and blind reviews before aggregate answers are revealed. Once a test's results inform a rule change, it becomes exposed data; new claims require a new untouched final set. Do not repeatedly tune against it.

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

Python 3.10+; standard library only. Run from the Trainer folder. Corpus and full logs belong in an ignored private directory, not inside a release bundle.

```text
python scripts/corpus.py --output /private/run/corpus --date YYYY-MM-DD
python scripts/freeze.py /private/run/frozen-v2 --source /path/to/candidate
python scripts/freeze.py /private/run/frozen-v2 --verify
python scripts/campaign.py --corpus /private/run/corpus --runs /private/run/development --selector-skill /path/to/candidate --limit 5
python scripts/runner.py prompt.txt --output /private/run/response.json
python scripts/evaluation.py records.json --output summary.json
python scripts/status.py --corpus /private/run/corpus --runs /private/run/development
```

Corpus allocation must be frozen before generation. The campaign stops on an execution/isolation failure and saves the genuine failed record. Inspect it before retrying. A retry of an identical completed request verifies artifact hashes; changed input requires a new output path/context. Never manually create successful completion records.

`status.py` reads checkpoints without a model call or the answer map. It distinguishes completed cases from prepared, generated and reviewed phases. A request without a terminal record may still be running or may have been interrupted; this status tool does not infer process liveness.

Use `--pilot --limit 5` for the five-family workflow check and `--limit 100` for the allocated development set. A `PAUSE` file in the run directory stops at the next case boundary; removing it and running the same command resumes. Preserve failed attempts and unfinished cases. A stopped generation is not a completed iteration. Inspect any diagnosed case needing an adoption decision and use `record_decision.py` with an evidence-based reason; accepted changes require changed files and actual regression output.

Optional `--auto-no-rule` records a no-change decision only when a genuine post-reveal diagnosis gives an explicit no-change reason, proposes either `no rule` or no hypotheses, confirms the stratum and has clean source/review audits. It preserves negative results and claims no unperformed repair. Proposed instruction changes, uncertain classification and hard failures still stop for review. This switch never edits the Selector or publishes anything.

Final evaluation uses `--split holdout --limit 50 --baseline-skill /private/run/frozen-v1 --selector-skill /private/run/frozen-v2`. Do not reveal answers until all fifty cases have sealed generations and reviews. Then use the same paths with `--split holdout --reveal-final`; the gate verifies output hashes and distinct generation/review contexts. Freeze the Trainer's execution scripts too, so later helper edits cannot silently change the evaluation protocol.

The campaign's development selection/review/reveal phase records `lesson_status: pending` until a reusable change or an explicit no-change decision has actually been assessed. Generation alone does not complete an iteration. Final tests additionally require both frozen V1 and V2 paths and the separate all-cases reveal gate. Use the protocol to interpret these scripts; running a command is not proof of gate success.

Campaign calls have a 1,800-second wall-time ceiling per fresh model turn; record actual elapsed time and failed attempts. The standalone runner defaults to 900 seconds unless overridden. Keep identical bounds for both final variants. A timeout with no terminal completion is incomplete even if it spent time computing. The project raised the campaign ceiling after a genuine 900-second pilot timeout; it preserved that failed attempt and retries the same case rather than replacing it.

When eligibility removes an unevaluated input and the preselected reserves are insufficient, `corpus.py --output /private/run/corpus --extend-reserves STRATUM --reserve-count 3 --seed RECORDED_SEED` appends licensed, nonduplicate reserves. It does not promote them or erase failures. Record the eligibility amendment and check split quotas and journal caps before freezing the replacement allocation. Never augment to replace a scored poor result.

Other hosts may perform the same steps manually. Without auditable fresh context and controlled inputs, record the lower isolation level and do not claim this campaign's blind-test gates passed.

---

## Inlined reference: isolation-and-records.md

# Isolation and records

Current journal registry records may verify title/ISSN identity, with explicit identity-only provenance. They cannot verify scope, method permission, indexing, JCR, JIF, fees or timelines. The project source collector prioritizes at most six coherent dossiers: up to twelve official web leads and six registry endpoints share eighteen initial slots, followed by at most twelve actual policy links. Missing registry records remain unknown. All variants use the same prepared evidence and resource ceiling.

Preserve each supplied record's `source_type` in the corresponding evidence envelope. A registry's own journal record is primary (`official`) identity evidence; article/abstract metadata is `bibliographic`. A shared domain does not give both records the same authority. Never silently relabel an original model output to erase a provenance error: retain the failure, record any diagnostic replay separately, then test the clarified rule with fresh generation and independent reviews.

Keep original papers and answers in a preparation-only store. Generator packets contain masked body text, constraints, target-Skill text and filtered source excerpts. They contain no target paper IDs, answer file paths, author names or exact manuscript title. Retain a private exclusion fingerprint containing DOI/PMID/PMCID, title tokens, authors and duplicate-family hashes; filter retrieved content before delivery.

Extract research text recursively: publishing notes, nested reference lists, self-citation instructions, transparency declarations and review histories can occur inside the XML body. Removing a citation or link must preserve its following XML tail, including methods and results. Audit known identity strings and publishing-history patterns before freezing masked inputs. A changed extractor requires a recorded input-hash amendment before generation; exposed cases affected by a protocol defect remain protocol-only records. Recheck near-duplicate families and identifier-based journal caps after changing extracted text.

Preserve visible research link labels and ordinary biomedical terms. Removing an external link must not remove its dataset accession, measurement or method. A journal named Blood/Cells/Medicine does not justify removing blood/cells/medicine from the research narrative; hide explicit publishing contexts and headers. By default retain public dataset accessions, mask trial registry numbers consistently while preserving the registration statement, and reject trial/dataset identifier lookups in journal discovery. Optional consistent accession pseudonyms preserve reuse comparisons but prevent independent checks of the real data source; record that limit and freeze the chosen policy before generation.

Keep ethics approval, patient/publication consent, registration and data/code availability even when placed under Declarations or in XML back matter. Remove identifying publication/author sections recursively rather than discarding that entire container. State which figure pixels or supplements were not inspected. Concealed links or identifiers are different from absent declarations.

Study registrations include NCT, ISRCTN, PROSPERO CRD, ChiCTR, ACTRN, UMIN, DRKS, IRCT and KCT identifiers. Preserve the fact and timing of registration while replacing repeat occurrences with the same local label. Apply the same identifier guard to retrieval queries. If an unseen input needs a masking correction, record its old/new hash before generation; completed unaffected inputs and scores remain unchanged.

Recommended project runner: fresh ephemeral Codex processes in an empty workspace, user config/memories/hooks/MCP loading disabled, explicit frozen model/effort, shell and direct web tools disabled. All input is supplied by the orchestrator; retrieval requests are serviced outside the model and filtered before the next generation. Inspect events for unexpected tools. A prompt-only prohibition is not equivalent. Test attempted answer reads and injected search titles with synthetic sentinel inputs before real cases.

The local record contains `case_id`, `stage`, `split`, `stratum`, `license`, `study_family`, `input_hash`, `skill_hash`, `model`, `effort`, `context_id`, `evidence_hash`, `output_hash`, `sealed_at`, `review_context_ids`, `review_hashes`, `reviews_sealed_at`, `revealed_at`, `status`, `failure_kind`, and `changes`. Timestamps are real ISO values including timezone. Hashes identify artifacts; they alone are not a tamper-proof remote audit.

Statuses: prepared, generated, reviewed, revealed, completed, infrastructure_failed, contamination_failed. Recommendation errors are scored results, not infrastructure failures. Save a checkpoint after every completed phase and refuse reuse if input/Skill/settings differ. Never label a failed or skipped model call successful. A final-set reveal gate checks all required output and review seals before reading the answer map.

Actual isolation values: `CONTROLLED_PACKET_FRESH_CONTEXT`, `FRESH_CONTEXT_UNRESTRICTED_TOOLS`, `SHARED_CONTEXT_EXPOSED`, `UNVERIFIED`. Only the first can satisfy this campaign's blind-evaluation gate after event inspection. It still does not exclude prior model memory of public text.

---

## Inlined reference: protocol.md

# Sampling and experiment protocol

Primary strata: clinical/nursing original; laboratory experiment; public-database secondary; bioinformatics; prediction model; network pharmacology/toxicology; systematic review/Meta-analysis; other review; bibliometrics; case report/series. Assign each paper one primary stratum plus overlapping method labels. Check the actual manuscript before claiming the search classifier is correct.

The project seed is `20261002`; stage-two seed is `20261003`. Select ten development and five final cases per stratum, with journal caps of five/three per split per stage. Search results are shuffled with the stored seed before allocation, not sorted by later model performance. Store preselected reserves. A replacement is permitted only for pre-generation eligibility/access/duplicate problems and must come from the same stratum with a recorded reason. Once the model has been evaluated on the input, keep its bad result in the denominator.

Use the CC0 or CC BY subset for this campaign, with methods and accessible supplements. Record the individual article license and retrieval path, including linked license URLs. Do not mistake Attribution-Non Commercial, NoDerivs or ShareAlike for plain CC BY; mixed or ambiguous permissions need eligibility review before generation. PMC accessibility alone does not establish reuse permission. Keep originals private; share identifiers and scores. Check clinical/medical relevance; classifications based solely on retrieval queries are provisional. Unknown JCR/SCIE cannot be called verified SCI. Record journal concentration and field coverage rather than claiming population representativeness.

Current mode uses current scope and method policy. Public-database/rapid computational discovery uses 24 months; other designs use five years with recent emphasis. Record any expansion. The published target is excluded from all retrieval windows even if it falls inside them. Historical mode, when separately requested, needs time-cutoff evidence and must not borrow later policies or papers.

Freeze input IDs, split, reserve order, model settings and tool bounds in `manifest.json` before generation. Ten development cases and five final cases per stratum are minimum required valid-input records, not a license to discard unfavorable recommendations. Access failures and contamination are explicit incomplete outcomes and cannot satisfy completion gates.

Check the answer's outlet identity in the preparation role before generation. A full-text XML journal block may omit ISSNs; reconcile them against an exact article-matched bibliographic or primary record and retain that provenance privately. The supplied helpers require reconciled identifiers for formal inputs. Keep answer metadata outside blind packets. Discovery, delivery and pending assessment are distinct from eligible recommendation: a discovered but policy-pending original outlet is not a hit in the supported fit sequence. Missing identity cannot silently become a non-hit.

## Shared-input interpretation

If the implementation shares a manuscript profile, retrieved journal pool and official snapshots between V1 and V2, describe the comparison as recommendation quality on shared prepared evidence. It does not measure differences in autonomous end-to-end search or discovery. Record the preparation model, queries, curation limits, page budget, clipping extent and time ceiling. Use identical bounds and snapshots for paired final variants; do not hide a retrieval repair's extra requests in the original case budget.

---

## Inlined reference: review-and-promotion.md

# Review, metrics and release gates

Review before answer reveal. Judges receive masked study materials, recommendations and sources, no version IDs, answer, previous judgments or change hypotheses. Journal names in the recommendation are visible because they are the object of review; the true publishing journal identity is hidden.

Check each recommended journal's identity, exact scope quote and manuscript-specific connection, article-type admission, actual method-policy evidence, hard constraints, and source support for every changing fact. Separate verified policy from a reasoned methodological assessment. Missing scope/admission evidence cannot become an eligible journal just because the manuscript resembles a published paper. Missing non-hard JCR/time data can empty those routes without invalidating a supported fit route.

Hard failures: fabricated/unsupported verified fact, wrong journal identity, fabricated scope quote, known article/method prohibition bypassed, user hard gate ignored, target-answer leakage, or individual acceptance guarantee. Record the precise claim, source and repair needed. Unavailable fields correctly marked unknown are not failures. An empty report avoids fabrication but does not count as usable coverage.

For paired V1/V2 comparison, judges choose A/B/tie based on supported useful recommendations, method reasoning, evidence calibration and unnecessary burden, with a source-based explanation. Two agreeing votes decide; otherwise a third judge reviews independently. An unresolved split remains unresolved and is reported, not assigned to the favored version.

Compute Hit@k against the evaluation-only fit sequence and record whether the target journal was discovered at all. Use all evaluated valid-input cases as denominator; do not drop non-hits or empty reports. Provide Wilson 95% intervals, per-stratum denominators, policy-change notes, and raw counts. Also report evidence-supported usable coverage (at least one eligible journal), unknown-field coverage, hard failures, independent-review disagreement, tokens and timing when observed.

Keep repeated source/reviewer error flags separately from affected-case counts; do not call two reports of one claim two distinct errors. Include actual retry/regression and unfinished-case receipts in observed resource totals, deduplicating copied receipts by context/input/start time. They never increase distinct completed cases. Preserve original development scores after repair and label regressions separately.

Report verified, unverified and invalid-status envelope counts for each fact/timeline field in the original sealed output. A model's verified label is not an independent correctness result; source and reviewer failures remain separate. Missing coverage records are unknown, not zero missing facts.

Stage promotion gates: 100 completed development and 50 untouched final records; every final V1/V2 generation and two blind reviews sealed before reveal; zero unresolved V2 hard failures; V2 paired wins >= losses; V2 usable coverage >= V1; protected behavior/language/package/installation checks passed. No statistical-improvement claim follows from a non-inferiority gate alone. The model/provider and AI-only judgments limit external validity.

Failure at stage one permits exactly one authorized extension (100 new development + 50 new final). Exposed test cases can diagnose defects but are not new blind evidence. Failure at stage two stops with `GATES_NOT_PASSED`; model connectivity exhaustion stops with `RUNNER_UNAVAILABLE`; no publication claims either outcome succeeded. General Trainer use may have other user-agreed bounds recorded in its manifest.
