---
id: RECHECK-20261008-356
slug: goal-040-ec02-04-stop-reasons
title: 独立复检：GOAL-040 cycle 1（EC-02/03/04）判定种类 / 终态分派 / 实跑反证
plan_id: PLAN-20261008-355
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-08
completed_at: 2026-10-08
owners:
  - root-agent
---

# RECHECK-20261008-356 — GOAL-040 cycle 1 独立复检

复检对象：`PLAN-20261008-355`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 判定种类扩齐 + 声明落库（AC-1）

| 读法 | 读数 |
| --- | --- |
| 枚举 | `ProgramDecisionKind` 九种（原六 + `STOP_RUN_FAILED` / `STOP_CANCELLED` / `RETRY_FAILED_RUN`），域判据断言九种集合 |
| 声明 | `ResearchProgram.max_attempts_per_index`（缺省 1、`>=1` 校验）；驱动判据覆盖缺省不重试 |
| 落库 | 迁移 019 在树；live PG 实测 `migration_version` 最新 = **19**、列清单实见该列；`tests/postgres/test_program_store_pg.py` 2 passed |

### 2. 按终态分派（AC-2）

驱动判据 **13 passed**（独立重跑），关键五条：① 失败轮 ⇒ `STOP_RUN_FAILED` + `state=FAILED`
+ 「未获结论」；② **反证**：失败轮**不**落「`STOP_RULE` + 空 `cited_facts`」；③ 取消 ⇒
`STOP_CANCELLED` 且**不**重试；④ 声明重试 ⇒ `RETRY_FAILED_RUN` + **同序号** + `attempts=1/2`，
用尽 ⇒ `STOP_RUN_FAILED` + `attempts=2/2` + 「重试已用尽」；⑤ 成功路径仍走结论面（`CONTINUE`）。

### 3. 实跑取证（AC-3）

`tests/e2e/test_program_stop_reasons_are_decidable.py` **4 passed**（独立重跑）。

### 4. 门链与记录面（AC-4）

`ruff` / `format` / `mypy`（1168 files）全绿；广面 **5138 passed, 18 skipped**；
`tests/contracts + tests/observability` **661 passed, 74 skipped**；OpenAPI 快照同轮重生成。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立。

### Warnings

- **W-1（三处既有 e2e 用例更新）**：本轮把失败轮从「结论面」移到「失败面」⇒ 三条既有用例
  原先**依赖旧的失真行为**（靠「失败轮被判续 ⇒ 还能起第 2 轮」取第 2 轮判词）。
  **先在干净树 `49b2c7d` 上复跑确认它们原先通过**（证明是行为修正、不是环境漂移），
  再按新语义更新；**断言强度未降**（都仍在断言「点名」这一实质）。
- **W-2（本轮不覆盖失败后的自动处置）**：重试**有界**但**无退避**；任务级重试与跨程序
  失败传播不在本轮。
- **W-3（承继残余原样保持）**：GOAL-039 的 `Q-1`…`Q-3`、GOAL-038 的 `P-1`…`P-3`、
  GOAL-037 的 `O-1`…`O-5`、`R26-*` 终态、未覆盖范围逐条保持；**不得**据此宣称项目安全；
  **不得**宣称投递语义为那四个字（**明确否认**）。
