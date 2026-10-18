---
id: RECHECK-20261018-516
slug: goal-084-ec01-review-independence-by-resolved-target
title: GOAL-084 cycle 1 复检 — 评审独立性的解析面与判定面
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-515
parent_goal: GOAL-20261018-084
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261018-516 — GOAL-084 cycle 1

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | **EXPLICIT_MODEL 解析成一个目标** | **PASS** | `test_explicit_model_resolves_to_one_target` |
| AC-2 | **MODEL_PROFILE 含 primary + 每个 fallback** | **PASS** | `test_profile_includes_primary_and_every_fallback`（三个目标） |
| AC-3 | **同名不同 endpoint ≠ 同一目标** | **PASS** | `test_same_model_name_on_different_endpoints_is_not_the_same_target` |
| AC-4 | **解析不了 ⇒ 点名（不静默空集）** | **PASS** | `test_unresolvable_bindings_are_named_not_silently_empty`（缺 model / 缺 profile / INHERIT 三形态） |
| AC-5 | **解析确定性** | **PASS** | `test_resolution_is_deterministic`（20 次同结果） |
| AC-6 | **出厂目录四个 ModelDefinition 全同 `model_name`+endpoint** | **PASS** | `test_the_factory_catalog_has_the_same_model_name_everywhere`（**钉住事实**：接入第二个模型时会红） |
| AC-7 | **生产者与评审者在出厂目录下相交** | **PASS** | `test_the_reviewer_and_the_producer_resolve_to_the_same_target_in_the_factory` |
| AC-8 | **绑定 id 不同但目标相同** | **PASS** | `test_comparing_binding_ids_would_have_passed_but_targets_do_not` |
| AC-9 | **fallback 造出相交** | **PASS** | `test_fallback_creates_a_shared_target_even_when_primary_differs`（primary 不同、fallback 相交） |
| AC-10 | **反证：清空 fallback ⇒ 相交消失** | **PASS** | `test_clearing_the_fallback_removes_the_overlap` |
| AC-11 | **`critic_independent` 可回落到 `research_alpha`** | **PASS** | `test_the_factory_critic_independent_profile_can_fall_back_to_the_producers_model` |
| AC-12 | **门链命中 ⇒ 点名目标与两侧角色** | **PASS** | `test_the_gate_rejects_a_shared_underlying_model_and_names_the_target`（判词含 `ep/shared-name` + 两个 role id） |
| AC-13 | **不相交 ⇒ 不判** | **PASS** | `test_the_gate_passes_when_the_underlying_models_differ` |
| AC-14 | **按压：关掉目标解析 ⇒ 回落 id ⇒ 变绿** | **PASS** | `test_press_comparing_ids_only_would_pass` |
| AC-15 | **同源**：门链用同一个解析器（不是第二套） | **PASS** | `test_the_gate_reads_the_same_resolution_helper` |
| AC-16 | **判据不写死出厂标识** | **PASS** | `test_profiles_and_models_are_not_hardcoded_in_the_check`（实现体里无 `research_strong` / `reviewer_gamma` / `research_alpha`） |
| AC-17 | **零回归** | **PASS** | application + loaders + contracts **1735 passed, 73 skipped** |
| AC-18 | **静态门 / 规模门** | **PASS** | ruff 绿；mypy **1272 files, no issues**；规模门 **1282 passed**（四文件 153/310/302/146 行） |
| AC-19 | **出厂目录零改动** | **PASS** | `examples/config/**` 无改动（`git status` 可证） |

## 警告（如实登记）

- **`W-1`**：**既有用例随语义收紧而改**。`test_heterogeneity_allows_distinct_models` 原先把
  「同 `model_name` 的两个 id」当成「不同模型」—— 按新口径那是**同一个底层模型**。
  处置 = **收紧**该用例（`model-2` 改成不同 `model_name`）+ **新增一条反证**
  （`test_a_model_with_the_same_underlying_name_is_not_distinct`）。
  **逐条申报**：删 2 行、改 4 行、新增 38 行；其余用例一字未动。这是**收紧**不是放宽：
  原用例考的行为在新语义下不再成立。
- **`W-2`**：**只判「模型是否同一个」**，不判「评审是否独立判断」—— 同模型可以给不同结论，
  不同模型也可能同质化。可判的只有「底层模型 + endpoint 是否相同」这一格。
- **`W-3`**：**不采购第二个模型**。本轮把问题**判出来**（出厂目录判「不独立」）；
  真正实现独立需要新 endpoint/model（上游与凭据变更，需拍板）。
- **`W-4`**：**只判协议声明的评审关系**（`review_panel_role` 聚合）；没声明的协议**不判**。
- **`W-5`**：**回落路径的两个口径并存**（解析成功比目标、解析失败比 id）——
  这是为了保住既有夹具的零回归。**它不会把「解析失败」当成「独立」**，
  但意味着「某个装配只给 id 不给 catalog」时判定会比新口径**更松**（等价旧行为）。
- **`W-6`**：`R-M1` 未收口 ⇒ 本记录**不**作任何安全结论；投递语义**不是**「恰好一次」。

## 未覆盖的面

- EC-05 自举收口。

## 结论

**PASS_WITH_WARNINGS**。23 条判据（13 + 5 + 5）全绿，零回归 **1735 passed**，出厂目录
**一字未改**。

核心读数：出厂目录下 `research_strong`（生产者）与 `reviewer_gamma`（评审者）
**解析到同一个 `endpoint/model_name`** —— 尽管绑定 id 与 profile 名**都不同**；
`fallback` 让问题更深（`critic_independent.fallback` 含 `research_alpha`）。
门链 `check_heterogeneity` 的判定面已从 model id 换成**解析后的目标**，命中时**点名**
目标与两侧角色；按压证明拒绝来自目标比较（关掉解析 ⇒ 回落 id ⇒ 变绿）。

一条既有用例**随语义收紧**（`W-1`，已逐条申报）。
