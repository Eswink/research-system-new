---
id: PLAN-20261011-415
slug: goal-054-ec01-04-a-conflict-declaration-passes-integrity-checks
title: GOAL-20261011-054 cycle 1（EC-01…EC-04）：冲突声明的被引 id 过完整性校验（与 `supersedes` 对齐）+ 四向反证
status: IN_PROGRESS
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261011-054
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-054 的 **EC-01…EC-04**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只动**记忆的 gate 校验**（`packages/application/memory/gate.py` 的
    `_contradiction_check`）+ 必要的读面点名形态 + 判据；
    **不**改 `supersedes` 的既有校验（那一侧是**基准**）；**不**新建存储 / 第二套门链阶段；
    **不**做自动消解（`CC-1`）/ **不**做内容级检测（`W-2` 另一半）；
    **不**给历史数据回溯校验；既有键**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**冲突声明的被引 id**与 `supersedes` **一样过完整性校验**：① 勘察定稿（三态实跑，EC-01）→
    ② gate 对齐（存在性 + **不得自指**；点名拒绝；`supersedes` 一字不动）（EC-02）→
    ③ 读面一致（`CONFLICTED` 形态逐字不变；悬空 / 自指不再可能进入；既有键逐字不变）（EC-03）→
    ④ 四向反证 `Q-1`…`Q-4`（悬空被接受 / 自指被接受 / 误伤正常 / `supersedes` 被放宽）全红（EC-04）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-conflict-integrity.py` 用**真实调用面**跑三态
      （悬空 / 自指 / 正常），逐条打印落库结果 + 读面 `disposition` / `reason`；
      校验面的**逐字引文 + 行号**；`rg` 反证「记忆面零检测实现」（命中逐条列名）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-conflict-integrity.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PASS
  - id: WP-2
    criterion: >-
      **gate 对齐（EC-02）**：`_contradiction_check` 里对 `contradictions` 加**存在性**校验
      （不存在 ⇒ **点名拒绝**，理由含该 id）与**自指**校验（被引 id == 提案自身 id ⇒ **点名拒绝**）；
      **正常声明照常通过**；**`supersedes` 的既有校验逐字不动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒ 全绿
      + 新用例（悬空拒绝 / 自指拒绝 / 正常通过 / `supersedes` 面逐字不变）—— **4 passed**。
    status: PASS
  - id: WP-3
    criterion: >-
      **读面一致（EC-03）**：`CONFLICTED` 的第五态与理由**逐字不变**；悬空 / 自指两种形态
      **不再可能进入**（由 gate 拒绝）；**既有键逐字不变**（编排面 13 键 + `terminal` /
      HTTP 面既有字段）；**不各写一套判定**（沿用应用层同一批纯函数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters -q` ⇒ 全绿
      + 新用例（既有键逐字不变 / 正常冲突仍 `CONFLICTED`）；**连带面**：
      `tests/`（除 e2e/postgres）**5100 passed, 114 skipped / 零 FAILED** ⇒ 既有测试数据
      **没有一条**被新校验拒掉（收紧 gate 的本 GOAL 特有风险面，逐条核对结论 = 无需收窄）。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`scratch/goal054_press.py` 逐条按压 —— `Q-1` 悬空**被接受** ⇒ RED；
      `Q-2` **自指**被接受 ⇒ RED；`Q-3` 校验**误伤正常声明** ⇒ RED；
      `Q-4` `supersedes` 的既有校验被**放宽** ⇒ RED。
      **基线门**：未按压必须 GREEN（否则非 0 退出）。**二进制读写**复原 + raw `sha256` 一致；
      归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal054_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-054-press-two-way.txt`
      （**732 B / 15 行 / `CR=0`** / `sha256 232ebbb5d135b65f…`）。
    status: PASS
---

# PLAN-20261011-415 — GOAL-20261011-054 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-054`（MAINLINE 程序表**序 22**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（三态实跑 + 校验面引文 + 零检测反证） | PASS |
| WP-2 | gate 对齐（存在性 + 不得自指；`supersedes` 一字不动） | PASS |
| WP-3 | 读面一致（`CONFLICTED` 逐字不变；既有键逐字不变） | PASS |
| WP-4 | 四向反证 `Q-1`…`Q-4` + 基线门 + 二进制复原 | PASS |

## 实施清单

- [x] WP-1 勘察定稿：三态实跑 + 逐条读数（只读，零改动）
- [x] WP-2 `_contradiction_check` 加两维校验 + 新用例（悬空 / 自指 / 正常 / `supersedes` 面）
- [x] WP-3 读面形态复核（既有键逐字不变 + 正常冲突仍 `CONFLICTED`）+ 受影响面同轮修
- [x] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | `tests/application/memory` **4 passed**（新）；`tests/api tests/adapters` **1207 passed, 7 skipped** |
| 四向反证 | **基线 GREEN**（4 passed）+ `Q-1`…`Q-4` **全 RED** + 四条 `sha 复原一致=True`；归档 **732 B / 15 行 / `CR=0`** |
| 收紧的**连带面** | `tests/`（除 e2e/postgres）**5100 passed, 114 skipped / 零 FAILED** ⇒ **既有数据无一条被拒** |
| 四道门 | `ruff` / `format` / **全量 mypy（1185 files Success）** / 规模门全绿 |

## 影响报告

- **Domain / API / schema 变化**：**零**（改的是**应用层**的 gate 校验；域上只校验非空字符串那条**未动**）。
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：**收紧的是新提案的校验**（历史记录**不**回溯）；
  连带面实测**零 FAILED** ⇒ 既有测试数据无一条被拒；调用方若此前提交过悬空 / 自指声明，
  **今后会被拒**（这是本轮要的形态，**点名**告知而不是静默接受）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本轮的做法（**引用完整性两侧对齐** + **收紧 gate 前先写死连带面的处置**）已写进 GOAL-054 的
授权面与 `escalation_triggers`，属该 GOAL 的边界，**未**另沉淀条目。
**一条本轮新学到的**留在此处备查：**探针必须打在产品路径上** —— 初版用适配器直写
（`store.commit`）测量，**绕过门链** ⇒ 把对照面读反；「直写」与「走门链」是**两个面**，
测量哪一面取决于问题问的是哪一面。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：三态勘察（悬空 / 自指 / 正常）+ gate 对齐 + 读面一致 + 四向反证。 |
| 2026-10-11 | DONE | WP-1…WP-4 全 PASS：门链两侧对齐（存在性 + 不得自指；`supersedes` 一字不动）+ 四向反证全红 + 连带面零 FAILED。EC-05 收口待做。 |
