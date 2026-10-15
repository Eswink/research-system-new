---
id: PLAN-20261015-475
slug: goal-078-ec04-live-run-on-the-new-relay
title: GOAL-078 cycle 4 — 新站真实 run 上检索内容到达会话（EC-04）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261014-078
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-476-goal-078-ec04-live-run-on-the-new-relay.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-221-declared-but-never-constructed-is-a-dead-seam.md
---

# PLAN-20261015-475 — GOAL-078 cycle 4

## 验收条件

- [x] live 判据扩到断言**上下文到达会话**（读面非空 + 逐条指向本次检索证据）
- [x] 同源判据（会话 `retrieval_digest` 在场于读面制品 digest）
- [x] 新站真实 run 实跑通过
- [x] 上下文面读数**落盘**（run id / ref / digest 记档）

## 目标（本 cycle 的可独立验收主题）

**EC-04**：在**新站**（`discovery-api.intern-ai.org.cn` / `deepseek-v4-flash-vision`）上
跑一次真实 run，证「**活检索取得的内容真的进了下游会话**」——不是离线夹具里的模型。

## 设计

- **复用既有 live 判据**（`tests/e2e/test_research_report_chain_live.py`，GOAL-077 建的）
  并**扩它**：装配侧补 `retrieval_context` 那一行（run-ready/live 判据不经组合根，
  与其余三条缝同一形态）+ 装 spec 记录器（观察、不改行为）。
- **上下文取证单列**：`tests/e2e/retrieval_context_support.py`（判据文件贴 450 行上限）。
- **两向都留读数**：下游非空（4 条真标识）/ 上游空且带理由。

## 实施清单

1. **WP-A**：live 装配补 seams + 记录器；取证助手单列。
2. **WP-B**：live 判据扩 2 处断言（读面非空 + 逐步指向 `RETRIEVED` 证据；同源 digest）。
3. **WP-C**：读数落盘（`evidence/GOAL-20261014-078-ec04-context-evidence.txt`）+ 记录 + m0。

## 影响报告

- **产品代码零改动**（EC-04 只扩判据）。
- **判据面**：live 模块 + 1 个支持件；既有判据零放宽。

## 残余与未覆盖

- EC-05（自举收口）不在本 cycle；
- 模型是否**真的读了**上下文 —— 属观测面（本 EC 只证「内容进了会话规格」）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| live 实跑 | **1 passed in 72.64s** | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 … -m pytest tests/e2e/test_research_report_chain_live.py -q` |
| 上下文面读数 | run `218280b6…`：下游 `multi_role_review` **4 条**真标识 + digest `sha256:8cfa62f3…`；上游 `research_report_plan` 空 + 点名理由 | `evidence/GOAL-20261014-078-ec04-context-evidence.txt` |
| 读面 | 两件上下文制品都在 `GET /runs/{id}/artifacts` 上（下游 4 条 / 上游 0 条带理由） | 同上的落盘读数 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 4 建档（EC-04 的 live 取证与扩判据）。 |
| 2026-10-15 | DONE | live 实跑通过（72.6s）；上下文面读数落盘；两向读数齐备。 |
