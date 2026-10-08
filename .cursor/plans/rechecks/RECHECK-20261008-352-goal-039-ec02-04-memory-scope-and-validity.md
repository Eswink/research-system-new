---
id: RECHECK-20261008-352
slug: goal-039-ec02-04-memory-scope-and-validity
title: 独立复检：GOAL-039 cycle 1（EC-02/03/04）scope 落库 + 声明式时效 + 到期可观测
plan_id: PLAN-20261008-351
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-352 — GOAL-039 cycle 1 独立复检

复检对象：`PLAN-20261008-351`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. `scope` 落库且往返一致（AC-1）

| 读法 | 读数 |
| --- | --- |
| 域 | `MemoryRecord.scope` 缺省 `"project"`；空串 ⇒ `ValueError`（判据 `test_an_empty_scope_is_refused_by_the_domain`） |
| 迁移 | `adapters/postgres/migrations/018_memory_scope_and_validity.sql` 在树（`ADD COLUMN IF NOT EXISTS ... DEFAULT 'project'`） |
| 三实现同契约 | ① SQLite：`test_scope_round_trips_through_the_store` **passed**；② **PG（真库）**：`tests/postgres/test_memory_scope_pg.py` **2 passed**（`scope` + 两时点往返）；③ Fake：`test_the_list_face_discloses_the_scope` 覆盖 |
| 迁移落地（live PG 实测） | `migration_version` 最新 = **18**；`information_schema` 里 `m12_memory` 列清单**实见 `scope`**（此前两库皆无） |
| 读面披露 | 列表读面逐条给 `scope`（API 判据断言 `rows[0]["scope"] == "project"`） |

### 2. 声明式时效（AC-2）

| 读法 | 读数 |
| --- | --- |
| 声明 ⇒ 真实值 | `test_declared_validity_is_persisted_as_real_values` **passed**（两时点逐字回读） |
| 未声明 ⇒ `None` | `test_undeclared_validity_stays_none` **passed**（既有行为逐字不变） |
| PG 不再硬编码 | 源码复核：`_proposal_values` 写 `proposal.review_after` / `proposal.expires_at`（此前三行硬编码 `None`） |

### 3. 到期可观测（AC-3）

| 读法 | 读数 |
| --- | --- |
| 三态 | `test_expired_and_review_due_and_none_are_all_distinguishable` **passed** |
| 边界 | `expires_at == now` ⇒ `EXPIRED`（`test_the_boundary_is_inclusive_on_expiry`） |
| 反证①未到期不报 | `test_a_not_yet_due_record_is_not_reported` **passed** |
| 反证②到期必报 | API 面：`?at=2028` ⇒ `EXPIRED`（判据断言） |
| 反证③未声明不误报 | `test_an_undeclared_validity_is_never_reported_as_expired` + API 面同断言 |
| 可复现 | `test_the_same_instant_yields_the_same_verdict`（同瞬 ⇒ 同判）；源码复核 `validity.py` **无挂钟调用** |
| 路由形态 | **GET**（读面族；写面枚举实测回到 **63**，未新增写面端点） |

### 4. 门链与记录面（AC-4）

`ruff` / `format` / `mypy`（1167 files）全绿；广面（api + adapters + domain + application +
contracts + loaders + tooling + observability + postgres）**4503 passed, 82 skipped**；
新读面登记 + OpenAPI 快照同轮同步。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立。

### Warnings

- **W-1（四处真红并修，如实登记）**：① SQLite 的 `INSERT` 硬编码 12 个 `?`（加列后 13 列）
  ⇒ 改为**按列数生成**；② 新路由首版写成 POST ⇒ 写面告警线 63 → 64，复核后判它是**读面**
  ⇒ 改 **GET**（写面回到 63）；③ 读面登记首版放错「声明内容」档 ⇒ 撞声明面上界（16 > 15）
  ⇒ 更正值**零命中档**（它不含记忆正文）；④ API 判定用例 53 行超规模上限 ⇒ **抽 helper**（`_commit_expiring`）。
- **W-2（旧库加列的射程）**：迁移用 `ADD COLUMN IF NOT EXISTS` ⇒ 既有 PG 库会被加列；
  **SQLite 开发库**若在建表**之后**才升级（无 ALTER 路径），旧表不会自动加列 —— 判据
  `test_legacy_rows_without_a_scope_column_read_the_default` 对这个形态**两种结果都接受**
  （读出缺省 / 抛 `OperationalError`），**故它对该形态不是强断言**；该边界已写进判据注释
  （开发库删除重建的既有做法见 `MEM: sqlite-dev-db-stale-schema`）。
- **W-3（本轮只到「事实可读」）**：到期/待复核现在是**可观测事实**；**自动处置**（删 / 降权 /
  重建索引）不在本轮（AGENTS.md §8 的另外两条由既有 `deactivate` / `delete` 承担）。
- **W-4（承继残余原样保持）**：GOAL-038 的 `P-1`…`P-3`、GOAL-037 的 `O-1`…`O-5`、`R26-*`
  终态、未覆盖范围逐条保持；**不得**据此宣称项目安全；**不得**宣称投递语义为那四个字
  （**明确否认**）。
