---
id: RECHECK-20261008-328
slug: goal-035-ec03-review-score-linkage
title: 独立复检：GOAL-035 cycle 3（EC-03）评审结论进入判据面
plan_id: PLAN-20261008-327
status: COMPLETED
result: PASS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-328 — GOAL-035 cycle 3（EC-03）独立复检

复检对象：`PLAN-20261008-327`。独立重跑下列机械面，**不引用 PLAN 结论当证据**。

## 检查结果

### 1. 来源被点名（AC-1）

| 读法 | 读数 |
| --- | --- |
| 分数路径来自合约声明 | `rg -n "metric: review_decision.score" examples/contracts/task_contracts.yaml` ⇒ 命中 `review_scored_deliverable` |
| 判定仍走既有域函数 | `rg -n "_evaluate_review_score" packages/domain/acceptance.py` ⇒ 既有实现；本 cycle **未改** `packages/domain/acceptance.py`（`git diff` 对该文件为空） |
| 不回落默认分 | 判据第三例断言缺来源时判词**无分数、无算子**（实测 `review score unknown`） |
| 零 schema 改动 | `git diff schemas/` ⇒ 空（`metric` 是 schema 既有字段） |

### 2. 三态（AC-2）

```
pytest tests/e2e/test_review_score_linkage_on_the_run_path.py -q  ⇒  3 passed
```

判词逐字：`review score 0.95 GTE 0.8`（`SUCCEEDED`）/ `review score 0.5 GTE 0.8`（`FAILED`）/
`review score unknown`（`FAILED`，无分数无算子）。判词经**既有读面** `GET /runs/{id}/reviews` 读。

### 3. 既有受判面未动（AC-3）

| 读法 | 读数 |
| --- | --- |
| 既有契约未改 | `git diff examples/contracts/task_contracts.yaml` ⇒ **只新增**（`review_scored_deliverable`），无删除行 |
| 既有协议未改 | `git status --short examples/protocols/` ⇒ 只有新文件 |
| 全量定向套件 | `tests/loaders tests/contracts tests/domain tests/application tests/api` ⇒ **2372 passed, 77 skipped** |

### 4. 按压复核（AC-4，独立重跑）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | `declared_review_score` 回落 `Decimal("1")` | **1 failed, 2 passed**（缺来源臂假绿） |

按压后复原（重跑 3 passed）。

### 5. 门（独立重跑）

| 门 | 读数 |
| --- | --- |
| `mypy` / `ruff check` / `ruff format --check`（触及面） | 绿（gate 文件 mypy `Success`） |
| `tests/e2e` + `tests/tooling` | 1636 passed, 13 skipped |
| **as-is m0**（`--profile m0 --keep-going`，冻结树、记录写完之后） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5358 passed, 20 skipped**；收集数 +4 逐文件分解 = 新判据 3 例 + 源文件参数化 +1；`skipped` 20 未升；终局行取自 `scratch/m0-goal035-cycle3.log`） |

### 6. 未覆盖 / 一等边界

- 本复检只覆盖 **EC-03**；EC-04（自举收口）**尚未收口**（状态以 GOAL frontmatter 为准）；
- 分数来源是**评审交付物自己给的数**（模型自述的评审结论）：本判据证明「结论能进判据面且
  三态可判」，**不是**「分数一定正确」；**异构评审的分数聚合**仍未接线（`ReviewPanelRole`
  只在 preflight 的角色面有线）—— 如实保留为未覆盖；
- **不得**声明项目安全（`R-M1` 未收口）；**不得**宣称投递语义为那四个字（**明确否认**）。

## 结论

**PASS**。分数来源由合约**自己声明**的路径点名、判定仍走既有域函数（**未建第二套**、零 schema
改动）、三态判词逐字可读（判过 / 判负点名分数 / 缺来源 fail-closed 且无分数无算子）、
既有受判面**一字未动**（新增契约 + 新增协议），按压「回落默认分」判红并复原。
**未覆盖范围与一等边界逐条明写，不外推。**
