---
id: PLAN-20260929-247
slug: goal-026-ec02-lease-heartbeat-retry-backoff
title: GOAL-026 cycle 2（EC-02）：租约 / 心跳 / 重试分类 / 退避 —— 时钟注入两向 + 引擎路径轨迹 + 续租真的发生
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-026
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-026 的 **EC-02**（§7 义务「Task lease + heartbeat」「retry classification」
    「exponential backoff」的对抗性自检）。授权沿用该 GOAL 的 `authorization.ref`：
    范围 = 「**新增判据**（一律落 `tests/**`；落在既有 `python/tests` 收集面内 ⇒ m0 条数仍 `23`）」+
    「**测试侧夹具 / 探针**」+「修**被新判据证明为真缺陷**的问题（**只允许收紧**）」+
    「文档同源更新」；push-to-main-for-CI 口径（**只推 main**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**判据文件，**不修改**任何既有判据 / 夹具 / 门禁 / 阈值 / 放行面
    （点名：`tests/adapters/sqlite/test_workflow_engine.py`、`test_workflow_retry_policy.py`、
    `test_workflow_retry_backoff.py`、`test_workflow_acquire_backoff.py`、
    `tests/domain/test_retry_backoff.py`、`tests/worker/test_worker_loop.py`、
    `tests/contracts/test_claim_fencing_contract.py`、`tests/distributed/**`、
    `tests/postgres/**`、`tools/tooling_scripts_meet_product_gates.py` 的清单、`tests/egress_guard.py`）；
    **产品侧只在「只收紧」修复时才动**，且**必须**先有判据证明（本轮**未**触发该分支）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构；**零**新依赖；**全离线**（无真实出网）；
    测试数据一律**合成值**；**不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称 exactly-once。
exit_criteria:
  - id: AC-1
    criterion: >-
      **租约到期 ⇒ 回收 ⇒ 另一次 claim**：未到期时回收 **0** 条（正控制，证明回收不是空转）、
      任务仍 `LEASED` 且**抢不走**；越过 `expires_at` 后回收 **1** 条 ⇒ `QUEUED` ⇒
      二次 claim 成功且 **`fence` 前进**（不永久卡死）。
    status: PASS
  - id: AC-2
    criterion: >-
      **心跳挡住回收 + 停跳后按预期到期（两向）**：续租使 `expires_at` **推后**；越过**原始**
      `expires_at` 后回收 **0** 条、任务仍 `LEASED`、抢不走；越过**新** `expires_at` 后回收 **1** 条
      ⇒ 可再 claim。
    status: PASS
  - id: AC-3
    criterion: >-
      **重试分类按结构化字段分叉**：可重试类别 ⇒ `RETRY_SCHEDULED` 且落库 `retry_at`；
      **不可重试**类别 ⇒ `FAILED`、**无** `TASK_RETRY_SCHEDULED` 事件、`claim_next` 为 `None`
      —— 断言绑定 `FailureCategory` / 状态 / 事件类型，**不匹配错误文本**。
    status: PASS
  - id: AC-4
    criterion: >-
      **退避轨迹（引擎路径）单调不减 + 有上界 + 增长**：从 `tasks.retry_at` 的实际落库值取出
      连续 4 次失败的间隔，实测 **`[30, 60, 100, 100]`**（基数 30 / 上界 100 / `max_attempts` 5）
      ⇒ 单调不减、被上界封顶、且**确实增长**（常量退避会判红）。
    status: PASS
  - id: AC-5
    criterion: >-
      **重试预算耗尽 ⇒ 终止态**：第 5 次失败 ⇒ `DEAD_LETTER` 且 `claim_next` 为 `None`
      （接 EC-03 的死信面）。
    status: PASS
  - id: AC-6
    criterion: >-
      **worker 面续租真的发生**：处理一个作业后 `renew` **至少一次**，且携带被持有的
      **身份三元组**（`task_id` / `lease_id` / `fence`）；对照：无作业时 **零续租**。
    status: PASS
  - id: AC-7
    criterion: >-
      **按压两向 + 逐字节复原 + 四道门（承 MEM-152 / MEM-159）**：① 退避公式改常量 ⇒ 判红
      （实测 `[30,30,30,30]`）；② 去掉「类别不在 `retryable_categories` ⇒ FAIL」规则 ⇒ 判红
      （实测 `'RETRY_SCHEDULED' == 'FAILED'`）；两次复原后 `packages/domain/tasks.py` 的
      raw `sha256` 均回到基线；③ 四道门全绿；④ 既有判据**逐字节未改**；新判据**无 skip / xfail**。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-248-goal-026-ec02-lease-heartbeat-retry-backoff.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-168-reliability-clock-seam-trajectory-and-heartbeat-two-way.md
---

# GOAL-026 cycle 2（EC-02）：租约 / 心跳 / 重试分类 / 退避

## 目标

把 §7 的三项义务 —— 「**Task lease + heartbeat**」「**retry classification**」
「**exponential backoff**」—— 从「**代码里有**」推进到「**有判据证明它真的成立**」。
既有判据的缺口（建档实测，不是推测）：

1. 「心跳使 `expires_at` 变大」（`test_workflow_engine.py:76-88`）与「到期 + 回收 ⇒ 可再 claim」
   （`test_workflow_retry_policy.py:185-204`）**各证一半** ⇒ 无人证「**心跳真的挡住了回收**」；
2. 退避只在**纯函数层**采样三点 + 上界，引擎层只断言**第一次**延迟
   ⇒ 无人把**连续多次失败的实际落库轨迹**取出来证「单调不减 + 有上界」；
3. `tests/worker/test_worker_loop.py` 的 `_FakeClient` 记 `self.renews`，**却没有任何用例断言它非零**
   ⇒ 「续租线程真的跑了」从未被证。

## 验收条件

- [x] **AC-1 租约到期 ⇒ 回收 ⇒ 另一次 claim**（未到期回收 0 条 + 抢不走；到期后 1 条 + `fence` 前进）。
- [x] **AC-2 心跳挡住回收 + 停跳后按预期到期**（两向）。
- [x] **AC-3 重试分类按结构化字段分叉**（可重试 ⇒ `RETRY_SCHEDULED`；不可重试 ⇒ `FAILED` 且无重排事件）。
- [x] **AC-4 退避轨迹单调不减 + 有上界 + 增长**（实测 `[30, 60, 100, 100]`）。
- [x] **AC-5 重试预算耗尽 ⇒ `DEAD_LETTER`**。
- [x] **AC-6 worker 面续租真的发生**（非零 + 身份三元组；无作业时零）。
- [x] **AC-7 按压两向 + 逐字节复原 + 四道门**。

## 实施清单

- [x] **WP-1**：新增 `tests/adapters/sqlite/test_workflow_lease_lifecycle.py`（3 例：AC-1 / AC-2）。
- [x] **WP-2**：新增 `tests/adapters/sqlite/test_workflow_retry_trajectory.py`（2 例：AC-3 / AC-4 / AC-5）。
- [x] **WP-3**：新增 `tests/worker/test_worker_renew_loop.py`（2 例：AC-6）。
- [x] **WP-4**：产品侧按压 P1（退避常量）/ P2（不可重试类当可重试）⇒ 判红；
      raw `sha256` 逐字节复原 ⇒ 复绿；留档二进制写盘。
- [x] **WP-5**：四道门 + 定向套件 + 规模自查；写 `RECHECK-20260929-248` + `MEM-20260929-168`；
      回写 GOAL-026 的 EC-02 状态与迭代日志；投影 `ALL_PLAN`。

## 证据

- **实跑**：`uv run --frozen --no-sync python -B -m pytest
  tests/adapters/sqlite/test_workflow_lease_lifecycle.py
  tests/adapters/sqlite/test_workflow_retry_trajectory.py
  tests/worker/test_worker_renew_loop.py -q` ⇒ **7 passed**。
- **轨迹实测**：`tasks.retry_at` 落库的连续间隔 = **`[30, 60, 100, 100]`**
  （基数 30 / 上界 100 / `max_attempts` 5；第 5 次失败 ⇒ `DEAD_LETTER`）。
- **按压矩阵**（`scratch/goal026-ec02-press-matrix.log`，二进制写盘 / `CR` 计数 0 /
  `sha256 = 5b3f59959ecd9d54…`）：**P1** 退避公式 → 常量 ⇒
  `AssertionError: 退避轨迹实测: [30, 30, 30, 30]`；**P2** 去掉「不可重试类别 ⇒ FAIL」规则 ⇒
  `AssertionError: assert 'RETRY_SCHEDULED' == 'FAILED'`；两次复原后
  `packages/domain/tasks.py` 的 raw `sha256` 回到
  `358800b68ccb9fcb81313c1dec74942401ea777e9048fe24ba0428419c6a0106`（`MATCHES_BASELINE True`）。
- **判据自跑抓到本人两处写错**（如实记录）：`Timestamp` 是 dataclass 包装、**不支持排序比较**
  ⇒ 必须比较 `.value`（既有判据 `test_workflow_engine.py:86` 就是这么写的）；
  以及一处把 `expires_at` 与 `datetime` 直接相减。两处都改成**结构化比较**，**不是**放宽断言。
- **四道门**：`ruff format --check` = `3 files already formatted`；`ruff check` = `All checks passed!`；
  `mypy` = `Success: no issues found in 3 source files`；规模门参数化 = **3 passed**。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | DONE | 三个新判据文件（7 例）落地；AC-1…AC-7 全部 PASS；`RECHECK-20260929-248` = `PASS_WITH_WARNINGS`（`W-1`…`W-5`）；沉淀 `MEM-20260929-168`。**产品代码零净改动**（两次按压均逐字节复原）。 |

## 影响报告

- **改动**：新增三个判据文件（7 例）；记录面（PLAN / RECHECK / MEM / GOAL / ALL_PLAN / INDEX）。
  产品代码**零净改动**（按压后 raw `sha256` 复原）。
- **lint / typecheck / test**：四道门全绿；新判据 **7 passed**。
- **Domain / API / schema 变化**：**无**。
- **安全 / 凭据变化**：**无**（合成值；零真实内容 / token）。
- **兼容性 / 迁移风险**：**无**。
- **上游版本影响**：**无**（零新依赖）。
- **未覆盖范围与残余**：见 `RECHECK-248` 的 `W-1`…`W-5`（PG 侧到期类判据仍靠改行 / 真跑、
  分布式场景未在本轮射程、续租线程为守护线程故用有界等待、`heartbeat`/`complete` 不校验过期的
  边界未纳入判据、按压为产品级但**只**覆盖两个函数）与 `R-M1` 未收口。
- **下一项任务**：GOAL-026 EC-03（断路器 / 死信 / 取消）。
