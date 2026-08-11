# Evaluation Harness v0.4.0

## 1. Fixed Test Layers

```text
Domain/schema tests
Protocol/compiler tests
Model relay compatibility tests
Tool/provider contract tests
Runtime adapter tests
Security/adversarial tests
Research process fixtures
Deliverable/evidence tests
```

## 2. Test Modes

```text
OFFLINE_FAKE
REPLAY
SANDBOX_INTEGRATION
LIVE_CANARY
BENCHMARK
```

默认 CI 使用 OFFLINE_FAKE。

## 3. Model/Role Eval

每个 ModelDefinition 可针对 Role fixture 评估：

```text
task success
schema validity
tool-use success
latency
tokens/cost
unsupported claims
policy violations
```

## 4. Replay

保存 redacted input refs、tool observations、artifacts，使 Agent/Model 改动可在相同 fixture 比较。

## 5. Human Calibration

LLM Judge 的评分需要抽样人工校准，不能视为绝对 ground truth。
