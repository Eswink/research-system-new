---
id: PLAN-20261012-435
slug: goal-063-ec01-05-a-resolved-pair-is-visible-on-both-sides
title: GOAL-20261012-063 cycle 1（EC-01…EC-05）：对端可读 + 处置扣已消解 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261012-063
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-063 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只加**消解记载的对端可见性**与处置面的**扣减**；
    `contradictions` 的**声明**语义、`resolutions` 的**记载**语义、序 30 的
    `conflicted_by` 语义**一字不动**；**不**做自动消解 / **不**做自动失效 /
    **不**做内容级语义比较；缺省形态**逐字不变**；新判据**两向实测**、
    反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**已消解的一对在两端都看得见**：① 勘察定稿（零命中 + 实跑缺口 + 先例 + 记载读法未动，
    EC-01）→ ② 对端可读 + 处置扣已消解（**逐对**；缺省逐字不变）（EC-02）→ ③ 两读面同源 +
    既有键逐字不变 + 快照同轮（EC-03）→ ④ 两向反证 `Z-1`…`Z-4` 全红（EC-04）→
    ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-resolved-pair-face.py` 逐条读出 ——
      ① 消解的反向面**零命中**；② **实跑**：一对被消解 ⇒ **A 侧 `USE` / B 侧 `CONFLICTED`**；
      ③ 先例 `conflicted_by_index` 形态逐条读出；④ `resolutions` 读法**逐字仍是单向**。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-resolved-pair-face.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **对端可读 + 处置扣已消解（EC-02）**：新增**反向消解表**（扫同批记录，与序 30 同一手法）；
      被消解方读面**逐条披露**（谁记的 / 何时）；处置面**先扣后判**（已消解的那一对**不再**
      算作反向冲突）；**逐对**（只消解一对 ⇒ 其余仍算数）；**缺省形态逐字不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒ 全绿
      + 新用例（对端可读 / 逐对 / 缺省逐字不变）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **两读面同源（EC-03）**：编排面与 HTTP 读面**同源**披露对端可见性；
      **既有键逐字不变**；动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`Z-1` 反向消解表被摘掉 ⇒ RED；`Z-2` 处置面**不**扣已消解 ⇒ RED；
      `Z-3` **缺省形态**被改动 ⇒ RED；`Z-4` **只消解一对**被当成全消解 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal063_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal063_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261012-435 — GOAL-20261012-063 cycle 1

## 背景

`GOAL-20261012-063`（MAINLINE 程序表**序 31**，轴 = 质量）。**实测起点**：
A 声明与 B 冲突、人把这一对**消解**掉 ⇒ **A 读 `USE`**（记载在 A 身上），
而 **B 仍读 `CONFLICTED`**（`conflicted_by=['m-a']` 未被抵消）⇒ **同一条已消解的分歧
两端处置不一致**；序 30 的 `conflicted_by_index` 就是同一手法的先例。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（零命中 + 实跑缺口 + 先例 + 记载未动）（WP-1） | `scratch/probe-resolved-pair-face.py` |
| EC-02 | 对端可读 + 处置扣已消解（逐对；缺省逐字不变）（WP-2） | `pytest tests/application tests/domain -q` |
| EC-03 | 两读面同源 + 既有键逐字不变 + 快照同轮（WP-3） | `pytest tests/api tests/adapters tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：反向消解表 + 处置面扣减 + 逐对。
3. **WP-3**：两读面同源披露 + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：反向消解表；EC-03 回填：读面键 + 快照）
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：纯附加披露 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：对端可读 + 处置扣减 + 四向反证。 |
