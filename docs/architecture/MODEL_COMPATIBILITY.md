# Model Compatibility & Drift v0.4.0

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

声明参数**不参与**本节的判定：`ModelDefinition.context_window_tokens` /
`thinking_intensity` 是用户声明值，本版本既不发送给 provider，也不参与 capability
匹配、eligibility 或预算折算；未声明（`null`）与声明某值在读面必须是可区分的两态。
详见 `DOMAIN_MODEL.md` §5「声明参数」。

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

## 9. `ModelCompatibilityProfile` 的形态（已定的决定，2026-09-25）

**决定（用户 2026-09-25 按 `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` 建议列拍板
**D-08 → 取 (b)**）：`ModelCompatibilityProfile` **维持派生视图**。**

- **它不是 Canonical State 的一等域实体**：不建表、不迁移、不进 RunManifest 冻结面；
  它每次由**已在树的事实**现算——`ModelProbeResult`（§5 的探测套件结果）、
  `ModelDefinition` 的声明字段、`ModelCapability` 词表，三者的**函数**。
- **为什么维持派生**（依据，供后续引用）：
  1. **可重建**：派生视图的全部输入都是已冻结 / 已登记的事实，重算幂等 ⇒ 不存在
     「两个真相源不一致」的风险面（AGENTS.md §6：PostgreSQL Domain Entity 是业务真相，
     派生面不是）。
  2. **零迁移面**：建一等实体要定义主键、生命周期与回滚，而它**今天没有任何写入方**
     ——为一个只读的复合事实付迁移与回滚成本不划算。
  3. **判据成本**：维持派生时，「兼容性判定」的判据只需断言**函数**（输入 → 输出），
     不需要额外的一致性判据去对齐两张表。
- **代价（如实登记）**：每次需要兼容性判定都要**现算**；若未来某个热路径把它算成了
  瓶颈，或出现「需要按兼容性维度检索 / 聚合」的需求，这条决定的**前提**就变了。

### 若要改成一等域实体（选项 (a)）的前置条件

**必须先出 ADR**（且该 ADR 至少写清三件事），否则**不得**动：

1. **Canonical State 的迁移**：新实体与既有 `ModelProbeResult` / `ModelDefinition` 的
   权威关系（谁是真相、谁派生），以及**历史数据如何回填**；
2. **回滚方案**：从一等实体退回派生视图时的动作与数据处置；
3. **一致性判据**：一旦有两个面，就必须有一条判据防止它们漂移（今天没有这条判据，
   因为只有一个面）。

> 本节**只写决定与前置条件**：**零代码改动**、**零迁移**、**零 Canonical State 边界变更**。
> 该决定在 `GOAL-20260925-016` 的 EC-04 固化；**下轮不再就同一问题重复提问**。
