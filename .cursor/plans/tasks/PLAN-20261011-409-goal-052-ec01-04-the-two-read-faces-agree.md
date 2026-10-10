---
id: PLAN-20261011-409
slug: goal-052-ec01-04-the-two-read-faces-agree
title: GOAL-20261011-052 cycle 1（EC-01…EC-04）：HTTP 读面对齐编排面 —— 四样补齐 + 同源同值 + 四向反证
status: DONE
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: .cursor/plans/rechecks/RECHECK-20261011-410-goal-052-ec01-04-the-two-read-faces-agree.md
memory_entries: []
parent_goal: GOAL-20261011-052
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261011-052 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**边界**：**不**改既有键（只作**附加**）；**不**改**编排消费面**的载荷
    （那一侧是**基准**）；**不**两处各写一套判定（**复用**既有纯函数）；**不**新建第二套读面 /
    投影表；`validity` 的**时点语义逐字保持**（不给时点**不猜**）；**不**做 `DD-1`…`DD-3`；
    **新判据必须两向实测**（**不得恒假** —— 承序 19 的两处空判据）；动 DTO ⇒ **同轮**同步
    OpenAPI 快照；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让**两个读面在同一份事实上给出一致的可判定性**：① 勘察定稿（逐字段差集，读数见 GOAL 正文）→
    ② **HTTP 读面补齐四样** —— `contradictions`（声明逐条）/ `superseded_by`（**反向**链接）/
    `disposition`（五态之一）/ `reason`（逐字理由），且**既有 13 字段逐字不变**（新增是**附加**），
    `validity` 的时点语义**逐字保持**（EC-02）→ ③ **同源与一致** —— 三处判定
    （`disposition_of` / `_reason` / `_reverse_links`）**复用**既有纯函数，**不**在路由里重算；
    **两处对同一记录给同值**；**OpenAPI 快照同轮重生成并提交**（EC-03）→
    ④ **四向反证** `N-1`…`N-4`，**每条两向实测会响**（EC-04）→ ⑤ EC-05（自举收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（读数逐条）**：编排面 13 键逐字 / HTTP 面 13 字段逐字 / **差集四样** /
      `rg` 反证零命中 / **实跑**键集差 / 正向有反向无 / `validity` 时点语义 / 结论
      「可判定性不一致」+ **一致性无判据**（`rg` 零命中）。
    verify: >-
      GOAL 正文「事实层结论」的八条读数（`rg` 命令 + 实跑探针）。
    status: PASS
  - id: AC-2
    criterion: >-
      **HTTP 读面补齐四样（附加 + 既有键逐字不变）**：`MemoryRecordDto` 披露 `contradictions` /
      `superseded_by` / `disposition` / `reason`；**既有 13 字段一个不改名、不改语义**；
      `validity` 的时点语义**逐字保持**（只有显式给 `at` 的路由才填它）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api -q` ⇒ 全绿 + 新用例
      （四样都在场 / 既有键逐字不变 / 不给时点 `validity` 仍为 `None`）。
    status: PASS
  - id: AC-3
    criterion: >-
      **同源与一致**：三处判定**复用**既有纯函数（`disposition_of` / `_reason` / `_reverse_links`）
      —— **不**在路由里重写一套；**两处对同一记录给同值**（判据钉住互指一致）；
      **OpenAPI 快照同轮重生成并提交**（动 DTO ⇒ 必须）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q` ⇒ 全绿
      （含快照判据）+ 新用例（两处同值 / 复用同一助手）。
    status: PASS
  - id: AC-4
    criterion: >-
      **四向反证（真按压，每条两向实测会响）**：`N-1` 两处不一致 ⇒ **RED**；
      `N-2` HTTP 面凭空生造判定（不取既有纯函数）⇒ **RED**；`N-3` 既有键被改动 ⇒ **RED**；
      `N-4` 不给时点却填了 `validity`（**猜**）⇒ **RED**。复原用**二进制读写**且 raw `sha256`
      逐字节相同；判词归档进树（`CR=0`）；**每条按压必须实测判红**（不得恒假）。
    verify: >-
      `scratch/goal052-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261011-052-press-two-way.txt`。
    status: PASS
---

# PLAN-20261011-409 — GOAL-20261011-052 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261011-052`（MAINLINE 程序表**序 20**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（逐字段差集：缺 `contradictions` / `superseded_by` / `disposition` / `reason`） | PASS |
| AC-2 | HTTP 读面补齐四样（附加；既有 13 字段逐字不变；`validity` 时点语义保持） | PASS |
| AC-3 | 同源与一致（复用既有纯函数 + 两处同值 + 快照同轮同步） | PASS |
| AC-4 | 四向反证 N-1…N-4 全红（含**基线门**）+ 二进制复原一致 | PASS |

## 实施清单

- [x] WP-1 `MemoryRecordDto` **+4 字段**（`contradictions` / `superseded_by` / `disposition` / `reason`）
- [x] WP-2 `_record_dto` **+4 赋值** —— 判定**复用** `disposition_of` / `_reason`（**同源**）
- [x] WP-3 反向链接：路由按**同一批记录**扫一次（复用 `_reverse_links`），传入 `_record_dto`
- [x] WP-4 **OpenAPI 快照同轮重生成并提交**
- [x] WP-5 判据：HTTP 四样在场 / 既有键逐字不变 / **两处同值** / 不给时点 `validity` 仍 `None`
- [x] WP-6 四向反证 N-1…N-4（**每条两向实测**）+ 归档进树
- [x] WP-7 四道门 + 定向套件 + 记录面

## 决策登记（本 cycle 落定）

| # | 决策 | 结论与依据 |
| --- | --- | --- |
| ① | 四样怎么进 DTO | **取「直接加四个字段」** —— 判据要求「**既有键逐字不变**」+「缺省不凭空多键」；四个字段都有**非空语义**（`contradictions` 空列表 / `superseded_by` 空列表 / `disposition` 恒有值 / `reason` 恒有值）⇒ **不**需要可空嵌套对象（那种形态会让「无值」与「空列表」混淆）|
| ② | 反向链接怎么取 | **取「路由在构造 DTO 前扫同一批记录一次」**（复用 `_reverse_links`）—— DTO 层**不做**带状态的扫描（它是纯数据）；逐条再查会 N+1 且两处看到不同的世界 |
| ③ | 处置与理由的**同源** | **已定**：**复用** `disposition_of` / `_reason`（**不**在路由里重写一套）；判据钉「两处同值」 |
| ④ | 快照 | **已定**：动 DTO ⇒ **同轮**重生成并提交；快照判据**一字不改** |
| ⑤ | 承接面 | **不动**（复用既有 DTO 单点 / 纯函数 / 快照机器）|

## 证据

| 门 | 读数 |
| --- | --- |
| HTTP 判据 | `test_memory_api.py` **13 passed**（原 10 + 3）|
| 快照判据 | `test_openapi_snapshot.py` **8 passed**（**一字未改**）；快照 `+24 / -0`（同轮重生成）|
| 四向反证 | **基线 GREEN**（未按压不得红）+ `N-1`…`N-4` **全 `RED`** + 二进制复原 raw `sha256` 一致；归档 **674 B / `CR=0`** |
| 四道门 | `ruff check` / `ruff format --check`（1192 files）/ `mypy` strict（**1182** files）/ 规模门 全绿 |

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/api/test_memory_api.py` | **追加**用例（既有 10 例**一字未动**） | — | 见 RECHECK | **0** |
| `services/api/dto/memory.py` | `MemoryRecordDto` **+4 字段** | **既有 13 字段一个不改名、不改语义**（纯**附加**）| 见 RECHECK | **0** |
| `services/api/routers/memory.py` | `_record_dto` **+4 赋值** + 反向链接扫描 | 既有赋值**逐字保留** | 见 RECHECK | 见 RECHECK |
| `docs/api/openapi.m13.json` | **同轮重生成**（生成器产出，非手写） | — | 见 RECHECK | — |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 影响报告

- **Domain / API / schema 变化**：`MemoryRecordDto` **+4 字段**（附加）；OpenAPI 快照**同轮重生成**。
- **安全 / 凭据变化**：无（`scope` 仍**不是** ACL；本轮**不**触认证面）。
- **兼容性 / 迁移风险**：**低** —— 新增键对旧读者是**附加信息**；既有 13 字段语义逐字不变。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本 cycle 的机械面（**两个读面必须同源同值**；**补读面缺口不得改既有键**）属既有纪律的应用；
**未**沉淀新条目 —— 其一般形态已由 `MEM-20261010-215`（判关系不判位置）与
`MEM-20261010-216`（下游同步纪律）承载；本轮**新增**的一级纪律（**判据不得恒假**）
已在 GOAL-052 的 frontmatter §8 写明，属该 GOAL 的**授权面**而非新记忆条目。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | 决策 ①/② 落定；WP-1…WP-7 开工。 |
### 本轮实测到的**假反证臂一处**（如实登记，已修 —— 由新增的**基线门**当场抓到）

`N-4`（不给时点却填 `validity`）**初版报 GREEN**：受判面用了一条**没有任何时效声明**的记录
⇒「不猜」与「拿挂钟猜」**两种行为都返回 `None`** ⇒ 该断言**区分不了两件事**（**反证臂失效**）。
**修法**：受判面换成**已到复核期**的记录（猜的话会立刻报 `REVIEW_DUE`，正确行为是 `None`）。
**这一条比「判据恒假」更细**：判据**会响**，但**受判面选得区分不了两件事** ——
「有断言」≠「断言在下判断」（承 `MEM-20261009-210` 同族；与序 17 的 `K-2` 同族）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | 决策 ①/② 落定；四样补齐 + 同源接线 + 快照同轮。 |
| 2026-10-11 | DONE | 四道门绿；`RECHECK-20261011-410` 独立复检（含基线门抓到的假反证臂修正）。 |
