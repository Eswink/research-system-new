---
id: PLAN-20260917-090
slug: resume-failure-compensation
title: 续跑失败即补偿：不留悬空 RUNNING、原因进事件链、补偿后可重入（EC-06）
status: IN_PROGRESS
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 7 = EC-06（后继入口第 7 项 / RECHECK-082 W-3）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260917-090 — 续跑失败补偿（GOAL-004 cycle 7 = EC-06）

## 目标

`resume_paused` 失败会把 run **留在悬空 `RUNNING`**，而且没有补偿（RECHECK-082 W-3）。
反向搜索确认机制（两条入口各自）：

- `RunOrchestrationService.resume_paused`（service.py:335）**先 pop 上下文再执行**：
  `stashed = self._paused.pop(run_id, None)` → 执行一旦抛错，暂停上下文**已经丢了**；
- **API 入口**（`POST /runs/{id}/resume`，`routers/approvals.py:216`）：调用方已把 canonical
  迁到 `RUNNING` 并落库；`resume_paused` 抛的**非 `InvalidInputError` 异常会直接向外冒**
  （500），run 行停在 `RUNNING`；
- **守护线程入口**（`RetryDispatchScheduler._resume`，scheduler.py）：`except Exception: return 0`
  ——如实注释为"留 RUNNING、没有 continuation"，但**没有任何补偿**；
- 后果：run 既不在 `PAUSED`（守护线程只派发 `PAUSED` 的到期重排，不会再碰它），也不能再
  `POST /resume`（`PAUSED → RUNNING` 迁移会 409，因为它已经是 `RUNNING`）⇒ **永久悬空**，
  只能人工改库。

本轮把失败路径收敛成**可判定状态**：失败 ⇒ canonical 放回 `PAUSED` + 事件链记原因
（`run.resume_failed`）+ 两条入口语义一致；补偿后**可重入**（再次续跑走重建路径并成功）。

## 口径

1. **补偿到 PAUSED，不发明新状态**：用既有域迁移 `ResearchRunState.Transition.PAUSE`
   （与守护线程重建被拒后的回退、`POST /pause` 同一条路径），不新增"失败停车"之类状态。
2. **原因进事件链**：新增 `run.resume_failed`（payload：`run_id` / `failure_type` /
   `message` / `compensated_to`）。事件链是 run 事实的 canonical 记录（AGENTS.md §6/§7），
   读面**不新增"停车原因"字段**——EC-02 已经明确拒绝那个方向。
3. **补偿只有一处**：两条入口共用同一个补偿函数（`run_terminals.compensate_failed_resume`），
   差别只在由谁落库（API 走 `save_run`，守护线程走 `runs_store.save_run`）。
4. **可重入靠既有重建路径**：进程内暂停上下文被 pop 后不会"复活"（本 PLAN 不改
   `resume_paused` 的 pop 语义）；补偿回 `PAUSED` 后，第二次 resume 走 **durable 重建**
   （GOAL-003 cycle 20 + GOAL-004 cycle 1 的冻结正文），这条路在用例里必须真的跑通。
   没有冻结正文的旧 run 仍会被诚实拒绝（重建路径的既有边界，不因本 PLAN 放宽）。
5. **不静默吞掉**：API 面把失败如实写进响应（`continuation=FAILED` + 原因 + 状态回
   `PAUSED`、`dispatch=HELD`），守护线程面把失败计入本轮结果并留遥测/日志，且**不中断**
   整轮 dispatch（单个 run 的失败不拖垮别的 run——既有约定）。
6. **判据只增强**：既有 resume/approval 用例（`RESUMED`/`REBUILT`/`NONE` 三种结局）断言
   不改；新增的是失败路径。

## 验收条件

- [ ] AC-01 **不留悬空 RUNNING（API 入口）**：注入 `resume_paused` 失败（进程内上下文在）
  ⇒ 响应如实（`continuation=FAILED` + 原因、`dispatch=HELD`）且 **run 行是 `PAUSED`**
  （不是 `RUNNING`）。
- [ ] AC-02 **不留悬空 RUNNING（守护线程入口）**：同一个失败注入 ⇒ 该 run 被放回 `PAUSED`，
  且本轮 dispatch 不因它中断（其它到期 run 照常续跑）。
- [ ] AC-03 **原因可从 canonical 事实读到**：两个入口各写一条 `run.resume_failed`
  （`failure_type`/`message`/`compensated_to=PAUSED`），并能从 run 的事件链读回
  （`GET /runs/{id}/events` 面或 store 直读）。
- [ ] AC-04 **可重入**：失败一次（补偿回 `PAUSED`）后，把注入的失败撤掉再 resume ⇒
  **成功**（走出 `REBUILT` 或 `RESUMED`），run 不再停在停车态。
- [ ] AC-05 **反证**：去掉补偿（异常直接冒/直接 return 0）⇒ AC-01/AC-02 用例红（run 留
  `RUNNING`），撤掉后复绿；反证必须实跑（Edit 改→跑→改回）。
- [ ] AC-06 **收口**：事件词表门禁同步（`EventType` 36 → 37 + `DOCUMENTED_EVENT_TYPES`
  + `EVENT_MODEL.md`）；定向套件 + m0 23 项 + web 门；RECHECK-090 + MEM + GOAL/ALL_PLAN
  记账。

## 实施清单

- [ ] WP-A **域/应用**：`EventType.RUN_RESUME_FAILED`；`run_terminals.compensate_failed_resume`
  （迁移 + 发事件）；`service.compensate_failed_resume` 薄接线（450 行上限 ⇒ 先把
  `_pending_human_gates` 搬到 `human_gates.py` 腾出空间，**不改门禁**）；词表门禁同步
  （domain 用例 + `EVENT_MODEL.md`）。
- [ ] WP-B **两条入口**：API `_resume_payload` 捕获失败 ⇒ 补偿 + 落库 + 如实响应；
  守护线程 `_resume` 捕获失败 ⇒ 同一补偿 + 落库 + 不中断本轮。
- [ ] WP-C **用例 + 反证 + 记录**：API 用例（失败补偿/事件可读/**可重入**）、守护线程用例
  （补偿 + 不中断）、反证一跑、定向 + m0 + web 门、RECHECK-090 + MEM + GOAL/ALL_PLAN。

## 证据

（收口时回填。）

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 7 = EC-06，driver=client-goal / owner=root-agent）；
  反向搜索确认机制 = `resume_paused` 先 pop 后执行（service.py:340）+ API 面异常外冒 +
  守护线程面 `except Exception: return 0`，两条路径都不补偿；`status: IN_PROGRESS`。

## 影响报告

- **Domain**：新增一个事件类型（`run.resume_failed`）；无新状态、无新字段。
- **API/schema**：`POST /runs/{id}/resume` 新增第四种结局 `continuation=FAILED`（既有三种
  不变）；无新端点；OpenAPI 快照不变（response_model=object）。
- **持久化**：多一条事件行；无迁移、无 schema 变化。
- **安全/凭据**：无新面（失败原因只带异常类型与文本，不含凭据；沿用既有 payload 隐私口径）。
- **兼容性/迁移风险**：`resume_paused` 的"先 pop"语义不变 ⇒ 进程内上下文不复活（重入走重建
  路径）；没有冻结正文的旧 run 重入仍被拒绝（既有边界）。
- **上游版本影响**：无新依赖。
