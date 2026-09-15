---
id: MEM-20260915-035
title: 写面必须被读面消费：ops 静音规则与事故处置的落地方式
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.90
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-059-ops-write-surface-rules-and-incidents.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-059-ops-write-surface-rules-and-incidents.md
supersedes: []
tags:
  - ops
  - alert-rules
  - incidents
  - write-surface
  - consumed-by-reader
---

# 写面落地的前提是"读面真的消费它"

## 做了什么

ops 两页的写面：告警**静音规则** CRUD（`GET/POST /projects/{id}/ops/alert-rules`、
`PATCH/DELETE /ops/alert-rules/{rule_id}`）与**事故处置**（`POST /projects/{id}/ops/incidents`、
`POST /ops/incidents/{id}/assign`、`POST /ops/incidents/{id}/close`），持久面是
`OpsStore`（SQLite `ops_alert_rules` / `ops_incidents` 两表，项目索引），
domain 侧 `packages/domain/ops_control.py` 带 `IncidentStatus` 状态机。

## 为什么这样做

`packages/domain/ops_view.py` 原先写着"这些页面若引入持久实体，在进程内 scheduler 并不读取
它们之前，就是一个**不被消费的假真相**"。所以本轮**先定消费关系，再写持久面**：

- 规则被**读面消费**成 `muted=true` + `muted_by=<rule id>` 标记，**不从列表隐藏**
  （看不见的问题更难修），并给出 `muted_count`；`kind=None` 表示不限来源、
  `max_severity` 表示静音上限。
- 事故被**读面消费**成两件事：①来源 run 的告警带 `incident_id`；②`GET .../ops/incidents`
  拆成 `incidents`（已登记，declare/assign/close 的真实对象）与 `candidates`（派生自 FAILED
  run，**不会自动变事故**）。已登记的 run 从候选里移出，但仍留在已登记列表可追溯。
- 读面在 store 缺失时给 `rules_available=false` / `workflow_available=false` + 原因，
  写面 503——不把"没有 store"渲染成"没有规则/没有事故"。

## 怎么做与复现

```
python -m pytest tests/api/test_ops_control_api.py -q   # 10 passed（含 503/404/409/422）
python -m pytest tests/api/test_ops_view_api.py -q      # 5 passed（消费关系：标记不隐藏、回链、候选扣减）
cd apps/web && pnpm exec playwright test ops-write.spec.ts      # 5 passed（stub）
cd apps/web && pnpm run test:e2e:live                           # 28 passed（含 3 条真实 HTTP 写链）
```

判据要点：每条写路径都必须有"写完再读"的断言（只断言 201/204 不算交付）；
已关闭事故再处置 → **409**（域状态机拒绝），不是静默 no-op；PATCH 空补丁 → 422。

## 适用边界

- 静音**不抑制来源**：失败 run 仍会被列出（要降噪需要阈值/去重/静默期策略，未做）。
- `assignee` 是自由文本（无成员校验），无 SLA/计时/升级链。
- `IncidentsViewDto.incidents` 元素形状由"候选行"改为"事故行"——外部消费者需按新 schema 升级。
- `tests/api/run_fixtures._run_ready_sqlite_stores` 现在带 `ops_store`，因此 live 装配
  具备写面；需要"未配置"语义的用例必须显式置 `None`。
- 清单单一来源仍只有 `apps/web/tests/e2e/live-specs.ts` 一处（新增 live spec 只改那里）。

## 来源

- PLAN-20260915-059 / RECHECK-20260915-059（GOAL-20260915-002 cycle 5 / EC-04）。
- 相关：[[MEM-20260915-034]]（同一"没有记录面就如实说"的收敛方式）、
  [[MEM-20260915-032]]（未连边清单同理）。
