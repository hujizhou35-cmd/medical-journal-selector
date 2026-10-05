# Trainer: evaluate and improve the journal-selection Skill

**English** | [简体中文](trainer-guide.zh-CN.md) · [Home](../README.md)

The Trainer is a companion preview for contributors. It organizes cases, blind AI review, diagnosis and regressions. It improves Skill instructions; it does not train model weights. Ordinary journal selection only needs the Selector.

## Install and prepare

[Trainer Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/SKILL.md)

Follow [installation](getting-started.md) with the folder name `medical-journal-selector-skill-trainer`. Full bundles include optional Python 3.10+ helpers. Your host supplies files, a model and browsing; batch scheduling also needs a configured model-call command. Native plugin import and full training workflows across every host are not verified.

Prepare a copy of the Selector, published studies you may evaluate, submission constraints chosen before scoring, and historical-outlet answers held separately. Test the workflow and permissions with fictional cases in a separate working directory first. Do not copy answers into a generation task.

## One complete improvement loop

1. **Prepare and mask.** Retain the methods and results needed to understand the study; mask authors, journal names and direct lookup identifiers. Store answers separately and inspect input completeness and leakage risks.
2. **Generate and seal.** Run the frozen Selector and record versions, sources and file hashes. Do not revise the output after seeing the answer.
3. **Review in fresh contexts.** Two answer-free contexts review anonymous outputs and their evidence. Adjudicate disagreements; preserve unresolved outcomes.
4. **Reveal and diagnose.** Reveal the historical outlet only after reviews are sealed. Diagnose non-hits: a historical journal is neither the only valid answer nor necessarily eligible today.
5. **Decide whether to change a rule.** Propose a reusable correction only when evidence supports it. No change is a valid decision.
6. **Check again.** Use a fresh context for affected cases and protected method routes. Record success, failure or rollback. Exposed cases are regressions, not new blind cases.

## Example request

```text
Use medical-journal-selector-skill-trainer.
Check case eligibility, masking and answer isolation before planning a small pilot.
Keep answers out of generation and review until recommendations and reviews are sealed.
Change rules only for supported, reusable improvements; retain failures and regressions.
Do not automatically start a 100+50 campaign. Explain inputs, call budget and checks first.
```

## From a pilot to final evaluation

Complete a small auditable loop before scaling. Worker count is not simultaneous model-call count. Preserve failed checkpoints and avoid duplicate credit on resume; missing usage is unknown, not zero.

Freeze the candidate, baseline, execution configuration and untouched cases before final evaluation. This project's final 50 were revealed only after the whole cohort was sealed. Revealed cases cannot become a new blind test set. Stop and report unmet quality gates.

## The completed 100+50 experiment

The project completed 100 development cases and 50 final tests; V2 still did not pass stable-promotion gates. [Read methods and results](evaluation/100-plus-50.md) or [download the process archive](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v2.0.0-experimental.1/medical-journal-selector-v2.0.0-experimental.1-process.zip). Earlier wave-by-wave status belongs to the archive and [pinned history](https://github.com/hujizhou35-cmd/medical-journal-selector/tree/0f9ffb7adbad863643428475412252e7ca322a42/docs/evaluation), not current progress.

Keep manuscripts, answer maps, complete prompts and raw model logs in private work directories. Publish derived numbers, methods and necessary evidence. [Contribute](../.github/CONTRIBUTING.md)
