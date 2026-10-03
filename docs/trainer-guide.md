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

The first stage uses 100 development papers and 50 sealed tests across ten article classes; 48/100 valid development cases are complete, 24 protocol trials are retained separately, and final testing remains 0/50. Original scores and valid-input poor results remain intact. The next ten-class wave is running with a global ten-model-call ceiling. If gates fail, one extension adds 100 development papers and 50 new tests. No stable V2 is published while gates fail. See the [protocol and actual results](evaluation/README.md).

## Installation

The Trainer uses its own `medical-journal-selector-skill-trainer` folder. For Codex, install in `.agents/skills/`; for Claude Code, in `.claude/skills/`. A standalone portable Trainer file accompanies the gated release. Preserve its name and the separate selector folder.

[Trainer source](../skills/medical-journal-selector-skill-trainer/) is included in this project. Release links are added after evaluation, not presented as available in advance.

## Automation and limits

Python helpers collect permitted papers, prepare masked packets, execute fresh restricted Codex sessions and retain seals/metrics. They use the host's existing access. Other Agents can follow the portable workflow with their own tools; auditable blind evaluation requires separated contexts and controlled retrieval.

The project uses AI reviewers, not medical experts. Public-paper model memory and the reviewed final manuscript remain limitations. Raw papers, answer maps and full logs are excluded from release packages.

Ten primary article-class queues can run one case per class, with ceilings of ten workers and ten simultaneous model calls. Each case keeps its serial preparation, recommendation, blind review, reveal and decision chain; the whole wave reaches a barrier before changes are adopted. Earlier barriers reached26/100 and35/100; the r23 source-only amendment yielded35 − 3 + 8 =40/100. Eight valid r24 chains now give40 + 8 =48/100, while two preselection class-label mismatches remain incomplete. All original scores and the latest genuine hard failure are retained. Execution r24 and Selector r17 remain unchanged, with no new Selector rule. The registered `r25-wave10-06` is running, one case per primary class, including the two corrected cached profiles. Running work adds no completion credit. Detailed wave and source findings belong in the [evaluation record](evaluation/README.md); [current state](evaluation/current-wave.json) distinguishes failures, decisions and completed cases. Read the [parallel execution plan](evaluation/parallel-execution-plan.md) before enabling the scheduler.

Final testing requires all 100 genuinely completed valid development records. Seal both ranking baselines and shared inputs before recommendations; both final reviewers inspect all four anonymous comparator results. Validate the whole fifty-case batch before the reveal/scoring role sees its answers. The real final evaluation remains unstarted. This class/quota amendment retains the same50 final sources, answers and masked inputs byte-for-byte. Nine masked inputs were corrected earlier in r24 before any final model call; those prior corrections remain. The two correct cached profiles can resume after the sealed metadata correction, which adds no blind-case credit. See the [repair records](evaluation/execution-repairs.json).
