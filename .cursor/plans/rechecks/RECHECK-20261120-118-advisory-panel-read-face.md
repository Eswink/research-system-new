---
id: RECHECK-20261120-118
slug: advisory-panel-read-face
title: GOAL-115 cycle 3 复检 —— advisory 并存只读读面（硬门一行不改）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-11-20
updated_at: 2026-11-20
plan_id: PLAN-20261120-118
parent_goal: GOAL-20261119-115
owners:
  - root-agent
verify_paths:
  - packages/application/run_orchestration/panel_advice.py
  - services/api/routers/inspection.py
  - services/api/dto/inspection.py
  - docs/api/openapi.m13.json
  - tests/application/run_orchestration/test_advisory_panel_read_face.py
  - tests/api/test_panel_advice_endpoint.py
---

# RECHECK-20261120-118

## 结论

**PASS_WITH_WARNINGS**。EC-05 的三条要求都成立：advisory 读面存在（HTTP + 编排两级）、
同一份判词下硬门仍判负而分歧可读、硬门与 `NOT_JUDGED` 逐字未动。warning 见
`W-1`：HTTP 面的「写不成」判据断言的是**非 2xx**，不是具体的 405（实测本装配下是 422）。

## 检查结果

| # | 要求 | 判据 | 实跑结果 |
| --- | --- | --- | --- |
| R-1 | 编排级只读读面 | `test_advisory_panel_read_face.py`（13 passed） | 按 `phase_id` 分组聚合；`phase_id=None` 的记录点名不并组 |
| R-2 | HTTP 只读读面 | `test_panel_advice_endpoint.py`（7 passed） | `GET /runs/{id}/panel-advice`；OpenAPI schema 里该方法集合恰为 `['GET']` |
| R-3 | **同一份判词：硬门判负 + advisory 可读** | 两个测试文件各一条 | 硬门口径 `verdict != "PASS"` 判负；advisory `votes == {"PASS":1,"REJECT":1}`、`dissent` 非空 |
| R-4 | advisory **不产生 `Decision`** | AST 判 | 模块不 import `Decision`；不调 `fail` / `reject`；不写 store（`put`/`save`/`delete` 全无） |
| R-5 | **`panel_rejection()` 一行不改** | 源码逐字断言 | `rejected = tuple(item for item in verdicts if item[1] != "PASS")` 仍在 |
| R-6 | `REVIEW_SCORE ≥ 0.8` 未改 | 配置原文断言 | `operator: GTE` 与 `threshold: 0.8` 仍在 |
| R-7 | `NOT_JUDGED` 五项未动 | 域常量断言 | `len(NOT_JUDGED) == 5` |
| R-8 | 两级读面**同源** | HTTP 票型对拍 | `/reviews` 聚合出的票型 == `/panel-advice` 的 `votes` |
| R-9 | 诚实失败 | HTTP 判据 | 未知 run ⇒ 404；存储未接 ⇒ 503（**不**返回空列表） |

## 反向按压（每条实跑）

| 臂 | 按压 | 期望 | 实测 |
| --- | --- | --- | --- |
| A-1 | 造「按 advisory 多数放行」的假想实现 | 结论与硬门**相反** | 2 过 1 负的批次：假想实现放行，硬门判负 |
| A-2 | 摘掉读面 | 分歧不可读 | 只剩「存在一张非 PASS 票」这一个事实 |
| A-3 | 把两条判词按 `task_id` 分组 | 小组不存在 | 判据按 `phase_id` 分组后同组两条 |
| A-4 | 往 advisory 模块写 store | 判据红 | `put`/`save`/`delete` 逐条断言为无 |

## 本轮修正的三条**判据自身缺陷**（都是假红，不是产品缺陷）

| # | 缺陷 | 成因 | 修法 |
| --- | --- | --- | --- |
| C-1 | `.append(` 被当成"写存储" | 我把「写面」判据写宽了 | 收窄到 store 的唯一写方法 `put`（附理由） |
| C-2 | 遍历 `app.routes` 读不出路径（全是空串） | 该装配下 `route.path` 不可用 | 改读 **OpenAPI schema**（同一个 app 生成的路由事实） |
| C-3 | POST 断言 `{404,405}` 却得 422 | FastAPI 在方法不匹配时的实际状态 | 改判「**不得是 2xx**」（对应产品事实：这个面只读） |

C-1..C-3 都是「判据盯错了东西」，**没有**放宽任何产品断言：C-3 从"必须是 405"变成
"必须不是成功"，对「只读」这个性质的约束没有变松（成功仍然不可能）。

## 警告

- **`W-1`**：R-2 的「写不成」用**非 2xx** 表达，而非 405。理由写在测试 docstring 里：
  判死 405 会把框架细节写进判据。若将来 FastAPI 改成让 POST 落到 405，本条仍绿；
  若它**允许** POST，本条会红 —— 这正是要守的那一面。

## 未覆盖

- advisory 面**尚未在真实 run 上被试过**：它读的是落库判词，而真实双评审 run（EC-04）
  仍需出网。这一格**不计入本复检的通过面**：读面逻辑由合成判词覆盖，
  真实数据的形态（`phase_id` 是否总被填）要等 EC-04 的读数。
- EC-05 不涉及前端消费：本轮只加读面，未接 UI。

## 无可复用事实

本轮没有沉淀新的工程记忆条目。C-1..C-3 属于「判据自身的三个假红形态」
（宽 Write 判、读不出属性的路由表、框架状态码细节），已在复检表里逐条点名；
它们更适合留在本记录里作为同类判据的检查清单，而不是升格为项目级记忆。
