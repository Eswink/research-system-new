# LLM Endpoint Integration v0.2.2

## 1. MVP 用户输入

```text
Base URL
API Key
Model ID(s)
```

协议固定为：

```text
OPENAI_COMPATIBLE
```

Research OS 不要求用户选择真实厂商。

## 2. LLMEndpoint

```yaml
id: main_relay
name: Main Relay
protocol: OPENAI_COMPATIBLE
base_url: https://xxx.com/api/v1
credential_ref: cred_main
request_timeout_seconds: 120
max_retries: 2
concurrency_limit: 8
enabled: true
```

## 3. URL 处理

- 保存用户原始 URL；
- runtime 层做 syntax/TLS validation；
- 不偷偷拼 `/v1`；
- Test Connection 以真实行为为准；
- 默认拒绝 localhost/private IP，除非部署策略允许。

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

- API Key 加密/Secret Store；
- Domain 只保存 ref；
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
