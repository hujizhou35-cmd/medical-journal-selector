#!/usr/bin/env python3
"""Ten stratum queues with frozen inputs, exclusive claims and parent-only summaries.

Selection and review still use campaign.execute and its fresh restricted Codex
calls.  This module schedules them; it never changes prompts or accepts rules.
Run this script from a verified frozen Trainer snapshot, not its editable source.
"""
from __future__ import annotations

import argparse
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from contextlib import AbstractContextManager
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
import threading
import uuid

import campaign
import freeze
import runner
from corpus import STRATA, stamp
from evaluation import require_reveal, summarize

DEFAULT_CASE_WORKERS = 10
DEFAULT_MODEL_CALL_LIMIT = 10
FAILED_STATES = {"infrastructure_failed", "model_failed", "contamination_failed",
                 "input_ineligible", "claim_failed", "scheduler_failed"}


class SnapshotDrift(ValueError):
    pass


class ClaimBusy(RuntimeError):
    pass


def concurrency_settings(case_workers, model_call_limit):
    if not isinstance(case_workers, int) or not 1 <= case_workers <= len(STRATA):
        raise ValueError("case_workers must be between one and ten article strata")
    if not isinstance(model_call_limit, int) or not 1 <= model_call_limit <= 2 * len(STRATA):
        raise ValueError("model_call_limit must be between one and twenty")
    return case_workers, model_call_limit


def stratum_waves(cases, case_workers):
    """At most one case per stratum in a wave; rotate queues fairly at lower caps."""
    queues = {stratum: deque() for stratum in STRATA}
    for case in cases:
        if case["stratum"] not in queues:
            raise ValueError("Case has an unregistered primary article stratum")
        queues[case["stratum"]].append(case)
    rotation = deque(queues)
    while any(queues.values()):
        wave = []
        for _ in range(len(rotation)):
            stratum = rotation.popleft()
            rotation.append(stratum)
            if queues[stratum]:
                wave.append(queues[stratum].popleft())
                if len(wave) == case_workers:
                    break
        yield wave


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic_write(path, value):
    """Readers see a complete old or new JSON document, never a partial write."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    try:
        with temporary.open("x", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def safe_id(value):
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"{prefix}{n}" for prefix in ("COM", "LPT") for n in range(1, 10)}
    if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", value)
            or value.endswith(".") or value.split(".")[0].upper() in reserved):
        raise ValueError("Unsafe case/version identifier")
    return value


def event(runs, case_id, value):
    """Each claim outcome has its own immutable file; no shared append log."""
    path = Path(runs) / "parallel-claim-records" / safe_id(case_id) / (uuid.uuid4().hex + ".json")
    atomic_write(path, {"case_id": case_id, "at": stamp(), **value})
    return path


class AtomicClaim(AbstractContextManager):
    def __init__(self, runs, case_id, scheduler=False):
        self.runs = Path(runs).resolve()
        self.case_id = safe_id(case_id)
        self.work = self.runs if scheduler else self.runs / self.case_id
        self.path = self.work / (".parallel-scheduler-claim.json" if scheduler else ".parallel-case-claim.json")
        self.owner = {"token": uuid.uuid4().hex, "pid": os.getpid(),
                      "host": socket.gethostname(), "thread": threading.get_ident(), "started_at": stamp()}
        self.owned = False

    def __enter__(self):
        self.work.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            try:
                existing = read(self.path)
            except (ValueError, OSError):
                existing = {"status": "owner record unavailable; claim not stolen"}
            receipt = event(self.runs, self.case_id, {"status": "claim_failed", "claim_path": str(self.path),
                            "requester": self.owner, "existing_owner": existing})
            raise ClaimBusy(f"Case/scheduler already claimed; receipt: {receipt}") from exc
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(self.owner, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            self.owned = True
            event(self.runs, self.case_id, {"status": "claimed", "owner": self.owner})
        except BaseException:
            self.path.unlink(missing_ok=True)
            raise
        return self

    def __exit__(self, exception_type, exception, traceback):
        if self.owned:
            if read(self.path).get("token") != self.owner["token"]:
                raise ClaimBusy("Claim ownership changed; refusing to remove another owner's claim")
            event(self.runs, self.case_id, {"status": "released", "owner": self.owner,
                  "exception": str(exception) if exception else None})
            self.path.unlink()
            self.owned = False
        return False


def release_stale_claim(runs, case_id, expected_token, reason, scheduler=False):
    """Explicit recovery only; caller must first confirm the owner has stopped."""
    if not expected_token or not reason.strip():
        raise ValueError("Recovery requires the observed token and an explicit stopped-owner reason")
    claim = AtomicClaim(runs, case_id, scheduler)
    owner = read(claim.path)
    if owner.get("token") != expected_token:
        raise ClaimBusy("Observed claim token changed; recovery refused")
    receipt = event(runs, case_id, {"status": "stale_claim_released", "owner": owner, "reason": reason})
    # A claim is never replaced while present. Recheck immediately before the
    # explicit unlink and retain the old owner in the immutable event receipt.
    if read(claim.path).get("token") != expected_token:
        raise ClaimBusy("Claim changed during recovery")
    claim.path.unlink()
    return receipt


class FrozenInputs:
    def __init__(self, corpus, trainer, skills, as_of, split,
                 case_workers=DEFAULT_CASE_WORKERS, model_call_limit=DEFAULT_MODEL_CALL_LIMIT):
        concurrency_settings(case_workers, model_call_limit)
        self.corpus = Path(corpus).resolve()
        self.trainer = Path(trainer).resolve()
        self.skills = {key: Path(path).resolve() for key, path in skills.items()}
        self.manifest = read(self.corpus / "manifest.json")
        if self.manifest.get("status") != "input_allocation_frozen":
            raise ValueError("Corpus allocation must be frozen")
        self.active_cases = [case for case in self.manifest["cases"] if case["split"] in ("development", "holdout")]
        ids = [safe_id(case["case_id"]) for case in self.active_cases]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate active case IDs in corpus allocation")
        paths = [self.corpus / "manifest.json"]
        for case in self.active_cases:
            work = self.corpus / case["case_id"]
            paths.extend(work / name for name in ("source.xml", "masked.txt", "answer.json"))
            masked_hash = hashlib.sha256((work / "masked.txt").read_text(encoding="utf-8").encode()).hexdigest()
            if masked_hash != case["input_hash"]:
                raise SnapshotDrift("Masked corpus input differs from its allocation hash")
        # Hash source and answers without parsing them. Neither these bytes nor
        # identities enter selection/review contexts or public receipts.
        self.corpus_files = {str(path): sha(path) for path in paths}
        try:
            for folder in [self.trainer, *self.skills.values()]:
                freeze.verify(folder)
        except (ValueError, OSError) as exc:
            raise SnapshotDrift(str(exc)) from exc
        self.snapshot_manifests = {str(folder): sha(folder / "snapshot-manifest.json")
                                   for folder in [self.trainer, *self.skills.values()]}
        self.bindings = {
            "corpus": str(self.corpus), "corpus_manifest_sha256": sha(self.corpus / "manifest.json"),
            "corpus_files_sha256": hashlib.sha256(json.dumps(self.corpus_files, sort_keys=True).encode()).hexdigest(),
            "trainer": str(self.trainer), "skills": {key: str(path) for key, path in self.skills.items()},
            "snapshot_manifest_sha256": self.snapshot_manifests, "date": as_of, "split": split,
            "model": runner.MODEL, "effort": runner.EFFORT, "case_workers": case_workers,
            "wave_size_max": case_workers, "model_call_limit": model_call_limit,
            "primary_stratum_per_wave_max": 1, "stratum_queue_order": list(STRATA),
        }

    def verify(self):
        try:
            if any(sha(path) != expected for path, expected in self.corpus_files.items()):
                raise SnapshotDrift("Frozen corpus changed during scheduler epoch")
            for folder, expected in self.snapshot_manifests.items():
                if sha(Path(folder) / "snapshot-manifest.json") != expected:
                    raise SnapshotDrift("Frozen snapshot manifest changed")
                freeze.verify(folder)
        except (ValueError, OSError) as exc:
            if isinstance(exc, SnapshotDrift):
                raise
            raise SnapshotDrift(str(exc)) from exc
        return True

    def verify_loaded_trainer(self):
        if Path(__file__).resolve().parent != self.trainer / "scripts":
            raise SnapshotDrift("Launch parallel_campaign.py from the frozen Trainer snapshot")
        for module in (campaign, runner, freeze, sys.modules["corpus"], sys.modules["broker"], sys.modules["evaluation"]):
            if Path(module.__file__).resolve().parent != self.trainer / "scripts":
                raise SnapshotDrift("Imported execution module is outside the frozen Trainer")


class ModelCallGate(AbstractContextManager):
    """A process-local ceiling around real calls, without adding model context."""
    def __init__(self, limit=DEFAULT_MODEL_CALL_LIMIT):
        concurrency_settings(1, limit)
        self.semaphore = threading.BoundedSemaphore(limit)
        self.lock = threading.Lock()
        self.active = 0
        self.peak = 0
        self.original = None

    def call(self, function, *args, **kwargs):
        with self.semaphore:
            with self.lock:
                self.active += 1
                self.peak = max(self.peak, self.active)
            try:
                return function(*args, **kwargs)
            finally:
                with self.lock:
                    self.active -= 1

    def __enter__(self):
        self.original = campaign.model_json
        campaign.model_json = lambda *args, **kwargs: self.call(self.original, *args, **kwargs)
        return self

    def __exit__(self, *ignored):
        campaign.model_json = self.original
        return False


def register_epoch(runs, eval_version, bindings):
    path = Path(runs) / "parallel-epochs" / (safe_id(eval_version) + ".json")
    if path.exists():
        if read(path)["bindings"] != bindings:
            raise SnapshotDrift("Epoch settings changed; register a new eval_version at a boundary")
    else:
        atomic_write(path, {"eval_version": eval_version, "registered_at": stamp(), "bindings": bindings})
    return path


def pending_decisions(cases, runs):
    pending = []
    for case in cases:
        path = Path(runs) / case["case_id"] / "ledger.json"
        if path.exists():
            ledger = read(path)
            if ledger.get("status") in ("diagnosed", "revealed", "reviewed") and ledger.get("lesson_status") != "completed":
                pending.append(case["case_id"])
    return pending


def failure_kind(message):
    """Describe retained errors for operations; never change their score/state."""
    text = (message or "").casefold()
    if "429" in text or "rate limit" in text or "too many requests" in text:
        return "rate_limit"
    if "usage limit" in text or "quota" in text or "capacity" in text:
        return "quota_or_capacity"
    if "timeout" in text or "timed out" in text or "exceeded" in text:
        return "timeout"
    return "other_or_unspecified" if text else None


def _execute_claimed(case, corpus, runs, skills, selector, as_of, guard, wave_id, execute):
    receipt = {"case_id": case["case_id"], "wave_id": wave_id, "started_at": stamp(), "executed": False,
               "status": "scheduler_failed", "failure": None}
    try:
        with AtomicClaim(runs, case["case_id"]):
            guard.verify()
            receipt["executed"] = True
            ledger = execute(case, corpus, runs, skills, selector, as_of)
            guard.verify()
            receipt.update(status=ledger["status"], lesson_status=ledger.get("lesson_status"), failure=ledger.get("failure"))
    except ClaimBusy as exc:
        receipt.update(status="claim_failed", failure=str(exc))
    except SnapshotDrift as exc:
        receipt.update(status="contamination_failed", failure=str(exc), snapshot_drift=True)
    except Exception as exc:
        receipt.update(status="scheduler_failed", failure=str(exc))
    receipt["sealed_at"] = stamp()
    receipt["failure_kind"] = failure_kind(receipt.get("failure"))
    receipt["failure_kind_basis"] = "Classification of retained failure text only; original model/transport receipts remain authoritative"
    path = Path(runs) / "parallel-worker-receipts" / wave_id / (case["case_id"] + ".json")
    atomic_write(path, receipt)
    return receipt


def invalidate_wave(cases, runs, wave_id, reason, receipts):
    """After workers drain, retain old ledgers and prevent polluted completion."""
    executed = {item["case_id"] for item in receipts if item.get("executed")}
    for case in cases:
        if case["case_id"] not in executed:
            continue # Never edit a folder whose claim belongs to another scheduler.
        work = Path(runs) / case["case_id"]
        path = work / "ledger.json"
        if not path.exists():
            continue
        ledger = read(path)
        atomic_write(work / "parallel-invalidated-ledgers" / (wave_id + ".json"), ledger)
        ledger.update(status="contamination_failed", failure=reason, failed_at=stamp(),
                      parallel_snapshot_valid=False, invalidated_wave=wave_id)
        atomic_write(path, ledger)


def run_campaign(corpus, runs, trainer, skills, selector, as_of, eval_version,
                 split="development", limit=10, case_ids=None, execute=None, require_loaded=True,
                 case_workers=DEFAULT_CASE_WORKERS, model_call_limit=DEFAULT_MODEL_CALL_LIMIT):
    if split not in ("development", "holdout") or limit < 1:
        raise ValueError("A positive limit and valid split are required")
    if split == "holdout" and set(skills) != {"v1", "v2"}:
        raise ValueError("Holdout generation requires both frozen variants")
    corpus, runs = Path(corpus).resolve(), Path(runs).resolve()
    guard = FrozenInputs(corpus, trainer, skills, as_of, split, case_workers, model_call_limit)
    guard.verify()
    if require_loaded:
        guard.verify_loaded_trainer()
    execute = execute or campaign.execute
    selected = [case for case in guard.active_cases if case["split"] == split]
    selected.sort(key=lambda case: (int(case["case_id"].split("-")[-1]), case["stratum"]))
    if case_ids is not None:
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Duplicate requested case IDs")
        by_id = {case["case_id"]: case for case in selected}
        if any(case_id not in by_id for case_id in case_ids):
            raise ValueError("Requested case is outside the frozen selected split")
        selected = [by_id[case_id] for case_id in case_ids]
    result = {"eval_version": eval_version, "split": split, "status": "prepared", "waves": [],
              "bindings": guard.bindings, "peak_model_calls": 0, "started_at": stamp(),
              "model_concurrency_measurement": "Active model_json operations; a cached checkpoint can occupy a slot without a new model request"}
    with AtomicClaim(runs, "scheduler", scheduler=True):
        register_epoch(runs, eval_version, guard.bindings)
        # Development waves never proceed past an unresolved preceding lesson.
        pending = pending_decisions([case for case in guard.active_cases if case["split"] == "development"], runs) if split == "development" else []
        if pending:
            result.update(status="decision_pending", pending_decisions=pending)
            atomic_write(runs / "parallel-summary.json", result)
            return result
        remaining = []
        for case in selected:
            path = runs / case["case_id"] / "ledger.json"
            ledger = read(path) if path.exists() else {}
            if ledger.get("status") == "completed" or (split == "holdout" and ledger.get("status") == "reviewed"):
                continue
            remaining.append(case)
        scheduled = 0
        with ModelCallGate(model_call_limit) as gate:
            for wave in stratum_waves(remaining, case_workers):
                wave = wave[:limit - scheduled]
                if not wave:
                    break
                if (runs / "PAUSE").exists():
                    result["status"] = "paused_at_boundary"
                    break
                guard.verify()
                scheduled += len(wave)
                wave_id = uuid.uuid4().hex
                record = {"wave_id": wave_id, "eval_version": eval_version, "case_ids": [case["case_id"] for case in wave],
                          "strata": [case["stratum"] for case in wave],
                          "started_at": stamp(), "status": "running", "bindings": guard.bindings}
                atomic_write(runs / "parallel-waves" / (wave_id + ".json"), record)
                # Only workers write case folders. This parent waits for all
                # futures before reading ledgers or writing any shared summary.
                with ThreadPoolExecutor(max_workers=case_workers) as pool:
                    futures = [pool.submit(_execute_claimed, case, corpus, runs, skills, selector,
                                           as_of, guard, wave_id, execute) for case in wave]
                    receipts = [future.result() for future in futures]
                try:
                    guard.verify()
                except SnapshotDrift as exc:
                    invalidate_wave(wave, runs, wave_id, str(exc), receipts)
                    record.update(status="snapshot_drift", failure=str(exc))
                else:
                    record["status"] = "failed" if any(item["status"] in FAILED_STATES for item in receipts) else "sealed"
                record.update(receipts=receipts, sealed_at=stamp(), peak_model_calls=gate.peak)
                atomic_write(runs / "parallel-waves" / (wave_id + ".json"), record)
                result["waves"].append(record)
                ledgers = [read(runs / case["case_id"] / "ledger.json") for case in guard.active_cases
                           if case["split"] == split and (runs / case["case_id"] / "ledger.json").exists()]
                atomic_write(runs / "run-summary.json", summarize(ledgers))
                result["peak_model_calls"] = gate.peak
                if record["status"] != "sealed":
                    result["status"] = record["status"]
                    break
                if split == "development":
                    pending = pending_decisions(wave, runs)
                    if pending:
                        result.update(status="decision_pending", pending_decisions=pending)
                        break
                result["status"] = "sealed"
                atomic_write(runs / "parallel-summary.json", result)
        result["finished_at"] = stamp()
        if not remaining:
            result["status"] = "nothing_to_run"
        atomic_write(runs / "parallel-summary.json", result)
    return result


def reveal_final(corpus, runs, trainer, skills, selector, as_of, eval_version, require_loaded=True,
                 case_workers=DEFAULT_CASE_WORKERS, model_call_limit=DEFAULT_MODEL_CALL_LIMIT):
    """Preserve the existing all-50 seal gate; no per-wave holdout reveal."""
    if set(skills) != {"v1", "v2"}:
        raise ValueError("Final reveal requires both frozen variants")
    guard = FrozenInputs(corpus, trainer, skills, as_of, "holdout", case_workers, model_call_limit)
    guard.verify()
    if require_loaded:
        guard.verify_loaded_trainer()
    cases = [case for case in guard.active_cases if case["split"] == "holdout"]
    if len(cases) != 50:
        raise ValueError("Final reveal requires the entire allocated 50-case holdout")
    runs = Path(runs).resolve()
    with AtomicClaim(runs, "scheduler", scheduler=True):
        register_epoch(runs, eval_version, guard.bindings)
        if any((runs / case["case_id"] / ".parallel-case-claim.json").exists() for case in cases):
            raise ClaimBusy("A holdout worker is still claimed; no answer reveal")
        records = [read(runs / case["case_id"] / "ledger.json") for case in cases]
        if any(record.get("parallel_snapshot_valid") is False for record in records):
            raise SnapshotDrift("A holdout wave was invalidated")
        require_reveal(records, final=True)
        # Additional drift checks cannot weaken require_reveal. All cases must
        # have used one frozen version/protocol/configuration before any answer
        # is read by the original reveal_case implementation.
        for variant in ("v1", "v2"):
            hashes = {record.get("skill_hashes", {}).get(variant) for record in records}
            expected = hashlib.sha256(campaign.skill_packet(skills[variant]).encode()).hexdigest()
            if hashes != {expected}:
                raise SnapshotDrift("Final Skill snapshot changed or was not recorded")
        protocols = {json.dumps(record.get("protocol_hashes"), sort_keys=True) for record in records}
        expected_protocol = json.dumps({path.name: sha(path) for path in (guard.trainer / "scripts").glob("*.py")}, sort_keys=True)
        configurations = {(item.get("model"), item.get("effort")) for record in records
                          for item in record["generations"] + record["reviews"]}
        if protocols != {expected_protocol} or configurations != {(runner.MODEL, runner.EFFORT)}:
            raise SnapshotDrift("Final protocol/model configuration changed or was not recorded")
        for case, ledger in zip(cases, records):
            work = runs / case["case_id"]
            outputs = {name: read(work / (name + "-selection.json")) for name in ("v1", "v2")}
            reviews = [read(work / f"review-{index}.json") for index in range(1, len(ledger["reviews"]) + 1)]
            campaign.reveal_case(case, corpus, work, ledger, outputs, reviews, read(work / "fixed-baselines.json"), selector)
        result = summarize([read(runs / case["case_id"] / "ledger.json") for case in cases])
        atomic_write(runs / "run-summary.json", result)
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path)
    parser.add_argument("--runs", type=Path, required=True)
    parser.add_argument("--trainer-snapshot", type=Path)
    parser.add_argument("--selector-skill", type=Path)
    parser.add_argument("--baseline-skill", type=Path)
    parser.add_argument("--eval-version")
    parser.add_argument("--date")
    parser.add_argument("--split", choices=("development", "holdout"), default="development")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--case-workers", type=int, default=DEFAULT_CASE_WORKERS,
                        help="Maximum different article strata per wave (1-10; initial smoke: 2)")
    parser.add_argument("--model-call-limit", type=int, default=DEFAULT_MODEL_CALL_LIMIT,
                        help="Global model-call ceiling (1-20; initial smoke: 4)")
    parser.add_argument("--case-id", action="append")
    parser.add_argument("--reveal-final", action="store_true")
    parser.add_argument("--release-claim", help="Case ID or scheduler; confirm its owner has stopped first")
    parser.add_argument("--claim-token")
    parser.add_argument("--reason", default="")
    args = parser.parse_args()
    if args.release_claim:
        receipt = release_stale_claim(args.runs, args.release_claim, args.claim_token, args.reason, args.release_claim == "scheduler")
        print(str(receipt))
        return
    if not all((args.corpus, args.trainer_snapshot, args.selector_skill, args.eval_version, args.date)):
        parser.error("Execution/reveal requires --corpus, --trainer-snapshot, --selector-skill, --eval-version and --date")
    sys.path.insert(0, str((args.selector_skill / "scripts").resolve()))
    import selector
    if Path(selector.__file__).resolve().parent != (args.selector_skill / "scripts").resolve():
        raise SnapshotDrift("Imported Selector is outside the frozen candidate snapshot")
    skills = {"v2": args.selector_skill}
    if args.baseline_skill:
        skills = {"v1": args.baseline_skill, **skills}
    if args.reveal_final:
        if args.split != "holdout":
            parser.error("Final reveal only applies to holdout")
        result = reveal_final(args.corpus, args.runs, args.trainer_snapshot, skills, selector, args.date, args.eval_version,
                              case_workers=args.case_workers, model_call_limit=args.model_call_limit)
    else:
        result = run_campaign(args.corpus, args.runs, args.trainer_snapshot, skills, selector, args.date,
                              args.eval_version, args.split, args.limit, args.case_id,
                              case_workers=args.case_workers, model_call_limit=args.model_call_limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") in ("failed", "snapshot_drift"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
