# V2 candidate checks

[简体中文](validation-v2.zh-CN.md) · [Evaluation status](evaluation/README.md) · [V1 release checks](validation.md)

These are observed development checks, not a completed V2 release or a journal-selection accuracy result. The required 100 development and 50 final cases remain tracked separately in [the actual case records](evaluation/results.json).

## Local checks

The checked source covers report language, current-source envelopes, hard constraints, three routes, policy exclusions, masking, source restrictions, duplicate families, answer isolation, sealed-output integrity, failed-attempt retention, final reveal gates and packaging. The complete suite passed 156 tests. Source links and standalone Markdown consistency passed separately.

The current corpus audit checked all 150 allocated inputs: hashes match their prepared research text, licenses and answer identities are documented, no detected near-duplicate families cross the splits, and journal caps hold. These program checks do not exclude remembered public papers, unknown duplicate versions or errors requiring scientific judgment.

## Actual host checks

| Host / format | Observed result | Limit |
|---|---|---|
| Claude Code, candidate `.skill` packages extracted into `.claude/skills/` | Both tools were discovered and read. A Chinese request about an English NHANES paper received Chinese output, identified random splitting as internal validation, and kept all three routes unavailable without current sources. Trainer evaluation was not started. | Existing host model: `deepseek-v4-pro`. One offline smoke test; scripts were not executed. |
| Codex CLI, candidate packages installed in `.agents/skills/` | A genuine completed fresh 6.1 Sol / xhigh response read both tools and the methods reference. Terminal events show three file-read commands, English output, correct internal-validation labeling and unavailable offline routes. | Source-provenance rules changed afterward. This result does not certify the final release files; repeat on the frozen release candidate. |
| Self-contained Markdown and archives | Generated from each tool's core and references, with deterministic archives and checksums. | Structural checks do not prove behavior in every Agent. |
| Codex Plugin ZIP | Manifest and same-source contents can be checked. | Native Plugin ZIP import has not been observed; do not claim one-click import or marketplace approval. |

The evaluation model remains `gpt-6.1-sol` with `xhigh` and existing Codex login. Host installation checks are not evaluated manuscript cases and never increase the iteration count. Full transcripts, account settings and original papers stay private.

## Before release

Complete the required real loops and untouched paired tests, assess the release gates, repeat host checks on frozen files, build from committed source, and verify public downloads against checksums. Until these observations exist, compatibility and publication checks remain incomplete.
