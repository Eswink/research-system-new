# Failure Model v0.4.0

## Categories

```text
CONFIGURATION
MODEL_AUTH
MODEL_RATE_LIMIT
MODEL_TIMEOUT
MODEL_RELAY_UNAVAILABLE
MODEL_INCOMPATIBLE
MODEL_DRIFT
TOOL_UNAVAILABLE
TOOL_SCHEMA_MISMATCH
TOOL_TIMEOUT
POLICY_DENIED
APPROVAL_REJECTED
WORKSPACE_FAILURE
EXECUTION_FAILURE
GPU_UNAVAILABLE
GPU_OOM
ARTIFACT_CORRUPTION
VALIDATION_FAILURE
BUDGET_EXHAUSTED
WORKER_LOST
SYSTEM_BUG
SCIENTIFIC_NEGATIVE_RESULT
```

M17 GPU 分类边界（ADR-0029）：

- `GPU_UNAVAILABLE`：设备不可见 / CUDA 初始化失败 / driver-runtime 不兼容 /
  framework 无 CUDA / GPU profile 作业从未被任何 worker claim 即超期。
  属于基础设施失败，**绝不降级为 CPU 执行**。
- `GPU_OOM`：CUDA 显存耗尽（`torch.cuda.OutOfMemoryError` 或容器内报告
  `gpu_oom=true`）。属于执行/资源失败。
- **与 `SCIENTIFIC_NEGATIVE_RESULT` 的边界**：模型指标未改善（如准确率
  下降、吞吐无提升）是合法科学结论，走 `SCIENTIFIC_NEGATIVE_RESULT` /
  `ExperimentRun.NEGATIVE_RESULT` 终态；CUDA OOM 是执行失败，走
  `GPU_OOM` / FAILED 终态。判据是「失败发生在计算子系统（显存/设备）」
  还是「计算完成后的科学语义」，二者不混淆（边界由测试固定）。

## Retry Matrix

| Category | Auto Retry | Notes |
|---|---|---|
| MODEL_RATE_LIMIT | Yes | backoff/jitter |
| MODEL_TIMEOUT | Yes | backoff/jitter |
| MODEL_RELAY_UNAVAILABLE | Yes | 5xx 中转站故障，backoff/jitter |
| TOOL_TIMEOUT | Conditional | only idempotent |
| WORKER_LOST | Yes | lease expiry/dedupe |
| MODEL_INCOMPATIBLE | No | preflight/config fix |
| POLICY_DENIED | No | approval/policy change |
| BUDGET_EXHAUSTED | No | budget decision |
| VALIDATION_FAILURE | Rework | new attempt/agent |
| SCIENTIFIC_NEGATIVE_RESULT | No failure | record result |
| GPU_UNAVAILABLE | Conditional | 幂等 GPU 作业可重试（先重新探测 capability）；绝不 CPU fallback |
| GPU_OOM | Conditional | 幂等作业可在显存契约修正后重试；同参数盲目重试无意义 |

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
