---
id: PLAN-20261010-389
slug: goal-047-ec01-04-the-gate-can-be-resumed
title: GOAL-20261010-047 cycle 1（EC-01…EC-04）：声明的闸门**接得回** —— 注册面 + 裁决后续跑 + 两向反证
status: IN_PROGRESS
created_at: 2026-10-10
updated_at: 2026-10-10
latest_recheck: null
memory_entries: []
parent_goal: GOAL-20261010-047
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261010-047 的 **EC-01 / EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**边界**：**不新建第二套**审批 / 闸门机制（复用既有 `ApprovalStore.register`
    与 `phase_pause` 的同一语义）；**不改 phase 面闸门语义**（逐字保持）；**不自动**批准 / 放行 /
    超时；**不**做催办 / 通知；改 DTO ⇒ 同轮同步 OpenAPI 快照（`MEM-20261010-216`）；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把「闸门只停不回」修成「**接得回**」：① 勘察定稿（读数见 GOAL 正文）；② **注册面** —— 声明闸门
    在该轮跑完后的推进里经**既有** `ApprovalStore.register` 注册一条待决审批（语义与 phase 面同源），
    判词**点名**该标识；**同一推进重复跑不重复注册**（幂等）；③ **接回面** —— 该审批**被裁决后**
    推进照常继续（该轮**不重跑**）、**未裁决仍停**、**缺面仍点名**；④ **两向反证**（未裁决不得续 /
    已裁决必须续 / 只读面不得冒充接回面 / 重复注册不增 / 未声明零调用）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **决策②的实测结论落定**（本轮**已测**）：`POST /approvals/{id}/decide` 对
      **`SUCCEEDED` 的 run** 报 `409 Invalid Transition`（`cannot decide approval in run state
      SUCCEEDED`），且 run 状态机**没有**「终态 ⇒ `WAITING_FOR_APPROVAL`」的边
      （`_TRANSITIONS` 只允许 `RUNNING → WAITING_FOR_APPROVAL`）⇒ **不能**靠「把 run 挪回等待态」
      来接回；**采纳的形态**：程序级闸门的审批用**自己的 action 前缀**（`program-gate:`，
      与 phase 面的 `human-gate:` **区分开**），`decide` 对**该前缀**走**新增分支**（准入 =
      该前缀 + run **终态**），**既有分支逐字不变**。
    verify: >-
      `rg -n "cannot decide approval in run state" services/api/approvals.py`；
      `rg -n "RUNNING, Transition.REQUEST_APPROVAL" packages/domain/run_state.py`；
      实跑读数见 GOAL 正文 1.7 与 PLAN 的「实测读数」表。
    status: PENDING
  - id: AC-2
    criterion: >-
      **注册面（复用既有 Port）**：推进在闸门轮**注册一条待决审批**（`ApprovalStore.register`，
      `risk="HUMAN_GATE"`、`action="program-gate:<program_id>"`、`context=<第 N 轮>`、
      `policy_source="program-gate"`、`requested_event_id=""` —— 逐字段与 phase 面**同源可对照**）；
      判词的 `cited_facts` **点名**该审批标识；**幂等**：同一声明点重复推进**不新增**待决
      （按 `list_for_run` 里**同 action 的待决**判去重，**不**新建表）；**缺写面**（只读审批面）
      ⇒ **点名**（不静默当成「已注册」）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/application/run_orchestration -q`
      ⇒ 全绿 + 新用例（注册发生 / 点名 / 幂等 / 只读面点名 / 未声明零调用）。
    status: PENDING
  - id: AC-3
    criterion: >-
      **接回面（经既有 HTTP 面）**：`POST /approvals/{id}/decide` 对 `program-gate:` 审批
      **接受裁决**（run 终态、无续跑语义 ⇒ **不**改 run 状态、**不**伪造续跑）；裁决后再推进
      ⇒ **照常继续**（`CONTINUE` / 起该轮**之后**的序号，**该轮不重跑**）；**未裁决** ⇒ 仍停且点名；
      **缺审批面** ⇒ 仍点名（fail-closed 逐字保持序 14 的三种形态）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e tests/api -q` ⇒ 全绿 + 新用例
      （裁决前停 / 裁决后续 / 该轮不重跑 / 只读面点名）。
    status: PENDING
  - id: AC-4
    criterion: >-
      **两向反证（真按压）**：`H-1` 未裁决也照常续（去掉拦住）⇒ **RED**；`H-2` 已裁决仍停 ⇒ **RED**；
      `H-3` 只读面冒充注册面（注册被静默跳过但判词说「已注册」）⇒ **RED**；`H-4` 重复注册
      （同推进跑两次仍新增待决）⇒ **RED**。复原用**二进制读写**，raw `sha256` 逐字节相同；
      归档进树（`CR=0`）。
    verify: >-
      `scratch/goal047-press.txt` 全 `RED` + `sha 复原一致=True`；归档
      `.cursor/plans/goals/evidence/GOAL-20261010-047-press-two-way.txt`。
    status: PENDING
---

# PLAN-20261010-389 — GOAL-20261010-047 cycle 1（EC-01…EC-04）

> **主线归属**：`GOAL-20261010-047`（MAINLINE 程序表**序 15**）的 EC-01…EC-04。

## 验收条件

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 决策②的实测结论落定（不能靠挪 run 状态；采纳 `program-gate:` 新分支） | PENDING |
| AC-2 | 注册面（复用既有 Port + 点名 + 幂等 + 缺写面点名） | PENDING |
| AC-3 | 接回面（裁决后照常续 / 未裁决仍停 / 不重跑） | PENDING |
| AC-4 | 两向反证 H-1…H-4 全红 + 二进制复原一致 | PENDING |

## 实施清单

- [ ] WP-1 `program_waiting`：注册助手（幂等去重 + 只读面点名）
- [ ] WP-2 `program_runner`：闸门分支注册 + `cited_facts` 点名
- [ ] WP-3 `approvals.py` + `decide` 路由：`program-gate:` 分支（既有分支逐字不变）
- [ ] WP-4 判据：判定面 4 例 + e2e/API 4 例
- [ ] WP-5 两向反证 H-1…H-4 + 归档进树
- [ ] WP-6 四道门 + 定向套件 + OpenAPI 快照同轮（若动 DTO）

## 实测读数（cycle 1 的决策依据；**已测**）

| # | 探针 | 读数 |
| --- | --- | --- |
| 1 | 闸门触发后 run 的状态 | **`SUCCEEDED`**（闸门**只写决策**，不改 run 状态） |
| 2 | 对 `SUCCEEDED` 的 run 走 `POST /approvals/{id}/decide` | **`409 Invalid Transition`**，`detail` = `cannot decide approval in run state SUCCEEDED` |
| 3 | 状态机是否有「终态 ⇒ `WAITING_FOR_APPROVAL`」的边 | **没有** —— `_TRANSITIONS` 只有 `(RUNNING, REQUEST_APPROVAL) → WAITING_FOR_APPROVAL` |
| 4 | 注册一条**真**审批后再裁决（run 仍 `SUCCEEDED`） | **同样 409** ⇒ 卡的**不是**「有没有记录」，是**状态准入** |
| 5 | `decide` 之后的续跑面 | `_resume_after_approval` 对**非 `human-gate:` 前缀**是 no-op（`_require_resumable` 提前返回、`resume_after_approval` 抛 `InvalidInputError` 被吞）⇒ **新增分支不需要动续跑面** |

## 证据

| 门 | 读数 |
| --- | --- |
| 勘察读数 | 上表 5 条（闸门后 run = `SUCCEEDED` / `decide` ⇒ `409 Invalid Transition` / 状态机无终态入边 / 真记录也 409 ⇒ 卡准入 / 续跑面对非 `human-gate:` 前缀是 no-op）|
| 判据（待回填） | 判定面新用例 + e2e/API 新用例 |
| 两向反证（待回填） | `H-1`…`H-4` 全 `RED` + 二进制复原 `sha256` 一致 |
| 四道门（待回填） | `ruff check` / `ruff format --check` / `mypy` strict / 规模门 |


**结论**：接回面 = ① 注册（AC-2）+ ② `decide` 的**准入新增一个分支**（AC-3）。
**不**改 `human-gate:` 分支的任何一行（既有 10 + 4 + 4 例审批面用例是它的**回归网**）。

## 影响报告

- **Domain / API / schema 变化**：预期 = 程序面接线 + `decide` 路由新增分支（**不**改 DTO 形状
  ⇒ 若确认不改 DTO 则**无需**快照同步；改动前先确认）。
- **安全 / 凭据变化**：**审批准入面新增一个分支** —— 必须**收窄**到「`program-gate:` 前缀 +
  run 终态」，且**不得**让既有的「非等待态不得裁决」规则被绕过（该规则是既有判据的靶子）。
- **兼容性 / 迁移风险**：**低**（缺省不声明闸门 ⇒ 既有路径逐字不变）。
- **上游版本影响**：无。
- **下一项任务**：WP-1…WP-6。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-10 | IN_PROGRESS | 决策②的实测读数落定（5 条，见上表）；WP-1…WP-6 待执行。 |
