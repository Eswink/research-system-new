---
id: PLAN-20261011-417
slug: goal-055-ec01-04-a-program-gate-can-be-declared-at-several-points
title: GOAL-20261011-055 cycle 1（EC-01…EC-04）：程序级闸门可以在多个点声明 + 推进面按多点等 + 四向反证
status: IN_PROGRESS
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261011-055
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-055 的 **EC-01…EC-04**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只动**程序域声明 + 推进判定 + 判据**；
    **复用**序 14/15/16 已立的闸门机制（注册 / 判定 / 恢复三段）—— **不新建**；
    **不**把多点与条件式混成一条声明（互斥**不解除**）；**缺省与单点形态逐字不变**；
    越界 / 重复 / 混用一律**点名拒绝**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让程序级闸门**可以在多个点声明**：① 勘察定稿（字段逐字 + 互斥引文 + 结构不可能，EC-01）→
    ② 多点可声明（缺省 / 单点逐字不变；越界 / 重复 / 混用点名拒绝）（EC-02）→
    ③ 推进面真的按多点等（每点各自可裁决，复用既有面；未命中轮次逐字不变）（EC-03）→
    ④ 四向反证 `R-1`…`R-4`（只认第一个 / 越界被接受 / 重复被接受 / 未声明被改）全红（EC-04）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-multi-gate.py` 逐字列出闸门相关字段（类型 + 行号）
      + 互斥校验引文 + **结构面反证**（两个序号**无处可写**）+ 机制三段逐条在位；
      `git diff --numstat` ⇒ **零改动**（本 WP 只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-multi-gate.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: WP-2
    criterion: >-
      **多点可声明（EC-02）**：声明形态**一组序号**（`tuple[int, ...]` 形态）；
      **缺省 = 不拦**、**单点语义逐字保持**；**越界**（超出 `1..max_runs`）⇒ **点名拒绝**；
      **重复序号** ⇒ **点名拒绝**；与 `human_gate_on_verdicts` **混用** ⇒ 沿用既有互斥点名。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/application -q` ⇒ 全绿
      + 新用例（多点声明 / 缺省不变 / 单点逐字 / 越界点名 / 重复点名 / 混用点名）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **推进面按多点等（EC-03）**：推进到**任一**声明点 ⇒ 等待人工（判词**点名**是**哪一个**
      序号触发的）；**未命中**的轮次**逐字不变**；每个点**各自可裁决**（注册复用既有面）；
      **缺省载荷逐字不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration tests/e2e -q`
      ⇒ 全绿 + 新用例（第 1 点拦 / 第 3 点拦 / 中间轮不拦 / 缺省不变）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`R-1` 多点**只认第一个** ⇒ RED；`R-2` **越界序号被接受** ⇒ RED；
      `R-3` **重复序号被接受** ⇒ RED；`R-4` **未声明形态被改动**（未声明也拦）⇒ RED。
      **基线门**：未按压必须 GREEN（否则非 0 退出）。**二进制读写**复原 + raw `sha256` 一致；
      归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal055_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-055-press-two-way.txt`。
    status: PENDING
---

# PLAN-20261011-417 — GOAL-20261011-055 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-055`（MAINLINE 程序表**序 23**，**深度轴**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（字段逐字 + 互斥引文 + 结构不可能 + 机制三段） | PENDING |
| WP-2 | 多点可声明（缺省 / 单点逐字不变；越界 / 重复 / 混用点名拒绝） | PENDING |
| WP-3 | 推进面按多点等（每点各自可裁决；未命中轮次逐字不变） | PENDING |
| WP-4 | 四向反证 `R-1`…`R-4` + 基线门 + 二进制复原 | PENDING |

## 实施清单

- [ ] WP-1 勘察定稿：闸门字段与校验逐条读数（只读，零改动）
- [ ] WP-2 域声明加**一组序号**形态 + 校验（越界 / 重复 / 混用点名）+ 新用例
- [ ] WP-3 推进判定按多点求值（点名触发者）+ 每点各自可裁决 + 新用例
- [ ] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | （待本轮实测回填） |
| 四向反证 | （待本轮实测回填） |
| 落库形态（域字段 + 三适配器 + 快照的连带面） | （待本轮实测回填） |

## 影响报告

- **Domain / API / schema 变化**：（待本轮实测回填 —— 本 GOAL **可能**动域字段 + 三适配器）
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：（待本轮实测回填）
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：勘察（字段 / 互斥 / 结构不可能）+ 多点声明 + 推进面 + 四向反证。 |
