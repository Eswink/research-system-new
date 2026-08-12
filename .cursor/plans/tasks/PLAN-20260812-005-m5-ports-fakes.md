---
id: PLAN-20260812-005
slug: m5-ports-fakes
title: M5 Ports + Fakes 实施
status: DONE
latest_recheck: .cursor/plans/rechecks/RECHECK-20260812-005-m5-ports-fakes.md
memory_entries:
  - .cursor/memory/entries/MEM-20260812-005-m5-ports-fakes-review.md
created_at: 2026-08-12
updated_at: 2026-08-12
cursor_plan_uri: "m5-ports-fakes"
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "M5 — Ports + Fakes（用户批准，planUri m5_ports_+_fakes_fe93a1c8）"
subagent_parallel_limit: 3
---

# PLAN-20260812-005 — M5 Ports + Fakes 实施

## 目标

为所有 Research OS 外部能力建立稳定、最小、provider-independent 的 Port
Contract（`packages/application/ports/`），并提供完全离线 CI 可用的
Fake Implementations（`adapters/fakes/`）与统一 Contract Suite
（`tests/contracts/`）。不重复实现前序阶段（M1-M4）已完成的领域逻辑；
不实现 OpenHandsRuntimeAdapter；不提前实现 M6/M7 内容。

## 验收条件

- [x] AC-01：12+2 Port Protocol（AgentRuntime / WorkflowEngine / ModelGateway /
  ToolProvider / WorkspaceBackend / ExecutionBackend / ArtifactStore /
  EventPublisher / PolicyEvaluator / CredentialResolver / MemoryStore /
  BudgetLedger + EndpointStore / ResourceCatalog）定义于
  `packages/application/ports/`，签名零 provider 类型泄漏（架构测试锁定）。
- [x] AC-02：`packages/domain` 零新增违规 import；domain 增量类型
  （ToolResultRecord / ExecutionRun / EventType / EventEnvelope）有
  invariant 测试。
- [x] AC-03：12 个 Fake 全部落地（deterministic / 错误注入 / call recording /
  close），不依赖网络、API Key、Docker、OpenHands、外部服务。
- [x] AC-04：contract suite 覆盖用户列出的 19 类测试语义（正常调用 /
  invalid input / timeout / transient / permanent / cancellation /
  duplicate-idempotent / retry boundary / malformed provider result /
  secret redaction / event ordering / resource cleanup / call recording /
  deterministic replay / serialization boundary / provider 类型泄漏 /
  Port 接口兼容性 等），全离线运行通过。
- [x] AC-05：preflight 经 PolicyEvaluator Port 注入
  （`PreflightContext.policy_evaluator`），无直接实例化。
- [x] AC-06：`docs/architecture/PORTS.md` + `docs/INDEX.md` 更新；
  AGENT_RUNTIME / DOMAIN_MODEL / EVENT_MODEL 与代码一致。
- [x] AC-07：全量回归——`run_all_checks.py --profile m0` 18/18 PASS；
  `validate_bundle.py` PASS；`validate.py` PASS；pytest 697 全绿；
  mypy 162 files；ruff clean；8 项架构边界测试（含新增 fakes 契约）。
- [x] AC-08：CHANGELOG / BACKLOG / ALL_PLAN 更新；M5R readiness 报告输出
  （含 D1-D6 决策记录）。

## 实施清单

- [x] STEP-01：ports 基座——errors.py + 收编迁移（ModelGateway /
  CredentialResolver / EndpointStore / ResourceCatalog / BudgetLedger）+
  全仓 import 更新回归。
- [x] STEP-02：domain 增量——ToolResultRecord / ExecutionRun /
  EventType / EventEnvelope + invariant 与序列化测试
  （tests/domain/test_m5_domain_increments.py 14 项）。
- [x] STEP-03：新 Port 定义——AgentRuntime / WorkflowEngine / ToolProvider /
  WorkspaceBackend / ExecutionBackend / ArtifactStore / EventPublisher /
  PolicyEvaluator / MemoryStore。
- [x] STEP-04：PolicyEvaluator 收编——NativePolicyEvaluator 声明实现 Port；
  preflight/policy_check.py 改为注入式。
- [x] STEP-05：adapters/fakes/ 基座（CallRecord / FakeBase）+ 12 个 Fake。
- [x] STEP-06：tests/contracts/ 注册表 + 通用矩阵 + Port 特定语义 +
  泄漏/序列化边界断言（94 项）。
- [x] STEP-07：边界加固——.importlinter.fakes 契约（禁厂商 SDK /
  adapters.relay / httpx）+ provider leakage 架构测试。
- [x] STEP-08：文档——PORTS.md / INDEX / AGENT_RUNTIME sync 修正 /
  CHANGELOG / BACKLOG。
- [x] STEP-09：全量回归 + validators + M5R readiness 报告。

## 关键决策记录（M5R 可基于 upstream 证据复审）

- D1：WorkflowEngine 纳入 M5（CODEX_BOOTSTRAP / MILESTONES 为准；
  BACKLOG M7 首项冲突已记录；PostgreSQL 持久化仍在 M7）。
- D2：全部 Port 同步语义；cancellation 协作式；AGENT_RUNTIME.md §1
  async 签名按契约资产规则同步修正为 sync。
- D3：Port 权威位置 packages/application/ports/；ModelRelayGateway 更名
  ModelGateway；BudgetReservationPort 收编进 BudgetLedger。
- D4：Evaluator 不入 M5（无使用场景，P1 Evaluation）。
- D5：不新增 JSON schema（Port 规范以 Python 类型为权威）。
- D6：Fake 位置 adapters/fakes/（test-double adapter，同一依赖方向）。

## 证据

- EV-01：`packages/application/ports/` 14 个 Port + errors.py；
  `tests/contracts/test_common_contract.py::test_interface_compatibility`
  对注册表内全部实现断言 runtime_checkable Protocol。
- EV-02：`tests/domain/test_m5_domain_increments.py` 14 项通过；
  import-linter `.importlinter.domain` 0 broken。
- EV-03：`adapters/fakes/` 12 个 Fake + base；`.importlinter.fakes` 契约
  0 broken（test_relay_boundaries.py::test_fakes_have_no_provider_or_relay_dependency）。
- EV-04：`tests/contracts/` 94 项通过（registry 驱动，M6/M7 真实 adapter
  注册后自动复用）。
- EV-05：preflight/policy_check.py 经 context.policy_evaluator 注入；
  NativePolicyEvaluator 实现 PolicyEvaluator Port（结构性匹配，mypy strict
  下 protocol 兼容）。
- EV-06：`docs/architecture/PORTS.md`、`docs/INDEX.md`、
  `AGENT_RUNTIME.md` §1 sync 修正、`CHANGELOG.md` v0.4.0（2026-08-12 M5
  条目）、`BACKLOG.md` M5 全勾。
- EV-07：`run_all_checks.py --profile m0` 18/18 PASS；
  `validate_bundle.py` PASS；`validate.py` PASS；pytest 697 passed；
  mypy 162 source files Success；ruff check + format clean；
  pytest tests/architecture/python 8 passed。

## 状态历史

- 2026-08-12：APPROVED（用户确认 M5 计划，planUri m5_ports_+_fakes_fe93a1c8）。
- 2026-08-12：IN_PROGRESS→VERIFYING（9 个实施步骤完成，DoD 证据齐备；
  DONE 需独立 recheck 通过——实现者自报不是通过证据；计划文件已按
  governance validator 的 VERIFYING 语义登记）。
- 2026-08-12：独立复审 PASS（用户发起 M5 端到端复审）。发现并修复：
  P0 FakeExecutionBackend 成功路径违反 domain invariant（SUCCEEDED 缺
  completed_at）；P1 AgentRuntime 终端状态被二次 run 覆盖（事件流重复）；
  P1 EventPublisher 幂等覆盖首次 payload；P1 WorkflowEngine submit 抛错
  而非幂等（含 idempotency_key 映射 bug）；P1 ArtifactStore delete 无法
  从 ACTIVE 删除且 tombstone 后内容仍可读；Fake 业务失败路径不记录调用
  （CallRecord 契约缺口，10 个 Fake 修正）；EndpointStore/ResourceCatalog
  补齐 Fake 与 contract 覆盖（14 Port 全集）；清理 dead code 2 处。
  Contract suite 94→121 项；pytest 727 passed；m0 profile 18/18 PASS；
  双 validator PASS。VERIFYING→DONE。

## 影响报告

- 改动：packages/application/ports/（新增 14 个 Port + 统一错误模型）；
  packages/domain（3 类新类型）；adapters/fakes/（12 个 Fake）；
  tests/contracts/（94 项）；preflight policy 注入式改造；
  .importlinter.fakes 新契约；文档（PORTS.md / INDEX / AGENT_RUNTIME /
  CHANGELOG / BACKLOG）。
- lint/typecheck/test：ruff clean；mypy 162 files Success；pytest 697 passed；
  m0 profile 18/18 PASS；双 validator PASS。
- Domain/API/schema 变化：ToolResultRecord / ExecutionRun（ExecutionStatus
  含 TIMED_OUT）/ EventType / EventEnvelope；无 schema 变更（决策 D5）；
  ModelRelayGateway 更名 ModelGateway（全仓 import 已迁移，旧模块导出更新）。
- 安全/凭据变化：CredentialResolver 密封语义保持；Fake call record 与
  PortError 消息 redaction 测试锁定；无新凭据暴露面。
- 兼容性/迁移风险：Port 权威位置迁移为纯 import 更新（pytest 回归全绿）；
  AGENT_RUNTIME.md §1 async→sync 属契约资产同步修正（决策 D2，M5R 复审点）。
- 上游版本影响：无新增第三方依赖；openhands_sdk 仍 PLANNED（M6 采用时以
  contract suite 验收）。
- 下一项任务：独立 recheck（RECHECK-20260812-005）从原始验收条件复核
  M5 DoD；通过后计划置 DONE 并输出 M5R readiness；M5R 只验证不改
  （除非真实 upstream 证据驱动修正，修正须在 M6 前）。