"""Four-comparator blind review inputs, private mappings and answer-free seals.

The deterministic comparators retain their existing ranking. They acquire no
generated fact envelopes, policy conclusions, production routes or model calls.
Two independent reviewer contexts each inspect all four results and all six
pairs. Every reviewer has its own deterministic label mapping; a V1/V2 decision
is extracted from that pair, never inferred from an overall winner.
"""
from __future__ import annotations

import copy
import hashlib
import itertools
import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

COMPARATORS = ("keyword", "abstract", "v1", "v2")
LABELS = ("A", "B", "C", "D")
CONTRACT = "four-comparator-v1"
SEED = 20261002
MANIFEST_NAME = "review-bundle-seal.json"
_META_KEYS = frozenset((
    "run", "schema_version", "variant", "comparator", "system_name",
    "skill_name", "skill_version", "skill_hash", "skill_hashes", "model_name",
    "model_id", "reasoning_effort", "context_id", "isolation",
    "prompt", "protocol_hashes", "output_hash", "generation_metadata",
))


class ReviewBundleError(ValueError):
    pass


def stamp():
    return datetime.now(timezone.utc).isoformat()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as exc:
        raise ReviewBundleError("Review bundle file unavailable: "+str(path)) from exc


def _read(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReviewBundleError("Review bundle JSON unavailable: "+str(path)) from exc


def _write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def anonymize(value, hidden_tokens=(), redact_narrative=True):
    """Remove generation metadata, preserving scientific models and versions.

    A generic clinical `model` or software `version` is not generation metadata.
    Exact host/model/Skill identifiers supplied by the caller are also redacted
    from narrative strings, without deleting source dates or scientific facts.
    """
    if isinstance(value, dict):
        # Fact values and verbatim evidence are scientific/source content, not
        # generation metadata. Redacting a model name from a source quotation
        # would create a false failed-source audit for a study about that model.
        return {key: (copy.deepcopy(item) if key in ("value", "evidence", "model", "version", "provider")
                      else anonymize(item, hidden_tokens, redact_narrative)) for key, item in value.items()
                if key not in _META_KEYS}
    if isinstance(value, list):
        return [anonymize(item, hidden_tokens, redact_narrative) for item in value]
    if isinstance(value, str):
        if not redact_narrative:
            return value
        result = value
        for token in sorted({str(t) for t in hidden_tokens if t}, key=len, reverse=True):
            result = re.sub(re.escape(token), "[identity hidden]", result, flags=re.I)
        result = re.sub(r"\b(?:skill|system|variant|comparator)\s+(?:version\s+)?v[12]\b|"
                        r"\bv[12]\s+(?:skill|system|variant|comparator)\b|"
                        r"\bmedical-journal-selector(?:-v[12])?\b", "[identity hidden]", result, flags=re.I)
        return result
    return copy.deepcopy(value)


def _hidden_tokens(outputs):
    tokens = []
    for output in outputs.values():
        run = output.get("evidence", {}).get("run", {})
        if isinstance(run, dict):
            tokens.extend(v for k, v in run.items()
                          if k in ("model", "model_name", "model_id", "skill_name", "skill_version")
                          and isinstance(v, str) and len(v) > 2)
    return tokens


def build_result_cards(packet, baselines, outputs):
    """Make four honest result cards using only existing candidates and sources."""
    if set(outputs) != {"v1", "v2"} or set(baselines) != {"keyword", "abstract"}:
        raise ReviewBundleError("Four-comparator review requires exactly two fixed rankings and V1/V2 outputs")
    candidates = {}
    for paper in packet.get("literature", []):
        jid = paper.get("journal_id")
        if not isinstance(jid, str) or not isinstance(paper.get("journal"), str):
            raise ReviewBundleError("Candidate identity is missing from the shared packet")
        candidates.setdefault(jid, {"title": paper["journal"], "sources": []})
        # Metadata is supplied provenance, not an independently verified policy.
        reference = {key: copy.deepcopy(paper[key]) for key in
                     ("url", "record_url", "checked_at", "source_type", "read_extent", "title", "year")
                     if key in paper}
        candidates[jid]["sources"].append(reference)
    tokens = _hidden_tokens(outputs)
    cards = {}
    for variant in COMPARATORS:
        baseline = variant in baselines
        sequence = ([item.get("journal_id") for item in baselines[variant]] if baseline
                    else outputs[variant].get("fit_sequence", []))
        if (not isinstance(sequence, list) or not all(isinstance(jid, str) for jid in sequence)
                or len(sequence) != len(set(sequence)) or len(sequence) > 10
                or (baseline and any(jid not in candidates for jid in sequence))):
            raise ReviewBundleError("Result ranking contains an unknown, duplicate or invalid candidate")
        claimed_titles = {item.get("id"): item.get("title") for item in
                          outputs.get(variant, {}).get("evidence", {}).get("journals", []) if isinstance(item, dict)}
        ranked = [{"rank": index, "journal_id": jid,
                   "title": candidates[jid]["title"] if jid in candidates else claimed_titles.get(jid),
                   "present_in_shared_candidate_pool": jid in candidates}
                  for index, jid in enumerate(sequence, 1)]
        if baseline:
            claims = {"journals": [], "profile": None, "constraints": None}
            notes = ["The supplied order is a deterministic text-match ranking. No independent "
                     "policy assessment or journal fact envelopes were produced by this result."]
            limits = ["Missing current policy facts remain unknown in this result. Review the shared "
                      "official snapshots for actual compatibility; similar published articles alone "
                      "do not establish permission. The order has not been revised using the other results."]
        else:
            evidence = outputs[variant].get("evidence", {})
            claims = {key: anonymize(evidence.get(key), tokens, redact_narrative=(key == "journals"))
                      for key in ("journals", "profile", "constraints")}
            notes = anonymize(outputs[variant].get("report_notes", []), tokens)
            limits = ["Assess each submitted claim against the shared captured sources; a claim's "
                      "verified label is not itself verification."]
        cards[variant] = {"ranked_candidates": ranked, "claims": claims,
                          "notes": notes, "limitations": limits,
                          "bibliographic_sources": [{"journal_id": jid, "records": candidates.get(jid, {}).get("sources", [])}
                                                    for jid in sequence]}
    return cards


def make_review_bundle(cards, case_id, reviewer_index, seed=SEED):
    if set(cards) != set(COMPARATORS) or reviewer_index not in (1, 2, 3):
        raise ReviewBundleError("Review bundle needs all four comparators and reviewer index 1, 2 or 3")
    seed_material = f"{CONTRACT}|{seed}|{case_id}|reviewer-{reviewer_index}"
    seed_hash = hashlib.sha256(seed_material.encode("utf-8")).hexdigest()
    order = list(COMPARATORS)
    random.Random(int(seed_hash, 16)).shuffle(order)
    mapping = dict(zip(LABELS, order))
    # Independent deterministic randomisation can occasionally coincide. Avoid
    # repeating an earlier whole order while retaining the recorded seed.
    earlier = [make_review_bundle(cards, case_id, index, seed)[1]["displayed_comparators"]
               for index in range(1, reviewer_index)]
    while order in earlier:
        order = order[1:]+order[:1]
    mapping = dict(zip(LABELS, order))
    public = {"display_order": list(LABELS),
              "systems": {label: copy.deepcopy(cards[variant]) for label, variant in mapping.items()}}
    private = {"contract": CONTRACT, "reviewer_index": reviewer_index,
               "seed": seed, "seed_hash": seed_hash, "label_to_comparator": mapping,
               "displayed_comparators": order,
               "payload_sha256": hashlib.sha256(_canonical(public).encode("utf-8")).hexdigest()}
    return public, private


def review_contract(value, expected_labels=LABELS, allowed_journal_ids=None):
    """Require all four systems and the six complete, unordered comparisons."""
    labels = set(expected_labels)
    if not isinstance(value, dict) or not isinstance(value.get("systems"), dict):
        return ["review must contain a systems object"]
    errors = []
    if len(labels) != 4 or set(value["systems"]) != labels:
        errors.append("review systems must contain exactly the four supplied labels")
    for label, system in value["systems"].items():
        if not isinstance(system, dict):
            errors.append(str(label)+" review must be an object")
            continue
        for key in ("hard_failures", "usable_journal_ids", "quality_notes"):
            if not isinstance(system.get(key), list):
                errors.append(str(label)+"."+key+" must be a list")
        ids = system.get("usable_journal_ids")
        if isinstance(ids, list):
            if not all(isinstance(jid, str) for jid in ids) or len(ids) != len(set(jid for jid in ids if isinstance(jid, str))):
                errors.append(str(label)+" usable ids must be unique strings")
            elif allowed_journal_ids is not None and any(jid not in allowed_journal_ids.get(label, ()) for jid in ids):
                errors.append(str(label)+" reviewer inserted a journal absent from that result's ranking")
        failures = system.get("hard_failures")
        if isinstance(failures, list) and not all(isinstance(item, dict) and
                all(isinstance(item.get(key), str) for key in ("claim", "source", "reason")) for item in failures):
            errors.append(str(label)+" hard failures require claim/source/reason strings")
        notes = system.get("quality_notes")
        if isinstance(notes, list) and not all(isinstance(note, str) for note in notes):
            errors.append(str(label)+" quality notes must be strings")
        assessment = system.get("ranking_assessment")
        if (not isinstance(assessment, dict) or assessment.get("judgment") not in
                ("supported", "partly_supported", "unsupported", "unresolved", "empty") or
                not isinstance(assessment.get("reason"), str) or not assessment.get("reason", "").strip() or
                not isinstance(assessment.get("sources"), list) or
                not all(isinstance(source, str) for source in assessment.get("sources", []))):
            errors.append(str(label)+" requires a source-grounded ranking_assessment")
        elif allowed_journal_ids is not None and allowed_journal_ids.get(label) and assessment["judgment"] == "empty":
            errors.append(str(label)+" cannot label a supplied nonempty ranking as empty")
    pairs = value.get("pairwise_decisions")
    if not isinstance(pairs, list):
        return errors+["review requires six pairwise_decisions; an overall winner cannot replace them"]
    seen = set()
    for item in pairs:
        if not isinstance(item, dict):
            errors.append("pairwise decision must be an object")
            continue
        left, right = item.get("left"), item.get("right")
        if not isinstance(left, str) or not isinstance(right, str) or left not in labels or right not in labels or left == right:
            errors.append("pairwise decision must name two different supplied labels")
            continue
        pair = tuple(sorted((left, right)))
        if pair in seen:
            errors.append("duplicate unordered pairwise decision")
        seen.add(pair)
        if item.get("decision") not in (left, right, "tie", "unresolved"):
            errors.append("pairwise winner must belong to that pair, or be tie/unresolved")
        if not isinstance(item.get("reason"), str):
            errors.append("pairwise decision needs a source-grounded reason string")
    if seen != set(itertools.combinations(sorted(labels), 2)) or len(pairs) != 6:
        errors.append("pairwise_decisions must cover all six unordered pairs exactly once")
    return errors


def _mapping(private):
    mapping = private.get("label_to_comparator", {})
    if set(mapping) != set(LABELS) or len(set(mapping.values())) != 4 or set(mapping.values()) != set(COMPARATORS):
        raise ReviewBundleError("Private label mapping is not a four-comparator bijection")
    return mapping


def normalize_review(review, private):
    errors = review_contract(review)
    if errors:
        raise ReviewBundleError("Invalid four-comparator review: "+"; ".join(errors))
    mapping = _mapping(private)
    pairs = []
    for item in review["pairwise_decisions"]:
        left, right = sorted((mapping[item["left"]], mapping[item["right"]]), key=COMPARATORS.index)
        pairs.append({"left": left, "right": right,
                      "decision": mapping.get(item["decision"], item["decision"]), "reason": item["reason"]})
    pairs.sort(key=lambda item: (COMPARATORS.index(item["left"]), COMPARATORS.index(item["right"])))
    return {"systems": {mapping[label]: copy.deepcopy(value) for label, value in review["systems"].items()},
            "pairwise_decisions": pairs}


def extract_pairwise_decision(review, private=None, left="v1", right="v2"):
    normalized = normalize_review(review, private) if private is not None else review
    matches = [item for item in normalized["pairwise_decisions"]
               if {item["left"], item["right"]} == {left, right}]
    if len(matches) != 1:
        raise ReviewBundleError("Requested pair is missing or duplicated")
    return matches[0]["decision"]


def review_conflicts(reviews, private_maps=None):
    if len(reviews) != 2:
        raise ReviewBundleError("Conflict detection needs exactly the two independent reviews")
    values = ([normalize_review(review, private) for review, private in zip(reviews, private_maps)]
              if private_maps is not None else reviews)
    if private_maps is not None and len(private_maps) != 2:
        raise ReviewBundleError("Conflict detection needs two private label mappings")
    a, b = values
    conflicts = []
    for variant in COMPARATORS:
        first, second = a["systems"][variant], b["systems"][variant]
        if set(first["usable_journal_ids"]) != set(second["usable_journal_ids"]):
            conflicts.append({"system": variant, "field": "usable_journal_ids"})
        failure_keys = lambda system: {_canonical({k: failure[k] for k in ("claim", "source", "reason")})
                                       for failure in system["hard_failures"]}
        if failure_keys(first) != failure_keys(second):
            conflicts.append({"system": variant, "field": "hard_failures"})
        if first["ranking_assessment"]["judgment"] != second["ranking_assessment"]["judgment"]:
            conflicts.append({"system": variant, "field": "ranking_assessment"})
    for left, right in itertools.combinations(COMPARATORS, 2):
        if extract_pairwise_decision(a, left=left, right=right) != extract_pairwise_decision(b, left=left, right=right):
            conflicts.append({"pair": [left, right], "field": "pairwise_decision"})
    return conflicts


def anonymize_normalized_reviews(reviews, private, original_private_maps=None):
    """Express prior adjudication material in the third reviewer's labels."""
    inverse = {variant: label for label, variant in _mapping(private).items()}
    values = []
    if original_private_maps is not None and len(original_private_maps) != len(reviews):
        raise ReviewBundleError("Adjudication requires one original mapping per quoted review")
    for index, review in enumerate(reviews):
        value = {"systems": {inverse[variant]: copy.deepcopy(value) for variant, value in review["systems"].items()},
                       "pairwise_decisions": [{"left": inverse[pair["left"]], "right": inverse[pair["right"]],
                                               "decision": inverse.get(pair["decision"], pair["decision"]),
                                               "reason": pair["reason"]} for pair in review["pairwise_decisions"]]}
        if original_private_maps is not None:
            # Never rewrite free prose or quoted biomedical text. Preserve it
            # with an explicit anonymous translation for any original A-D
            # narrative references, while structural labels use current order.
            value["quoted_narrative_label_translation"] = {
                label: inverse[variant] for label, variant in _mapping(original_private_maps[index]).items()}
        values.append(value)
    return values


def seal_review_bundles(work, case_id, packet, baselines, outputs, preparation_binding):
    """Pin shared prep, original rankings, outputs, cards and three fixed orders."""
    work = Path(work)
    manifest_path = work/MANIFEST_NAME
    if manifest_path.exists():
        raise ReviewBundleError("Existing review bundle needs its original ledger binding; cannot retrofit a seal")
    if any((work/f"review-{index}.json.record.json").exists() or (work/f"review-{index}.json.input.txt").exists()
           or (work/f"review-{index}.json").exists() for index in (1, 2, 3)):
        raise ReviewBundleError("Cannot create review bundle after a review request/output exists")
    cards = build_result_cards(packet, baselines, outputs)
    paths = ["preparation-seal.json", "generator-packet.json", "fixed-baselines.json", "v1-selection.json", "v2-selection.json"]
    entries = []
    for variant in COMPARATORS:
        name = variant+"-review-result.json"
        _write(work/name, cards[variant])
        paths.append(name)
    for index in (1, 2, 3):
        public, private = make_review_bundle(cards, case_id, index)
        payload_name, private_name = f"review-{index}.bundle.json", f"review-{index}.identity-map.json"
        _write(work/payload_name, public)
        _write(work/private_name, private)
        paths.extend((payload_name, private_name))
        entries.append({"reviewer_index": index, "payload_path": str((work/payload_name).resolve()),
                        "private_map_path": str((work/private_name).resolve()), "systems": list(COMPARATORS)})
    sealed_at = stamp()
    manifest = {"contract": CONTRACT, "case_id": case_id, "sealed_at": sealed_at,
                "preparation_binding": copy.deepcopy(preparation_binding),
                "files": {name: _hash(work/name) for name in paths}, "review_bundles": entries}
    _write(manifest_path, manifest)
    return {"path": str(manifest_path.resolve()), "manifest_hash": _hash(manifest_path),
            "sealed_at": sealed_at, "contract": CONTRACT}, entries


def verify_review_bundle_seal(work, binding, case_id=None, preparation_binding=None):
    work = Path(work).resolve()
    if not isinstance(binding, dict) or binding.get("contract") != CONTRACT or not binding.get("manifest_hash"):
        raise ReviewBundleError("Missing original four-comparator review bundle seal binding")
    path = Path(binding.get("path", ""))
    if path.resolve() != work/MANIFEST_NAME or _hash(path) != binding["manifest_hash"]:
        raise ReviewBundleError("Review bundle manifest changed or moved after sealing")
    manifest = _read(path)
    if manifest.get("contract") != CONTRACT or (case_id is not None and manifest.get("case_id") != case_id):
        raise ReviewBundleError("Review bundle case/contract mismatch")
    if manifest.get("sealed_at") != binding.get("sealed_at"):
        raise ReviewBundleError("Review bundle original seal timestamp mismatch")
    if preparation_binding is not None and manifest.get("preparation_binding") != preparation_binding:
        raise ReviewBundleError("Review bundle original preparation binding changed")
    required = {"preparation-seal.json", "generator-packet.json", "fixed-baselines.json", "v1-selection.json", "v2-selection.json"}
    required.update(variant+"-review-result.json" for variant in COMPARATORS)
    required.update(f"review-{index}.{kind}.json" for index in (1, 2, 3) for kind in ("bundle", "identity-map"))
    if set(manifest.get("files", {})) != required:
        raise ReviewBundleError("Review bundle seal does not pin every required input/result/map")
    for name, expected in manifest["files"].items():
        if _hash(work/name) != expected:
            raise ReviewBundleError("Review bundle file changed after sealing: "+name)
    cards = {variant: _read(work/(variant+"-review-result.json")) for variant in COMPARATORS}
    originals = build_result_cards(_read(work/"generator-packet.json"), _read(work/"fixed-baselines.json"),
                                   {variant: _read(work/(variant+"-selection.json")) for variant in ("v1", "v2")})
    if cards != originals:
        raise ReviewBundleError("Review cards do not faithfully represent the sealed original results")
    entries = manifest.get("review_bundles", [])
    if len(entries) != 3 or [entry.get("reviewer_index") for entry in entries] != [1, 2, 3]:
        raise ReviewBundleError("Review bundle requires three fixed reviewer orders")
    for entry in entries:
        index = entry["reviewer_index"]
        if (entry.get("systems") != list(COMPARATORS) or
                Path(entry.get("payload_path", "")).resolve() != work/f"review-{index}.bundle.json" or
                Path(entry.get("private_map_path", "")).resolve() != work/f"review-{index}.identity-map.json"):
            raise ReviewBundleError("Review bundle artifact path/coverage mismatch")
        expected_public, expected_private = make_review_bundle(cards, manifest["case_id"], index)
        if _read(entry["payload_path"]) != expected_public or _read(entry["private_map_path"]) != expected_private:
            raise ReviewBundleError("Review bundle order/mapping is not the sealed deterministic order")
    return manifest


def require_final_review_bundles(records, runs, expected_count=50):
    """Answer-free final gate: all four results were shown in each actual review."""
    if expected_count is not None and len(records) != expected_count:
        raise ReviewBundleError("Final four-comparator gate requires exactly the registered case count")
    ids = [ledger.get("case_id") for ledger in records]
    if not all(isinstance(case_id, str) and case_id for case_id in ids) or len(ids) != len(set(ids)):
        raise ReviewBundleError("Final four-comparator cases must have distinct allocated identities")
    for ledger in records:
        work = (Path(runs)/ledger["case_id"]).resolve()
        if work.parent != Path(runs).resolve():
            raise ReviewBundleError("Final review bundle is outside its allocated case directory")
        manifest = verify_review_bundle_seal(work, ledger.get("review_bundle_seal"),
                                            ledger["case_id"], ledger.get("preparation_seal"))
        if not isinstance(ledger.get("preparation_seal"), dict):
            raise ReviewBundleError("Final four-comparator ledger lacks its original preparation binding")
        if ledger.get("review_bundle_contract") != CONTRACT or ledger.get("review_bundles") != manifest["review_bundles"]:
            raise ReviewBundleError("Final ledger lacks the original four-comparator review mappings")
        reviews = ledger.get("reviews", [])
        if len(reviews) not in (2, 3):
            raise ReviewBundleError("Final case needs two actual blind reviews and at most one adjudication")
        for index, artifact in enumerate(reviews, 1):
            expected_output = work/f"review-{index}.json"
            if Path(artifact.get("path", "")).resolve() != expected_output.resolve() or _hash(expected_output) != artifact.get("output_hash"):
                raise ReviewBundleError("Actual review output changed or mapping/order mismatched")
            payload = _read(work/f"review-{index}.bundle.json")
            private = _read(work/f"review-{index}.identity-map.json")
            allowed = {label: [item["journal_id"] for item in card["ranked_candidates"]]
                       for label, card in payload["systems"].items()}
            errors = review_contract(_read(expected_output), allowed_journal_ids=allowed)
            if errors:
                raise ReviewBundleError("Final review does not cover four results and six pairs: "+"; ".join(errors))
            normalize_review(_read(expected_output), private)
            prompt_path = expected_output.with_suffix(expected_output.suffix+".input.txt")
            prompt = prompt_path.read_text(encoding="utf-8")
            if json.dumps(payload, ensure_ascii=False) not in prompt:
                raise ReviewBundleError("Actual review request did not contain the sealed four-result payload")
            if json.dumps(_read(work/"generator-packet.json"), ensure_ascii=False) not in prompt:
                raise ReviewBundleError("Actual four-result review request omitted the sealed common manuscript/source packet")
            record = _read(expected_output.with_suffix(expected_output.suffix+".record.json"))
            # These calls use no response-schema file. This is the same input
            # identity as runner.run's controlled-packet v3 protocol; drift must
            # fail rather than accepting a request file rewritten after a call.
            expected_input = hashlib.sha256(prompt_path.read_bytes()+record.get("model", "").encode()+
                                            record.get("effort", "").encode()+
                                            b"controlled-packet-env-closed-tools-disabled-v3").hexdigest()
            if record.get("input_hash") != expected_input:
                raise ReviewBundleError("Actual four-result review request differs from its original model receipt")
            if datetime.fromisoformat(record["started_at"]) < datetime.fromisoformat(manifest["sealed_at"]):
                raise ReviewBundleError("Actual review began before its four-result input bundle was sealed")
            if datetime.fromisoformat(artifact["sealed_at"]) < datetime.fromisoformat(manifest["sealed_at"]):
                raise ReviewBundleError("Actual review was sealed before its four-result input bundle")
    return True
