---
id: PLAN-20261013-455
slug: goal-073-ec01-05-write-face-routes-also-refuse-query-parameters
title: GOAL-20261013-073 cycle 1（EC-01…EC-05）：写面拒绝查询参数 + 两向反证
status: DONE
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-456-goal-073-ec01-04-write-face-routes-also-refuse-query-parameters.md
memory_entries: []
parent_goal: GOAL-20261013-073
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-073 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只把守卫的 **`None` 支**（非读面）从「不在射程」改成
    「有查询参数 ⇒ 422 + 逐个点名」；**读面两支**（已声明 / 未声明）**一字不动**；
    写面**请求体**纪律（序 39）**不回归**；缺省形态**逐字不变**；落地前先做**影响面盘点**；
    新判据**两向实测**、反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**写面（非读面）**路由**不再静默吞掉**查询参数：① 勘察定稿（实跑 + 写面清单 +
    影响面盘点 + 缺省基线，EC-01）→ ② None 支改拒绝（422 + 逐个点名 + 明写「不接受查询参数」；
    读面与缺省逐字不变）（EC-02）→ ③ **射程如实**（读面 / 写面体不回归）+ live e2e +
    快照同轮（**预期零 diff**）（EC-03）→ ④ 两向反证 `Z-1`…`Z-4` 全红（EC-04）→
    ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-write-face-query-params.py` 逐条读出 ——
      ① 实跑：写面带查询参数 ⇒ **成功**（POST 与 PATCH 各一）；② 写面路由**逐条**读数
      （数量 + 是否声明查询参数）；③ 影响面：web/tests 带查询串的写调用（有 ⇒ 逐条点名）；
      ④ 缺省基线（不带查询串的写请求的状态码 + 关键键）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-write-face-query-params.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **None 支改拒绝（EC-02）**：非读面路由收到查询参数 ⇒ **422 + 逐个点名 + 明写
      「不接受查询参数」**；读面两支**一字不动**；缺省逐字不变。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（写面点名 / 多个逐个 / 读面不回归 / 缺省不变）。
    status: PASS
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：读面（序 36/37/38/40）与写面体（序 39）判据全绿；
      影响面（EC-01 ③）逐条处理；**live e2e** 全绿；快照同轮（**预期零 diff**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + `pnpm --dir apps/web test:e2e:live` ⇒ 全绿。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`Z-1` 写面又被静默忽略 ⇒ RED；`Z-2` 读面被误伤 ⇒ RED；
      `Z-3` 缺省形态被改动 ⇒ RED；`Z-4` 读面未声明面被误伤 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal073_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal073_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261013-455 — GOAL-20261013-073 cycle 1

## 背景

`GOAL-20261013-073`（MAINLINE 程序表**序 41**，轴 = 质量）。**实测起点**：
「静默吞掉」族已连接通四面（读面已声明 37/38 / 写面体 39 / 读面未声明 40），
**仅剩**非读面这一族仍静默 —— 写面带查询参数**照样成功**
（实测 `POST /projects?definitely_unknown=1` ⇒ 201）。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（实跑 / 写面清单 / 影响面盘点 / 缺省基线）（WP-1） | `scratch/probe-write-face-query-params.py` |
| EC-02 | 非读面 422 + 逐个点名；读面与缺省逐字不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（读面 / 写面体不回归）+ live e2e + 快照同轮（预期零 diff）（WP-3） | `pytest ...` + live |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数；影响面盘点必须**先**做）。
2. **WP-2**：守卫 None 支改拒绝（共享守卫一处声明）。
3. **WP-3**：读面 / 写面体回归 + live e2e + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

| WP | 命令 | 读数 | commit |
| --- | --- | --- | --- |
| WP-1 | `uv run --frozen --no-sync python -B scratch/probe-write-face-query-params.py` | `POST /projects?definitely_unknown=1` ⇒ **201**；`PATCH ?zz=1` ⇒ **200**；**63 条非读面路由 / 声明 0 条**；影响面：626 写调用点**同行带查询串 0**（如实登记为上界）；缺省基线（201/200 + 五键） | （本轮） |
| WP-2 | `pytest tests/api -q` | **665 passed**（新 6 例）；**四处改签**（序 37 判据改名+改判 / 序 40 判据改名+改判 / 序 36 过期注释 / 两处收口断言集 —— 后者被 `test_closeout_verifiers` **当场抓到**） | `a7ab5e2e` |
| WP-3 | `pytest tests/contracts tests/tooling -q` + `tests/e2e` + **live e2e** | 1999 + 307 + **53 passed**；快照 `git diff --numstat` ⇒ **零 diff**（不动签名） | `a7ab5e2e` |
| WP-4 | `uv run --frozen --no-sync python -B scratch/goal073_press.py` | **BASELINE GREEN**（23 passed）；Z-1/Z-2/Z-3/Z-4 全 **RED**（**首跑即全红、无假绿**）；逐条 `sha 复原一致=True`；`SUMMARY presses=4 all_red_and_restored=True`；归档 `evidence/GOAL-20261013-073-press-two-way.txt`（二进制、`CR=0`）；零进程泄漏 | （本轮） |

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）请求处理链的校验面 —— 不动签名
  ⇒ 快照**预期零 diff**；**无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只拒绝**非读面路由上的**查询参数 ⇒
  正确调用（不带查询串）逐字不变；依赖旧吞掉行为的调用按 EC-01 ③ 逐条处理）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：写面拒绝查询参数 + 四向反证。 |
