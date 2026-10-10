---
id: PLAN-20261010-393
slug: goal-048-ec01-04-a-declared-gate-can-be-a-condition
title: GOAL-20261010-048 cycle 1（EC-01…EC-04）：条件式程序闸门 —— 声明面 + 求值接线 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261010-048
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-048 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**边界**：**不新建第二套**闸门机制（复用序 14 的判定面与序 15 的
    注册面）；**不改** phase 面 `HUMAN_GATE` 语义；**不**做自然语言条件 / 表达式引擎 / 新依赖；
    **不**自动放行 / 超时；改 DTO ⇒ **同轮**同步 OpenAPI 快照；**有副作用的实现不得放进
    只读判定面**（承 `MEM-20261010-216`）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让程序**自己声明一个条件式闸门**：① 勘察定稿（读数见 GOAL 正文六条）；② **声明面** ——
    `human_gate_on_verdicts: tuple[str, ...] | None`（**与 `verdict_in` 同族**的可机检取值集合；
    缺省 `None` ⇒ 逐字不变；空集合 / 空串 / **与序号声明并存** 三种坏声明各自**点名**）；
    两库同契约落库（迁移 **021** 只加列；`NULL` ≠ `[]`）；建程序 DTO / 路由透传；
    ③ **求值与推进** —— `declared_gate_trigger` 按落库**判词取值**判定；命中 ⇒ 走上条已成立的
    闸门语义（注册 + 等人 + 可裁决 / 可接回）且**点名条件与命中依据**；不命中 ⇒ 逐字走结论面；
    ④ **两向反证** J-1…J-4。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（读数逐条）**：声明位类型逐字 / 越界已点名 / **循环面** `stop_when` 已在且
      **未知判据点名** / **程序面零命中** / 结论面取值分派手法现成 / 闸门等待起点已落库。
    verify: >-
      GOAL 正文「事实层结论」的六条读数（`rg` 命令 + 实跑读回）。
    status: PASS
  - id: AC-2
    criterion: >-
      **声明面（可机检 + 缺省逐字不变 + 坏声明点名 + 两库同契约）**：域 +1 **可选**声明
      `human_gate_on_verdicts`（与 `verdict_in` 同族）；三种坏声明各自**点名**；与序号声明
      **互斥**（域层拒绝）；SQLite 列 + **迁移 021**（只加列）+ PG 列与 `INSERT` / `_PROGRAM_SELECT`；
      DTO / 路由透传；往返一致（声明读回声明、缺省读回 `None`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters/sqlite
      tests/postgres tests/api -q` ⇒ 全绿 + 新用例。
    status: PASS
  - id: AC-3
    criterion: >-
      **求值与推进（点名）**：`declared_gate_trigger` 按**落库判词取值**判定（只读；
      与结论面读**同一批**事实 ⇒ 两处不可能看到不同结论）；命中 ⇒ 触发（注册 + 等人 +
      点名声明条件与命中依据）；不命中 ⇒ **逐字**走结论面；推演**先于**结论面（AST 按被调名判行号）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration tests/e2e -q` ⇒ 全绿 + 新用例（命中 / 不命中 /
      点名依据 / 条件也注册 / 未声明零调用）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（真按压）**：`J-1` 条件成立仍放行 / `J-2` 条件不成立也拦 /
      `J-3` 非法条件被静默当成「无条件」 / `J-4` 未声明条件也产生副作用 —— 四条**全部判红**；
      复原用**二进制读写**且 raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `scratch/goal048-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-048-press-two-way.txt`。
    status: PASS
---

# PLAN-20261010-393 — GOAL-20261010-048 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-048`（MAINLINE 程序表**序 16**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（六条读数） | PASS |
| AC-2 | 声明面（域可选 + 两库同契约 + 迁移 021 + DTO/路由） | PASS |
| AC-3 | 求值与推进（按落库事实触发 + 点名条件与依据） | PASS |
| AC-4 | 两向反证 J-1…J-4 全红 + 二进制复原一致 | PASS |

## 实施清单

- [x] WP-1 域：`human_gate_on_verdicts` + 三种坏声明点名 + 与序号**互斥**（抽 `_validate_gate_declarations`）
- [x] WP-2 SQLite：列 + `_encode_gate_conditions` / `_decode_gate_conditions` + INSERT / 两处 SELECT
- [x] WP-3 PG：`_PROGRAM_SELECT` + `INSERT` + `_decode_program` + **迁移 021**
- [x] WP-4 建程序面：DTO +2 处 + 路由写入与读面透传 + **OpenAPI 快照同轮重生成**
- [x] WP-5 判定面：`declared_gate_trigger`（只读）+ `declared_gate_pending` / `declared_gate_verdict` 接上
- [x] WP-6 注册面：`register_declared_gate` 改由**同一** trigger 判触发（单一来源）
- [x] WP-7 接线：`program_runner` 落库判词读**一次**，结论面与条件闸门**共用**
- [x] WP-8 判据 +7 例（域 1 / 判定面 5 / e2e 2）+ 两向反证 J-1…J-4 + 归档

## 证据

| 门 | 读数 |
| --- | --- |
| 域判据 | `tests/domain/test_research_program.py` **11 passed**（原 10 + 1）|
| 判定面判据 | `test_program_waiting_on_the_run_path.py` **20 passed**（原 20，条件面**单列**）+ `test_program_conditional_gate_on_the_run_path.py` **5 passed**（本轮新增；规模门 450 行逼出的拆分）|
| e2e 判据 | `test_program_advance_on_the_run_path.py` **13 passed**（原 11 + 2，**成对**：命中 / 不命中）|
| 规模门逼出的拆分 | 判定面测试文件曾到 **487 行** ⇒ 条件面单列成新文件（**行为等价**，用例一字未改）；`program_gate_registration.register_declared_gate` 曾 **51 行** ⇒ 抽 `_open_write_face` |
| 两向反证 | `J-1`…`J-4` **全 `RED`**（11/2/1/3 例）+ 二进制复原 raw `sha256` 一致；归档 **455 B / `CR=0`** |
| 四道门 | `ruff check` / `ruff format --check`（1191 files）/ `mypy` strict（**1181** files）/ 规模门（三处逼出改动：域 `__post_init__` 触**复杂度门** ⇒ 抽 `_validate_gate_declarations`；注册面 51 行 ⇒ 抽 `_open_write_face`；判定面测试 487 行 ⇒ 条件面**单列**）全绿 |
| **下游同步** | **OpenAPI 快照同轮重生成**（`+28 / -0`）+ 判据 **8 passed**（承 `MEM-20261010-216`）|
| 迁移 | **021 只加列**（`NULL` = 未声明，**与 `[]` 语义不同**）|

## 决策登记（本 cycle 落定）

| # | 决策 | 结论与依据 |
| --- | --- | --- |
| ① | 条件形态 | **取「落库判词取值集合」**（`human_gate_on_verdicts`）—— 与结论面 `verdict_in` **同族**（那里命中 ⇒ 续，这里命中 ⇒ 停）⇒ **可机检、可点名、不引入表达式引擎**（与建题时的候选一致）|
| ② | 与既有单序号声明的关系 | **取互斥**（域层 `ValueError` 点名拒绝）—— 两条声明各有求值时序（按轮次 / 按落库事实），**并存会让「为什么停」读不出是哪一条要求的**；互斥少一套交互语义 |
| ③ | 是否新增判定种类 | **不新增** —— **复用**序 12/14 的 `WAIT_FOR_APPROVAL`（同一件事：等人拍板），**来源由判词与被引事实点名**（`human_gate_on_verdicts=...` + `verdict <命中值>`）|
| ④ | 迁移 | **要新迁移（021）**：020 只有按序号的列；`ADD COLUMN IF NOT EXISTS ... JSONB`（只加列，无回填）|

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | **追加** 1 例（既有 10 例一字未动） | — | 见 RECHECK | **0** |
| `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | **追加** 5 例（既有 20 例一字未动） | — | 见 RECHECK | **0** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | **追加** 2 例（既有 11 例一字未动） | — | 见 RECHECK | **0** |
| `tests/e2e/program_advance_support.py` | `create_program` **+1 可选形参**（缺省**不发键**） | 缺省路径请求体与旧形态**逐键相同** | 见 RECHECK | 见 RECHECK |
| `packages/application/run_orchestration/program_waiting.py` | `declared_gate_pending` / `declared_gate_verdict` 接条件 | 「序号声明的判词逐字保持」（**同一条点名句仍在**） | 见 RECHECK | 见 RECHECK |
| `packages/domain/program.py` | `__post_init__` 抽 `_validate_gate_declarations` | **等价**（同一批校验，只是搬出函数） | 见 RECHECK | 见 RECHECK |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 影响报告

- **Domain / API / schema 变化**：域 **+1 可选字段**；**新增迁移 021**（只加列）；
  DTO **+1 可选字段**（⇒ OpenAPI 快照同轮重生成，已做）。
- **安全 / 凭据变化**：无（复用既有判定面与注册面；准入分支未动）。
- **兼容性 / 迁移风险**：**低** —— 缺省 `None` 路径逐字不变；迁移只加列且 `NULL` 即未声明。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本 cycle 的机械面（**条件声明与序号声明互斥**、**触发判定单一来源**、**落库判词只读一次供
两处共用**）属「声明式判据」这一族在本仓的**第三次**落地（循环面 `stop_when` → 结论面
`verdict_in` → 闸门面 `human_gate_on_verdicts`）；**未**沉淀新条目 —— 该族的一般形态已由
`MEM-20261010-216` 的同族纪律覆盖，且本轮的**真缺陷类**（坏的声明必须点名）已由序 14 的
`MEM` 承载。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 域 + 两库 + 迁移 021 + 求值接线落地；判据 +7 例；四向按压全红。 |
| 2026-10-10 | DONE | 四道门 + 定向套件全绿；OpenAPI 快照同轮重生成；`RECHECK-20261010-394` 独立复检。 |
