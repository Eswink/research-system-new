---
id: PLAN-20261012-437
slug: goal-064-ec01-05-references-to-a-deleted-record-are-no-longer-silent
title: GOAL-20261012-064 cycle 1（EC-01…EC-05）：悬空引用可读 + 两读面同源 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261012-064
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-064 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只加**悬空引用的可见性**（读面点名）；
    `contradictions` / `supersedes` / `terminal` 的既有语义与取值**一字不动**；
    **不**级联删除 / **不**自愈 / **不**阻断删除 / **不**做内容级语义比较；
    缺省形态**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**引用被删的记录不再是静默的**：① 勘察定稿（零命中 + 实跑 + 写面对照 + 先例，EC-01）→
    ② 悬空引用可读（两方向各自点名；缺省逐字不变；跨范围不猜）（EC-02）→ ③ 两读面同源 +
    既有键逐字不变 + 快照同轮（EC-03）→ ④ 两向反证 `V-1`…`V-4` 全红（EC-04）→
    ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-dangling-reference.py` 逐条读出 ——
      ① 悬空面**零命中**；② **实跑**：删掉被引记录 ⇒ 读面照旧 + **无悬空标记**
      （`terminal` 报 `CURRENT`）；③ **写面对照**：未知 id **拒绝提交**（两条判词逐字）；
      ④ 先例 `TERMINAL_OUT_OF_VIEW` 在树。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-dangling-reference.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PENDING
  - id: WP-2
    criterion: >-
      **悬空引用可读（EC-02）**：新增悬空判定（**扫同批记录**，与序 18/30/31 同一手法）；
      两个方向（`supersedes` / `contradictions`）**各自点名**；**缺省形态逐字不变**；
      **跨范围不猜**（只看本批 —— 分不清「被删」与「在范围外」时**如实**给候选键）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒ 全绿
      + 新用例（悬空可读 / 两方向分开 / 缺省逐字不变 / 跨范围不猜）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **两读面同源（EC-03）**：编排面与 HTTP 读面**同源**披露悬空引用；
      **既有键逐字不变**（`terminal` 的取值**一字不动** —— 悬空信号**另键**）；
      动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`V-1` 悬空表被摘掉 ⇒ RED；`V-2` **跨范围**被当成悬空 ⇒ RED；
      `V-3` **缺省形态**被改动 ⇒ RED；`V-4` 两个方向混用 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal064_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PENDING
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal064_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PENDING
---

# PLAN-20261012-437 — GOAL-20261012-064 cycle 1

## 背景

`GOAL-20261012-064`（MAINLINE 程序表**序 32**，轴 = 质量）。**实测起点**：
A 声明 `contradictions=['m-b']` + `supersedes=['m-b']`，随后 **m-b 被删** ⇒ 读面**照旧披露**
那两个 id、**没有任何悬空标记**，`terminal` 甚至报 **`CURRENT`**；而**写面**对未知 id 是
**拒绝提交**的（序 22）⇒ **写面严、读面静默**的不对称；序 21 的 `OUT_OF_VIEW` 是同一纪律的先例。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（零命中 + 实跑 + 写面对照 + 先例）（WP-1） | `scratch/probe-dangling-reference.py` |
| EC-02 | 悬空可读（两方向各自点名；缺省逐字不变；跨范围不猜）（WP-2） | `pytest tests/application tests/domain -q` |
| EC-03 | 两读面同源 + 既有键逐字不变 + 快照同轮（WP-3） | `pytest tests/api tests/adapters tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：悬空判定（扫同批）+ 两方向各自点名 + 跨范围不猜。
3. **WP-3**：两读面同源披露（另键）+ 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：悬空判定；EC-03 回填：读面键 + 快照）
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：（EC-02 回填：纯附加披露 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：悬空引用可读 + 两方向分开 + 四向反证。 |
