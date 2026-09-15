---
id: MEM-20260915-026
title: 能力策略镜像只覆盖 preflight 能力；门链能力需要第二个多 scope 常量
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.9
review_after: 2026-12-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260914-049-memory-capability-policy.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-049-memory-capability-policy.md
supersedes: []
tags:
  - policy
  - memory
  - capability
  - api
  - contract-mirror
---

# MEM-20260915-026 — policy 镜像契约：preflight 单 scope vs 门链多 scope

## 做了什么

cycle 9（PLAN-049）把 `memory.write` 接进策略面：`examples/config/policy.yaml`
声明四个 tier 的 allow 规则、`capabilities.yaml` 注册能力、控制面装配真实
`NativePolicyEvaluator`，并新增只读端点 `GET /policy/capabilities`。

## 事实一：`_CAPABILITY_SCOPE` 只描述 preflight 工具需求

`packages/application/preflight/policy_check.py::_CAPABILITY_SCOPE` 是
`dict[str, str]`（一能力一 scope），它服务的是 **preflight 阶段**：`ToolRequirement`
的能力去 policy.yaml 找 scope（`workspace.read → project` 等）。而
`memory.write` 的求值发生在**门链阶段**（`memory/gate.py::_evaluate_policy`），
scope 由领域语义给出（memory tier），一个能力对应四个 scope。两条路径的 scope
来源不同，因此新增了第二个常量：

```python
_GATE_CAPABILITY_SCOPES: dict[str, frozenset[str]] = {
    "memory.write": frozenset({"SESSION", "RUN", "PROJECT", "ORGANIZATION"}),
}
```

镜像一致性测试因此从"单值映射 == 声明"改为**并集相等**：
`_CAPABILITY_SCOPE ∪ _GATE_CAPABILITY_SCOPES == policy.yaml 中带 scope 的声明对`
（外加 `_CAPABILITY_SCOPE == 声明 − memory.write`）。这是**同样严格**的重写
（不是放宽成子集），改的只是"谁能覆盖一个能力"。

## 事实二：接线的安全姿势 = 先把默认行为钉成显式规则

系统默认 `default_effect: DENY`。若只把 evaluator 注入门链、不在 policy.yaml 里
为四个 tier 显式写 allow，则 `memory.write` 会落到 default DENY，把既有写入全部
打回 422。接线必须先补规则（默认行为不变），再谈"运维可收紧"——收紧（deny /
require_approval）只改 YAML，无需改代码。

## 为什么这样做

- 不建第二套 permission model：门链 policy 阶段复用同一 `PolicyEvaluator` Port 与
  同一份 policy.yaml；可见性端点也用运行期同一求值器算"逐 scope 有效判决"
  （不做第二套判定，避免"显示 ALLOW、实际 DENY"的漂移）。
- 单 scope 常量和多 scope 常量分开，是为了让"preflight 能力"和"门链能力"的
  语义边界留在类型里，而不是把 `dict[str, str]` 硬改成多值表示去覆盖老逻辑。

## 怎么做与复现

- 复现 1（镜像契约）：`pytest -q tests/application/test_m2_audit.py`（16 passed，
  含并集相等断言）。
- 复现 2（运行时门）：`pytest -q tests/application/memory/test_policy_wiring.py`
  （8 passed：四 tier 默认放行、PROJECT/ORGANIZATION 仍走 curator 门、deny 的
  scope 特异性、require_approval 无 curator 拒绝/有 curator 通过）。收紧用
  `PolicyDefinition(deny=...+PolicyRule(capability="memory.write", scope="SESSION"))`。
- 复现 3（可见性 + API 拒绝）：`pytest -q tests/api/test_policy_view_api.py`
  （4 passed：503 诚实缺口、快照字段、收紧后 422 detail =
  `policy deny: matched deny rule`、默认策略 201/ALLOW）。
- 复现 4（装配共享）：`services/api/assembly.py::policy_bindings()` 同时被
  `composition._assemble_sqlite`、`pg_composition.build_postgres_apideps` 与
  `tests/api/run_fixtures.make_run_ready_deps` 使用——三处同源，避免"开发路径
  注入了、PG 还是 None"。

## 适用边界

适用于"给记忆门链或其他门链能力加策略"这一场景。不改变：curator 门语义、
provenance 白名单、sanitize-before-commit；policy 未加载时不伪造默认策略
（端点 503、门链退回 provenance+curator 兜底）。策略是**进程启动时读取**的
只读文件，无热加载、无规则 CRUD（变更需改 YAML 并重启控制面）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260914-049-memory-capability-policy.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260915-049-memory-capability-policy.md`
- 代码：`packages/application/preflight/policy_check.py`（两个镜像常量 +
  `gate_capability_scopes()`）、`packages/application/memory/gate.py`
  （`_evaluate_policy` 回传 reason）、`services/api/routers/policy.py`、
  `services/api/assembly.py`
- 相关：MEM-20260914-023（夹具实例共享同侧教训）
