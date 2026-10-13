---
id: PLAN-20261014-461
slug: goal-076-ec01-05-declared-query-params-have-explicit-length-bounds
title: GOAL-20261014-076 cycle 1（EC-01…EC-05）：已声明查询参数补显式长度界 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-14
updated_at: 2026-10-14
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261014-076
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261014-076 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只给那 **10 条无界**已声明 str 型参数补**显式长度界**
    （**在路由签名里声明** `max_length=…`）；五面（序 37/40/41/42/43）**不回归**；
    **已界**参数与 `list` 声明**一字不动**；**不**动「非法枚举值 ⇒ 空集」（文档化设计）；
    缺省与合法值**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**已声明查询参数**不再静默接受超长值：① 勘察定稿（超长实跑 + 长度界盘点 + 影响面 +
    缺省基线，EC-01）→ ② 10 条补显式长度界（超长 ⇒ 422 点名；缺省与合法值逐字不变）（EC-02）→
    ③ **射程如实**（五面 + 写面体 + 事件流不回归）+ live e2e + 快照同轮（**预期会变**）（EC-03）→
    ④ 两向反证 `L-1`…`L-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-query-param-length-bounds.py` 逐条读出 ——
      ① 超长值在**无界**参数上 ⇒ 200（≥2 条）；② **对照臂**（有界参数 + 写面 ⇒ 422）；
      ③ **长度界盘点**（逐条：有界 / 无界）；④ 缺省基线（状态码 + 关键键）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-query-param-length-bounds.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **补界（EC-02）**：10 条无界参数补显式 `max_length` ⇒ 超长值 **422 + 点名**；
      缺省与合法值逐字不变；已界参数与 `list` 声明一字不动。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（逐条超长拒绝 / 合法值不变 / 缺省不变 / 已界参数不回归）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：五面（序 37/40/41/42/43）+ 写面体（序 39）+ 事件流（序 38）
      判据全绿；**live e2e** 全绿；快照**同轮**（**预期会变**：`maxLength` 进 schema）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + `pnpm --dir apps/web test:e2e:live` ⇒ 全绿 + 快照 diff 与声明面一致。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`L-1` 无界参数又静默接受超长 ⇒ RED；`L-2` 有界参数被误伤 ⇒ RED；
      `L-3` 缺省形态被改动 ⇒ RED；`L-4` 空值臂被误伤 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal076_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal076_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261014-461 — GOAL-20261014-076 cycle 1

## 背景

`GOAL-20261014-076`（MAINLINE 程序表**序 44**，轴 = 质量）。**实测起点**：
五面已接通，而**长度界**读面 **10/16 条缺失**（`?endpoint_id=<5000 字符>` ⇒ 200），
对照**有界**参数（`kind`）与**写面**（`name`）都拒 ⇒ **读面不设界、写面设界**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（超长实跑 / 长度界盘点 / 影响面 / 缺省基线）（WP-1） | `scratch/probe-query-param-length-bounds.py` |
| EC-02 | 10 条补显式长度界；缺省与合法值逐字不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（五面 / 写面体 / 事件流不回归）+ live + 快照同轮（预期会变）（WP-3） | `pytest ...` + live |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：10 条参数补显式 `max_length`（逐条在证据表里明写界值）。
3. **WP-3**：五面 / 写面体 / 事件流回归 + live e2e + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）路由签名 + OpenAPI（**预期**：`maxLength` 进 schema）
  —— **无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**超长**值 ⇒ 合法值调用逐字不变；
  依赖旧「无界」语义的调用按 EC-01 ③ 逐条处理）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | IN_PROGRESS | cycle 1 建档：补显式长度界 + 四向反证。 |
