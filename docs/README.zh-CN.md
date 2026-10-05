# 医学选刊工具

[English](../README.md) | **简体中文**

把医学稿件变成一份**有来源、可核查的投稿期刊清单**。提供稿件与投稿要求，工具会按**分区、时间、适配**三条路线推荐期刊，说明理由和仍需核验的事项。

## 从这里开始

| 我想做什么 | 使用什么 | 入口 |
|---|---|---|
| 为稿件选择期刊 | **Selector V1.0.0 稳定版** | [下载与说明](releases/v1.0.0.zh-CN.md) |
| 评测和改进选刊规则 | **Trainer 配套预览版** | [下载与说明](releases/trainer-v1.0.0.zh-CN.md) · [教程](trainer-guide.zh-CN.md) |

**选刊工具下载：** [Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md)

只选一种即可：`.skill` 是单个 Skill 的安装包；Plugin ZIP 包含 Codex 插件信息与 Skill；`SKILL.md` 是供其他助手读取的完整单文件指令。它们不是独立的AI服务；模型、文件读取与联网由你使用的助手提供。[安装教程](getting-started.zh-CN.md)

## 三步开始选刊

1. **安装一个文件。** 首次使用选择V1稳定版，然后打开新对话。
2. **提供稿件与投稿要求。** 包括收录或分区、预算、是否接受开放获取及截止日期；说明期限指接收、在线发表还是检索。
3. **比较推荐清单。** 阅读每本期刊的证据、适配理由和待核验事项，再决定投稿目标。

```text
使用 medical-journal-selector 帮我选刊，请用中文回复。
先判断研究问题、文章类型、方法和验证方式。
缺少关键投稿要求时问我，再检索并核验候选期刊。
比较分区、时间、适配三条路线，附来源与待核验项。
```

也可以要求工具使用英文或其他语言输出。

## 你会得到什么

**读稿 → 理解研究 → 查找相似论文 → 核验当前期刊政策 → 比较候选。**

| 路线 | 比较内容 |
|---|---|
| 分区优先 | 在其他条件合格的期刊中，比较已核验的JCR分区 |
| 时间优先 | 比较与你所需投稿阶段和期限对应的时间证据 |
| 适配优先 | 比较研究方法、文章类型、读者与发表先例 |

每条路线最多三本期刊，证据不足时可以更少。变化信息附来源和日期，查不到就写“未核到”。推荐清单不代表录用概率。

[查看完整虚构示例](examples/fictional-report.zh-CN.md) · [隐私说明](privacy.zh-CN.md)

## V1 与 V2 实验版有什么区别

V1建立三条推荐路线和当前来源核验。V2进一步细化方法政策、来源用途和最终报告审计。Trainer完成了**100篇开发案例**，再对冻结的V1和V2进行**50篇最终测评**。

| 最终50篇指标 | V1 | V2 |
|---|---:|---:|
| 历史发表期刊进入前十 | 4/50，8% | 1/50，2% |
| 至少一个可用推荐，且无保留硬错误 | 14/50，28% | 16/50，32% |
| 硬错误涉及案例 | 21/50，42% | 12/50，24% |
| 保留硬错误标记数 | 37 | 41 |

V2硬错误涉及案例更少，但标记总数更多，历史期刊命中更少。AI评审记录为**V2胜11、平26、V1胜8、未决5**。结果没有证明V2整体更好；**V1继续作为稳定版，V2继续作为实验版**。

[V2实验版与下载](releases/v2.0.0-experimental.1.zh-CN.md) · [方法、消耗与完整比较](evaluation/100-plus-50.zh-CN.md)

## 用 Trainer 改进工具

Trainer组织这样的闭环：**遮蔽已发表案例 → 封存推荐 → 在独立上下文评审 → 揭晓历史期刊 → 诊断 → 检查可复用的规则修改**。它改进的是Skill指令和检查流程，不训练模型参数。

**Trainer下载：** [Trainer Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/SKILL.md)

预览版面向想研究或改进流程的贡献者，普通选刊不需要安装。[新手教程](trainer-guide.zh-CN.md) · [公开实验资料](evaluation/README.zh-CN.md)

## 参与改进

欢迎改进教程、兼容性、来源核验与推荐规则。[报告问题](https://github.com/hujizhou35-cmd/medical-journal-selector/issues/new/choose)、阅读[贡献指引](../.github/CONTRIBUTING.md)，或[提交Pull request](https://github.com/hujizhou35-cmd/medical-journal-selector/compare)。

选定期刊后，可使用[投稿信工具](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial)根据已经核实的稿件信息撰写投稿信。

作者：**Jizhou Hu** · [MIT许可证](../LICENSE) · [引用信息](../CITATION.cff)
