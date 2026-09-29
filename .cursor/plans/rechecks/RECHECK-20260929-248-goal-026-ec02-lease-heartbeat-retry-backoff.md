---
id: RECHECK-20260929-248
slug: goal-026-ec02-lease-heartbeat-retry-backoff
title: GOAL-026 EC-02 复检：租约到期与心跳两向 + 引擎路径退避轨迹 + 续租非零（含产品级按压与逐字节复原）
plan_id: PLAN-20260929-247
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-248 — GOAL-026 EC-02 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`）。
**未实跑的不记通过**。

## 检查结果

### 1. AC-1 / AC-2 租约与心跳（实测，全部落 SQLite + 注入时钟）

- 交付：`tests/adapters/sqlite/test_workflow_lease_lifecycle.py`（**3 例**），TTL = 60s，
  时钟为模块内的可推进 `_Clock`（`SqliteWorkflowEngine(lease_ttl_seconds=60, now=clock)`）。
- **AC-1**：未到期时 `recover_expired_leases() == 0`（正控制 ⇒ 回收不是空转）、任务 `LEASED`、
  他 worker `claim_next` 为 `None`；推进 `61s` ⇒ 回收 `1` ⇒ `QUEUED` ⇒ 二次 claim 成功且
  **`fence == 2`**。
- **AC-2**：`heartbeat` 后 `expires_at.value` **strictly greater**；越过**原始** `expires_at`
  ⇒ 回收 `0`、仍 `LEASED`、抢不走（**心跳挡住回收**）；再越过**新** `expires_at` ⇒ 回收 `1`
  ⇒ 可再 claim。
- 读法：两条合起来才成立 —— 单独证「续租使到期变大」或单独证「到期可回收」都**不足以**排除
  「心跳只是把字段改了、回收逻辑根本不看它」这一形态。

### 2. AC-3 / AC-4 / AC-5 分类、轨迹与终止（实测）

- 交付：`tests/adapters/sqlite/test_workflow_retry_trajectory.py`（**2 例**）。
- **轨迹实测**：从 `tasks.retry_at`（**存储行**）取出连续 4 次失败的间隔 =
  **`[30, 60, 100, 100]`**（基数 30 / 上界 100 / `max_attempts` 5）⇒ 单调不减、
  被上界封顶、且**确实增长**（`gaps[1] > gaps[0]` 这一条把「常量退避」挡在外面）；
  第 5 次失败 ⇒ `DEAD_LETTER` 且 `claim_next` 为 `None`。
- **分类对照**：`VALIDATION_FAILURE`（不在 `retryable_categories`）⇒ `FAILED`、
  **无** `TASK_RETRY_SCHEDULED` 事件、`claim_next` 为 `None`。
  断言绑定 `FailureCategory` / 任务状态 / `EventType`，**不匹配错误文本**。
- **判据自跑抓到本人两处写错**（如实记录，非产品缺陷）：`Timestamp` 是 dataclass 包装、
  **不支持排序比较**（`TypeError: '>' not supported`）⇒ 改成比较 `.value`；
  另一处把 `Timestamp` 与 `datetime` 直接相减。两处都改成**结构化比较**，**未**放宽断言。

### 3. AC-6 续租真的发生（实测）

- 交付：`tests/worker/test_worker_renew_loop.py`（**2 例**）。
- 处理一个作业后 **`renew` 至少一次**，且集合恰为 `{("task-1", "lease-1", 1)}`
  ⇒ 续租携带的是**被持有的身份三元组**；对照：无作业时 `renews == []`。
- **判据用有界等待（≤5s）**：续租线程是守护线程、作业本身瞬间结束 ⇒ 不能假设它已被调度；
  这是**窗口**而非放宽（见 `W-3`）。

### 4. AC-7 按压 + 逐字节复原 + 四道门（实测）

**按压矩阵**（留档 `scratch/goal026-ec02-press-matrix.log`，二进制写盘 / `CR` 计数 0 /
`sha256 = 5b3f59959ecd9d54…`）：

| 按压 | 位置（**产品代码**） | 期望 | 实测红（原样） | 复原 |
| --- | --- | --- | --- | --- |
| **P1** 退避公式 → 常量 | `packages/domain/tasks.py` 的 `retry_delay`（`seconds = policy.backoff_seconds * (2 ** (attempt - 1))` → `policy.backoff_seconds`） | 判红 | `AssertionError: 退避轨迹实测: [30, 30, 30, 30]`（轨迹例红；对照例绿） | raw `sha256` 回到 `358800b68ccb9fcb81313c1dec74942401ea777e9048fe24ba0428419c6a0106`（`MATCHES_BASELINE True`）⇒ `2 passed` |
| **P2** 去掉「不可重试 ⇒ FAIL」 | `packages/domain/tasks.py` 的 `decide_failure`（删去 `category not in policy.retryable_categories` 那两行） | 判红 | `AssertionError: assert 'RETRY_SCHEDULED' == 'FAILED'`（对照例红；轨迹例绿） | raw `sha256` 回到同上基线（`MATCHES_BASELINE True`）⇒ **7 passed** |

- **两向**：两次按压中各只有**目标**用例红，另一例保持绿 ⇒ 「不该红时不红」。
- **复原逐字节**：两次都以 raw `sha256` 复核回到基线；`git status --porcelain -- packages/`
  只剩**与本 GOAL 无关**的既有 `model_drift.py` ⇒ 产品树净。
- **四道门**（三个新文件）：`ruff format --check` = `3 files already formatted`；
  `ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 3 source files`；
  规模门参数化 = `3 passed`（首次 `ruff format --check` 报 3 处待重排 ⇒ 按门格式化**本人新写的**文件）。
- **既有判据逐字节未改**；新判据**无 skip / xfail**。

## 结论

**EC-02 = PASS_WITH_WARNINGS**（`PLAN-20260929-247` 的 AC-1…AC-7 全部成立且有实跑证据）。
§7 三项义务在**单节点 SQLite + 注入时钟**的射程内**成立**：
「**Task lease + heartbeat**」（到期⇒回收⇒再 claim；心跳挡住回收；停跳后按预期到期）、
「**retry classification**」（两类按结构化字段分叉）、
「**exponential backoff**」（引擎路径实测 `[30, 60, 100, 100]`，单调不减 + 有上界 + 增长 + 耗尽进死信）。

**如实登记的警告（`W-1`…`W-5`）**：

- `W-1` 确定性判据全部落在 **SQLite**：PG 侧 `server_now` 让**假时钟无法推进**
  （`tests/postgres/test_workflow_retry_backoff_pg.py` 只能改写 `retry_at` 或真跑）
  ⇒ PG 的到期类语义本轮**只引用既有资产**，未新增判据；
- `W-2` **分布式 / 跨进程**租约场景（`tests/distributed/**`，需 PG + 子进程 + 墙钟等待）
  **不在本轮射程**；
- `W-3` 续租判据用**有界等待**（守护线程 + 瞬时作业 ⇒ 调度窗口），不是确定性 join：
  极端负载下存在极小概率的假红窗口（如实登记，**不是** skip）；
- `W-4` 实测到的**适配器分歧**未纳入判据：`heartbeat` 两个适配器都**不校验**租约是否已过期
  （可复活未回收的过期租约），且 SQLite `complete` **不校验过期**而 PG 校验
  （`adapters/sqlite/workflow_ops.py:233-264,284-296` vs `adapters/postgres/workflow_ops.py:34-51,125-128`）
  —— 这属**语义面变更**，本轮**只登记**，不改判据也不改产品；
- `W-5` 两次按压都是**产品级**，但只覆盖 `retry_delay` / `decide_failure` 两个函数；
  租约与心跳两条 AC 的按压未做（改适配器回收 / 续租逻辑风险更高 ⇒ 只登记）；
- `R-M1` 未收口（Mimosa 钩子 `scanner_enobufs` 未得完整结论）⇒ **不得**据此宣称项目安全。

**未覆盖范围（承 GOAL-026）**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
`R-M1` 未收口。
