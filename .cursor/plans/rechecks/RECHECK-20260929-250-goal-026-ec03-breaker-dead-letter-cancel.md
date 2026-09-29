---
id: RECHECK-20260929-250
slug: goal-026-ec03-breaker-dead-letter-cancel
title: GOAL-026 EC-03 复检：断路器三态与半开探针预算（含一处**产品真缺陷已修**）+ 死信面 + 取消语义（含两向按压与逐字节复原）
plan_id: PLAN-20260929-249
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-250 — GOAL-026 EC-03 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`）。
**未实跑的不记通过**。

## 检查结果

### 1. 半开探针预算：**一处真缺陷被新判据证明，并按「只收紧」修复**

- 声明语义：`CircuitBreakerConfig.half_open_max_probes` 与 `OpenAIChatGateway._consult_circuit`
  自己的注释都要求「**名额耗尽的再次 consult ⇒ 拒绝**」。
- 实测前行为：`apply_tick` 在半开名额耗尽时抛 `CircuitBreakerTransitionError`，而接线处
  **吞掉了它**（`pass`）⇒ 状态停在 `HALF_OPEN` ⇒ `state.is_open` 为**假** ⇒ **请求被放行**
  ⇒ 探针上限形同虚设（半开期可无限并发打下游）。
- 判据红形态（修复前，原样）：`Failed: DID NOT RAISE CircuitOpenRelayError`。
- 修复（`adapters/relay/gateway.py::_consult_circuit`，**唯一一处产品净改动**）：
  改为 fail-closed —— `raise CircuitOpenRelayError(FailureCategory.MODEL_RELAY_UNAVAILABLE,
  "circuit half-open probe budget exhausted: request denied") from None`，并把判据与
  GOAL-026 EC-03 写进 docstring。
- 修复后：`tests/adapters/relay/test_gateway_half_open_budget.py` +
  `test_gateway_circuit.py` + `tests/domain/test_circuit_breaker.py` ⇒ **29 passed**。

### 2. 三态结构化断言 + 阈值驱动 + 预算耗尽（实测）

- 交付：`tests/adapters/relay/test_gateway_half_open_budget.py`（**5 例**）。
- `CLOSED` **放行**（下游调用计数 `== 1`）；`OPEN`（冷却未到）**拒绝且不触达下游**
  （`CircuitOpenRelayError` + 计数 `== 0` + `is_open`）；`HALF_OPEN`（名额未用）**放行一个探针**
  且成功后状态串转 `CLOSED`；**阈值驱动**：真实 500 达阈值 ⇒ `is_open`，此后调用**不再触达下游**；
  **名额耗尽** ⇒ 拒绝且计数 `== 0`。
- 断言全部绑**结构化面**（状态串 / `is_open` / 下游调用计数 / 异常类型），**不匹配错误文本**。
- **与既有判据的分工**：`tests/adapters/relay/test_gateway_circuit.py` 已覆盖阈值路径（故阈值驱动例
  与本判据**有意重叠** —— EC-03 的按压要求「阈值不可达 ⇒ 本轮的判据判红」，受判集内必须有阈值驱动例）；
  本文件补的是**它没有的**「名额耗尽」这一态。

### 3. 死信面：可枚举 / 重放幂等 / 无出边（实测）

- 交付：`tests/adapters/sqlite/test_workflow_dead_letter_surface.py`（**3 例**）。
- 死信**可枚举**：`list_tasks` 里该行 `status == DEAD_LETTER`、`attempt == 2`（打满
  `max_attempts`）、且 `claim_next` 为 `None`（不可再 claim）。
- 重放**幂等**：对同一死信再交一次完成 ⇒ `pending_outbox()` 计数**不变**。
- **无出边**：枚举 `vars(ResearchTaskState.Transition)`（它是**普通类**、不是 `Enum` —— 见 §5），
  过滤下划线名与非字符串值后逐条构造，全部抛 `InvalidTransitionError`；并且断言枚举下界（`>= 8`）
  ⇒ 「受判集非空」不是空话。
- 读法：「可枚举」与「无出边」是**两件事**：前者证恢复面有东西可处置，后者证死信不是伪终态。

### 4. 取消语义：幂等 + 释放 + 终止 + 取消后零新副作用（实测）

- 交付：`tests/adapters/sqlite/test_workflow_cancel_semantics.py`（**3 例**）。
- 重复取消 ⇒ 结构化结论 `deduped`、状态仍 `CANCELLED`、`claim_next` 为 `None`、
  **outbox 计数不变**（副作用计数，而非只看文案）。
- **取消后的陈旧完成** ⇒ `InvalidInputError`，且 outbox **零新增**。
- `CANCELLED` 与 `DEAD_LETTER` 同族：都在 `ResearchTaskState.terminal()`。
- **结构性机制（本轮实测出来的事实）**：抑制「取消后副作用」的锚点**不是**完成路径里的
  `cancelled` 标志位 —— 完成路径里**根本没有**这个检查（全仓仅 claim 候选过滤用
  `cancelled = 0`）；锚点是 `cancel_task` 里的 `DELETE FROM leases`（旧租约失效 ⇒
  `_require_current_lease` 拒绝）。按压 B 正是抽掉这条锚点，判据随即判红（见 §6）。

### 5. 工具面断路器边界：开态吸收 + 产品装配面扫描（实测）

- 交付：`tests/application/test_tool_plane_breaker_boundary.py`（**2 例**）。
- `OPEN` 是**吸收态**：`record_probe`（healthy）也抛 `CircuitBreakerTransitionError`
  ⇒ 工具面断路器不会被一次「探测成功」悄悄闭合。
- **产品装配面**：对 `PRODUCT_ROOTS = ("packages", "adapters", "services", "apps")` 做
  `os.walk(followlinks=False)` 源码枚举，断言「断言符号」只在
  `packages/application/tool_plane/` 内出现（`_SYMBOLS` 见文件），并且**扫描面下界**
  `len(sources) >= _MIN_SCANNED (=400)` ——受判面成立性由该下界承担。
- 读法：这是**源码级**判据（扫描 + 下界），**不是**类型级证明（见 `W-5`）。

### 6. 两向按压 + 逐字节复原（实测）

**按压矩阵**（留档 `scratch/goal026-ec03-press-matrix.log`，二进制写盘 / `CR` 计数 0 / 3481 字节）：

| 按压 | 位置（**产品代码**） | 按压态 `sha256` | 实测红（原样） | 复原 |
| --- | --- | --- | --- | --- |
| **P1** 断路器阈值调成不可能达到 | `packages/domain/circuit_breaker.py::apply_failure` 的 `CLOSED` 分支（`if failures >= config.failure_threshold:` → `+ 1000000000`） | `74bcc0705b32e1be…` | `5 failed, 5 passed`；本判据：`assert False = CircuitBreakerState(state='CLOSED', consecutive_failures=1, opened_at=None, probes_in_half_open=0).is_open` | raw `sha256` 回到 `e392139eb4da0186…`（== 基线）⇒ `10 passed` |
| **P2** 取消后仍产生副作用 | `adapters/sqlite/cancel_run.py::cancel_task`（删掉 `DELETE FROM leases`） | `1c6ea53275cc98b0…` | `1 failed, 2 passed`；`Failed: DID NOT RAISE InvalidInputError` | raw `sha256` 回到 `a9d132c525a30bf3…`（== 基线）⇒ `13 passed` |

- **按压 B 的副作用取证**（按压态下跑 `scratch/goal026_ec03_pressb_probe.py`，公开 API）：
  `status_after_stale_completion = SUCCEEDED`（取消后被改回 `SUCCEEDED`）、
  `outbox_events_before = 2 after = 3`、`statuses_seen = ['SUCCEEDED']`
  ⇒ 「取消后仍产生副作用」是**实测**形态，不是推断。
- **两向**：两次按压中各只有**目标**用例红（`P1` 另有 4 条**既有**断路器判据同时红 —— 它们压的是同一条
  产品路径；`P2` 恰好只有 1 条红，另 2 条保持绿）⇒ 「不该红时不红」。
- **复原逐字节**：两次都以 raw `sha256` 复核回到基线；`git status --short` 中两个按压文件**均已消失**
  （只剩与本 GOAL 无关的既有 WIP 文件）⇒ 产品树净。
- **既有判据逐字节未改**；新判据**无 skip / xfail**。

### 7. 四道门（含首轮被抓到的本人错误，如实记录）

- `ruff format --check`（5 文件：4 新 + `adapters/relay/gateway.py`）= `5 files already formatted`；
- `ruff check` = `All checks passed!`；
- `mypy` = `Success: no issues found in 5 source files`；
- 规模门（`tests/tooling/test_python_source_limits.py`）= **1067 passed**；
- 定向套件（`tests/adapters/relay` + `tests/adapters/sqlite` + `tests/application` + `tests/domain`
  + 规模门）= **2501 passed, 1 skipped**。
- **首轮本人写错被抓（不是产品缺陷，如实登记）**：① `ruff` 报 2 处（`packages.application` 未排在
  `packages.domain` 前、`json_response` 未使用）；② `mypy` 报 4 处 —— `EndpointHealth` 实际在
  `packages.domain.enums`（从 `packages.domain.models` 导入是**隐式再导出**的错用）、
  `InvalidTransitionError` 实际在 `packages.domain.state_base`、两处 `-> object` 应为
  `TaskLease`；③ 我第一版取消判据把副作用计数写在第二次 `cancel()` **之后** ⇒ 断言恒真（**假绿**），
  已改成在**之前**取值。三处都按门/规格修正，**未**放宽任何断言。

## 结论

**EC-03 = PASS_WITH_WARNINGS**（`PLAN-20260929-249` 的 AC-1…AC-7 全部成立且有实跑证据）。
§7 三项义务在**单节点 SQLite + 注入时钟 + Fake 传输**的射程内**成立**：
「**circuit breaker**」（三态结构化 + 阈值驱动 + 开态吸收 + 半开名额耗尽的 fail-closed 拒绝）、
「**dead-letter / manual recovery**」（可枚举 + 重放幂等 + 无出边；**恢复动作**未取证，见 `W-2`）、
「**cancellation semantics**」（幂等 + 释放租约 + 终止 + 取消后零新副作用）。
本轮的**唯一产品净改动**是一处**只收紧**的 fail-closed 修复（半开探针预算耗尽 ⇒ 拒绝）。

**如实登记的警告（`W-1`…`W-6`）**：

- `W-1` 该修复是**可观察行为变更**：配置了断路器的端点在「半开且名额耗尽」时，请求由**放行**改为
  **拒绝**。这是 GOAL-026 授权的「只收紧」分支，但它确实改变行为 ⇒ 后续若要恢复放行语义，
  必须同时改判据与声明，不得只改代码。
- `W-2` 死信的**人工恢复动作**没有产品路径可点（无「重新投递 / 手工改派」入口）⇒ 本轮的
  「manual recovery」只证到**可枚举、可处置的终态**，**恢复动作本身未取证**（登记为 `R26-1`）。
- `W-3` 取消是**协作式**：没有向在飞工作发信号的通道（无取消令牌 / 无中断点）⇒
  「取消后不再产生副作用」只在**陈旧完成被拒**这一形态上被证（登记为 `R26-3`）。
- `W-4` **应用层事件消费者**不存在 ⇒ outbox 的「送达后被消费」边界留到 EC-04 处理，本轮不出结论。
- `W-5` 工具面边界判据是**源码扫描 + 扫描面下界**（受判面 = 4 个产品根下的 `.py`），
  能证明「没有别的产品代码碰这些符号」，但**不是**类型级 / 运行时证明。
- `W-6` 确定性判据仍全部落在 **SQLite**；PG 侧未新增判据（承 EC-02 的 `W-1` / `W-2`）。
- `R-M1` 未收口（Mimosa 钩子 `scanner_enobufs` 未得完整结论）⇒ **不得**据此宣称项目安全。

**未覆盖范围（承 GOAL-026）**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
`R-M1` 未收口。
