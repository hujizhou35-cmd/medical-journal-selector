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

The first stage uses 100 development papers and 50 sealed tests across ten article classes; **82/100 valid development cases are complete, final testing remains 0/50, and 24 protocol trials are retained separately**. **r32b-wave7-10 is running seven cases from the seven unfinished queues**, configured with **ten case workers and a global cap of five simultaneous model calls**. The ten r31 central decisions are complete. A bibliography-only inline-format matching repair was adopted in frozen execution **r25**; Selector **r18** and its rules are unchanged. Original scores and valid-input poor results remain intact. Software checks add no blind cases or evidence of accuracy improvement. If gates fail, one extension adds 100 development papers and 50 new tests. The stable download remains **V1.0.0** until the gates pass. See the [protocol and actual results](evaluation/README.md).

## Installation

The Trainer uses its own `medical-journal-selector-skill-trainer` folder. For Codex, install in `.agents/skills/`; for Claude Code, in `.claude/skills/`. A standalone portable Trainer file accompanies the gated release. Preserve its name and the separate selector folder.

[Trainer source](../skills/medical-journal-selector-skill-trainer/) is included in this project. Release links are added after evaluation, not presented as available in advance.

## Automation and limits

Python helpers collect permitted papers, prepare masked packets, execute fresh restricted Codex sessions and retain seals/metrics. They use the host's existing access. Other Agents can follow the portable workflow with their own tools; auditable blind evaluation requires separated contexts and controlled retrieval.

The project uses AI reviewers, not medical experts. Public-paper model memory and the reviewed final manuscript remain limitations. Raw papers, answer maps and full logs are excluded from release packages.

Ten primary article-class queues can run one case per class, with ceilings of ten workers and ten simultaneous model calls. Each case keeps its preparation, recommendation, blind review, reveal and decision in order; the whole wave reaches a barrier before changes are adopted.

Earlier barriers reached 26/100 and 35/100. On 3 October 2026, the historical r23 amendment gave 40/100, r24 gave 48/100, and nine valid r25 chains raised the total to **57/100**. Original grades, genuine blind reviews, negative results and incomplete chains remain recorded. The retained **276 offline tests** keep their original scope; execution **r24** and Selector **r17** stay frozen.

The earlier `r26-wave10-07` ended as failed on 3 October 2026 after repeated request errors. All ten chains remained incomplete, with partial outputs retained, no new completed-case credit and no answers revealed. Retries stopped after three errors of the same cause. Its historical cause remains unproven; those failures did not establish quota exhaustion or a safety refusal.

The `r27-recovery-5` wave ended and was sealed on **3 October 2026 at 11:48:55 UTC**; its five recovered cases passed explicit sealed no-change central decisions, giving **57 + 5 = 62/100 development, 0/50 final and 24 retained protocol trials**. Original grades remain **three usable and two unusable, with zero hard failures**; poor valid-input results stay in the denominator. One earlier paper-free, tool-free nonce call through the existing local proxy completed in **26.853 seconds** without observed connection errors. That small request did not prove full-case or concurrent reliability or locate the earlier fault; this observed five-case recovery does not prove future ten-call reliability. Original failed calls and scores remain retained. No new Selector instruction or execution software change was adopted at this barrier; frozen execution **r24** and Selector **r17** continue. The subsequent r28 execution covered ten primary classes with a ten-worker, ten-call ceiling and the same launcher-only proxy: the five original remaining incomplete cases have priority, and each of the other five classes takes its next unexposed case from the frozen queue. r28 ended and was sealed at 12:49:08 UTC; its genuine audit and decision gates are recorded in the evaluation pages. Detailed findings belong in the [evaluation record](evaluation/README.md); [current state](evaluation/current-wave.json) distinguishes planned work, running work, failures and completed cases. Read the [parallel execution plan](evaluation/parallel-execution-plan.md) before enabling the scheduler.

The r28 ten-class wave retains original grades of **four usable, six unusable and three hard-failure cases**. All are valid inputs. Its ten sealed central decisions are now complete: **three accepted-change and seven no-change decisions**, raising development completion from **62 to 72/100**. The original r29-b interruption remains recorded as **five launched calls, three completed and two failed**. After reported recovery, r30 completed **six new calls** and reused **three completed checkpoints**: **nine distinct contexts**, an actual new-call peak of **three**, and **zero new transport errors**. It passed **388 independent administrative checks**, the root's **nine schema, source-support and constraint checks across three cases**, and **36 local behavior/language checks**. Both reviews completed for each replay; all three still had **zero usable candidates**. Earlier failures, negative scores and unknown failed-attempt costs remain. The adopted three general Step 5 checks support the narrow regression result, not an accuracy-improvement claim; exposed-input replays add **zero blind-case credit**. See the [evaluation record](evaluation/README.md).

The **r31-wave10-09** wave is sealed and its ten central decisions are complete: **one accepted software change and nine no-change decisions**, raising development completion from **72 to 82/100**. Its original grades remain **five with usable candidates, five without and one hard-failure case**. The adopted repair only handles permitted inline formatting in bibliographic precedent support; it changes no Selector rules, rewrites no original grades, adds no blind-case credit and establishes no accuracy improvement. Detailed call, exit-code, reconnect and software-check evidence is in the [evaluation record](evaluation/README.md).

Laboratory, bioinformatics and prediction have each completed their ten development cases. **r32b-wave7-10 is running seven cases**, taking the next unexposed frozen queue head from each of the other **seven primary classes**. It is configured with **ten case workers and a global cap of five simultaneous model calls**, using frozen execution **r25** and unchanged Selector **r18**. Running cases add no completion credit; the formal count remains **82/100 development and 0/50 final**. Current execution details are in the [evaluation record](evaluation/README.md).

Final testing requires all 100 genuinely completed valid development records. Seal both ranking baselines and shared inputs before recommendations; both final reviewers inspect all four anonymous comparator results. Validate the whole fifty-case batch before the reveal/scoring role sees its answers. The real final evaluation remains unstarted. Across the latest independently verified class/quota metadata amendment only, the same 50 final sources, answers and masked inputs remain byte-identical. Nine masked inputs were corrected earlier in r24 before any final model call; those prior corrections remain. A rejected reserve remains recorded, and replacements must pass the main-purpose gate before use. Metadata correction adds no blind-case credit. See the [repair records](evaluation/execution-repairs.json).
