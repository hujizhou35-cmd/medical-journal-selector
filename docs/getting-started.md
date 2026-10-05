# Install and try the Skill

[简体中文 ↓](#简体中文) · [Homepage](../README.md) · [Stable download](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0)

**Choose one installation method.** The `.skill` and ZIP downloads for a version contain the same selector rules. The links below install **stable V1.0.0**. The completed 100+50 experiment did not support stable V2 promotion; see the [experimental build notes](releases/v2.0.0-experimental.1.md) and [results](evaluation/100-plus-50.md).

## Trying experimental V2

Use a separate test project for the experimental build. It keeps the same Skill name, so install only one selector version in that project's discovery paths. Choose the experimental `.skill`, portable ZIP or standalone `SKILL.md` described in its release notes, and follow the same directory layout below. Check `SHA256SUMS.txt` before installing. Experimental package checks do not imply improved recommendations, native plugin import, or verified behavior in every host.

## Codex

1. Download `medical-journal-selector-v1.0.0.skill` and give the file to Codex.
2. Ask: `Install this Skill in this project's .agents/skills/medical-journal-selector folder.` The `.skill` file is a ZIP archive. The installed folder should contain `SKILL.md`, `references`, `scripts` and `agents` directly.
3. Start a new chat and select **Medical Journal Selector**, or explicitly write `$medical-journal-selector`.

The repository's current `skills/medical-journal-selector` folder contains **experimental r18**, whereas the V1 release downloads retain the original stable files. Use the release matching the version you intend to try. Project `.agents/skills/` and user `~/.agents/skills/` are discovery paths; import buttons can differ between versions. [Official instructions](https://learn.chatgpt.com/docs/build-skills)

**Success check:** run the short prompt below. The assistant should recognize the Skill and handle missing information correctly. A folder existing on disk alone does not prove it loaded.

## Claude Code

1. Download `medical-journal-selector-portable-v1.0.0.zip`.
2. Extract it and copy `medical-journal-selector` into your project's `.claude/skills/`. The final path is `.claude/skills/medical-journal-selector/SKILL.md`; avoid an extra nested folder.
3. Open Claude Code in that project and invoke `/medical-journal-selector`, then provide your manuscript.

For all projects, use `~/.claude/skills/`. Start a new session if the folder is not recognized. Browsing depends on the host's tools and permissions. [Official instructions](https://code.claude.com/docs/en/skills)

**Success check:** when browsing is unavailable, the assistant describes the limitation and keeps the three routes unavailable rather than inventing journal facts.

## Another AI assistant

Download standalone `SKILL.md`, attach it and say: `Read this file and follow its workflow to select journals for my manuscript.` References are included. Full selection needs file-reading and current web access; uploading a file alone does not install it.

Use the portable ZIP if your host supports standard Agent Skills folders. Unchecked hosts are format-portable, not universally tested.

## Codex Plugin option

The ZIP contains `.codex-plugin/plugin.json` and `skills/medical-journal-selector/`. It is intended for Codex versions supporting local plugins; it does not supply browsing or a JCR subscription.

If your version has no ZIP import entry, extract `skills/medical-journal-selector` and install at the Codex path above. This uses the same Skill without a marketplace or MCP configuration. Validation distinguishes package checks from actual plugin loading.

## First, try this prompt

```text
Use medical-journal-selector. I have a nursing qualitative-interview abstract,
but no full manuscript yet. Compare quartile, time and fit routes.
Do not browse in this test and do not guess journal facts.
Explain what additional materials you need and what you can provide now.
Please respond in English.
```

Expect a manuscript profile and search plan, material/browsing limits, and why current rankings are unavailable. It should not invent impact factors, quartiles, fees or acceptance rates.

## Prepare for a real selection

Provide a manuscript or abstract, important methods/supplements, indexing and quartile requirements, budget/currency, OA preference, deadline endpoint and institutional warning lists. Only missing conditions need clarification. An abstract cannot establish all methods or independent validation.

Read pending hard requirements first, then compare routes. Choose a journal before requesting the cover-letter handoff. Specify your report language; V2 follows your request or conversation language independently of this website.

## Update or uninstall

Back up your edits, then replace the old Skill folder. Avoid duplicate copies across discovery paths. Uninstall only your installed folder, preserving other Skills and the parent `.agents` or `.claude` folder.

## Troubleshooting

| Problem | What to check |
|---|---|
| Skill not found | `SKILL.md` is directly inside the correct folder; start a new session |
| Cannot extract `.skill` | Copy it, rename the copy to `.zip`, then extract |
| Old Python version | Helpers need Python 3.10+; use `py -3` on Windows, or the manual workflow |
| JCR requires login | Missing accessible evidence stays Not verified（未核到）; add a permitted source if available |
| Facts differ from an older report | Compare year, currency, article type and check date; new selections recheck changing facts |
| Every route is empty | Inspect hard requirements and evidence gaps; unknown facts are not confirmed matches |

For evaluation and improvement, see the separate [Trainer guide](trainer-guide.md).


<a id="简体中文"></a>
<details>
<summary><strong>简体中文：完整安装教程</strong></summary>

# 安装与第一次使用

[English](getting-started.md) · [中文主页](README.zh-CN.md) · [下载页面](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/tag/v1.0.0)

**选择一种安装方式即可。** `.skill` 和 ZIP 中包含相同的核心规则。推荐安装到当前稿件项目，便于管理不同版本。100+50测评已完成，稳定晋升门槛未通过；上方入口继续安装V1。实验版保留r18，详情见[实验版说明](releases/v2.0.0-experimental.1.md)与[过程页](evaluation/100-plus-50.md)。实验版请装在独立测试项目，不要同时加载两个同名Skill。

## Codex

1. 下载 `medical-journal-selector-v1.0.0.skill`，将文件提供给 Codex。
2. 复制主页的安装指令。`.skill` 是 ZIP 格式，不是可执行程序。安装后的路径应为 `.agents/skills/medical-journal-selector/SKILL.md`，文件夹内还包含 `references`、`scripts` 和 `agents`。
3. 打开新对话，在 Skill 选择器寻找 **Medical Journal Selector**，或明确输入 `$medical-journal-selector`。

仓库当前 `skills/medical-journal-selector` 目录是实验版r18，V1 Release下载保持原稳定文件。请按要使用的版本选择来源。当前官方本地发现路径是项目 `.agents/skills/` 或用户 `~/.agents/skills/`；不假定每个版本都提供相同的文件导入按钮。[官方说明](https://learn.chatgpt.com/docs/build-skills)

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


</details>
