# Cursor Framework Learning System v0.4.0

目标：从真实 Research OS 开发经验中学习，同时避免一次偶发失败污染长期 Rule/Skill。

## Lifecycle
```text
Runtime Observation
→ Learning Proposal
→ Cluster / Relation Analysis
→ Replay Before
→ Candidate Change
→ Replay After
→ Deterministic Validation
→ Scoped Approval when required
→ Promotion / Reject
```

Observation 不是知识，Proposal 不是事实，Promotion 不是自动批准。

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
