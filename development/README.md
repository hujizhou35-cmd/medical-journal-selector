# Development

Python 3.10+; helpers use the standard library. On this Windows workstation use `py -3.12` instead of `python`, which may select an older interpreter.

```text
python -m unittest discover -s development/tests -v
python development/check_project.py
python development/build_release.py --target stable
python development/build_release.py --target experimental
python development/build_release.py --target trainer
```

Each target writes exactly three install files under its own `dist/` directory. Stable builds read the pinned V1 Git commit and check the published hashes. Experimental builds validate frozen r18 and preserve published bytes. Trainer builds only the tracked Trainer sources. Fetch full history (`git fetch --tags --unshallow` for a shallow clone) before building stable V1. CI checks Windows/Linux with Python 3.10/3.12.

Canonical instructions live under `skills/`. Standalone `SKILL.md` files are generated only in `dist/`; do not commit copies at the root. Release configuration and expected hashes live in `development/releases/`. The legacy experimental builder retains its exact seven-file staging contract for provenance tests; only three install formats are selected for public release. The separate immutable process ZIP is recorded in the distribution inventory.

For fictional example edits, run `python development/make_fictional_example.py` and review the resulting English/Chinese reports. Software checks test structure and behavior, not scientific accuracy. New host claims require an actual loading test; package inspection alone is insufficient. See [behavior cases](behavior-cases.md).

## Publishing

Build and test a committed source tree. Preserve existing Selector tags and retained asset bytes. Upload and anonymously verify new evidence archives before removing archived records from the default branch. Keep a local backup of old notes and every removed attachment. Update English release notes and the complete Chinese page together; SHA-256 values in both must match `distribution.json`.

Use a separate Trainer tag and prerelease; keep Selector V1 marked Latest. The manual package workflow only checks/builds artifacts and cannot overwrite a release. Download verification uses `python development/verify_public_release.py TAG DIRECTORY`; its proof is stored beside, not inside, the asset directory. Publish a fresh proof without rewriting historical checks.

Keep private inputs, answer maps, prompts, raw logs and credentials out of the public tree. Preserve original experiment scores and limitations. View [public experiment records](../docs/evaluation/README.md) for the archived history.
