# Event Stream API

## SSE Event

```json
{
  "event_id": "...",
  "type": "task.completed",
  "occurred_at": "...",
  "run_id": "...",
  "task_id": "...",
  "trace_id": "...",
  "payload": {}
}
```

## Resume

客户端传：

```text
Last-Event-ID
```

Server 从 durable event/outbox projection 继续。

## Backpressure

- token streaming 与 Domain Event stream 分离；
- 大 payload 使用 Artifact ref；
- 慢客户端允许丢弃临时 telemetry，不丢 Domain Event。

## Redaction

事件永远不包含 Secret；Prompt/Response 默认只含摘要/digest。
