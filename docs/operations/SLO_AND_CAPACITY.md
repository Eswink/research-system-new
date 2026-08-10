# SLO & Capacity Planning v0.2.2

## Suggested Indicators

```text
API availability/latency
Event delivery latency
Task queue lag
Lease expiry rate
Resume success rate
Endpoint/tool error rate
Workspace startup latency
Artifact durability/verification
Evaluation pass rate
Budget forecast accuracy
```

## Capacity Drivers

- concurrent AgentSession；
- Relay concurrency/rate limit；
- Tool Provider rate limit；
- Docker/remote sandbox startup；
- Artifact throughput/storage；
- DB event/outbox volume；
- embedding/index rebuild。

## Admission Control

Run 启动前根据：

```text
available worker slots
endpoint concurrency
tool quotas
compute capacity
budget reservation
```

决定 READY 或 WAITING_CAPACITY。

## Load Shedding

优先降低：

- optional Scout；
- low-priority index jobs；
- verbose telemetry；
- background eval。

不能跳过安全/证据 Hard Gate。
