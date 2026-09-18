---
id: RECHECK-20260918-105
plan_id: PLAN-20260918-105
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-cycle6
baseline_ref: ca4bb05
checked_head: WORKTREE
---

# RECHECK-20260918-105 — 续跑失败的诚实边界 (b)（GOAL-006 cycle 6 = EC-06）

## 检查范围

EC-06 是**二选一终态**（RECHECK-090 W-3 / W-4 / W-5）。本轮选 **(b) 一等边界 + 降级可见**，
两条要求逐条对表：

| EC 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| (b) ① 把「哪一步炸的仍需读事件链上下文」登记为**一等边界**（文档同源） | `docs/architecture/EVENT_MODEL.md` + `docs/api/CONTROL_PLANE_API.md` 两处写明 payload **不含任务级归因** | `tests/application/run_orchestration/test_resume_compensation_failure_event.py::test_both_docs_state_the_attribution_boundary` |
| (b) ② 守护线程补偿失败的**静默降级**做成读面可见（canonical 事件或读面字段） | 新事件 `run.resume_compensation_failed`（`EventType` 追加成员 + `run_terminals.publish_compensation_failure` + 服务薄封装 + 守护线程失败路径先发后吸收） | 读面：`tests/api/test_compensation_failure_visibility_api.py`（真调度一轮 + `GET /runs/{id}/events`）；形状：`test_resume_compensation_failure_event.py`；接线：`tests/application/ops/test_retry_dispatch_scheduler.py` |
| 「不得只留在遥测/log」 | 旧路径 `except: pass` 已改：先发 canonical 事件再吸收；地板（连事件都发不出去）显式登记 | `test_even_an_unpublishable_failure_event_does_not_break_the_pass`（地板语义仍不中断整轮） |
| W-5「响应仍 200」属产品决策 | **不改**，只如实登记（`CONTROL_PLANE_API.md` 一等边界 ②） | 文档同源判据（本轮不新增行为） |
| 既有语义不变 | 补偿成功路径、整轮不中断、可重入、无 `RUNNABLE` 伪造 | `tests/api/test_resume_compensation_api.py`（4 条，未改）+ 调度器 11 条既有用例 |

## 检查结果

### (b) ② 补偿失败留痕

- **形状**：`run_terminals.publish_compensation_failure(publish, run_id, failure, canonical_state)`
  发 `EventType.RUN_RESUME_COMPENSATION_FAILED`（线上串 `run.resume_compensation_failed`），
  payload 键 **`run_id` / `failure_type` / `message` / `canonical_state`**——`failure_type` /
  `message` 描述的是**补偿**这次的失败（最初那次续跑失败仍由 `run.resume_failed` 记录），
  `canonical_state` 是补偿失败时 run 仍停在的状态（**没有**被伪造成 `PAUSED`）。
- **接线**：`services/api/scheduler.py::_compensate_failed_resume` 的 `except` 分支先
  `self._runs.publish_compensation_failure(run_id, exc, resumed.state)`，再吸收异常（整轮不中断
  的既有语义不变）；服务侧 `RunOrchestrationService.publish_compensation_failure` 是薄封装
  （事件构造只有一处）。
- **读面**：`GET /runs/{id}/events`（既有 SSE + JSON replay 读面）⇒ 不需要新 DTO 字段、
  不动 OpenAPI 快照。API 用例真的跑一轮 `RetryDispatchScheduler`（真 service + 真事件发布），
  只把**补偿的落库**打坏，事件即出现在读面上。

### (b) ① 归因边界

- 两处文档都写明「**不含任务级归因**」：`EVENT_MODEL.md`（词表 + 两个 resume 事件段的语义与
  边界）与 `CONTROL_PLANE_API.md`（续跑/审批段的「两条一等边界」）。
- 词表同步：`docs/architecture/EVENT_MODEL.md` 词表新增该事件；`tests/domain/test_m5_domain_increments.py`
  的 `DOCUMENTED_EVENT_TYPES` 同步并 37 → 38（**门禁本身未改**，只随词表同步）。

## 反证与实测

| # | 扰动 | 预期 | 实测 |
| --- | --- | --- | --- |
| CP-1 | 守护线程失败路径改回 `except: pass`（去掉留痕） | 可见性判据红 | 3 failed：API `test_a_failed_compensation_is_readable_on_the_event_chain` + 调度器两条（`assert [] == [(_RUN_ID, 'RuntimeError', 'RUNNING')]`） |
| CP-2 | 从发出的 payload 里删掉 `canonical_state` | 键集合判据红 | 3 failed（`{'契约文本声明': [canonical_state, failure_type, message, run_id], '实现实际发': [failure_type, message, run_id]}` + `KeyError: 'canonical_state'`） |
| CP-3 | 从契约文本的声明行里删掉 `canonical_state` | 键集合判据红 | 1 failed（声明 3 个键 vs 实发 4 个键） |
| CP-4 | 从 `EVENT_MODEL.md` 删掉「不含任务级归因」 | 边界同源判据红 | 1 failed（"必须登记「不含任务级归因」这条边界"） |
| CP-5 | 去掉留痕调用外层的 try/except（地板消失） | 地板用例红 | 1 failed（`RuntimeError: even the event cannot be published` 冒到 pass 外） |

五条全部**先红后复原**，复原后复跑：定向 `tests/api tests/application tests/domain tests/contracts`
**1959 passed / 3 skipped**（217.25s，DSN pin + PG 容器）。

### 返工（记录诚实）

- `service.py` 因新增薄封装 + 导入超出 450 行硬上限（452）⇒ 按 GOAL「450 行随改动搬代码」的
  纪律就地让行：把 `compensate_failed_resume` / `pause_requested` / `reservation_ref` 三处
  docstring 收紧为不影响事实的短句（**无行为改动**），落到 448 行。
- 调度器用例首版把「一条 run 的补偿失败不影响另一条」写成全局 `boom` ⇒ 第二条也被打坏，
  断言 `0 == 1` 红；改为按 run 注入（`boom_only`）后绿（夹具修正，未改断言强度）。
- 新判据首版残留一行占位断言（`assert payload["success"] if False else True`）⇒ 删除并补上
  对 `run_id` / `failure_type` / `message` 的逐项断言（强度只增不减）。

## 告警（W）

- **W-1（可见 ≠ 自动恢复）**：补偿失败若发生在**落库**这一步，canonical 行已停在前一步写的
  `RUNNING`，而 `_dispatch_due` 只扫 `PAUSED` ⇒ **下一轮不会自动把它捞回来**；那条事件是它唯一
  的痕迹。自动修复属新机制与产品决策，不在本 EC 内（已在 `scheduler.py` docstring 与
  `CONTROL_PLANE_API.md` 登记）。
- **W-2（地板仍是地板）**：连留痕事件都发不出去（发布面同挂）时只剩遥测——用例证明了"不中断
  整轮"，但没有（也无法）证明"必然留痕"；文档如实登记，不宣称。
- **W-3（同形入口未接线）**：审批入口 `resume_after_approval` 的补偿是同形入口（RECHECK-090
  W-1 已登记），本轮**未**给它加留痕（不在 EC-06 判据内）；两处口径由 `compensate_failed_resume`
  共用，但失败留痕目前只有守护线程面。
- **W-4（归因仍是文本）**：EC-06 (a) 的"任务级归因"本轮未做——payload 仍只有异常类型与文本；
  这是 (b) 路线下**有意**的终态（边界已一等登记），不是遗漏。
- **W-5（未实测真 store 故障）**：用例用受控注入（第 2 次写失败 / 补偿调用抛错 / 发布抛错），
  没有真的拔掉数据库连接；三档失败面都被覆盖，但"真故障下的行为"仍属推断。

## 结论

EC-06 以 **(b) 一等边界 + 降级可见** 收口：① 「失败原因不含任务级归因」在 `EVENT_MODEL.md` 与
`CONTROL_PLANE_API.md` 两处一等登记；② 守护线程补偿失败**不再静默**——新增
`run.resume_compensation_failed`（payload 四键，`canonical_state` 如实回答"补偿失败时 run 停在
哪"），读面 `GET /runs/{id}/events` 可判；地板（连事件都发不出去）与"可见 ≠ 自动恢复"两条边界
如实登记。零 DTO / 路由 / OpenAPI / 迁移变化（`EventType` 追加一个成员 + 一条新事件形态）。
结论：**PASS_WITH_WARNINGS**（W-1…W-5 见上）。

## 门禁

- 规模门禁（`tests/tooling/test_python_source_limits.py`）：见 PLAN-20260918-105「证据」
  （`service.py` 448 行、`scheduler.py` 425 行、`run_terminals.py` 125 行）。
- 定向：`tests/api tests/application tests/domain tests/contracts` **1959 passed / 3 skipped**。
- `ruff check` / `ruff format --check`：变更文件全绿；`tools/docs_consistency_check.py`
  = **DOCS-CHECK PASS**。
- `make validate-all`（m0 全量 23 项）：见 PLAN-20260918-105「证据」与 GOAL-006 迭代日志。
