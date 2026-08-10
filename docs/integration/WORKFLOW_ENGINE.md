# Workflow Engine Integration

## MVP

```text
LocalWorkflowEngine
+
PostgreSQL task queue / lease
```

用于快速开发和 contract tests。

## Production

```text
TemporalWorkflowEngine
```

Temporal 负责：

- durable orchestration；
- timers；
- retry；
- pause/signal；
- long-running workflow。

LLM、Tool、Sandbox 执行放 Activity/外部 Worker，不能进入 deterministic Workflow code。

## Domain Boundary

Temporal history 不是 canonical Domain state。

## Idempotency

即使使用 Temporal，外部 Activity 仍要按 idempotency 设计。
