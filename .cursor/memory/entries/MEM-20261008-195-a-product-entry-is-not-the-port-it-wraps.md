---
id: MEM-20261008-195
title: "产品入口 ≠ 它包装的 Port：一个能力在引擎面成立，产品面仍可能零入口（`requeue` 全仓调用方都在 tests/）"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.9
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-311-goal-033-ec01-dead-letter-product-entry.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-312-goal-033-ec01-dead-letter-product-entry.md
supersedes: []
tags: [port-vs-product, product-entry, dead-letter, requeue, goal-033, plan-311]
---

## 做了什么

GOAL-032 把「人工恢复一条死信任务」做成了 Port 上的一等能力（ADR-0033 的
`WorkflowEngine.requeue`，三实现同形、契约判据齐全、真编排 e2e 全绿）。据此很容易认为
「死信恢复已交付」。GOAL-033 建档实测推翻了这一读法，三行读数：

| 复核 | 命令 | 读数 |
| --- | --- | --- |
| 服务层有无该动作 | `rg -n "requeue" services/` | **零命中** |
| 有无 HTTP 路由 | `rg -n "requeue" services/api/routers/` | **零命中** |
| 谁在调用 Port | `rg -n "\.requeue\(" --type py` | 产品面**零调用**；调用方**全部**在 `tests/`（5 文件 / 13 处） |

⇒ 运维要恢复一条死信**只能进 REPL 或改库**。同一份文档还把该路径逐字登记为
「`POST /tasks/{id}/retry`（**未提供**：retry 属 WorkflowEngine 内部策略）」。

## 为什么这样做

**判据形态**：Port 方法存在、实现齐、契约用例绿 —— 这些**全都**不蕴含「产品能走通」。
正确的最小判据是三条同时成立：① 端点可调；② **下游真的动了**（任务面真回 `QUEUED`）；
③ **自动路径真的认它**（`claim_lease` 不再被终态守卫拒绝）。第 ③ 条最容易被漏 ——
只断言前两条会放过「状态写回了但引擎仍不认」这类半成品。

**接线纪律**：新端点**只**做「找 Port → 调用 → 翻译结论」，不在路由层判状态、不写任务行
（源码断言 `.requeue(` 存在 **且** 无 `ResearchTaskState.transition` / 无直接 UPDATE）。
路由里若出现状态判定，就等于把 ADR-0033 的决定复制成第二份。

## 关联

- 与 `MEM-20260929-…`（`R26-5` 那类「已实现但未取证」）**方向相反**：那条是「有实现没判据」，
  本条是「有判据没入口」。
- 入口落地时会把既有的**写面保护面**自动纳入（保护面由方法分类推出，不是路径清单）——
  见 `tests/api/test_write_face_cannot_be_bypassed.py` 自述的枚举口径。

## 怎么做与复现

```bash
# 立项前的最小复核（三条一起看，缺一条就会误判"已交付"）
rg -n "requeue" services/                       # 服务层有没有这个动作 → 零命中
rg -n "requeue" services/api/routers/           # 有没有 HTTP 路由     → 零命中
rg -n "\.requeue\(" --type py | grep -v tests  # 谁在调 Port          → 产品面零调用

# 落地后的最小判据（三条必须同时成立）
uv run --frozen --no-sync python -B -m pytest tests/api/test_task_retry_api.py -q
#   ① 端点 200 + result=restored
#   ② 任务面真的回 QUEUED
#   ③ 恢复后 acquire_lease 成功（自动路径真的认它）
```

## 适用边界

- 适用于「Port/库 API 已实现且有契约判据」但**控制面未接线**的能力。
- **不**适用于纯内部机制（无人工动作语义的 Port 方法不需要产品入口）。
- 第 ③ 条是分界线：只断言 ① ② 会放过「状态写回了但引擎仍不认它」的半成品；
  判「真的可用」必须有一条**下游消费证据**。
- 交接边界：本端点只做「找 Port → 调用 → 翻译结论」；任何状态判定都必须留在 domain /
  adapter，路由层出现状态机调用即视为第二套实现。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-311-goal-033-ec01-dead-letter-product-entry.md`
- `.cursor/plans/rechecks/RECHECK-20261008-312-goal-033-ec01-dead-letter-product-entry.md`
- ADR-0033（`docs/adr/ADR-0033-dead-letter-manual-recovery.md`）
