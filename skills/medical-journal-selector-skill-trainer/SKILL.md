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

Freeze both the final candidate and original baseline before running the untouched final set. Compare fixed keyword, fixed TF-IDF abstract similarity, original V1, and candidate V2 with equal data-source/window/tool budgets. Shared case snapshots preserve actual acquisition times; they are experimental inputs, not a reusable claim of today's facts. Keyword and abstract baselines are discovery/ranking comparators, not complete evidence-audited reports.

Seal ALL final-set generations and blind reviews before aggregate answers are revealed. Once a test's results inform a rule change, it becomes exposed data; new claims require a new untouched final set. Do not repeatedly tune against it.

Report numerator, denominator, failures, missingness, by-stratum results, Hit@k and Wilson intervals, true-journal rank, V2/V1 wins/ties/losses, eligible-candidate coverage, evidence violations, timing and available token usage. AI sessions are not medical experts; same-model judgments are not independent human validation. Neither journal matches nor precedents estimate acceptance probability. Read [review-and-promotion.md](references/review-and-promotion.md).

Project promotion requires complete case records, no unresolved V2 hard failures in final tests, wins at least losses, non-decreasing evidence-supported usable coverage, protected behavior tests, bilingual output, package checks and observed installation compatibility. Do not invent a success threshold or claim a significant gain without statistical evidence. If stage one fails, perform only the authorized one-stage extension. If stage two fails, keep the candidate and truthful results without a stable release.

## Execution and portability

The scripts in `scripts/` assist with corpus preparation, masked packets, hashes, model-run records, fixed baselines and aggregation. Python 3.10+ is required for these helpers. The host supplies its existing model access; no GPT API key is required by this Skill. `runner.py` uses fresh Codex CLI calls for the project campaign, not a transferable API credential.

For another Agent, apply the same workflow using its own isolated contexts and controlled retrieval. If scripting or isolation is unavailable, do not simulate successful automation. Record the limit and perform only the supported manual steps. See [commands.md](references/commands.md).

Keep raw papers, answer maps, credentials and full model logs out of the public repository and release archives. Public reports contain permitted identifiers, derived decisions and concise paraphrased lessons; do not reproduce full papers. Deliver the candidate Skill, case ledger, change ledger, review/metrics report, actual isolation record, final gate decision and one stopping reason.
