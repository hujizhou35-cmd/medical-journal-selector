"""No-model tests of the formal case scheduler, claims and reveal barrier."""
import concurrent.futures
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "skills/medical-journal-selector-skill-trainer/scripts"))
import campaign
from corpus import STRATA
from freeze import freeze
from parallel_campaign import (AtomicClaim, ClaimBusy, FrozenInputs, ModelCallGate,
                               SnapshotDrift, atomic_write, read, release_stale_claim,
                               reveal_final, run_campaign, stratum_waves, failure_kind)


class ParallelCampaignTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.corpus = self.root / "corpus"
        self.runs = self.root / "runs"
        self.corpus.mkdir()
        self.runs.mkdir()
        self.trainer = self.snapshot("trainer")
        self.v1 = self.snapshot("v1")
        self.v2 = self.snapshot("v2")
        self.skills = {"v2": self.v2}
        self.cases = self.allocate(4)

    def snapshot(self, name):
        source = self.root / (name + "-source")
        source.mkdir()
        (source / "SKILL.md").write_text("Synthetic " + name + " rules", encoding="utf-8")
        (source / "scripts").mkdir()
        (source / "scripts" / "synthetic.py").write_text("# no model execution\n", encoding="utf-8")
        target = self.root / (name + "-frozen")
        freeze(source, target)
        return target

    def allocate(self, count, split="development", strata=("clinical_nursing", "laboratory")):
        cases = []
        for number in range(1, count + 1):
            stratum = strata[(number - 1) % len(strata)]
            case = {"case_id": f"dry-{stratum}-{number:03d}", "stratum": stratum, "split": split}
            work = self.corpus / case["case_id"]
            work.mkdir(exist_ok=True)
            text = "Synthetic masked research " + str(number)
            (work / "masked.txt").write_text(text, encoding="utf-8")
            (work / "source.xml").write_text("<article>Synthetic research</article>", encoding="utf-8")
            # This object must never be parsed by a worker or reveal wrapper
            # before the existing require_reveal gate accepts every case.
            atomic_write(work / "answer.json", {"journal": "SYNTHETIC HIDDEN ANSWER", "issns": ["9000-0005"]})
            case["input_hash"] = hashlib.sha256(text.encode()).hexdigest()
            cases.append(case)
        atomic_write(self.corpus / "manifest.json", {"status": "input_allocation_frozen", "cases": cases})
        return cases

    def invoke(self, execute, **kwargs):
        kwargs.setdefault("case_workers", 2)
        kwargs.setdefault("model_call_limit", 4)
        return run_campaign(self.corpus, self.runs, self.trainer, self.skills, None,
                            "2026-10-02", "synthetic-epoch-1", execute=execute,
                            require_loaded=False, **kwargs)

    def fake_ledger(self, case, status="diagnosed"):
        ledger = {"case_id": case["case_id"], "stratum": case["stratum"], "split": case["split"],
                  "status": status, "lesson_status": "change_review_pending" if status == "diagnosed" else "completed",
                  "calls": [], "scores": {}, "generations": [], "reviews": []}
        atomic_write(self.runs / case["case_id"] / "ledger.json", ledger)
        return ledger

    def test_two_case_wave_unique_dirs_parent_waits_and_no_rule_is_adopted(self):
        barrier = threading.Barrier(2)
        lock = threading.Lock()
        observed = []
        active = 0
        peak = 0

        def fake(case, corpus, runs, skills, selector, date):
            nonlocal active, peak
            work = Path(runs) / case["case_id"]
            self.assertTrue((work / ".parallel-case-claim.json").exists())
            self.assertEqual(skills, self.skills)
            self.assertFalse((Path(runs) / "run-summary.json").exists())
            with lock:
                active += 1
                peak = max(peak, active)
                observed.append(work)
            barrier.wait(timeout=5)
            output = self.fake_ledger(case)
            # Even an explicit no-rule diagnosis must wait for the parent's
            # wave-boundary decision. The scheduler never calls record_decision.
            output["diagnosis"] = {"no_change_reason": "Synthetic already-covered rule", "hypotheses": [{"rule": "no rule"}]}
            atomic_write(work / "ledger.json", output)
            with lock:
                active -= 1
            return output

        result = self.invoke(fake, limit=4)
        self.assertEqual(peak, 2)
        self.assertEqual(len(set(observed)), 2)
        self.assertEqual(len(result["waves"]), 1)
        self.assertEqual(result["status"], "decision_pending")
        self.assertEqual(len(result["pending_decisions"]), 2)
        self.assertTrue((self.runs / "run-summary.json").exists())
        self.assertEqual(read(self.runs / "run-summary.json")["completed"], 0)
        self.assertFalse((self.runs / self.cases[2]["case_id"] / "ledger.json").exists())
        for work in observed:
            self.assertEqual(read(work / "ledger.json")["lesson_status"], "change_review_pending")
            self.assertFalse((work / ".parallel-case-claim.json").exists())

    def test_previous_pending_decision_blocks_new_wave(self):
        self.fake_ledger(self.cases[0])
        with patch("parallel_campaign.campaign.execute") as execute:
            result = self.invoke(execute, case_ids=[self.cases[1]["case_id"]])
        execute.assert_not_called()
        self.assertEqual(result["status"], "decision_pending")
        self.assertEqual(result["pending_decisions"], [self.cases[0]["case_id"]])

    def test_failure_resume_preserves_old_worker_receipt_and_uses_same_epoch(self):
        attempts = {}

        def fake(case, *ignored):
            attempts[case["case_id"]] = attempts.get(case["case_id"], 0) + 1
            state = "infrastructure_failed" if attempts[case["case_id"]] == 1 else "completed"
            return self.fake_ledger(case, state)

        case_id = self.cases[0]["case_id"]
        first = self.invoke(fake, case_ids=[case_id])
        self.assertEqual(first["status"], "failed")
        first_receipt = self.runs / "parallel-worker-receipts" / first["waves"][0]["wave_id"] / (case_id + ".json")
        old_bytes = first_receipt.read_bytes()
        second = self.invoke(fake, case_ids=[case_id])
        self.assertEqual(second["status"], "sealed")
        self.assertEqual(first_receipt.read_bytes(), old_bytes)
        self.assertEqual(read(first_receipt)["status"], "infrastructure_failed")
        self.assertEqual(attempts[case_id], 2)
        self.assertEqual(first["bindings"], second["bindings"])
        events = [read(path) for path in (self.runs / "parallel-claim-records" / case_id).glob("*.json")]
        self.assertEqual(sum(event["status"] == "claimed" for event in events), 2)
        self.assertEqual(sum(event["status"] == "released" for event in events), 2)

    def test_atomic_duplicate_case_claim_retains_failure_receipt(self):
        case_id = self.cases[0]["case_id"]
        with AtomicClaim(self.runs, case_id) as owner:
            original = owner.path.read_bytes()
            with self.assertRaises(ClaimBusy):
                with AtomicClaim(self.runs, case_id):
                    self.fail("Duplicate claim entered")
            self.assertEqual(owner.path.read_bytes(), original)
        events = [read(path) for path in (self.runs / "parallel-claim-records" / case_id).glob("*.json")]
        failure = next(event for event in events if event["status"] == "claim_failed")
        self.assertEqual(failure["existing_owner"]["token"], owner.owner["token"])
        self.assertFalse(owner.path.exists())

    def test_parent_claim_prevents_two_central_summary_writers(self):
        with AtomicClaim(self.runs, "scheduler", scheduler=True):
            with patch("parallel_campaign.campaign.execute") as execute, self.assertRaises(ClaimBusy):
                self.invoke(execute)
            execute.assert_not_called()
            self.assertFalse((self.runs / "run-summary.json").exists())
        failures = [read(path) for path in (self.runs / "parallel-claim-records" / "scheduler").glob("*.json")]
        self.assertTrue(any(value["status"] == "claim_failed" for value in failures))

    def test_duplicate_requested_case_is_rejected_before_execution(self):
        with patch("parallel_campaign.campaign.execute") as execute, self.assertRaises(ValueError):
            self.invoke(execute, case_ids=[self.cases[0]["case_id"]] * 2)
        execute.assert_not_called()

    def test_unsafe_case_path_is_rejected(self):
        for case_id in ("../outside", "..", "CON", "NUL.txt", "case/001"):
            with self.subTest(case_id=case_id), self.assertRaises(ValueError):
                AtomicClaim(self.runs, case_id)

    def test_stale_claim_recovery_requires_matching_token_and_reason(self):
        path = self.runs / self.cases[0]["case_id"] / ".parallel-case-claim.json"
        atomic_write(path, {"token": "old-stopped-worker", "pid": 12345})
        with self.assertRaises(ClaimBusy):
            release_stale_claim(self.runs, self.cases[0]["case_id"], "different-owner", "Confirmed stopped")
        self.assertTrue(path.exists())
        with self.assertRaises(ValueError):
            release_stale_claim(self.runs, self.cases[0]["case_id"], "old-stopped-worker", "")
        receipt = release_stale_claim(self.runs, self.cases[0]["case_id"], "old-stopped-worker", "Synthetic owner verified stopped")
        self.assertFalse(path.exists())
        self.assertEqual(read(receipt)["owner"]["token"], "old-stopped-worker")

    def test_frozen_trainer_and_selector_drift_are_rejected(self):
        guard = FrozenInputs(self.corpus, self.trainer, self.skills, "2026-10-02", "development")
        (self.v2 / "SKILL.md").write_text("Changed after freezing", encoding="utf-8")
        with self.assertRaises(SnapshotDrift):
            guard.verify()
        with patch("parallel_campaign.campaign.execute") as execute, self.assertRaises(SnapshotDrift):
            self.invoke(execute)
        execute.assert_not_called()

    def test_frozen_corpus_answer_and_masked_hashes_are_checked_without_parsing_answer(self):
        guard = FrozenInputs(self.corpus, self.trainer, self.skills, "2026-10-02", "development")
        # Invalid JSON is sufficient to prove verification hashes bytes rather
        # than inspecting the publishing answer.
        answer = self.corpus / self.cases[0]["case_id"] / "answer.json"
        answer.write_text("changed hidden answer bytes", encoding="utf-8")
        with self.assertRaises(SnapshotDrift):
            guard.verify()
        (self.corpus / self.cases[0]["case_id"] / "masked.txt").write_text("changed masked input", encoding="utf-8")
        with self.assertRaises(SnapshotDrift):
            FrozenInputs(self.corpus, self.trainer, self.skills, "2026-10-02", "development")

    def test_snapshot_drift_in_wave_retains_old_ledger_and_cannot_count_complete(self):
        def fake(case, *ignored):
            ledger = self.fake_ledger(case, "completed")
            (self.v2 / "SKILL.md").write_text("Changed mid-wave", encoding="utf-8")
            return ledger

        result = self.invoke(fake, case_ids=[self.cases[0]["case_id"]])
        self.assertEqual(result["status"], "snapshot_drift")
        work = self.runs / self.cases[0]["case_id"]
        ledger = read(work / "ledger.json")
        self.assertEqual(ledger["status"], "contamination_failed")
        self.assertIs(ledger["parallel_snapshot_valid"], False)
        archive = next((work / "parallel-invalidated-ledgers").glob("*.json"))
        self.assertEqual(read(archive)["status"], "completed")
        self.assertEqual(read(self.runs / "run-summary.json")["completed"], 0)

    def test_epoch_changes_cannot_silently_resume(self):
        self.invoke(lambda case, *ignored: self.fake_ledger(case, "completed"), limit=1)
        with patch("parallel_campaign.runner.EFFORT", "high"), self.assertRaises(SnapshotDrift):
            self.invoke(lambda *args: self.fail("Changed model should not execute"))

    def test_model_gate_enforces_four_real_call_slots_without_altering_arguments(self):
        gate = ModelCallGate(4)
        active = 0
        peak = 0
        lock = threading.Lock()

        def operation(argument):
            nonlocal active, peak
            with lock:
                active += 1
                peak = max(peak, active)
            time.sleep(.05)
            with lock:
                active -= 1
            return argument

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(lambda value: gate.call(operation, value), range(8)))
        self.assertEqual(results, list(range(8)))
        self.assertEqual(peak, 4)
        self.assertEqual(gate.peak, 4)
        original = campaign.model_json
        with patch("parallel_campaign.campaign.model_json", return_value=("model result", "receipt")) as real_call:
            with ModelCallGate(4):
                self.assertEqual(campaign.model_json("unchanged prompt", "file.json", timeout=7), ("model result", "receipt"))
            real_call.assert_called_once_with("unchanged prompt", "file.json", timeout=7)
        self.assertIs(campaign.model_json, original)

    def test_ten_stratum_workers_are_distinct_and_global_ten_call_cap_is_enforced(self):
        self.cases = self.allocate(20, strata=list(STRATA))
        barrier = threading.Barrier(10)
        observed = []
        lock = threading.Lock()
        active_calls = 0
        peak_calls = 0

        def actual_model_call(argument):
            nonlocal active_calls, peak_calls
            with lock:
                active_calls += 1
                peak_calls = max(peak_calls, active_calls)
            time.sleep(.02)
            with lock:
                active_calls -= 1
            return argument

        def fake(case, *ignored):
            with lock:
                observed.append((case["case_id"], case["stratum"]))
            barrier.wait(timeout=10)
            # Each article still has two independent blind review calls. The
            # central gate caps their combined concurrency rather than allowing
            # all twenty to consume model slots at once.
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                list(pool.map(campaign.model_json, [case["case_id"] + "-review-1", case["case_id"] + "-review-2"]))
            return self.fake_ledger(case)

        with patch("parallel_campaign.campaign.model_json", side_effect=actual_model_call) as model_call:
            result = self.invoke(fake, limit=20, case_workers=10, model_call_limit=10)
        self.assertEqual(model_call.call_count, 20)
        self.assertEqual(len(observed), 10)
        self.assertEqual(len({item[0] for item in observed}), 10)
        self.assertEqual({item[1] for item in observed}, set(STRATA))
        self.assertLessEqual(peak_calls, 10)
        self.assertLessEqual(result["peak_model_calls"], 10)
        self.assertEqual(result["status"], "decision_pending")
        self.assertEqual(len(result["waves"]), 1)
        self.assertEqual(result["bindings"]["case_workers"], 10)
        self.assertEqual(result["bindings"]["model_call_limit"], 10)
        self.assertEqual(result["bindings"]["primary_stratum_per_wave_max"], 1)

    def test_stratum_queues_never_put_two_same_category_cases_in_one_wave(self):
        cases = self.allocate(30, strata=list(STRATA))
        waves = list(stratum_waves(cases, 5))
        ids = []
        for wave in waves:
            self.assertLessEqual(len(wave), 5)
            self.assertEqual(len({case["stratum"] for case in wave}), len(wave))
            ids.extend(case["case_id"] for case in wave)
        self.assertEqual(set(ids), {case["case_id"] for case in cases})
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual({case["stratum"] for wave in waves[:2] for case in wave}, set(STRATA))

    def test_concurrency_ramp_requires_new_registered_epoch(self):
        self.invoke(lambda case, *ignored: self.fake_ledger(case, "completed"), limit=1)
        with self.assertRaises(SnapshotDrift):
            self.invoke(lambda *args: self.fail("Concurrency drift cannot execute"), case_workers=5, model_call_limit=10)

    def test_rate_limit_and_quota_errors_are_recorded_separately_from_timeout(self):
        self.assertEqual(failure_kind("HTTP 429 Too many requests"), "rate_limit")
        self.assertEqual(failure_kind("You've hit your usage limit"), "quota_or_capacity")
        self.assertEqual(failure_kind("Model call exceeded 1800 seconds"), "timeout")
        self.assertEqual(failure_kind("Model call did not complete"), "other_or_unspecified")

    def test_review_contract_rejects_missing_labels_unhashable_ids_and_wrong_comparison_mode(self):
        valid_system = {"hard_failures": [], "usable_journal_ids": [], "quality_notes": []}
        values = [
            {"systems": {}, "paired_decision": "single"},
            {"systems": {"A": valid_system}, "paired_decision": "single"},
            {"systems": {"A": {**valid_system, "usable_journal_ids": [{}]}, "B": valid_system}, "paired_decision": "A"},
            {"systems": {"A": valid_system, "B": valid_system}, "paired_decision": "single"},
        ]
        for value in values:
            with self.subTest(value=value):
                self.assertTrue(campaign.review_contract(value, expected_labels={"A", "B"}))
        self.assertEqual(campaign.review_contract({"systems": {"A": valid_system}, "paired_decision": "single"}, expected_labels={"A"}), [])
        self.assertEqual(campaign.review_contract({"systems": {"A": valid_system, "B": valid_system}, "paired_decision": "A"}, expected_labels={"A", "B"}), [])

    def test_invalid_identity_value_is_scored_as_retained_schema_failure_without_reveal_crash(self):
        from fixtures import fixture
        sys.path.insert(0, str(ROOT / "skills/medical-journal-selector/scripts"))
        import selector
        evidence = fixture()
        evidence["journals"][0]["facts"]["identity"]["value"] = ["not-an-object"]
        value = {"evidence": evidence, "fit_sequence": [], "report_notes": []}
        failures = campaign.source_audit(value, {"policies": [], "literature": []}, selector)
        self.assertTrue(any("identity" in failure for failure in failures))
        case = self.cases[0]
        work = self.runs / case["case_id"]
        atomic_write(work / "literature.json", {"papers": []})
        atomic_write(work / "generator-packet.json", {"literature": []})
        atomic_write(work / "v2-audit.json", failures)
        ledger = {"case_id": case["case_id"], "stratum": case["stratum"], "split": "development", "identity_map": {"A": "v2"}}
        review = {"systems": {"A": {"hard_failures": [], "usable_journal_ids": [], "quality_notes": []}}, "paired_decision": "single"}
        result = campaign.reveal_case(case, self.corpus, work, ledger, {"v2": value}, [review, review], {}, selector)
        self.assertEqual(result["status"], "revealed")
        self.assertEqual(result["scores"]["v2"]["hard_failures"], failures)
        self.assertFalse(result["scores"]["v2"]["usable"])

    def test_holdout_waves_do_not_reveal_or_make_development_decisions(self):
        self.cases = self.allocate(4, split="holdout")
        self.skills = {"v1": self.v1, "v2": self.v2}
        with patch("parallel_campaign.campaign.reveal_case") as reveal:
            result = self.invoke(lambda case, *ignored: self.fake_ledger(case, "reviewed"), split="holdout", limit=4)
        reveal.assert_not_called()
        self.assertEqual(result["status"], "sealed")
        self.assertEqual(len(result["waves"]), 2)
        self.assertTrue(all(len(wave["case_ids"]) == 2 for wave in result["waves"]))

    def test_holdout_requires_both_versions_before_any_model_call(self):
        self.cases = self.allocate(4, split="holdout")
        with patch("parallel_campaign.campaign.execute") as execute, self.assertRaises(ValueError):
            self.invoke(execute, split="holdout")
        execute.assert_not_called()

    def test_final_reveal_rejects_partial_set_and_failed_original_gate_before_answer_read(self):
        self.cases = self.allocate(4, split="holdout")
        self.skills = {"v1": self.v1, "v2": self.v2}
        with patch("parallel_campaign.campaign.reveal_case") as reveal, self.assertRaises(ValueError):
            reveal_final(self.corpus, self.runs, self.trainer, self.skills, None, "2026-10-02", "holdout-epoch", require_loaded=False)
        reveal.assert_not_called()
        self.cases = self.allocate(50, split="holdout")
        for case in self.cases:
            self.fake_ledger(case, "reviewed")
        with patch("parallel_campaign.require_reveal", side_effect=ValueError("Unsealed original model turn")) as original_gate:
            with patch("parallel_campaign.campaign.reveal_case") as reveal, self.assertRaises(ValueError):
                reveal_final(self.corpus, self.runs, self.trainer, self.skills, None, "2026-10-02", "holdout-epoch", require_loaded=False)
            self.assertEqual(len(original_gate.call_args[0][0]), 50)
            self.assertTrue(original_gate.call_args.kwargs["final"])
            reveal.assert_not_called()

    def test_uniform_but_wrong_final_snapshot_cannot_pass_reveal(self):
        self.cases = self.allocate(50, split="holdout")
        self.skills = {"v1": self.v1, "v2": self.v2}
        for case in self.cases:
            ledger = self.fake_ledger(case, "reviewed")
            ledger["skill_hashes"] = {"v1": "same-but-wrong-version", "v2": "same-but-wrong-version"}
            atomic_write(self.runs / case["case_id"] / "ledger.json", ledger)
        with patch("parallel_campaign.require_reveal", return_value=True), patch("parallel_campaign.campaign.reveal_case") as reveal:
            with self.assertRaises(SnapshotDrift):
                reveal_final(self.corpus, self.runs, self.trainer, self.skills, None, "2026-10-02", "holdout-epoch", require_loaded=False)
            reveal.assert_not_called()


if __name__ == "__main__":
    unittest.main()
