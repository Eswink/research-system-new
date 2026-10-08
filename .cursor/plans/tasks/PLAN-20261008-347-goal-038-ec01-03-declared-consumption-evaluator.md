---
id: PLAN-20261008-347
slug: goal-038-ec01-03-declared-consumption-evaluator
title: GOAL-038 cycle 1（EC-01/EC-02/EC-03）：勘察定稿 + 声明式消费 + 编排层求值（`CUSTOM_EVALUATOR`）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-348-goal-038-ec01-03-declared-consumption-evaluator.md
memory_entries: []
parent_goal: GOAL-20261008-038
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-038 的 **EC-01 / EC-02 / EC-03**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：判定必须是**结构化**的（声明路径 → 取值 →
    与来源逐字比；**不得**文本子串巧合）；fail-closed（缺声明 / 缺路径 / 缺前序 ⇒ **点名**，
    不回落默认值）；**域层** `_evaluate_custom_evaluator` 的既有返回值语义**逐字不动**
    （它有既有判据把守，且它明说该由编排层执行）；**不改**任何既有判据的断言；
    **不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 `CUSTOM_EVALUATOR` 从「恒判负、由编排层执行」推进到**真的被求值**：
    ① **勘察定稿（EC-01）** —— 域与合约面已在场、域求值器恒判负、编排层零实现；
    ② **声明式消费（EC-02）** —— 合约用**既有** `metric` 字段声明消费路径；解析器
    fail-closed 三态；
    ③ **编排层求值（EC-03）** —— 结构化比对（本轮产物声明路径的取值 vs 前序 run 落库的
    结论逐字）；相等判过留痕（含来源 run id）/ 不等点名两侧值 / 缺席点名；结论经
    `EvaluationInputs.consumption` **贴回判据下标**，判词进**既有**读面。
exit_criteria:
  - id: AC-1
    criterion: >-
      **勘察定稿（读数逐条）**：`AcceptanceCriterionType.CUSTOM_EVALUATOR` 与
      `AcceptanceCriterion.evaluator`（+ `schemas/task-contract.schema.json` 的 `evaluator`
      字段）在场；`_evaluate_custom_evaluator` 恒判负且含「must be executed by the
      orchestration layer」；`rg` 全仓该求值器**零命中**（除域类型 / 域求值器 / 既有用例）。
    verify: >-
      `rg -n "CUSTOM_EVALUATOR|evaluator" packages/ services/ adapters/ examples/ schemas/`
      读数逐条。
    status: PASS
  - id: AC-2
    criterion: >-
      **声明式消费（fail-closed 三态）**：`declared_consumption.py` 按 `metric` 点分路径
      取值；未声明 / 路径缺失 / 值不可取 ⇒ **逐条点名**；未认得的求值器 id ⇒ 点名
      （不静默当作无此判据）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_declared_consumption.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **编排层求值 + 接线**：结构化比对（相等 ⇒ 判过且判词含来源 run id 与逐字值；不等 ⇒
      点名期望值 / 实际值；前序缺席 ⇒ 点名）；**整段文本含来源串不算消费成立**（反文本巧合）；
      结论经 `EvaluationInputs.consumption` 贴回判据下标；**未注入 ⇒ 域层既有判词逐字保留**。
    verify: >-
      同上判据文件的接线用例 + 门面（`evaluate_task_gate`）判定逐条。
    status: PASS
  - id: AC-4
    criterion: >-
      **门链 + 记录面**：四道门绿（ruff / format / mypy / 规模）；记录（本 PLAN、
      `RECHECK-20261008-348`）；治理 `validate.py` 绿；受影响套件全绿。
    verify: >-
      门读数逐条 + `tests/application tests/domain` 读数。
    status: PASS
---

# PLAN-20261008-347 — GOAL-038 cycle 1（EC-01/02/03）

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 勘察定稿（读数逐条） | PASS |
| AC-2 | 声明式消费（fail-closed 三态 + 未知求值器点名） | PASS |
| AC-3 | 编排层求值 + 接线（结构化比对；未注入时域层判词逐字保留） | PASS |
| AC-4 | 四道门 + 记录面 + 治理 | PASS |

## 实施清单

- [x] `packages/application/run_orchestration/declared_consumption.py`：声明解析 + 取值 +
      结构化比对（fail-closed 三态 + 未知求值器点名）。
- [x] `packages/application/run_orchestration/evaluation_gate.py`：`EvaluationInputs.consumption`
      注入位 + `_apply_consumption`（**只在给了结论时替换**；顺序与声明同序）。
- [x] `tests/application/run_orchestration/test_declared_consumption.py`：12 例。
- [x] 记录面：本 PLAN、`RECHECK-20261008-348`、GOAL 行、`ALL_PLAN`。

## 证据

### 交付面（WP）

| # | WP | 交付面 |
| --- | --- | --- |
| WP-1 | 求值器 | `packages/application/run_orchestration/declared_consumption.py`（`EVALUATOR_ID = "cross_run_consumption"`；`resolve_consumption` / `resolve_consumption_evaluations` / `declared_consumption_criteria`） |
| WP-2 | 门接线 | `packages/application/run_orchestration/evaluation_gate.py`（`EvaluationInputs.consumption` + `_apply_consumption`） |
| WP-3 | 判据 | `tests/application/run_orchestration/test_declared_consumption.py`（12 例） |
| WP-4 | 记录面 | 本 PLAN、`RECHECK-20261008-348`、GOAL 迭代日志 / 状态历史、`ALL_PLAN` |

### 判据要点（逐条可被单变量按压）

| 断言 | 形态 |
| --- | --- |
| 主路 | 值 == 前序结论 ⇒ `passed is True`；判词含**来源 run id** 与逐字值 |
| 不一致 | 判负且**两侧值都点名**（`'REJECT'` 与 `'PASS'` 同时在判词） |
| fail-closed 三态 | 未声明 ⇒ 「未声明消费路径」；路径缺失 ⇒ 「缺失」+ 路径名；前序缺席 ⇒ 「没有前序结论」 |
| 未知求值器 | 「不认识这个求值器」+ id 点名 |
| **反文本巧合** | 整段文本**含**来源串 ⇒ 仍判负（结构化比对，不是子串包含） |
| 门接线 | 注入 ⇒ 门判 `PASS` 且判词含来源 run id；**未注入 ⇒ 域层判词逐字保留** |

### 门（实测读数）

| 门 | 读数 |
| --- | --- |
| `ruff check`（改动面） | `All checks passed!` |
| `ruff format --check` | 绿（两文件 left unchanged） |
| `mypy`（strict，全仓） | `Success: no issues found in 1163 source files` |
| 新判据 | `tests/application/run_orchestration/test_declared_consumption.py` **12 passed** |
| 受影响套件 | `tests/application + tests/domain + tests/tooling/test_python_source_limits.py` **2412 passed, 1 skipped** |

## 无可复用事实

本 cycle 的机制（声明路径的 fail-closed 三态）与 GOAL-035 EC-03 的
`declared_review_score` 同一口径，其可复用事实已由既有记录承载；本轮未产生新的可复用事实。

## 影响报告

- **Domain / API / schema 变化**：**零**（域层与 schema **一字未动**；本轮只在编排层新增
  求值器 + 一个注入位）。
- **安全 / 凭据变化**：无（不动放行面 / 不动承接面）。
- **兼容性 / 迁移风险**：无（新字段缺省为空映射 ⇒ 既有调用方行为**逐字不变**，由「未注入 ⇒
  域层判词逐字保留」那条判据钉住）。
- **观测隐私**：判词只含路径名 / 逐字值与来源 run id（不含新敏感面）。
- **上游版本影响**：无。
- **下一项任务**：cycle 2（EC-04 两轮实跑 + 两向反证）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 三条 AC 落地：声明式消费 + 编排层求值 + 门接线；判据 12 例全绿；四道门绿。 |
| 2026-10-08 | DONE | 四条 AC 全 PASS；`RECHECK-20261008-348` 独立复检。域层与 schema 零改动；未注入时域层判词逐字保留（兼容性由判据钉住）。 |
