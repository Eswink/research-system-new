---
id: PLAN-20261015-473
slug: goal-078-ec03-what-entered-the-context-is-readable
title: GOAL-078 cycle 3 — 「进了什么」在既有读面上可复核（EC-03）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-15
parent_goal: GOAL-20261014-078
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-474-goal-078-ec03-what-entered-the-context-is-readable.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-221-declared-but-never-constructed-is-a-dead-seam.md
---

# PLAN-20261015-473 — GOAL-078 cycle 3

## 验收条件

- [x] 上下文落成**制品**（task 前缀命名 ⇒ 落在既有 `GET /runs/{id}/artifacts` 上）
- [x] **同源**判据：写盘字节**就是** `retrieval_digest` 的源（读面值不可能与装配点分叉）
- [x] 载荷**自足**：run 标识 + 逐条（标识 / 证据 id / 制品 id / 摘录）
- [x] 空集合也写且**带理由**（「没有内容进去」本身要读得出来）
- [x] HTTP 面端到端取证（下游非空 / 上游空且带理由 / digest 与会话同源）
- [x] 既有判据零放宽（定向套件 + 全量 m0 绿）

## 目标（本 cycle 的可独立验收主题）

**EC-03**：让「哪些内容进了会话上下文」在**既有读面**上可复核 ——
不是只有进程内对象知道。**零新路由、零新 DTO、零 OpenAPI 快照改动。**

## 设计（为什么这样落地）

### 落点 = **制品**，不是新路由

上下文是**按时刻装配**的装配事实。把它写成一件制品（`{task_id}:retrieval_context`）：

- **既有读面直接可用**：`GET /runs/{id}/artifacts` 按 `task:{id}` 约定收 run 作用域制品
  （`_run_artifact_ids`），`GET /artifacts/{id}/content` 已有内容路由 ⇒ **零新路由**；
- **同源可证**（本 cycle 的关键）：写出的字节**就是** `retrieval_digest` 的源
  ⇒ 「读面的值 == 会话拿到的值」不是靠比对两次计算，而是**不可能分叉**；
- **空集合也写**（带理由）：判据要的是「读得出来」，不是「断言非空」——
  「没有内容进去」与「读面缺一条」必须**分得开**。

### 只对**会建会话**的任务写（射程边界）

实验 / 报告格**不建会话** ⇒ 为它们写「进了什么上下文」是**答非所问**。
实现按**契约声明**分流（`experiment` / `report` 非空 ⇒ 跳过），不按合约名硬编码。

### 逐条载荷自足

`{run_id, entries: [{identifier, evidence_id, artifact_id, shown}]}` ——
读面的人不用回查任何东西就能看出「进了什么、从哪来」。

## 实施清单

1. **WP-A**（产品）：`retrieval_context.context_payload` / `payload_bytes` 抽出为**唯一**
   构造点与编码点；`persist_retrieval_context` 写制品；`with_retrieval_context` 顺带落盘
   （仅会话任务）。
2. **WP-B**（判据）：`test_retrieval_context_read_face.py`（5 例）+ e2e 增 2 例
   （HTTP 面 + 同源）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写 / ALL_PLAN 同提交；m0。

## 影响报告

- **产品代码**：`retrieval_context.py` 内新增 `context_payload` / `payload_bytes` /
  `persist_retrieval_context` / `_persist_for_session_task` 与 `_CONTEXT_CREATOR` 常量，
  并把 `with_retrieval_context` 扩成「装配 + 落盘」（仅会话任务）；视图新增 `run_id` 字段
  （缺省 `""` ⇒ 既有调用点逐字节不变）。**零新路由、零新 DTO、零 OpenAPI 快照改动。**
- **读面**：run 的制品清单**多两条**（每个会话 phase 一条上下文制品）—— 已核实不回归
  既有的精确计数判据（它们的 harness 不接该缝）。
- **判据面**：新增 1 个模块（5 例）+ e2e 增 2 例；既有判据**零放宽**。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化、无出网新增。**

## 残余与未覆盖

- EC-04（真实中转站）/ EC-05（自举收口）**不在本 cycle**；
- 模型是否真的读了上下文 —— 属观测面，不在本 GOAL 的射程内。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| 读面判据（新模块） | **5 passed** | `… -m pytest tests/application/test_retrieval_context_read_face.py -q` |
| 接缝判据 | 16 passed（未回归） | `… -m pytest tests/application/test_retrieval_context_seam.py -q` |
| e2e（含 HTTP 面） | **7 passed** | `… -m pytest tests/e2e/test_retrieval_context_reaches_the_session.py -q` |
| 同源实测 | 写盘字节的 digest == `retrieval_digest`；读面制品 digest == 会话 digest | 见判据 + 探查读数 |
| 四向按压 | `V8-1…V8-4` 全 RED + 逐字节复原 | `… -B scratch/goal078c2_press.py` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 3 建档（EC-03 的落点与同源设计）。 |
| 2026-10-15 | DONE | WP-A…WP-C 落地：制品落盘 + 同源判据 + HTTP 面取证；四向按压全红。 |
