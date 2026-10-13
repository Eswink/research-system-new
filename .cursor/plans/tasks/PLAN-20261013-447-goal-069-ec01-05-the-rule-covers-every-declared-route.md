---
id: PLAN-20261013-447
slug: goal-069-ec01-05-the-rule-covers-every-declared-route
title: GOAL-20261013-069 cycle 1（EC-01…EC-05）：签名导出守卫 + 17 条路由覆盖 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261013-069
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-069 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只把序 36 的未知参数纪律**机械扩到已声明查询参数的路由**
    （已知集**从签名导出**）；**不**覆盖无参数路由 / **不**改写面 / **不**动已知参数语义 /
    **不**退步序 36 的记忆读面行为；缺省形态**逐字不变**；新判据**两向实测**、
    反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**未知查询参数的纪律覆盖每条已声明查询参数的路由**：① 勘察定稿（AST 导出 + 实跑 +
    零命中 + 射程分类 + 序 36 在位，EC-01）→ ② 未知参数**逐路由点名拒绝**（已知集**从签名导出**；
    多个逐个；已知与缺省逐字不变）（EC-02）→ ③ **射程如实**（无参数路由不受影响；序 36 不回归）
    + 快照同轮（EC-03）→ ④ 两向反证 `W-1`…`W-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-query-param-coverage.py` 逐条读出 ——
      ① AST 导出（17 条 + 逐条清单）；② 实跑（两条不同路由打错 ⇒ 200）；③ 零命中；
      ④ 射程分类（65 条 GET / 17 条已声明 / 无参数面**不**覆盖）；⑤ 序 36 守卫在位。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-query-param-coverage.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **签名导出守卫（EC-02）**：已知集**从路由签名导出**（不手写清单）；未知参数
      ⇒ **422 + 逐个点名 + 该路由的已知集**；**已知与缺省逐字不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（导出面与签名一致 / 逐路由点名 / 多个逐个 / 已知不变 / 缺省不变）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：无查询参数的路由**不受影响**（对照组）；
      序 36 的记忆读面判据**全绿**；若动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 新用例（对照组 / 记忆读面回归）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`W-1` 导出面返回空集 ⇒ RED；`W-2` 导出面**多收**（含路径参数）⇒ RED；
      `W-3` 缺省形态被改动 ⇒ RED；`W-4` 只覆盖记忆读面 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal069_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal069_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261013-447 — GOAL-20261013-069 cycle 1

## 背景

`GOAL-20261013-069`（MAINLINE 程序表**序 37**，轴 = 质量）。**实测起点**：
序 36 让**记忆读面**的未知参数点名拒绝（射程**有意**只有那两个 GET），而**实测**全仓
**17 条 GET 已声明查询参数**（签名可导出），其中 `/notifications?limt=5` 与
`/cost-forecast?horizon_day=7` **都 200 + 静默吞掉** ⇒ 调用方**以为设了参数**而用默认值。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 五段读数（AST 导出 / 实跑 / 零命中 / 射程分类 / 序 36 在位）（WP-1） | `scratch/probe-query-param-coverage.py` |
| EC-02 | 未知参数逐路由点名 + 已知集**签名导出** + 已知与缺省不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（无参数路由不受影响）+ 序 36 不回归 + 快照同轮（WP-3） | `pytest tests/api tests/contracts tests/tooling -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；五段读数）。
2. **WP-2**：签名导出守卫（17 条路由覆盖；逐路由点名）。
3. **WP-3**：射程对照组判据 + 序 36 回归 + 快照同轮（若动 DTO）。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：请求处理链的参数校验面）——**无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**未知**参数 ⇒ 既有调用逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：签名导出守卫 + 17 条路由覆盖 + 四向反证。 |
