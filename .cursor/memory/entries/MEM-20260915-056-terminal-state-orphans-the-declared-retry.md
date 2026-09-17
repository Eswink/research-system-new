---
id: MEM-20260915-056
title: "终态会把声明好的续跑变成孤儿：'现在不能跑'与'跑不了'必须分开表达"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.92
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-081-parked-retry-run-level-redispatch.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-081-parked-retry-run-level-redispatch.md
supersedes: []
tags:
  - retry
  - run-state
  - terminal-state
  - park-and-resume
  - typed-errors
---

# 终态会把声明好的续跑变成孤儿

## 做了什么

cycle 17 让"退避 > 0"的任务落 `RETRY_SCHEDULED`（带 `retry_at`），把下一次尝试交给
派发方。cycle 18 的探针量出：对 AGENT_SESSION 任务**没有派发方**——同一场景下

```text
收口前：phase runner 返回 = FAILED / on_pause 拿到 0 条 specs / FAILED 之后 RESUME = InvalidTransitionError
        （durable 侧其实是好的：任务 RETRY_SCHEDULED、deadline 前 acquire 拒绝、到期后能租到 fence=2）
收口后：phase runner 返回 = PAUSED / on_pause 拿到 1 条 specs / RESUME = 合法 → RUNNING
```

收口做法：把"重排未到期"与"这次尝试失败"分开表达——执行器给结果打 `retry_deferred`，
phase runner 据此**停车**（`PAUSED`，把失败任务与其后所有 specs 经 `on_pause` 交回），
而不是判 run 失败；deadline 守卫从裸 `InvalidInputError` 细分出子类 `RetryNotDueError`，
让调用方能区分"现在不是交付时机"和"这个任务交付不了"。

## 为什么这样做

1. **终态是承诺的坟场**：`FAILED` 没有出边（`FAILED --RESUME-->` 不在迁移表里），
   一旦落进去，durable 侧那条 `RETRY_SCHEDULED` 就再没有任何入口能再来取——**声明得
   再完整也无法兑现**。判断"还能不能被继续"这件事，先看状态机有没有出口。
2. **"不能跑"和"现在不能跑"是两种语义**：前者该失败，后者该等。用一个错误类型（甚至
   一条字符串）表达两件事，调用方就只能二选一：要么把可重试的失败当永久失败，要么把
   永久失败当可重试——cycle 18 之前正是前者（早到的 resume 会把 run 弄死）。
3. **别造第二套机制**：仓内已有 `PAUSED`/`RESUME` + `on_pause` 暂存上下文 + resume 续跑
   （PLAN-048 的协作式暂停）。重排停车与它同构 ⇒ 复用它，只在"谁触发 resume"上不同。
4. **交回的东西要以失败任务开头**：只交回"后面的" specs 会让 resume 跳过真正要重试的
   那个任务——续跑的上下文必须从断点本身开始。

## 怎么做与复现

```bash
python -B scratch/goal3-cycle18-probe1-parked-retry.py                       # 收口前/后对照
python -m pytest tests/e2e/test_retry_park_and_resume.py -q                  # 5 passed（真 SQLite + 注入时钟）
python -m pytest tests/application/run_orchestration/test_parked_retry.py -q # 4 passed
```

做这类"自动续跑"改动时的检查清单：① 列出这条重试路径的**终态出口**（run 状态机是否
允许再进来）；② 把"现在不能跑"单独表达（类型化错误 / 显式标志），别混进失败；③ 续跑
上下文要包含**断点本身**及其后全部工作；④ 到期判定只认一个权威时钟/字段；
⑤ 对照组要有：无策略、有策略无退避，证明既有语义没被顺手改掉。

## 适用边界（踩过的坑）

- **没有自动派发方**：本轮交付"停车 + 有人/控制面触发就能真的跑完"，**没有**调度器按时
  自动 resume ⇒ 长退避会一直停着（下一轮首选项）。
- **进程内暂存**：续跑上下文与 PLAN-048 同源，进程重启后 resume 诚实报 `continuation=NONE`，
  不假装能跨进程续跑。
- **两种 PAUSED 读面不区分**：用户暂停与重排停车都是 `PAUSED`；要区分得读任务面
  （`RETRY_SCHEDULED` + `retry_at`）或事件流。
- **预算预留跟着停车挂着**（终态才释放）——重试需要预算，这是有意的。
- 相关：[[MEM-20260915-055]]（一次尝试一套账）、[[MEM-20260915-053]]（声明了的状态 ≠
  会发生的状态）、[[MEM-20260915-051]]（边界要枚举）。

## 来源

- PLAN-20260915-081 / RECHECK-20260915-081（GOAL-20260915-003 cycle 18）。
