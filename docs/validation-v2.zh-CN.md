# 宿主兼容性与验证范围

[English](validation-v2.md) | **简体中文** · [安装教程](getting-started.zh-CN.md)

`.skill`与Plugin ZIP中的规则和脚本可检查，但打包成功不等于每个宿主都完成了实际加载。原生插件导入、全部宿主的端到端行为没有普遍验证。单文件模式依赖助手读取指令并手动遵循内嵌参考规则。

Windows/Linux与Python 3.10/3.12的自动检查验证软件行为、文件结构与构建。当前三种构建入口分别处理稳定Selector、实验Selector和Trainer，V1/V2生成字节必须匹配原发布校验值。

[历史验证记录](validation.md)与[原V2下载验证](releases/v2.0.0-experimental.1-verification.json)保留当时范围，原记录中的七项附件不是当前精简清单。当前文件与校验值以[发布页](releases/v2.0.0-experimental.1.zh-CN.md)为准。软件检查不能证明推荐准确率提高；[实验结果](evaluation/100-plus-50.zh-CN.md)单独报告。
