# Model Gateway v0.4.0

## 1. Flow

```text
AgentSpec
→ ModelBinding
→ ModelResolver
→ ModelEligibilityPolicy
→ ModelDefinition
→ LLMEndpoint
→ OpenAICompatible Gateway / OpenHands LLM config
```

## 2. Responsibilities

- credential resolve；
- endpoint health/circuit breaker；
- timeout/retry；
- usage normalization；
- error taxonomy；
- runtime fingerprint；
- fallback audit；
- content/telemetry policy。

## 3. OpenHands Mapping

OpenHands 的 LLM 接口支持 model/base_url/api_key 等配置，底层 provider naming 由 Adapter 转换。

Domain：

```text
model_name = user Model ID
```

Adapter：

```text
runtime provider/model identifier
```

identifier 变换按 `endpoint.protocol` 取前缀（`OPENAI_COMPATIBLE` ⇒ 探测失败时 `openai/`；
`ANTHROPIC` ⇒ `anthropic/`），未知协议点名拒绝——见 `integration/LLM_ENDPOINTS.md` §1。

上游命名不进入 Domain。

## 4. Eligibility

模型必须满足 Role/Task 硬能力。

例如执行型 Agent 不得在 Tool Calling Probe 失败后继续自动运行。

声明参数（`ModelDefinition.context_window_tokens` / `thinking_intensity`）**不参与**
eligibility 判定：它们是用户对该模型的声明，当前既不发送给 provider，也不参与能力
匹配或预算折算。把它当作已生效的运行时约束会制造「配了就等于跑到了」的假象；
同理，读面必须把「未声明」与「声明了某个值」渲染成可区分的两态
（见 `architecture/DOMAIN_MODEL.md` §5 声明参数）。

## 5. Fallback

Fallback：

- 必须满足硬能力；
- 受 budget/policy；
- 记录原因和实际模型；
- Session 中途默认不切换；
- 优先 Fork/New Session。

## 6. Cost

Relay 可能没有可信价格。

Gateway 支持：

```text
user-configured price
reported usage
unknown cost + hard token/request limit
```

不编造 cost。
