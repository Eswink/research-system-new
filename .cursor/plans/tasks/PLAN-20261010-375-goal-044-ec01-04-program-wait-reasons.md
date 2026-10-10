---
id: PLAN-20261010-375
slug: goal-044-ec01-04-program-wait-reasons
title: GOAL-20261010-044 cycle 1（EC-01…EC-04）：等待理由可区分（WAIT_FOR_APPROVAL）+ 点名面 + 两向反证
status: DONE
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: .cursor/plans/rechecks/RECHECK-20261010-376-goal-044-ec01-04-program-wait-reasons.md
memory_entries:
  - waiting-reasons-must-not-share-one-kind
parent_goal: GOAL-20261010-044
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-044 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：等待理由**互不混用**；等待**点名**（不静默）；
    **不**新建第二套审批存储（复用既有 `ApprovalStore.list_for_run`，**只读**）；
    phase 面人工闸门语义**逐字保持**；**不**自动批准 / 不自动跳过；缺省逐字不变；
    **改既有判据必须走自证清单**（`MEM-20261009-210`）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把「程序推进的非终态等待」落成**两类互不混用**：① 新增 `WAIT_FOR_APPROVAL`
    （等人拍板：`WAITING_FOR_APPROVAL` / `PAUSED`）+ 判词**点名待审批 id**（经既有
    `ApprovalStore.list_for_run`；查不到 / 缺审批面 / 面故障**都点名**）；② 「还在跑」
    **仍落 `WAIT`** 且理由串与 `cited_facts` **逐字保持**；③ 判定面接线（驱动按 run 状态分派、
    API 组合根传入既有审批实例）；④ 实跑 + **两向反证**（W-1 混用必红 / W-2 点名失效必红）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿**：程序面只按 `is_terminal` 分派（非终态一律 `WAIT`）；run 面已有两个
      非终态常量；phase 面人工闸门经 `pause_for_human_gate` + `APPROVAL_REQUESTED`；
      审批查询面 = `ApprovalStore.list_for_run`。
    verify: >-
      `rg` 三条（`program_runner` 的分派 / `run_state` 的状态常量 / `phase_pause` 的闸门）；
      `rg -n "list_for_run" packages/application/ports/approval_store.py`。
    status: PASS
  - id: AC-2
    criterion: >-
      **判定种类扩齐**：`ProgramDecisionKind` +1（`WAIT_FOR_APPROVAL`）；域判据的**集合相等**
      同轮加一条（**纯加法**，谓词形态一字未改）；既有各态**逐字保持**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain -q` ⇒ 全绿；
      `git diff --numstat HEAD -- tests/domain/test_research_program.py` ⇒ `+4 / -0`（删除行 **0**）。
    status: PASS
  - id: AC-3
    criterion: >-
      **点名面（等待不静默）**：等待审批时 `cited_facts` **逐条点名** `state=<原文>` 与
      `待审批 id=<id>`；查不到 ⇒ 点名「查不到」；缺审批面 ⇒ 点名「未提供审批面」；
      面抛异常 ⇒ 点名异常（**不**静默降级）。「还在跑」的判词**逐字保持**既有形态。
    verify: >-
      `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` **7 passed**
      （逐条：点名 id / 暂停也算 / 还在跑仍 WAIT / 缺面点名 / 查不到点名 / 非 PENDING 不算 /
      只读审批面）。
    status: PASS
  - id: AC-4
    criterion: >-
      **两向反证（真按压）**：`W-1`（把 `WAIT_FOR_APPROVAL` 面压成恒 `WAIT` ⇒ **复现混用**）
      ⇒ 判据必红；`W-2`（点名句改成「查不到」）⇒ 判据必红；复原用**二进制读写**且 raw `sha256`
      **逐字节相同**。**并**：按压过程中发现 `pending_approval` 早先返回的 id 串是**死值**
      （改它不影响任何判据）⇒ 已删（签名收成单返回值）。
    verify: >-
      `scratch/goal044-press.txt` 两行全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-044-press-two-way.txt`（110 B / `CR=0`）。
    status: PASS
---

# PLAN-20261010-375 — GOAL-20261010-044 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-044`（MAINLINE 程序表**序 12**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（三条读数 + 审批查询面） | PASS |
| AC-2 | 判定种类扩齐（域集合纯加法 `+4/-0`） | PASS |
| AC-3 | 点名面（新判据 7 passed） | PASS |
| AC-4 | 两向反证（W-1/W-2 全红 + 死值清理） | PASS |

## 实施清单

- [x] WP-1 域：`WAIT_FOR_APPROVAL` + 文档（与 `WAIT` 互不混用的理由）
- [x] WP-2 新模块 `program_waiting.py`（`AWAITING_HUMAN` / `pending_approval` /
      `waiting_round_decision`）—— `program_runner.py` 有 450 行硬上限 ⇒ 与既有拆法同形
- [x] WP-3 驱动接线：`_evaluate` / `advance_program` 收 `approvals`（**只读**面）
- [x] WP-4 API 组合根：`approvals=deps.approvals`（**复用既有实例**，不建第二套存储）
- [x] WP-5 判据：拆出 `test_program_waiting_on_the_run_path.py`（7 例；规模门）
- [x] WP-6 两向反证（W-1/W-2）+ 归档进树
- [x] WP-7 门（四道门 + 规模门；`tests/application`/`domain`/`tooling` 广面绿）

## 证据

| 门 | 读数 |
| --- | --- |
| 新判据 | `test_program_waiting_on_the_run_path.py` **7 passed** |
| 驱动套件 | `test_program_runner.py` **18 passed**（既有面逐字保持） |
| 广面 | `tests/application + domain + tooling/test_python_source_limits` **2464 passed, 1 skipped** |
| 四道门 | `ruff check` / `ruff format --check` / `mypy` strict **全绿** |
| 规模门 | `program_runner.py` **448 行**（≤ 450）；`program_waiting.py` 78 行；两个判据文件 ≤ 450 |
| 两向反证 | `W-1` / `W-2` **全红**；二进制复原 raw `sha256` 一致；归档 110 B / `CR=0` |

## 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行读数 |
| --- | --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | 集合 +1 条目 | **形态一字未改**（仍是集合相等）；**纯加法** | `+4 / -0` | 删除行 **0** |
| `tests/application/run_orchestration/test_program_runner.py` | 新增 7 例**迁出**到新文件（拆分，非删除） | 既有 18 例**逐字在** | `+0 / -0`（拆分后净零） | 删除行 **0**（是搬迁） |
| `packages/application/run_orchestration/program_runner.py` | 非终态分派**搬到** `program_waiting.py`；签名 +1 参数 | **等价**（`WAIT` 分支逐字） | `+10 / -8` | 删除的**仅**被搬迁的 5 行分派块 + 2 行签名/传参 |
| `packages/domain/program.py` | 枚举 +1 | — | `+7 / -0` | **0** |
| `services/api/routers/programs.py` | 传 `approvals=deps.approvals` | — | `+4 / -0` | **0** |

## 影响报告

- **Domain / API / schema 变化**：域枚举 **+1**；**无**迁移（判定种类是代码值，不落库表结构）；
  **无** DTO / OpenAPI 变化（`kind` 以 `str` 透出，前端未枚举它）。
  路由**入口签名未变**（仍 `POST /programs/{id}/advance`）。
- **安全 / 凭据变化**：无（**只读**审批面；**不**新建存储、**不**改审批状态）。
- **兼容性 / 迁移风险**：**低** —— 新增 kind 对旧读者是**未知字符串**；`WAIT` 面逐字保持。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 域 + 新模块 + 驱动/组合根接线 + 7 例判据；规模门拆文件；两向反证全红（并清掉一处死值）。 |
| 2026-10-10 | DONE | 四道门 + 广面 2464 passed；`RECHECK-20261010-376` 独立复检。 |
