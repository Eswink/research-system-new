---
id: MEM-20261007-191
title: "人工恢复一条死信：终态语义改成「对自动路径终态」+ 不重置尝试预算；且按压必须行尾自适应（LF 模式匹配 CRLF 文件会静默不命中）"
status: ACTIVE
created_at: 2026-10-07
updated_at: 2026-10-07
scope: repository
confidence: 0.93
review_after: 2027-04-07
source_plans:
  - .cursor/plans/tasks/PLAN-20261007-303-goal-032-ec01-dead-letter-manual-recovery.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261007-304-goal-032-ec01-dead-letter-manual-recovery.md
supersedes: []
tags: [dead-letter, manual-recovery, terminal-semantics, press-test, crlf, goal-032, plan-303]
---

## 做了什么

`R26-1`（GOAL-026 登记「死信人工恢复路径不存在」）在 GOAL-032 cycle 1 落地为
`WorkflowEngine.requeue`（ADR-0033）。三条可复用的工程事实：

**① 「终态」与「可人工恢复」不矛盾，但读法必须写死。** `DEAD_LETTER ∈ terminal()` 是既有
设计决定（被 5 个 adapter 守卫点消费：两 adapter 的 `acquire_lease` / `cancel_run`、PG 的
完成校验与幂等集）。要给它加出边而不放大语义变化面，做法是：

- 出边**只有一条**且**只由人工入口**触发（自动路径不引用那个事件名）—— `terminal()`
  **逐字不动**，语义收紧为「**对自动路径**终态」（谁不会再自动动它）而不是「对一切路径
  终态」（人也不能动它）；
- **用新事件名**（`REQUEUE`，不重用 `ENQUEUE`）：重用被占用的名字会让「谁在驱动这次迁移」
  在读面与既有参数化判据（`test_terminal_states_are_final` 的 `DEAD_LETTER + ENQUEUE` 行）
  上不可区分 —— 用新名 ⇒ **那条参数行一行都不用改**；
- **事件复用既有类型**（`task.retry_scheduled` + `reason=manual_requeue`，与租约恢复
  `reason=lease_expired` 同形）⇒ canonical 事件词表 **零扩张**，避开 `EventType` 计数与
  `EVENT_MODEL.md` 的四处同步。代价：读面要靠 `reason` 区分"人工恢复"与"自动重排"。

**② 人工恢复 ≠ 重置尝试预算。** `fence_seq` 是租约代次（M16 §8 单调性），**不能回退**；
`attempt` 由交付路径按代次重写。所以「恢复」只能给任务**再一次交付**的机会：再失败 ⇒ 仍按
`decide_failure` 落回死信（人工可再恢复）。若想要「恢复 = 重置预算」，那是**另一条**语义，
必须改 ADR 与判据 —— 别把它当实现细节顺手做掉。

**③ 按压的 CRLF 陷阱（本轮实测踩到）。** 首版反证脚本用 LF 字节模式在 `task_state.py` 里找
出边 ⇒ **静默未命中** ⇒ `P1` 报 "8 passed"（**假绿**）。文件是 CRLF（本仓 Windows 工作树
常见）。修法：按压前先按 `b"\r\n" in original` 自适应 `\n → \r\n`，且**断言模式确实命中**
（`assert pattern in original`）—— 该断言就是这条记忆的机械化。

## 为什么这样做

- 「终态」这个谓词在本仓被当**边界**用（不可重新租约 / 不可取消 / 不可完成）。把 `DEAD_LETTER`
  从 `terminal()` 里**移出去**会**放大**语义变化面：5 个守卫点里「终态不可重新租约」不再
  覆盖死信 ⇒ 自动路径（claim / acquire / 退避派发）会开始捞它 = **无人值守的重试**，与
  「等人工」的意图相反。保留 `terminal()` + 只加一条人工出边是**最小的语义差**。
- 事件词表扩张的代价不在枚举本身，而在**它的四处同步**（`EventType` 计数判据、
  `EVENT_MODEL.md`、控制台页面图、既有 use case）——「任务回到可交付面」与租约恢复是**同类**
  canonical 事实，复用它更诚实也更小。
- 按压脚本不命中锚点时必须**判负而不是静默通过**：`pytest` 会照常报绿，所以
  `assert pattern in original` 是这类脚本唯一的自检。

## 怎么做与复现

- **先勘察后实现**：`rg -n "DEAD_LETTER" packages/domain/task_state.py` +
  `rg -n "terminal\(\)" packages/ adapters/ services/ --type py` 列出全部消费点；
  跑既有「无出边」判据确认它钉的正是要改的事实（`test_dead_letter_has_no_outgoing_transition`）。
- **改语义必须留 ADR**：读 `ADR-0030` 的候选（它问的是「验收门拒收要不要**进**死信」，
  与本决定**可分别决定**），新增 `ADR-0033`；`docs/INDEX.md` 同步登记。
- **三实现同判**：新 Port 方法要同时落在 SQLite / PG / Fake（Fake 没有死信到达路径 ⇒
  用测试装配面 `mark_dead_letter` 造起态，并把这条差异**写成断言**）。
- **按压**：`uv run --frozen --no-sync python -B scratch/goal032-cycle1-press.py` ⇒
  `P1_RED`（摘掉出边）/ `P2_RED`（点名拒绝改静默）/ `FINAL_MATCHES_BASELINE True`；
  留档 `scratch/goal032-cycle1/press-matrix.log`（二进制写盘、CR=0）。
- 复现判据：
  `uv run --frozen --no-sync python -B -m pytest tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py
  tests/contracts/test_dead_letter_manual_recovery_contract.py tests/e2e/test_dead_letter_recovery_full_loop.py -q`
  ⇒ 全绿。

## 适用边界

- **只覆盖 `DEAD_LETTER` 的人工恢复这一条路径**：自动恢复（超时自动重生 / 指数再入队）、
  按 run 批量恢复、恢复的审批门（`require_approval`）、恢复后 run 的**自动**继续
  （run 级入口仍是人工 `POST /runs/{id}/resume`）**都不在**本决定内。
- **只在单节点 / 单进程语义下实测**；跨副本的恢复竞争（同一死信被两处恢复）未取证。
- 「恢复 = 不重置预算」是本 ADR 的选择，不是不可变事实：要改成"重置"须改 ADR 与判据。
- `tools/` 目录的旧资产不在受判面内（只有被点名脚本过四道门）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261007-303-goal-032-ec01-dead-letter-manual-recovery.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261007-304-goal-032-ec01-dead-letter-manual-recovery.md`
- 决策：`docs/adr/ADR-0033-dead-letter-manual-recovery.md`（`Status: Accepted`）；
  邻接未决 `docs/adr/ADR-0030-validation-failure-consumption.md`（仍 `Proposed`）
- 事实：GOAL-20261007-032 的「事实层结论」第 2 条（`terminal()` 的 5 个消费点逐条）；
  按压留档 `scratch/goal032-cycle1/press-matrix.log`（249 B / CR=0）
