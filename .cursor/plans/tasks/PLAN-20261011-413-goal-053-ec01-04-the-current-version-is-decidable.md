---
id: PLAN-20261011-413
slug: goal-053-ec01-04-the-current-version-is-decidable
title: GOAL-20261011-053 cycle 1（EC-01…EC-04）：链式取代的「当前版本」可判定 —— 终点进载荷 + 两处同源 + 四向反证
status: IN_PROGRESS
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261011-053
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-053 的 **EC-01…EC-04**。授权原文见该 GOAL 的 `authorization.ref`。
    **本 PLAN 专属边界**：只动**读面**（编排消费面 `adapters/canonical/memory_read.py` +
    HTTP 读面 `services/api/{dto,routers}/memory.py`）+ **应用层共用纯函数** + 判据；
    **不**改取代的**写入**语义（`supersede_memory` / gate 一字不动）；
    **不**新建存储 / 第二套链接表；**不**做自动消解；**不**做通用图算法；
    任一既有键（`supersedes` / `superseded_by`）**逐字不变**；
    新判据**两向实测**、反证脚本**带基线门**；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让链式取代的**当前版本**在读面上**可判定**：① 勘察定稿（真实读面实测，EC-01）→
    ② 读面披露**链的终点**（环 / 自指 / 无后继均**点名**；既有 13 键逐字不变）（EC-02）→
    ③ 两个读面**同源同值** + OpenAPI 快照同轮（EC-03）→ ④ 四向反证 `P-1`…`P-4`
    （终点算错 / 退回直接链接 / 既有键被改 / 环却静默）全红 + 基线门（EC-04）。
exit_criteria:
  - id: WP-1
    criterion: >-
      **勘察定稿（EC-01）**：`scratch/probe-chain-supersede.py` 用**真实读面**
      （`_memory_row`）跑 A ⊂ B ⊂ C，逐条打印 `supersedes` / `superseded_by` /
      `disposition` / `reason`；**逐条反证**「载荷里没有字段能回答当前版本是谁」；
      `git diff --numstat` ⇒ **零改动**（本 WP 只读）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/probe-chain-supersede.py`；
      GOAL 的「事实层结论」表逐行与实测对齐（不符则登记差异，以实测为准）。
    status: PENDING
  - id: WP-2
    criterion: >-
      **链的终点成为可判定事实（EC-02）**：应用层纯函数给出**终点**与**形态**
      （无后继 / 有终点 / 环 / 自指，四态**互不混用**且都**点名**）；两个读面**逐条披露**；
      **既有 13 键一个不改名、不改语义**；**缺省形态逐字不变**（无取代链接的记录
      ⇒ 新增键的取值形态与既有约定一致）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q` ⇒ 全绿
      + 新用例（链式终点 / 无后继点名 / 环点名 / 自指点名 / 既有键逐字不变）。
    status: PENDING
  - id: WP-3
    criterion: >-
      **同源与一致（EC-03）**：HTTP 读面**不得** import 适配器（`.importlinter.api`）⇒
      共用判定落**应用层**；两处取值**同一批纯函数**（**不**各写一套）；**互指一致**由判据钉住；
      **OpenAPI 快照同轮重生成并提交**（动 DTO ⇒ 必须）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/architecture -q`
      ⇒ 全绿 + 新用例（两处同值 / 复用同一助手）；`tests/architecture` 判分层契约。
    status: PENDING
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`scratch/goal053_press.py` 逐条按压 —— `P-1` 终点**算错**（取直接
      后继）⇒ RED；`P-2` **退回直接链接**（不披露终点）⇒ RED；`P-3` **既有键改名** ⇒ RED；
      `P-4` 链上有**环却静默** ⇒ RED。**基线门**：未按压必须 GREEN（否则非 0 退出）。
      **二进制读写**复原 + raw `sha256` 逐字节一致；归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal053_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-053-press-two-way.txt`。
    status: PENDING
---

# PLAN-20261011-413 — GOAL-20261011-053 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-053`（MAINLINE 程序表**序 21**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（真实读面实测 + 反证无字段可答） | PENDING |
| WP-2 | 链的终点进载荷（四态点名；既有 13 键逐字不变） | PENDING |
| WP-3 | 两处同源同值 + 快照同轮 + 分层契约绿 | PENDING |
| WP-4 | 四向反证 `P-1`…`P-4` + 基线门 + 二进制复原 | PENDING |

## 实施清单

- [ ] WP-1 勘察定稿：真实读面实测 + 逐条反证（只读，零改动）
- [ ] WP-2 应用层纯函数（终点 / 无后继 / 环 / 自指四态）+ 两个读面逐条披露 + 新用例
- [ ] WP-3 HTTP 读面接应用层同一批纯函数 + OpenAPI 快照同轮 + 两处同值判据
- [ ] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | （待本轮实测回填） |
| 四向反证 | （待本轮实测回填） |
| 既有键逐字不变 | （待本轮实测回填） |

## 影响报告

- **Domain / API / schema 变化**：（待本轮实测回填）
- **安全 / 凭据变化**：无。**兼容性 / 迁移风险**：无。**上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

（待本轮结束时判：若沉淀，写入 `memory_entries`；若无，改写本节为「无可复用事实」并给理由。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：勘察定稿（真实读面实测链式取代）+ 终点进载荷 + 两处同源 + 四向反证。 |

