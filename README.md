# Medical Journal Selector

**Find journals for your medical manuscript—from understanding the study to checking each journal and comparing submission options.**

[简体中文](docs/README.zh-CN.md) · [Download v1.0.0](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0) · [Installation guide](docs/getting-started.md) · [Example report](docs/examples/fictional-report.md)

## Start here

Choose the AI assistant you use. You only need **one** download.

- **Codex:** download the [Skill package](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill), then ask Codex to install it in your project's `.agents/skills/medical-journal-selector/` folder.
- **Claude Code:** download the [Skill folder ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-portable-v1.0.0.zip), put the enclosed folder in `.claude/skills/`, then invoke `/medical-journal-selector`.
- **Another AI assistant:** download [standalone SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md) and ask your assistant to read it and use it with your manuscript.

For step-by-step setup or the Codex Plugin option, see the [installation guide](docs/getting-started.md).

## How it works

1. **Read your manuscript.** Identify the research question, study design, data sources, main findings and intended readers. Check what the supplied files actually establish.
2. **Identify the field and article type.** Place the study in a broad medical field and a more specific topic. Distinguish an original study, review, case report or other article type; extract useful search terms and assess the methods and validation.
3. **Confirm your requirements.** Ask only for missing preferences or limits: JCR quartile, indexing, budget, open access, excluded journals and your deadline. Clarify whether you need acceptance, online publication or indexing.
4. **Search for candidate journals.** Find similar published studies and relevant journals across publishers. Public-database analyses prioritize the past 24 months; other studies use a five-year background with emphasis on recent work.
5. **Check each journal.** Read its current Aims & Scope, article-type and method policies. Verify indexing, JCR, impact factor, publication times, open-access options, fees and relevant warning lists.
6. **Filter and compare.** Apply your hard requirements, then compare higher-quartile, time and methodological-fit routes. Keep unresolved requirements visible and explain exclusions.
7. **Review the evidence and deliver the report.** Recheck gaps or conflicting information, revise the shortlist where needed, and give you the reasons, sources and remaining questions. You choose the journal before moving to a cover letter.

Keywords help discover candidates; the manuscript's methods, the journal's current policies and your requirements determine the shortlist.

## Try it with your manuscript

Attach your manuscript, or start with its abstract, then copy:

```text
Use medical-journal-selector to help me choose journals for this manuscript.
Identify its field, article type, methods and validation first.
Ask me for any missing submission requirements, then search and verify candidates.
Compare higher-quartile, time and fit routes, explaining each recommendation
with current sources. Clearly mark anything you cannot verify.
Please respond in English.
```

To receive the report in Chinese, replace the last line with **“请用中文回复。”** The homepage language does not determine the language of your report.

You can add: `I need JCR Q2 or above, a total fee below [budget/currency], and acceptance by [date].` These are example requirements, not defaults.

## What you receive

| Route | What it prioritizes |
|---|---|
| **Higher quartile** | Better verified JCR quartiles among journals that meet the basic fit and submission requirements |
| **Time** | Comparable publication times for the stage you need to reach |
| **Fit** | The closest match to the study's methods, article type, readers and recent publication precedents |

Each journal comes with an official **Aims & Scope quotation**, a specific explanation of its fit, similar papers, key publication information and source links. Each route contains up to three journals; fewer are shown when the evidence is insufficient. Fit is an assessment, not an acceptance probability.

**[Read a complete example report →](docs/examples/fictional-report.md)** The example uses fictional journals and figures to show the report format. Switch to Chinese at the top of the report.

## Improve the selector

**Medical Journal Selector Skill Trainer** runs masked manuscript cases, seals recommendations and independent reviews, then reveals the known publishing journal. It turns supported failures into reusable rules and checks a separate untouched test set.

The V2 candidate and Trainer are under evaluation: **82/100 valid development cases are complete, final testing remains 0/50, and 24 protocol trials are retained separately.** The latest wave and central decisions are sealed. A bibliography-format matching repair was adopted; original scores and negative results remain. The next seven-class wave is planned with at most five simultaneous model calls and has not started. The stable release remains **V1.0.0** until the gates pass. [Trainer guide](docs/trainer-guide.md) · [Evaluation status](docs/evaluation/README.md)

## Common questions

<details>
<summary><strong>Can I start with just an abstract?</strong></summary>

Yes. The Skill can identify the topic and begin the search. Share the full methods and relevant supplements when you want a more reliable assessment of journal fit.

</details>

<details>
<summary><strong>What kinds of papers can I use it for?</strong></summary>

Clinical and nursing studies, laboratory research, public-database analyses, bioinformatics and prediction models, network pharmacology/toxicology, reviews, Meta analyses, bibliometrics and case reports. It checks whether each journal accepts your particular article type and methods.

</details>

<details>
<summary><strong>Can I set a target quartile, budget or deadline?</strong></summary>

Yes—tell the Skill what is required and what is only a preference. For a deadline, say whether it means acceptance, online publication or indexing. The report compares available evidence without promising a completion date.

</details>

<details>
<summary><strong>Why does a field say “Not verified”?</strong></summary>

The Skill could not confirm that information from a reliable current source. Chinese reports use “未核到” for the same status. The report explains what is missing. If that fact is one of your hard requirements, the journal stays pending rather than being presented as a confirmed match.

</details>

## After you choose a journal

Pass the selected journal, manuscript facts and verified fit evidence to [Journal Cover Letter Skill](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial) to prepare your submission letter.

---

Created by **Jizhou Hu** · [MIT License](LICENSE) · [Privacy](docs/privacy.md) · [Report an issue](https://github.com/hujizhou35-cmd/medical-journal-selector/issues)
