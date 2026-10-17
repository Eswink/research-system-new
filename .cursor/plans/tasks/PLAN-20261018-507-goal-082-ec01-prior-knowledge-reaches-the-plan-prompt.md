---
id: PLAN-20261018-507
slug: goal-082-ec01-prior-knowledge-reaches-the-plan-prompt
title: GOAL-082 cycle 1 — 前序知识进立题会话（EC-01…EC-04）
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-082
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-508-goal-082-ec01-prior-knowledge.md
memory_entries: []
---

# PLAN-20261018-507 — GOAL-082 cycle 1

## 验收条件

- [x] **EC-01**：受治记忆的有界摘录进立题会话的提示词（与检索段**并列**；空集 ⇒ 无该段）
- [x] **EC-02**：上限与 `retrieval_context.DEFAULT_MAX_*` **同一对象**（`is` 判）；截断可见；
      条数上限按确定性顺序
- [x] **EC-03**：提示词那段与 `GET /projects/{id}/memory` 的跨 run 档位记录**逐条逐字**相同；
      反证（新增一条记忆 ⇒ 两读面同时变）
- [x] **EC-04 已按降级梯如实处置**：真实 run 上模型**引用**前序知识这一格 —— **未达成**
      （三次 run 均零命中 `memory_id`），阻塞点已点名并归档（`evidence/…-ec04-evidence.txt`）。
      **本条勾选的是「如实处置」，不是「达成」**；达成与否以 GOAL 的 EC-04 状态为准。
- [x] 两个组合根 + live/e2e 装配都接上（缺省 `None` ⇒ 提示词逐字不变）
- [x] 读数归档进树（`CR=0`）+ 受影响套件零回归

## 目标

把「**前序 run 落库的知识**」送进**立题会话**的提示词，并判它是否可复核。

## ★ 建档实测（为什么这一条是缺口）

1. `examples/protocols/*.yaml`（**23 份**）与全部合约里 `required_capabilities` 出现
   `memory.read` 的 **0 份** —— 能力已放行、有实现、有测试，但**没有协议消费它**；
2. 记忆写入缺省 `MemoryTier.RUN`（`memory_promotion`）⇒ 运行链写入的记忆**下一轮读不到**；
3. 提示词装配面（`session_resolution` / `session_carry` / `retrieval_context`）对 `memory`
   的提及为 **0 / 0 / 1（仅类型）** ⇒ 即便在库也没有消费者；
4. `cross_run_knowledge_v1.yaml` 自陈「本协议**不**声称读到的结论改变了后续 run 的科学结论」。

## 实施清单

1. **WP-A**（装配器）：`packages/application/run_orchestration/prior_knowledge.py` ——
   只读 `MemoryStore.query(tier=...)`；只收 `PROJECT` / `ORGANIZATION`；`expires_at` 过 ⇒ 排除、
   `review_after` 过 ⇒ 收但标注；逐条截断（**复用** `retrieval_context` 的上限）。
2. **WP-B**（渲染 + 拼装）：`retrieval_prompt.render_prior_knowledge_prompt` /
   `compose_prompt`（**先前序、后检索**）；adapter 只拼**已渲染好的**字符串。
3. **WP-C**（接线）：`SessionSpecContext.prior_knowledge` → `AgentSessionSpec.prior_knowledge_prompt`
   → 两个组合根（`composition.py` / `pg_composition.py`）+ `runner_wiring` + 求值点
   （与 `with_retrieval_context` 同一处）。
4. **WP-D**（判据）：`tests/application/run_orchestration/test_prior_knowledge_in_prompt.py`（9 条）
   + `tests/e2e/test_prior_knowledge_reaches_the_prompt.py`（3 条，含反证）
   + `tests/e2e/test_prior_knowledge_changes_the_next_round.py`（3 条，含空库按压）
   + `tests/e2e/test_prior_knowledge_changes_the_plan_live.py`（live，默认 skip）。
5. **WP-E**（实跑）：三次真实 run + 证据归档。

## 影响报告

- **产品代码**：新增一个装配器 + 一个支持件；`retrieval_prompt` 加两段并行入口；
  `task_executor` / `session_resolution` / `phase_runner` / `dependencies` / `runner_wiring`
  各加一条**缺省空**的通道；两个组合根各接一行。**未声明 ⇒ 提示词逐字不变**
  （既有 e2e 24 条 + application/architecture/integration 1408 条零回归）。
- **合约面**：`research_report_plan` 的 purpose 增一段（**前提**：要求模型在**有**前序知识段时
  引用其 `memory_id`；无该段时该段文字自我失效）。不是放宽判据 —— 它让判据考的行为
  在指令里**存在**（此前从未要求过，等于考模型没被告知的事）。
- **读面 / DTO / 路由 / 快照**：零改动（记忆经既有 `GET /projects/{id}/memory` 可读）。
- **写入链**：`MemoryWriteProposal → gate → commit` **一字未动**。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化。**

## 工程记忆

**无可复用事实**（本轮口径全部写进 PLAN 与 RECHECK-508 的可复核观察面；
判据文件本身即事实面，不另立记忆条目）。

## 残余与未覆盖

- **EC-04 未达成**（点名阻塞点见 GOAL）；`RUN` → `PROJECT` 的提升策略不在本轮；
- 多轮累积衰减（哪条记忆该退休）不在射程；记忆全文不进提示词（§10）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01/EC-02 判据 | **9 passed** | `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration/test_prior_knowledge_in_prompt.py -q` |
| EC-03 判据（读面同源 + 反证） | **3 passed** | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_prior_knowledge_reaches_the_prompt.py -q` |
| EC-04 离线（含空库按压） | **3 passed** | `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_prior_knowledge_changes_the_next_round.py -q` |
| EC-04 live | **3 次真实 run**：两段提示词都在场；`memory_id` **零命中**（未达成） | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 uv run --frozen --no-sync python -B -m pytest tests/e2e/test_prior_knowledge_changes_the_plan_live.py -q` |
| 读数归档 | `evidence/GOAL-20261018-082-ec04-evidence.txt` | — |
| 受影响套件 | **1408 passed, 1 skipped**（application + architecture + integration） | — |
| 受撞 e2e | **24 passed** | e2e 报告链 / 检索上下文 / 跨相输入 / 读面对齐 / 多角色 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | IN_PROGRESS | cycle 1 建档（前序知识进立题会话）。 |
| 2026-10-18 | DONE | EC-01/02/03 PASS；**EC-04 未达成**（三次真实 run 模型不引用 `memory_id`，但内容被采纳）⇒ 按降级梯记**未达成** + 点名阻塞点。 |
