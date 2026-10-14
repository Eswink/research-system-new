---
id: MEM-20261014-218
title: "中转站切换是一次「配置往返」：改 3 处配置 + 3 处钉值判据；且声明 model 名与返回名可以不同（§4 必须记）"
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
scope: repository
confidence: 0.95
review_after: 2027-04-14
source_plans:
  - .cursor/plans/tasks/PLAN-20261014-462-relay-switch-to-intern-ai-and-a-real-run-on-it.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261014-463-relay-switch-to-intern-ai-and-a-real-run-on-it.md
supersedes: []
tags: [relay, model-drift, config-round-trip, live-run, credential-discipline]
---

## 做了什么

把中转站从 `https://apihub.agnes-ai.com/v1` / `agnes-2.5-flash` 切到
`https://discovery-api.intern-ai.org.cn/v1` / `deepseek-v4-flash-vision`，并用新站
跑通一次真实 run。

## 换站的**完整**影响面（实测，别多改也别少改）

**要改（6 处）**：

1. `examples/config/llm_endpoints.yaml` — `main.base_url` + `main.discovery.allow_models`
   + `agnes-anthropic.base_url`（同一站点的另一协议面）
2. `examples/config/models.yaml` — **四个** `model_name`（它们是同一底层模型的四张能力画像）
   + `display_name` + `context_window_tokens`（按 `GET /v1/models` 的 `max_context_length` 填）
3. `.env` 的 `LLM_MAIN_KEY`（**只在这里**；`.env` 在 `.gitignore:1`，
   且**不在** `tools/credential_audit.py` 的四个面内 ⇒ 是凭据的**合法落点**）
4. `tests/loaders/test_contract_loaders.py` — 三处**钉值**：`allow_models` /
   `model_name` / `context_window_tokens`（**谓词一字未改**，只是等值断言钉新值）

**不用改（实测零耦合）**：`services/` / `packages/` / `adapters/` **全部产品代码**；
`tools/` 的三个 CLI（按端点 **id** 取，不按 URL）；OpenAPI 快照（DTO 生成，不含配置）；
`tests/api/**`（用自建 fixture 端点）。

**刻意不改**：**endpoint id `agnes-anthropic`**。它是**稳定句柄**，被 5+ 判据与测试常量引用
（`test_anthropic_surface_boundary.py:46`、`live_control_plane_support.py:40`、
四个 live 测试的 `_ANTHROPIC_ENDPOINT`、`test_runtime_egress_gate.py:296`）⇒ 改名是
**装饰性**改动却要连坐一片，**收益为负**。

## §4：声明名 ≠ 返回名（必须记，且不得宣称"完全模型可复现"）

实测一次真实 probe：

```
declared:  deepseek-v4-flash-vision
returned:  dsv4-flash-vision          ← 不同
system_fingerprint: null              ← provider 未提供
```

⇒ 口径只能是「**可重复配置**」。这条正是 AGENTS.md §4 要抓的形态：中转站可以在同一个
model id 后面换真实模型，所以**每次 run 都要记**声明名 / 返回名 / 指纹 / 两个 digest。

## 工具调用：同一模型**两副面孔**（实测）

| 请求形态 | 响应 |
| --- | --- |
| 正常（自动选择） | `finish_reason: stop`，`tool_calls: null`，content 里是 **DSML 文本** `<｜DSML｜tool_calls>…` |
| `tool_choice: required` | `finish_reason: tool_calls`，**标准 `tool_calls` 数组** |
| Anthropic 面 `/v1/messages` | 只给 **DSML 文本**（无 `tool_use` 块） |

⇒ **run 腿必须走 OpenAI 兼容面并强制 `tool_choice`**（否则模型不真调工具）。
本次真实 run 在这条面上跑通（`1 passed`），但 OpenHands 侧实际发的是哪种形态**未取证**。

## 为什么这样做

**为什么要「只改这 6 处、别多改也别少改」**：换站在本仓是**配置往返**——产品代码
零耦合（实测：`services/` / `packages/` / `adapters/` 无一处引用站名或模型名），
但**三处钉值判据**会红（`tests/loaders`）。少了它们 ⇒ 门红；多了（比如顺手改
endpoint id）⇒ 连坐一片**与换站无关**的判据。所以正确形态是「**配置 + 凭据 + 钉值**」
三件齐，其余一概不动。

**为什么 endpoint id 刻意保稳**：id 是**稳定句柄**（被 5+ 判据与测试常量引用），
而站名/模型名才是**会变的事实**。把会变的写进配置、让句柄不动，是"换站改动最小化"的
直接推论——改名带来的收益（字面更好看）远小于它连坐的判据面。

**为什么必须记「声明名 ≠ 返回名」**：AGENTS.md §4 的立论前提就是**中转站可以在同一个
model id 后面换真实模型**。本次实测正是这个形态（声明 `deepseek-v4-flash-vision`、
返回 `dsv4-flash-vision`、无系统指纹）⇒ 只能宣称「**可重复配置**」，
**不得**宣称「完全模型可复现」。不记这一条，§4 的整套记录面就落空了。

**为什么凭据只落 `.env`**：`.env` 在 `.gitignore:1`，且**不在** `credential_audit.py` 的
四个面（`tracked` / `records` / `config_db` / `logs`）内 ⇒ 它是设计上的**唯一合法落点**。
任何 tracked 文件（记录、GOAL、`examples/`）出现 `sk-…` 都会被 `tracked` 面抓到。

## 怎么做与复现

```bash
# 1) 新站连通与能力（需 LLM_MAIN_KEY + RESEARCHOS_LIVE_E2E=1）
uv run --frozen --no-sync python -B tools/m12_relay_smoke.py

# 2) 真实 run（真实 runtime + 真实中转站，约 4-5 分钟）
RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 \
  uv run --frozen --no-sync python -B -m pytest tests/e2e/test_real_protocol_run_live.py -q

# 3) 凭据纪律自证（tracked 面必须 offenders=0）
uv run --frozen --no-sync python -B tools/credential_audit.py
```

## 适用边界

- `RESEARCHOS_AGENT_RUNTIME` / `RESEARCHOS_LIVE_E2E` **不要写进 `.env`**——
  会污染本地默认门（默认门必须离线）。
- `docs/integration/` 两份文档的同步**没做**（`LIVE_MODEL_RUNBOOK.md` §6 表被机算复核、
  `LLM_ENDPOINTS.md` §12 标题被钉住）⇒ 需专门一轮，不能顺手改。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）。

## 来源

- `PLAN-20261014-462` / `RECHECK-20261014-463`；
- 实测命令见上；`endpoint_config_digest = sha256:1498eb14…`、
  `probe_suite_digest = sha256:d384cbb5…`。
