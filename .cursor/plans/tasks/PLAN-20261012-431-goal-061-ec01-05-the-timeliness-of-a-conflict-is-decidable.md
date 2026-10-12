---
id: PLAN-20261012-431
slug: goal-061-ec01-05-the-timeliness-of-a-conflict-is-decidable
title: GOAL-20261012-061 cycle 1（EC-01…EC-05）：冲突时效可判定 + 两读面同源 + 两向反证
status: DONE
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: .cursor/plans/rechecks/RECHECK-20261012-432-goal-061-ec01-04-the-timeliness-of-a-conflict-is-decidable.md
memory_entries: []
parent_goal: GOAL-20261012-061
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-061 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只加**冲突声明的时效面**（按调用方给的时点判定，**不读挂钟**）；
    记忆自身的时效机制（`validity_at` 三态）与五态处置**一字不动**；
    **不**自动消解 / **不**自动失效（判定仍由**人**给 —— 序 26 立的边界**一字不动**）；
    **不**做内容级语义比较；缺省形态**逐字不变**；新判据**两向实测**、
    反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**冲突声明的时效**成为可读事实：① 勘察定稿（时效面零命中 + `ConflictResolution` 字段 +
    记忆自身时效面可复用，EC-01）→ ② 冲突时效可判定（三态互不混用且点名；缺省逐字不变；
    坏时点点名拒绝）（EC-02）→ ③ 两读面**同源**披露（既有键逐字不变）+ 快照同轮（EC-03）→
    ④ 两向反证 `X-1`…`X-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-conflict-timeliness.py` 逐条读出 ——
      ① 时效面**零命中**（六组候选标识符，三个产品根）；② `ConflictResolution` 字段**逐个读出**
      （无时效面）；③ 记忆自身时效机制**在树**（`review_after` / `expires_at` + `validity_at`）；
      ④ 五态处置**逐条读出**（无「冲突已不再算数」）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-conflict-timeliness.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: WP-2
    criterion: >-
      **冲突时效可判定（EC-02）**：按**调用方给的时点**判定冲突声明的时效（三态**互不混用**
      且都**点名**）；**缺省形态逐字不变**（未声明时效 ⇒ 不猜，冲突仍按既有五态处置）；
      坏时点 / 坏声明**点名拒绝**；**不**自动消解 / **不**自动失效。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/application -q` ⇒ 全绿
      + 新用例（三态各自可判 / 缺省逐字不变 / 坏形态点名）。
    status: PASS
  - id: WP-3
    criterion: >-
      **两读面同源披露（EC-03）**：编排消费面与 HTTP 读面**同源**（同一批纯函数）披露冲突时效；
      **既有键逐字不变**（未声明时效 ⇒ 逐字与改动前相同）；落库面（若加声明位）两库同契约；
      动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 未声明逐字不变 / 快照含新键）。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`X-1` 过期冲突仍被判有效 ⇒ RED；`X-2` 未到期被判失效 ⇒ RED；
      `X-3` 未声明时效被当成已到期 ⇒ RED；`X-4` 缺省形态被改动 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal061_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal061_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261012-431 — GOAL-20261012-061 cycle 1

## 背景

`GOAL-20261012-061`（MAINLINE 程序表**序 29**，轴 = 质量）。**实测起点**：
`contradictions` 可声明（序 13）、可落库、可处置（序 19 第五态）、可消解（序 26），
但**时效面零命中**（`conflict_valid` / `contradiction_valid` / `conflict_review` 三根全零）
且 `ConflictResolution` 只有（对端 / 消解者 / 时点）⇒ **冲突一经声明永久算数**，
与记忆自身的 `review_after` / `expires_at` 机制（序 7 起）**不对称**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（时效面零命中 + 字段 + 可复用面 + 五态）（WP-1） | `scratch/probe-conflict-timeliness.py` |
| EC-02 | 冲突时效可判定 + 坏形态点名（WP-2） | `pytest tests/domain tests/application -q` |
| EC-03 | 两读面同源 + 既有键逐字不变 + 快照同轮（WP-3） | `pytest tests/api tests/adapters tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：冲突时效判定（复用 `validity_at` 的时点纪律；三态互不混用 + 点名）。
3. **WP-3**：两读面同源披露 + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：冲突时效声明位；EC-03 回填：读面 + 快照）
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只加可选声明 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：冲突时效可判定 + 两读面同源 + 四向反证。 |
| 2026-10-12 | DONE | cycle 1 收口：WP-1…WP-5 全 PASS（独立复检 `RECHECK-20261012-432` = PASS_WITH_WARNINGS）。**交付**：两个声明位（记录 + 提案）+ `ConflictTimelinessState` 三态纯函数 + 两条坏形态点名 + 三适配器同契约（迁移 `026`）+ 两读面同源披露 + 快照同轮；判据 19 例；四向反证全红 + 归档（`CR=0`）。 |
