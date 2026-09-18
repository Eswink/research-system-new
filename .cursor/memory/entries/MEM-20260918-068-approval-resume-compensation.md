---
id: MEM-20260918-068
title: "审批续跑的失败补偿：decide 先落 RUNNING，失败不补偿就是悬空 RUNNING（不是 WAITING）"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.9
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-094-approval-resume-failure-compensation.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-094-approval-resume-failure-compensation.md
supersedes: []
tags:
  - resume
  - approval-gate
  - compensation
  - canonical-state
  - evidence
---

# 审批续跑失败：补偿形状与一个被写错的告警

## 做了什么

GOAL-005 cycle 2（EC-02）把 GOAL-004 收口时登记的同形缺口（RECHECK-090 W-1）收口：
`POST /approvals/{id}/decide`（approve）在续跑失败时**不再把异常冒给端点**，而是走与
`resume_paused` 相同的补偿——`RUNNING --PAUSE--> PAUSED` + `run.resume_failed`
（`failure_type` / `message` / `compensated_to`）。产品改动只有一处
（`services/api/routers/approvals.py::_resume_after_approval` 多一个 `except` 分支
调 `compensate_failed_resume`），加 4 条 API 用例与一段文档。

## 为什么这样做

- **上游告警对缺口的描述是错的，先纠正再动手**：RECHECK-090 W-1 说失败后"run 停在
  `WAITING_FOR_APPROVAL`"；实测 `decide` 端点**先把 run 落成 `RUNNING`**
  （`WAITING_FOR_APPROVAL --APPROVAL_GRANTED--> RUNNING`）再续跑 ⇒ 失败后的真实事实是
  **悬空 `RUNNING`**（没有执行者；`_waiting` 已被 pop；连"再 resume 一次"也走不到，
  因为 `PAUSED → RUNNING` 那条迁移要求状态是 PAUSED）。按告警原文写测试会写出一条
  **永远绿**的断言。
- **补偿复用既有迁移，不碰 Canonical State 边界**：`RUNNING → PAUSED` 是既有迁移
  （`POST /runs/{id}/pause` 同路径）⇒ 不需要新状态、不需要 ADR。
- **竞态不是失败**：`InvalidInputError`（上下文已被取走）保持 no-op，此时 `RUNNING`
  是**正确**状态——另一个入口正在跑这个 run。补偿只覆盖真失败。

## 怎么做与复现

```bash
# 定向（DSN 固化配方）
RESEARCHOS_POSTGRES_DSN=postgresql://research_os:research_os_m14_test@localhost:15432/research_os \
  uv run --frozen --no-sync python -B -m pytest tests/api/test_approval_resume_compensation_api.py -q
# 合并既有补偿/审批用例
uv run --frozen --no-sync python -B -m pytest \
  tests/api/test_approval_resume_compensation_api.py tests/api/test_resume_compensation_api.py \
  tests/api/test_approvals_api.py -q
# 反证：把补偿分支换成 `raise exc` 后重跑上面的第一条 ⇒ 期望 2 failed / 2 passed
```

判据落在 **store 里的 run 行状态**（`_stored_state` 读 `runs_store`），不读响应文本；
失败注入用实例级替身（只替换 `has_waiting_context` / `resume_after_approval`），
补偿跑真实现。

## 适用边界（踩过的坑）

- **响应仍是 200**：`decide` 成功响应不含续跑结局字段，调用方判失败要读 canonical
  状态或事件链（与 `/resume` 的 `continuation` 口径一致；文档已写明）。
- **进程内上下文不复活**：补偿只改 canonical，`_waiting` 已被 pop ⇒ 重入走
  `resume_paused`，没有暂停上下文时再走 durable 重建（与 EC-06 的 W-2 同一边界）。
- **单入口**：审批续跑只有 API 端点一个驱动（守护线程不涉审批）⇒「两条入口语义一致」
  这条在本轮表现为**单入口共用同一补偿实现**，不要写成"两处都验证过"。
- 相关：[[MEM-20260917-065]]（`resume_paused` 的补偿与诚实边界，本条的镜像）、
  [[MEM-20260917-063]]（canonical 状态是唯一事实的口径）。

## 来源

- PLAN-20260918-094 / RECHECK-20260918-094（GOAL-20260918-005 cycle 2 = EC-02）。
- 上游：RECHECK-20260917-090 的 W-1（告警描述已被本轮纠正为"悬空 RUNNING"）。
