---
id: PLAN-20261014-462
slug: relay-switch-to-intern-ai-and-a-real-run-on-it
title: 中转站切换（intern-ai）+ 新站真实 run 冒烟
status: DONE
created_at: 2026-10-14
updated_at: 2026-10-14
parent_goal: null
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261014-463-relay-switch-to-intern-ai-and-a-real-run-on-it.md
memory_entries:
  - .cursor/memory/entries/MEM-20261014-218-relay-switch-is-a-config-round-trip-and-the-returned-name-differs.md
---

# PLAN-20261014-462 — 中转站切换 + 新站真实 run 冒烟

## 验收条件

- [x] 新站实测可用（`/v1/models` 200、chat 200、Anthropic 面 200）
- [x] `main.base_url` / `allow_models` / 四个 `model_name` 切换完成
- [x] 新 key 只落 `.env`（gitignored），tracked 面零出现
- [x] `tools/m12_relay_smoke.py` ⇒ `RELAY SMOKE OK`
- [x] 真实链冒烟 `test_real_protocol_run_live.py` ⇒ `1 passed`
- [x] 受影响定向判据全绿（loaders / anthropic 边界 / egress gate 54 passed）

## 实施清单

1. **实测新站**（模型 id 精确匹配、能力面、工具调用形态、Anthropic 面）：
   - `GET /v1/models` ⇒ 10 个模型，含 `deepseek-v4-flash-vision`
   - 元数据：`max_context_length = 1048576`、`supported_parameters.tools = true`、`reasoning = true`
   - chat ping ⇒ 200；Anthropic `/v1/messages` ⇒ 200
   - **工具调用关键实测**：默认自动选择时返回 **DSML 文本**（非标准字段）；
     `tool_choice: required` 时返回**标准 `tool_calls`**（`finish_reason: tool_calls`）
2. **改配置**：`examples/config/llm_endpoints.yaml`（`main.base_url`、`allow_models`、
   `agnes-anthropic` 的 `base_url` 与 `name`）+ `examples/config/models.yaml`
   （四个 `model_name` + `display_name` + `context_window_tokens: 512000 → 1048576`）。
   **endpoint id 保持 `agnes-anthropic` 不变**（它是稳定句柄，被 5+ 判据引用；改名是装饰性改动）
3. **写 `.env`**：只替换 `LLM_MAIN_KEY=` 一行（脚本按行匹配、断言恰好 1 行命中）
4. **同轮判据同步**（`tests/loaders/test_contract_loaders.py`）：
   - `:134` `allow_models == ("deepseek-v4-flash-vision",)`
   - `:143` `model_name == "deepseek-v4-flash-vision"`
   - `:151` `context_window_tokens == 1048576`
   —— **谓词一字未改**（仍是等值断言，只是钉新值）
5. **真实验证两条**：relay smoke（probe）+ 真实 run（`test_real_protocol_run_live.py`）

## 证据

| 面 | 读数 |
| --- | --- |
| relay probe | `probe ok=True`；`observed_capabilities = CHAT,STREAMING,STRUCTURED_OUTPUT_NATIVE,TOOL_CALLING_NATIVE,USAGE_REPORTING`；`capability_failures` 空 |
| §4 漂移事实 | 声明 `deepseek-v4-flash-vision` / **返回 `dsv4-flash-vision`** / `system_fingerprint=None` |
| 配置 digest | `endpoint_config_digest = sha256:1498eb14684ab15dee120e8b9b0fec31fb2443af4da93d4c451605627d2386ee` |
| probe suite | `probe_suite_digest = sha256:d384cbb5911eb67f0b2a51e12a067e29b9180b11d7a56e77ae44f38d52b85405` |
| 真实 run | `1 passed in 258.50s`（真实 runtime + 真实中转站，跑完整协议到终态） |
| 定向判据 | `54 passed`（loaders + anthropic 边界 + egress gate） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-14 | IN_PROGRESS | 新站实测（含工具调用两形态）→ 配置切换 → `.env` 落 key → 判据同步 |
| 2026-10-14 | DONE | relay smoke `OK` + 真实 run `1 passed`；定向 54 passed |

## 影响报告

- **配置面**：`examples/config/llm_endpoints.yaml`、`examples/config/models.yaml`
- **凭据面**：`.env` 的 `LLM_MAIN_KEY` 值更新（**gitignored**；`credential_audit` 四面均不含 `.env`）
- **判据面**：`tests/loaders/test_contract_loaders.py` 三处**钉值更新**（谓词未改）
- **产品代码**：**零改动**
- **文档**：`LIVE_MODEL_RUNBOOK.md` / `LLM_ENDPOINTS.md` 的同步**未在本轮完成**
  ⇒ 登记为 `W-1`（见残余）
- **兼容性**：endpoint id 未改 ⇒ 既有测试常量（`agnes-anthropic`）无需变动

## 残余与未覆盖（如实登记）

- **`W-1`**：`docs/integration/LIVE_MODEL_RUNBOOK.md`（§1.1 / §5 / §6 表 / §7）与
  `docs/integration/LLM_ENDPOINTS.md`（§10 / §12.2-12.4）**仍写着旧站与旧模型名**，
  未在本轮同步。约束：§6 表被 `test_live_drift_sample_same_source.py` **机算复核**
  （改表须自洽）；§12 小节标题与路径被 `test_anthropic_surface_boundary.py` 钉住
  （只许改内容不许删节）⇒ 需专门一轮。
- **`W-2`**：工具调用的**两形态**（默认 DSML vs `tool_choice: required` 标准字段）只做了
  **实测观察**，**未加判据**；OpenHands 侧如何发 `tool_choice` 未核。
- **`W-3`**：`.env.example` 未加新站注释（键名未变，非必需）。
- **`W-4`**：`R-M1` 未收口；本记录**不**作任何安全结论；投递语义**不是**「恰好一次」
  （口径只能是 at-least-once + idempotency + deduplication）。

## 复核命令

```bash
# 新站连通与能力
uv run --frozen --no-sync python -B tools/m12_relay_smoke.py          # 需 LLM_MAIN_KEY + RESEARCHOS_LIVE_E2E=1

# 真实 run（约 4-5 分钟）
RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \
  uv run --frozen --no-sync python -B -m pytest tests/e2e/test_real_protocol_run_live.py -q

# 凭据四面审计（确认 tracked 面零出现）
uv run --frozen --no-sync python -B tools/credential_audit.py
```
