# Installation and first use

**English** | [简体中文](getting-started.zh-CN.md) · [Home](../README.md)

Start with [stable V1](releases/v1.0.0.md) and choose one file. Try [V2](releases/v2.0.0-experimental.1.md) in a separate project to avoid replacing the same Skill identifier. The repository's Selector source is experimental r18, not V1.

## Choose an installation method

| Host | File and destination |
|---|---|
| Codex Skill | Download `.skill`, a ZIP archive; extract its contents directly into `.agents/skills/medical-journal-selector/` in your project |
| Codex Plugin | Download Plugin ZIP, containing `.codex-plugin/` metadata and `skills/`. Native plugin import is not verified; use the Skill route if your host does not support it |
| Claude Code | Use the same `.skill` archive, renaming it to `.zip` if necessary; extract its contents into `.claude/skills/medical-journal-selector/` |
| Another assistant | Download and ask it to read `SKILL.md`; references are inlined, but executable helpers are not included in this single file |

Selector V1 downloads: [Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md)

The destination should directly contain `SKILL.md`, `references/`, `scripts/` and `agents/`, without a duplicate wrapper folder. Open a fresh conversation and explicitly request `medical-journal-selector`. Files on disk alone do not establish successful loading: check the host's actual response. Enable the host's file and browsing tools as needed.

## First run

Provide the manuscript and relevant supplements, then state indexing/quartile requirements, fee budget, open-access preferences and your deadline stage.

```text
Use medical-journal-selector. Read my manuscript first.
Ask for missing submission requirements, then compare quartile, time and fit.
For each journal, include sources, verification dates, reasons and pending checks.
Please respond in English.
```

A successful invocation understands the research, asks for essential missing requirements and marks unsupported facts **Not verified**. With only an abstract or no browsing, it should explain the limitations and provide a research profile and search plan. [Example report](examples/fictional-report.md)

## Trainer and file verification

Install the [Trainer](trainer-guide.md) only to evaluate or improve the Skill. Its folder name is `medical-journal-selector-skill-trainer`; installation follows the same methods. Optional Python helpers in the full bundles need Python 3.10+. Single-file instructions can be followed by the host without those helpers.

Compare a downloaded file with the SHA-256 section in its Release notes. On Windows, use `Get-FileHash -Algorithm SHA256 path`; on macOS/Linux, use `shasum -a 256 path`. GitHub's two automatic Source code downloads are for developers.
