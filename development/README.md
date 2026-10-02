# Development

Python 3.10+; helper scripts use the standard library. From repository root:

```text
python -m unittest discover -s development/tests -v
python development/make_fictional_example.py
python development/build_release.py --sync-portable
python development/check_project.py
```

Before a release, commit all tested source. Build from a clean checkout of that commit/tag, without `--sync-portable`; stale generated content must fail. ZIPs use sorted entries and fixed ZIP timestamps. `SHA256SUMS.txt` covers the eight assets for Selector and Trainer. Never publish `.work/`, private input, credentials, or raw model transcripts. During development, package filenames follow the unchanged stable `VERSION`; local candidate packages are not release assets and must not replace V1 downloads.

The example renderer reads the corresponding English and Chinese evidence JSON files and preserves acquisition times. Rendering or translating a stored snapshot does not perform current verification.

The validator checks declared evidence structure and filters, not source truth. Human/Agent reading of actual sources is still required. The fictional fixture tests different rankings and failure modes; it is not a scientific evaluation of recommendation quality. Live examples preserve acquisition times and known gaps, and do not constitute a permanently current journal database.

For behavioral checks, place a built Skill in a temporary project's `.agents/skills/` (Codex) or `.claude/skills/` (Claude Code), start a fresh session, and use the cases in `behavior-cases.md`. Keep transcripts outside the public tree; publish only concise observed outcomes and limitations in `docs/validation.md`.

The Trainer's current experiment, isolation and completion gates are documented in [its guide](../docs/trainer-guide.md) and [evaluation status](../docs/evaluation/README.md). Do not label generated fixtures, retries, policy counterexamples or unfinished case records as the required 100 real development loops. Freeze execution scripts as well as both Skill variants before final testing. Preserve original frozen corpus allocations when resuming acquisition.

Frontend checks use GitHub's Markdown rendering and a local preview. Verify downloads, long tables, accessible text alternatives and narrow screens. Release archives should be downloaded again from the public URL and compared with their checksums.
