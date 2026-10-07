---
id: MEM-20261007-192
title: "过期的「未实现」登记要用判据追认，而不是改历史记录：先量「哪一半过期」（`PgOutboxRelay` 零测试引用 vs `consumer_offsets` 仍缺席）"
status: ACTIVE
created_at: 2026-10-07
updated_at: 2026-10-07
scope: repository
confidence: 0.9
review_after: 2027-04-07
source_plans:
  - .cursor/plans/tasks/PLAN-20261007-305-goal-032-ec02-outbox-relay-evidence.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261007-306-goal-032-ec02-outbox-relay-evidence.md
supersedes: []
tags: [stale-registration, forensic-judge, outbox-relay, pg-gated-judge, goal-032, plan-305]
---

## 做了什么

GOAL-026 的 `R26-5` 登记「应用级事件消费者不存在 ⇒ 新建消费者 = 新能力」。GOAL-032
cycle 2 实测把它拆成两半：

- **过期的一半**：`PgOutboxRelay`（`adapters/postgres/outbox_relay.py`）**自 M14 就在树**，
  且生产 PG 组合根默认启用（`services/api/pg_composition.py` 设 `True`）——
  用一句 `rg -l "PgOutboxRelay" tests/` 得到 **零命中**（全仓只有实现、调度器与一个
  一次性探针引用它）就能量出「它没有任何自动判据」。
- **仍成立的一半**：`consumer_offsets` 类（按偏移量物化业务事实）**确实只存在于文档**
  （`rg -n "consumer_offsets" .` 全仓唯一命中 `docs/storage/DATABASE_SCHEMA.md`）。

处置：**不改历史 GOAL 正文**（它是不可变记录），在本轮记录里**只追加**一条事实更正，
并把要追认的那一半**落成判据**（4 条 PG 判据 + 5 条离线启用面判据）。

## 为什么这样做

- 「登记过期」不是笔误，是**没有东西在看着**：一个组件可以交付、生产启用、然后静静躺在
  树的角落里，而登记仍说它不存在。判据是唯一会自己失效的东西 —— 散文不会。
- **不要整段推翻**：多数过期登记其实是**一半过期**（实现有了，但你关心的那一轴未必）。
  `R26-5` 的「消费者」一词同时指 **投递器**（有了）与 **按偏移量物化的消费者**（没有）——
  整段勾掉会丢掉真实缺口。
- **量"零测试引用"是一个便宜的过期信号**：`rg -l "<符号名>" tests/` 空 ⇒ 该组件没有
  任何自动判据（不等于有缺陷，但等于"登记没人看着"）。

## 怎么做与复现

- **先量两面**：`rg -l "<Symbol>" tests/`（有没有判据）与 `rg -n "<config flag>" services/`
  （启用面真值在哪）。GOAL-032 的读数：`PgOutboxRelay` 在 `tests/` **0 命中**；
  `outbox_relay_enabled = True` **恰好一处**（`pg_composition.py`）。
- **判据分两层**：PG 行为（真投递 / 崩溃重投 / 去重）标 `postgres`；**启用面**离线判据
  （AST 读启用点 + 门控**两向**行为）。门控只判"假 ⇒ None"会漏掉「恒 None 的假实现」——
  必须补「真 ⇒ 穿过」臂。
- **崩溃语义用注入式**（本进程内投递后抛错）时说清楚它**不是**真实 kill；
  真实进程崩溃的取证面若在一次性探针里，就把它点名登记为**未被自动跑**（`W-1`）。
- 复现：
  `RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os
  uv run --frozen --no-sync python -B -m pytest tests/postgres/test_outbox_relay_forensics.py -q`
  ⇒ 4 passed；
  `uv run --frozen --no-sync python -B -m pytest
  tests/architecture/python/test_outbox_relay_enablement_is_explicit.py -q` ⇒ 5 passed；
  反证 `uv run --frozen --no-sync python -B scratch/goal032-cycle2-press.py`。

## 适用边界

- 本仓的 **outbox / relay / 调度守护线程**面适用；**其它**组件的"登记过期"要各自量。
- 「注入式崩溃」不等于「真实进程崩溃」；`probe_outbox.py` 是**未被 m0 自动跑**的
  M14 一次性探针（且其场景 D 有一条 `>= 0` 的恒真断言 —— `W-2`），引用它时必须注明。
- 投递语义的**唯一**允许口径仍是 at-least-once + idempotency + deduplication
  （relay 的注释与判据都按它写；**不得**据此宣称恰好一次）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261007-305-goal-032-ec02-outbox-relay-evidence.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261007-306-goal-032-ec02-outbox-relay-evidence.md`
- 判据：`tests/postgres/test_outbox_relay_forensics.py` /
  `tests/architecture/python/test_outbox_relay_enablement_is_explicit.py`
- 事实：`rg -n "outbox_relay_enabled|OutboxRelayScheduler|PgOutboxRelay" services/ adapters/`；
  `rg -l "PgOutboxRelay" tests/`（零命中）；`rg -n "consumer_offsets" .`（文档独有）
