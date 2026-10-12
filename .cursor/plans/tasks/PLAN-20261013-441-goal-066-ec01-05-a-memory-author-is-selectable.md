---
id: PLAN-20261013-441
slug: goal-066-ec01-05-a-memory-author-is-selectable
title: GOAL-20261013-066 cycle 1（EC-01…EC-05）：查询面第三维 + 消费面可传 + 两向反证
status: DONE
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-442-goal-066-ec01-04-a-memory-author-is-selectable.md
memory_entries: []
parent_goal: GOAL-20261013-066
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261013-066 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只让**作者**成为 `query` 的**可选维度**（与 `tier` / `scope` 同一形态）
    并在消费面**可选**传它；`provenance` / `scope` / `tier` 的既有语义**一字不动**；
    **不**做作者鉴权 / **不**做通配·模糊匹配 / **不**给 HTTP 读面加该筛选；
    缺省形态**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**记忆的作者可筛选**：① 勘察定稿（签名逐个 + 实跑 TypeError + 先例 + 三适配器签名，EC-01）→
    ② 作者成为查询面**可选维度**（三适配器同契约；缺省不筛；未知作者空集）（EC-02）→
    ③ 消费面可传 + 载荷**点名**（缺省逐字不变）（EC-03）→ ④ 两向反证 `X-1`…`X-4` 全红（EC-04）→
    ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-author-selectable.py` 逐条读出 —— ① `query` 形参逐个；
      ② 实跑（读得出作者 / 按作者选 ⇒ `TypeError`，**异常类型与消息逐字**）；③ 先例（序 17 的
      `scope` 形态）；④ 三适配器签名逐个。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-author-selectable.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **查询面第三维（EC-02）**：`MemoryStore.query` +1 可选形参；**三适配器同契约**
      （SQLite / PG / **Fake**）；缺省 ⇒ **不筛**（既有行为逐字不变）；**未知作者 ⇒ 空结果**；
      与 `tier` / `scope` **可并存**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/postgres -q` ⇒ 全绿
      + 新用例（同契约 / 缺省不变 / 两维并存 / 未知空集）。
    status: PASS
  - id: WP-3
    criterion: >-
      **消费面可传（EC-03）**：`memory_read` 可传作者 ⇒ 载荷**点名**筛了什么与**筛掉了多少条**
      （与既有 `scope` 的披露形态同源同形）；**缺省载荷逐字相同**；既有键一字不动。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/memory tests/api -q`
      ⇒ 全绿 + 新用例。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`X-1` 查询面忽略作者筛 ⇒ RED；`X-2` 适配器不带该维度 ⇒ RED；
      `X-3` 缺省形态被改动 ⇒ RED；`X-4` 消费面不点名（静默丢条数）⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal066_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal066_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261013-441 — GOAL-20261013-066 cycle 1

## 背景

`GOAL-20261013-066`（MAINLINE 程序表**序 34**，轴 = 质量）。**实测起点**：
序 33 让作者**读得出**（两读面披露 `proposed_by`），但 `MemoryStore.query` 的形参**只有**
`tier` / `scope` ⇒ 传 `proposed_by=` 直接 **`TypeError`**；**实跑**两条不同作者的记忆 ⇒
读面报得出作者而**选不着**（与序 17 的 `scope` **同一缺口形态**：看得见、选不着）。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（签名逐个 + 实跑 + 先例 + 三适配器签名）（WP-1） | `scratch/probe-author-selectable.py` |
| EC-02 | 查询面第三维 + 三适配器同契约（缺省不筛；未知空集）（WP-2） | `pytest tests/adapters tests/postgres -q` |
| EC-03 | 消费面可传 + 载荷点名（缺省逐字不变）（WP-3） | `pytest tests/application/memory tests/api -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：`query` +1 可选形参（三适配器同契约；未知空集；两维并存）。
3. **WP-3**：`memory_read` 可传 + 载荷点名（缺省逐字不变）。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：Port 签名 + 三适配器；EC-03 回填：消费面载荷）
  ——**无迁移**（不落新列，只加查询维度）。
- **安全 / 凭据变化**：无。筛是**选择**，**不是** ACL。
- **兼容性 / 迁移风险**：（EC-02 回填：新形参**可选** ⇒ 既有调用点逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：查询面第三维 + 消费面可传 + 四向反证。 |
| 2026-10-13 | DONE | cycle 1 收口：WP-1…WP-5 全 PASS（独立复检 `RECHECK-20261013-442` = PASS_WITH_WARNINGS）。**交付**：`query` 第三维（三适配器同契约）+ 消费面可传 + 载荷点名 + `_Selection` 参数对象；判据 10 + PG 1 例；四向反证全红 + 归档（`CR=0`）。 |
