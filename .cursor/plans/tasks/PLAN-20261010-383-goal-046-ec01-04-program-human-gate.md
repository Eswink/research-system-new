---
id: PLAN-20261010-383
slug: goal-046-ec01-04-program-human-gate
title: GOAL-20261010-046 cycle 1（EC-01…EC-04）：程序级人工闸门可声明 / 可判定 / 可点名
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-384-goal-046-ec01-04-program-human-gate.md
memory_entries:
  - extraction-must-not-re-point-existing-criteria
parent_goal: GOAL-20261010-046
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-046 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不声明 ⇒ 逐字不变**；`[]` 与 `None`
    **语义互不混用**；**不**自动消解冲突；**不**做冲突检测算法；两库（+ Fake）**同契约**；
    **改既有判据必须走自证清单**（`MEM-20261009-210`）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    让程序**自己声明**「到第 N 轮停下等人」：① 域 +1 **可选**声明 `human_gate_at_index`
    （缺省 `None` = 不设闸门 ⇒ 既有行为逐字不变；越界 ⇒ **点名**）；② **两库同契约**落库
    （SQLite schema + 迁移 020 只加列；PG `INSERT` 带列）；③ 建程序 DTO / 路由 / 读面透传；
    ④ **判定与推进**：第 N 轮**跑完之后**的推进被拦住 —— 判定**复用**序 12 的
    `WAIT_FOR_APPROVAL`（同一件事：等人拍板），判词**点名**声明值与待审批标识；
    语义**照抄** phase 面的 `pending_human_gates`（声明的闸门 **−** 已裁决审批）；
    ⑤ **两向反证**（G-1 绕过 / G-2 轮前误拦 / G-3 已裁决仍拦）。
    **不**新建第二套审批/闸门机制；**不**自动放行；缺省逐字不变。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿**：提案字段表**无**该两字段 / 记录字段表**有** / SQLite 只带 `supersedes` /
      PG 硬编码 `[]`（`empty at commit`）/ 消费面零命中 / 构造带 `contradictions=` 的提案 ⇒ `TypeError`。
      两列**已在表上**（SQLite schema 与 `migrations/004`）⇒ **无新迁移**（决策 ② 的答案）。
    verify: >-
      `dataclasses.fields(...)` 两份字段表；`rg -n "empty at commit" adapters/postgres/memory_store.py`；
      `rg -n "valid_from|contradictions" adapters/postgres/migrations/004_memory_state.sql`。
    status: PASS
  - id: AC-2
    criterion: >-
      **声明与落库（三适配器同契约）**：提案可声明；SQLite / PG / Fake 的 `commit` 都带上；
      往返一致；缺省 `[]` / `None` 在**三处**都逐字保持。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/adapters tests/domain -q`
      ⇒ **1027 passed, 3 skipped**（含新用例）。
    status: PASS
  - id: AC-3
    criterion: >-
      **判定与读面（点名）**：读面**逐条披露** `contradictions` 与 `valid_from`；
      理由**点名**冲突标识（`[]` ⇒ 不追加任何文字）；生效起点以 ISO 串披露（`None` 不猜）。
    verify: >-
      `tests/adapters/canonical/test_memory_read_dispositions.py` ⇒ **18 passed**
      （原 15 + 3 新：冲突点名 / 生效起点披露 / 未声明不得凭空）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（真按压）**：`C-1`（SQLite 不带两字段 ⇒ 复现**静默丢弃**）/`C-2`（点名句变空）/
      `C-3`（**未声明也报冲突**，凭空）三条**全部判红**；复原用**二进制读写**且 raw `sha256`
      **逐字节相同**。
    verify: >-
      `scratch/goal045-press.txt` 三行全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-046-press-two-way.txt`（295 B / `CR=0`）。
    status: PASS
---

# PLAN-20261010-383 — GOAL-20261010-046 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-046`（MAINLINE 程序表**序 13**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（六条读数 + 无新迁移的判定） | PASS |
| AC-2 | 声明与落库（三适配器同契约）⇒ 1027 passed | PASS |
| AC-3 | 判定与读面（点名 + 披露）⇒ 18 passed | PASS |
| AC-4 | 两向反证（C-1/C-2/C-3 全红 + 二进制复原一致） | PASS |

## 实施清单

- [x] WP-1 域：提案 +2 **可选**字段（缺省 `[]` / `None`）+ 冲突项校验（非空字符串，非法点名）
- [x] WP-2 SQLite `commit` 带上两字段（此前只带 `supersedes`）
- [x] WP-3 PG `commit` 带上两字段（**删掉** `None` / `_json([])` 两个硬编码）
- [x] WP-4 **Fake `commit`** 带上两字段（**同一类缺陷的第三个适配器** —— 判据当场抓到）
- [x] WP-5 读面：逐条披露两字段 + 理由点名冲突（`[]` 不追加）
- [x] WP-6 判据：域 4 例 + SQLite 2 例 + 读面 3 例
- [x] WP-7 两向反证（C-1/C-2/C-3）+ 归档进树
- [x] WP-8 门（四道门 + 规模门；`tests/adapters`/`domain`/`postgres` 广面绿）

## 证据

| 门 | 读数 |
| --- | --- |
| 域判据 | `tests/domain/test_memory_declaration_fields.py` **4 passed** |
| SQLite 往返 | `test_memory_scope_and_validity.py` **13 passed**（原 11 + 2 新） |
| 读面判据 | `test_memory_read_dispositions.py` **18 passed**（原 15 + 3 新） |
| 广面 | `tests/adapters + domain` **1027 passed, 3 skipped**；`tests/postgres` + 规模门 **1201 passed, 101 skipped** |
| 四道门 | `ruff check` / `ruff format --check` / `mypy` strict（441 files）**全绿** |
| 两向反证 | `C-1`/`C-2`/`C-3` **全红**；二进制复原 raw `sha256` 一致；归档 295 B / `CR=0` |
| **as-is m0** | `PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0 / **5345 passed, 228 skipped**）|

### 本轮实测到的**第三个适配器**（同类缺陷，如实登记）

Fake 的 `commit` **同样**只带 `supersedes` —— 判据在 Fake 路径上当场假绿（读面判据 3 例里
2 例红）。它的源码注释**自己就写着**这条纪律（「少带字段会让判据在 Fake 路径上假绿（实测过）」）
⇒ **同一条纪律第二次生效**。已修（三适配器同契约）。

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/sqlite/test_memory_scope_and_validity.py` | **追加** 2 例（既有 11 例**一字未动**） | — | `+41 / -0` | **0** |
| `tests/adapters/canonical/test_memory_read_dispositions.py` | **追加** 3 例（既有 15 例一字未动） | — | `+51 / -0` | **0** |
| `tests/domain/test_memory_declaration_fields.py` | **新增**文件 | — | 新增 | — |
| `packages/domain/memory.py` | +2 字段 + 校验 | — | `+12 / -0` | **0** |
| `adapters/sqlite/memory_store.py` | `commit` +2 字段 | — | `+4 / -0` | **0** |
| `adapters/postgres/memory_store.py` | `commit` +2 字段（**替换**两个硬编码） | 硬编码 `None`/`[]` ⇒ 提案值 | `+4 / -2` | 仅那 2 行 |
| `adapters/fakes/memory_store.py` | `commit` +2 字段 | — | `+5 / -0` | **0** |
| `adapters/canonical/memory_read.py` | 读面 +2 字段 + 点名助手 | — | `+20 / -1` | 仅被扩展的 1 行 |

## 影响报告

- **Domain / API / schema 变化**：域**+2 可选字段**；**无**迁移（两列已在表上）；
  读面载荷 **+2 键**（`contradictions` / `valid_from`）—— 新增键对旧读者是**附加信息**
  （既有键逐字不变）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：**低** —— 缺省路径逐字不变（三适配器各有判据钉住）。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 域 + 三适配器 + 读面落地；**判据抓到第三个适配器（Fake）的同类缺陷**；三向按压全红。 |
| 2026-10-10 | DONE | 四道门 + 广面绿；`RECHECK-20261010-384` 独立复检。 |
