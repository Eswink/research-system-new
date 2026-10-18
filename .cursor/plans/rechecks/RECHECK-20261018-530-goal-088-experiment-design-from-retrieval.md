---
id: RECHECK-20261018-530
slug: goal-088-experiment-design-from-retrieval
title: GOAL-088 cycle 1 复检 —— 实验设计由检索证据派生（EC-01…EC-04）
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-529
parent_goal: GOAL-20261018-088
owners:
  - root-agent
verify_paths:
  - tests/application/test_experiment_design_from_retrieval.py
  - tests/application/test_experiment_design_decides.py
  - packages/application/experiments/design_from_retrieval.py
memory_entries: []
---

# RECHECK-20261018-530 — GOAL-088 cycle 1

## 检查结果

### EC-01 —— 设计由检索记录派生

- **正向**：`design_source="retrieval"` + 一条 `RETRIEVED` 的工具结果记录带设计块 ⇒
  `_arms_for` 返回的臂**就是**记录里那些（`from_retrieval_a` 带 `n_items: 40`）。
- **换记录 ⇒ 换设计**：同一装配、两份不同记录 ⇒ `["only_arm"]` vs
  `["control", "treatment"]`。
- **来源可归因**：读出的设计 `arm_source_evidence == ("evidence:named",)`、
  `run_id` 逐字 —— 「从哪条证据读的」可复核。

### EC-02 —— 性质维度不可伪造 + run 作用域

- **性质**：同一条内容来源标成 `USER_PROVIDED` ⇒ 点名
  `no system-retrieved evidence`（**不算**检索派生）。
- **作用域**：记录挂在**另一个 run** 下 ⇒ 同样 `no system-retrieved evidence`。

### EC-03 —— 来源唯一 + fail-closed 逐条点名

- `retrieval` + 显式 `arms` 同场 ⇒ 点名含 `undecidable` 与那个臂名；
- 记录里**没有**设计块 ⇒ 点名含 `experiment_design`；
- **两份设计** ⇒ 点名含 `more than one`（**不**取最后一条）；
- 参数越白名单 ⇒ 点名含 `outside the whitelist` 与那个键；
- **未声明来源** ⇒ 既有装配面语义（由 `test_experiment_design_decides.py` 的零回归组判）。

### EC-04 —— 两个来源真的不同且 `plan` 逐字不变

- `DESIGN_SOURCES == (plan, retrieval)` 且两者不相等；未认得来源仍点名
  `unknown experiment design source`。
- **零回归**：既有实验判据 **40 passed**（`test_experiment_design_decides` /
  `test_experiment_parameters` / `test_experiment_design_from_the_plan` /
  `test_two_arm_experiment_offline`）。

### 静态门

| 面 | 读数 |
| --- | --- |
| 新判据 | **10 passed** |
| 既有实验判据 | **40 passed** |
| `ruff check` / `ruff format --check` / `mypy` | 全绿（含 `services/api/experiment_support.py`） |

## 结论

**PASS**。EC-01…EC-04 达成：设计可以从**系统真的取回了什么**里读出，性质维度不可伪造，
冲突与畸形逐条点名，既有 `plan` 来源与未声明来源的行为逐字不变。
EC-05（自举收口）由收口 cycle 承担 —— 本文件的 PASS **不**覆盖它。
