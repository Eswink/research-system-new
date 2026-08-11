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
