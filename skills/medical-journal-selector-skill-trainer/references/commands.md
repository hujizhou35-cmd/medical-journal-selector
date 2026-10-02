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
