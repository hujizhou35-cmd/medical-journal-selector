# Install and try the Skill

[简体中文](getting-started.zh-CN.md) · [Homepage](../README.md) · [Stable download](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0)

**Choose one installation method.** The `.skill` and ZIP downloads contain the same selector rules. Install in your manuscript project so its version is easy to manage. V2 is being evaluated; the stable download above remains V1 until release gates pass.

## Codex

1. Download `medical-journal-selector-v1.0.0.skill` and give the file to Codex.
2. Ask: `Install this Skill in this project's .agents/skills/medical-journal-selector folder.` The `.skill` file is a ZIP archive. The installed folder should contain `SKILL.md`, `references`, `scripts` and `agents` directly.
3. Start a new chat and select **Medical Journal Selector**, or explicitly write `$medical-journal-selector`.

You can also install the repository's `skills/medical-journal-selector` folder. Project `.agents/skills/` and user `~/.agents/skills/` are discovery paths; import buttons can differ between versions. [Official instructions](https://learn.chatgpt.com/docs/build-skills)

**Success check:** run the short prompt below. The assistant should recognize the Skill and handle missing information correctly. A folder existing on disk alone does not prove it loaded.

## Claude Code

1. Download `medical-journal-selector-portable-v1.0.0.zip`.
2. Extract it and copy `medical-journal-selector` into your project's `.claude/skills/`. The final path is `.claude/skills/medical-journal-selector/SKILL.md`; avoid an extra nested folder.
3. Open Claude Code in that project and invoke `/medical-journal-selector`, then provide your manuscript.

For all projects, use `~/.claude/skills/`. Start a new session if the folder is not recognized. Browsing depends on the host's tools and permissions. [Official instructions](https://code.claude.com/docs/en/skills)

**Success check:** when browsing is unavailable, the assistant describes the limitation and keeps the three routes unavailable rather than inventing journal facts.

## Another AI assistant

Download standalone `SKILL.md`, attach it and say: `Read this file and follow its workflow to select journals for my manuscript.` References are included. Full selection needs file-reading and current web access; uploading a file alone does not install it.

Use the portable ZIP if your host supports standard Agent Skills folders. Unchecked hosts are format-portable, not universally tested.

## Codex Plugin option

The ZIP contains `.codex-plugin/plugin.json` and `skills/medical-journal-selector/`. It is intended for Codex versions supporting local plugins; it does not supply browsing or a JCR subscription.

If your version has no ZIP import entry, extract `skills/medical-journal-selector` and install at the Codex path above. This uses the same Skill without a marketplace or MCP configuration. Validation distinguishes package checks from actual plugin loading.

## First, try this prompt

```text
Use medical-journal-selector. I have a nursing qualitative-interview abstract,
but no full manuscript yet. Compare quartile, time and fit routes.
Do not browse in this test and do not guess journal facts.
Explain what additional materials you need and what you can provide now.
Please respond in English.
```

Expect a manuscript profile and search plan, material/browsing limits, and why current rankings are unavailable. It should not invent impact factors, quartiles, fees or acceptance rates.

## Prepare for a real selection

Provide a manuscript or abstract, important methods/supplements, indexing and quartile requirements, budget/currency, OA preference, deadline endpoint and institutional warning lists. Only missing conditions need clarification. An abstract cannot establish all methods or independent validation.

Read pending hard requirements first, then compare routes. Choose a journal before requesting the cover-letter handoff. Specify your report language; V2 follows your request or conversation language independently of this website.

## Update or uninstall

Back up your edits, then replace the old Skill folder. Avoid duplicate copies across discovery paths. Uninstall only your installed folder, preserving other Skills and the parent `.agents` or `.claude` folder.

## Troubleshooting

| Problem | What to check |
|---|---|
| Skill not found | `SKILL.md` is directly inside the correct folder; start a new session |
| Cannot extract `.skill` | Copy it, rename the copy to `.zip`, then extract |
| Old Python version | Helpers need Python 3.10+; use `py -3` on Windows, or the manual workflow |
| JCR requires login | Missing accessible evidence stays Not verified（未核到）; add a permitted source if available |
| Facts differ from an older report | Compare year, currency, article type and check date; new selections recheck changing facts |
| Every route is empty | Inspect hard requirements and evidence gaps; unknown facts are not confirmed matches |

For evaluation and improvement, see the separate [Trainer guide](trainer-guide.md).
