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

## 漂移判定（登记声明值 vs provider 返回标识）

中转站可能在**同一个 Model ID 之后替换真实模型**（AGENTS.md §4）。因此每次 probe 都把
**登记声明值**（`ModelDefinition.model_name`）与**provider 返回的模型标识**
（completion 响应里的 `model` 字段）做一次对比，结论以三态出现在读面上：

| 状态 | 何时 | 读面义务 |
| --- | --- | --- |
| `MATCH` | 去首尾空白后**精确相等** | 可以说「一致」 |
| `DRIFT` | 两者都存在但不相等 | **必须点名两个原值**，让人判断差在哪 |
| `UNKNOWN` | 未探到（没探测 / provider 没回模型名 / 探测失败） | **必须写明「未知不等于无漂移」** |

判据只有一处：`packages/domain/model_drift.py::assess_model_drift`（纯函数，无 IO）。

两条**刻意的严格**：

- 只做 `strip()`，**不折叠大小写**、不解释别名/日期后缀——`model-a` 与 `MODEL-A` 记
  `DRIFT`。本仓无法证明它们指向同一底层模型，宽松归一化等于替 provider 打包票；
- `UNKNOWN` **不是**「无漂移」。它是「无法证明一致」，必须与「已证明一致」在文案上分开，
  否则一次没探到的探测会被读成一次通过。

漂移是**可见性**，不是熔断：`DRIFT` 不自动禁用模型、不改变 eligibility 判定
（`docs/architecture/MODEL_COMPATIBILITY.md`）；它只把差异摆到读面上。

## 判定规则

- 每项验证通过的能力以 `CapabilityAssertion(status=PROBED, ...)` 写入结果断言，`probe_version` 记录 suite 版本；
- 失败的能力写入 `ModelProbeResult.capability_failures`（`CapabilityProbeFailure`），携带 `error_category` 区分“模型不支持”（`MODEL_INCOMPATIBLE`）与网络/认证/限流/超时/中转站故障（`EXECUTION_FAILURE` / `MODEL_AUTH` / `MODEL_RATE_LIMIT` / `MODEL_TIMEOUT` / `MODEL_RELAY_UNAVAILABLE`）；
- 运行类失败（429/5xx/timeout/网络）**不**写入能力断言，避免把瞬时故障误判为永久能力变化；
- 非致命失败（streaming/tool calling/structured output）不使整体 probe 失败，`ok` 仍为 true 且失败原因可机器读取；
- `ok=False` 的 probe 输出机器可读 `ModelProbeResult`（`error_category` ∈ FailureCategory）；
- 错误消息必须 redacted（见 `docs/security/SECRET_MANAGEMENT.md` §6）；
- Discovery（`GET <base_url>/models`）结果以 `CapabilitySource.DISCOVERED` 标记，默认不启用，需用户显式确认（manual ModelDefinition 是唯一强依赖）。