---
id: RECHECK-20261008-344
slug: goal-037-ec04-idempotent-advance-and-restart
title: 独立复检：GOAL-037 cycle 4（EC-04）编排步的幂等与中断
plan_id: PLAN-20261008-343
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-344 — GOAL-037 cycle 4（EC-04）独立复检

复检对象：`PLAN-20261008-343`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 同键重放（AC-1）

| 读法 | 读数 |
| --- | --- |
| 判据 | `tests/e2e/test_program_idempotency_on_the_run_path.py::test_replaying_the_same_key_is_byte_identical_and_does_not_duplicate` **passed** |
| 断言 | `replay == first`（响应体相等）+ run 数 1 + 决策数 1 |
| 承载 | 既有 `IdempotencyMiddleware`（本 cycle **未新增产品面**）—— 直接读 `services/api/middleware.py` 的 replay 分支复核 |

### 2. 新事实推进 / 崩溃窗口 / 重启重入（AC-2）

| 读法 | 读数 |
| --- | --- |
| 不同键 | 第 1 次 `START`、第 2 次 `CONTINUE`、`started_run_id` 不同、run 数 2（**passed**） |
| 崩溃窗口 | 预置「决策已落、run 未落库」⇒ `DEDUP`、`started_run_id is None`、run 数仍 1、`cited_run_id` == 幽灵 id（**passed**） |
| 重启重入 | 新 `TestClient(create_app(deps))` ⇒ 读面 run 数 1，推进落 `CONTINUE`、run 数 2（**passed**） |
| 承载复核 | 驱动判定只读 `runs.for_program` / `programs.decisions_of` ⇒ 进程内零记忆（读源码） |

### 3. 口径守卫（AC-3）

| 读法 | 读数 |
| --- | --- |
| 机械面 | `tests/architecture/python/test_delivery_semantics_wording.py` **6 passed**（无新增 `AFFIRMATIVE`；CJK lemma 零命中面不变） |
| 记录面 | 两个记录文件里 `at-least-once` + 幂等 在场 + 「恰好一次」的**否认**形态在场（判据自证） |
| 口径 | 只有 **at-least-once + idempotency + deduplication**；**明确否认**「恰好一次」（本 cycle 不新增任何相反表述） |

### 4. 门链与记录面（AC-4）

`ruff check` / `format --check`（1171 files）/ `mypy`（1161 files）/ 规模门 **全绿**；
新增判据 **5 passed**；as-is m0 与治理读数见 GOAL 迭代日志 cycle 4 行。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立；**无产品缺陷**
（本 cycle 零产品改动：既有中间件与驱动已提供全部机制，本轮把它们**变成可复核事实**）。

### Warnings

- **W-1（判据只断可观测事实，不断言「不存在重复投递」）**：at-least-once 的**含义**就是
  允许重复投递；本文件断言的是「重复到达时**不重复副作用**」（同键逐字节相同 / 崩溃窗口
  不产生第二个 run）。把判据写成「绝无重复」会**超出机制**并违反口径。
- **W-2（崩溃窗口的取证形态是预置的）**：`DEDUP` 用例手工写入一条形态真实的 `CONTINUE`
  决策（`cited_run_id` 指向幽灵 run），而不是真去杀进程 —— 判的是**判定逻辑**对
  「决策已落、run 未落库」这一事实的响应；真杀进程属 infra 面（既有配方不在本 cycle）。
- **W-3（承继残余原样保持）**：GOAL-036 的 `M-1`…`M-5`、`R26-*` 终态、未覆盖范围逐条保持；
  **不得**据此宣称项目安全；**不得**宣称投递语义为那四个字（**明确否认**）。
