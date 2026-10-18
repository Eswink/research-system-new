---
id: RECHECK-20261018-518
slug: goal-084-review-independence-on-a-distinct-model
title: 复检 — GOAL-084 cycle 2：评审独立性按解析后的目标判，且评审者落在真不同的模型上
status: COMPLETED
result: PASS
created_at: 2026-10-18
updated_at: 2026-10-18
plan_id: PLAN-20261018-517
parent_goal: GOAL-20261018-084
reviewer: root-agent
owners:
  - root-agent
verify_paths:
  - 离线判据（21 条新判据 + 5 条异构专项 + 28 条受影响 API）
  - 产品路径反向按压（`compile_and_preflight` 走 `services.api.catalog`）
  - 宽面零回归（`tests/application tests/api tests/loaders tests/contracts tests/architecture`）
memory_entries: []
---

## 复检口径

不复用 PLAN / GOAL 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| EC-01 | **解析面**：全部可能目标（primary + 每个 fallback）成集合；解析不了点名 | **PASS** | `test_review_independence.py` **8 passed**，含 `test_profile_includes_primary_and_every_fallback` / `test_unresolvable_bindings_are_named_not_silently_empty` / `test_the_resolver_makes_no_outbound_calls` |
| EC-02 | **判定面按解析目标**：出厂目录不相交；指回生产者模型 ⇒ 判红 | **PASS** | `test_review_independence_judgment.py`：`test_the_factory_reviewer_and_producer_sit_on_different_underlying_models`（`main/deepseek-v4-flash-vision` vs `main/glm-5.3` vs `main/kimi-k2.6`，**逐对**不相交）+ `test_binding_ids_alone_do_not_decide_independence`（`resolved_models` 相同、只改 `model_name` ⇒ 结论翻转） |
| EC-03 | **fallback 覆盖**：相交即判出并点名；清空 ⇒ 消失；两个方向都判 | **PASS** | `test_a_fallback_creates_the_overlap_even_when_primaries_differ` / `test_clearing_the_fallback_removes_the_overlap` / `test_a_fallback_to_a_producer_model_is_caught_through_a_profile` |
| EC-04 | **产品路径**：`m12` 不再拒冻；按压仍咬；未声明不判；按压不改树 | **PASS** | `preflight/test_review_independence_gate.py` **4 passed**；手工按压读数见下节 |
| — | **受影响 API 恢复** | **PASS** | forecast / draft-run-linkage / failed-run-digest = **28 passed** |
| — | **宽面零回归** | **PASS** | `tests/application tests/api tests/loaders tests/contracts tests/architecture` = **2708 passed, 77 skipped** |
| — | **静态门** | **PASS** | `mypy packages/application/preflight/` = `Success: no issues found in 10 source files`；`ruff check`（改动文件）= `All checks passed!` |

## 每条 EC 的读数与两向反证

**BLOCKED-084 解除**：cycle 1 记的三条出路之外存在第四条且最简单 ——
**给评审者换一个真不同的 `model_name`**（同端点、同凭据）。本轮按它落地，判据与出厂目录
**同时成立**：`m12_reference_research_v1` 不再被 `HETEROGENEITY_VIOLATION` 拒冻，而把评审者
指回生产者的模型时**判据仍然咬得住**。

### EC-01 解析面（8 条判据）

| 判据 | 断言 | 读数 |
| --- | --- | --- |
| `test_explicit_model_resolves_to_a_single_target` | `EXPLICIT_MODEL` ⇒ 单元目标 | PASS |
| `test_profile_includes_primary_and_every_fallback` | `primary` + **每个** fallback（含跨 endpoint） | PASS |
| `test_same_model_name_on_different_endpoints_is_a_different_target` | 同名不同 endpoint **不算**同一个 | PASS |
| `test_unresolvable_bindings_are_named_not_silently_empty` | 缺 model / 缺 profile / `INHERIT` 裸绑 ⇒ **`problems` 非空** | PASS |
| `test_compiled_primary_covers_inherit_bindings_and_still_expands_fallbacks` | 无编译值 ⇒ 点名；有编译值 ⇒ primary + fallback 都进集合 | PASS |
| `test_resolution_is_deterministic` | 20 次运行结果集合恒等 | PASS |
| `test_describe_target_is_stable_and_readable` | 判词形态 `endpoint/model_name` | PASS |
| `test_the_resolver_makes_no_outbound_calls` | 模块源码不 import 网络/网关面（**零出网**） | PASS |

**反证**：`test_unresolvable_bindings_are_named_not_silently_empty` 的受判面**非空**
（三条都真的产出 `problems`），且与 `resolved` 属性成对（`not resolved`）。

### EC-02 判定面（5 条判据，正向 + 反向成对）

| 判据 | 读数 |
| --- | --- |
| `test_the_factory_reviewer_and_producer_sit_on_different_underlying_models` | 生产者 = `main/deepseek-v4-flash-vision`；`reviewer_a` = `main/glm-5.3`；`reviewer_b` = `main/kimi-k2.6`；**逐对**不相交（非并集掩蔽） |
| `test_the_critic_profile_no_longer_falls_back_to_the_producers_model` | `critic_independent.fallback == []`，且与生产者的模型名集合不相交 |
| `test_the_gate_passes_for_distinct_underlying_models` | 底层不同 ⇒ `[]`（先断言两 agent 都被解析：`{prod, rev}`） |
| `test_the_gate_fails_when_two_ids_share_one_underlying_model_name` | 底层相同 ⇒ **恰好 1 条** `HETEROGENEITY_VIOLATION`，点名 `ep/deepseek-v4-flash-vision` 与两侧 role |
| `test_binding_ids_alone_do_not_decide_independence` | 两个 plan 的 `resolved_models` **完全相同**（`{w: prod, r: rev}`），只改 `model_name` ⇒ **结论翻转** |

### EC-03 fallback（3 条判据）

| 判据 | 读数 |
| --- | --- |
| `test_a_fallback_creates_the_overlap_even_when_primaries_differ` | primary 不同（`{w: prod, r: rev}` 已断言）但 fallback 相交 ⇒ 判红并点名 `ep/reviewer-underlying` |
| `test_clearing_the_fallback_removes_the_overlap` | 有 fallback ⇒ 判红；清空 ⇒ `[]`（**同一组模型、同一组绑定**，只差 fallback） |
| `test_a_fallback_to_a_producer_model_is_caught_through_a_profile` | **反方向**（评审者回落到生产者）也判出并点名 `ep/producer-underlying` |
| `test_an_unresolvable_role_is_named_instead_of_silently_passing` | 编译期只解析出 writer（`{w: prod}`）⇒ 判定面给出**恰好 1 条** `MODEL_MISSING`，点名 `ghost` 与 `role:g084_reviewer_role` |

### EC-04 产品路径（4 条判据 + 一次手工按压）

| 判据 | 读数 |
| --- | --- |
| `test_the_factory_protocol_passes_the_independence_gate` | `m12_reference_research_v1` 经 `services.api.catalog` + `compile_and_preflight` ⇒ **0 条** `HETEROGENEITY_VIOLATION` |
| `test_the_gate_still_bites_when_the_reviewer_goes_back_to_the_producer_model` | 内存内把 `reviewer_a` 改成 `EXPLICIT_MODEL reviewer_gamma` ⇒ **恰好 1 条**，消息含 `main/deepseek-v4-flash-vision` + `research_writer` + `scientific_reviewer` |
| `test_the_press_is_reversible_and_leaves_the_config_bytes_untouched` | 三份配置的 `sha256` 按压前后**相同** |
| `test_a_catalog_without_writer_or_reviewer_panels_is_not_judged` | 全部 `review_panel_role=NONE` ⇒ `[]`（**未声明评审关系 ⇒ 不判**，既有语义不变） |

**手工按压读数**（产品路径，非测试内）：

```
=== as-is ===
  resolved reviewer: {'reviewer_a': 'reviewer_independent', 'reviewer_b': 'kimi_k2_6'}
  heterogeneity hits: 0
=== press: reviewer_a -> EXPLICIT reviewer_gamma (same model_name as producer) ===
  resolved reviewer: {'reviewer_a': 'reviewer_gamma', 'reviewer_b': 'kimi_k2_6'}
  heterogeneity hits: 1
   RED: model target main/deepseek-v4-flash-vision (endpoint/model_name) is reachable by
        both writer roles (research_writer) and reviewer roles (scientific_reviewer);
        use distinct underlying models for an independent review panel
```

## 受影响 API 套件恢复（cycle 1 的真红根因）

| 套件 | cycle 1 | 本轮 |
| --- | --- | --- |
| `tests/api/test_budget_forecast_api.py` | 红（preflight 拒冻） | **PASS** |
| `tests/api/test_draft_run_linkage.py` | 红（同上） | **PASS**（manifest 真冻结：`manifest_digest` 非空） |
| `tests/api/test_failed_run_semantic_digest_api.py` | 红（同上） | **PASS** |

合计 **28 passed**。

## 既有判据的更新（逐条申报，含 `numstat` 与谓词比对）

| 文件 | `numstat` | 谓词比对 | 判定 |
| --- | --- | --- | --- |
| `tests/application/test_m4_heterogeneity.py` | `51 +, 1 -` | `test_heterogeneity_allows_distinct_models` 的 `== []` **逐字未变**；只把 `model-2` 的 `model_name` 改成不同值。新增 `test_a_model_with_the_same_underlying_name_is_not_distinct` 钉住原形态 | **收紧** |
| `tests/loaders/test_contract_loaders.py` | `7 +, 2 -` | `allow_models` 仍为**等值断言**，只是元组内容多了两个第三方评审模型 | 等值，非放宽 |
| `tests/architecture/python/test_anthropic_surface_boundary.py` | `18 +, 2 -` | 判据谓词**未变**（仍判 run 腿全在 `OPENAI_COMPATIBLE`）；只把解析链从「只认显式绑定」扩到「profile 先解析 primary」——`reviewer_a` 改 profile 绑定后原解析会误红 | 解析面修正 |

**没有任何一处放宽**：三处都不是「把断言变弱 / 扫描面收窄 / 阈值下调」。

## 宽面零回归

```
pytest tests/application tests/api tests/loaders tests/contracts tests/architecture
=> 2708 passed, 77 skipped
```

（`egress guard: BLOCKED 198.51.100.1` 的 8 条来自 `test_default_egress_guard.py` **自身**的
受控探针，是判据要证明的行为，不是出网泄漏。）

`mypy packages/application/preflight/` ⇒ `Success: no issues found in 10 source files`；
`ruff check`（改动文件）⇒ `All checks passed!`。

## §4 漂移事实（AGENTS.md 要求逐条记）

| 声明名 | 返回名 | 结论 |
| --- | --- | --- |
| `deepseek-v4-flash-vision` | `dsv4-flash-vision` | **不同** ⇒ 只能称「可重复配置」 |
| `glm-5.3` | `glm-5.3` | **相同**（更干净，但仍属「可重复配置」，不称「完全模型可复现」） |
| `kimi-k2.6` | `kimi-k2.6` | **相同**（同上） |

## 残余与未覆盖范围（逐条）

- **`W-1`** — EC-05（自举收口）尚未执行，是本收口 cycle 的交付物；
- **`W-2`** — 本判据只判「底层模型 + endpoint 是否相同」，**不判**「评审是否真的独立判断」；
- **`W-3`** — **已解除**：本轮已接入第二个/第三个真实模型（`glm-5.3` / `kimi-k2.6`）；
- **`W-4`** — 只判协议声明的评审关系（`review_panel_role`）；没声明 ⇒ 不判；
- **`W-5`（新增，如实登记）** — `research_strong.fallback` 仍是 `[reviewer_gamma]`
  （= 生产者的同一个底层模型）：它不制造跨面板相交（因为 `reviewer_gamma` 不再担任评审），
  但意味着**生产侧没有模型多样性**；「生产者的 fallback 落到另一个真模型」仍无判据；
- **未覆盖**：读面认证、多租户·RBAC·BOLA·BFLA、部署面验证、D 组审批通道、
  默认 runtime 改真（默认仍 Fake）—— 均不做；
- `R-M1` **未收口** ⇒ **不得**宣称项目安全；
- 投递语义**不是**「恰好一次」—— **明确否认**。

## 结论

**PASS**。EC-01…EC-04 各有可复核读数（21 条新判据 + 5 条异构专项 + 28 条受影响 API），
宽面零回归 **2708 passed / 77 skipped**，静态门全绿。核心读数两条：**出厂目录下评审者与
生产者落在不同 `(endpoint, model_name)`**；**把评审者指回生产者的模型 ⇒ 恰好 1 条
`HETEROGENEITY_VIOLATION` 并点名相交目标与两侧 role**。

三处既有判据的更新已逐条申报（一处收紧、一处等值同步、一处解析链修正），**无任何放宽**。
**EC-05（自举收口）不在本文件射程**，由收口 cycle 交付。
