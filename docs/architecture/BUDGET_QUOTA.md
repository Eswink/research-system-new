# Budget, Quota & Cost Ledger v0.2.2

## 1. 预算维度

```text
model tokens/requests/cost
tool requests/cost
CPU/GPU time
memory/storage
network/download
wall-clock
agent turns
parallelism
```

## 2. BudgetReservation

Run 启动前预留：

```text
run
phase
agent
tool
compute
```

避免多个并行 Agent 同时透支。

## 3. UsageLedger

所有实际消耗进入 append-only Ledger：

```text
resource_type
quantity
unit
estimated_cost
actual_cost?
source
task/agent/tool/model
timestamp
```

## 4. 中转站价格未知

用户 Relay 未必返回可信价格。

策略：

- 用户可配置单价；
- 无单价时按 token/request/turn/compute 进行硬限制；
- 标注 cost 为 UNKNOWN，不伪造金额。

## 5. Threshold

```text
SOFT_WARNING
AUTO_DEGRADE
REQUIRE_APPROVAL
HARD_STOP
```

## 6. Degradation

预算紧张时可以：

- 减少并行 Scout；
- 使用 cheaper ModelProfile；
- 缩小检索范围；
- 降低实验矩阵；
- 保留必须 Reviewer。

降级必须记录 Decision。
