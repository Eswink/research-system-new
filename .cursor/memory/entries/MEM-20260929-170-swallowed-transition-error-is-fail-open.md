---
id: MEM-20260929-170
title: "吞掉状态机迁移异常 = fail-open：断路器半开探测名额耗尽时请求被放行，声明语义与代码行为相反"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-249-goal-026-ec03-breaker-dead-letter-cancel.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-250-goal-026-ec03-breaker-dead-letter-cancel.md
supersedes: []
tags: [circuit-breaker, fail-open, relay-gateway, goal-026, ec-03, tightening]
---

## 做了什么

GOAL-026 EC-03 的「半开探针预算」判据把一处**真缺陷**证了出来，并按 GOAL 授权**只收紧**修复：

- 声明语义：`CircuitBreakerConfig.half_open_max_probes` 与 `_consult_circuit` 自己的注释
  都要求「名额耗尽的再次 consult ⇒ **拒绝**」。
- 实测行为（修复前）：`apply_tick` 在半开名额耗尽时抛 `CircuitBreakerTransitionError`，
  而**接线处把它吞掉了**（`except ...: pass`）⇒ 状态停在 `HALF_OPEN` ⇒ `state.is_open` 为**假**
  ⇒ 后续请求**被放行**。判据红形态原样：`Failed: DID NOT RAISE CircuitOpenRelayError`。
- 修复：`adapters/relay/gateway.py::_consult_circuit` 改为 fail-closed
  （`raise CircuitOpenRelayError(FailureCategory.MODEL_RELAY_UNAVAILABLE, ...) from None`）。

## 为什么这样做

- **吞异常的默认方向是「放行」**：状态机迁移函数抛错时，若调用方 `pass` 掉并沿用**旧状态**，
  而旧状态恰好是「允许通过」的那一态（`HALF_OPEN` 的 `is_open` 为假），代码的实际语义就
  从「拒绝」翻成「放行」。**门槛类**逻辑（断路器、限流、预算）里，这个翻向是安全相关的。
- **「有字段」不等于「字段有效」**：`half_open_max_probes` 存在、被声明、被文档引用，
  但预算耗尽这一态从未被任何判据压过 ⇒ 上限形同虚设。**声明一个上限不是实现一个上限**。
- **判据必须能压到「预算耗尽」**：这一态无法从公开 API 确定性构造（需要「探针正在飞」），
  所以判据要能通过**受控置态**（`gateway._store_breaker(...)`）到达，并断言
  「异常类型 + 下游调用计数 `== 0`」两件结构化事实，而不是只断言异常消息。

## 怎么做与复现

1. 判据：`tests/adapters/relay/test_gateway_half_open_budget.py`
   （`CLOSED` 放行 / `OPEN` 拒绝且不触达下游 / `HALF_OPEN` 放行一个探针 / 阈值驱动开路 /
   名额耗尽 ⇒ 拒绝且不触达下游）。
2. 反证（把阈值调成不可能达到）：`packages/domain/circuit_breaker.py` 的
   `if failures >= config.failure_threshold:` → `+ 1000000000` ⇒ 判据红（`is_open` 为假）。
3. 命令：`uv run --frozen --no-sync python -B -m pytest
   tests/adapters/relay/test_gateway_half_open_budget.py
   tests/adapters/relay/test_gateway_circuit.py tests/domain/test_circuit_breaker.py -q`
   ⇒ **29 passed**。
4. 复原核对：`packages/domain/circuit_breaker.py` 的 raw `sha256` 回到
   `e392139eb4da01869ad168fd6f32ce9a48e053b3ac2fc09bc12aa9e4f1a9e04e`。

## 适用边界

- 修复方向是**更严**（放行 → 拒绝），但确实是**可观察行为变更**：配置了断路器的端点在
  「半开且名额耗尽」时会开始收到 `CircuitOpenRelayError`（登记 `RECHECK-250` 的 `W-1`）。
- 只覆盖 `OpenAIChatGateway` 的 chat 与读面探针共用入口 `_consult_circuit`；工具面断路器
  （`packages/application/tool_plane/health.py`）是**另一处接线**，另有吸收态判据。
- 判据里的「不触达下游」靠**计数传输**（`httpx.BaseTransport` 子类）证明，不是靠日志。

## 来源

- `PLAN-20260929-249`（GOAL-026 EC-03）与 `RECHECK-20260929-250`（§1 与 §6）；
- 实跑留档：`scratch/goal026-ec03-press-matrix.log`（二进制写盘 / `CR` 计数 0）；
- 相关代码：`adapters/relay/gateway.py::_consult_circuit`、
  `packages/domain/circuit_breaker.py::apply_tick`；
- 同轮另一条记忆：[[MEM-20260929-169]]（取消副作用的锚点在删租约）。
