---
id: RECHECK-20261018-521
slug: goal-085-verdict-attribution-and-panel
title: 复检 — GOAL-085 cycle 1：判词点名模型 + 多评审聚合 + 独立性可判
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-520
parent_goal: GOAL-20261018-085
reviewer: root-agent
owners:
  - root-agent
verify_paths:
  - 三份新判据（归因 10 / 聚合 13 / 运行路径 6）
  - 应用面与宽面零回归（1201 + 3086）
  - 运行路径 e2e（371 passed）
memory_entries: []
---

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| EC-01 | 判词带 `reviewer_model`（`endpoint/model_name`） | **PASS** | `test_the_verdict_carries_the_reviewer_model`：`== "main/glm-5.3"` |
| EC-01 | 身份不是 agent 名 / profile 名 / model id | **PASS** | `test_the_target_is_not_the_agent_id_or_the_profile_name`：三条 `!=` 的机械分界 |
| EC-01 | 解析不了 ⇒ `None`（不拼半个目标） | **PASS** | `test_a_missing_endpoint_or_model_is_not_half_a_target` + `test_an_unattributed_verdict_stays_none` |
| EC-01 | 与 `review_independence` 同源 | **PASS** | `test_the_target_shape_matches_the_preflight_resolver`（两侧都是 `main/glm-5.3`） |
| EC-01 | `reviewed_by` 逐字不变 | **PASS** | `test_the_existing_reviewed_by_wording_is_unchanged`：`gate:reviewer_a` |
| EC-01 | 落库链搬运归因 | **PASS** | `test_the_run_chain_record_carries_the_reviewer_model` + 反证 `..._leaves_it_none_...` |
| EC-01 | sqlite round-trip | **PASS** | `test_the_sqlite_store_round_trips_the_reviewer_model` |
| EC-02 | 两票一致 ⇒ advisory | **PASS** | `test_two_agreeing_votes_produce_that_advisory` |
| EC-02 | **平票 ⇒ `None`** | **PASS** | `test_opposing_votes_are_a_tie_and_name_no_advisory`（`decided is False`） |
| EC-02 | 多数票 + 少数意见点名 | **PASS** | `test_majority_wins_and_the_minority_is_named`：`dissent == ("gate:reviewer_c:PASS",)` |
| EC-02 | 无身份者**不进票但点名** | **PASS** | `test_an_unattributed_finding_is_named_not_counted`：`voters == 1` 且 `ineligible` 点名 |
| EC-02 | 全失败 ⇒ 无票 | **PASS** | `test_all_failures_leave_no_advisory_and_no_voters` |
| EC-02 | **单评审不聚合** | **PASS** | `test_a_single_review_is_not_aggregated`（`None`） |
| EC-02 | 确定性 | **PASS** | `test_aggregation_is_deterministic`（20 次 `repr` 相同） |
| EC-03 | 异目标 ⇒ 独立 | **PASS** | `test_distinct_targets_are_independent` |
| EC-03 | **同目标 ⇒ 不独立并点名** | **PASS** | `test_the_same_target_twice_is_not_an_independent_panel` |
| EC-03 | **按压翻转** | **PASS** | `test_pointing_the_second_reviewer_back_flips_the_conclusion` |
| EC-03 | 同名不同 endpoint ⇒ 独立 | **PASS** | `test_the_same_model_name_on_different_endpoints_is_independent` |
| EC-03 | advisory 不夺真相权 | **PASS** | `test_the_aggregate_does_not_produce_a_decision`（源码级：无 `Decision(` / `decided_by`） |
| EC-04 | 读面带 `reviewer_model` | **PASS** | `test_each_verdict_names_its_model_on_the_read_face` |
| EC-04 | 单评审 ⇒ `panels == []` | **PASS** | `test_a_single_review_produces_no_panel` |
| EC-04 | 两模型 ⇒ 独立 panel | **PASS** | `test_two_distinct_models_produce_an_independent_panel` |
| EC-04 | 按压翻转（读面） | **PASS** | `test_pressing_the_second_model_to_the_first_flips_independence` |
| EC-04 | 不跨任务混票 | **PASS** | `test_panels_never_mix_two_tasks` |
| EC-04 | 无身份者读面点名 | **PASS** | `test_an_unattributed_verdict_is_named_on_the_read_face` |
| — | 应用面零回归 | **PASS** | `tests/application` ⇒ **1201 passed, 1 skipped** |
| — | 宽面零回归 | **PASS** | `tests/application tests/api tests/contracts tests/architecture tests/loaders tests/e2e` ⇒ **3086 passed, 94 skipped** |
| — | 静态门（规模） | **PASS** | `tests/tooling/test_python_source_limits.py` ⇒ **1289 passed**（含 `evaluate_task_gate` 拆函数后 ≤50 行、`task_phase_helpers` 440 行） |
| — | 静态门 | **PASS** | `ruff check` 绿；`ruff format --check` **1289 files**；`mypy` **1279 files, no issues** |
| — | as-is m0 | **PASS** | 静止工作树、记录写完之后：**`PASS: profile=m0; 23 deterministic checks`** |

## 既有判据是否被改动

**零改动**。本轮**只新增**判据文件（三份）与产品代码；既有的 `tests/**` 一个字未改。
`ReviewFinding` 的新字段**可空带缺省** ⇒ 既有构造点与断言逐字不变（1201 + 2729 + 371 的
零回归就是证据）。

`test_the_aggregate_does_not_produce_a_decision` 是本轮**新增**的射程边界判据
（源码级：聚合模块不得出现 `Decision(` / `decided_by`）—— 它保护「advisory 不夺真相权」。

## 警告（如实登记）

- **`W-2`**：**多数票不等于「对」**。本 GOAL 判的是**可归因与可聚合**，不判「哪一票更对」。
- **`W-3`**：只判模型**身份是否相同**，不判两个模型是否**同质化**（那需要任务级质量对比，
  射程外 —— 与 GOAL-084 的 `W-2` 同一条边界）。
- **`W-4`**：**不改**既有 `reviewed_by` 的写法（仍是 `gate:<agent id>`）；归因放在**新增**的
  `reviewer_model` 上。
- **`W-5`（本轮新增，如实登记）**：**两个评审实例的 `task_id` 必须相同才会被聚成一票**。
  这是有意的（不同任务评的是不同产物），但它意味着「跨任务的评审小组」**不在射程**。
- **`W-6`（本轮新增）**：`panels` 里**没有**「哪一票来自哪个 phase」这一格 —— 阶段归属要
  从 `reviews[].task_id` 反查。若将来需要「按阶段看小组」，那属新增读面字段。
- **`R-M1` 未收口** ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」（**明确否认**）。

## 未覆盖的面

- EC-05 自举收口；
- **真实模型在两个不同目标上各判一次并给出不同判词**（阶梯的下一级；需要 live run，
  本 GOAL 的 `W-3` 已登记该边界）。

## 结论

**PASS**。EC-01…EC-04 全部达成：判词**可归因到解析后的 `(endpoint, model_name)`**、
多票**确定性聚合**（平票与无身份者**分开点名**、advisory **不夺真相权**）、
**独立性与 GOAL-084 同源**（同目标两个实例 ⇒ 不独立并点名）、
读面与落库链**都**带着归因（不是只活在内存里）。

三份新判据 **29 条**；零回归 **1201**（application）+ **3086**（含 e2e 的宽面）；静态门全绿。**既有判据零改动**。
