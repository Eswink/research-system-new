---
id: PLAN-20261011-421
slug: goal-057-ec01-04-the-overdue-signal-has-an-exit
title: GOAL-20261011-057 cycle 1（EC-01…EC-04）：超期信号的可注入出口 + 静默缺省 + 只读纪律 + 四向反证
status: IN_PROGRESS
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261011-057
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-057 的 **EC-01…EC-04**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只新增**端口 + 静默缺省实现 + 调用方侧接线 + 判据**；
    **不**做真实外发 / **不**做重试·去重·投递保证 / **不**做升级链；**不**读挂钟；
    **端口调用不得进只读判定面**（序 12/14 起的既有判据钉住）；**只送摘要**（隐私 §10）；
    缺省形态**逐字不变**；新判据**两向实测**、反证脚本**带基线门**；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**超期信号有出口**：① 勘察定稿（出口面零命中 + 序 24 产物在树 + 同类 seam 先例逐条，EC-01）→
    ② 端口与静默缺省（形状照抄既有 sink 那一族；未注入 ⇒ 逐字不变；只收摘要）（EC-02）→
    ③ 接线与只读纪律（有副作用在**调用方那侧**；故障点名；组合根决定注入）（EC-03）→
    ④ 四向反证 `T-1`…`T-4`（缺省被改动 / 超期不送 / 故障被静默 / 只读面被塞写方法）全红（EC-04）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-nudge-exit.py` 逐条读出四组 —— ① 出口面**零命中**；
      ② 序 24 的产物**在树**；③ 同类 seam 的**形状**（端口的方法签名逐条）；
      ④ 它的**静默缺省**与**注入点**（逐行引文）。`git diff --numstat` ⇒ **零改动**（只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-nudge-exit.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: WP-2
    criterion: >-
      **端口与静默缺省（EC-02）**：新增出口端口（形状照抄既有 sink 那一族）+ **静默缺省**；
      **未注入 ⇒ 既有行为逐字不变**（不报错、不静默当成失败）；载荷**只收结构化摘要**
      （标识 / 计数 / 判词片段；**不**收内容原文 / 凭据）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application tests/domain -q` ⇒ 全绿
      + 新用例（缺省静默 / 摘要形状 / 不含内容字段）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **接线与只读纪律（EC-03）**：超期信号由**调用方那侧**交给端口（**不得**进只读判定面）；
      **端口故障点名**（不静默吞）；**组合根决定是否注入**（缺省不注入 ⇒ 逐字不变）；
      **序 24 的超期判定语义与三种闸门声明一字未动**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration tests/api -q`
      ⇒ 全绿 + 新用例（注入后收到 / 未注入静默 / 端口故障点名 / 判定面无写方法）。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`T-1` **缺省不送被改动** ⇒ RED；`T-2` **超期不送** ⇒ RED；
      `T-3` **端口故障被静默** ⇒ RED；`T-4` **只读判定面被塞进写方法** ⇒ RED。
      **基线门**：未按压必须 GREEN（否则非 0 退出）。**二进制读写**复原 + raw `sha256` 一致；
      归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal057_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-057-press-two-way.txt`。
    status: PENDING
---

# PLAN-20261011-421 — GOAL-20261011-057 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-057`（MAINLINE 程序表**序 25**，**连续性轴**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（出口面零命中 + 产物在树 + 同类 seam 先例逐条） | PENDING |
| WP-2 | 端口与静默缺省（形状照抄；只收摘要） | PENDING |
| WP-3 | 接线与只读纪律（有副作用在调用方侧；故障点名；组合根注入） | PENDING |
| WP-4 | 四向反证 `T-1`…`T-4` + 基线门 + 二进制复原 | PENDING |

## 实施清单

- [ ] WP-1 勘察定稿：四组读数（只读，零改动）
- [ ] WP-2 端口 + 静默缺省 + 摘要形状 + 新用例
- [ ] WP-3 调用方侧接线 + 故障点名 + 组合根注入 + 新用例
- [ ] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | （待本轮实测回填） |
| 四向反证 | （待本轮实测回填） |
| 只读判定面（序 12/14 起的既有判据） | （待本轮实测回填） |
| 隐私（载荷只含摘要） | （待本轮实测回填） |

## 影响报告

- **Domain / API / schema 变化**：（待本轮实测回填 —— 预计只新增端口 + 组合根装配）
- **安全 / 凭据变化**：无（端口只收结构化摘要；**不**外发、**不**收凭据）。
- **兼容性 / 迁移风险**：（待本轮实测回填 —— 缺省不注入 ⇒ 逐字不变）
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：勘察（出口面零命中）+ 端口/静默缺省 + 接线 + 四向反证。 |
