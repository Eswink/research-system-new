---
id: PLAN-20261010-401
slug: goal-050-ec01-04-superseded-memory-is-no-longer-used
title: GOAL-20261010-050 cycle 1（EC-01…EC-04）：被取代不再照用 —— 两向披露 + 第四态 + 消费端分派
status: DONE
created_at: 2026-10-11
updated_at: 2026-10-11
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-402-goal-050-ec01-04-superseded-memory-is-no-longer-used.md
memory_entries: []
parent_goal: GOAL-20261010-050
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-050 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**边界**：**不**新建存储 / 第二套生命周期机制；**不**做自动取代或
    链式传递闭包（只报**直接**链接）；**不**失去既有三态（`USE` / `ANNOTATE` / `SKIP`）的语义；
    **不**顺手改缺省路径（无取代关系时处置与理由**逐字不变**）；判据**不按位置/文本**写死
    （承 `MEM-20261010-215`）；改 DTO ⇒ 同轮同步 OpenAPI 快照（`MEM-20261010-216`）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让「**被取代**」成为一种**可判定的不适用理由**：① 勘察定稿（读数见 GOAL 正文八条）→
    ② **读面披露** —— `memory_read` 的逐条载荷**两个方向**都点名（`supersedes` / `superseded_by`；
    无关系 ⇒ 空列表）+ 既有十键**逐字保持**（EC-02）→ ③ **处置面** —— 新增第四态
    `SUPERSEDED`（与 `SKIP` **理由可区分**：被新版本替代 vs 时效已过；两者皆有时**都点名**），
    且**消费端真的按它分派**（研究循环的记忆门：处置同「跳过」，**判词各自点名**）（EC-03）→
    ④ **两向反证** `L-1`…`L-4`（EC-04）→ ⑤ EC-05（自举收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（读数逐条）**：`supersedes` 在域两面在场 / `supersede_memory` 是真写者
      （新记录 commit + 旧记录 `deactivate`）/ gate 有引用完整性 / 读面**零命中** /
      `disposition_of` 只吃时效 / **实跑** `active=False` 仍 `USE` / 消费端三态分派。
    verify: >-
      GOAL 正文「事实层结论」的八条读数（`rg` 命令 + 实跑探针）。
    status: PASS
  - id: AC-2
    criterion: >-
      **读面披露（两向都点名 + 既有键逐字保持）**：逐条载荷含 `supersedes`（它取代了谁）与
      `superseded_by`（谁取代了它）；**无关系 ⇒ 空列表**（声明性的值，不是缺字段）；
      既有十键**全在场且值不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters/canonical -q`
      ⇒ 全绿 + 新用例 5 例（被取代不再照用 / 两向披露 / 无关系逐字不变 /
      与过期可区分 / 计数摘要分开报）。
    status: PASS
  - id: AC-3
    criterion: >-
      **处置面（第四态 + 与「已过期」可区分 + 真的被消费）**：被取代的记录处置为
      `SUPERSEDED`（**不再** `USE`）；理由**点名**取代它的那条 id；**两者皆有时都点名**
      （优先级固定：已取代先于时效）；**消费端**（`memory_gate_verdict`）**真的按它分派**
      （处置同 `SKIP`，判词**各自点名**，不共用一句）；**无取代关系 ⇒ 逐字不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration -q`
      ⇒ 全绿 + 新用例 3 例（被取代跳过 / 两因分开点名 / 只有被取代时不得说过期）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（真按压）**：`L-1` 被取代仍报 `USE` / `L-2` 未取代却报为已取代（凭空）/
      `L-3` 两个方向只给一个 / `L-4` 把「已取代」与「已过期」混用 —— 四条**全部判红**；
      复原用**二进制读写**且 raw `sha256` 逐字节相同；判词归档进树（`CR=0`）。
    verify: >-
      `scratch/goal050-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-050-press-two-way.txt`（471 B / `CR=0`）。
    status: PASS
---

# PLAN-20261010-401 — GOAL-20261010-050 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-050`（MAINLINE 程序表**序 18**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（八条读数：有写者 / 无读面 / 处置面看不见 / 实跑 `active=False` 仍 `USE`） | PASS |
| AC-2 | 读面披露（两向都点名 + 无关系空列表 + 既有十键逐字保持） | PASS |
| AC-3 | 处置面（第四态 `SUPERSEDED` + 与过期可区分 + **消费端真的分派**） | PASS |
| AC-4 | 两向反证 L-1…L-4 全红 + 二进制复原一致 | PASS |

## 实施清单

- [x] WP-1 读面：`DISPOSITION_SUPERSEDED` 常量 + `disposition_of(..., superseded=)`（**缺省 False ⇒ 逐字不变**）
- [x] WP-2 读面：`_reverse_links`（**只从同一批记录算**，不新增 Port 方法、不 N+1 查询）
- [x] WP-3 读面：逐条 +2 键（`supersedes` / `superseded_by`）+ `_reason` 两因分开点名
- [x] WP-4 读面：`dispositions` 计数摘要**多一格**（四态分开报）
- [x] WP-5 消费端：`MEMORY_SUPERSEDED` + `_split_by_disposition` 分三组 + 判词**两因分开点名**
- [x] WP-6 判据：读面 +5 例 / 消费端 +3 例；既有计数判据**同轮跟上枚举**（申报见 RECHECK）
- [x] WP-7 两向反证 L-1…L-4 + 归档进树

## 决策登记（本 cycle 落定）

| # | 决策 | 结论与依据 |
| --- | --- | --- |
| ① | 「已取代」怎么进处置 | **取「新增第四态 `SUPERSEDED`」** —— 要求是「与已过期**可区分**」；复用 `SKIP` 会让两者共用一格，判词只能靠措辞区分（**那正是轴的反面**）|
| ② | 反向链接怎么取 | **取「从同一批记录扫一次」**（`_reverse_links`）—— **不**新增 Port 方法（改动面最小、不动契约），也**不**逐条再查（那会 N+1 且两处看到不同的世界）|
| ③ | 是否动 DTO | **本 cycle 不动**：HTTP 读面（`MemoryRecordDto`）的披露面**另议**（本轮改的是**编排消费面**的读面 `memory.read`）。**若要动 ⇒ 必须同轮同步 OpenAPI 快照**（承 `MEM-20261010-216`）|
| ④ | 消费端 | 新态**进** `_split_by_disposition`（第三组），处置同 `SKIP` 但判词**分开点名**；未知取值仍 **fail closed**（新增已知态**不是**放宽那条）|
| ⑤ | 承接面 | **不动**（复用既有 `supersedes` / `deactivate` / 三态常量 / 消费端分派形态）|

## 证据

| 门 | 读数 |
| --- | --- |
| 读面判据 | `test_memory_read_dispositions.py` **27 passed**（原 22 + 5）|
| 消费端判据 | `test_memory_validity_gate.py` **15 passed**（原 12 + 3）|
| 两向反证 | `L-1`…`L-4` **全 `RED`**（3/7/1/2 例）+ 二进制复原 raw `sha256` 一致；归档 **471 B / `CR=0`** |
| 四道门 | `ruff check` / `ruff format --check` / `mypy` strict / 规模门 全绿 |
| 定向套件 | 见 RECHECK 的读数行（记录写完时回填）|
| **下游同步** | 本轮**未动** DTO / 路由 ⇒ **无需**重生成快照（§⑤ 的申报）|

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/canonical/test_memory_read_dispositions.py` | 既有计数判据的**期望枚举 +1 成员**；另追加 5 例；`_record` 助手 +1 可选形参 | **谓词形态一字未改**（仍是 `==` **精确相等** —— 不放宽、不改子集判定）；原有三个键**仍逐个被要求** ⇒ **未收窄受判面** | 见 RECHECK | 见 RECHECK |
| `tests/application/run_orchestration/test_memory_validity_gate.py` | **追加** 3 例 + `_row` 助手支持新态 | — | 见 RECHECK | **0**（助手是**字典加键**，既有三键逐字保留）|

**为什么动既有计数判据**：处置枚举**多了一个成员**是**契约变更**，期望值必须同轮跟上
（否则那条判据会**正确地**判红）。**登记为「契约扩展的同轮同步」**，不是放宽。

## 影响报告

- **Domain / API / schema 变化**：编排消费面的读面**+2 键**（`supersedes` / `superseded_by`）+
  处置枚举 **+1 态**（`SUPERSEDED`）；**无迁移**（`supersedes` 列早已在表上）；
  **HTTP DTO 未动** ⇒ OpenAPI 快照无需重生成。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：**低** —— 无取代关系时处置与理由**逐字不变**（判据钉住）；
  新增键对旧读者是**附加信息**；消费端对**未知**处置仍 fail closed。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口）。

## 无可复用事实

本 cycle 的机械面（**「新不适用理由」要单成一态而不是复用旧态靠措辞区分**；
**反向链接从同一批记录算而不新增查询面**）属既有纪律的应用；**未**沉淀新条目 ——
与该族相关的一般形态已由 `MEM-20261010-215`（判关系不判位置）与
`MEM-20261010-216`（下游同步纪律）承载。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-11 | IN_PROGRESS | 第四态 + 两向披露 + 消费端分派落地；判据 +8 例；四向按压全红。 |
| 2026-10-11 | DONE | 四道门全绿；`RECHECK-20261010-402` 独立复检。 |
