# Budget, Quota & Cost Ledger v0.4.0

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

预留生命周期：reserve（Preflight 通过后冻结）→ run 收敛到
成功/失败/取消时 release（幂等，未知/已释放引用为 no-op）。
usage 记录 append-only，不随 release 清除。

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

## 7. M15 成本运营实现

- **quantity 三态**:`UsageLedgerEntry.quantity_status ∈ {KNOWN, UNKNOWN}` +
  `unavailable_reason`;UNKNOWN 绝不解释为 0(域不变量强制 reason)。
  历史行解码为 KNOWN/attempt=1,不重解释既有数字。
- **attempt 作用域**:`attempt` 字段进入 entry id(retry 追加而非碰撞);
  失败/重试耗尽/取消路径由 `record_attempt_usage` / `record_cancelled_usage`
  记账(quantity=0 + UNKNOWN,不伪造 turn 消耗)。
- **定价快照**:`examples/config/pricing.yaml`(出厂 `unpriced_v1`,零条目)
  → `PricingTable`(版本 + currency + effective_from + calculation_method +
  sha256 `pricing_digest()`);厂商价格不进 Domain、不进仓库默认配置。
- **成本投影**:`packages/application/cost/projection.py` 五状态
  `CostAmountStatus{ACTUAL, ESTIMATED, MONETARY_UNAVAILABLE, USAGE_UNKNOWN, ZERO}`,
  完备判定:UNKNOWN→USAGE_UNKNOWN;未定价/单位不匹配→MONETARY_UNAVAILABLE;
  quantity=0→ZERO;实测→ACTUAL;其余→ESTIMATED(表价计算)。每个金额盖
  pricing_version+digest 章,改价不改写历史投影。
- **唯一 usage 输入**:`BudgetLedger.snapshot()`(telemetry 绝不是成本输入,
  tests/application/test_cost_projection.py 断言)。
- **API**:`GET /runs/{id}/cost` 只读投影;usage 端点契约不变(M13 绿)。
