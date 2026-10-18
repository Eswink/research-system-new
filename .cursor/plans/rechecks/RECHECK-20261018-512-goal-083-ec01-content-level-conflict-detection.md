---
id: RECHECK-20261018-512
slug: goal-083-ec01-content-level-conflict-detection
title: GOAL-083 cycle 1 复检 — 记忆的内容级冲突检测
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-511
parent_goal: GOAL-20261018-083
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261018-512 — GOAL-083 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **三种形态判得出** | **PASS** | `test_content_conflict_detection.py` 的 6 条正向：否定极性 / 数值方向（带单位）/ 反义谓词（中英各一） |
| AC-2 | **对称 + 确定** | **PASS** | `test_detection_is_symmetric`（`(a,b)` 与 `(b,a)` 同形态同核）+ `test_repeated_calls_are_byte_identical`（50 次逐字相同） |
| AC-3 | **零出网 / 零模型 / 零时钟 / 零随机** | **PASS** | `test_the_decider_has_no_io_imports`（AST 扫 import 黑名单）+ `test_the_decider_reads_no_clock_or_randomness`（源码级） |
| AC-4 | **未声明但相反 ⇒ 判拒并点名** | **PASS** | `test_undeclared_opposite_content_is_rejected_with_the_id_and_form`：判词含对方 id + `NEGATION_POLARITY` |
| AC-5 | **既有语义逐字不变** | **PASS** | `test_reference_integrity_is_unchanged`（两条既有判词原文）/ `test_self_contradiction_is_still_rejected` / `test_a_declared_conflict_still_wins_over_content` |
| AC-6 | **三条边界** | **PASS** | `test_only_the_same_scope_is_scanned` / `test_inactive_records_do_not_participate` / `test_consistent_content_is_accepted` |
| AC-7 | **按压：关掉判定 ⇒ 通过** | **PASS** | `test_press_disabling_the_content_check_lets_it_through`（同输入、只改判定在不在，读数相反） |
| AC-8 | **两种来源分得开** | **PASS** | `test_reference_integrity_and_content_conflict_use_distinguishable_wordings`：一侧点 `does not exist`、另一侧点 `content contradicts` + 形态，**互不包含** |
| AC-9 | **同阶段（不新造第六段）** | **PASS** | `test_both_sources_land_on_the_same_stage` |
| AC-10 | **API 缺口被钉住** | **PASS** | `test_the_http_proposal_dto_does_not_expose_declarations`：`contradictions` **不在** `MemoryProposalDto.model_fields` |
| AC-11 | **真实语料零误报** | **PASS** | `test_content_conflict_precision.py` 24 条：同义 4 / 无关 5 / 真实语料 7 / 射程边界 4 / 非空转对照 2 |
| AC-12 | **零回归** | **PASS** | `tests/application` + `tests/api/test_memory_api.py` = **1171 passed, 1 skipped**（既有 memory 套件 139 + 183 全绿） |
| AC-13 | **静态门** | **PASS** | `ruff check` 绿；`mypy` **1269 files, no issues**；两文件 298 / 292 行（≤450）、无 >50 行函数 |

## 警告（如实登记）

- **`W-1`**：**EC-03 是改判的**。原判据写成 e2e「读两种 422 判词」，实测发现
  `MemoryProposalDto` 不接受 `contradictions` ⇒ **HTTP 写面没有「声明冲突」这条路**，
  读面上不可能有两种来源。已改判到**门链层**（两种来源唯一共存的层），并新增一条断言
  **钉住该缺口**（将来补入口时会红 —— 那是「该更新判据」的信号，不是让它默默变绿）。
- **`W-2`**：**射程是形态级**。世界知识级矛盾（`the drug is effective` vs `it does not work`）、
  同义改写（`increase` vs `rise`）、需要推演的数值（`2x` vs `twice`）**明确不判** ——
  判据在 `_OUT_OF_SCOPE` 里**断言它们 `None`**（与「零误报」同等重要）。
- **`W-3`**：**无单位数字不判**（`W-6`）：`the metric is 2.0` vs `0.5` 在无单位时**不判** ——
  实测三条误报（`mem-1`/`内容 1`/`pipeline A ... B`）证明无单位数字无法与编号区分。
  **这是取舍不是遗漏**：代价是「纯数字分歧」不在射程。
- **`W-4`**：**不做存量补判**：判定只在**写入时**（提案 vs 现行记录），已存在的矛盾记录
  不会被回溯标记（那属迁移）。
- **`W-5`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- EC-05 自举收口。

## 结论

**PASS_WITH_WARNINGS**。四种形态/边界各有判据（**60 条**），零回归（application **1171 passed**），
静态门全绿。核心读数：**未声明但内容相反 ⇒ 判拒并点名对方 id 与判词形态**；**关掉判定 ⇒ 通过**
（按压成立）；**真实语料零误报**。

两条如实登记的边界：`W-1`（EC-03 因 API 缺声明入口而**改判**到门链层）、`W-3`（无单位数字不判）。
