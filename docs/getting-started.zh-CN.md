# 安装与第一次使用

[English](getting-started.md) · [中文主页](README.zh-CN.md) · [下载页面](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0)

**选择一种安装方式即可。** `.skill` 和 ZIP 中包含相同的核心规则。推荐安装到当前稿件项目，便于管理不同版本。V2 正在评测，上方稳定下载仍为 V1，须通过发布检查才会更新。

## Codex

1. 下载 `medical-journal-selector-v1.0.0.skill`，将文件提供给 Codex。
2. 复制主页的安装指令。`.skill` 是 ZIP 格式，不是可执行程序。安装后的路径应为 `.agents/skills/medical-journal-selector/SKILL.md`，文件夹内还包含 `references`、`scripts` 和 `agents`。
3. 打开新对话，在 Skill 选择器寻找 **Medical Journal Selector**，或明确输入 `$medical-journal-selector`。

也可以让 Codex 从本仓库的 `skills/medical-journal-selector` 目录安装。当前官方本地发现路径是项目 `.agents/skills/` 或用户 `~/.agents/skills/`；不假定每个版本都提供相同的文件导入按钮。[官方说明](https://learn.chatgpt.com/docs/build-skills)

**成功标志：** 用后面的测试提示，它能够识别 Skill 并按规则处理缺失数据。仅看到文件夹存在不等于调用成功。

## Claude Code

1. 下载 `medical-journal-selector-portable-v1.0.0.zip`。
2. 解压，把最外层 `medical-journal-selector` 文件夹复制到稿件项目的 `.claude/skills/`。最终路径是 `.claude/skills/medical-journal-selector/SKILL.md`，不要再套一层同名文件夹。
3. 在这个项目内打开 Claude Code，输入 `/medical-journal-selector`，然后提供稿件；也可以直接在请求中点名 Skill。

希望所有项目都能用时，可放到用户目录 `~/.claude/skills/`。若新目录尚未被识别，重启会话。联网功能取决于 Claude Code 当前可用的工具和权限。[官方说明](https://code.claude.com/docs/en/skills)

**成功标志：** 指令能够触发；Agent 在联网不可用时明确说明，并保留三条路线的空结果，不编造期刊数字。

## 其他 Agent

下载独立 `SKILL.md`，提供给 Agent，并说：“请读取这个文件，按其中流程处理我的稿件。”这个文件已经内嵌参考规则。需要文件读取和联网能力才能完成完整任务；单纯把文件上传到不读取它的对话不会自动安装。

如果宿主支持标准 Agent Skills 文件夹，优先使用便携 ZIP。每个平台的安装发现机制不同，未经实际测试的平台仅声明格式可移植，不声称已经验证全部功能。

## Codex Plugin

Plugin ZIP 包含 `.codex-plugin/plugin.json` 和 `skills/medical-journal-selector/`。供支持本地插件开发／导入的 Codex 版本使用；它不是 Claude Code 插件包，也没有自动取得联网或 JCR 权限。

若当前版本没有直接导入 ZIP 的入口，解压后取 `skills/medical-journal-selector` 文件夹，按上面的 Codex 路径安装即可。这条回退路径使用同样的功能，不要求配置插件市场或 MCP。发布记录会区分插件包结构检查与真正的插件加载测试。

## 第一次先试这一句

```text
使用 medical-journal-selector。我有一篇护理领域的质性访谈摘要，暂无全文，
希望同时比较分区、时间和适配。你现在不要联网，也不要猜期刊数据。
请说明还需要哪些材料，并按 Skill 给出目前能交付的内容。
```

正确结果会指出材料和联网限制，提供稿件画像／问题／检索计划，说明三条路线暂不能核验。**不应该凭记忆给出 IF、Q 区、费用或录用率。**

## 正式使用要准备什么

全文或摘要；重要补充方法；分区及收录要求；预算和币种；OA 偏好；时间终点；单位认可的预警名单（如有）。允许 Agent 询问尚未明确的条件。仅有摘要时，它不能替你证明外部验证或完整方法质量。

拿到报告后，先看待核验硬条件，再看三条路线。将期刊选定后，才让 Agent 生成投稿信交接材料。V2 报告先服从你明确要求的语言，否则跟随对话语言，不按主页或论文语言决定。

## 更新与卸载

更新前备份自己改过的内容。下载新版本，用新 Skill 文件夹替换旧版；不同安装路径不要重复保留同名 Skill。卸载时移除自己安装的这个文件夹；不要删除整个 `.agents`、`.claude` 或其他 Skill。

## 常见卡点

| 问题 | 处理 |
|---|---|
| 找不到 Skill | 检查文件夹内直接存在 `SKILL.md`，路径对应当前 Agent；新开会话 |
| `.skill` 无法解压 | 它是 ZIP，可复制一份改为 `.zip` 再解压 |
| Python 版本太旧 | 使用 Python 3.10+；Windows 可用 `py -3`。也可暂不用辅助脚本 |
| JCR 要登录 | 不绕过访问限制；报告写“未核到”，有合法权限时补核验 |
| 报告数字看起来与旧报告不同 | 检查年度、币种、文章类型及来源日期；每次重新核验是预期行为 |
| 所有路线都为空 | 查看硬条件和缺失证据，不把未确认期刊塞进推荐榜单 |

评测和改进请使用独立的 [Trainer 教程](trainer-guide.zh-CN.md)。
