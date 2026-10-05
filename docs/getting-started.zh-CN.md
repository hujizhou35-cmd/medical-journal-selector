# 安装与第一次使用

[English](getting-started.md) | **简体中文** · [返回首页](README.zh-CN.md)

首次使用选择[V1稳定版](releases/v1.0.0.zh-CN.md)，下载一种文件即可。试用[V2](releases/v2.0.0-experimental.1.zh-CN.md)时使用独立项目，避免覆盖同名Skill。仓库中的Selector源码是实验版r18，不是V1。

## 选择安装方式

| 使用方式 | 下载与操作 |
|---|---|
| Codex Skill | 下载`.skill`，它是ZIP文件；将内部文件解压到项目的`.agents/skills/medical-journal-selector/` |
| Codex Plugin | 下载Plugin ZIP；其中包含`.codex-plugin/`元数据与`skills/`目录。原生插件导入未验证；不确定宿主是否支持时使用Skill方式 |
| Claude Code | 同样下载`.skill`，必要时改扩展名为`.zip`；将内部文件解压到项目的`.claude/skills/medical-journal-selector/` |
| 其他助手 | 下载`SKILL.md`并让助手读取全文；参考规则已内嵌，执行脚本不在单文件中 |

Selector V1下载：[Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/medical-journal-selector-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v1.0.0/SKILL.md)

最终目录内应直接出现`SKILL.md`、`references/`、`scripts/`和`agents/`，不要多套一层文件夹。安装后打开新对话，明确要求使用`medical-journal-selector`。只看到文件存在，不代表宿主已加载；以实际调用结果为准。宿主可能需要你开启联网或文件权限。

## 第一次运行

提供稿件和必要补充材料，再说明分区或收录要求、费用上限、开放获取偏好和截止日期。

```text
使用 medical-journal-selector，先读我的稿件。
缺少关键投稿要求时问我，再推荐分区、时间、适配三条路线。
每本期刊附来源、核验日期、理由和待核验项，请用中文回复。
```

成功的调用会先理解研究、追问必要条件，并将无法证实的信息标为“未核到”。只有摘要或无法联网时，应说明材料限制并提供研究画像和检索计划，不编造期刊数据。[输出示例](examples/fictional-report.zh-CN.md)

## Trainer与文件校验

只有想评测或改进Skill时才安装[Trainer](trainer-guide.zh-CN.md)。其目录名为`medical-journal-selector-skill-trainer`，安装方式相同。完整包的可选Python脚本需要Python 3.10+，单文件由助手按指令操作。

Release底部的SHA-256折叠区可校验文件。Windows使用`Get-FileHash -Algorithm SHA256 文件路径`；macOS/Linux使用`shasum -a 256 文件路径`。GitHub自动附加的两项Source code供开发者使用。
