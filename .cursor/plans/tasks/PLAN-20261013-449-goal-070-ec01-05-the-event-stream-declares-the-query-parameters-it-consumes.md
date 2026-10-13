---
id: PLAN-20261013-449
slug: goal-070-ec01-05-the-event-stream-declares-the-query-parameters-it-consumes
title: GOAL-20261013-070 cycle 1（EC-01…EC-05）：事件流声明它消费的查询参数 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261013-070
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-070 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只把 `/runs/{run_id}/events` **消费**的 `cursor` / `poll`
    **声明进签名**（守卫自动接管）；**不**改 SSE 帧格式 / 续传 / 去重语义 / 头路径 /
    写面 / 序 37 的守卫；缺省形态**逐字不变**；新判据**两向实测**、
    反证脚本**带基线门 + `timeout` 收口**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让事件流路由**声明它消费的查询参数**：① 勘察定稿（消费/声明差集 + OpenAPI 空 + 实跑静默 +
    SSE 危害 + 正确基线，EC-01）→ ② `cursor` / `poll` 声明进签名（缺省逐字不变；守卫自动接管）
    （EC-02）→ ③ **射程如实**（SSE 语义 / 序 37 不动）+ 快照同轮（**预期会变**）（EC-03）→
    ④ 两向反证 `V-1`…`V-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-event-stream-params.py` 逐条读出 ——
      ① 差集扫描（唯一 `run_events.py`）；② OpenAPI 声明面**空**；③ 实跑 `?po11=0` /
      `?nonsense=1` 都 **200**；④ SSE 危害（打错 `poll` ⇒ 静默保持轮询；`timeout` 收口）；
      ⑤ 正确形态基线（`?poll=0` / `?cursor=` / 头路径照旧）。
      `git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-event-stream-params.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **声明进签名（EC-02）**：`cursor: str | None = Query(default=None)` /
      `poll: str = Query(default="1")`（与现行为**逐字相同**）；未知参数 ⇒
      **422 + 逐个点名 + 已知集**（序 37 守卫**自动**接管，不改守卫本体）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（声明面 / 未知点名 / `?poll=0` 与 `?cursor=` 逐字 / 头路径不变 / 缺省不变）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **射程如实 + 无回归（EC-03）**：SSE 帧 / 续传 / 去重**一字不动**（既有 SSE 用例全绿）；
      序 37 守卫与判据不回归；快照**同轮**重生成并提交（本轮**预期会变** —— 如实登记）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/tooling -q`
      ⇒ 全绿 + 快照 diff 与声明面一致。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`V-1` 声明被移除 ⇒ RED；`V-2` 缺省被改动 ⇒ RED；
      `V-3` `poll=0` 语义被破坏 ⇒ RED；`V-4` `cursor` 续传被破坏 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal070_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal070_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261013-449 — GOAL-20261013-070 cycle 1

## 背景

`GOAL-20261013-070`（MAINLINE 程序表**序 38**，轴 = 质量）。**实测起点**：
序 37 的守卫**按签名**决定射程（这是对的），但它**暴露**了更上游的缺陷 ——
`GET /runs/{run_id}/events` **从原始 `request.query_params` 读** `cursor` / `poll`，
**却一个都没声明** ⇒ OpenAPI 不可见 + 打错名字静默吞掉（**SSE 模式下更糟**：打错 `poll`
⇒ 静默**保持轮询**）。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 五段读数（差集 / 空声明 / 实跑静默 / SSE 危害 / 正确基线）（WP-1） | `scratch/probe-event-stream-params.py` |
| EC-02 | `cursor`/`poll` 声明进签名 + 守卫自动接管 + 头路径不变（WP-2） | `pytest tests/api -q` |
| EC-03 | 射程如实（SSE 不动）+ 序 37 不回归 + 快照同轮（预期变）（WP-3） | `pytest tests/api tests/contracts tests/tooling -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；五段读数；SSE 段必须 `timeout` 收口）。
2. **WP-2**：`Query(...)` 声明进签名（缺省逐字同现行为）。
3. **WP-3**：SSE 回归 + 快照重生成（预期变）+ 序 37 不回归。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填）路由签名 + OpenAPI（**预期**）
  —— **无迁移**。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：只加声明 ⇒ 已知/缺省形态逐字不变；
  未知参数从「静默」变「422」—— 与序 37 的口径一致）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：事件流声明它消费的查询参数 + 四向反证。 |
