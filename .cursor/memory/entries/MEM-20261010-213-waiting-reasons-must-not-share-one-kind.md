---
id: MEM-20261010-213
title: "非终态的「等人」与「等机器」不得共用一个判定种类 —— 流程面的等待理由必须可区分（否则恢复路径无法回答「该等谁」）"
status: ACTIVE
created_at: 2026-10-10
updated_at: 2026-10-10
scope: repository
confidence: 0.95
review_after: 2027-04-10
source_plans:
  - .cursor/plans/tasks/PLAN-20261010-375-goal-044-ec01-04-program-wait-reasons.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261010-376-goal-044-ec01-04-program-wait-reasons.md
supersedes: []
tags: [orchestration, decision-kinds, human-gate, continuity, goal-044]
---

## 做了什么

程序推进（`advance_program`）此前对**非终态**轮只有一个判定种类 `WAIT`：理由串
`第 N 轮尚未终止（state=<s>）⇒ 本轮不推进`。但它把两件相反的事读成同一件：

- **还在跑**（等**机器**：正常，什么都不用做）；
- **停在人工闸门**（等**人**拍板：需要人去批，机器做不了）。

本轮新增 `WAIT_FOR_APPROVAL` 并把分派收进 `program_waiting.py`：`state ∈
{WAITING_FOR_APPROVAL, PAUSED}` ⇒ 新种类 + 判词**点名待审批 id**（经既有
`ApprovalStore.list_for_run`）；其余非终态 ⇒ `WAIT`（**逐字保持**）。

## 为什么这样做

**同一病在两处的形态**（本仓实测的第二处）：

| 面 | 被混用的两件事 | 处置 |
| --- | --- | --- |
| **终态面**（GOAL-040，序 8） | 「没有结论（跑失败了）」vs「结论说停」 | `STOP_RUN_FAILED` vs `STOP_RULE` |
| **非终态面**（本条，序 12） | 「等机器跑完」vs「等人拍板」 | `WAIT` vs `WAIT_FOR_APPROVAL` |

**为什么这是连续性轴的失真**：`WAIT` 是**恢复路径的入口判定**。它若把「等人」读成「还在跑」，
恢复侧就无法回答「该不该重试 / 该找谁 / 该等哪个审批」——这正是轴定义里
「中断后能接回、**交接不丢上下文**」在编排层的直接违反。

**为什么必须点名**（而不是只给种类）：种类回答「等谁（人/机器）」；**点名**回答
「等**哪一个**审批」。缺任一半，恢复侧仍要自己去猜 —— 而**猜**正是本仓反复禁止的形态
（「点名失败而非静默降级」）。

## 现象

```
# 混用（修正前）：同一 kind、不同真相
kind=WAIT  reason="第 1 轮尚未终止（state=RUNNING）⇒ 本轮不推进"
kind=WAIT  reason="第 1 轮尚未终止（state=WAITING_FOR_APPROVAL）⇒ 本轮不推进"
           ↑ 前者等机器，后者等人 —— 读面分不出

# 修正后
kind=WAIT              reason="...（state=RUNNING）..."          # 等机器，逐字保持
kind=WAIT_FOR_APPROVAL reason="第 1 轮停在**人工闸门**（state=WAITING_FOR_APPROVAL）
                              ⇒ 等**人**拍板待审批 id=apr-1；本轮不推进（不自动批准、不自动跳过）"
```

## 根因

| 层 | 事实 |
| --- | --- |
| 判定面 | `_evaluate` 只按 `last.is_terminal` 二元分派（终态 / 非终态）⇒ 非终态内部不再细分 |
| 域层 | **早已可区分**：`run_state.py` 有 `WAITING_FOR_APPROVAL` / `PAUSED`（不在 `terminal()` 里） |
| 闸门面 | phase 面已有（`pause_for_human_gate` 注册 `ApprovalRecord` + `APPROVAL_REQUESTED`） |
| 落差 | 程序推进**不读**审批面 ⇒ 它不知道「这一轮在等人」 |

## 怎么做与复现

**修法（三处，全在既有件上）**：

1. 域：`ProgramDecisionKind` + `WAIT_FOR_APPROVAL`（**同轮**把域判据的集合相等加一条 —— 纯加法）；
2. 判定：新模块 `program_waiting.waiting_round_decision(last, index, approvals)` ——
   `state ∈ AWAITING_HUMAN` ⇒ 新种类 + `pending_approval(...)` 点名；否则 `WAIT` **逐字**；
3. 接线：驱动收 `approvals`（**只读**形状：只用 `list_for_run`）；组合根传**既有**实例
   （`deps.approvals` —— **不**建第二套存储）。

**`pending_approval` 的四态（都点名，无静默分支）**：查到 PENDING ⇒ 点名 id；
没有 PENDING 记录 ⇒ 点名「查不到」；缺审批面 ⇒ 点名「未提供审批面」；
面抛异常 ⇒ 点名异常类型与消息（**不**降级成「没等待」）。

**判据**（`tests/application/run_orchestration/test_program_waiting_on_the_run_path.py`，7 例）：
逐条覆盖上表 + **反证**：RUNNING 仍落 `WAIT` 且理由串**逐字相同**、非 `PENDING` 不算待审批、
推进**只读**审批面（不自动批准 / 不跳过）。

**按压（两向反证）**：`W-1` 把 `AWAITING_HUMAN` 判断压成恒真 ⇒ 6 例红；
`W-2` 把点名句改成「查不到」⇒ 2 例红。

## 适用边界

- 适用于：一切「等待/暂停/阻塞」在多态流程里被**共用一个状态**的地方（本仓：程序推进的
  非终态面；对照组：终态面的 GOAL-040）。
- **不**适用于：终态（那里已有 `STOP_*` 族）；也不需要为**每一种**等待都新增 kind ——
  只有当两类等待的**处置相反**（一个什么都不用做 / 一个必须人工介入）时才必须分开。
- **不声称**：本条的判定**只到「可判定 + 点名」**；**不**做等待的处置（催办 / 升级 / 超时）
  与 SLA（登记为 `V-1` / `V-3`）；**不**接通 D 组审批通道本身。
- **只读**：判定面对审批面**只读**（`list_for_run`）—— 推进**不**改审批状态。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20261010-375-goal-044-ec01-04-program-wait-reasons.md` | 三处修法 / 判据 / 两向反证 |
| recheck | `.cursor/plans/rechecks/RECHECK-20261010-376-goal-044-ec01-04-program-wait-reasons.md` | 独立复检：混用实测 / 逐条点名 / W-1·W-2 全红 |
| repository | `packages/application/run_orchestration/program_runner.py`（旧）与 `program_waiting.py`（新） | 混用现场与两类分派 |
| repository | `packages/domain/run_state.py` / `phase_pause.py` / `approval_store.py` | 域已可区分 + 闸门副作用 + 审批查询面 |
