---
id: PLAN-20261012-429
slug: goal-060-ec01-05-the-hybrid-form-of-gate-declarations
title: GOAL-20261012-060 cycle 1（EC-01…EC-05）：混合式闸门可声明 + 双触发各自点名 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261012-060
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-060 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只加**混合式声明**（多点 **且** 条件）与它在推进里的求值；
    三条既有声明各自的**语义与判词一字不动**；**不**解除「同一维度上两条声明互斥」的纪律；
    **不**新造机制（复用三条既有的注册 / 判定 / 恢复面）；缺省形态**逐字不变**；
    新判据**两向实测**、反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**闸门声明的混合式**可声明：① 勘察定稿（三条声明的类型 + 互斥判词 + 三条机制三段，
    EC-01）→ ② 混合式可声明（多点 **且** 条件；缺省逐字不变；坏形态点名）（EC-02）→
    ③ 推进面按混合式判定（两种触发**各自点名**）+ 两库同契约 + DTO 透传 + 快照同轮（EC-03）→
    ④ 两向反证 `W-1`…`W-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-gate-hybrid.py` 逐条读出 ——
      ① 三条声明的类型（`dataclasses.fields` / 字段注解逐个）；② 互斥判词（行号 + 逐字）；
      ③ 三条各自的机制三段（注册 / 判定 / 恢复）逐条定位；④ 序 24 的时限面**正交**（不参与
      互斥 —— 本轮**一字不动**）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-gate-hybrid.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: WP-2
    criterion: >-
      **混合式可声明（EC-02）**：域上 +1 声明形态（多点 **且** 条件）；缺省 `None` ⇒
      **逐字不变**；坏形态（空组 / 空判词 / 越界 / 重复 / 坏取值）**点名拒绝**；
      **同一维度上**的既有互斥**仍成立**（两条同维声明并用 ⇒ 仍点名拒绝）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain -q` ⇒ 全绿
      + 新用例（混合式可声明 / 缺省逐字不变 / 各坏形态点名）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **推进面按混合式判定（EC-03）**：两种触发**各自点名**是哪一条触发的（多点命中 /
      条件命中 / 两者都命中时**两条都点名**）；两库同契约（SQLite 加法式列 + PG 迁移只加列）；
      DTO 透传（建与读两侧）；动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters tests/api
      tests/contracts -q` ⇒ 全绿 + 新用例（两种触发各自点名 / 都命中都点名 / 两库往返）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`W-1` 混合声明被拒 ⇒ RED；`W-2` 只按多点判（条件被忽略）⇒ RED；
      `W-3` 只按条件判 ⇒ RED；`W-4` 缺省形态被改动 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal060_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal060_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261012-429 — GOAL-20261012-060 cycle 1

## 背景

`GOAL-20261012-060`（MAINLINE 程序表**序 28**，轴 = 深度）。**实测起点**：
三条闸门声明（`human_gate_at_index` / `_on_verdicts` / `_at_indexes`）在
`packages/domain/program.py` **互斥**（`are mutually exclusive` ⇒ 同时声明即点名拒绝）
⇒ 「第 1、3 轮停，**且**判词为 X 时也停」**结构上做不到**；而三条机制**都已全在**
（序 14/15/16/23）⇒ 缺的只是**组合维度**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 三条声明类型 + 互斥判词 + 三段机制（WP-1） | `scratch/probe-gate-hybrid.py` 输出 |
| EC-02 | 混合式可声明 + 坏形态点名（WP-2） | `pytest tests/domain -q` 全绿 |
| EC-03 | 推进面双触发各自点名 + 两库 + DTO + 快照（WP-3） | `pytest tests/application tests/adapters tests/api tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；三条声明 + 互斥 + 三段机制 + 时限面正交）。
2. **WP-2**：域上 +1 混合式声明（多点 **且** 条件）+ 校验；同维互斥仍成立。
3. **WP-3**：推进面双触发各自点名；两库列 + 迁移；DTO + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：域 +1 声明形态；EC-03 回填：两库列 + 迁移 + DTO）
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只加可选声明 / 只加列 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：混合式可声明 + 双触发各自点名 + 四向反证。 |
