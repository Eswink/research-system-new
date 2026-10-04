---
id: MEM-20261004-183
title: "会话工具的求值 scope 曾被写成会话 id ⇒ 带 scope 的 allow 规则永不匹配，工具 executor 一次也不会被触达（run 终态却是 SUCCEEDED）"
status: ACTIVE
created_at: 2026-10-04
updated_at: 2026-10-04
scope: repository
confidence: 0.95
review_after: 2027-04-04
source_plans:
  - .cursor/plans/tasks/PLAN-20261004-275-goal-029-ec01-session-tool-actually-executes.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261004-276-goal-029-ec01-session-tool-actually-executes.md
supersedes: []
tags: [policy-scope, session-tools, silent-deny, goal-029, plan-275, verdict-shape]
---

## 做了什么

GOAL-029 建档轮实测到：`PolicyEnforcingAgent._evaluate` 构造 `PolicyRequest` 时把
`scope=self.policy_scope`（= **会话 id**）传进去。`examples/config/policy.yaml` 的带 scope
`allow` 规则要求 **scope 相等**才匹配，而会话 id 永不等于 `project` / `run` /
`approved_tool_providers` ⇒ **每一条**会话工具调用都落 `default_effect: DENY`，
工具 executor **一次也不会被触达**。桥侧 `session_tool_invocation` 经 `execute_tool_call`
求值同样**不带** scope（运行链用 `phase_capabilities.ScopedPolicy` 补，会话面没有对应补法）。

## 为什么这样做

两件事被混为一谈：**会话身份**（`session_id`，用于 `_queue_approval` 的
`RuntimeEvent.session_id`）与**求值 scope**（策略规则里的 `scope:` 字段）。前者是运行时标识，
后者是策略匹配键。混用后失败形态是**静默的**：`_execute_action_event` 返回 `AgentErrorEvent`
（不是异常），agent loop 照常收尾 ⇒ run 终态 `SUCCEEDED`。因此「run 绿」**不能**作为
「工具跑通了」的证据。实测对照（同一装配只差一个字段）：`artifact.read`（**已放行**）
修复前 `executor_reached=[]`，修复后 `executor_reached=['hi']`。

## 怎么做与复现

- **判据要读「executor 是否真被触达」**，不能读 run 终态字符串 —— 后者会被
  「拒绝后 agent 照样收尾」骗过。见
  `tests/adapters/openhands/test_session_tool_reaches_executor.py`：在工具 executor 里记录调用，
  四向断言（已放行 ⇒ 触达；未放行 ⇒ 拒；需审批 ⇒ 拒；两条门同源）。
- **补 scope 时复用既有那一张表**：`packages/application/preflight/policy_check.policy_scope_for`
  （或既有 `ScopedPolicy` 包装），**不要**另造第二张 —— 仓内已有四处同源点：preflight
  `_evaluate_requirement`、运行链 `ScopedPolicy`、沙箱实验 `governed.py`、会话面（本轮）。
- **会话 id 仍然要传**（`_queue_approval` 用它标识会话）——修的是 **scope 字段**，不是会话标识。
- 复现配方：`uv run --frozen --no-sync python -B -m pytest
  tests/adapters/openhands/test_session_tool_reaches_executor.py -q -p no:randomly`；
  按压（把 `scope=policy_scope_for(tool_name)` 改回 `scope=self.policy_scope`）⇒ 2 failed。
- **为什么 Fake 策略面看不见它**：`FakePolicyEvaluator` 的缺省决策是 `ALLOW`，恰好掩盖这条
  静默 DENY ⇒ 判据必须用**真实** `NativePolicyEvaluator(policy.yaml)` 才咬得住。

## 适用边界

本仓任何「执行期策略求值 + 能力带声明 scope」的调用点都适用（会话工具、运行链能力步、
沙箱实验、门链）。**不**适用于无 scope 的规则（那类规则不要求 scope 相等）。
`policy_enforcing_agent.policy_scope` 字段仍在（会话身份用途）——字段名与求值 scope 的
区分靠注释与判据行为，**没有**类型级区分。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261004-275-goal-029-ec01-session-tool-actually-executes.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261004-276-goal-029-ec01-session-tool-actually-executes.md`
- 事实：`adapters/openhands/policy_enforcing_agent.py`（`_evaluate`）、
  `adapters/openhands/session_tool_invocation.py`（`make_tool_invoker`）、
  `examples/config/policy.yaml`（带 scope 的 allow 规则）、
  `packages/application/tool_plane/execution.py`（`_TOOL_ACTION` / `evaluate_execution_policy`）
