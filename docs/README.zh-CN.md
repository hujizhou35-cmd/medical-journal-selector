# Medical Journal Selector｜医学选刊助手

**从读懂稿件、查找期刊到逐项核验，帮你比较适合这篇文章的投稿选择。**

[English](../README.md) · [下载 v1.0.0](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0) · [安装教程](getting-started.zh-CN.md) · [完整报告示例](examples/fictional-report.zh-CN.md)

## 从这里开始

选择你正在使用的 AI 助手，**只需下载一种文件**。

- **Codex：** 下载 [Skill 安装包](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill)，将文件交给 Codex，安装到当前项目的 `.agents/skills/medical-journal-selector/`；[查看步骤](getting-started.zh-CN.md#codex)。
- **Claude Code：** 下载 [Skill 文件夹 ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-portable-v1.0.0.zip)，将其中的文件夹放进 `.claude/skills/`，再调用 `/medical-journal-selector`；[查看步骤](getting-started.zh-CN.md#claude-code)。
- **其他 AI 助手：** 下载 [独立 SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md)，让助手读取这个文件，再提供稿件。

完整安装步骤和 Codex Plugin 的使用方式见[安装教程](getting-started.zh-CN.md)。

## 它怎样完成选刊

1. **阅读稿件。** 梳理研究问题、研究设计、数据来源、主要发现和目标读者，分清稿件已经提供的信息与尚未说明的内容。
2. **判断领域与文章类型。** 先识别所属医学大类，再细分到具体主题；判断是原创研究、综述、病例报告等，提取检索词，同时查看研究方法和验证方式。
3. **确认投稿要求。** 只追问影响选刊的缺失条件，例如 JCR 分区、收录、预算、开放获取、排除期刊和截止日期。时间要求会分清“接收”“上线”还是“完成检索”。
4. **检索候选期刊。** 从相似已发表研究和相关期刊入手，跨出版社寻找候选。公共数据库分析优先查看近 24 个月的同类研究；其他文章以近 5 年为背景，侧重近期证据。
5. **逐刊核验。** 阅读当前 Aims & Scope、文章类型和方法政策，现查收录、JCR、影响因子、周期、开放获取、费用及相关预警名单。
6. **筛选并比较三条路线。** 先执行你的硬条件，再分别按分区、时间和适配程度比较；需要补查的条件单独列出，被排除的期刊说明原因。
7. **复查证据，交付报告。** 对缺失或冲突信息补查，必要时调整名单，最后提供推荐理由、来源和待确认事项。由你选定期刊后，再进入投稿信流程。

关键词用于发现候选；真正决定是否合适的是稿件方法、期刊当前政策和你的投稿要求。

## 带着稿件试一次

提供全文，或先提供摘要，然后复制：

```text
使用 medical-journal-selector 帮我选刊，请用中文回复。
先判断稿件领域、文章类型、研究方法和验证方式。
缺少关键投稿要求时集中问我，再检索并核验候选期刊。
同时比较高分区优先、时间优先和适配优先三条路线，
说明每项推荐的理由与当前来源；未确认的信息写“未核到”。
```

想用英文时，可以改成 **“Please respond in English.”** 项目主页的显示语言不会限制报告语言。

也可以补充：“我需要 JCR Q2 及以上，总费用不超过［预算和币种］，希望在［日期］前接收。”这些是填写示例，不是默认要求。

## 你会得到什么

| 路线 | 优先比较什么 |
|---|---|
| **高分区优先** | 在范围、方法和投稿条件基本符合后，比较已核验的 JCR 分区 |
| **时间优先** | 按你需要达到的时间终点，比较口径相近的周期 |
| **适配优先** | 方法、文章类型、目标读者及近期发表先例的吻合程度 |

每本期刊都附有官网 **Aims & Scope 原文**、具体适配理由、相似论文、投稿信息和来源。每条路线最多列 3 本，证据不足时少列。适配判断不等于录用概率。

**[查看完整报告示例 →](examples/fictional-report.zh-CN.md)** 示例中的期刊与数字均为虚构，用来展示你会收到怎样的报告。

## 改进选刊 Skill

**Medical Journal Selector Skill Trainer** 先对脱敏稿件选刊、封存推荐和独立评审，再揭晓真实发表期刊，将有依据的问题变成可复用规则，并用未参与修改的文章验收。

V2 候选和 Trainer 正在评测：**有效开发已完成 62／100 篇，最终测试仍为 0／50 篇，另保留 24 篇协议试运行。**原始分数和负面结果保留。收到连接恢复报告后，正在补跑缺失的回归步骤，同时调用上限为三，暂不增加完成数。发布门槛通过前，稳定下载仍为 **V1.0.0**。[Trainer 教程](trainer-guide.zh-CN.md) · [评测状态](evaluation/README.zh-CN.md)

## 常见问题

<details>
<summary><strong>只有摘要，可以开始吗？</strong></summary>

可以先判断主题并开始检索。想更准确地评估方法是否符合期刊要求，建议再提供完整方法和相关补充材料。

</details>

<details>
<summary><strong>可以处理哪些文章？</strong></summary>

包括临床、护理、基础实验、公共数据库、生信、预测模型、网络药理／毒理、综述、Meta 分析、文献计量及病例报告。它会按你的具体文章类型和方法检查期刊要求。

</details>

<details>
<summary><strong>能按分区、预算或毕业时间筛选吗？</strong></summary>

可以。告诉它哪些是必须满足的条件，哪些只是偏好。涉及毕业时间时，需要说明是接收、上线还是检索；报告会比较现有周期证据，但不能保证完成日期。

</details>

<details>
<summary><strong>为什么有些信息显示“未核到”？</strong></summary>

表示本次没有从可靠的当前来源确认，报告会说明缺在哪里。如果这项信息关系到你的硬条件，该刊会进入待核验名单，不会被当作已经满足要求的推荐。

</details>

## 选好期刊以后

将选定期刊、稿件事实和已核验的适配理由交给 [Journal Cover Letter Skill](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial)，继续准备投稿信。

---

作者：**Jizhou Hu** · [MIT 许可](../LICENSE) · [隐私说明](privacy.zh-CN.md) · [反馈问题](https://github.com/hujizhou35-cmd/medical-journal-selector/issues)
