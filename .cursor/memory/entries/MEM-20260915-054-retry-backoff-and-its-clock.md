---
id: MEM-20260915-054
title: "重排 ≠ 立刻再派发：退避要落在同一权威时钟上，且比较必须发生在候选扫描内"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-079-retry-backoff-after-reschedule.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-079-retry-backoff-after-reschedule.md
supersedes: []
tags:
  - retry
  - backoff
  - workflow-engine
  - clock
  - claim
---

# 重排 ≠ 立刻再派发

## 做了什么

上一轮（PLAN-20260915-078）让 `RETRY_SCHEDULED` 与 `QUEUED` **同权**之后，"排了下一次
尝试"等于"现在就能再被取走"：失败很快的任务会在 `max_attempts` 内**热循环**，占满 worker
与外部配额。而 AGENTS.md §7 要求的 "exponential backoff" 在策略面**连字段都没有**
（`retryPolicy` 只有 `max_attempts` + `retryable_categories`，schema `additionalProperties:
false`），所以当时只能如实登记"没做"。

本轮补上：策略面两个可选字段（`backoff_seconds` 基数、`max_backoff_seconds` 上限）→
Domain 纯函数 `TaskContract.retry_delay(attempt)` = `min(base * 2^(attempt-1), cap)` →
`tasks.retry_at` 列 → 两个 adapter 的 claim 在**候选扫描内**过滤未到期的重试 → 交付时清回
NULL。没写字段 = 立即重排（既有契约行为不变）。

## 为什么这样做

1. **时延属于策略面，不属于适配器**：写死常量等于替契约发明语义。加字段才叫"能声明退避"。
2. **deadline 的写入与比较必须是同一个时钟**：PG 侧最初写成 SQL 的 `now() + interval`，
   而 claim 的比较用 `server_now(conn, now)`（生产 = 数据库时钟、测试 = 注入时钟）——
   两者在测试里立刻分叉（deadline 落在假时钟的过去，任务被当成"没在等退避"）。
   收敛成"写入也走 `server_now`"，一处来源。
3. **过滤要在扫描内**：候选查询先取再丢会和 PAUSED run 的处理走反——一个没到期的重试会
   占满候选窗口，把别的 run 的可派发任务饿死。
4. **交付即清 `retry_at`**：一次交付就是一个时刻，残留的过去 deadline 虽无害，但会让
   "这条任务在等什么"这个读面事实变得含糊。

## 怎么做与复现

```bash
python -m pytest tests/domain/test_retry_backoff.py -q                            # 7 passed
python -m pytest tests/adapters/sqlite/test_workflow_retry_backoff.py -q          # 4 passed
python -m pytest tests/postgres/test_workflow_retry_backoff_pg.py -q              # 3 passed（parity）
```

改动这类"时间相关的门"时的检查清单：① 时延/期限要么来自策略面、要么来自显式常量，
不写进 adapter；② deadline 的写入与比较**同一个时钟源**（本仓：`server_now` /
`timestamp_now`，生产读库、测试注入）；③ 过滤放进候选扫描，不要取到再丢；④ 交付/完成时把
一次性字段清掉；⑤ 缺省值必须等于"字段出现之前的行为"，否则既有契约悄悄变语义。

## 适用边界（踩过的坑）

- **只覆盖 durable 层**：应用层 `task_executor` 的 in-process 重试循环仍立刻重试，且它用
  局部 `attempts` 计数——同一个 `max_attempts` 目前是**两套账**（未统一，已登记）。
- **没有 jitter**：同一批任务会在同一时刻集中到期；策略面没有 jitter 字段，不发明语义。
- **上限是硬约束**：`max_backoff_seconds < backoff_seconds` 直接拒——否则 cap 会静默压基数。
- **"零消费者"要限定层**（上一轮的教训，见 [[MEM-20260915-053]]）：说某配置没人用时必须
  写清"哪一层没人用"，本轮的校正就是这么来的。
- 相关：[[MEM-20260915-047]]（声明了却没人消费的配置是一种谎言）、
  [[MEM-20260915-053]]（声明了的状态 ≠ 会发生的状态）。

## 来源

- PLAN-20260915-079 / RECHECK-20260915-079（GOAL-20260915-003 cycle 16）。
