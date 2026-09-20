# LLM Endpoint Integration v0.4.0

## 1. MVP 用户输入

```text
Base URL
API Key
Model ID(s)
```

协议取值为（域枚举 `LLMProtocol`，唯一词表）：

```text
OPENAI_COMPATIBLE | ANTHROPIC
```

Research OS 不要求用户选择真实厂商；协议标识指**线协议族**，不是模型厂商绑定。
默认 `OPENAI_COMPATIBLE`（API DTO 默认值）。

**执行侧按协议选路**（`adapters/relay/protocols.py` 是唯一分派点）：

| protocol | 线上形态 | 鉴权头 | 备注 |
| --- | --- | --- | --- |
| `OPENAI_COMPATIBLE` | `POST {base_url}/chat/completions`，或按 `api_style=responses` 走 `POST {base_url}/responses` | `Authorization: Bearer` | 既有行为，未变 |
| `ANTHROPIC` | `POST {base_url}/messages`（Messages 形态） | `x-api-key` + `anthropic-version`（**不**发 `Authorization`） | 见下方缺口 |

**未知协议 fail-closed**：`select_wire_shape` 抛分类错误（`MODEL_INCOMPATIBLE`）且
**不发起任何出站请求**——静默回退会让「配了某种协议」与「实际跑的是另一种形态」不可区分。

**Messages 形态的已知缺口（如实登记，不伪造能力）**：

- **流式未实现**：`stream=True` 点名拒绝（不降级成非流式、不套用 OpenAI SSE 解析）；
  probe 的 `streaming` 步因此记为 capability failure，**不写 SUPPORTED 断言**；
- **`response_format` 无对应参数**：非空即点名拒绝（静默丢弃等于声称支持了没支持的能力）；
- **`max_tokens` 必填**：该形态要求该字段，缺失即点名拒绝；probe 层对它显式给出
  `PROBE_ANTHROPIC_MAX_TOKENS`（256），**产品流量必须自带自己的值**；
- **无 `system_fingerprint` 等价字段**：该槽位保持 `None`（不拿别的字段顶替）；
- **usage** 用 `input_tokens` / `output_tokens`；`total_tokens` 仅在两者都存在时给出。

OpenHands 侧的 runtime model identifier 同样按协议取前缀（`adapters/openhands/llm_factory.py`）：
`ANTHROPIC` ⇒ `anthropic/`，`OPENAI_COMPATIBLE` ⇒ 既有探测失败后 `openai/` 前缀。

## 2. LLMEndpoint

```yaml
id: main_relay
name: Main Relay
protocol: OPENAI_COMPATIBLE   # OPENAI_COMPATIBLE | ANTHROPIC
api_style: chat_completions   # 仅对 OPENAI_COMPATIBLE 生效：chat_completions | responses
base_url: https://xxx.com/api/v1
credential_ref: cred_main
request_timeout_seconds: 120
max_retries: 2
concurrency_limit: 8
enabled: true
# 可选块（契约 schema 支持；API PATCH 目前不回传，见 API 文档）
discovery: { enabled: false }
circuit_breaker: { failure_threshold: 5, open_timeout_seconds: 60, half_open_max_probes: 1 }
```

## 3. URL 处理

- 保存用户原始 URL；
- runtime 层做 syntax/TLS validation；
- 不偷偷拼 `/v1`；
- Test Connection 以真实行为为准；
- **默认拒绝** localhost / 环回（`127.0.0.0/8`、`::1`）/ 私有 / 链路本地 / **保留类**
  （多播、未指定、保留段、CGNAT `100.64.0.0/10`、非全局单播），除非部署策略允许；
- 每一类有**自己的**开关：`allow_localhost` / `allow_private` / `allow_link_local`；
  保留类**没有**开关，只能靠 `allowed_hosts` 点名豁免（唯一判据
  `packages/application/model_relay/endpoint_policy.py::_host_kind`）；
- host 是域名时不做 DNS 解析（判定在 adapter 层），因此「放行域名」不等于「可达」。

## 4. ModelDefinition

```yaml
id: model_alpha
endpoint_id: main_relay
model_name: alpha-2026
display_name: Research Alpha
```

`model_name` 原样传给中转站。

## 5. Discovery

```text
Manual                # 永远可用
Optional /models      # 兼容时使用
```

Discovery 结果不能自动启用，需用户确认。

Endpoint 可选配置（`llm-endpoint.schema.json`）：

```yaml
discovery:
  enabled: true
  allow_models: [model-alpha]   # 允许加入候选的模型白名单
```

## 6. Probe

```text
connectivity
authentication
basic chat
streaming
tool calling
structured output
vision（可选）
usage metadata
```

Probe 使用无敏感信息的固定 fixture。

## 7. Health

EndpointHealth：

```text
UNKNOWN
HEALTHY
DEGRADED
OPEN_CIRCUIT
DISABLED
```

记录 latency/error rate/rate-limit/circuit 状态。

Circuit breaker 配置（`llm-endpoint.schema.json`，迁移表见 `docs/reliability/CIRCUIT_BREAKER.md`）：

```yaml
circuit_breaker:
  failure_threshold: 5
  open_timeout_seconds: 60
  half_open_max_probes: 1
```

## 8. Drift Fingerprint

中转站可能在相同 Model ID 后改变底层模型。

运行时尽可能记录：

- returned model field；
- system fingerprint；
- selected safe headers；
- probe suite hash；
- calibration result digest；
- observed capabilities。

不能获取真实底模时，不宣称“模型完全可复现”。

## 9. Credentials

**凭据值现在存在哪里**（如实声明；历史声明与本节的差异见
`.cursor/plans/rechecks/RECHECK-20260920-116-*.md`）：

| 层 | 事实 | 落点 |
| --- | --- | --- |
| Domain | 只保存 `credential_ref`（形如 `endpoint:<id>`），**永不保存密钥值** | `LLMEndpoint.credential_ref` |
| 进程内注册表 | `POST /llm-endpoints` 的 `api_key` 进 `register()`，只活在**内存**里 | `adapters/relay/registry_credential_resolver.py` |
| 环境变量 | `resolve()` 先查注册表，未命中再按 `credential_ref` **同名**环境变量回退 | 同上 |

由此得到三条必须写进读面的边界：

- 凭据值**只存在于环境变量或进程内注册表**；注册表随进程消失，**重启后需重新注入**
  （UI 显示 `credential=missing`，由向导重新输入）。**不伪装 Secret Manager**：
  没有加密存储层，也**不落盘**、不进数据库/配置面 JSON、不进 CI；
- 读面只回答存在性：`GET /llm-endpoints*` 回 `credential: configured | missing`，
  任何响应/日志/错误消息都不回显密钥（映射集中在 `services/api/mappers/endpoints.py`）；
- 明文凭据不进仓库/记录/日志：判据是 `tools/credential_audit.py`（四面扫描；
  放行项按**值**白名单逐条给理由，新串仍判红）+ `tests/tooling/test_credential_audit.py`。

其余既有约定不变：

- 不进入 Agent context；
- 不进入 Tool Provider；
- 不进入 telemetry/log；
- Test Connection 错误必须 redacted。

## 10. 多 Endpoint

产品默认一个 Endpoint，但 Domain 支持多个，便于：

- 备用 relay；
- confidential self-hosted relay；
- organization/project override。

不要在 MVP 引入复杂智能路由。
