# Improve the selector with the Trainer

[简体中文](trainer-guide.zh-CN.md) · [Homepage](../README.md)

**Medical Journal Selector Skill Trainer** organizes an improvement experiment. Use the selector itself when you only need journals for one manuscript.

## Three steps

1. Supply a snapshot of the selector and permitted manuscript examples. Set the development/test split and model/settings before inspecting results.
2. Let fresh contexts select journals from masked manuscripts. Seal recommendations and independent source-based reviews before revealing the known publishing journal.
3. Turn demonstrated problems into reusable rules, test protected cases, then evaluate the frozen candidate on untouched manuscripts.

```text
Use medical-journal-selector-skill-trainer to evaluate this selector.
Use masked manuscripts and hide publishing journals until outputs
and independent reviews are sealed. Preserve an untouched final test set.
Explain which rule changes are supported and whether release gates pass.
Please respond in English.
```

## What is an iteration?

One distinct manuscript completes selection, blind review, reveal, diagnosis and a supported change or explicit no-change decision. Retries and regressions do not add cases. A recommendation can be reasonable without matching the published outlet; published articles do not supply rejection data or acceptance probabilities.

## Project V2 campaign

The first stage uses 100 development papers and 50 untouched tests across ten article classes. If gates fail, one extension adds 100 development papers and 50 new tests. No stable V2 is published while gates fail. See the [protocol and actual results](evaluation/README.md).

## Installation

The Trainer uses its own `medical-journal-selector-skill-trainer` folder. For Codex, install in `.agents/skills/`; for Claude Code, in `.claude/skills/`. A standalone portable Trainer file accompanies the gated release. Preserve its name and the separate selector folder.

[Trainer source](../skills/medical-journal-selector-skill-trainer/) is included in this project. Release links are added after evaluation, not presented as available in advance.

## Automation and limits

Python helpers collect permitted papers, prepare masked packets, execute fresh restricted Codex sessions and retain seals/metrics. They use the host's existing access. Other Agents can follow the portable workflow with their own tools; auditable blind evaluation requires separated contexts and controlled retrieval.

The project uses AI reviewers, not medical experts. Public-paper model memory and the reviewed final manuscript remain limitations. Raw papers, answer maps and full logs are excluded from release packages.

For a faster campaign, ten primary article-class queues can run one case per class, with a default ceiling of ten workers and ten simultaneous model calls. Each case retains its serial preparation, recommendation, blind review, reveal and decision chain. Actual two-case and five-case waves have passed their checks; a ten-case wave still needs observed receipts. Read the [parallel execution plan](evaluation/parallel-execution-plan.md) before enabling the scheduler.

Final testing requires the completed development records. Seal both ranking baselines and shared inputs before recommendations; both final reviewers inspect all four anonymous comparator results. Validate the whole fifty-case batch before the reveal/scoring role sees its answers. These implemented guards have synthetic checks, while the real final evaluation remains unstarted.
