# Medical Journal Selector

**English** | [简体中文](docs/README.zh-CN.md)

Turn a medical manuscript into a journal shortlist with sources you can check. Provide your manuscript and submission requirements; receive recommendations organized by **quartile, time and fit**, with reasons and unresolved checks.

## Start here

| I want to… | Use | Get it |
|---|---|---|
| Choose journals for a manuscript | **Selector V1.0.0 — stable** | [Download](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0) |
| Evaluate and improve the Skill | **Skill Trainer — companion preview** | [Download](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/trainer-v1.0.0) · [Guide](docs/trainer-guide.md) |

**Selector downloads:** [Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md)

Choose one format: `.skill` contains one installable Skill; Plugin ZIP contains Codex plugin metadata and the Skill; `SKILL.md` is a self-contained instruction file for another assistant. These are instructions and optional helpers, not a standalone AI service. Your host supplies the model, file access and browsing. [Installation](docs/getting-started.md)

## Choose journals in three steps

1. **Install one package.** Start with stable V1, then open a fresh conversation.
2. **Provide your manuscript and requirements.** Include your indexing/quartile requirement, budget, open-access preference and deadline. Say whether the deadline means acceptance, online publication or indexing.
3. **Compare the shortlist.** Review the evidence, fit reasons and remaining checks before choosing a submission target.

```text
Use medical-journal-selector to help me choose journals for this manuscript.
First identify the research question, article type, methods and validation.
Ask for missing submission requirements, then search and verify candidates.
Compare quartile, time and fit routes, with sources and unresolved checks.
Please respond in English.
```

You can request another output language, including Chinese.

## What you receive

**Read the manuscript → understand the research → find similar papers → check current journal policies → compare candidates.**

| Route | What it helps you compare |
|---|---|
| Quartile | Verified JCR quartiles among otherwise eligible journals |
| Time | Evidence about the specific submission stage and deadline you need |
| Fit | Research methods, article type, readership and publication precedents |

Each route contains up to three journals; evidence gaps can mean fewer. Facts include sources and dates. Missing evidence remains **Not verified**. A shortlist does not estimate acceptance probability.

[Read a complete fictional report](docs/examples/fictional-report.md) · [Privacy](docs/privacy.md)

## V1 and the V2 experiment

V1 introduced the three routes and current-source checks. V2 made method-policy checks, source roles and final-report auditing more explicit. The Trainer completed **100 development cases**, followed by **50 final tests** of frozen V1 and V2.

| Final 50 cases | V1 | V2 |
|---|---:|---:|
| Historical journal in the top ten | 4/50 (8%) | 1/50 (2%) |
| At least one usable recommendation, with no retained hard failure | 14/50 (28%) | 16/50 (32%) |
| Cases affected by hard failures | 21/50 (42%) | 12/50 (24%) |
| Retained hard-failure flags | 37 | 41 |

V2 affected fewer cases with hard failures, but retained more flags and matched fewer historical journals. AI review recorded **11 V2 wins, 26 ties, 8 V1 wins and 5 unresolved cases**. The results do not establish overall superiority; **V1 remains stable and V2 remains experimental**.

[V2 experiment and downloads](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v2.0.0-experimental.1) · [Methods, costs and full comparison](docs/evaluation/100-plus-50.md)

## Improve the Skill with the Trainer

The Trainer organizes an improvement loop: **mask a published case → seal recommendations → review in separate contexts → reveal the historical outlet → diagnose → test a reusable rule change**. It revises Skill instructions and checks; it does not train model weights.

**Trainer downloads:** [Trainer Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/SKILL.md)

The preview is for contributors who want to study or extend the workflow. Ordinary journal selection does not require it. [Beginner guide](docs/trainer-guide.md) · [Public experiment records](docs/evaluation/README.md)

## Contribute

Help improve documentation, host compatibility, source checks or recommendation rules. [Report an issue](https://github.com/hujizhou35-cmd/medical-journal-selector/issues/new/choose), read [Contributing](.github/CONTRIBUTING.md), or [submit a pull request](https://github.com/hujizhou35-cmd/medical-journal-selector/compare).

After choosing a journal, use [Journal Cover Letter Skill](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial) to prepare the cover letter from verified manuscript facts.

Created by **Jizhou Hu** · [MIT License](LICENSE) · [Citation](CITATION.cff)
