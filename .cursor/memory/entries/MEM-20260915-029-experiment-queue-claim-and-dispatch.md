---
id: MEM-20260915-029
title: 实验队列认领语义与派发复用装配链（G14）：原子条件更新 + at-least-once 恢复
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.90
review_after: 2026-12-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-052-experiment-queue-and-scheduling.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-052-experiment-queue-and-scheduling.md
supersedes: []
tags:
  - queue
  - dispatcher
  - at-least-once
  - console
  - control-plane
---

## 做了什么

G14 实验队列：`ExperimentQueueEntry`（QUEUED → DISPATCHING → DISPATCHED | FAILED；
QUEUED → CANCELLED；DISPATCHING → QUEUED 仅认领过期）+ 三实现存储 + 控制面派发器
+ 五端点 + console live。

## 为什么这样做

- **队列必须有消费者**：条目状态由真实派发推进（复用 `POST /runs` 同一条装配链），
  否则就是第二个"注册了没人跑"的空壳（M14/PLAN-045 起反复出现的诚实性红线）。
- **不建第二份协议副本**：入队冻结的是**来源**（`protocol_path` 或草稿修订），
  派发时按来源重新解析，与 HTTP 面同链。
- **认领必须原子**：状态列 + 条件更新（`WHERE state = 'QUEUED'`）是唯一仲裁点；
  PG 用 `FOR UPDATE SKIP LOCKED` 取候选，SQLite 用单事务读 + 条件写。并发派发者
  只有一个 rowcount=1，其余返回 None（不是异常）。
- **认领过期要能恢复**：进程崩溃/停机中断留下的 DISPATCHING 超过 TTL 归位 QUEUED
  再参与本轮认领 ⇒ **at-least-once**（同一排期可能启动两次，条目上 `run_id` 是最近
  一次结果）。不假装 exactly-once，文档/响应/复检都写明。

## 怎么做与复现

- 存储契约：`tests/adapters/sqlite/test_experiment_queue_sqlite.py`（含白盒反证
  `test_stale_write_loses_to_conditional_update`：旧快照写入 `from_state=QUEUED`
  必须 rowcount 0）、`tests/postgres/test_experiment_queue_pg.py`。
- 派发：`tests/api/test_experiment_queue_api.py`——`run_once()` 后断言 run 行真的
  落在 `GET /projects/{id}/runs`；归档竞态 → `FAILED + ARCHIVED`；未到期 → 不派发。
- console：`apps/web/tests/e2e/{experiment-queue.spec.ts,live-experiment-queue.spec.ts}`。
- 复现命令见 RECHECK-20260915-052 的「复现」小节。

## 适用边界

- 派发在控制面进程内**同步串行**执行 run（与 HTTP 面 run 同步执行同一事实），
  多实例靠原子认领防重复但不提升吞吐；停机不打断在途 run（留给 TTL 恢复）。
- 失败是终态，不静默重试；重新排队是显式运维动作。
- 队列状态变化不发 outbox 事件（与 PLAN-046/048 同口径），观测靠轮询 + 派发 span/metric。
- `ExperimentPlan` 域无 `project_id`，`GET /experiment-plans` 因此是全局列表；
  项目归属由队列条目的 `project_id` 承载（派发按它解析项目设置）。

## 来源

- PLAN-20260915-052（cycle 12）+ RECHECK-20260915-052（PASS_WITH_WARNINGS，W-1..W-6）；
  会话记录：GOAL-20260912-001 状态历史 2026-09-15 cycle 12。
