---
id: PLAN-20260920-114
slug: anthropic-protocol-execution-path
title: ANTHROPIC 协议执行路径：按 endpoint.protocol 选路（Messages 形态 + 未知协议 fail-closed + llm_factory 前缀）（EC-01）
status: DONE
created_at: 2026-09-20
updated_at: 2026-09-20
parent_goal: GOAL-20260920-008
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260920-008 cycle 1 = EC-01（ANTHROPIC 协议执行路径）。授权来源：2026-09-20 用户 goal 模式指令（建档 GOAL-008 并自动化循环推进、无需逐轮确认）。真实端点登记 / 模型参数口径 / 凭据纪律 / push-to-main-for-CI 授权见 GOAL-20260920-008 frontmatter `authorization.ref`。本 PLAN 严格遵守：不解锁任何出网、不引入新依赖（anthropic 形态**手写 HTTP**）、不上传凭据、不把真实 runtime 设为默认、默认门保持离线。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260920-114-anthropic-protocol-execution-path.md
memory_entries:
  - MEM-20260920-087
---

# PLAN-20260920-114 — ANTHROPIC 协议执行路径（GOAL-008 cycle 1 = EC-01）

## 目标

把「`LLMEndpoint.protocol` 允许 `ANTHROPIC`、但**没有任何执行路径读它做分派**」这条
**声明与事实的落差**收敛成**按协议选路的执行面**：

1. **一个协议词表**：`OPENAI_COMPATIBLE` / `ANTHROPIC` 在**域**里有一等枚举，
   `LLMEndpoint` 的校验与 relay/llm_factory 的分派**同源**，不出现第二份字面量清单。
2. **按协议选路**：relay 网关按 `endpoint.protocol` 决定线上形态
   （`ANTHROPIC` ⇒ Anthropic Messages：`POST {base_url}/messages`、`x-api-key` +
   `anthropic-version` 头、`max_tokens` 必填、`content[]` 合并出文本）；
   `OPENAI_COMPATIBLE` **保持今日行为逐字节不变**（仍按 `api_style` 分 chat_completions / responses）。
3. **未知协议 fail-closed**：既不静默回退到 OpenAI 形态，也不静默发请求——**点名拒绝**。
4. **OpenHands 侧按协议取前缀**：`resolve_runtime_model_name` 在 `ANTHROPIC` 下产出
   `anthropic/` 前缀，**不再无条件 `openai/`**；`OPENAI_COMPATIBLE` 的既有取值不变。

## 先探明再动手（建档时只读勘察已确认的事实）

1. **分派键是 `api_style`，不是 `protocol`**：`adapters/relay/completions.py:29-43`
   （`complete_any`）。`protocol` 的全部引用都是持久化 / 摘要 / DTO —— 见 GOAL-008
   「建档时已探明的现状」第 1 条（含逐处行号）。
2. **鉴权头写死在传输层**：`adapters/relay/transport.py:103-106`
   `headers = {"Authorization": f"Bearer {credential.value}", "Accept": "application/json"}`。
   Anthropic Messages 形态要求 `x-api-key` + `anthropic-version` ⇒ 头必须**按协议**构造。
3. **`max_tokens` 无承载**：`CompletionRequest`（`packages/application/ports/model_gateway.py:39-45`）
   有 `model/messages/tools/response_format/stream`，**没有** `max_tokens`；
   而 Anthropic Messages 形态把它列为**必填**。probe 层的请求构造在
   `packages/application/model_relay/suite.py:42-75`（`basic_request`）与
   `:90-107`（`extended_capability_steps`），调用点在 `probe.py`
   （`_connectivity_and_chat`、`_collect_probe`、`_extended_steps`——三处 `endpoint` 均在作用域内）。
4. **`openai/` 前缀只有一处且无条件**：`adapters/openhands/llm_factory.py:20-32`
   （`resolve_runtime_model_name`）；`build_llm`（`:51-58`）不读 `protocol`。
   生产调用链 `services/api/runtime_support.py:152-171` 以 3 参调用 `build_llm`。
5. **relay 适配器禁止 import 厂商 SDK**：`tests/architecture/python/test_relay_boundaries.py:51-54`
   经 `.importlinter.relay` 强制（`openai` / `litellm` / `anthropic` 一概不可）。
   ⇒ anthropic 形态**必须手写 HTTP**（复用既有 `transport.py`），**不得**引入 SDK。
6. **既有 relay 测试面**：`tests/adapters/relay/`（`test_gateway.py`、`test_gateway_probe.py`、
   `test_responses_api.py`、`relay_fakes.py` 等）与 `tests/adapters/openhands/test_llm_relay.py`
   （`:62,69-70` 以 **2 参**调用 `resolve_runtime_model_name`）。

## 口径（设计取舍，先写死避免实施时漂移）

- **协议词表的唯一来源**：在 `packages/domain/enums.py` 增 `LLMProtocol`（StrEnum，
  `OPENAI_COMPATIBLE` / `ANTHROPIC`）；`LLMEndpoint.__post_init__` 改为按该枚举校验
  ——**接受集合与错误文本逐字不变**（既有契约/用例不得因本次改动变红或变绿）。
  协议标识是**线协议族**名（与既有 `OPENAI_COMPATIBLE` 同性质），**不是**模型厂商绑定；
  本 PLAN **不新增**任何厂商名。
- **分派落点**：新模块 `adapters/relay/protocols.py` 提供
  `select_wire_shape(protocol, api_style) -> WireShape`（纯函数，**未知协议抛带分类的
  `RelayHTTPError`**）+ `request_headers(protocol, credential)`（OpenAI ⇒ 既有
  `Authorization: Bearer`；Anthropic ⇒ `x-api-key` + `anthropic-version`）。
  `complete_any` 与 `list_models` 都走它——**一个分派点，不散落 `if`**。
- **`max_tokens` 必填的诚实处理**：`CompletionRequest` 增**可选** `max_tokens`；
  Anthropic body 在缺失时**点名拒绝**（不得编造默认值静默截断输出）。
  probe 层对 anthropic 端点显式传 probe 常量（`PROBE_ANTHROPIC_MAX_TOKENS = 256`，
  文档写明这是 **probe 阶段**输出上限，产品流量自带自己的值）；
  **`OPENAI_COMPATIBLE` 路径不传 ⇒ 请求体与今日逐字节一致**（回归对照的判据）。
- **流式**：Anthropic Messages 流式形态（SSE `message_start` / `content_block_delta` /
  `message_stop`）**本轮不实现**——`stream=True` 时**点名 fail-closed**
  （`MODEL_INCOMPATIBLE`，消息说明该形态尚未实现），**不得**静默降级成非流式或 OpenAI SSE
  解析。后果如实登记：probe 的 `streaming` 步对该端点记为 capability failure（非致命），
  **不写 SUPPORTED 断言**（不伪造能力）。
- **`usage` 口径不伪造**：Anthropic 用 `input_tokens` / `output_tokens`；
  `total_tokens` **仅当两者都存在**时置为其和，否则保持 `None` 并给
  `usage_unavailable_reason`（沿用 M12-R1 WP6 口径）。
- **`system_fingerprint`**：Anthropic 响应无此字段 ⇒ 保持 `None`（**不得**拿别的字段顶替）。
- **不做**：不改 `api_style` 语义、不改 OpenAI 形态、不引入 SDK、不动
  `.github/workflows/**`、不改门禁与既有断言强度、不登记真实端点（那是 EC-03）。

## 验收条件

- **AC-01 词表同源**：`LLMProtocol` 是协议值的唯一来源；`LLMEndpoint` 接受集合不变
  （既有 `tests/domain/test_entities_invariants.py:83-90` 的 `ANTHROPIC` 用例仍绿），
  且全仓不再存在第二份 `("OPENAI_COMPATIBLE", "ANTHROPIC")` 字面量清单（结构判据）。
- **AC-02 按协议选路（正向）**：`protocol=ANTHROPIC` 的端点经真实 `OpenAIChatGateway` +
  注入式 `httpx.MockTransport` 收到 **Messages 形态**请求（URL `/messages`、
  `x-api-key` 头存在且 `Authorization` **不存在**、`anthropic-version` 存在、body 含
  `max_tokens`），响应 `content[]` 文本被正确取出、`usage` 映射到
  `prompt/completion/total`，`system_fingerprint` 为 `None`。
- **AC-03 回归对照（OpenAI 不变）**：同一 gateway 对 `protocol=OPENAI_COMPATIBLE` 端点
  仍然 `POST /chat/completions` + `Authorization: Bearer`，`api_style=responses` 仍走
  `/responses`；**请求体逐字节与改动前一致**（同夹具比对）。
- **AC-04 fail-closed**：未知协议 ⇒ `RelayHTTPError`（`MODEL_INCOMPATIBLE`）且
  **出站调用计数为 0**（记录型 transport 证明）；`stream=True` + `ANTHROPIC` ⇒
  同样**点名拒绝且不发起请求**。
- **AC-05 `llm_factory` 按协议取前缀**：`ANTHROPIC` ⇒ `anthropic/{model}`；
  `OPENAI_COMPATIBLE` ⇒ 既有取值**不变**（含已带 `/` 的名字透传）；
  **反证**：把前缀分支短路回无条件 `openai/` ⇒ 对应用例红（先红后复原）。
- **AC-06 文档同源**：`docs/integration/LLM_ENDPOINTS.md`（现称「协议固定为
  OPENAI_COMPATIBLE」，与代码事实不符）改为**如实描述两种协议 + 各自形态 + 流式缺口**；
  相关文档口径一致（`docs/architecture/MODEL_GATEWAY.md` 等引用处）。
- **AC-07 门禁**：受影响定向套件绿 + 规模门禁（50 行函数 / 450 行文件）绿 +
  `ruff` / `mypy` 绿 + m0 全量 23 项绿 + 治理 `validate.py` 绿。

## 实施清单

### WP-A — 域词表同源 + relay 协议分派骨架

- `packages/domain/enums.py`：新增 `LLMProtocol`（StrEnum）。
- `packages/domain/models.py`：`LLMEndpoint.__post_init__` 按 `LLMProtocol` 校验
  （接受集合与错误文本不变）。
- 新增 `adapters/relay/protocols.py`：`WireShape`、`select_wire_shape`、
  `request_headers`、`ANTHROPIC_VERSION`。
- `adapters/relay/transport.py`：`request_with_retries(..., headers=None)`
  ——传 None 时**保持**今日行为（默认头），传值时按协议构造。
- 提交：`feat(relay): protocol vocabulary in domain + wire-shape selection (fail-closed)`

### WP-B — Anthropic Messages 形态（请求构造 + 响应解析 + 网关接入）

- 新增 `adapters/relay/anthropic_api.py`：`messages_body`（`max_tokens` 必填、
  `system` 抽取）、`messages_result`（`content[]` 文本合并、`tool_use` ⇒ `ToolCallDraft`、
  usage 映射、`system_fingerprint` 保持 None）。
- `packages/application/ports/model_gateway.py`：`CompletionRequest` 增可选 `max_tokens`。
- `adapters/relay/completions.py`：`complete_any` 经 `select_wire_shape` 分派；
  新增 `_complete_anthropic`（非流式）；anthropic + stream ⇒ **点名 fail-closed**。
- `adapters/relay/gateway.py`：`list_models` 用 `request_headers(endpoint.protocol, ...)`；
  `probe_endpoint` / `complete` 路径经同一分派。
- `packages/application/model_relay/suite.py` + `probe.py`：probe 层对 anthropic 端点
  显式传 `PROBE_ANTHROPIC_MAX_TOKENS`（OpenAI 路径保持不传）。
- 提交：`feat(relay): anthropic messages wire shape selected by endpoint protocol`

### WP-C — OpenHands llm_factory 按协议取前缀

- `adapters/openhands/llm_factory.py`：`resolve_runtime_model_name(*, model_name, base_url, protocol)`；
  `build_llm` 传 `endpoint.protocol`；`ANTHROPIC` ⇒ `anthropic/` 前缀。
- 更新 2 参调用点（`tests/adapters/openhands/test_llm_relay.py` 等）为**显式协议**
  ——**只改调用签名，不改断言强度**。
- 提交：`feat(openhands): pick runtime model prefix by endpoint protocol`

### WP-D — 判据与反证

- 新增 `tests/adapters/relay/test_anthropic_messages.py`：AC-02 / AC-03 / AC-04 的用例
  （MockTransport 记录请求；出站计数；未知协议与 stream 的 fail-closed）。
- 新增/扩展 openhands 侧用例：AC-05 的正向与**反证**。
- 结构判据：协议词表同源（无第二份字面量清单）+ relay 边界测试仍绿（无 SDK import）。
- 提交：`test(relay): pin protocol routing, messages shape, and fail-closed refusals`

### WP-E — 文档同源 + 记录

- `docs/integration/LLM_ENDPOINTS.md`：协议段改为如实描述（两种协议、形态、鉴权头、
  流式缺口、`max_tokens` 必填语义）。
- 相关文档口径对齐（`MODEL_GATEWAY.md` / `MODEL_PROBE.md` 若有「固定 OpenAI」表述）。
- 子 PLAN 收口 + RECHECK；GOAL-008 回写（EC-01、迭代日志、child_plans）。
- 提交：`docs(integration): document both endpoint protocols and the streaming gap`

## 证据

- **交付物（树内可复核）**：`packages/domain/enums.py::LLMProtocol`、
  `packages/domain/models.py::_LEGAL_PROTOCOLS`、`adapters/relay/protocols.py`
  （`select_wire_shape` / `request_headers` / `ANTHROPIC_VERSION`）、
  `adapters/relay/anthropic_api.py`、`adapters/relay/completions.py::_complete_anthropic`、
  `adapters/relay/gateway.py`（`list_models` 走协议头）、
  `adapters/relay/transport.py`（`headers` 覆盖 + `_execute_request`）、
  `packages/application/ports/model_gateway.py::CompletionRequest.max_tokens`、
  `packages/application/model_relay/suite.py::probe_max_tokens`、
  `adapters/openhands/llm_factory.py::resolve_runtime_model_name(*, protocol)`、
  文档 `docs/integration/LLM_ENDPOINTS.md` §1 / `MODEL_GATEWAY.md` §3。
- **判据套件**：`tests/adapters/relay/test_anthropic_messages.py`（14）、
  `tests/architecture/python/test_protocol_vocabulary.py`（3）、
  `tests/application/test_probe_protocol_requests.py`（3）、
  `tests/adapters/openhands/test_llm_relay.py::TestProtocolPrefix`（5）。
- **反证（先红后复原）**：F1 `llm_factory` 前缀分支短路 ⇒ 2 failed；
  F2 `complete_any` Messages 分派短路 ⇒ 与 F1 合并 9 failed（失败日志显示请求落到
  `/chat/completions`）；F3 未知协议静默回退 ⇒ 2 failed（`DID NOT RAISE`）。
  复原后同命令 **168 passed**。
- **门禁（完整 m0，冻结树）**：`PASS: profile=m0; 23 deterministic checks`，
  **4072 passed / 11 skipped**。m0 本轮实际拦下四处缺陷并按缺陷修（`python/format-check`、
  `python/typecheck` 7 错误、50 行函数门 G3、`framework/validate_bundle` G4）——
  详见 RECHECK-20260920-114 的 G1–G4 与 W-1…W-9。
- **复检**：`.cursor/plans/rechecks/RECHECK-20260920-114-anthropic-protocol-execution-path.md`
  = **PASS_WITH_WARNINGS**（W-1 真实端点面未实测 / W-2 流式未实现 / W-3 `response_format`
  无对应 / W-4 `max_tokens` 无产品调用方 / W-5 `system_fingerprint` 恒空 / W-6 端点未入库 /
  W-7 上游历史记录未改写 / W-8 域值名含厂商词属既有取值 / W-9 `tool_use.input` 非 dict 无用例）。

## 状态历史

- 2026-09-20 建档（GOAL-008 cycle 1 = EC-01）：`status: IN_PROGRESS`。
  只读勘察确认 6 条事实（分派键是 `api_style`、鉴权头写死在传输层、`max_tokens` 无承载、
  `openai/` 前缀唯一且无条件、relay 禁 import 厂商 SDK、既有测试面行号）。
- 2026-09-20 完成（`status: DONE`）。WP-A…WP-E 各自独立提交；三条反证先红后复原；
  m0 三跑（前两跑各拦下一批缺陷，冻结树上最终 **23/23 + 4072 passed**）；
  RECHECK-20260920-114 = PASS_WITH_WARNINGS（W-1…W-9 已登记）。

## 影响报告

- **Domain/API/schema 变化**：新增 `LLMProtocol` 枚举（**接受集合不变**：仍是
  `OPENAI_COMPATIBLE` / `ANTHROPIC`，错误文本逐字未改）；`CompletionRequest` 增**可选**
  `max_tokens`（默认 None ⇒ 既有调用方行为不变）；`resolve_runtime_model_name` 的 protocol
  改为**必填关键字参数**（调用点显式化，唯一测试调用点已更新且断言未改）。
  **无 DTO / 路由 / OpenAPI 快照 / 迁移变化**（协议值集合与持久化编码均未变；
  `docs/api/openapi.m13.json` 本轮未改，快照门在 m0 内通过）。
- **安全/凭据变化**：鉴权头**按协议**构造（Messages 用 `x-api-key` + `anthropic-version`，
  且不再发送 `Authorization`）；请求头**不进入**白名单采集（`SAFE_RESPONSE_HEADERS` 未动）；
  **未新增出网面**——分派发生在既有 URL 策略与门链之后，且未知协议在触网前拒绝。
- **兼容性/迁移风险**：无数据迁移。风险点是 Messages 形态的 `max_tokens` 语义
  （缺失即点名拒绝，**不静默补默认**）与**流式未实现**（拒绝而非降级）——两者都是
  「宁可拒绝也不伪造能力」，已随 W-2/W-4 登记。
- **上游版本影响**：**无**（未引入依赖、未改 pin；Messages 形态手写 HTTP，relay 适配器
  「不得 import 厂商 SDK」的既有结构约束仍绿）。
- **下一项任务**：EC-02（模型参数落库：上下文窗口 512000 + 思考强度 Max 的承载字段、
  往返、读面、快照；反证：缺字段 ⇒ 用例红）。
