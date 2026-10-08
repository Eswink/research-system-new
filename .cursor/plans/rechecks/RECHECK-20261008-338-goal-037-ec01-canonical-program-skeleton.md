---
id: RECHECK-20261008-338
slug: goal-037-ec01-canonical-program-skeleton
title: 独立复检：GOAL-037 cycle 1（EC-01）研究程序的 canonical 骨架
plan_id: PLAN-20261008-337
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-338 — GOAL-037 cycle 1（EC-01）独立复检

复检对象：`PLAN-20261008-337`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 决策定稿（AC-1）

六条设计决策逐条定稿在 PLAN 的「决策定稿」节；**独立复核**两处关键读数：

| 读法 | 读数 |
| --- | --- |
| 词表不变（承接面不为「程序」扩词表） | `examples/config/capabilities.yaml` 仍是 46 条（未改文件） |
| `research_state.read` 在差集表（cycle 3 的承接目标） | `docs/architecture/POLICY_SURFACE_AUDIT.md` 的差集表含该行（未承接） |
| 关联落点是 canonical | `packages/domain/run.py` 字段 + `runs` 行载荷（`run_json`）内 —— 无侧表 / 无日志推断 |

### 2. 关联落 canonical 且向后兼容（AC-2）

| 读法 | 读数 |
| --- | --- |
| 三个重建函数带住程序字段 | `test_transition_keeps_program_fields` / `test_with_manifest_and_protocol_source_keep_program_fields` **passed** |
| 旧载荷反序列化 | `test_program_fields_round_trip_and_legacy_payload_still_decodes` **passed**（无 program 键 ⇒ 两字段 `None`） |
| `for_program` 排序与过滤 | SQLite 与 PG 各一条用例 **passed**（按 `program_index` 升序、跨程序不混） |
| 全量 mypy | `Success: no issues found in 1151 source files` |

### 3. 程序域类型 + 存储 + 迁移（AC-3）

| 读法 | 读数 |
| --- | --- |
| 迁移在 live PG 可跑 | `migrate(dsn)` 后 `migration_version` 最新 = **17**；两表在 `information_schema` 可见 |
| PG 往返 | `tests/postgres/test_program_store_pg.py` **2 passed**（程序往返 / 决策幂等 / run 归属） |
| SQLite 往返 + 决策 append-only | `tests/adapters/sqlite/test_program_store_sqlite.py` **4 passed** |

### 4. 同轮同步（AC-4）

| 读法 | 读数 |
| --- | --- |
| OpenAPI 快照 | 按生成器重生成（`+22` 行，**只增字段**），`tests/contracts/test_openapi_snapshot.py` **8 passed** |
| 前端类型 | `apps/web/src/api/types.ts` 的 `RunDetailDto` 增两字段（与快照一致） |
| 广面套件 | `tests/contracts + tests/api + tests/tooling` **2516 passed, 76 skipped**；`tests/application + tests/architecture` **1063 passed, 1 skipped**；`tests/domain + tests/adapters + tests/contracts` **1590 passed, 5 skipped**（DSN 已设 ⇒ postgres 标记用例实跑，不再整批跳过） |

### 5. 门链与记录面（AC-5）

`ruff check`（全仓改动面）`All checks passed!`；`ruff format --check` 绿；`mypy` 绿；
新增判据文件 `13 passed`；as-is m0 与治理读数见 GOAL 的迭代日志 cycle 1 行。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立。

### Warnings

- **W-1（DSN 影响读数口径，如实登记）**：`tests/domain+adapters+contracts` 的读数在
  「设了 `RESEARCHOS_POSTGRES_DSN`」与「没设」两种环境下不同（后者 postgres 标记整批跳过）
  ⇒ 与历史读数比对必须连同环境一起看（见 `MEM-20261008-207`）。
- **W-2（程序编排尚未落地，属 cycle 2 范围）**：本轮只有**骨架**（域类型 / 存储 / 迁移 /
  接线）；驱动、advance 入口、双 run 实跑与两向反证在 cycle 2。
- **W-3（承继残余原样保持）**：GOAL-036 的 `M-1`…`M-5`、`R26-*` 终态、未覆盖范围
  逐条保持；**不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
- **W-4（关联查询的形状）**：`for_program` 走 JSON 抽取（SQLite `json_extract` / PG
  `->>`），**未**给 `runs` 增列与索引 —— 程序内 run 数为个位数时够用；规模变了要重新评估
  （本轮不改 `runs` DDL 是**减小爆炸半径**的有意选择）。
