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

Final evaluation uses `--split holdout --limit 50 --baseline-skill /private/run/frozen-v1 --selector-skill /private/run/frozen-v2`. Do not reveal answers until all fifty cases have sealed generations and reviews. Then use the same paths with `--split holdout --reveal-final`; the gate verifies output hashes and distinct generation/review contexts. Freeze the Trainer's execution scripts too, so later helper edits cannot silently change the evaluation protocol.

The campaign's development selection/review/reveal phase records `lesson_status: pending` until a reusable change or an explicit no-change decision has actually been assessed. Generation alone does not complete an iteration. Final tests additionally require both frozen V1 and V2 paths and the separate all-cases reveal gate. Use the protocol to interpret these scripts; running a command is not proof of gate success.

Campaign calls have a 1,800-second wall-time ceiling per fresh model turn; record actual elapsed time and failed attempts. The standalone runner defaults to 900 seconds unless overridden. Keep identical bounds for both final variants. A timeout with no terminal completion is incomplete even if it spent time computing. The project raised the campaign ceiling after a genuine 900-second pilot timeout; it preserved that failed attempt and retries the same case rather than replacing it.

When eligibility removes an unevaluated input and the preselected reserves are insufficient, `corpus.py --output /private/run/corpus --extend-reserves STRATUM --reserve-count 3 --seed RECORDED_SEED` appends licensed, nonduplicate reserves. It does not promote them or erase failures. Record the eligibility amendment and check split quotas and journal caps before freezing the replacement allocation. Never augment to replace a scored poor result.

Other hosts may perform the same steps manually. Without auditable fresh context and controlled inputs, record the lower isolation level and do not claim this campaign's blind-test gates passed.
