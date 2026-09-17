---
id: MEM-20260917-065
title: "续跑失败要补偿：pop 掉的暂停上下文不复活、放回 PAUSED + 事件链记原因、补偿后被 409 挡住才算修好"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-090-resume-failure-compensation.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-090-resume-failure-compensation.md
supersedes: []
tags:
  - run-orchestration
  - resume
  - compensation
  - canonical-state
  - domain-events
---

# 续跑失败：从悬空 RUNNING 到补偿回停车

## 做了什么

`resume_paused` 执行失败后，**canonical run 被放回 `PAUSED`**（既有域迁移 `PAUSE`）并发
`run.resume_failed`（payload：`failure_type` / `message` / `compensated_to`）。两条入口
（API `POST /runs/{id}/resume` 与守护线程 `RetryDispatchScheduler._resume`）共用同一个
补偿函数（`run_terminals.compensate_failed_resume`），差别只在由谁落库。API 多一种结局
`continuation=FAILED`（+ 原因 + `dispatch=HELD`）。

## 为什么这样做

1. **悬空 `RUNNING` 是死路**：`resume_paused` **先 pop 上下文再执行**（`service.py`），
   执行抛错后上下文已丢；此时 run 停在 `RUNNING` ⇒ 守护线程只派发 `PAUSED`（不会来救），
   `POST /resume` 的 `PAUSED → RUNNING` 迁移会 **409**（也不能重试）。除了人工改库，
   没有任何入口能再推进它。
2. **失败不是终态**：所以不是 `run.failed`（那会让 run 终结）。补偿 = 回到"可重试的停车
   态"，而不是把这次失败升级成终局。
3. **原因只在事件链**：run 行没有"停车原因"字段（GOAL-004 cycle 2 明确拒绝过那个方向），
   事件链本来就是 run 事实的 canonical 记录 ⇒ `run.resume_failed` 是唯一的落点。

## 怎么做与复现

```bash
python -m pytest tests/api/test_resume_compensation_api.py -q                 # API 补偿 + 事件 + 可重入
python -m pytest tests/application/ops/test_retry_dispatch_scheduler.py -q    # 守护线程补偿 + 下一轮可续
```

反证：`approvals.py` 的补偿分支换成 `raise` ⇒ 前两条 API 用例红；守护线程的
`self._compensate_failed_resume(...)` 换成 `return 0` ⇒ 调度器两条新用例红
（失败文本正是旧行为 `RUNNING != PAUSED`）。

## 适用边界（踩过的坑）

- **同形的坑还有一处（未修，登记为告警）**：`resume_after_approval` 也是"先 pop
  `_waiting` 再执行"，失败后上下文同样丢失——只是它停在 `WAITING_FOR_APPROVAL` 而不是
  `RUNNING`，不在 EC-06 的判据里。
- **上下文不会"复活"**：本 PLAN 不改 pop 语义，所以补偿后的重入走 **durable 重建**
  （冻结正文 + 来源），没有冻结正文的旧 run 重入仍被诚实拒绝。
- **数量级/替身手法**：注入失败用实例级替身（`deps.runs.has_paused_context = lambda…`），
  只替换执行侧，补偿跑真实现（真迁移 + 真事件发布）——否则"补偿真的写进 canonical"这条
  断言会退化成测替身。
- **450 行硬上限继续决定代码位置**：`service.py` 到顶 ⇒ `_pending_human_gates` 搬去
  `human_gates.py`；`scheduler.py` 到顶 ⇒ `LeaseRecoveryScheduler` 搬去
  `lease_recovery.py`（`PeriodicDaemon` 留在原处，避免搬迁基类）。
- **未 pin DSN 的合并跑会出现假红**：`tests/api` 等混合套件在未 pin `RESEARCHOS_POSTGRES_DSN`
  时会因 operator `.env` 注入的 DSN 出现 3 条组合用例失败；隔离复跑 + pin 后复跑均绿
  （按"环境问题"处置，不记为缺陷）。
- 相关：[[MEM-20260917-064]]（派发读面）、[[MEM-20260917-060]]（停车语义读面）、
  [[MEM-20260915-047]]（声明要有消费者）。

## 来源

- PLAN-20260917-090 / RECHECK-20260917-090（GOAL-20260917-004 cycle 7 = EC-06）。
