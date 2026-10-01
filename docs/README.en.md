# Medical Journal Selector

[简体中文](../README.md) · [Release v1.0.0](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0) · [Examples](examples/README.md)

Read a medical manuscript and compare **higher JCR quartile**, **time**, and **methodological fit** in one evidence-backed report. Every changing metric or status is checked during the run. Unverified facts are labelled **未核到** (not verified), never completed from memory.

## Install once, then ask

| Agent | File | Installation |
|---|---|---|
| Codex | [`.skill`](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill) | Unzip into your project `.agents/skills/medical-journal-selector/`; invoke `$medical-journal-selector` |
| Claude Code | [Portable ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-portable-v1.0.0.zip) | Place the enclosed folder in `.claude/skills/`; invoke `/medical-journal-selector` |
| Other agents | [`SKILL.md`](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md) | Give the self-contained file to an agent with reading and web tools |
| Codex plugin users | [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-codex-plugin-v1.0.0.zip) | Use a supported local plugin workflow; otherwise install its enclosed skill folder |

The ZIPs do not supply a model, JCR subscription or web access. This is not an officially listed marketplace plugin. See [tested compatibility](validation.md).

```text
Use medical-journal-selector with my attached manuscript. Ask only for missing
decision-changing constraints. Return higher-quartile, time, and fit routes.
Quote official Aims & Scope and verify indexing, JCR categories/year, JIF/year,
timelines, OA, applicable fees, and warning coverage. Include source URLs and
check times. Mark unavailable facts 未核到. Respond in English.
```

Provide the manuscript, required JCR/indexing, budget/currency, OA preference and deadline endpoint (acceptance, online publication or indexing). Abstract-only assessment remains limited.

## What the workflow checks

The manuscript profile combines topic, study design, article type, data provenance, validation and readers. Public-database secondary analyses emphasize the last 24 months; other designs use a five-year background with recent evidence favored. Current policies override older precedents.

Each unique journal gets an official scope quotation, manuscript-specific explanation, comparable publications, indexing, all verified JCR categories, JIF, separate time stages, OA/fees and scoped warning checks. Unknown hard constraints remain pending. Empty rankings are allowed.

Published precedents are not a rejection denominator. The skill does not predict acceptance probabilities, guarantee deadlines, treat random data splitting as external validation, or mistake first decision for acceptance.

The host supplies its model and tools. Optional helpers use Python 3.10+ and the standard library. No additional GPT API purchase is required by this project; host usage charges still apply. Offline hosts can only prepare profiles and search plans.

## Examples and development

- [Fictional three-route example](examples/fictional-report.md): invented journals and numbers, not submission advice.
- [Dated live-source example](examples/live-report.md): fictional manuscript, real-source snapshot, visible gaps.
- [Design and references](design.md), [privacy](privacy.md), [development](../development/README.md), [validation](validation.md).

After choosing a journal, pass the evidence and unresolved items to [Journal Cover Letter Skill](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial).

MIT licensed original code/documentation. Journal excerpts and third-party marks retain their original rights. Created by Jizhou Hu. See [LICENSE](../LICENSE) and [CITATION.cff](../CITATION.cff).
