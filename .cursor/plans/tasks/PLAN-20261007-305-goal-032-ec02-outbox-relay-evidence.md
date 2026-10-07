---
id: PLAN-20261007-305
slug: goal-032-ec02-outbox-relay-evidence
title: GOAL-032 cycle 2（EC-02）：`R26-5` 取证追认 —— relay 四条判据 + 启用面两向 + 两向反证 + 记录更正（只追加）
status: DONE
created_at: 2026-10-07
updated_at: 2026-10-07
latest_recheck: .cursor/plans/rechecks/RECHECK-20261007-306-goal-032-ec02-outbox-relay-evidence.md
memory_entries:
  - a-stale-registration-needs-a-forensic-judge-not-a-note
parent_goal: GOAL-20261007-032
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 **EC-02**（`R26-5` 取证追认）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**零产品改动**（relay 实现与启用面
    一字未动；本轮只**新增判据**与**追加记录更正**）；**不改 GOAL-026 的正文**
    （历史记录不可变 ⇒ 更正写在**本轮**记录里）；未启用组合根**如实登记**（不暗示已覆盖）；
    **不得**宣称 exactly-once —— 口径只能是 at-least-once + idempotency + deduplication
    （relay 的语义就是「至少一次 + 消费端按 event_id 去重」；**明确否认**恰好一次）。
objective: >-
    把 `R26-5`「应用级事件消费者不存在（GOAL-026 登记）」从**未取证**推进到
    **有判据的结论**：① 实现面（`PgOutboxRelay.run_once` 的 drain/mark/失败语义）；
    ② 启用面实测（生产 PG 组合根启用、SQLite 未启用、门控行为两向）；③ 四条新判据
    （一轮真的投递并 mark / 崩溃语义 ⇒ 重投 / 消费端按 event_id 去重 / 未启用组合根如实
    登记）；④ 两向反证（改坏 mark ⇒ 判红；摘掉去重 ⇒ 判红）；⑤ **只追加**一条事实更正
    （实现早已在树、登记过期）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **实现面 + 启用面核实**：`PgOutboxRelay`（pending → publish → mark 逐条）与
      `OutboxRelayScheduler`（`_execute_pass` = 同一 pass 的 telemetry 包装）的真实行为；
      启用面：PG 组合根 `True`（恰好一处）、SQLite 组合根默认 `False`、门控两向行为。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/architecture/python/test_outbox_relay_enablement_is_explicit.py -q` ⇒ 5 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **四条判据（PG 侧，含读数）**：① 一轮投递并 mark（pending 前后 + 返回值 + sink 逐条）；
      ② 崩溃语义（投递后抛错 ⇒ 未 mark ⇒ 下一轮重投同一条）；③ 消费端去重（重复投递不产生
      第二条事实；数据臂 = `event_id` 主键唯一）；④ 未启用组合根如实登记（门控 `None`）。
    verify: >-
      `RESEARCHOS_POSTGRES_DSN=<test dsn> uv run --frozen --no-sync python -B -m pytest
      tests/postgres/test_outbox_relay_forensics.py -q` ⇒ 4 passed；
      未启用面在 AC-1 的离线判据里。
    status: PASS
  - id: AC-3
    criterion: >-
      **两向反证**：① mark 的 UPDATE 摘掉 ⇒ 「一轮投递并 mark」判红；② 判据消费端去重摘掉
      ⇒ 去重判据判红；两臂复原后 raw `sha256` 回到基线。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal032-cycle2-press.py` ⇒
      `P1_RED 1 failed` / `P2_RED 1 failed, 3 passed` / `FINAL_MATCHES_BASELINE True`；
      留档 `scratch/goal032-cycle2/press-matrix.log`（二进制写盘、CR=0）。
    status: PASS
  - id: AC-4
    criterion: >-
      **记录更正（只追加）**：本轮记录里写明「GOAL-026 的 `R26-5` 登记已被实测推翻 ——
      relay 实现自 `ed2fa0e` 起在树且生产启用」；**不改** GOAL-026 正文；残余（按偏移量
      物化业务事实的消费者仍不存在）如实登记。
    verify: >-
      本文件与 `RECHECK-20261007-306` 的「事实更正」节；`git diff` 对
      `GOAL-20260929-026-*` **零改动**（`git status` 读数）。
    status: PASS
  - id: AC-5
    criterion: >-
      **门与留档**：受影响套件全绿；四道门（`ruff check` / `ruff format --check` / `mypy` /
      规模门）绿；PG 判据在 DSN 不可达时**如实 skip**（不是 PASS 的替代）。**零产品改动**
      （`git diff --numstat` 对 `adapters/` `services/` `packages/` 为空）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/postgres tests/architecture -q`
      （带 DSN）⇒ 全绿；`git diff --numstat` 无产品文件的读数。
    status: PASS
---

# PLAN-20261007-305 — GOAL-032 cycle 2（EC-02）：`R26-5` 取证追认

## 事实更正（**只追加**；GOAL-026 的正文是历史记录，不改）

GOAL-20260929-026 的 `R26-5` 登记：**「应用级事件消费者不存在（仓内无『按事件物化业务事实』
的消费者；`consumer_offsets` 是文档独有）⇒ 新建消费者 = 新能力 + 触碰 Canonical State
写入面」**。2026-10-07 的实测（GOAL-20261007-032 建档勘察 + 本 cycle）：

- **登记被推翻的一半**：`PgOutboxRelay`（`adapters/postgres/outbox_relay.py`）**自 `ed2fa0e`
  （M14）起就在树**，`OutboxRelayScheduler` 在 `services/api/scheduler.py`，
  且**生产 PG 组合根默认启用**（`services/api/pg_composition.py` 设
  `deps.outbox_relay_enabled = True`）。它不是"待新建的能力"——它是**已交付且生产启用**的
  组件，只是**从未有过专门判据**（`PgOutboxRelay` 全仓零测试引用，实测）。
- **仍然成立的一半**：**按偏移量物化业务事实**的应用级消费者（`consumer_offsets` 那一类）
  **确实不存在**（全仓只命中 `docs/storage/DATABASE_SCHEMA.md`）。relay 是**投递**面，
  不是"以业务事实为目的的消费者"。
- ⇒ 更正口径：**`R26-5` 的"实现不存在"部分过期**（本轮补判据追认）；**"消费偏移量表
  不存在"部分仍成立**（如实登记为本轮之外的残余）。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-5）。

## 实施清单

| # | 项 | 交付 |
| --- | --- | --- |
| WP-1 | relay 判据（PG） | `tests/postgres/test_outbox_relay_forensics.py`（4 例：一轮/崩溃/去重/守护线程同一 pass） |
| WP-2 | 启用面判据（离线） | `tests/architecture/python/test_outbox_relay_enablement_is_explicit.py`（5 例，含门控两向） |
| WP-3 | 反证 | `scratch/goal032-cycle2-press.py`（mark 摘掉 / 去重摘掉）+ 留档 |
| WP-4 | 记录更正 | 本文件的「事实更正」节 + RECHECK 同步 |

## 证据

- **判据读数**：`tests/postgres/test_outbox_relay_forensics.py` ⇒ **4 passed**（DSN 指向本机
  `localhost:15432`）；`tests/architecture/python/test_outbox_relay_enablement_is_explicit.py`
  ⇒ **5 passed**。
- **反证留档**：`scratch/goal032-cycle2/press-matrix.log`（268 B、CR=0）：
  `P1_RED 1 failed` / `P1_RESTORED True` / `P2_RED 1 failed, 3 passed` / `P2_RESTORED True` /
  `FINAL_MATCHES_BASELINE True`。
- **门**：`ruff check` = `All checks passed!`；`ruff format --check` = 干净；
  `mypy` = `Success: no issues found in 2 source files`。
- **零产品改动**：`git diff --numstat` 对 `adapters/` `services/` `packages/` 无条目。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-07 | IN_PROGRESS | cycle 2 开工：先复核实现面（`rg` 已证 `PgOutboxRelay` 零测试引用）。 |
| 2026-10-07 | DONE | 五条 AC 全 PASS（`RECHECK-20261007-306` = PASS_WITH_WARNINGS）。 |

## 影响报告

- **Domain/API/schema**：零改动（新增判据文件 + 记录）。
- **安全/凭据**：零影响（PG 判据用测试 DSN；无真实凭据）。
- **兼容性/迁移**：零影响。
- **上游版本**：零影响。
- **下一项任务**：cycle 3 = EC-03（研究连续性 / `run_resume` 覆盖度）。
