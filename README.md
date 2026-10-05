# Medical Journal Selector

**Turn a medical manuscript into a source-backed journal shortlist.** Read the study, search similar papers, verify current journal policies, then compare **quartile, time and fit** routes.

[Stable V1.0.0](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0) · [Install](docs/getting-started.md) · [Example report](docs/examples/fictional-report.md) · [简体中文 ↓](#简体中文)

> **100 development cases + 50 final cases completed.** V2 did not demonstrate a clear overall improvement and did not pass stable promotion gates. The unchanged evaluated candidate is being packaged as **V2.0.0 Experimental 1**. [Release notes](docs/releases/v2.0.0-experimental.1.md) · [100 + 50: changes, process and results](docs/evaluation/100-plus-50.md)

## Try it in three steps

1. **Install one stable V1 file.** Codex: [Skill package](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill). Claude Code: [folder ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-portable-v1.0.0.zip). Another assistant: [standalone SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md).
2. **Provide your manuscript and requirements.** Include methods, indexing/quartile, budget, OA preference and whether your deadline means acceptance, publication or indexing.
3. **Compare the report.** Read the reasons, current sources and pending checks for each journal, then choose your submission target.

```text
Use medical-journal-selector to help me choose journals for this manuscript.
Identify its research question, article type, methods and validation first.
Ask for missing requirements, then search and verify candidate journals.
Compare quartile, time and fit routes with sources and pending checks.
Please respond in English.
```

For Chinese output, replace the last line with **“请用中文回复。”** The page language does not set the report language. [Detailed installation](docs/getting-started.md)

## What you receive

**Manuscript → research profile → published precedents → current policies → shortlist.** Keywords discover journals; methods, article type, policy evidence and your requirements determine eligibility.

| Route | What you compare |
|---|---|
| Quartile | Verified JCR quartiles among otherwise eligible journals |
| Time | Comparable evidence for your required deadline stage |
| Fit | Methods, article type, readers and publication precedents |

Each route contains up to three journals, with fewer when evidence is insufficient. Recommendations include official Scope evidence, fit reasons, similar papers and unresolved conditions. Changing facts are checked when used; gaps remain **Not verified（未核到）**. [Read a fictional complete report](docs/examples/fictional-report.md). A shortlist does not predict acceptance.

## What the V2 experiment found

The Trainer iterated across **100 development manuscripts**, then compared frozen r18 with V1, keyword ranking and TF-IDF on **50 separate final manuscripts**.

| Final result, denominator 50 | V1 | V2 |
|---|---:|---:|
| Historical journal in the top ten | 4/50 (8%) | 1/50 (2%) |
| At least one usable recommendation, no retained hard failure | 14/50 (28%) | 16/50 (32%) |
| Cases affected by hard failures | 21/50 | 12/50 |

V2 had fewer affected cases and slightly higher usable coverage, but lower historical-journal hits. Anonymous same-model AI review recorded **11 V2 wins, 26 ties, 8 V1 wins and 5 unresolved**. Results retain all failures and a disclosed reserve-order deviation; they do not establish a clear overall gain or a human-expert validation. [Full comparison, intervals, costs and limitations](docs/evaluation/100-plus-50.md)

V1.0.0 remains stable. The experimental build preserves the evaluated Selector r18; later changes need new validation. [Trainer guide](docs/trainer-guide.md) · [Derived records](docs/evaluation/README.md)

## Before you submit

Read unresolved requirements and official journal instructions. The host supplies model access, file reading and browsing; the Skill adds no model service or JCR subscription. With only an abstract or no browsing, it can organize a profile and search plan, stating limitations. [Privacy](docs/privacy.md) · [Host compatibility](docs/validation-v2.md)

After selecting a journal, pass verified facts to [Journal Cover Letter Skill](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial).

<a id="简体中文"></a>
<details>
<summary><strong>简体中文：用途、安装与100+50结果</strong></summary>

**把医学稿件变成有来源支撑的投稿期刊清单。** 先读懂研究，再查相似论文和当前期刊政策，最后比较**分区、时间、适配**三条路线。

[稳定版 V1.0.0](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0) · [安装教程](docs/getting-started.md#简体中文) · [完整示例](docs/examples/fictional-report.md#简体中文) · [100+50过程页](docs/evaluation/100-plus-50.md)

**100篇开发和50篇最终测评已完成。** V2没有证明整体明显提升，严格稳定发布门槛未通过。正在将评测时保持不变的候选打包为**V2.0.0 实验版**；[查看说明](docs/releases/v2.0.0-experimental.1.md)。

### 三步开始

1. **只下载一种稳定版文件。** Codex用Skill安装包，Claude Code用文件夹ZIP，其他助手可读取独立SKILL.md；入口在本页英文部分。
2. **提供稿件与投稿要求。** 包括方法、收录／分区、预算、OA及截止日期。请说明日期是“接收”“上线”还是“检索”；缺失的关键条件会集中追问。
3. **比较报告后选刊。** 查看每刊的理由、当前来源和待核验项，再决定投稿目标。

```text
使用 medical-journal-selector 帮我选刊，请用中文回复。
先判断研究目的、文章类型、方法和验证方式。
缺少关键投稿要求时问我，再检索并核验候选。
比较分区、时间、适配三条路线，附来源与待核验项。
```

流程是**读稿→研究画像→发表先例→当前政策→期刊清单**。关键词帮助发现候选；方法、文章类型、期刊政策和你的硬条件决定能否推荐。分区、费用和周期等变化信息现查，查不到写“未核到”。每条路线最多三本，证据不足时少列；适配判断不等于录用率。

### 这次迭代得到什么

Trainer用100篇开发稿件逐波改进，再将冻结候选与V1、关键词排序、TF-IDF在另外50篇上比较。开发100篇经历多个版本，不能当成最终版本的100次同版盲测。

| 最终50篇结果 | V1 | V2 |
|---|---:|---:|
| 历史发表期刊进入前十 | 4/50（8%） | 1/50（2%） |
| 至少一个可用推荐，且无保留硬失败 | 14/50（28%） | 16/50（32%） |
| 硬失败涉及篇数 | 21/50 | 12/50 |

V2硬失败涉及篇数减少、可用覆盖略升，但历史期刊命中下降。同模型匿名盲评中V2胜11、平26、负8，另5篇未决。不能合并这些指标宣称明显提升，也不是人类专家验证。全部50篇、失败尝试、储备顺序偏差与消耗均保留。[阅读过程、区间和局限](docs/evaluation/100-plus-50.md)。

稳定下载继续使用V1.0.0。实验版保持最终评测的Selector r18；后续修改不能继承这次结论。GitHub只公开规则、软件与派生结果，不公开私有稿件、答案、提示词及完整日志。

只有摘要或无法联网时，可先整理研究画像和检索方案，并说明材料限制。宿主提供模型、文件读取与联网；Skill不附带模型服务、JCR订阅或录用保证。选定期刊后，可将已核验事实交给投稿信Skill。

</details>

Created by **Jizhou Hu** · [MIT License](LICENSE) · [Report an issue](https://github.com/hujizhou35-cmd/medical-journal-selector/issues)