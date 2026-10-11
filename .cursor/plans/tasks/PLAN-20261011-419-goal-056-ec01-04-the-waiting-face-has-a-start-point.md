---
id: PLAN-20261011-419
slug: goal-056-ec01-04-the-waiting-face-has-a-start-point
title: GOAL-20261011-056 cycle 1（EC-01…EC-04）：等待面有始点 + 超期可判定（只点名）+ 四向反证
status: DONE
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: .cursor/plans/rechecks/RECHECK-20261011-420-goal-056-ec01-04-the-waiting-face-has-a-start-point.md
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
    status: PASS
  - id: WP-2
    criterion: >-
      **始点可读（EC-02）**：等待面能回答「何时开始等」—— 时点由**调用方给**（不读挂钟）；
      同一份记录 + 同一时点 ⇒ 判定**必相同**；**缺省形态逐字不变**（不给时点 ⇒ 不报始点）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/adapters -q` ⇒ 全绿
      + 新用例（始点可读 / 同一时点同结论 / 不给时点不猜）—— **8 passed**；
      并在**产品路径**接线（推进路由给两个时点；取不到 ⇒ 传 `None` ⇒ 不报时长）。
    status: PASS
  - id: WP-3
    criterion: >-
      **超期可判定（EC-03）**：超过**声明的界** ⇒ **点名**（不自动放行/拒绝）；
      **未声明界** ⇒ 不催不报（逐字不变）；**未给时点** ⇒ **点名**「无法判定时长」；
      界必须是**正整数**（零/负 ⇒ 点名拒绝）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration tests/domain -q`
      ⇒ 全绿 + 新用例（超期点名 / 未声明不催 / 未给时点点名 / 坏界点名）—— **8 passed**。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`S-1` 始点**读不出** ⇒ RED；`S-2` **超期不点名** ⇒ RED；
      `S-3` **未声明形态被改动** ⇒ RED；`S-4` **坏时点被接受** ⇒ RED。
      **基线门**：未按压必须 GREEN（否则非 0 退出）。**二进制读写**复原 + raw `sha256` 一致；
      归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal056_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-056-press-two-way.txt`
      （**660 B / 15 行 / `CR=0`** / `sha256 451f0848eb2f9a13…`）。
    status: PASS
---

# PLAN-20261011-419 — GOAL-20261011-056 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-056`（MAINLINE 程序表**序 24**，**连续性轴**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（时限面零命中 + 字段逐条 + 点名句引文） | PASS |
| WP-2 | 始点可读（不读挂钟；缺省逐字不变） | PASS |
| WP-3 | 超期可判定（有界只点名；未声明/未给时点都不猜） | PASS |
| WP-4 | 四向反证 `S-1`…`S-4` + 基线门 + 二进制复原 | PASS |

## 实施清单

- [x] WP-1 勘察定稿：四组读数（只读，零改动）
- [x] WP-2 始点：时点由调用方给 + 等待面披露 + 新用例
- [x] WP-3 超期：有界判定 + **只点名** + 坏界拒绝 + 新用例
- [x] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | 新用例 **8 passed**；`tests/application/run_orchestration` **204 passed**；`tests/{application,domain,api}` **1945 passed, 5 skipped**；`tests/architecture` **1486 passed**；四道门绿（**全量 mypy 1189 files**）|
| 四向反证 | **基线 GREEN**（8 passed）+ `S-1`…`S-4` **全 RED** + 四条 `sha 复原一致=True`；归档 **660 B / `CR=0`** |
| 落库形态 | **域 +1 字段**（`gate_nudge_after_seconds`，缺省 `None` ⇒ 逐字不变；**与三种闸门声明正交 ⇒ 不参与互斥**）；**无迁移需求**（始点复用既有 `ResearchRun.updated_at` —— `D-6` 的结论）|
| 收口门 | 收口验证器 **61 判词 / 0 FAIL**；两树 **`TWO-TREE PASS`**（`sha256 ebc0ee1e…`）；**as-is m0 待实测回填** |

## 影响报告

- **Domain / API / schema 变化**：**域 +1 字段**（`gate_nudge_after_seconds`，可选，缺省 `None`）；
  **落库零改动**（`D-6` 的结论：始点复用既有 `ResearchRun.updated_at` ⇒ **不需要新列 / 迁移**）；
  **端口 / 应用层参数面**：`GateClock` / `GateInputs` 两个参数对象 + 抽出
  `program_gate_evaluation.py`（语义未动）；**HTTP 路由接线**（推进时传两个时点）
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：**低** —— 新字段缺省 `None`（既有行读到 `None`）；
  两个参数对象**兼容裸元组**（既有调用点逐字不变）；**无迁移**；判词在**不给时点时逐字不变**
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本轮的做法已写进 GOAL-056 的授权面（`forbidden` / `escalation_triggers`），属该 GOAL 的边界。
**三条本轮新学到的**留在此处备查：
① **`max-args = 5` 的解法是参数对象**（两个时点合成 `GateClock`，再与 `verdicts` 合成
   `GateInputs`），且**要兼容旧形态**（裸元组 ⇒ 视为其中一个字段）才不会打断既有调用点。
② **规模门会两度触顶**（文件 450 / 函数 50 是**两道独立的门**）：抽出模块后可能**又**撞函数门
   ⇒ 预留「再抽一层」的余地；两次都选**抽函数**而**不是**放宽门禁。
③ **跨模块搬运 `dataclass` 时类型不同形** ⇒ mypy 会在返回点判负；**显式转换**比让它接受
   两个不同 `dataclass` 更清楚（也避免 `Any` 化）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：勘察（时限面零命中）+ 始点 + 超期点名 + 四向反证。 |
| 2026-10-11 | DONE | WP-1…WP-4 全 PASS + 产品路径接线 + EC-05 收口（验证器 61 判词 / 两树 `TWO-TREE PASS` / 归档定格 / 治理 + 宪章判据绿）。`RECHECK-20261011-420` 独立复检。 |
