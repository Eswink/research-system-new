---
id: PLAN-20260929-249
slug: goal-026-ec03-breaker-dead-letter-cancel
title: GOAL-026 cycle 3（EC-03）：断路器三态与半开探针预算 / 死信面 / 取消语义 —— 两向按压 + 一处只收紧的真缺陷修复
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-026
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-026 的 **EC-03**（§7 义务「circuit breaker」「dead-letter / manual recovery」
    「cancellation semantics」的对抗性自检）。授权沿用该 GOAL 的 `authorization.ref`：
    范围 = 「**新增判据**（一律落 `tests/**`；落在既有 `python/tests` 收集面内 ⇒ m0 条数仍 `23`）」+
    「**测试侧夹具 / 探针**」+「修**被新判据证明为真缺陷**的问题（**只允许收紧**）」+
    「文档同源更新」；push-to-main-for-CI 口径（**只推 main**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**判据文件，**不修改**任何既有判据 / 夹具 / 门禁 / 阈值 / 放行面
    （点名：`tests/adapters/relay/test_gateway_circuit.py`、`tests/domain/test_circuit_breaker.py`、
    `tests/adapters/sqlite/test_workflow_engine.py`、`test_workflow_cancel_run.py`、
    `tests/application/tool_plane/**`、`tests/egress_guard.py`）；
    **产品侧只在「只收紧」修复时才动**，且**必须**先有判据证明 —— 本轮**触发了**该分支（见 AC-2，
    唯一一处产品净改动）；**不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构；**零**新依赖；
    **全离线**（无真实出网）；测试数据一律**合成值**；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**宣称 exactly-once。
exit_criteria:
  - id: AC-1
    criterion: >-
      **三态各有结构化断言 + 快速失败不触达下游**：`CLOSED` 放行（下游计数 `== 1`）、
      `OPEN` 拒绝且计数 `== 0`、`HALF_OPEN` 放行**一个**探针且成功转 `CLOSED`；
      另加**阈值驱动**例（真实失败达阈值 ⇒ `is_open`，此后不再触达下游）。
      断言绑状态串 / `is_open` / 调用计数 / 异常类型，**不匹配错误文本**。
    status: PASS
  - id: AC-2
    criterion: >-
      **半开探针预算耗尽 ⇒ 拒绝（fail-closed）**：声明语义要求拒绝；实测原行为**放行**
      （吞掉迁移异常 ⇒ 停在 `HALF_OPEN` ⇒ `is_open` 为假）⇒ 按授权**只收紧**修复接线处
      （`adapters/relay/gateway.py::_consult_circuit`），修复后判据绿且下游零调用。
    status: PASS
  - id: AC-3
    criterion: >-
      **死信可枚举 + 重放幂等 + 无出边**：`list_tasks` 可见 `DEAD_LETTER` 行（`attempt` 打满）且
      `claim_next` 为 `None`；重复提交同一完成 ⇒ outbox 计数不变；枚举
      `vars(ResearchTaskState.Transition)`（**普通类**，非 `Enum`）逐条构造并全部
      `InvalidTransitionError`，附**枚举下界**断言（受判集非空）。
    status: PASS
  - id: AC-4
    criterion: >-
      **取消幂等 + 释放租约 + 终止 + 取消后零新副作用**：重复取消 ⇒ 结构化 `deduped`、
      状态仍 `CANCELLED`、`claim_next` 为 `None`、**outbox 计数不变**（在第二次取消**之前**取值）；
      取消后的**陈旧完成** ⇒ `InvalidInputError` 且 outbox 零新增；`CANCELLED` ∈ `terminal()`。
    status: PASS
  - id: AC-5
    criterion: >-
      **工具面断路器边界**：`OPEN` 是**吸收态**（healthy 探测也抛 `CircuitBreakerTransitionError`）；
      对 `PRODUCT_ROOTS` 源码枚举断言断言符号**只**出现在 `packages/application/tool_plane/` 内，
      且扫描面**下界** `>= _MIN_SCANNED (=400)` 成立。
    status: PASS
  - id: AC-6
    criterion: >-
      **按压两向 + 逐字节复原（承 MEM-152 / MEM-159）**：① 断路器阈值调成不可能达到 ⇒ 判红
      （`5 failed`，本判据在列）；② 取消不再释放租约 ⇒ 判红（`1 failed`，
      `Failed: DID NOT RAISE InvalidInputError`，另附副作用取证：状态转 `SUCCEEDED`、outbox `2 → 3`）；
      两次复原后 raw `sha256` 均回到基线；留档二进制写盘（`CR` 计数 0）。
    status: PASS
  - id: AC-7
    criterion: >-
      **四道门 + 定向套件 + 既有判据未改**：`ruff format --check` / `ruff check` / `mypy` /
      规模门（1067 passed）全绿；定向套件（relay + sqlite + application + domain + 规模门）
      = `2501 passed, 1 skipped`；既有判据**逐字节未改**；新判据**无 skip / xfail**。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-250-goal-026-ec03-breaker-dead-letter-cancel.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-169-cancel-side-effect-suppression-anchors-on-lease-deletion.md
  - .cursor/memory/entries/MEM-20260929-170-swallowed-transition-error-is-fail-open.md
---

# GOAL-026 cycle 3（EC-03）：断路器 / 死信 / 取消

## 目标

把 §7 的三项义务 —— 「**circuit breaker**」「**dead-letter / manual recovery**」
「**cancellation semantics**」—— 从「**代码里有**」推进到「**有判据证明它真的成立**」，
并对**被新判据证明为真缺陷**的问题按授权**只收紧**修复。建档/探查发现的既有覆盖缺口：

1. 既有 `tests/adapters/relay/test_gateway_circuit.py` 覆盖了阈值 / 快速失败 / 半开恢复，
   但**没有**「半开名额耗尽」这一态 —— 而声明语义（`half_open_max_probes` + 接线处注释）
   明确要求该态**拒绝**；
2. 死信在既有判据里只作为「重试预算耗尽的状态」出现，**没有人**证「它可枚举（有东西可处置）」、
   「重放幂等」、「它没有出边（不是伪终态）」；
3. 既有取消判据只证「第二次取消是 `deduped`」，**没有人**证「取消后**不再产生副作用**」
   （陈旧完成是否被接受、outbox 是否新增）；
4. 工具面断路器（`packages/application/tool_plane/health.py`）的**产品装配面**从未被扫过。

## 验收条件

- [x] **AC-1 三态结构化断言 + 快速失败不触达下游 + 阈值驱动**。
- [x] **AC-2 半开探针预算耗尽 ⇒ fail-closed**（真缺陷已证并按授权只收紧修复）。
- [x] **AC-3 死信可枚举 + 重放幂等 + 无出边**（含枚举下界）。
- [x] **AC-4 取消幂等 + 释放租约 + 终止 + 取消后零新副作用**。
- [x] **AC-5 工具面断路器边界**（开态吸收 + 产品装配面扫描 + 扫描面下界）。
- [x] **AC-6 按压两向 + 逐字节复原**（阈值不可达 / 取消不释放租约）。
- [x] **AC-7 四道门 + 定向套件 + 既有判据未改**。

## 实施清单

- [x] **WP-1**：新增 `tests/adapters/relay/test_gateway_half_open_budget.py`（5 例：AC-1 / AC-2）。
- [x] **WP-2**：新增 `tests/adapters/sqlite/test_workflow_dead_letter_surface.py`（3 例：AC-3）。
- [x] **WP-3**：新增 `tests/adapters/sqlite/test_workflow_cancel_semantics.py`（3 例：AC-4）。
- [x] **WP-4**：新增 `tests/application/test_tool_plane_breaker_boundary.py`（2 例：AC-5）。
- [x] **WP-5**：产品侧**只收紧**修复 `adapters/relay/gateway.py::_consult_circuit`
      （半开名额耗尽 ⇒ `CircuitOpenRelayError`，不再吞异常）；docstring 写明判据出处。
- [x] **WP-6**：按压 P1（阈值不可达）/ P2（取消不释放租约）⇒ 判红；raw `sha256` 逐字节复原 ⇒ 复绿；
      留档二进制写盘（`scratch/goal026-ec03-press-matrix.log` +
      按压态取证探针 `scratch/goal026_ec03_pressb_probe.py`）。
- [x] **WP-7**：四道门 + 定向套件 + 规模自查；写 `RECHECK-20260929-250` + `MEM-20260929-169` /
      `MEM-20260929-170`；回写 GOAL-026 的 EC-03 状态与迭代日志；投影 `ALL_PLAN`。

## 证据

- **实跑**：`uv run --frozen --no-sync python -B -m pytest
  tests/adapters/relay/test_gateway_half_open_budget.py
  tests/adapters/sqlite/test_workflow_dead_letter_surface.py
  tests/adapters/sqlite/test_workflow_cancel_semantics.py
  tests/application/test_tool_plane_breaker_boundary.py -q` ⇒ **13 passed**；
  加上既有断路器判据（`test_gateway_circuit.py` + `tests/domain/test_circuit_breaker.py`）
  ⇒ **29 passed**；定向套件 ⇒ **2501 passed, 1 skipped**。
- **真缺陷（修复前 / 修复后）**：判据红形态 `Failed: DID NOT RAISE CircuitOpenRelayError`
  （半开名额耗尽时请求被**放行**）⇒ 修复为 fail-closed ⇒ 复绿。
- **按压矩阵**（`scratch/goal026-ec03-press-matrix.log`，二进制写盘 / `CR` 计数 0 / 3481 字节）：
  **P1** 阈值 → 不可达 ⇒ `5 failed, 5 passed`，本判据失败行为
  `assert False = CircuitBreakerState(state='CLOSED', consecutive_failures=1, opened_at=None,
  probes_in_half_open=0).is_open`；**P2** 取消不删租约 ⇒ `1 failed, 2 passed`，
  `Failed: DID NOT RAISE InvalidInputError`，探针实测
  `status_after_stale_completion = SUCCEEDED` / `outbox 2 → 3`。
  两次复原后 raw `sha256` 分别回到
  `e392139eb4da01869ad168fd6f32ce9a48e053b3ac2fc09bc12aa9e4f1a9e04e`（`circuit_breaker.py`）与
  `a9d132c525a30bf3a70432a9876429d4e429a67442acde29c296258e28929982`（`cancel_run.py`）
  == 按压前基线。
- **结构性事实**：抑制「取消后副作用」的锚点是 `cancel_task` 里的 `DELETE FROM leases`，
  **不是**完成路径里的 `cancelled` 标志（完成路径里没有这个检查）⇒ 沉淀 `MEM-169`。
- **四道门**：`ruff format --check` = `5 files already formatted`；`ruff check` =
  `All checks passed!`；`mypy` = `Success: no issues found in 5 source files`；
  规模门 = **1067 passed**。
- **首轮被抓到的本人错误**（如实记录，非产品缺陷）：`ruff` 2 处（导入排序 / 未用导入）、
  `mypy` 4 处（`EndpointHealth` 与 `InvalidTransitionError` 的**真实**归属模块、两处 `-> object`
  应为 `TaskLease`）、以及我第一版取消判据把副作用计数取在第二次 `cancel()` **之后**
  ⇒ 断言恒真（**假绿**）已改到**之前**取值。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | DONE | 四个新判据文件（13 例）落地；AC-1…AC-7 全部 PASS；`RECHECK-20260929-250` = `PASS_WITH_WARNINGS`（`W-1`…`W-6`）；沉淀 `MEM-20260929-169` / `MEM-20260929-170`。**产品净改动 1 处**（`adapters/relay/gateway.py`，只收紧）。 |

## 影响报告

- **改动**：新增四个判据文件（13 例）；**产品侧 1 处只收紧修复**（半开名额耗尽 ⇒ fail-closed）；
  记录面（PLAN / RECHECK / MEM / GOAL / ALL_PLAN / INDEX）。
- **lint / typecheck / test**：四道门全绿；定向套件 `2501 passed, 1 skipped`。
- **Domain / API / schema 变化**：**无**（`CircuitOpenRelayError` 的类别沿用
  `FailureCategory.MODEL_RELAY_UNAVAILABLE`，未新增类别 / 字段 / 路由）。
- **安全 / 凭据变化**：**无**（合成值；零真实内容 / token；该修复方向本身是**更严**的拒绝语义）。
- **兼容性 / 迁移风险**：**有且已知**：配置了断路器的端点在「半开且名额耗尽」时由**放行**变**拒绝**
  （见 `RECHECK-250` 的 `W-1`）；若将来要恢复放行，必须**同时**改判据与声明。
- **上游版本影响**：**无**（零新依赖）。
- **未覆盖范围与残余**：死信**人工恢复动作**无产品路径（`R26-1`）、取消是协作式且无在飞信号
  （`R26-3`）、应用层事件消费者不存在（`R26-5`，留 EC-04）、工具面边界判据是源码扫描 + 下界
  （`W-5`）、PG 侧未新增判据（`W-6`）、`R-M1` 未收口。
- **下一项任务**：GOAL-026 EC-04（补偿 + outbox 原子性 + exactly-once 否认）。
