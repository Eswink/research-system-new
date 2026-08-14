# Cursor Framework Learning System v0.4.0

目标：从真实 Research OS 开发经验中学习，同时避免一次偶发失败污染长期 Rule/Skill。

## Lifecycle
```text
Runtime Observation
→ Experience Entry (低置信度缓冲，.cursor/experience/)
→ Learning Proposal
→ Cluster / Relation Analysis
→ Replay Before
→ Candidate Change
→ Replay After
→ Deterministic Validation
→ Scoped Approval when required
→ Promotion / Reject
```

Observation 不是知识，Experience Entry 不是事实，Proposal 不是事实，Promotion 不是自动批准。

## Promotion gates
任何 `ACCEPTED` proposal 必须：
1. 有可追溯证据；
2. 普通经验至少来自两个独立 task/attempt；安全严重问题必须有确定性复现；
3. 有 before/after replay；
4. 有 target paths 和 blast radius；
5. 运行 deterministic validators/regression；
6. 保存 validation evidence；
7. 有显式 promotion authorization；
8. 根据风险按需调用相关 reviewer，不规定固定 reviewer 人数或固定审核轮数。

建议 reviewer 路由：
- Architecture/ADR/Domain boundary → `architecture-reviewer`
- Validator/runtime correctness → `verification-reviewer`
- Hook/secret/MCP/permission/supply chain → `security-governance-reviewer`

Reviewer 是风险控制工具，不是每个任务强制的数量配额。

## 非确定性观察分流

模型采样行为（如并行 wave 是否单消息批量发出、格式遵循、工具调用策略）是非确定性观察，无法产出可复现的 before/after replay，因此不进入上述 Promotion gates，按以下路径分流：

1. 记录路径：写入 `.cursor/knowledge/KNOWN_CAVEATS.md` 的 Model Behavior 小节（或其他知识文档），标注为工程观察，不晋升为 Rule/Skill。
2. 跨会话同类观察 ≥2 次时，可先经 `capture-experience` 沉淀为 `.cursor/experience/` 条目，供 sessionStart 注入摘要。
3. 不得用"模型行为观察"绕过确定性验证要求去修改 Rule、validator 或授权规则。

该分流不改变 Promotion gates 的准入条件，也不把低置信度观察升格为工程事实。
