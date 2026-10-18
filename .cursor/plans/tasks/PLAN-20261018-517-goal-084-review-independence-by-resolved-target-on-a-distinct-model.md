---
id: PLAN-20261018-517
slug: goal-084-review-independence-by-resolved-target-on-a-distinct-model
title: GOAL-084 cycle 2 — 评审独立性的解析面 + 判定面，落在**真不同的底层模型**上
status: DONE
created_at: 2026-10-18
updated_at: 2026-10-18
parent_goal: GOAL-20261018-084
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261018-518-goal-084-review-independence-on-a-distinct-model.md
memory_entries: []
---

# PLAN-20261018-517 — GOAL-084 cycle 2

## 为什么重推（cycle 1 的 BLOCKED 不成立）

cycle 1 把本 GOAL 记成阻塞，理由是「三条出路都撞约束」。复核后第四条出路**存在且最简单**：
**给评审者换一个真不同的 `model_name`** —— 不需要新凭据（同一个 `main` 端点 + 同一把
`LLM_MAIN_KEY`）、不需要新端点、不需要改判据、不需要改 Phase 结构。实测该端点上
`glm-5.3` / `kimi-k2.6` 等 9 个非 deepseek 模型均在售且 `tools=True`。

因此本 cycle **撤销 BLOCKED**，按第四条出路重推。

## 验收条件

- [x] **EC-01 解析面**：一个 agent 的**全部可能执行目标**（primary + **每个** fallback）
      解析成 `(endpoint, model_name)` 集合；确定性纯函数、零出网（源码级钉住）；
      解析不了 ⇒ **点名**（`MODEL_MISSING` finding，不是静默空集）。
- [x] **EC-02 判定面**：比较的是**解析后的目标**，不是绑定 id；出厂目录下评审者与生产者
      **不相交**（本轮接入了第三方模型）；把评审者指回生产者的模型 ⇒ **必须判红**并点名
      相交目标与两侧角色。
- [x] **EC-03 fallback**：profile 的 fallback 是「可能落到」的面 ⇒ 相交即判出并点名；
      清空 fallback ⇒ 相交消失；**两个方向**都判（生产者回落到评审者 / 评审者回落到生产者）。
- [x] **EC-04 产品路径**：`m12_reference_research_v1` 的 preflight 不再被本判据拒冻；
      反向按压仍咬得住；未声明评审关系 ⇒ 不判；按压不改树（`sha256` 前后相同）。
- [x] **受影响 API 套件恢复**（`test_budget_forecast_api` / `test_draft_run_linkage` /
      `test_failed_run_semantic_digest_api`）——它们 cycle 1 红的根因就是 preflight 拒冻。
- [x] **EC-05 不在本 cycle 的射程**（如实登记：收口 cycle 的交付物）。

## 落地内容

### (A) 给评审者接真不同的模型

| 文件 | 改动 |
| --- | --- |
| `examples/config/models.yaml` | 新增 `reviewer_independent`（`model_name: glm-5.3`）与 `kimi_k2_6`（`model_name: kimi-k2.6`）；能力逐条按**实测**声明 |
| `examples/config/model_profiles.yaml` | `critic_independent.primary` → `reviewer_independent`，**fallback 清空**（原先回落到生产者模型 `research_alpha`） |
| `examples/config/agents.yaml` | `reviewer_a` → `MODEL_PROFILE critic_independent`；`reviewer_b` → `EXPLICIT_MODEL kimi_k2_6`（两个评审者彼此也不同模型） |
| `examples/config/llm_endpoints.yaml` | `discovery.allow_models` 加 `glm-5.3` / `kimi-k2.6`（否则发现面会拒它们） |

**实测读数（2026-10-18，同一 `main` 端点 + `LLM_MAIN_KEY`）**：

- `GET /v1/models` ⇒ 11 个 id，含 `glm-5.3` / `kimi-k2.6`（`is_ready: true`；
  `max_context_length` 分别为 1048576 / 262144）；
- `POST /v1/chat/completions`（`glm-5.3`）⇒ HTTP 200、`content: "OK"`、**返回名 = 声明名**；
- `tool_choice: required` ⇒ 真返回标准 `tool_calls`（两者都通过）；
- `stream: true` ⇒ SSE chunk；`usage` 逐次回报；
- `response_format: json_schema`：`kimi-k2.6` **被遵守**（只回 schema 内的键、类型正确）⇒
  声明 `STRUCTURED_OUTPUT_NATIVE`；`glm-5.3` **未被强制**（多出 schema 外的 `status` 键、
  把 string 写成 number）⇒ 只声明 `STRUCTURED_OUTPUT_PROMPTED`。

### (B) 判据实现

- 新增 `packages/application/preflight/review_independence.py`：`resolve_agent_targets` /
  `resolve_targets_by_role` / `describe_target`。**primary 以编译期解析值为准**
  （这样 `INHERIT` 这类「绑定里没有模型名」的形态也能判），**fallback 仍逐个展开**；
- `role_checks._panel_role_map` 改装解析后的目标；解析失败 ⇒ **逐条 `MODEL_MISSING`**，
  且解析失败的 agent **不再被跳过**（跳过 = 空集 = 「无交集」= 假绿）。

### (C) 既有判据的更新（逐条申报）

| 文件 | `numstat` | 谓词变化 | 判定 |
| --- | --- | --- | --- |
| `tests/application/test_m4_heterogeneity.py` | `51 +, 1 -` | `test_heterogeneity_allows_distinct_models` 的 `== []` **未变**；`model-2` 从「同 `model_name` 不同 id」改为 `model_name="other-underlying-model"` ⇒ **收紧**（原形态在新语义下是同一个底层模型）。另新增反证用例 `test_a_model_with_the_same_underlying_name_is_not_distinct`（`== ["HETEROGENEITY_VIOLATION"]`） | **收紧**，非放宽 |
| `tests/loaders/test_contract_loaders.py` | `7 +, 2 -` | `allow_models == ("deepseek-v4-flash-vision",)` → `== ("deepseek-v4-flash-vision", "glm-5.3", "kimi-k2.6")` —— 仍是**等值断言** | 等值，非放宽 |
| `tests/architecture/python/test_anthropic_surface_boundary.py` | `18 +, 2 -` | 解析链从「只认 `EXPLICIT_MODEL`」改为「`MODEL_PROFILE` 先解析到 primary」（`reviewer_a` 改成 profile 绑定后原判据误红）。**谓词未变**：仍判「该 run 消费的模型都在 `OPENAI_COMPATIBLE` 面」 | 解析面修正，谓词未变 |

## 保留的边界（如实登记）

- **`agnes_flash` 不改**：它是 live 探针腿（`tests/e2e/test_ec04_live_first_run.py`）的
  `_MODEL`，改它会改 live 判据的射程；
- **`research_strong.fallback` 仍是 `[reviewer_gamma]`**：生产者的 primary 是
  `research_alpha`（`deepseek-v4-flash-vision`），回落到 `reviewer_gamma` **仍落在同一个
  底层模型**上，所以它不制造新的「跨面板相交」；但它意味着**生产侧的 fallback 不能提供
  模型多样性** —— 这是下一步的真实缺口（见残余 `W-5`）。
- **W-2（判定语义边界）不变**：本判据只判「底层模型 + endpoint 是否相同」，不判「评审是否
  真的独立判断」。

## 实施清单

1. **WP-A（配置面）**：`models.yaml` 新增 `reviewer_independent`（`glm-5.3`）与
   `kimi_k2_6`（`kimi-k2.6`）；`model_profiles.yaml` 的 `critic_independent` 改 primary
   并**清空 fallback**；`agents.yaml` 把 `reviewer_a` 改 profile 绑定、`reviewer_b` 改显式
   绑 `kimi_k2_6`；`llm_endpoints.yaml` 的 `allow_models` 放行两个新名字。
2. **WP-B（解析面）**：`packages/application/preflight/review_independence.py` ——
   `resolve_agent_targets` / `resolve_targets_by_role` / `describe_target`；
   primary 取**编译期解析值**（覆盖 `INHERIT`），fallback 逐个展开。
3. **WP-C（判定面）**：`role_checks._panel_role_map` 改装解析后的目标；解析失败
   **逐条 `MODEL_MISSING`**，且失败 agent **仍在受判面内**。
4. **WP-D（判据）**：`test_review_independence.py`（EC-01 解析面 8 条）+
   `test_review_independence_judgment.py`（EC-02/EC-03 9 条）+
   `preflight/test_review_independence_gate.py`（EC-04 产品路径 4 条）+
   `review_independence_fixtures.py`（共享夹具）。

## 影响报告

- **产品代码**：新增一个解析面模块（纯函数、零出网）；`check_heterogeneity` 的**判定面**
  从 model id 换成解析后的 `(endpoint, model_name)`。**不新增门、不改 finding 严重度**。
- **配置面**：`examples/config/**` 四处改动 —— 这是本 GOAL 的**被评对象**（让评审真的
  独立），不是「靠改目录让判据变绿」：判据对**旧配置**仍判红（有专门用例）。
- **读面 / DTO / 路由 / OpenAPI 快照**：**零改动**。
- **判据面**：新增 4 个文件（21 条判据）；既有 `test_m4_heterogeneity.py` 收紧 1 处
  （逐条申报，见 RECHECK）、`test_contract_loaders.py` 等值同步、
  `test_anthropic_surface_boundary.py` 解析链修正（谓词未变）。
- **无 schema 迁移、无依赖变化、无放行面变化、无凭据变化**；`agnes_flash` 未动。

## 工程记忆

**无可复用事实**（本轮三条读数写进 RECHECK-518 的可复核观察面；判据文件即事实面）：
`INHERIT` 绑定的 primary 只能从编译期解析值取；解析失败不能静默跳过（跳过 ⇒ 两边
「无交集」⇒ 假绿）；`AgentBinding` 在域构造期强制 `INHERIT` 不带值。

## 残余与未覆盖

见 GOAL 的「残余与未覆盖范围」：`W-2`（不判「是否真的独立判断」）、`W-5`（生产侧
fallback 无多样性）、`W-6`（`glm-5.3` 的结构化输出未强制）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| EC-01 解析面 | **8 passed** | `... pytest tests/application/test_review_independence.py -q` |
| EC-02 + EC-03 判定/fallback | **9 passed** | `... pytest tests/application/test_review_independence_judgment.py -q` |
| EC-04 产品路径 + 按压 | **4 passed** | `... pytest tests/application/preflight/test_review_independence_gate.py -q` |
| 异构专项 | **5 passed** | `... pytest tests/application/test_m4_heterogeneity.py -q` |
| 受影响 API | **28 passed** | `... pytest tests/api/test_budget_forecast_api.py tests/api/test_draft_run_linkage.py tests/api/test_failed_run_semantic_digest_api.py -q` |
| 宽面零回归 | **2708 passed, 77 skipped** | `... pytest tests/application tests/api tests/loaders tests/contracts tests/architecture -q` |
| 静态门 | ruff 绿 / mypy `10 source files` no issues | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-18 | **IN_PROGRESS** | 承 GOAL-084 的 cycle 2：按「第四条出路」（给评审者换一个真不同的 `model_name`）重推。 |
| 2026-10-18 | **DONE** | EC-01…EC-04 达成、受影响 API 恢复、宽面零回归；EC-05 留给收口 cycle。 |

