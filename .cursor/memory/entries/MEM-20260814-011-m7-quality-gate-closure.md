---
id: MEM-20260814-011
title: M7 Quality Gate Closure 修复事实
status: ACTIVE
created_at: 2026-08-14
updated_at: 2026-08-14
scope: repository
confidence: 0.9
review_after: 2026-11-14
source_plans:
  - .cursor/plans/tasks/PLAN-20260814-011-m7-quality-gate-closure.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260814-011-m7-quality-gate-closure.md
supersedes: []
tags: [m7, quality-gate, mypy, ruff, closure]
---

# MEM-20260814-011 — M7 Quality Gate Closure 修复事实

## 做了什么

修复 M7 交付后 m0 profile 的确定性门禁红灯（2026-08-14 实测）：ruff
product-lint 4 errors + format 12 files + mypy strict 16 errors → 全绿。
修复面（全部为类型/导入/格式层，零行为变更）：

1. `packages/application/preflight/preflight.py`：`frozen_contracts` 显式
   注解 `dict[str, object]`，与 `RunManifest.task_contracts` 的
   `dict[str, object]` 字段对齐（mypy dict 不变性方差）。
2. `tests/application/test_m2_policy_budget.py`：测试内 `Reserver` 补齐
   BudgetLedger protocol 缺失的 `release` 方法（runtime_checkable
   protocol 成员不全时报 [arg-type]）。
3. `tests/e2e/test_run_rejections.py`：`ModelDefinition.capabilities` 键
   从字符串字面量改为 `ModelCapability` 枚举（dict-item 类型不匹配）。
4. `tests/e2e/test_fault_convergence.py`：`_start` 返回类型从 `object`
   改为 `RunOutcome`。
5. `tests/e2e/test_cancel_resume.py`：`_drift_parts` 从
   `tuple[object, dict[str, object]]` 改为 TypedDict `DriftParts` +
   `RunManifest` 精确类型化。

## 为什么这样做

m0 profile 是每阶段/每次变更的确定性验收门禁；M7 交付时遗留的红灯使
后续所有工作无法在绿门上验证。修复是 M7 收尾工程债（BACKLOG P1），
不改变产品行为，仅消除类型/格式噪音。

## 怎么做与复现

1. `uv run --frozen --no-sync python -m ruff check packages adapters tests`
   （0 errors）
2. `uv run --frozen --no-sync python -m ruff format --check ...`（244 files）
3. `uv run --frozen --no-sync python -m mypy`（227 files Success）
4. `uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`
   （pytest 989 passed；双 validator PASS；唯一 FAIL 为 learning-evals P2）

## 适用边界

- 适用于：M7 质量门禁状态引用；后续产品能力（Tool Plane 等）以
  m0 profile 全绿为起点。
- 不适用于：learning-evals（LEARN registry）修复——属 `.cursor/learning/`
  资产（P2），走 capture-learning/consolidate-learning 流程；产品行为
  变更（本记忆对应修复不改变运行时语义）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-14）时先复核再引用。
- `RunManifest` 字段类型或 BudgetLedger protocol 变化时，对应修复的
  具体形态可能过时，但"mypy strict 必须全绿"的约束不变。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260814-011-m7-quality-gate-closure.md` | 任务范围与 AC |
| recheck | `.cursor/plans/rechecks/RECHECK-20260814-011-m7-quality-gate-closure.md` | 2026-08-14 实际重跑验证 |
| repository | `packages/application/preflight/preflight.py`、`tests/application/test_m2_policy_budget.py`、`tests/e2e/` | 修复位置 |
| check | m0 profile 输出（2026-08-14） | ruff/mypy/pytest 全绿证据 |