# 设计记录与参考作品

## 2026-10-05 页面改版

参考 [Journal Cover Letter](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial) 的主工具与 Trainer 分流、独立中文页面及三种安装格式，以及 [PaperQA](https://github.com/Future-House/paper-qa) 的用途优先、快速开始在前的顺序。以下旧设计记录保留其历史范围；当前结构以首页为准。

当前顺序：用途 → 选刊／改进两个入口 → 三步使用 → 输出示例 → 简短版本比较 → Trainer → 贡献。英文与中文分别成页，Release 默认英文并链接完整中文说明。实验记录集中为带校验清单的过程包，主分支保留源码和易读报告。

## 产品边界

V1.0 是可移植的 Agent Skill 和 Codex 分发包。用户在现有 Agent 内提供稿件、回答必要问题并取得报告。GitHub 首页负责解释、下载和引导；无需独立上传网站或自建模型后端。

保留三条路线，避免把分区、耗时和适配压缩成一个难以解释的总分。脚本执行可明确检查的过滤；医学判断由 Agent 结合实际稿件与现查来源作出，并明确其推断性质。

## 参考来源与取舍

调研与文档核对日期：2026-10-01 至 2026-10-02。以下描述为项目公开资料中的功能，不是对推荐质量的独立测评。

| 作品 | 借鉴 | 本项目的取舍 |
|---|---|---|
| [Elsevier Journal Finder](https://www.elsevier.support/publishing/answer/how-can-i-find-the-right-journal-for-my-paper-in-journal-finder) | 简短输入与期刊指标比较 | 跨出版社；周期必须说明起止与统计人群 |
| [Springer Nature Finder](https://link.springer.com/journals) | 查找期刊与 OA 费用／资助信息 | 将适用费用和分区等硬条件明确区分 |
| [JANE](https://jane.biosemantics.org/faq.php) | 以生物医学相似论文发现期刊 | 相似度与发表数量不转成录用率 |
| [Jot](https://github.com/Townsend-Lab-Yale/journal_targeter) | 论文、引用、指标共同辅助选择 | 借鉴多维比较思路；未复制 GPL 代码或概率代理公式 |
| [sci-select](https://github.com/keros68/xiaoyu-skill/tree/main/skills/sci-select) | 短安装指令、稿件画像、来源状态 | 当前事实每次重查；增加医学方法和三路线；未复制数据或代码 |
| [Journal Atlas](https://github.com/Zaious/journal-atlas) | 证据缺口和期刊方法偏好 | 不以静态知识库替代当前数据 |
| [Cover Letter Skill](https://github.com/hujizhou35-cmd/journal-cover-letter-tutorial) | 文件选择表、三步教程、多个 Release 资产 | 沿用作者自己的分发模式，并加 Claude Code 标准文件夹包 |
| [Superpowers](https://github.com/obra/superpowers) | 按使用的 Agent 区分安装路径 | 首页保留三个主要人群，避免过长平台菜单 |
| [Anthropic Skills](https://github.com/anthropics/skills) | 自包含 Skill 文件夹和明确示例 | 通用规则不硬编码某一个 Agent 的工具名 |

## 主页布局

一句话作用 → 下载选择 → 三步使用 → 可复制提示词 → 完整示例 → 数据边界 → FAQ → 开发说明。

GitHub 原生排版优先。示意图使用蓝色表示分区、琥珀色表示时间、青绿色表示适配，三条路线下方连接同一套证据。正文保持原生字体；图中采用系统无衬线字体，数字／标识使用等宽字体。配色：深蓝 #102A43、蓝 #1768AC、青绿 #0A7D70、琥珀 #A56418、浅底 #F6F9FC、灰蓝 #526477。重要信息同时以文字表格提供，不依赖颜色或图片识别。

## 循环与失败处理

运行时：读稿 → 追问缺失条件 → 检索 → 核验 → 三路线 → 审查 → 必要时最多补查两轮 → 报告。没有新证据时保留未核到，不重复空转。

开发时：主页／规则／证据／兼容／发布各自执行“构建→检查→修复→复查”。同一阻塞连续三次未解决就报告具体原因，不用失败结果宣称验收通过。V1.0 不包含已发表论文回测或自动训练功能。
