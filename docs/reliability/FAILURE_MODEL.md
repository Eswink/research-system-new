# Failure Model v0.2.2

## Categories

```text
CONFIGURATION
MODEL_AUTH
MODEL_RATE_LIMIT
MODEL_INCOMPATIBLE
MODEL_DRIFT
TOOL_UNAVAILABLE
TOOL_SCHEMA_MISMATCH
TOOL_TIMEOUT
POLICY_DENIED
APPROVAL_REJECTED
WORKSPACE_FAILURE
EXECUTION_FAILURE
ARTIFACT_CORRUPTION
VALIDATION_FAILURE
BUDGET_EXHAUSTED
WORKER_LOST
SYSTEM_BUG
SCIENTIFIC_NEGATIVE_RESULT
```

## Retry Matrix

| Category | Auto Retry | Notes |
|---|---|---|
| MODEL_RATE_LIMIT | Yes | backoff/jitter |
| TOOL_TIMEOUT | Conditional | only idempotent |
| WORKER_LOST | Yes | lease expiry/dedupe |
| MODEL_INCOMPATIBLE | No | preflight/config fix |
| POLICY_DENIED | No | approval/policy change |
| BUDGET_EXHAUSTED | No | budget decision |
| VALIDATION_FAILURE | Rework | new attempt/agent |
| SCIENTIFIC_NEGATIVE_RESULT | No failure | record result |

## FailureRecord

```text
category
operation
attempt
retryable
cause chain
redacted context
artifact refs
recommended action
```

## Recovery

```text
retry
replan
switch model
switch provider
fork task/run
compensate
manual intervention
terminate
```
