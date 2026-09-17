---
id: RECHECK-20260917-090
plan_id: PLAN-20260917-090
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-004-cycle7
baseline_ref: 0fbce45
checked_head: 56a93e8+worktree
---

# RECHECK-20260917-090 — 续跑失败补偿（GOAL-004 cycle 7 = EC-06）

## 检查范围

PLAN-20260917-090 声称的交付面：`resume_paused` **执行失败**时不留悬空 `RUNNING`——
canonical 被放回 `PAUSED`（既有域迁移，不发明新状态）、失败原因进**事件链**
（`run.resume_failed`，唯一 canonical 记录）、两条入口（API `POST /runs/{id}/resume`
与守护线程 `RetryDispatchScheduler._resume`）共用同一处补偿、补偿后可重入（再次续跑能成功）。

**不在本 PLAN**：`resume_after_approval`（另一条 pop 语义的入口，停在
`WAITING_FOR_APPROVAL`，见 W-1）与"进程内暂停上下文复活"（pop 语义保持不变，重入走重建路径）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| API 失败即补偿（AC-01） | API 用例：实例级替身让 `resume_paused` 抛 `RuntimeError` ⇒ 响应 `continuation=FAILED` + 原因 + `dispatch=HELD` + `state=PAUSED`，且**从 store 读回的 run 行**是 `PAUSED` | PASS |
| 原因可从 canonical 事实读到（AC-03） | 同用例从 `GET /runs/{id}/events` 读回 `run.resume_failed`：`run_id` / `failure_type=RuntimeError` / `message` / `compensated_to=PAUSED`；且**只有一条**（重入成功不再记） | PASS |
| 可重入（AC-04） | 同文件第二条用例：失败一次（行回到 `PAUSED`）⇒ 撤掉失败注入再 `POST /resume` ⇒ **200 + `continuation=RESUMED` + 行 `RUNNING`**（悬空 `RUNNING` 时这条会被 409 挡住，是本判据的分界线） | PASS |
| 守护线程失败即补偿（AC-02） | 调度器单测：`runs.boom=True` ⇒ `_execute_pass()` 返回 0、补偿记录 `(run_id, "RuntimeError")`、store 写入序列 `[RUNNING, PAUSED]`；另一条用例证明**下一轮 pass 真的把它续起来**（返回 1、store 末条 = 续跑结果） | PASS |
| 不中断整轮 | 既有用例（读面 boom ⇒ 本轮 0 且不动状态）继续绿；本轮未改"单 run 失败不拖垮整轮"的约定 | PASS |
| 既有语义不变 | `test_pause_resume_api.py`（含无上下文 → `continuation=NONE`）、`test_api_restart_recovery.py`、`tests/e2e` 全绿；新增用例另钉"没有暂停上下文 ⇒ 走重建路径且**不记**失败事件"与"竞态（`InvalidInputError`）仍是既有回答、不记失败事件" | PASS |
| 词表同步 | `EventType` 36 → 37；`DOCUMENTED_EVENT_TYPES` + 计数断言同步；`EVENT_MODEL.md` 词表与一段口径说明（为什么不是 `run.failed`、为什么读面不加原因字段） | PASS |

## 反证与实测

- **反证 ①（API 补偿）**：把 `approvals.py` 补偿分支换成 `raise` ⇒
  `test_a_failed_resume_is_compensated_and_the_reason_is_canonical` 与
  `test_the_compensated_run_is_not_bricked` **2 红**（异常直接冒成 500，run 留 `RUNNING`），
  撤掉后复绿。
- **反证 ②（守护线程补偿）**：把 `_resume` 的 `self._compensate_failed_resume(...)` 换成
  `return 0` ⇒ 调度器 **2 红**，失败文本正是旧行为（`'RUNNING' != 'PAUSED'`），撤掉后复绿。
- **450 行硬上限两次决定代码位置（本改动引入）**：`service.py` 加方法后 449 → 451 行 ⇒
  `_pending_human_gates` 搬 `human_gates.py`（纯函数，`run_id` 由调用方显式传入——原实现从
  `context.run.id.value` 取）。`scheduler.py` 加补偿方法后 465 行 ⇒ `LeaseRecoveryScheduler`
  搬 `lease_recovery.py`（`PeriodicDaemon` 基类留在原处，避免搬迁基类；`app.py` 与
  `tests/distributed/worker_harness.py` 的 import 同步）。**未改门禁、未改断言强度**。
- **未 pin DSN 的组合跑出现 3 条假红**：`tests/api tests/application tests/e2e tests/domain
  tests/contracts` 一次性跑（无 DSN pin）时 `test_worker_plane_composition.py` 3 条失败；
  隔离复跑 **6 passed**、按固化配方 pin `RESEARCHOS_POSTGRES_DSN` 后同一条命令 **1993 passed
  / 4 skipped** ⇒ 判定为环境（operator `.env` 注入 DSN）而非本改动，未记为缺陷。
- **补偿必须跑真实现**：API 用例只替换执行侧（`has_paused_context` / `resume_paused`），
  补偿走真迁移 + 真事件发布并**从 store/事件面读回**验证——否则"写进 canonical"这条断言
  退化成测替身。

## 告警

- **W-1（同形入口未修：`resume_after_approval`）**：审批通过后的续跑同样**先 pop
  `_waiting` 再执行**（`service.py`），执行失败会丢掉上下文，run 停在 `WAITING_FOR_APPROVAL`
  且 `_resume_after_approval` 对非 `InvalidInputError` 不补偿（异常冒给审批端点）。它不在
  EC-06 的判据（悬空 `RUNNING`）内，本 PLAN 不动；登记为后继入口（补偿形状可直接复用）。
- **W-2（上下文不复活）**：补偿只改 canonical，进程内暂停上下文已被 pop ⇒ 重入走
  **durable 重建**（需要冻结正文/来源）。没有冻结正文的旧 run 失败后会被拒绝（重建路径的
  既有边界），此时"可重入"表现为"能再尝试且拒绝原因可见"，不是"必然成功"。
- **W-3（失败原因不含任务级归因）**：事件 payload 只有异常类型与文本（`message`），没有
  失败任务/phase 归因；要"哪一步炸的"仍需读 run 的事件链上下文（本 PLAN 未扩展）。
- **W-4（守护线程补偿失败静默降级）**：`_compensate_failed_resume` 内部 `except: pass`
  （store 不可用时本 pass 放弃、下一轮重评估）。这是既有的"单 run 失败不拖垮整轮"约定，
  但**补偿失败本身不在读面**——遥测/log 之外没有 canonical 痕迹（下一轮若成功会再记一条
  `run.resume_failed`）。
- **W-5（API 响应仍是 200）**：续跑失败返回 `200` + `continuation=FAILED`（与 `NONE`/`REBUILT`
  同形状），调用方必须以 `continuation` 判断结局；如需更强的传输层信号（5xx）属产品决策。

## 门禁

- 定向：`tests/application/ops/test_retry_dispatch_scheduler.py` **11 passed**；
  `tests/api/test_resume_compensation_api.py` **4 passed**；`tests/api tests/application
  tests/e2e tests/domain tests/contracts`（DSN pin）**1993 passed / 4 skipped**（233.21s）。
- 类型/风格：`mypy` **920 source files** 无问题；ruff check/format 绿；
  `tests/tooling/test_python_source_limits.py` **930 passed**（两处搬迁后两个文件均达标）。
- web 门：lint / typecheck / unit **76** / build / stub e2e **83** / live e2e **36** 全绿。
- m0：首跑 22/23（唯一红项 = `framework/validate` 报"MEM-065 引用的 RECHECK-090 尚不存在"
  ——记录顺序问题，本文件为该红项的直接修复）；其余 22 项含 `python/tests` **3896 passed /
  10 skipped**（562.60s）；补齐记录后复跑见迭代日志第 7 行。

## 结论

`resume_paused` 失败不再是"悬空 `RUNNING`"：两条入口共用一处补偿，把 canonical 放回
`PAUSED`（既有域迁移）并把失败原因写进事件链（`run.resume_failed`，读面不新增原因字段）。
API 面多一种如实结局（`continuation=FAILED` + 原因 + `dispatch=HELD`），守护线程面补偿后继续
服务本轮其余 run。补偿**不是终局**：撤掉故障后同一入口能把它真的续起来（用例里真的跑到
`RUNNING`）。

结果为 **PASS_WITH_WARNINGS**：W-1 是同形入口 `resume_after_approval` 未修，W-2…W-5 是
"上下文不复活、失败无任务级归因、守护线程补偿失败静默降级、响应仍 200"四条如实边界。
**未宣称**：失败原因能定位到具体任务/phase，或补偿在所有 store 故障下都必然成功。
