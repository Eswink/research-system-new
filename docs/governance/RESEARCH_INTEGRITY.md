# Research Integrity v0.4.0

本文件适用于软件/研发过程，不把系统限定为论文生产。

## Hard Rules

1. VERIFIED Claim 必须有 Evidence。
2. 实验 Metric 必须来自实际 Artifact/Execution。
3. Negative Result 不得被静默删除。
4. Writer/Editor 不得修改事实状态。
5. Reviewer finding 与最终 Decision 分离。
6. 不得伪造 Source、DOI、运行日志或环境信息。
7. External publish 默认需要 Gate。
8. 重大人工干预、模型切换和数据变更必须披露在 Audit。

## Separation of Duties

推荐：

```text
Writer model != all Reviewer models
ExperimentEngineer != sole EvidenceReviewer
Runtime != Evaluation Engine
```

## Contradiction

矛盾 Evidence 不能因多数票自动消失。

Claim 可以是：

```text
SUPPORTED
CONTRADICTED
QUALIFIED
UNRESOLVED
```

## Reproducibility Boundary

用户中转站可能隐藏真实底层模型，因此输出必须区分：

- 配置可复现；
- 代码/数据/环境可复现；
- 模型身份仅部分可观察。
