# Development

Python 3.10+; helper scripts use the standard library. From repository root:

```text
python -m unittest discover -s development/tests -v
python development/make_fictional_example.py
python development/build_release.py --sync-portable
python development/check_project.py
```

Before a release, commit all tested source. Build from a clean checkout of that commit/tag, without `--sync-portable`; stale generated content must fail. ZIPs use sorted entries and fixed ZIP timestamps. `SHA256SUMS.txt` covers the four user-facing assets. Never publish `.work/`, private input, credentials, or raw model transcripts.

The validator checks declared evidence structure and filters, not source truth. Human/Agent reading of actual sources is still required. The fictional fixture tests different rankings and failure modes; it is not a scientific evaluation of recommendation quality. Live examples preserve acquisition times and known gaps, and do not constitute a permanently current journal database.

For behavioral checks, place a built Skill in a temporary project's `.agents/skills/` (Codex) or `.claude/skills/` (Claude Code), start a fresh session, and use the cases in `behavior-cases.md`. Keep transcripts outside the public tree; publish only concise observed outcomes and limitations in `docs/validation.md`.

Frontend checks use GitHub's Markdown rendering and a local preview. Verify downloads, long tables, accessible text alternatives and narrow screens. Release archives should be downloaded again from the public URL and compared with their checksums.
