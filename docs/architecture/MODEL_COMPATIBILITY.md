# Model Compatibility & Drift v0.2.2

## 1. 背景

用户只提供中转站 URL、Key 和 Model ID。

不同中转站/模型可能：

- 不支持原生 Tool Calling；
- 返回非标准 JSON；
- Streaming 行为不同；
- Context Window 不准确；
- 在同一 Model ID 后切换底层模型；
- 不返回价格或可靠 usage；
- 忽略部分参数。

因此不能只凭 Model ID 判定能力。

## 2. ModelCapability

建议枚举：

```text
CHAT
STREAMING
TOOL_CALLING_NATIVE
TOOL_CALLING_EMULATED
STRUCTURED_OUTPUT_NATIVE
STRUCTURED_OUTPUT_PROMPTED
VISION
REASONING
EMBEDDING
SEED
USAGE_REPORTING
SYSTEM_FINGERPRINT
```

## 3. Capability 来源

```text
USER_DECLARED
DISCOVERED
PROBED
ADMIN_OVERRIDE
RUNTIME_OBSERVED
```

每项能力记录：

```text
status
confidence
source
last_verified_at
probe_version
```

## 4. Role Eligibility

示例：

### ExperimentEngineer

硬要求：

```text
CHAT
TOOL_CALLING_NATIVE or approved emulation
```

### ResearchWriter

可允许：

```text
CHAT
STRUCTURED_OUTPUT_PROMPTED
```

### VisionEvidenceCurator

硬要求：

```text
VISION
```

不兼容模型在 Preflight 阶段拒绝。

## 5. Probe Suite

低成本测试：

```text
connectivity
authentication
basic completion
streaming
tool call
schema output
context limit smoke test
usage metadata
```

Probe 不应把敏感项目内容发送到模型。

## 6. Model Runtime Fingerprint

中转站可能让相同 Model ID 漂移。

Run 记录：

```text
requested model ID
returned model field
system fingerprint（若返回）
safe response metadata
probe suite digest
calibration prompt version
calibration result digest
observed capability matrix
```

这不能保证知道真实底模，但能提高漂移可见性。

## 7. Fallback

Fallback 只能在满足 Role 硬能力时发生。

必须记录：

```text
from_model
to_model
reason
time
task
manifest policy
```

对已开始的 AgentSession，默认不原地切换模型；优先新 Session/Fork，避免上下文语义混杂。

## 8. Health / Circuit Breaker

Endpoint 状态：

```text
UNKNOWN
HEALTHY
DEGRADED
OPEN_CIRCUIT
DISABLED
```

连续失败触发熔断；恢复采用半开探测。
