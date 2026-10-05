# Trainer：如何评测和改进选刊Skill

[English](trainer-guide.md) | **简体中文** · [首页](README.zh-CN.md)

Trainer是给贡献者使用的配套预览工具。它组织案例、盲评、问题诊断和规则回归，改进的是Skill指令，不训练模型参数。普通选刊只需要Selector。

## 安装与准备

[Trainer Skill](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-v1.0.0.skill) · [Plugin ZIP](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/medical-journal-selector-skill-trainer-codex-plugin-v1.0.0.zip) · [SKILL.md](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/trainer-v1.0.0/SKILL.md)

按[安装教程](getting-started.zh-CN.md)操作，目录名使用`medical-journal-selector-skill-trainer`。完整包包含可选Python 3.10+辅助脚本；助手提供文件访问、模型和联网能力，批量调度还需要配置可用的模型调用命令。原生插件导入和所有宿主上的完整训练流程没有普遍验证。

准备：待改进的Selector副本、允许用于评测的已发表研究、作者预先确定的投稿条件，以及独立保管的历史期刊答案。先在独立工作目录用虚构案例检查流程和权限，不把真实答案复制到生成任务里。

## 一个完整改进闭环

1. **准备与遮蔽。** 保留理解研究所需的方法和结果，遮蔽作者、期刊和可直接定位原文的标识；答案放在独立位置。先检查材料完整性和可能的泄露。
2. **生成并封存。** 用冻结的Selector生成推荐，记录版本、来源与文件哈希。看到答案之前不改结果。
3. **独立上下文评审。** 两个未见答案的新上下文评审匿名输出和证据；有分歧再裁决，仍无法解决的保留“未决”。
4. **揭晓并诊断。** 封存评审后才读取历史发表期刊。检查未命中原因；历史期刊不是唯一正确答案，也不代表当前一定合格。
5. **决定是否改规则。** 将有证据支持的通用问题转成候选修改；不修改也是有效决定。
6. **重新检查。** 新上下文运行受影响案例和其他受保护的方法路线。记录通过、失败或回退；暴露过的案例只算回归，不算新的盲测。

## 可以直接使用的请求

```text
使用 medical-journal-selector-skill-trainer。
先检查案例资格、遮蔽方式和答案隔离，再制定小规模试运行方案。
推荐与评审完成封存前，不允许生成或评审上下文读取答案。
只有证据支持可复用改进时才修改规则，并保留失败和回归结果。
不要自动启动100+50实验；先说明所需材料、调用预算与检查方法。
```

## 从小规模试运行到最终测评

先完成一个可审计的小规模闭环，再考虑并行或更多案例。线程数不等于同时模型调用数；保留失败检查点，恢复时避免重复计数。缺失用量记为未知，不当作零。

最终测评前冻结候选、基线、执行配置和未暴露案例集；本项目的最终50篇是在全队列封存后统一揭晓。揭晓后的案例不能再次作为新的盲测集。工具应停止并报告未满足的质量门槛。

## 已完成的100＋50实验

本项目已完成100篇开发和50篇最终测评，V2仍未通过稳定晋级门槛。[阅读方法与结果](evaluation/100-plus-50.zh-CN.md)，或[下载过程包](https://github.com/hujizhou35-cmd/medical-journal-selector/releases/download/v2.0.0-experimental.1/medical-journal-selector-v2.0.0-experimental.1-process.zip)。旧的逐波进度记录保存在过程包及[固定历史提交](https://github.com/hujizhou35-cmd/medical-journal-selector/tree/0f9ffb7adbad863643428475412252e7ca322a42/docs/evaluation)，不代表当前进度。

原文、答案映射、完整提示词和模型日志留在私有工作目录；发布派生数字、方法和必要证据。[参与改进](../.github/CONTRIBUTING.md)
