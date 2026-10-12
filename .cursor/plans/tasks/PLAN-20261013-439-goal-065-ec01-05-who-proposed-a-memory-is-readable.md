---
id: PLAN-20261013-439
slug: goal-065-ec01-05-who-proposed-a-memory-is-readable
title: GOAL-20261012-065 cycle 1（EC-01…EC-05）：作者面落 canonical + 两读面同源 + 两向反证
status: DONE
created_at: 2026-10-13
updated_at: 2026-10-13
latest_recheck: .cursor/plans/rechecks/RECHECK-20261013-440-goal-065-ec01-04-who-proposed-a-memory-is-readable.md
memory_entries: []
parent_goal: GOAL-20261012-065
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-065 的 **EC-01…EC-05**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只让**提议者**在 canonical 有位并在**两个读面**读得出
    （复用提案面既有 `proposed_by`，**不**新造第二个作者字段）；`provenance`（来源）的既有语义
    与两个内部调用点**一字不动**；**不**按作者筛选 / **不**做作者鉴权 / **不**做内容级语义比较；
    缺省形态**逐字不变**（未声明作者 ⇒ `None`）；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**谁提议的这条记忆读得出来**：① 勘察定稿（字段逐个 + 零命中 + 实跑 + 来源语义，EC-01）→
    ② 作者面落 canonical（记录 +1 可选字段；三适配器同契约；既有行读出 `None`）（EC-02）→
    ③ 两读面同源披露 + 既有键逐字不变 + 快照同轮（EC-03）→ ④ 两向反证 `W-1`…`W-4` 全红（EC-04）→
    ⑤ 自举收口（EC-05）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-memory-author.py` 逐条读出 —— ① 两处字段表逐个；
      ② 零命中复核（读面 + 两适配器）；③ 实跑（带作者的提案 ⇒ 记录无该属性、读面键集无它）；
      ④ `provenance` 与作者是两件事。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-memory-author.py`；
      GOAL 的「事实层结论」表逐行与实测对齐。
    status: PASS
  - id: WP-2
    criterion: >-
      **作者面落 canonical（EC-02）**：`MemoryRecord` +1 **可选**字段（缺省 `None`）；
      `commit` 把提案的 `proposed_by` **原样带进**；**三个适配器同契约**（SQLite 加法式列 +
      PG 迁移只加列 + Fake）；既有行（未声明）读回 `None`（**不猜**）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters tests/postgres -q`
      ⇒ 全绿 + 新用例（三适配器往返 / 既有行 `None` / 两声明面同源）。
    status: PASS
  - id: WP-3
    criterion: >-
      **两个读面同源披露（EC-03）**：编排面与 HTTP 读面**都**披露作者面（同一份 canonical 事实）；
      **既有键逐字不变**；动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`
      （+ `apps/web/src/api/types.ts` 若本轮触及）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 既有键逐字不变 / 快照含新键）。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`W-1` 记录侧字段被摘掉 ⇒ RED；`W-2` 适配器不带该列 ⇒ RED；
      `W-3` 缺省形态被改动（未声明被伪造）⇒ RED；`W-4` 读面披露被摘掉 ⇒ RED。基线门 GREEN；
      复原用二进制读写 + raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal065_press.py` ⇒ 全 `RED` +
      `sha 复原一致=True` + `BASELINE…: GREEN`。
    status: PASS
  - id: WP-5
    criterion: >-
      **自举收口（EC-05）**：收口验证器 + 断言集进树（`IN_SCOPE` 纯收紧 + 射程清单）；
      两树复检 `TWO-TREE PASS` + 判词归档（二进制写盘 / `CR=0`）；as-is m0 **23/23**
      （记录写完之后）；治理 + 宪章判据绿；CI 台账逐提交。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal065_closeout.py` ⇒ 全 `PASS`；
      两树 `TWO-TREE PASS`；m0 终局行 `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261013-439 — GOAL-20261012-065 cycle 1

## 背景

`GOAL-20261012-065`（MAINLINE 程序表**序 33**，轴 = 质量）。**实测起点**：
`MemoryWriteProposal` **有** `proposed_by`，而 `MemoryRecord` **没有该字段**（两次
`dataclasses.fields` 对照 + `hasattr` 复核）⇒ **实跑**：带作者的提案提交 ⇒ 记录无作者面、
编排读面 20 键里也没有它 ⇒ 「这条记忆是谁提的」在 canonical **无从可查**；
读面与两个适配器对 `proposed_by` **零命中**。

## 验收条件

| EC | 判据 | 证据 |
| --- | --- | --- |
| EC-01 | 四段读数（字段逐个 + 零命中 + 实跑 + 来源语义）（WP-1） | `scratch/probe-memory-author.py` |
| EC-02 | 作者面落 canonical + 三适配器同契约（既有行 `None`）（WP-2） | `pytest tests/domain tests/adapters tests/postgres -q` |
| EC-03 | 两读面同源 + 既有键逐字不变 + 快照同轮（WP-3） | `pytest tests/api tests/adapters tests/contracts -q` |
| EC-04 | 四向反证全红 + 基线门 + `sha256` 复原（WP-4） | 归档判词（`CR=0`） |
| EC-05 | 自举收口（WP-5） | 验证器全 `PASS` + 两树 + m0 23/23 |

## 实施清单

1. **WP-1**：定稿探针（只读；四段读数）。
2. **WP-2**：记录侧 +1 可选字段；`commit` 带进；三适配器同契约（迁移只加列）。
3. **WP-3**：两读面同源披露 + 快照同轮。
4. **WP-4**：按压脚本（四条）+ 基线门 + 归档。
5. **WP-5**：收口验证器 + 断言集 + 两树 + m0 + 治理 + 台账。

## 证据

（逐 WP 回填：命令 + 读数 + commit。）

## 影响报告

- **Domain / API / schema 变化**：（EC-02 回填：记录 +1 可选字段 + 迁移；EC-03 回填：读面 + 快照）
- **安全 / 凭据变化**：无。作者面是**声明**，**不是** ACL。
- **兼容性 / 迁移风险**：（EC-02 回填：只加列 + 可选字段 ⇒ 既有数据逐字不变）
- **上游版本影响**：无。
- **下一项任务**：按 EC 顺序推进。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-13 | IN_PROGRESS | cycle 1 建档：作者面落 canonical + 两读面同源 + 四向反证。 |
| 2026-10-13 | DONE | cycle 1 收口：WP-1…WP-5 全 PASS（独立复检 `RECHECK-20261013-440` = PASS_WITH_WARNINGS）。**交付**：`MemoryRecord.proposed_by`（可选）+ `commit` 带进 + 三适配器同契约（迁移 `027`）+ 两读面同源披露 + 快照同轮；判据 11 + PG 1 例；四向反证全红 + 归档（`CR=0`）。 |
