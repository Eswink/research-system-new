---
id: PLAN-20261011-419
slug: goal-056-ec01-04-the-waiting-face-has-a-start-point
title: GOAL-20261011-056 cycle 1（EC-01…EC-04）：等待面有始点 + 超期可判定（只点名）+ 四向反证
status: IN_PROGRESS
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261011-056
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-056 的 **EC-01…EC-04**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只动**审批记录的时间侧**（域/端口字段或冻结值算法）+
    **等待面点名句** + 判据；**不**做自动放行/拒绝；**不**做通知外发 / 升级链；
    **不**读挂钟（时点由调用方给）；**不**改序 14/16/23 三条闸门声明的语义（只加**时间侧**）；
    缺省形态**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让等待面**有始点、可催办（有界，只点名）**：① 勘察定稿（时限面零命中 + 字段逐条 + 引文，EC-01）→
    ② 始点可读（时点由调用方给，不读挂钟；缺省逐字不变）（EC-02）→
    ③ 超期可判定（有界只点名；未声明/未给时点都不猜；坏界点名拒绝）（EC-03）→
    ④ 四向反证 `S-1`…`S-4`（始点读不出 / 超期不点名 / 未声明被改动 / 坏时点被接受）全红（EC-04）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-waiting-clock.py` 逐条读出四组 ——
      ① 时限面**零命中**的检索证据；② `ApprovalRecord` 的字段**逐个读出**（无时间字段）；
      ③ 等待面三处点名句**逐条引文**；④ 三种闸门声明语义已定（本轮不改）。
      `git diff --numstat` ⇒ **零改动**（本 WP 只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-waiting-clock.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: WP-2
    criterion: >-
      **始点可读（EC-02）**：等待面能回答「何时开始等」—— 时点由**调用方给**（不读挂钟）；
      同一份记录 + 同一时点 ⇒ 判定**必相同**；**缺省形态逐字不变**（不给时点 ⇒ 不报始点）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters -q` ⇒ 全绿
      + 新用例（始点可读 / 同一时点同结论 / 不给时点不猜）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **超期可判定（EC-03）**：超过**声明的界** ⇒ **点名**（不自动放行/拒绝）；
      **未声明界** ⇒ 不催不报（逐字不变）；**未给时点** ⇒ **点名**「无法判定时长」；
      界必须是**正整数**（零/负 ⇒ 点名拒绝）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration tests/domain -q`
      ⇒ 全绿 + 新用例（超期点名 / 未声明不催 / 未给时点点名 / 坏界点名）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`S-1` 始点**读不出** ⇒ RED；`S-2` **超期不点名** ⇒ RED；
      `S-3` **未声明形态被改动** ⇒ RED；`S-4` **坏时点被接受** ⇒ RED。
      **基线门**：未按压必须 GREEN（否则非 0 退出）。**二进制读写**复原 + raw `sha256` 一致；
      归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal056_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-056-press-two-way.txt`。
    status: PENDING
---

# PLAN-20261011-419 — GOAL-20261011-056 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-056`（MAINLINE 程序表**序 24**，**连续性轴**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（时限面零命中 + 字段逐条 + 点名句引文） | PENDING |
| WP-2 | 始点可读（不读挂钟；缺省逐字不变） | PENDING |
| WP-3 | 超期可判定（有界只点名；未声明/未给时点都不猜） | PENDING |
| WP-4 | 四向反证 `S-1`…`S-4` + 基线门 + 二进制复原 | PENDING |

## 实施清单

- [ ] WP-1 勘察定稿：四组读数（只读，零改动）
- [ ] WP-2 始点：时点由调用方给 + 等待面披露 + 新用例
- [ ] WP-3 超期：有界判定 + **只点名** + 坏界拒绝 + 新用例
- [ ] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | （待本轮实测回填） |
| 四向反证 | （待本轮实测回填） |
| 落库形态（域/端口 + 两根 + DTO + 快照的连带面） | （待本轮实测回填） |

## 影响报告

- **Domain / API / schema 变化**：（待本轮实测回填 —— `D-6` 决定是落新列还是用既有冻结值）
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：（待本轮实测回填）
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：勘察（时限面零命中）+ 始点 + 超期点名 + 四向反证。 |
