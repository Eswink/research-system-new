# M15 OpenTelemetry Qualification Report

- Date: 2026-08-28
- Scope: `docs/roadmap/MILESTONES.md` M15 §Upstream Qualification (OpenTelemetry; genai 内容默认关闭)
- Upstream: OpenTelemetry Python SDK/API + OTLP/HTTP exporter + OTel Collector (contrib)
- Method: 官方文档 + 官方 repository 证据;版本事实依据 `uv.lock` 现有传递依赖与其 sdist 摘要;不批量 clone、不把 upstream 源码混入主仓库。Ad-Hoc spike 代码在 `tests/observability/` 与 `adapters/otel/`(adapter 边界内),不放到 `packages/domain` / `packages/application`。
- Inputs: `docs/architecture/OBSERVABILITY.md`、ADR-0020、ADR-0026(本文件结论所依据的边界决策)、`UPSTREAM_COMPONENTS.yaml`(opentelemetry PLANNED 条目)、`tests/architecture/python/*`(import-linter 边界)

## Upstream Source

| Field | Value |
|---|---|
| Repository (SDK/API) | `https://github.com/open-telemetry/opentelemetry-python` |
| Pinned revision (SDK/API) | `opentelemetry-api==1.39.1`、`opentelemetry-sdk==1.39.1`(PyPI;直接进入 Research OS `pyproject.toml` 与 `uv.lock`) |
| sdist digest (api) | sha256 `fbde8c80e1b937a2c61f20347e91c0c18a1940cecf012d62e65a7caf08967c9c`(`uv.lock:1323`) |
| sdist digest (sdk) | sha256 `cf4d4563caf7bff906c9f7967e2be22d0d6b349b908be0d90fb21c8e9c995cc6`(`uv.lock:1426`) |
| Repository (semantic conventions) | `https://github.com/open-telemetry/semantic-conventions` |
| Pinned revision (semconv) | `opentelemetry-semantic-conventions==0.60b1`(仅作为 `opentelemetry-api`/`-sdk` 的**传递依赖**保持解析;Research OS 代码零 import、0.60b1 为 pre-release,M15 复审后**移除了直接依赖声明**) |
| sdist digest (semconv) | sha256 `87c228b5a0669b748c76d76df6c364c369c28f1c465e50f661e39737e84bc953`(传递解析锁定;`uv.lock`) |
| Repository (Collector contrib) | `https://github.com/open-telemetry/opentelemetry-collector-contrib`(官方发行:opentelemetry-collector-releases) |
| Collector pin | `otel/opentelemetry-collector-contrib` 镜像,经 `adapters/otel/collector/Dockerfile` 以 sha256 digest 固定(见 `UPSTREAM_COMPONENTS.yaml`) |
| License | SDK/API/Collector:Apache-2.0(官方仓库 LICENSE;evidence 见 `UPSTREAM_COMPONENTS.yaml` 与 `docs/references/LICENSE_MATRIX.md`) |
| Qualification date | 2026-08-28 |
| Compatibility facts | Python 3.12 (Research OS);`opentelemetry-*` 已在 `uv.lock` 中作为 `openhands-sdk → lmnr` 与 `fastmcp-slim` extra 的传递依赖存在,版本对齐为兼容性约束;OTLP/HTTP 仅依赖 `httpx`/`requests` 已现成,无新增二进制原生依赖 |

> 稳定性风险:0.60b1 为 pre-release。为避免滚入破坏性变更,M15 仅消费
> `opentelemetry-api`/`-sdk`/`-exporter-otlp-proto-http` 的稳定 API 面;
> Research OS 自有 vocabulary 不经由 semconv 扩展点(不写自定义 GenAI 语义
> 属性),全仓代码对 `opentelemetry-semantic-conventions` **零 import**——
> 它只作为 SDK 的传递依赖被解析,M15 复审后已移除直接依赖声明并同步
> `UPSTREAM_COMPONENTS.yaml`/`LICENSE_MATRIX.md`。

## Adopted Surfaces

| Surface | 采用方式 | 证据/理由 |
|---|---|---|
| `opentelemetry-api` Trace API (`opentelemetry.trace`) | Adapter 内创建真实 `Span`(显式 parent context、显式 start/end 时间戳、显式 `set_attribute`) | DoD-2/3/4/5;与内部 `OperationBegin/End` 一对一映射,不依赖隐式 context composite |
| `opentelemetry-sdk` `TracerProvider` + Batching SpanProcessor | Adapter 内初始化;采样、resource attribute、exporter queue 在该层配置 | batching/export 语义(OBSERVABILITY.md §2) |
| `opentelemetry-exporter-otlp-proto-http` + SQLite/`:memory:` 测试接收器 | OTLP/HTTP 导出;测试用 in-repo HTTP receiver 解码真实 OTLP protobuf(`tests/observability/otlp_receiver.py`) | DoD-6 canary 检视真实 wire bytes,不依赖 vendor UI 判断 |
| Collector `file` + `debug` exporter(contrib) | 仅测试/证据用 pipeline;任何 vendor 后端均不进入默认 repo | Deployment 见 `adapters/otel/collector/collector.yaml` |
| Resource attributes | `service.name=research-os`、`service.version=<VERSION>`、host 基础属性;不采集 host home/secret | `docs/architecture/OBSERVABILITY.md` |
| Stable signal types 子集 | trace + metric(仅 Research OS 定制的 `OperationOutcome`/`MetricSample`),不加 logs signal | 仓库当前无 `logging`/`structlog` 面,logs 推迟到后续阶段 |

## Rejected / Deferred Surfaces

- **Auto-instrumentation** (e.g. `opentelemetry-instrumentation-fastapi`, flask):不采用。自动插桩会 capture 未经 Research OS 语义裁剪的内容,违反隐私优先与自营 vocabulary 策略。
- **GenAI semantic conventions 的 content-bearing 属性**(`gen_ai.prompt`、`gen_ai.completion`、`gen_ai.prompt.*` 等携带原文的字段):拒绝。M15 不建立内容采集通道,无捕获原文的配置项。
- **gRPC OTLP exporter**(`opentelemetry-exporter-otlp-proto-grpc`):M15 不采用;OTLP/HTTP 简化依赖与供应链,LAN/Local 部署足够。
- **OTel Logs signal**:不采用。仓库尚无结构化日志管线;没有可观测日志面,不引入半个 logs 实现。
- **Vendor SDK / vendor-specific attributes**(Laminar、OpenInference 等 vendor 语义):不采用。vendor 类型与 attribute 一律不进入核心层;任何 vendor 集成都走 `adapters/otel/` 的 mapping。
- **Debug 内容采样 Debug Mode**:M15 明确**不**提供 (ADR-0026)。观测默认不采集内容,不存在 "Debug Mode 放行原始内容" 的开关;后续阶段若引入,须为显式 opt-in + retention policy + redaction,且不能成为默认生产路径。

## Collector Failure Behavior (evidence from OTel SDK/Collector design)

| Failure scenario | 观测 | 风险与忽略策略 |
|---|---|---|
| Collector down / OTLP timeout | Exporter 重试 + `BatchSpanProcessor` 有界队列;`otel_sdk` 导出失败记录在 exporter 内部,不 throw 回调用线程 | `FailSafeTelemetrySink` 捕获一切,不改变业务调用方返回值 |
| 500 / malformed endpoint | Exporter 标记导出失败并计入重试;`schedule_delay` 内重试 | 与 M14 reliability path 独立:队列 claim / lease / outbox / 事务不依赖 telemetry |
| slow collector | 影响 exporter flush 时延,队列堆积,`max_queue_size` 触发丢弃 | 有界队列 + `shutdown` 只 flush 固定时长 |
| exporter restart | OTLP/HTTP 连接复用重连;丢批次不重试原始 HTTP 请求 | 丢 telemetry 是允许的;canonical state 不回退 |
| network interruption | 与 down 同路径 | DoD-7 断言 canonical state 不变 |
| malformed exporter URL 配置 | exporter 构造失败在 adapter init 抛出,被 FailSafe 吞掉,telemetry 保持 off | 不阻断 API/run |

关键结论:OTel SDK 采用 fail-open 语义(batch processor 的失败不会传播到业务线程),与 `FailSafeTelemetrySink` 叠加后,telemetry 故障不可能破坏 Research Run / PG transaction / outbox。

## Scoring: ADOPT

OpenTelemetry SDK/API (OTLP/HTTP) + Collector 定位为 ADAPTER 层依赖。不做 content capture、不做 auto-instrumentation、不把 vendor types 引入 Domain/Application。为满足 m0 供应链门禁(ADOPTED 必须直接锁定依赖),6 个 OTel Python 包提升为 `pyproject.toml` 直接依赖并 pin 到 `uv.lock` 现成版本;Collector 镜像经 `adapters/otel/collector/Dockerfile` 以 sha256 digest 固定。

## Next Steps

1. `adapters/otel/` 实现(span/metric mapping + FailSafe sink + provider init/shutdown)。
2. `packages/application/observability/` 内部 vocabulary(闭集 `AttributeKey`/`MetricName`/`MetricLabel`,无内容通道)。
3. `tests/observability/otlp_receiver.py` + `tests/observability/*`(trace hierarchy, privacy canary, fault injection)。
4. `docker-compose.m15.yml` + collector config + `UPSTREAM_COMPONENTS.yaml` ADOPTED 更新。

## 路径迁移说明（2026-09-07 根目录分类归档）

上文 Next Steps 中的 `docker-compose.m15.yml` 为资格化当时路径；该文件现已迁至
`infra/compose/otel-evidence.yaml`。原资格化事实不变，完整映射见
`docs/operations/REPOSITORY_HYGIENE.md`。
