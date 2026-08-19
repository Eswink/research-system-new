# Model Probe Suite v0.4.0

Probe 规格与 digest 规则是 v0.4.0 明确规格；实现位于 `packages/application/model_relay/probe.py`（编排）与 `adapters/relay/gateway.py`（HTTP 执行），测试位于 `tests/application/test_run_probe.py` 与 `tests/adapters/relay/test_gateway.py`。

## Probe 步骤（`probe-suite-v1`）

| 步骤 | 请求 | 判定 | 输出能力 / 失败 |
| --- | --- | --- | --- |
| connectivity | `GET <base_url>/models` | HTTP 2xx | 连通性；失败见 `ModelProbeResult.error_category` |
| authentication | `GET <base_url>/models` | 401/403 → `MODEL_AUTH` | 凭据有效性；失败中止 probe |
| basic completion | `POST <base_url>/chat/completions`（1 条固定消息） | 返回 `choices[0].message.content` | CHAT；失败中止 probe |
| streaming | `POST <base_url>/chat/completions`（`stream: true`） | SSE 解析至 `[DONE]` | STREAMING（非致命失败） |
| tool calling | `POST <base_url>/chat/completions`（`tools` 参数） | `message.tool_calls` 非空 | TOOL_CALLING_NATIVE（非致命失败） |
| structured output | `POST <base_url>/chat/completions`（`response_format` json_schema） | 返回合法 JSON | STRUCTURED_OUTPUT_NATIVE（非致命失败） |
| usage metadata | 上述 completion 响应 | `usage.total_tokens` 存在 | USAGE_REPORTING |
| vision（可选，默认关闭） | `POST <base_url>/chat/completions`（image_url 输入） | 返回文本 | VISION |

`<base_url>` 为 LLMEndpoint.base_url 原样（如 `https://xxx.com/api/v1`），网关只追加 `/models` 或 `/chat/completions`，不拼接 `/v1`。

## 探测消息

Probe 使用无敏感信息的固定 fixture，不发送真实项目内容：

```text
Reply with the single word: pong
```

Structured output probe 的 schema 为最小 JSON Schema（`{"type": "object", "properties": {"pong": {"type": "string"}}}`），固定且不含业务字段。

## Digest 与版本

- `probe_suite_digest`：probe suite 定义（步骤列表 + 固定消息 + structured schema）的 canonical serialization digest（`packages/domain/serialization.py`，key 排序、UTF-8、sha256）。
- `calibration_prompt_version`：`probe-suite-v1`（与 suite digest 配套的人类可读版本号）。
- `calibration_result_digest`：对返回文本与 `system_fingerprint` 的 canonical serialization digest。

## 判定规则

- 每项验证通过的能力以 `CapabilityAssertion(status=PROBED, ...)` 写入结果断言，`probe_version` 记录 suite 版本；
- 失败的能力写入 `ModelProbeResult.capability_failures`（`CapabilityProbeFailure`），携带 `error_category` 区分“模型不支持”（`MODEL_INCOMPATIBLE`）与网络/认证/限流/超时/中转站故障（`EXECUTION_FAILURE` / `MODEL_AUTH` / `MODEL_RATE_LIMIT` / `MODEL_TIMEOUT` / `MODEL_RELAY_UNAVAILABLE`）；
- 运行类失败（429/5xx/timeout/网络）**不**写入能力断言，避免把瞬时故障误判为永久能力变化；
- 非致命失败（streaming/tool calling/structured output）不使整体 probe 失败，`ok` 仍为 true 且失败原因可机器读取；
- `ok=False` 的 probe 输出机器可读 `ModelProbeResult`（`error_category` ∈ FailureCategory）；
- 错误消息必须 redacted（见 `docs/security/SECRET_MANAGEMENT.md` §6）；
- Discovery（`GET <base_url>/models`）结果以 `CapabilitySource.DISCOVERED` 标记，默认不启用，需用户显式确认（manual ModelDefinition 是唯一强依赖）。