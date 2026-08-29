# ADR-0026 — OpenTelemetry Adapter Boundary (Privacy-first Observability)

Status: Accepted

## Context

Research OS 需要在不泄漏科研内容与凭据的前提下回答运行问题(什么发生、
时间消耗在哪、哪个 Model/Tool/Experiment/Evaluation 出错、成本如何)。
M15(milestone authority:`docs/roadmap/MILESTONES.md` §M15)在 Adapter 面接入
OpenTelemetry 并落地 `docs/architecture/OBSERVABILITY.md` 的隐私优先观测。

现状:`packages/domain` / `packages/application` 从未 import 任何 telemetry 类型;
仓库没有结构化日志管线;`Consent` 常量 `capture_content = false` 是 OBSERVABILITY.md 的
唯一默认可编码语义。

## Decision

### 1. OpenTelemetry 只存在于 Adapter 层

```text
Domain / Application
  → Research OS operational signal(内部 vocabulary)
  → adapters/otel(OTel SDK 唯一所在地)
  → OTLP / HTTP
  → OTel Collector(测试/证据用 file+debug exporter;不引入 vendor)
```

- 禁止 `packages.domain` / `packages.application` import `opentelemetry.*`(import-linter 强制)。
- `Application` 面不暴露 `Span` / `Tracer` / `Meter`;只暴露 Research OS 自己的
  `OperationBegin/End`、`MetricSample` 与 `TelemetrySink` Port。
- OTel Context 不进入 Domain;trace_id 只作为 correlation id,不替代 Domain identity。
- Collector 不是 Audit Store;`span exists` ≠ `business action committed`;
  `telemetry missing` ≠ `business state missing`。

### 2. 观测默认不采集内容

- 内部 vocabulary **不存在内容通道**:`AttributeKey` 为闭集 allow-list,
  `sanitize_attributes` 只接受稳定 `str/int/bool` 标量,并对字符串执行
  `redact_text` 与截断。
- M15 **不实现 Debug 内容采样 Debug Mode**。观测默认不采集完整 Prompt/Response/
  reasoning/Tool 参数/Tool 输出/Source 全文/Artifact body/凭据/Authorization
  header/DSN secret;没有 "Debug Mode 放行原始内容" 的开关。
- 只记录:ID、digest、size、type、latency、token 数、status、稳定错误分类、
  provider/model/tool identity、允许的结构化 metadata。
- `capture_content = false` 以结构性方式保证(无法表达原文,而非运行时 flag)。

### 3. Telemetry 不是 Audit Truth

- Domain/Audit Event(EventEnvelope + outbox)是唯一业务真相;telemetry 可被
  sampled / delayed / dropped / exporter unavailable,但不影响 canonical state。
- Cost 只从 UsageLedger snapshot 派生;Eval verdict 只由 M11 `compute_verdict` /
  `compare_reports` 产生;Dashboard 不得自己发明 threshold。

### 4. 上游限定

- 采用 `opentelemetry-api`/`-sdk`/`-exporter-otlp-proto-http`
  (pin 到 `uv.lock` 现成 1.39.1/semconv 0.60b1)。Rejected:auto-instrumentation、
  GenAI content 属性、gRPC exporter、vendor SDK/attribute、custom semantic convention
  扩展点。详情见 `docs/references/upstream/M15_OTEL_QUALIFICATION.md`。

## Consequences

- API/run 行为在 telemetry off(默认)时与 M14/M13 完全一致;telemetry on 时仅
  增加 OTel SDK 依赖与 `FailSafeTelemetrySink` 包装,不影响返回语义。
- collector/exporter 故障不会破坏 PostgreSQL transaction、queue claim、lease
  heartbeat、outbox、Experiment、Evaluation、Evidence commit(M14 reliability path 独立成立)。
- 需要内容级 call-level 诊断的产品能力属于后续阶段(显式 opt-in + retention +
  redaction + 不得成为默认)。