---
id: PLAN-20261120-118
slug: advisory-panel-read-face
title: GOAL-115 cycle 3 —— advisory 并存只读读面（硬门一行不改）
status: IN_PROGRESS
created_at: 2026-11-20
updated_at: 2026-11-20
parent_goal: GOAL-20261119-115
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20261120-118

## 背景

EC-05：新增一个**只读**的「面板建议」读面（HTTP + 编排两级），返回聚合结论与逐票分歧；
**`acceptance_criteria` 的 `REVIEW_SCORE ≥ 0.8` 与 `review_panel_judging.panel_rejection()`
一行不改**；advisory **不产生 `Decision`**、**不动 `NOT_JUDGED` 五项**。

**建档实测（2026-11-20，读代码确认）**：

| 事实 | 证据 |
| --- | --- |
| 聚合逻辑**已存在**且完整：`voters` / `votes` / `advisory` / `dissent` / `ineligible` / `targets` / `independent` | `packages/application/evaluation/panel_verdict.py:89-134` |
| 分组键**必须是 `phase_id`**，不是 `task_id` | `ports/review_finding_store.py` 的 `ScopedReviewFinding` 文档逐字警告：按 `task_id` 分组会让「评审小组永远不存在」 |
| 少于两份 ⇒ `aggregate_panel` 返回 `None` | 同文件 93-96 行（单评审不聚合，零回归边界） |
| 现有读面只有**逐条** finding（`/runs/{id}/reviews`），**没有**聚合视图 | `services/api/routers/inspection.py:165` |
| 硬门在 `panel_rejection`：任何非 PASS 票即失败 | `run_orchestration/review_panel_judging.py:106-124` |

⇒ **本 cycle 不需要新算法**：需要的是（a）一个把 `aggregate_panel` 挂到既有存储上的
**只读**端点，（b）一个**编排级**读取入口（不经 HTTP），（c）判据证明「硬门仍判负」与
「advisory 同时读出 1 负 1 过」两件事并存。

## 交付面（checkbox）

- [ ] WP-1 编排级只读取数：按 `phase_id` 分组 → `aggregate_panel`（不产生 `Decision`）
- [ ] WP-2 HTTP 只读端点 `GET /runs/{run_id}/panel-advice`
- [ ] WP-3 两向反证：把 advisory 接进 `panel_rejection` ⇒ 判红；摘掉读面 ⇒ 判红
- [ ] WP-4 同一份判词下：硬门 `FAILED` **且** advisory 可读「1 负 1 过」
- [ ] WP-5 逐字守卫：`REVIEW_SCORE ≥ 0.8` / `panel_rejection()` / `NOT_JUDGED` 五项不变

## 实施清单

### WP-1 编排级只读取数

新模块 `packages/application/run_orchestration/panel_advice.py`（**只读**、零写面）：

```python
def panel_advice(findings: Sequence[ScopedReviewFinding]) -> tuple[PanelAdvice, ...]
```

- 按 `phase_id` 分组（`None` 的不并组，**逐条点名**它们未参与聚合 —— 与既有口径一致）；
- 每组调 `evaluation.panel_verdict.aggregate_panel`；
- 单条/无归因组 ⇒ 仍返回该组但 `verdict=None`（**可读**「这组没形成小组」比"什么都不返回"更诚实）；
- **不得** import `Decision`、不得调 `deps.fail`、不得写任何存储。

### WP-2 HTTP 端点

`GET /runs/{run_id}/panel-advice` → `list[PanelAdviceDto]`：

```
phase_id, advisory, votes, dissent, voters, independent, independence_notes, ineligible
```

- 存储未接 ⇒ 503（与 `/reviews` 同口径，**不假装空结论**）；未知 run ⇒ 404；
- **只读**：无写方法、无 `Decision`、不改 policy；
- 同步 `docs/api/openapi.m13.json` 快照与 `apps/web` 类型（若前端需要）。

### WP-3 两向反证（判据自带）

① **接进硬门 ⇒ 判红**：造一份「1 负 1 过」的判词，断言
`panel_rejection(...)` 返回失败（硬门不变）；再用一个**假想的**"按 advisory 多数放行"
实现断言它会**放过**同一份判词 ⇒ 两条判据的结论必须相反（证明 advisory 不是硬门）。
② **摘掉读面 ⇒ 判红**：`panel_advice` 不在（或返回空）时，断言同一份判词下
「1 负 1 过」**不可读**。

### WP-4 并存事实

同一份判词同时断言：
- `panel_rejection(...)` is not None（硬门判负）；
- `panel_advice(...)` 的该组 `advisory` 可读、`votes == {"PASS": 1, "REJECT": 1}`、
  `dissent` 非空（分歧可读）。

### WP-5 逐字守卫

判据读**源码文本**断言：
- `examples/contracts/task_contracts.yaml` 的 `threshold: 0.8` 与 `operator: GTE` 在场；
- `panel_rejection` 的**签名与判负条件**逐字在（`rejected = tuple(item for item in verdicts
  if item[1] != "PASS")`）；
- `manuscript_quality.NOT_JUDGED` 仍是**五项**且内容逐字。

## 验证

```bash
uv run --frozen --no-sync python -B -m pytest tests/application/evaluation tests/application/run_orchestration tests/api -q
uv run --frozen --no-sync python -B tools/run_m0_with_witness.py
```

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | WP-1 | test | 按 `phase_id` 分组聚合 | 待填 |
| EV-02 | WP-2 | test | `GET /runs/{id}/panel-advice` | 待填 |
| EV-03 | WP-3 | test | 两向反证 | 待填 |
| EV-04 | WP-4 | test | 硬门 + advisory 并存 | 待填 |
| EV-05 | WP-5 | test | 逐字守卫 | 待填 |

## 验收条件

- advisory 读面存在且**只读**（无 `Decision`、无写面）；
- 同一份判词：硬门 `FAILED` **且** advisory 可读「1 负 1 过」；
- `REVIEW_SCORE ≥ 0.8`、`panel_rejection()`、`NOT_JUDGED` 五项**逐字未动**；
- 全量 m0 绿。

## 状态历史

- 2026-11-20：建档。cycle 2 已收口（EC-03/EC-06 PASS）；本轮做**不需出网**的 EC-05。

## 影响报告

- **Domain/API/schema**：新增一条**只读** GET 端点 + DTO；无新域对象、无写面、无 migration。
- **安全/凭据**：无变化（读面不认证是既有设计）。
- **兼容性/迁移**：纯新增端点；既有 `/reviews` 面逐字不变。
- **上游版本影响**：无。
