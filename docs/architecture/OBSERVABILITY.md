# Observability v0.4.0

## 1. Trace Hierarchy

```text
project
└ run
  └ phase
    └ task
      └ agent_session
        ├ llm_call
        ├ tool_call
        └ execution_run
```

传播：

```text
project_id
run_id
phase_run_id
task_id
agent_run_id
agent_session_id
tool_call_id
experiment_run_id
trace_id
```

## 2. Signals

### Traces
因果链和延迟。

### Metrics

```text
LLM latency/error/token
tool latency/error
queue lag
lease expiry
workspace startup
agent stuck rate
retry count
budget utilization
evaluation pass rate
```

### Logs
结构化、redacted。

### Domain Events
产品审计，不等于 telemetry。

## 3. GenAI Content

模型输入输出可能包含敏感数据。

默认：

```text
capture_content = false
```

仅记录摘要/digest/size/usage。

## 4. Suggested SLO Targets

仅作为产品目标，不是当前承诺：

```text
Control API availability
event delivery latency
task resume success
artifact durability
secret leakage incidents = 0
```

## 5. Alerting

重点：

- endpoint circuit open；
- repeated stuck agents；
- lease churn；
- budget anomaly；
- tool permission denial spike；
- artifact digest mismatch；
- outbox backlog。

## 6. Implementation Map (M15)

M15 落地了自营观测词汇 + OpenTelemetry 适配器（ADR-0026）：

```text
packages/application/observability/   OperationScope/Outcome, CorrelationRef,
                                      闭集 AttributeKey/MetricName/MetricLabel,
                                      sanitize_attributes, operation()
packages/application/ports/telemetry_sink.py   TelemetrySink Port + Null 默认
adapters/otel/                        config/resource/span_mapping/metric_mapping/
                                      sink/provider/failsafe（OTel SDK 只在此包）
adapters/otel/collector/              digest-pinned collector(Dockerfile+config)
adapters/fakes/telemetry_sink.py      FakeTelemetrySink
tests/observability/                  roundtrip/canary/fault-injection/overhead
tools/probes/probe_telemetry_soak.py  手工 soak 探针
infra/compose/otel-evidence.yaml      collector 证据管线
```

关键实现事实（均有测试支撑）：

- 无内容通道：prompt/response/tool args/artifact body 在词汇层结构性不可表达
  （`AttributeKey`/`MetricLabel` 闭集 + sanitize）；不存在 `capture_content` 开关，
  M15 无内容 Debug Mode。
- fail-open：`FailSafeTelemetrySink` 吞掉一切 inner 异常并计 drop；
  collector down/timeout/500/slow/restart/hangup/queue-full/malformed-endpoint
  八种注入下 canonical state 与 telemetry-off baseline 逐项相等
  （tests/observability/test_failure_isolation.py；PG 变体 postgres 标记）。
- 信号站点：relay gateway（含内部重试 metric）、tool_plane 执行用例与
  PolicyWrappedToolExecutor、sqlite/pg workflow 引擎（queue lag / task duration /
  lease expired）、outbox relay（backlog/drained）、schedulers（per-pass span）、
  docker execution backend、eval runner、run orchestration（run/task span）。
- duration metric 由 sink 在 end_operation 自动派生（scope→MetricName 映射）；
  TASK 的 duration 由 workflow engine 按 created_at 计，避免二次计数。
- 真实 OTLP wire bytes 由 in-repo receiver（tests/observability/otlp_receiver.py）
  接收并解码；隐私 canary 对原始字节零标记出现。
- 架构边界：`.importlinter.otel` + 各层 forbidden 列表 + AST 扫描测试强制
  OTel SDK 只存在于 adapters/otel。

## M16 Distributed Execution Signals

- 新增闭集词表：OperationScope（worker_session / worker_dispatch /
  remote_execution）；MetricName（worker.count / registered_total /
  heartbeat_lost_total / drain_total / protocol_mismatch_total、
  scheduler.claim_latency_ms / partition_lag、remote_execution.duration_ms /
  failover_total / stale_result_rejected_total /
  artifact_transfer_failed_total）；OperationFailureReason（worker_lost /
  stale_result_rejected / protocol_mismatch / artifact_integrity_failed）。
- `worker_ref`（worker_id 的 sha256 短 digest）只作为 span attribute；
  原始 worker id、session token、bundle 内容不进遥测（canary 断言）。
- partition label 有界 0..15；worker_state / rejection_reason 闭集折叠。

## 观测隐私边界与受判面（GOAL-024，2026-09-28）

**两条条款**（写作纪律：本节只描述今天树上的事实与明确的空白，**不作安全结论**）：

```text
条款 ①（canonical 允许持有用户输入）：canonical state（PG 域实体 / SQLite 域表）允许持有
  用户自己的任务输入与产出 —— 那是业务真相，不是泄漏；不得用「金丝雀出现在 DB 里」判红。
条款 ②（非 canonical 出口不得含内容）：非 canonical 出口不得含用户内容；内容只允许出现在
  「契约声明返回/保存它」的载体上，其余出口一律零命中。
```

**受判出口（6 条）**：OTLP traces wire / OTLP metrics wire / 应用日志（stdlib logging）/
读面响应（应用自身路由表）/ 失败载荷 / 磁盘制品（运行与证据目录制品）。

**读面口径 = 白名单**：读面只判「契约声明返回内容」的路由能否看到内容；其余读路由必须零命中。
被点名的判据文件（**改名即判红**）：

```text
tests/observability/test_privacy_canary.py                 词汇层 + wire 隐私金丝雀
tests/observability/test_privacy_exit_census.py             非 canonical 出口清单（分区 + 理由）
tests/observability/test_privacy_content_canary_end_to_end.py 端到端内容金丝雀 + 逐通道正控制
tests/observability/test_privacy_read_face_canary.py        读面 68 条路由逐条实取
tests/observability/test_privacy_boundary_clauses_are_pinned.py 本节条款与未覆盖面的钉点
```

**未覆盖面（逐条登记，不静默）**：

```text
未覆盖面 1：debug mode 的受控内容采样（AGENTS.md §10 允许、受 retention 管理）未验证 ——
            本仓默认 capture_content=false 且不存在该开关；开关一旦出现必须重新取证。
未覆盖面 2：真实 collector / 生产部署面未验证 —— 本轮全部判据跑在进程内（OTLP 只发 loopback
            测试接收器），外部 collector、网络与部署形态的行为不在射程。
未覆盖面 3：CI 产物面不在射程 —— CI 的日志/工件缓存由平台持有，本轮不对其作任何断言。
未覆盖面 4：R-M1 未收口 —— 本仓不宣称项目安全；上述条款只覆盖被点名判据实际跑到的那些面。
```

