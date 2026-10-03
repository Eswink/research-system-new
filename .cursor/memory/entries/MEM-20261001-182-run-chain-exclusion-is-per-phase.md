---
id: MEM-20261001-182
title: "run-chain 排除是 per-phase 的：一个 provider 在别的 phase 仍可能在会话工具面内 ⇒ 绑定必须按 phase 逐面核"
status: ACTIVE
created_at: 2026-10-01
updated_at: 2026-10-01
scope: repository
confidence: 0.95
review_after: 2027-04-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261001-271-goal-028-ec03-multi-role-subiteration-on-the-default-assembly.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261001-272-goal-028-ec03-multi-role-subiteration-on-the-default-assembly.md
supersedes: []
tags: [session-tools, run-chain, per-phase, goal-028, plan-271, session-tool-bindings]
---

## 做了什么

GOAL-028 EC-03 给真实多 role 协议（`multi_role_research_v1.yaml`）的 `review` phase
补会话工具绑定。首版只绑了**三条** —— 我推断「`europe_pmc` 被 scouting 声明为 run-chain
⇒ 它不在会话工具里」。**实测判红**：会话创建点名
`ToolDefinition 'europe_pmc' is not registered`。

## 为什么这样做

冻结集（`flatten_tool_providers(plan)`）是 **plan 级**的：所有 phase 的
`ToolRequirement.provider_ids` 取并集 ⇒ 四个 provider 都在冻结集里。
而 run-chain 排除（`run_chain_tool_ids(plan, phase_id)`）是 **per-phase** 的：

```python
if phase is None or phase.capability_execution is not CapabilityExecution.RUN_CHAIN:
    return ()
```

—— 它只对**声明了** `capability_execution: run_chain` 的那个 phase 返回非空。
所以 `scouting` 的会话工具面为空（全被排除），但 `review` 的会话工具面仍是
`冻结集 − ∅` = **四个全在**。我按「plan 级排除」去推，漏掉了一个。

## 怎么做与复现

- **判定某个 provider 要不要绑定，必须逐 phase 算它的会话工具面**，不要按 plan 级推断：

  ```python
  face = session_tool_face(plan, phase.id)          # 冻结集 − 本 phase 的 run-chain 排除
  bound = dict(session_tool_bindings(plan, phase.id))
  assert set(face) <= set(bound)                    # 面内每一个都必须绑
  ```

- 复现配方：`uv run --frozen --no-sync python -B -m pytest
  tests/e2e/test_multi_role_on_the_default_assembly.py -q -p no:randomly`；
  按压形态（先红后绿）：删掉协议里 `europe_pmc` 那条 `session_tool_bindings` ⇒ 3 failed，
  失败文本正是 `ToolDefinition 'europe_pmc' is not registered`。
- **顺带一条**：`strategy: deterministic` 且合约声明 `experiment: {}` 的 phase
  **不创建会话**（`phase_runner` 按 `contract.experiment is not None` 派给
  `dispatch_experiment`）⇒ 它的会话工具面**从不被消费**，对它要求绑定是加一行没有语义的
  声明。判据因此按 `strategy` 分流，并另断言「恰有一个带会话面的 phase」防分流过宽。

## 适用边界

本仓所有「冻结集 + 会话工具面」相关的声明与判据（`session_tool_bindings`、
`capability_execution: run_chain`、`session_tool_face` / `session_tool_ids`）。
**不适用于**：preflight / 策略 / 冻结面 —— 那些是 plan 级的，四个 provider 一律在内
（这正是「声明化排除 ≠ 静默丢弃」的另一半：排除不改任何检查面）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261001-271-goal-028-ec03-multi-role-subiteration-on-the-default-assembly.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261001-272-goal-028-ec03-multi-role-subiteration-on-the-default-assembly.md`
- 事实：`packages/application/run_orchestration/session_resolution.py`（`run_chain_tool_ids` / `session_tool_face`）
