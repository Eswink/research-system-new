---
id: PLAN-20261010-383
slug: goal-046-ec01-04-program-human-gate
title: GOAL-20261010-046 cycle 1（EC-01…EC-04）：程序级人工闸门可声明 / 可判定 / 可点名
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-384-goal-046-ec01-04-program-human-gate.md
memory_entries:
  - extraction-must-not-re-point-existing-criteria
parent_goal: GOAL-20261010-046
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-046 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不声明 ⇒ 逐字不变**；**不**新建第二套
    审批存储或第二套闸门机制（复用既有 `ApprovalStore` / `human_gates` / `phase_pause`）；
    **不**改 phase 面闸门语义（逐字保持）；**不**自动批准 / 自动放行 / 自动超时；
    **改既有判据必须走自证清单**（`MEM-20261009-210`）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让程序**自己声明**「到第 N 轮停下等人看结果」：① 域 +1 **可选**声明 `human_gate_at_index`
    （缺省 `None` = 不设闸门 ⇒ 既有行为逐字不变；越界 / 零 / 负数 ⇒ **点名**）；② **两库同契约**
    落库（SQLite schema + 迁移 **020** 只加列；PG `INSERT` 与 `_PROGRAM_SELECT` 带列）；
    ③ 建程序 DTO / 路由 / 读面透传；④ **判定与推进**：第 N 轮**跑完之后**的推进被拦住 ——
    判定**复用**序 12 的 `WAIT_FOR_APPROVAL`（同一件事：等人拍板），判词**点名**声明值与待审批；
    语义**照抄** phase 面的 `pending_human_gates`（声明的闸门 **−** 已裁决审批）；
    ⑤ **三向反证**（G-1 闸门被绕过 / G-2 轮前误拦 / G-3 已裁决仍拦）。
    **不**新建第二套审批/闸门机制；**不**自动放行；缺省逐字不变。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（读数逐条）**：`ResearchProgram` 字段表**无**闸门位（逐字列出）/ 程序面
      三文件对 `human_gated|human_gate` **零命中** / 序 12 只做「认得状态」 / phase 面
      `pending_human_gates` 的语义与 `pause_for_human_gate` 的三步副作用**可复用** /
      两库程序表**无**可承载列（⇒ 需迁移 020）。
    verify: >-
      `dataclasses.fields(ResearchProgram)`；`rg -c "human_gated|human_gate"` 三个程序面文件
      ⇒ 全 0；`rg -n "def pending_human_gates" -A12`；`rg -n "human" adapters/*/program_store.py`。
    status: PASS
  - id: AC-2
    criterion: >-
      **声明与落库（两库同契约）**：域声明**可选**（缺省 `None` ⇒ 逐字不变；越界**点名**）；
      SQLite schema + **迁移 020**（只加列，无缺省回填）与 PG `INSERT` / `_PROGRAM_SELECT`
      都带列；往返一致（声明值读回声明值、缺省读回 `None`）；建程序 DTO / 路由可传该声明。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters/sqlite
      tests/postgres tests/api -q` ⇒ 全绿 + 新用例（详见 PLAN-20261010-387 的补测）。
    status: PASS
  - id: AC-3
    criterion: >-
      **判定与推进（点名）**：`declared_gate_pending` / `declared_gate_verdict` 的语义
      **照抄** phase 面（声明闸门 − 已裁决）；判定面**只读**审批面（`list_for_run`，
      无写方法）；缺审批面 / 查询失败 / 查不到 ⇒ 三种形态**各自点名**（不静默放行）；
      **闸门求值先于结论面**（AST 按被调名取行号判）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration -q` ⇒ 全绿 + 新用例 7 例。
    status: PASS
  - id: AC-4
    criterion: >-
      **真的被用上（+ 三条反证）**：声明闸门 ⇒ 该轮跑完后的推进落 `WAIT_FOR_APPROVAL`
      且**点名**声明值；**轮前不停**（反证①）；**未声明 ⇒ 逐字走结论面**（反证②）；
      **已裁决 ⇒ 不再拦**（与 phase 面同语义）；推进**不写**审批面（反证③）。
    verify: >-
      `scratch/goal046-press.txt` 三行全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-046-press-two-way.txt`（295 B / `CR=0`）。
    status: PASS
---

# PLAN-20261010-383 — GOAL-20261010-046 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-046`（MAINLINE 程序表**序 14**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（四条读数：域无闸门位 / 三文件零命中 / phase 面可复用 / 两库无列） | PASS |
| AC-2 | 声明与落库（域可选 + 迁移 020 只加列 + 两库同契约 + DTO/路由透传） | PASS |
| AC-3 | 判定与推进（语义照抄 + 三种缺面形态点名 + 只读 + 闸门先于结论面） | PASS |
| AC-4 | 三向反证（G-1/G-2/G-3 全红 + 二进制复原 raw `sha256` 一致） | PASS |

## 实施清单

- [x] WP-1 域：`human_gate_at_index: int | None = None` + `1..max_runs` 校验（越界**点名**）
- [x] WP-2 SQLite：schema 列 + `_encode_program` / `_decode_program` + 两处 SELECT
- [x] WP-3 PG：`_PROGRAM_SELECT` + `INSERT` 列与占位符 + `_decode_program` + **迁移 020**
- [x] WP-4 建程序面：`ProgramCreateDto` / `ProgramDetailDto` + 路由写入与读面透传
- [x] WP-5 判定面：`program_waiting.declared_gate_pending` / `declared_gate_verdict`
- [x] WP-6 接线：`program_runner` 在**结论面之前**分派闸门（`_gate_evaluation`）
- [x] WP-7 规模门逼出的搬迁：失败重试面 → `program_retry.py`（行为等价）
- [x] WP-8 三向反证 G-1/G-2/G-3 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 判定面新用例 | `test_program_waiting_on_the_run_path.py` **14 passed**（序 12 的 7 + 本轮 7） |
| 三向反证 | `G-1` 闸门被绕过 / `G-2` 轮前误拦 / `G-3` 已裁决仍拦 **全 `RED`**；二进制复原 raw `sha256` 一致 |
| 归档 | `.cursor/plans/goals/evidence/GOAL-20261010-046-press-two-way.txt`（295 B / `CR=0`） |
| 四道门 | `ruff check` / `ruff format --check` / `mypy` strict / 规模门（`program_runner.py` **430 行**、函数全 ≤ 50）全绿 |
| 广面 | `tests/{application,adapters,domain,api,tooling}` **3894 passed, 8 skipped** |
| **迁移** | **020 只加列**（`ADD COLUMN IF NOT EXISTS`，无缺省回填 —— `NULL` 就是缺省语义） |

### 规模门逼出的搬迁撞红既有判据（本轮实测，如实登记）

为守 `program_runner.py` 的 **450 行硬上限**，把失败重试面的计数口径
（`_RETRY_CLAIM_KINDS` / `_retry_face_state`）搬到新模块 `program_retry.py`（行为等价）。
**当场撞红 `goal041` 的两条断言** —— 它们按**文本位置**（在 `runner` 文件里）钉实现。
**被 GOAL-043 立的「零判负」判据当场捕获**
（`test_every_named_assertion_set_reports_no_negative_on_this_tree`）。
**处置**：把这两条改成**判关系不判位置**（`_retry_face_text` 同时看执行面与拆出去的判定面；
断言要求的仍是「两类认领都在计数面里」与「未落库的认领也计入」这两件**事**）。
沉淀 `MEM-20261010-215`。**如实登记为**「搬迁的既有代价」（不是产品缺陷）。

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | **追加** 1 例（既有 9 例**一字未动**） | — | `+28 / -0` | **0** |
| `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | **追加** 7 例（序 12 的 7 例**一字未动**） | — | `+122 / -0` | **0** |
| `tests/adapters/sqlite/test_program_store_sqlite.py` | **追加** 1 例（既有 4 例一字未动） | — | `+15 / -0` | **0** |
| `tests/postgres/test_program_store_pg.py` | **追加** 1 例（既有 2 例一字未动） | — | `+34 / -0` | **0** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | **追加** 2 例（既有 7 例一字未动） | — | `+49 / -0` | **0** |
| `tests/e2e/program_advance_support.py` | `create_program` **+1 可选形参**（缺省**不发键** ⇒ 未声明臂的请求体逐字不变） | 缺省路径的行为**等同**（载荷字典缺省与旧字面量逐键相同） | `+13 / -7` | 那 7 行是**同一字面量改写成 `payload` 变量**（谓语/键值一字未改） |
| `tools/goal041_closeout_assertions.py` | 两条按**位置**写死的断言 ⇒ **判关系不判位置** | **等价**（同一关系：两类认领都在计数面里 / 未落库的认领也计入） | `+44 / -4` | 删的**仅**那 4 行按位置写死的表达式 |

**注**：上表里「追加」的五个测试文件的**补测时点在后续 cycle**（修复轮
`PLAN-20261010-387`）—— 本 cycle 落地时 EC-02/EC-04 声明的**行为面用例**
（两库往返 / 缺省 / 越界点名 / HTTP 面实跑）**只有实现与文本在场、没有用例**；
该缺口由修复轮补齐并在此表事后补记（**不是**把没做的事写成做过）。

## 影响报告

- **Domain / API / schema 变化**：域 **+1 可选字段**；**新增迁移 020**（只加列）；
  OpenAPI 快照与 web 类型需同轮同步（**同步面由修复轮补齐 —— 见下**）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：**低** —— 缺省 `None` 路径逐字不变；
  迁移只加列且 `NULL` 即缺省语义。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）+ 修复轮（快照同步 + 用例补齐）。

## 本 cycle 的**未完成面**（如实登记；由修复轮 `PLAN-20261010-387` 收口）

1. **OpenAPI 快照未同轮重生成并提交** ⇒ CI 的 `quality-*` 在 `de9d396` 上判红
   （`tests/contracts/test_openapi_snapshot.py::test_openapi_snapshot_is_current`）；
2. **EC-02/EC-04 声明的行为面用例**（两库往返 / 缺省 / 越界点名 / HTTP 面实跑）当时未写。
   两条都在修复轮登记、补齐并复跑全门。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 域 + 两库 + 迁移 020 + 判定接线落地；三向按压全红。 |
| 2026-10-10 | DONE | `RECHECK-20261010-384` 独立复检；**两处未完成面**（快照同步 / 用例补齐）如实登记，交修复轮。 |
