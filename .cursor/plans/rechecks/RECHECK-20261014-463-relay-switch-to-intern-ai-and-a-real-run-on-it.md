---
id: RECHECK-20261014-463
slug: relay-switch-to-intern-ai-and-a-real-run-on-it
title: 复检 — 中转站切换（intern-ai）与新站真实 run
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-14
updated_at: 2026-10-14
plan_id: PLAN-20261014-462
parent_goal: null
reviewer: root-agent
owners:
  - root-agent
---

# RECHECK-20261014-463 — 中转站切换

## 复检口径

不复用 PLAN 叙述；每项给出**可复核观察面**（命令 + 读数）。**未实跑的不记通过**。

## 检查结果

| # | 观察 | 结果 |
| --- | --- | --- |
| AC-1 | 新站连通 | **PASS** — `GET /v1/models` ⇒ HTTP 200，10 个模型，含精确 id `deepseek-v4-flash-vision` |
| AC-2 | 模型元数据按实测填写 | **PASS** — `max_context_length=1048576`（= 写入的 `context_window_tokens`）；`supported_parameters.tools=true`、`reasoning=true` |
| AC-3 | 对话可用 | **PASS** — chat ping ⇒ 200，`usage.total_tokens=21` |
| AC-4 | Anthropic 面可用 | **PASS** — `POST /v1/messages` ⇒ 200（`type: message`，含 `thinking` 块） |
| AC-5 | 配置切换 | **PASS** — `main.base_url` / `allow_models` / 四个 `model_name` 全部指向新站 |
| AC-6 | **endpoint id 保稳** | **PASS** — `agnes-anthropic` **未改名**（被 5+ 判据与测试常量引用；改名属装饰性改动且会连坐） |
| AC-7 | 凭据落位 | **PASS** — `.env` 的 `LLM_MAIN_KEY`（len 67、`sk-` 前缀）；脚本按行替换、断言恰好命中 1 行 |
| AC-8 | relay probe | **PASS** — `RELAY SMOKE OK`；五项能力全过、`capability_failures` 空 |
| AC-9 | **真实 run** | **PASS** — `test_real_protocol_run_live.py` ⇒ `1 passed in 258.50s`（真实 runtime + 真实中转站） |
| AC-10 | 定向判据 | **PASS** — `54 passed`（loaders + anthropic 边界 + egress gate） |

## §4 模型漂移事实（AGENTS.md §4 要求逐项记录）

| 字段 | 读数 |
| --- | --- |
| 声明 model 名 | `deepseek-v4-flash-vision` |
| **返回 model 名** | **`dsv4-flash-vision`** ← **两者不同** |
| `system_fingerprint` | `null`（provider 未提供） |
| `endpoint_config_digest` | `sha256:1498eb14684ab15dee120e8b9b0fec31fb2443af4da93d4c451605627d2386ee` |
| `probe_suite_digest` | `sha256:d384cbb5911eb67f0b2a51e12a067e29b9180b11d7a56e77ae44f38d52b85405` |
| compatibility | 五项能力 SUPPORTED（probe 实得，非声明） |

⇒ 口径：**可重复配置**（声明名与返回名不同、无系统指纹）——**不得**称
「完全模型可复现」。

## 警告（如实登记）

- **`W-1`**：`docs/integration/` 的两份文档**未同步**（仍写旧站/旧模型名）。
  约束：`LIVE_MODEL_RUNBOOK.md` §6 表被 `test_live_drift_sample_same_source.py` **机算复核**、
  `LLM_ENDPOINTS.md` §12 的小节标题与路径被 `test_anthropic_surface_boundary.py` 钉住
  ⇒ 需专门一轮做，不能顺手改。
- **`W-2`**：**工具调用两形态只观察未加判据**——默认自动选择 ⇒ 返回 **DSML 文本**；
  `tool_choice: required` ⇒ 返回**标准 `tool_calls`**。本次真实 run 里 OpenHands 侧
  实际走的是哪一形态**未核**（run 成功说明其调用链可用，但机制未取证）。
- **`W-3`**：`.env.example` 未加新站注释（键名未变，非必需）。
- **`W-4`**：`R-M1` 未收口；本记录**不**作任何安全结论；投递语义**不是**「恰好一次」
  （口径只能是 at-least-once + idempotency + deduplication）。

## 未覆盖的面

- 两份 `docs/integration/` 文档的同步（`W-1`）；
- 工具调用形态的机制取证（`W-2`）；
- 新站的**限流 / 配额**行为（10 模型 × 每分钟容量已在 `/v1/models` 声明，但未压测）；
- 新站的**故障面**（超时 / 5xx 分类）未在本轮触发。

## 结论

**PASS_WITH_WARNINGS。** 中转站从 `apihub.agnes-ai.com` 切到
`discovery-api.intern-ai.org.cn`，模型从 `agnes-2.5-flash` 切到 `deepseek-v4-flash-vision`：
**配置面 3 处 + 凭据 1 处 + 判据 3 处（钉值更新，谓词未改）**，产品代码**零改动**。
两条真实证据：relay probe `OK`（能力五项全过）与真实 run `1 passed`（258 秒）。
endpoint id 刻意保稳（未改名）以免连坐 5+ 判据。
