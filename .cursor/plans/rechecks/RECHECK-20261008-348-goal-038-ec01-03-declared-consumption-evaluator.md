---
id: RECHECK-20261008-348
slug: goal-038-ec01-03-declared-consumption-evaluator
title: 独立复检：GOAL-038 cycle 1（EC-01/02/03）声明式消费与编排层求值
plan_id: PLAN-20261008-347
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-348 — GOAL-038 cycle 1 独立复检

复检对象：`PLAN-20261008-347`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察定稿（AC-1）

| 读法 | 读数 |
| --- | --- |
| 域类型 | `AcceptanceCriterionType.CUSTOM_EVALUATOR` 在 `packages/domain/enums.py` |
| 合约字段 | `AcceptanceCriterion.evaluator` 在 `packages/domain/tasks.py`；schema 字段在 `schemas/task-contract.schema.json` |
| 域求值器恒判负 | `_evaluate_custom_evaluator` 返回 `passed=False` + 「must be executed by the orchestration layer」 |
| 编排层零实现（建档时） | `rg` 在 `packages/ services/ adapters/ examples/` 零命中（本 cycle 新增 `declared_consumption.py` 后**本行读数即历史事实**） |

### 2. 声明式消费（AC-2）

| 读法 | 读数 |
| --- | --- |
| 判据 | `tests/application/run_orchestration/test_declared_consumption.py` **12 passed** |
| fail-closed 三态 | 未声明 / 路径缺失 / 前序缺席 **逐条点名**（三条用例各自断言判词子串） |
| 未知求值器 | 「不认识这个求值器」+ id（用例断言） |

### 3. 编排层求值 + 接线（AC-3）

| 读法 | 读数 |
| --- | --- |
| 结构化比对 | 相等判过（判词含来源 run id）；不等**两侧值都点名** |
| **反文本巧合** | 整段文本含来源串 ⇒ 仍判负（`test_structured_values_are_compared_not_substrings`） |
| 门接线 | 注入 ⇒ `evaluate_task_gate` 判 `PASS`；**未注入 ⇒ 域层判词逐字保留**（两条独立用例） |
| 兼容性 | `evaluate_task_gate` 的调用方（`task_phase_helpers` / `scorers_runtime`）**一字未改**（缺省空映射） |

### 4. 门链与记录面（AC-4）

`ruff check` / `format --check` / `mypy`（1163 files）全绿；新判据 12 passed；
受影响套件 `tests/application + tests/domain + tests/tooling/test_python_source_limits.py`
**2412 passed, 1 skipped**。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立；**域层与 schema 零改动**。

### Warnings

- **W-1（判据只到「携带」不到「因果」）**：判过 = 那条声明路径的值与前序落库结论**逐字一致**；
  **未**证「因为读了它才这么写」（因果不可判 —— 它是过程面事实）。这一条已写进 GOAL 的
  本轮残余。
- **W-2（求值器 id 是白名单）**：本轮只认 `cross_run_consumption`；别的 id ⇒ **点名**
  （不静默）。插化注册（插件化求值器）不在本轮范围，已登记为本 GOAL 的未覆盖面。
- **W-3（承继残余原样保持）**：GOAL-037 的 `O-1`…`O-5`（其中 `O-4` 是**本 GOAL 的立项依据**）、
  `M-1`…`M-5`、`R26-*` 终态、未覆盖范围逐条保持；**不得**据此宣称项目安全；
  **不得**宣称投递语义为那四个字（**明确否认**）。
