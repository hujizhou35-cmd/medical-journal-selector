"""Pin shared preparation before execution; never retrofit old cases as sealed.

The returned binding belongs in the case ledger. Its hash must be retained,
not recomputed from a possibly changed manifest at verification time. All final
cases pass require_final_preparation before any answer.json is opened. This
module reads only source.xml/masked.txt in the source case directory.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from runner import completed_message, event_records, parse_json_message

SCHEMA_VERSION = 1
MANIFEST_NAME = 'preparation-seal.json'
REQUIRED_FILES = (
    'fixed-baselines.json', 'profile.json', 'literature.json', 'policies.json',
    'generator-packet.json', 'source-plan.json', 'candidate-handoff.json',
    'policies.retrieval.json', 'profile.json.record.json',
    'profile.json.events.jsonl', 'profile.json.input.txt',
    'source-plan.json.record.json', 'source-plan.json.events.jsonl',
    'source-plan.json.input.txt',
)
SOURCE_FILES = ('source.xml', 'masked.txt')


class PreparationSealError(ValueError):
    pass


def stamp():
    return datetime.now(timezone.utc).isoformat()


def _fail(message):
    raise PreparationSealError('Preparation seal: '+message)


def _read(path):
    try:
        return parse_json_message(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        _fail('missing or invalid JSON '+str(path)+': '+str(exc))


def _hash(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError as exc:
        _fail('required file unavailable '+str(path)+': '+str(exc))


def _time(value, label):
    try:
        result = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        _fail(label+' has an invalid timestamp: '+str(exc))
    if result.tzinfo is None or result.utcoffset() is None:
        _fail(label+' requires a timezone-aware timestamp')
    return result


def _no_execution(work):
    # Even an input/request or failed attempt proves that execution began.
    for path in work.iterdir():
        if re.match(r'^(?:v\d+-selection|review-\d+|lesson)\.', path.name):
            _fail('cannot create a new seal after a generation/review/lesson request exists')
    ledger_path = work/'ledger.json'
    if ledger_path.exists():
        ledger = _read(ledger_path)
        if (ledger.get('generations') or ledger.get('reviews') or
                ledger.get('revealed_at') or ledger.get('lesson_record') or
                ledger.get('status') in ('reviewed', 'revealed', 'diagnosed', 'completed')):
            _fail('cannot retrofit preparation after execution or reveal')


def assert_preparation_unstarted(work):
    """Reject old execution evidence before a caller rewrites preparation files."""
    work = Path(work)
    if work.exists():
        _no_execution(work)
    return True


def _receipt(work, output_name):
    output = work/output_name
    record = _read(work/(output_name+'.record.json'))
    if (record.get('status') != 'completed' or not record.get('context_id') or
            record.get('output_contract_status') == 'failed' or
            record.get('output_hash') != _hash(output)):
        _fail('no matching completed model receipt for '+output_name)
    message = completed_message(event_records(work/(output_name+'.events.jsonl')))
    if message is None or message != output.read_text(encoding='utf-8'):
        _fail('no genuine matching terminal event for '+output_name)
    started = _time(record.get('started_at'), output_name+' started_at')
    completed = _time(record.get('completed_at'), output_name+' completed_at')
    if completed < started:
        _fail('model receipt completes before its start: '+output_name)
    return record


def _check_preparation_timing(work, sealed_at):
    sealed = _time(sealed_at, 'sealed_at')
    for name in ('profile.json', 'source-plan.json'):
        record = _receipt(work, name)
        if _time(record['completed_at'], name+' completed_at') > sealed:
            _fail('preparation model completed after its seal')
    packet = _read(work/'generator-packet.json')
    if _time(packet.get('started_at'), 'packet started_at') > sealed:
        _fail('packet was prepared after its seal')
    for source in packet.get('policies', []) + packet.get('retrieval_records', []):
        if _time(source.get('checked_at'), 'retrieval checked_at') > sealed:
            _fail('source was acquired after its seal')


def _files(work, names):
    result = {}
    for name in names:
        path = work/name
        result[name] = {'sha256': _hash(path), 'bytes': path.stat().st_size}
    return result


def seal_preparation(work, source_case_dir, case_id, *, expected_masked_hash=None,
                     existing_binding=None):
    """Create once, before selection; reuse only an independently pinned binding."""
    work, source_case_dir = Path(work).resolve(), Path(source_case_dir).resolve()
    if not work.is_dir():
        _fail('case preparation directory does not exist')
    path = work/MANIFEST_NAME
    if path.exists():
        if existing_binding is None:
            _fail('an existing seal requires its original ledger binding')
        verify_preparation_seal(work, existing_binding, case_id=case_id,
                                source_case_dir=source_case_dir,
                                expected_masked_hash=expected_masked_hash)
        return dict(existing_binding)
    if existing_binding is not None:
        _fail('pinned preparation manifest is missing; do not recreate it')
    _no_execution(work)
    files = _files(work, REQUIRED_FILES)
    source_files = _files(source_case_dir, SOURCE_FILES)
    masked_hash = hashlib.sha256((source_case_dir/'masked.txt').read_text(encoding='utf-8').encode()).hexdigest()
    if expected_masked_hash is not None and masked_hash != expected_masked_hash:
        _fail('masked source differs from its allocation hash')
    sealed_at = stamp()  # No caller-supplied or backdated seal time.
    _check_preparation_timing(work, sealed_at)
    _no_execution(work)
    manifest = {'schema_version': SCHEMA_VERSION, 'case_id': case_id,
                'sealed_at': sealed_at, 'source_case_dir': str(source_case_dir),
                'masked_input_hash': masked_hash, 'files': files, 'source_files': source_files,
                'comparators': ['keyword', 'abstract', 'v1', 'v2'],
                'baseline_input': 'LLM-assisted shared profile keywords and abstract_summary',
                'interpretation': 'Actual preparation seal created before any recommendation/review request; not retrofitted.'}
    payload = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')
    try:
        with path.open('xb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError:
        _fail('another preparation seal already exists; do not overwrite it')
    binding = {'schema_version': SCHEMA_VERSION, 'status': 'sealed', 'case_id': case_id,
               'path': str(path), 'output_hash': hashlib.sha256(payload).hexdigest(),
               'sealed_at': sealed_at}
    verify_preparation_seal(work, binding, case_id=case_id,
                            source_case_dir=source_case_dir,
                            expected_masked_hash=expected_masked_hash)
    return binding


def verify_preparation_seal(work, binding, *, case_id, source_case_dir,
                            expected_masked_hash=None):
    """Verify every pinned input without changing files, timestamps or scores."""
    work, source_case_dir = Path(work).resolve(), Path(source_case_dir).resolve()
    if not isinstance(binding, dict) or binding.get('status') != 'sealed':
        _fail('missing original preparation binding')
    path = work/MANIFEST_NAME
    if (binding.get('case_id') != case_id or binding.get('schema_version') != SCHEMA_VERSION or
            Path(binding.get('path', '')).resolve() != path or
            binding.get('output_hash') != _hash(path)):
        _fail('manifest binding changed or belongs to another case')
    manifest = _read(path)
    if (manifest.get('schema_version') != SCHEMA_VERSION or manifest.get('case_id') != case_id or
            manifest.get('sealed_at') != binding.get('sealed_at') or
            Path(manifest.get('source_case_dir', '')).resolve() != source_case_dir):
        _fail('manifest identity, time or source binding changed')
    if set(manifest.get('files', {})) != set(REQUIRED_FILES) or set(manifest.get('source_files', {})) != set(SOURCE_FILES):
        _fail('manifest omits required preparation inputs')
    for folder, key in ((work, 'files'), (source_case_dir, 'source_files')):
        for name, expected in manifest[key].items():
            file = folder/name
            if expected.get('sha256') != _hash(file) or expected.get('bytes') != file.stat().st_size:
                _fail('pinned input changed: '+name)
    masked_hash = hashlib.sha256((source_case_dir/'masked.txt').read_text(encoding='utf-8').encode()).hexdigest()
    if masked_hash != manifest.get('masked_input_hash') or (expected_masked_hash is not None and masked_hash != expected_masked_hash):
        _fail('masked source differs from its preparation/allocation hash')
    _check_preparation_timing(work, manifest['sealed_at'])
    return manifest


def require_final_preparation(records, corpus, runs, expected_count=50):
    """Validate the whole four-comparator batch before the caller reads an answer."""
    if len(records) != expected_count or len({r.get('case_id') for r in records}) != expected_count:
        _fail('final preparation requires the entire distinct-case batch')
    for ledger in records:
        case_id = ledger.get('case_id')
        if not isinstance(case_id, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', case_id) or case_id.endswith('.'):
            _fail('unsafe or missing case id')
        work = Path(runs)/case_id
        manifest = verify_preparation_seal(work, ledger.get('preparation_seal'), case_id=case_id,
                                           source_case_dir=Path(corpus)/case_id,
                                           expected_masked_hash=ledger.get('masked_input_hash'))
        sealed = _time(manifest['sealed_at'], 'sealed_at')
        generations, reviews = ledger.get('generations', []), ledger.get('reviews', [])
        if {a.get('variant') for a in generations} != {'v1', 'v2'} or len(reviews) < 2:
            _fail('final case lacks both variants or two reviews')
        for artifact in generations + reviews:
            output = Path(artifact.get('path', '')).resolve()
            if output.parent != work.resolve():
                _fail('execution artifact is outside its case directory')
            record = _receipt(work, output.name)
            if (record.get('context_id') != artifact.get('context_id') or
                    record.get('output_hash') != artifact.get('output_hash')):
                _fail('execution receipt differs from the sealed artifact')
            if _time(record['started_at'], output.name+' started_at') < sealed:
                _fail('preparation was sealed after execution began')
    return True
