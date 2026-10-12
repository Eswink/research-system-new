---
id: PLAN-20261012-427
slug: goal-059-ec01-05-the-waiting-face-timeline-is-reachable
title: GOAL-20261012-059 cycle 1（EC-01…EC-05）：界可声明可落库 + 出口可注入 + 两向反证
status: DONE
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: .cursor/plans/rechecks/RECHECK-20261012-428-goal-059-ec01-04-the-timeline-chain-is-reachable.md
memory_entries: []
parent_goal: GOAL-20261012-059
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-059 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只把序 24/25 的既有产物**接通到产品面**（界可声明 / 可落库 /
    出口可注入）；序 24 的超期判定语义与序 25 的端口形状、三态纪律**一字不动**；
    **不**做真实外发 / **不**做升级链 / **不**做重试·去重·投递保证 / **不**自动放行或拒绝；
    缺省形态**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**等待面的时限链在产品面上可达**：① 勘察定稿（三段读数：声明面 / 落库面 / 出口面
    逐段实跑，EC-01）→ ② 界**可声明**（两 DTO +1 可选键）+ **可落库**（SQLite 加法式列 +
    PG 迁移 024 只加列；坏形态点名）（EC-02）→ ③ 出口**可注入**（组合根决定；缺省
    `NullNudgeSink` ⇒ 逐字不变）+ 快照同轮（EC-03）→ ④ 两向反证 `V-1`…`V-4` 全红（EC-04）
    → ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-nudge-reachability.py` 逐条读出 ——
      ① 声明面两个 DTO 的 `model_fields`（键不在）；② 落库 round-trip（`60` ⇒ `None`）；
      ③ `services/` 零命中；④ 迁移目录逐条读出；⑤ 序 24/25 的产物在树（判定两句 /
      端口三类 / 缺省实现在位）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-nudge-reachability.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **界可声明、可落库（EC-02）**：`ProgramCreateDto` / `ProgramDetailDto` 各 +1**可选**键
      （缺省 `None` ⇒ 逐字不变）；SQLite `_SCHEMA` + `_ensure_compatible_schema`（加法式
      `ALTER TABLE`）落列，`_encode_program` / `_decode_program` 带上；PG 迁移 `024` 只加列 +
      `_PROGRAM_SELECT` / `INSERT` 带列；**域校验一字不动**（非正整数仍点名拒绝）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/domain -q` ⇒ 全绿
      + 新用例（两库往返 / 缺省逐字不变 / 坏界点名）。
    status: PASS
  - id: WP-3
    criterion: >-
      **出口可注入（EC-03）**：组合根依赖面 +1 可注入字段（缺省 `NullNudgeSink`）；
      推进路由把界与出口交给既有推进入口；**只读判定面仍只读**（无 `.nudge(` / 无 `NudgeSink`）；
      动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`（+ `apps/web/src/api/types.ts`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/application tests/architecture -q`
      ⇒ 全绿 + 新用例（注入后收到 / 未注入静默 / 只读面无写方法 / 快照含新键）。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`V-1` 落库去掉新列 ⇒ RED；`V-2` DTO 摘掉新键 ⇒ RED；
      `V-3` 组合根不注入 ⇒ RED；`V-4` 缺省也送（三态纪律被改）⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal059_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal059_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261012-427 — GOAL-20261012-059 cycle 1

## 背景

`GOAL-20261012-059`（MAINLINE 程序表**序 27**，轴 = 连续性）。**实测起点**：
序 24 让等待面能判超期、序 25 让信号有出口，但**三层全断** ——
① `services/api/dto/programs.py` 对 `gate_nudge` **零命中**；② `SqliteProgramStore`
round-trip **静默丢弃**（`60` ⇒ `None`，两库都无该列）；③ `services/` 对 `nudges=` /
`NudgeSink` **零命中**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 三段读数逐段实跑（WP-1） | `scratch/probe-nudge-reachability.py` 输出 |
| EC-02 | 界可声明、可落库（WP-2） | `pytest tests/adapters tests/domain -q` 全绿 |
| EC-03 | 出口可注入 + 快照同轮（WP-3） | `pytest tests/api tests/application tests/architecture -q` 全绿 |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；三段读数）。
2. **WP-2**：两 DTO 加键；SQLite 列 + 加法式补齐 + 编解码；PG 迁移 `024` + select/insert。
3. **WP-3**：组合根可注入字段 + 推进路由透传 + 快照/web types 同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：DTO +2 键；迁移 024；两库同契约）
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只加列 / 只加可选键 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：三段读数定稿 + 接线三段（声明 / 落库 / 注入）+ 四向反证。 |
| 2026-10-12 | DONE | cycle 1 收口：WP-1…WP-5 全 PASS（独立复检 `RECHECK-20261012-428` = PASS_WITH_WARNINGS）。**交付**：两 DTO +1 可选键 / SQLite 加法式列 + PG 迁移 `024` / 组合根可注入出口 + 推进路由交出 / 产品路径判据 4 例 + 落库往返判据 19 例 / 四向反证全红 + 归档（`CR=0`）/ 收口验证器 + 断言集进树。 |
