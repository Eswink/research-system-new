---
id: PLAN-20261013-443
slug: goal-067-ec01-05-the-http-read-face-does-not-silently-ignore-the-author-filter
title: GOAL-20261013-067 cycle 1（EC-01…EC-05）：HTTP 面按作者筛 + 披露 + 缺省不变 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261013-067
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-067 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只让 HTTP 读面的作者筛选**与 `?scope=` 同形**（可选 / 缺省不筛 /
    披露两键）；`?scope=` 的既有语义**一字不动**；**不**做未知查询参数的通用拒绝 /
    **不**做作者鉴权 / **不**做模糊匹配；缺省形态**逐字不变**；新判据**两向实测**、
    反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让 **HTTP 读面的作者筛选不再被静默忽略**：① 勘察定稿（实跑静默忽略 + 不对称对照 +
    路由签名 + 先例，EC-01）→ ② 路由 +1 可选参数并**按它筛**（披露两键；缺省逐字不变；
    未知作者空集）（EC-02）→ ③ 两个 DTO 形态与快照同轮（EC-03）→
    ④ 两向反证 `Y-1`…`Y-4` 全红（EC-04）→ ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-http-author-filter.py` 逐条读出 ——
      ① 实跑（`?proposed_by=` ⇒ 全量 + 无披露键）；② 对照（`?scope=` ⇒ 多两键）；
      ③ 路由签名逐个；④ 先例（序 17 的 `?scope=` 形态）。`git diff --numstat` ⇒ **零改动**。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-http-author-filter.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **HTTP 面按作者筛（EC-02）**：路由 +1 **可选**查询参数；传 ⇒ 只出那一位的；
      **披露**筛了什么与**筛掉多少条**（与 `?scope=` 同形）；**缺省载荷逐字不变**；
      **未知作者 ⇒ 空集**；与 `?scope=` **可并存**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿
      + 新用例（按作者筛 / 披露 / 缺省不变 / 未知空集 / 可并存）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **DTO 形态与快照同轮（EC-03）**：走**既有的两个形态**（并集形态追加键 —— **不**开
      `response_model_exclude_none`）；动 DTO ⇒ **同轮**重生成并提交
      `docs/api/openapi.m13.json`（+ `apps/web/src/api/types.ts` 若本轮触及）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ 全绿
      + 新用例（两个形态各自的键集 / 快照含新键）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`Y-1` 路由忽略该参数 ⇒ RED；`Y-2` 缺省形态被改动 ⇒ RED；
      `Y-3` 不披露（筛了不报条数）⇒ RED；`Y-4` 未知作者被当成全选 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal067_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal067_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261013-443 — GOAL-20261013-067 cycle 1

## 背景

`GOAL-20261013-067`（MAINLINE 程序表**序 35**，轴 = 质量）。**实测起点**：
序 34 让作者在**查询面 + 编排消费面**选得着，而 **HTTP 读面仍只认 `scope`** ⇒
**实跑**：`GET …?proposed_by=agent:x` ⇒ **200 + 全量两条**、载荷键仍 `['records','scope_note']`
⇒ **参数被静默忽略**（不筛 / 不报错 / 不披露）；对照 `?scope=` **会筛并披露 `filtered_out`**
⇒ 同一读面两个参数**待遇不对称**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（实跑 + 对照 + 签名 + 先例）（WP-1） | `scratch/probe-http-author-filter.py` |
| EC-02 | HTTP 面按作者筛 + 披露 + 缺省不变 + 未知空集（WP-2） | `pytest tests/api -q` |
| EC-03 | 两个 DTO 形态 + 快照同轮（WP-3） | `pytest tests/api tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：路由 +1 可选参数 + 筛 + 披露（沿用序 17 的形态）。
3. **WP-3**：并集 DTO 形态追加键 + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-03 回填：读面 DTO 并集形态 + 快照）——**无迁移**。
- **安全 / 凭据变化**：无。筛是**选择**，**不是** ACL。
- **兼容性 / 迁移风险**：（EC-02 回填：新查询参数**可选** ⇒ 既有请求逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：HTTP 面按作者筛 + 披露 + 四向反证。 |
