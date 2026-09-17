---
id: MEM-20260915-057
title: "自动派发的两条硬约束：先迁 canonical 状态再动手；新执行体必须进受控词表与读面"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.92
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-082-unattended-retry-dispatch.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-082-unattended-retry-dispatch.md
supersedes: []
tags:
  - retry
  - scheduler
  - daemon
  - run-state
  - read-face
  - ops-visibility
---

# 自动派发的两条硬约束

## 做了什么

cycle 18 让重排未到期的失败把 run 停 `PAUSED`（上下文交回 service），cycle 19 补上
"没有人自动按 resume"这一环：新增 `WorkflowEngine.due_retry_task_ids(run_id)` 读面 +
`RetryDispatchScheduler` 守护线程（`ScheduleJob.RETRY_DISPATCH`，每轮扫 canonical
`PAUSED` 且**到期**的 run 并续跑一次）。落地时踩到两个坑，都不是"实现细节"，是这类
组件的通用约束。

## 为什么这样做

1. **派发方必须先迁 canonical 状态，再动手**。协作式暂停谓词（`pause_requested`）读的
   就是 canonical run 状态——"还停在 `PAUSED`"对 phase runner 就是"继续暂停"。第一版
   守护线程直接调 `resume_paused`：run 确实被续跑了，续跑体一进场就被自己的暂停谓词
   挡住，**一个任务都没执行**，e2e 抓到 `assert 1 == 2`（派发 1 个 run，runtime 只跑了
   1 次）。正确顺序与 `POST /runs/{id}/resume` 完全同序：`PAUSED → RUNNING` 并**先落库**
   → 续跑 → 把续跑结果如实写回（又停回 `PAUSED` 就写 `PAUSED`）。
   **判据**：任何"替用户按按钮"的组件，都要把那个按钮的完整副作用序列走一遍，而不是
   只调用被按钮包装的核心函数。
2. **会自己动手的组件必须可见、可控**。守护线程不响应用户请求就能改 canonical 状态，
   如果它不在读面里，运维看到的就是"run 自己变了，但系统里找不到任何会这么做的组件"。
   落地口径：新执行体进受控词表（`ScheduleJob` 的成员顺序即词表）、进内置定义
   （`ensure_builtins` 幂等补齐）、进 ops 读面的**回落事实**（没有 store 也能看到它存在）、
   进文档的合法 job 列表，并且**每个 cycle 的 API 用例镜像同步**（`_BUILTIN_NAMES`
   这类镜像与词表钉成一致）——否则"系统里多了一个会自己动的东西"这件事没有读面。
3. **到期判定只问一个读面**。任务投影**不携带** `retry_at`（期限只在任务行与
   `task.retry_scheduled` 事件里），所以"现在能不能再交付"只能问 adapter——比较用**权威
   时钟**（生产 DB 时钟 / 测试注入时钟），守护线程不自己拿墙钟去比。这与 MEM-20260915-054
   （退避与它的时钟）同源：写 deadline 的人和判 deadline 的人必须是同一个时钟。

## 怎么做与复现

```bash
python -B scratch/goal3-cycle19-probe1-unattended-parked-run.py         # 收口前/后对照
python -m pytest tests/e2e/test_retry_dispatch_full_loop.py -q          # 2 passed（真 SQLite + 注入时钟）
python -m pytest tests/application/ops/test_retry_dispatch_scheduler.py -q  # 6 passed
python -m pytest tests/adapters/sqlite/test_workflow_due_retries.py tests/postgres/test_workflow_due_retries_pg.py -q
```

写这类"自动续跑/自动重派"组件的检查清单：① 它的**判定输入**来自哪个读面？该读面是否
存在（不存在就先补读面，不要退化成"猜"）？② 它动手前要不要走完被代理的用户动作的**全部
副作用**（状态迁移、落库、审计）？③ 它进没进**受控词表 + 读面 + 文档**，运维能不能看到它、
停掉它？④ 没有能力完成时是否**诚实跳过**（本进程没有续跑上下文 ⇒ 跳过并计数，不伪装
成功、不偷偷执行）？⑤ 重复运行是否幂等（跑完再扫一轮应得 0）？

## 适用边界（踩过的坑）

- **跨进程仍不成立**：续跑上下文是进程内暂存，重启后守护线程**如实跳过**（`has_paused_context`
  为假），run 停在 `PAUSED` 等人工介入——没有假装"自动续跑已完成"。
- **用户暂停与重排停车仍同形**（都是 canonical `PAUSED`）：本守护线程靠**任务面**
  （`RETRY_SCHEDULED` 且有到期项）区分，不靠猜测；读面本身仍不区分两者。
- **多实例**：两个进程都跑守护线程时，重复 pass 至多一个真的取到上下文（另一个的
  `resume_paused` 会抛），但仍属"多实例共享同一 DB"的既有锁粒度边界。
- **自动续跑没有额外预算闸门**：`max_attempts` 是唯一预算（durable 判据），长退避会让
  run 长时间停着——与声明一致，不是 bug。
- 相关：[[MEM-20260915-056]]（终态会把声明好的续跑变成孤儿）、[[MEM-20260915-054]]
  （退避与它的时钟）、[[MEM-20260915-041]]（scheduler 仍是执行体）、[[MEM-20260915-053]]
  （声明了的状态 ≠ 会发生的状态）。

## 来源

- PLAN-20260915-082 / RECHECK-20260915-082（GOAL-20260915-003 cycle 19）。
