---
id: MEM-20260915-055
title: "一次尝试一套账：同一次执行的两套计数器，会让预算变成乘法"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-080-one-attempt-ledger-in-process-retry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-080-one-attempt-ledger-in-process-retry.md
supersedes: []
tags:
  - retry
  - attempt
  - budget
  - ledger
  - canonical-state
---

# 一次尝试一套账

## 做了什么

cycle 15/16 让 durable 层按"交付代次"数 `attempt` 并据此判重排/死信，但应用层的
`execute_task` 一直在用**自己的局部计数** `attempts`（上限同样是 `max_attempts`）。
两层各算各的，结果是**预算变乘法**——探针实测（`scratch/goal3-cycle17-probe1-two-ledgers.py`）：

```text
收口前：max_attempts=3 backoff=None  → 一次调用跑 3 次，3 次交付共 9 次，任务停在 LEASED
        max_attempts=3 backoff=3600  → 退避声明无效，照样立刻跑满 3 次
收口后：max_attempts=3 backoff=None  → 总共 3 次，任务落 DEAD_LETTER（attempt=3）
        max_attempts=3 backoff=3600  → 一次调用只跑 1 次，任务留 RETRY_SCHEDULED（带 deadline）
```

收口：尝试序号取 durable 的交付代次（`lease.fence`）；每次失败先
`complete(FAILED, failure_category=...)` 落账，再由 durable 判据决定重排/死信；声明了退避
就把下一次尝试**交回派发方**（进程内不自旋）；`acquire_lease` 与 `claim_next` 一样守
`retry_at`（此前只有 claim 守，"deadline 之前不得交付"只在一个入口成立）。

## 为什么这样做

1. **计数器的"权威"必须唯一**：两个计数器各自"正确"时，系统行为仍然是错的（乘法）。
   问"这个数谁说了算"比问"这个数对不对"更能抓到问题。
2. **失败不落账 = canonical state 说谎**：收口前失败路径从不 `complete`，任务停在
   `LEASED`，而 durable 的 `RETRY_SCHEDULED`/`DEAD_LETTER`/退避**一个都够不着**——
   声明得再完整也没有执行路径走进去。
3. **退避是 durable 的事实**：进程内自旋会绕过 deadline。正确做法是"把下一次尝试交回
   派发方"，而不是在进程里 `sleep`（worker 被一个长退避钉住比失败更糟）。
4. **不变量要在每个入口成立**：cycle 16 只在 `claim_next` 的候选扫描里过滤了 `retry_at`，
   按 task_id 的 `acquire_lease` 仍能把没到期的任务租出去——与 cycle 13/14 的教训同源
   （"哪个入口还没守"必须枚举，见 [[MEM-20260915-051]]）。

## 怎么做与复现

```bash
python -B scratch/goal3-cycle17-probe1-two-ledgers.py                                     # 收口前/后对照
python -m pytest tests/application/run_orchestration/test_execute_task_one_ledger.py -q    # 3 passed
python -m pytest tests/adapters/sqlite/test_workflow_acquire_backoff.py -q                 # 2 passed
python -m pytest tests/postgres/test_workflow_acquire_backoff_pg.py -q   # 2 passed（PG 可达时）
python -m pytest tests/application/run_orchestration -q                                    # 26 passed（既有用例未改断言）
```

改这类"谁数数"的地方时的检查清单：① 先问"这个计数器谁说了算"，同一事实只允许一个权威；
② 失败路径必须**落账**，否则 canonical state 会停在最后一个写入者留下的状态；
③ 期限/退避由权威层持有，进程内不 `sleep`、不自旋；④ 新不变量要在**每个入口**都守
（列出全部交付入口再逐个检查）；⑤ 心跳会轮换租约标识——失败落账必须用**心跳之后**的租约。

## 适用边界（踩过的坑）

- **dispatch 侧仍缺**：退避 > 0 时把重试交回派发方，但对 AGENT_SESSION 任务，phase runner
  的失败语义是"任务失败 ⇒ run 失败"，没有派发方会再来取 ⇒ "声明了退避的重排"目前是
  "状态正确但没人执行"。如实登记，未假装闭环。
- **session 级失败没有类别**：`AgentSessionResult` 不带 failure category ⇒ 完成时不带类别
  ⇒ durable 按"不可判定"处理（FAIL，保守）。要支持它走重试策略，得先给会话结果一个类别来源。
- **预算用尽时不执行**：进入循环时交付代次已 ≥ `max_attempts` ⇒ 这次调用一次都不跑、
  直接判用尽（与语义一致，但读日志时要知道这条路径存在）。
- 相关：[[MEM-20260915-053]]（声明了的状态 ≠ 会发生的状态）、
  [[MEM-20260915-054]]（退避要落在同一权威时钟上）、[[MEM-20260915-047]]（声明了却没人消费）。

## 来源

- PLAN-20260915-080 / RECHECK-20260915-080（GOAL-20260915-003 cycle 17）。
