---
id: PLAN-20261013-453
slug: goal-072-ec01-05-routes-without-declared-query-params-also-refuse-them
title: GOAL-20261013-072 cycle 1（EC-01…EC-05）：未声明读面拒绝查询参数 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261013-072
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-072 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只把守卫的**空集支**（读面但无声明）从「跳过」改成
    「有查询参数 ⇒ 422 + 逐个点名」；`None` 支（非读面）**一字不动**；已声明面（序 37/38）
    与写面（序 39）**不回归**；缺省形态**逐字不变**；落地前先做**影响面盘点**；
    新判据**两向实测**、反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**未声明查询参数**的读面路由**不再静默吞掉**查询参数：① 勘察定稿（实跑 + 射程清单 +
    影响面盘点 + 缺省基线，EC-01）→ ② 空集支改拒绝（422 + 逐个点名 + 明写「不接受查询参数」；
    缺省逐字不变）（EC-02）→ ③ **射程如实**（已声明面 / 写面不回归）+ 快照同轮
    （**预期零 diff**）（EC-03）→ ④ 两向反证 `Y-1`…`Y-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-undeclared-query-params.py` 逐条读出 ——
      ① 实跑：未声明路由收到查询串 ⇒ **200**（≥2 条）；② 射程清单：未声明查询参数的
      GET 路由**逐条**；③ 影响面盘点：web/tests 对这些路由的带查询串调用（有 ⇒ 逐条点名）；
      ④ 缺省基线（不传参数的状态码 + 关键键）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-undeclared-query-params.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **空集支改拒绝（EC-02）**：未声明读面收到**任何**查询参数 ⇒ **422 + 逐个点名**；
      **缺省逐字不变**；**非读面一字不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（未声明路由点名 / 多个逐个 / 缺省不变 / 非读面不受影响）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：已声明面（序 37/38）与写面（序 39）判据全绿；
      影响面（EC-01 ③）逐条处理；快照同轮（**预期零 diff**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`Y-1` 未声明面又被静默忽略 ⇒ RED；`Y-2` 已声明面被误伤 ⇒ RED；
      `Y-3` 缺省形态被改动 ⇒ RED；`Y-4` **非读面被误伤**（射程越界）⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal072_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal072_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261013-453 — GOAL-20261013-072 cycle 1

## 背景

`GOAL-20261013-072`（MAINLINE 程序表**序 40**，轴 = 质量）。**实测起点**：
「静默吞掉」族已连接通三面（读面已声明 37/38、写面 39），**仅剩**「读面**未声明**」
这一面仍静默 —— 全仓 **58 条** GET 未声明查询参数，收到查询串时**照样 200**
（实测 `/projects?definitely_unknown=1` ⇒ 200）。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（实跑 / 射程清单 / 影响面盘点 / 缺省基线）（WP-1） | `scratch/probe-undeclared-query-params.py` |
| EC-02 | 未声明读面 422 + 逐个点名；缺省逐字不变；非读面不动（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（已声明面 / 写面不回归）+ 快照同轮（预期零 diff）（WP-3） | `pytest tests/api tests/contracts tests/tooling -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数；影响面盘点必须**先**做）。
2. **WP-2**：守卫空集支改拒绝（共享守卫一处声明）。
3. **WP-3**：已声明面 / 写面回归 + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）请求处理链的校验面 —— 不动签名
  ⇒ 快照**预期零 diff**；**无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**未声明路由上的**查询参数 ⇒
  正确调用（不传查询串）逐字不变；依赖旧吞掉行为的调用按 EC-01 ③ 逐条处理）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：未声明读面拒绝查询参数 + 四向反证。 |
