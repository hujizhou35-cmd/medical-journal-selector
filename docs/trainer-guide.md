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

The first stage uses 100 development papers and 50 sealed tests across ten article classes; **57/100 valid development cases are complete, final testing remains 0/50, and 24 protocol trials are retained separately**. Original scores and valid-input poor results remain intact. The latest ten-class wave ended after repeated connection errors and added no completed cases; its cause remains under review. If gates fail, one extension adds 100 development papers and 50 new tests. The stable download remains **V1.0.0** until the gates pass. See the [protocol and actual results](evaluation/README.md).

## Installation

The Trainer uses its own `medical-journal-selector-skill-trainer` folder. For Codex, install in `.agents/skills/`; for Claude Code, in `.claude/skills/`. A standalone portable Trainer file accompanies the gated release. Preserve its name and the separate selector folder.

[Trainer source](../skills/medical-journal-selector-skill-trainer/) is included in this project. Release links are added after evaluation, not presented as available in advance.

## Automation and limits

Python helpers collect permitted papers, prepare masked packets, execute fresh restricted Codex sessions and retain seals/metrics. They use the host's existing access. Other Agents can follow the portable workflow with their own tools; auditable blind evaluation requires separated contexts and controlled retrieval.

The project uses AI reviewers, not medical experts. Public-paper model memory and the reviewed final manuscript remain limitations. Raw papers, answer maps and full logs are excluded from release packages.

Ten primary article-class queues can run one case per class, with ceilings of ten workers and ten simultaneous model calls. Each case keeps its preparation, recommendation, blind review, reveal and decision in order; the whole wave reaches a barrier before changes are adopted.

Earlier barriers reached 26/100 and 35/100. On 3 October 2026, the historical r23 amendment gave 40/100, r24 gave 48/100, and nine valid r25 chains raised the total to **57/100**. Original grades, genuine blind reviews, negative results and incomplete chains remain recorded. The retained **276 offline tests** keep their original scope; execution **r24** and Selector **r17** stay frozen.

The subsequent `r26-wave10-07` ended as failed after repeated request errors. All ten chains remained incomplete, with partial outputs retained, no new completed-case credit and no answers revealed. Retries of the failed calls stopped after three errors of the same cause. The cause remains under review; the failure does not establish quota exhaustion, a safety refusal or recovery. Detailed call counts and runtime findings belong in the [evaluation record](evaluation/README.md); [current state](evaluation/current-wave.json) distinguishes failures from completed cases. Read the [parallel execution plan](evaluation/parallel-execution-plan.md) before enabling the scheduler.

Final testing requires all 100 genuinely completed valid development records. Seal both ranking baselines and shared inputs before recommendations; both final reviewers inspect all four anonymous comparator results. Validate the whole fifty-case batch before the reveal/scoring role sees its answers. The real final evaluation remains unstarted. Across the latest independently verified class/quota metadata amendment only, the same 50 final sources, answers and masked inputs remain byte-identical. Nine masked inputs were corrected earlier in r24 before any final model call; those prior corrections remain. A rejected reserve remains recorded, and replacements must pass the main-purpose gate before use. Metadata correction adds no blind-case credit. See the [repair records](evaluation/execution-repairs.json).
