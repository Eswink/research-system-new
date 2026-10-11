---
id: PLAN-20261011-413
slug: goal-053-ec01-04-the-current-version-is-decidable
title: GOAL-20261011-053 cycle 1（EC-01…EC-04）：链式取代的「当前版本」可判定 —— 终点进载荷 + 两处同源 + 四向反证
status: DONE
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: .cursor/plans/rechecks/RECHECK-20261011-414-goal-053-ec01-04-the-current-version-is-decidable.md
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
    status: PASS
  - id: WP-2
    criterion: >-
      **链的终点成为可判定事实（EC-02）**：应用层纯函数给出**终点**与**形态**
      （无后继 / 有终点 / 环 / 自指，四态**互不混用**且都**点名**）；两个读面**逐条披露**；
      **既有 13 键一个不改名、不改语义**；**缺省形态逐字不变**（无取代链接的记录
      ⇒ 新增键的取值形态与既有约定一致）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/api -q` ⇒ 全绿
      + 新用例（链式终点 / 无后继点名 / 环点名 / 跨范围点名 / 既有键逐字不变）。
    status: PASS
  - id: WP-3
    criterion: >-
      **同源与一致（EC-03）**：HTTP 读面**不得** import 适配器（`.importlinter.api`）⇒
      共用判定落**应用层**；两处取值**同一批纯函数**（**不**各写一套）；**互指一致**由判据钉住；
      **OpenAPI 快照同轮重生成并提交**（动 DTO ⇒ 必须）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts tests/architecture -q`
      ⇒ 全绿 + 新用例（两处同值 / 复用同一助手）；`tests/architecture` 判分层契约。
    status: PASS
  - id: WP-4
    criterion: >-
      **两向反证（EC-04）**：`scratch/goal053_press.py` 逐条按压 —— `P-1` 终点**算错**（取直接
      后继）⇒ RED；`P-2` **退回直接链接**（不披露终点）⇒ RED；`P-3` **既有键改名** ⇒ RED；
      `P-4` 链上有**环却静默** ⇒ RED。**基线门**：未按压必须 GREEN（否则非 0 退出）。
      **二进制读写**复原 + raw `sha256` 逐字节一致；归档**二进制写盘**（`CR=0`）。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal053_press.py` ⇒ `all_red_and_restored=True`
      + 基线 GREEN；归档 `.cursor/plans/goals/evidence/GOAL-20261011-053-press-two-way.txt`。
    status: PASS
---

# PLAN-20261011-413 — GOAL-20261011-053 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-053`（MAINLINE 程序表**序 21**）的 **EC-01…EC-04**。

## 验收条件

| WP | 主题 | 状态 |
| --- | --- | --- |
| WP-1 | 勘察定稿（真实读面实测 + 反证无字段可答） | PASS |
| WP-2 | 链的终点进载荷（四态点名；既有 13 键逐字不变） | PASS |
| WP-3 | 两处同源同值 + 快照同轮 + 分层契约绿 | PASS |
| WP-4 | 四向反证 `P-1`…`P-4` + 基线门 + 二进制复原 | PASS |

## 实施清单

- [x] WP-1 勘察定稿：真实读面实测 + 逐条反证（只读，零改动）
- [x] WP-2 应用层纯函数（终点 / 无后继 / 环 / **跨范围**四态）+ 两个读面逐条披露 + 新用例
- [x] WP-3 HTTP 读面接应用层同一批纯函数 + OpenAPI 快照同轮 + 两处同值判据
- [x] WP-4 反证脚本（**带基线门**）+ 四向按压 + 归档进树

## 证据

| 门 | 读数 |
| --- | --- |
| 定向套件 | `tests/api tests/contracts` **1140 passed, 76 skipped**；`tests/architecture` **287 passed**（分层契约 `2 kept, 0 broken`）|
| 四向反证 | **基线 GREEN**（18 passed）+ `P-1`…`P-4` **全 RED** + 四条 `sha 复原一致=True`；归档 **747 B / 15 行 / `CR=0`**（`sha256 e33739554f9dca42…`）|
| 既有键逐字不变 | 新用例**逐条**断言 `superseded_by == ["mem-b"]` / `supersedes == ["mem-b"]`（仍是**直接**链接）；`+12 / -0` 的快照纯附加 |
| 四道门 | `ruff` / `format` / **全量 mypy（1184 files Success）** / 规模门（抽出 4 个助手）全绿 |
| 新用例 | `tests/api/test_memory_chain_end.py` **5 passed**（链终点 / 无后继 / 环 / 跨范围 / HTTP 同值）|

## 影响报告

- **Domain / API / schema 变化**：**HTTP 读面 +2 字段**（`terminal_state` / `terminal_ids`）与
  **编排读面 +1 键**（`terminal{state,ids}`）—— 皆**纯附加**（既有键逐字不变）；
  OpenAPI 快照**同轮**重生成（`+12 / -0`）。**Domain 零改动**（`supersedes` 早已声明）。
- **安全 / 凭据变化**：无（纯读面事实；`terminal_versions` 是**只读**纯函数，不查 store）。
- **兼容性 / 迁移风险**：无迁移（不新增列、不改写入语义）。**既有读者**：键**只增不减** ⇒
  不破坏；`OUT_OF_VIEW` 是**新取值**，旧读者若按 `CURRENT` 判「是当前版本」需知悉新态
  （已写进本 PLAN 与 GOAL 的 W-2）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本轮的可复用做法**已写进 GOAL-053 的 frontmatter §8**（「判关系不判位置」的修法要复查是否开口子；
反证脚本带基线门）—— 属该 GOAL 的边界，**未**另沉淀条目。**两条本轮新学到的**留在此处备查
（不升格为跨仓规则，因为它们是**设计被实测推翻**的两个具体案例）：
① **不可达分支 = 恒假支**：「后继 id 不在批内」看似该有的防御，实测**不可能发生**
   （后继全部来自批内）⇒ 写进判据就是**永不响**的空判据（承序 19/20 的同一形态）。
② **图算法的环判据不能复用「见过的集合」**：BFS 会把手性菱形误报成环 ⇒ 用 **DFS 三色**，
   并按「回到**当前路径上**的 id」判环。

## EC-05 收口轮（同 PLAN 内追加；收口面 `tools/verify_goal053_closeout.py`）

| 项 | 读数 |
| --- | --- |
| 收口验证器 | **64 判词 / 0 FAIL**；标准断言集**一行未重写** |
| 两树复检 | **`TWO-TREE PASS`**（两路 **64 判词** / `sha256` 相同 `d3bcd99d6fa0d682…`）|
| 判词归档 | 两份各 **2383 B / 64 行 / `CR=0` / 0 FAIL**（二进制写盘）|
| 两处射程 | `IN_SCOPE` **+2 行**；`_VERIFIERS` **+1 行**（下界 22 不变）—— 均**纯收紧** |
| `R26-*` 终态 | 六条**逐条明写**（初版只写区间 `R26-*` ⇒ 判据判红 ⇒ 已按纪律补齐）|
| **as-is m0** | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` **24** / `FAILED [` **0** / **5619 passed, 21 skipped** / `EXIT=0`；**独占**、仓库 `.venv`、不接管道、**在全部记录写完之后**）；日志 `scratch/m0-goal053-ec05.log` |

> **m0 条数 = 23**（终局行逐字）；`PASS [` **24** = 23 + `release-assets-immutable`（在计数之外）。
> **passed 读数差（GOAL-052 收口轮 `5613` → 本轮 `5619`，+6）逐条归因**：
> ① 新用例 **5 条**（`tests/api/test_memory_chain_end.py`：链终点 / 无后继 / 环 / 跨范围 / HTTP 同值）；
> ② 新增文件进入规模门的**参数化面**（`PRODUCT_ROOTS` 含 `tests`，每个 `.py` 一个用例）（**+1**）。
> **无**其他计数来源。

### 收口轮的两处既有断言修正（如实登记）

`goal045` / `goal050` 各一条**只认字典字面量写法**的断言被本轮的**字段分组**改动打成**假红**
（`reason` / `supersedes` / `superseded_by` 搬进下标赋值）。两条均改为 **AST 判关系**
（两种写法都认），**两向实测**：真树绿 / 删掉赋值红 / 空源码红 / 合成旧写法绿。
**无一处收窄受判面**，**未**删任何断言。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | cycle 1 建档：勘察定稿（真实读面实测链式取代）+ 终点进载荷 + 两处同源 + 四向反证。 |
| 2026-10-11 | DONE | EC-01…EC-04 全 PASS + EC-05 收口（验证器 64 判词 / 两树 `TWO-TREE PASS` / 归档定格 / m0 23/23 / 治理 + 宪章判据绿）。`RECHECK-20261011-414` 独立复检。 |

