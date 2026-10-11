---
id: PLAN-20261012-423
slug: goal-058-ec01-04-a-resolved-conflict-is-decidable
title: GOAL-20261012-058 cycle 1（EC-01…EC-04）：消解可记录 + 读面披露 + 四向反证
status: IN_PROGRESS
created_at: 2026-10-12
updated_at: 2026-10-12
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261012-058
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261012-058 的 **EC-01…EC-04**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只新增**消解记载**（写路径 + 读面披露 + 判据）；
    声明的既有语义（序 22 已收口的判据）**一字不动**；**不**做自动消解 / **不**做内容级检测 /
    **不**删声明 / **不**走审批；缺省形态**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**被消解的冲突读得出来**：① 勘察定稿（消解面零命中 + 改声明路径零命中 + 五态无误 +
    三个写路径都不碰冲突维，EC-01）→ ② 消解可记录（哪一对 + 由谁 + 何时；四种坏形态点名；
    **声明一字不动**）（EC-02）→ ③ 读面披露（同源；**未消解逐字仍是 `CONFLICTED`**）+ 快照同轮（EC-03）→
    ④ 四向反证 `U-1`…`U-4`（未消解被判已消解 / 消解后被判未消解 / 声明被删除 / 未知对被接受）全红（EC-04）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-conflict-resolution.py` 逐条读出五组 ——
      ① 消解面**全零命中**（五组标识符）；② **改既有声明的路径全零命中**（四组标识符）；
      ③ 五态枚举**逐个读出**（无「已消解」）；④ `lifecycle.py` 的三个写路径**逐个读出**；
      ⑤ 声明语义已收口（本轮不动）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-conflict-resolution.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: WP-2
    criterion: >-
      **消解可记录（EC-02）**：新增一条**消解记载**（**哪一对**两个 id + **由谁** + **何时**）；
      **点名拒绝**坏形态：未知冲突对（不在该记录 `contradictions` 里）/ 自己与自己 / 空 id /
      未声明的对；**`contradictions` 一字不动**（历史事实保留）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/application -q` ⇒ 全绿
      + 新用例（消解可记 / 四种坏形态点名 / 声明逐字不变）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **读面披露（EC-03）**：两个读面（编排消费面 + HTTP 读面）**同源**披露「已消解」与
      **消解者 / 时点**；**未消解 ⇒ 逐字仍是 `CONFLICTED`**（既有键逐字不变）；
      动 DTO ⇒ **同轮**重生成并提交 `docs/api/openapi.m13.json`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/adapters tests/contracts -q`
      ⇒ 全绿 + 新用例（两处同值 / 未消解逐字不变 / 快照含新字段）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`U-1` **未消解被判已消解** ⇒ RED；`U-2` **消解后被判未消解** ⇒ RED；
      `U-3` **声明被删除 / 改写** ⇒ RED；`U-4` **未知冲突对被接受** ⇒ RED。
      **基线门**：未按压必须 GREEN（否则非 0 退出）。**二进制读写**复原 + raw `sha256` 一致；
      归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal058_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261012-058-press-two-way.txt`。
    status: PENDING
---

# PLAN-20261012-423 — GOAL-20261012-058 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261012-058`（MAINLINE 程序表**序 26**，**质量轴**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（消解面零命中 + 改声明路径零命中 + 五态无误 + 三个写路径） | PENDING |
| WP-2 | 消解可记录（哪一对 + 由谁 + 何时；四坏形态点名；声明不动） | PENDING |
| WP-3 | 读面披露（同源；未消解逐字不变）+ 快照同轮 | PENDING |
| WP-4 | 四向反证 `U-1`…`U-4` + 基线门 + 二进制复原 | PENDING |

## 实施清单

- [ ] WP-1 勘察定稿：五组读数（只读，零改动）
- [ ] WP-2 消解记载 + 四种坏形态点名 + 新用例
- [ ] WP-3 两个读面同源披露 + 快照同轮 + 新用例
- [ ] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | （待本轮实测回填） |
| 四向反证 | （待本轮实测回填） |
| 落库形态（域 + 两根 + DTO + 快照的连带面） | （待本轮实测回填） |
| 声明不受影响（序 22 的既有判据） | （待本轮实测回填） |

## 影响报告

- **Domain / API / schema 变化**：（待本轮实测回填 —— `D-5` 决定落库形态）
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：（待本轮实测回填）
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-12 | IN_PROGRESS | cycle 1 建档：勘察（消解面零命中）+ 消解记载 + 读面披露 + 四向反证。 |
