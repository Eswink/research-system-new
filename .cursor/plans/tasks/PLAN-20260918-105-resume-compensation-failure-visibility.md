---
id: PLAN-20260918-105
slug: resume-compensation-failure-visibility
title: 续跑失败的诚实边界 (b)：归因边界一等登记 + 守护线程补偿失败在读面可见（EC-06）
status: DONE
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 6 = EC-06（GOAL-005 收口结论 4 / RECHECK-090 W-3 + W-4 + W-5）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-105-resume-compensation-failure-visibility.md
memory_entries:
  - MEM-20260918-078
---

# PLAN-20260918-105 — 续跑失败的诚实边界（GOAL-006 cycle 6 = EC-06）

## 目标

EC-06 的**二选一终态**（RECHECK-090 W-3 / W-4 / W-5）：

- (a) **结构化任务级归因**：`run.resume_failed` payload 从「异常类型 + 文本」升级为
  结构化任务级归因（失败任务/phase 可判）且读面能判；**或**
- (b) **一等边界 + 降级可见**：把「哪一步炸的仍需读事件链上下文」登记为一等边界（文档同源），
  **并**把守护线程补偿失败的静默降级（`_compensate_failed_resume` 里的 `except: pass`）
  做成**读面可见**（canonical 事件或读面字段），不得只留在遥测/log。

（W-5「响应仍 200 + `continuation=FAILED`」的传输层信号属产品决策，**只作如实登记，不改**。）

## 先探明再动手（本轮只读勘察已确认的事实）

1. **失败原因的既有形状**：`packages/application/run_orchestration/run_terminals.py::compensate_failed_resume`
   发 `run.resume_failed`，payload = `{run_id, failure_type, message, compensated_to}`——
   **只有异常类型与文本，没有任务/phase 归因**（W-3）。
2. **守护线程的静默降级**：`services/api/scheduler.py::_compensate_failed_resume`（约 404 行）
   把 `self._runs.compensate_failed_resume(...)` + `self._runs_store.save_run(...)` 包在
   `try/except Exception: pass` 里——store 不可用时**补偿失败本身没有任何 canonical 痕迹**
   （W-4），只有下一轮重新评估这条约定。
3. **读面已有事件链**：`services/api/routers/run_events.py`（SSE + JSON replay）是既有的 canonical
   事件读面 ⇒ 「canonical 事件」这一形态**不需要**新增 DTO 字段或 OpenAPI 变更即可被判。
4. **同类入口**：`services/api/routers/approvals.py` 的 `resume_after_approval` 复用同一处补偿
   （W-1 已登记为后继入口，**不在** EC-06 判据内，本 PLAN 不动它）。
5. **既有判据**：`tests/api/test_resume_compensation_api.py` 4 条（补偿后 PAUSED + 原因进事件链 +
   可重入 + 无暂停上下文时重建路径不变）——本轮补的是**补偿自身失败**这条路径。

## 口径（为什么选 (b)）

- 今天的续跑失败发生在 `resume_paused` / `continue_from_rebuild` 的**整体调用**上，边界处
  只有异常对象（类型 + 文本）；任务/phase 身份在更深的任务执行层，没有回传到这个边界。
  做 (a) 等于新增一条跨层身份回传通道，代价与风险都远大于 (b)，而 EC 的判定细则把 (b) 与
  (a) 并列为一等终态。
- **实施时若发现任务身份其实已经在边界可用**（例如异常对象已带 task 上下文），则改做 (a) 并
  如实登记——口径不降，只是路线变更。
- (b) 的第二半不是"写一段文档"，而是**把静默变成 canonical 事实**：补偿失败要在事件链里
  留下一条现在**根本不存在**的事件；边界（连事件都发不出去时只剩遥测）也要写明。
- W-5 不改：响应仍 `200` + `continuation=FAILED`，只登记为产品决策。

## 验收条件

- **AC-01 补偿失败在读面可见**：守护线程那次补偿失败（例如 `save_run` 抛错）之后，
  `GET /runs/{id}/events` 能读到一条 `run.resume_compensation_failed`，payload 点名
  **补偿失败**的类型与文本、以及补偿失败时 canonical 仍停在哪个状态；canonical **不被伪造**
  （run 行仍是原状态，不是被硬改成 `PAUSED`）。
- **AC-02 既有语义不变**：单 run 补偿失败**不中断整轮**（同轮其余 run 照常处理）；故障撤掉后
  同一入口仍能真的续起来（"下一轮重新评估"这条约定不破）。
- **AC-03 边界一等登记 + 同源**：`run.resume_failed` 的"不含任务级归因"与 W-5 的"响应仍 200"
  在文档（`CONTROL_PLANE_API.md` + 事件发布处 docstring）写明；新事件的 payload 键集合与
  文档写明的键集合由**机器判据**互钉（少写/多写一个键就红）。
- **AC-04 反证**：① 把补偿失败改回静默（去掉那条事件）⇒ AC-01 的用例红；② 把边界声明从
  文档/`docstring` 删掉 ⇒ AC-03 的判据红；③ 把"不中断整轮"改成抛出 ⇒ AC-02 的用例红。
  三条都必须**先红后复原**。
- **AC-05 门禁**：定向（`tests/api`、`tests/application`、`tests/domain`、`tests/contracts`）+
  规模门禁 + m0 全量 23 项 + CI 六 job 终态；`EventType` 追加成员后事件 schema 判据（若有）保持绿。

## 实施清单

### WP-A — 补偿失败在 canonical 事件链留痕

- [x] `packages/domain/events.py`：追加 `EventType.RUN_RESUME_COMPENSATION_FAILED = "run.resume_compensation_failed"`
      （与既有 `RUN_DEGRADED` / `RUN_RESUME_FAILED` 同形，附一句语义注释）。
      词表同步：`docs/architecture/EVENT_MODEL.md` 词表 + `tests/domain/test_m5_domain_increments.py`
      的 `DOCUMENTED_EVENT_TYPES` 与计数 37 → 38（门禁本身未改）。
- [x] `packages/application/run_orchestration/run_terminals.py`：新增
      `publish_compensation_failure(publish, run_id, failure, canonical_state)`（事件构造只有一处），
      docstring 里**写明 payload 键集合**（AC-03 的判据读它）。
- [x] `packages/application/run_orchestration/service.py`：加同形薄封装（与
      `compensate_failed_resume` 并列）；因 450 行硬上限，就地让行（三处 docstring 收紧，无行为改动）。
- [x] `services/api/scheduler.py::_compensate_failed_resume`：失败路径先发这条事件、再吸收异常
      （整轮不中断的语义不变）；docstring 写明"连事件也发不出去 ⇒ 只剩遥测"这条地板边界，
      并写明"可见 ≠ 自动恢复"（补偿的落库失败时 canonical 已停在 `RUNNING`，下一轮只扫 `PAUSED`）。

### WP-B — 判据与反证

- [x] 读面用例 `tests/api/test_compensation_failure_visibility_api.py`：真跑一轮
      `RetryDispatchScheduler`（真 service + 真事件发布），只打坏**补偿的落库** ⇒ 从
      `GET /runs/{id}/events` 读到 `run.resume_compensation_failed`（四键与值逐项断言）+ canonical
      未被改写；**反空洞**：同样跑一轮但补偿能落库 ⇒ **没有**该事件（且 run 回 `PAUSED`）。
- [x] 调度器用例（`tests/application/ops/test_retry_dispatch_scheduler.py`）：补偿失败留痕带
      **当时 canonical 仍停的状态**；一条 run 的补偿失败不影响同轮其它 run；连事件都发不出去时
      仍不中断整轮（地板）。
- [x] 机器判据 `tests/application/run_orchestration/test_resume_compensation_failure_event.py`：
      事件串与读面契约一致、payload 键集合 == 契约文本声明行、两份文档写出同一组键、
      两处都写明「不含任务级归因」这条一等边界。
- [x] **反证实跑**（五条，先红后复原）：见「证据」。

### WP-C — 文档同源

- [x] `docs/api/CONTROL_PLANE_API.md`：新增"补偿失败本身也是可读事实"（事件 + 四键 + 读法）+
      "地板"登记 + 两条一等边界（不含任务级归因；响应仍 200 + `continuation=FAILED` 属产品决策）。
- [x] `docs/architecture/EVENT_MODEL.md`：词表新增该事件 + 一段语义说明（含四键与一等边界）。

### WP-D — 记录与回写

- [x] RECHECK-20260918-105（PASS_WITH_WARNINGS，W-1…W-5）、MEM-20260918-078、
      PLAN/ALL_PLAN/`memory/INDEX.md`、GOAL-006 回写（EC-06 PASS + 证据块 / 迭代日志 /
      子计划 / 状态历史 / 续点 → GOAL 收口）。

## 证据

- **反证**（五条，先红后复原；细节与实测输出见 RECHECK-20260918-105「反证与实测」表）：
  CP-1 失败路径改回 `except: pass` ⇒ 3 failed（读面 + 调度器两条）；
  CP-2 从 payload 删 `canonical_state` ⇒ 3 failed（键集合不一致 + `KeyError`）；
  CP-3 从契约声明行删一个键 ⇒ 1 failed；CP-4 从 `EVENT_MODEL.md` 删「不含任务级归因」⇒ 1 failed；
  CP-5 去掉留痕外层 try/except ⇒ 1 failed（地板语义消失，异常冒到 pass 外）。
- **定向**（`RESEARCHOS_POSTGRES_DSN` pin + PG 容器在跑）：
  `tests/api tests/application tests/domain tests/contracts` ⇒ **1959 passed / 3 skipped**（217.25s）。
- **规模门禁**：`service.py` 448 行（贴线就地让行后）、`scheduler.py` 425 行、`run_terminals.py`
  125 行；`tests/tooling/test_python_source_limits.py` 随定向套件绿。
- **lint / 类型 / 文档门**：`ruff check` + `ruff format --check` 变更文件全绿；`mypy`
  **932 source files** 无问题（m0 `python/typecheck`）；`DOCS-CHECK PASS: 6 deterministic checks`。
- **m0 全量 23 项 = PASS**（`PASS: profile=m0; 23 deterministic checks`）。
  诚实记录：首跑 1 红 = `framework/run_cursor_framework_evals`，根因是既有 Windows 文件占用
  flake（`PermissionError: [WinError 5] os.replace('.cursor/runtime/evolution_state.json.tmp')`
  —— 日志已留痕），隔离复跑 **FRAMEWORK EVAL PASS** + 全量复跑 **23/23**；**非代码回归**，
  未改任何门禁或断言。
- CI：见 GOAL-006 迭代日志 cycle 6 行的 run 编号与六 job 结论。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 6 = EC-06，driver=client-goal / owner=root-agent）：
  只读勘察确认 W-3（payload 无任务级归因）、W-4（守护线程补偿失败无 canonical 痕迹）、
  既有事件读面（`run_events.py`），据此选 (b) 并把"补偿失败留痕"作为本轮主要交付；
  `status: IN_PROGRESS`。
- 2026-09-18 收口：WP-A…WP-D 全部完成；CP-1…CP-5 五条反证先红后复原；定向 **1959 passed /
  3 skipped**；m0 **23/23 PASS**（首跑 1 红 = 既有 Windows 文件占用 flake，隔离 + 全量复跑绿）；
  `status: DONE`，`latest_recheck` 指向 RECHECK-20260918-105（PASS_WITH_WARNINGS）。

## 影响报告

- **Domain / API / schema**：`EventType` **追加**一个成员（附加式，不改既有取值）；
  新增一条 canonical 事件形态；DTO / 路由形状 / OpenAPI 快照**不变**（不改响应字段）。
- **持久化 / 迁移**：无（事件走既有 outbox/store 路径）。
- **安全 / 凭据**：无（事件 payload 只含异常类型与文本，沿用既有 redaction 边界）。
- **兼容性 / 迁移风险**：低——消费者按 `event_type` 过滤，未知类型应被忽略；判据会钉住
  "既有事件形状不变"。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 全 EC 收口后按 README 的收口流程处理（本 PLAN 是 EC-06 的候选终态；
  若 (b) 成立则该 GOAL 六条 EC 全 PASS，可进入 ACHIEVED 收口）。
