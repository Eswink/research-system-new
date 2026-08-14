# Ports Contract — v0.4.0

本文件是 Research OS 全部外部能力边界 Port 的集中式规格（M5 产物）。
Port 由 Research OS 拥有（inward-owned，`packages/application/ports/`）；
adapter 实现这些接口，不反向控制 Domain。Port 输入输出只使用
`packages.domain` 类型与本包 DTO，禁止 provider-specific 类型泄漏
（架构测试锁定：`tests/contracts/test_common_contract.py`）。

## 1. 统一语义

- 同步语义：全部 Port 方法为同步调用（M5 决策 D2）。
- 错误模型：Port 失败必须抛 `packages/application/ports/errors.py` 层次内异常
  （`TransientPortError` 可重试 / `PermanentPortError` 不可重试 /
  `PortTimeoutError`（瞬时）/ `InvalidInputError`（调用方 bug）/
  `PortCancelledError`（不得重试）），消息一律 redaction。
- Cancellation：协作式。`cancel()` 置会话/任务级信号，`run()`/推进在步骤边界
  检查并终止；取消不属于 FailureCategory，不按 transient 重试。
- Idempotency：请求携带操作键（idempotency key / entry_id / event_id /
  operation_key），重复键返回首次结果且不产生重复副作用。
- Retry：transient 可重试、permanent 不可；重试边界由调用方策略
  （`TaskContract.RetryPolicy` / tenacity）执行，Port 实现不自行重试。
- 生命周期：带 `close()` 的 Port 在 close 后所有调用抛 `PermanentPortError`。

## 2. Port Inventory 与职责

### AgentRuntime（`ports/agent_runtime.py`）

- 职责：AgentSession 生命周期 create/run/pause/cancel/stream_events/fork；
  输出归一化 runtime event 与终端结果；状态来自 domain `AgentSessionState`。
- 非职责：不编排 run/phase/task（WorkflowEngine）；不选模型（ModelGateway）；
  不记账（BudgetLedger）；runtime event 不替代 Domain Event（EventPublisher）。
- 不预设上游 Runtime 的 Conversation/Event 类型；上游状态由 adapter 显式映射。

### WorkflowEngine（`ports/workflow_engine.py`）

- 职责：任务分发（at-least-once + idempotency 去重）、lease 获取/心跳、
  取消传播、recover_expired_leases（过期 lease 收敛，返回恢复数量；
  orchestration 在 start_run 前懒触发，见 WORKFLOW_RELIABILITY.md §2）。
- 非职责：不执行 Agent 循环（AgentRuntime）；不持久化
  （M7 PostgreSQL task queue/outbox，见 BACKLOG.md M7）。
- 幂等语义：重复 submit（同 task.id 或同 idempotency_key）静默幂等——
  返回首次结果、不抛错、不覆盖首次契约（M5 复审修正）。

### ModelGateway（`ports/model_gateway.py`，收编原 ModelRelayGateway）

- 职责：OpenAI-compatible 网关最小调用面 complete/list_models/probe。
- 非职责：凭据解析（CredentialResolver）；预算记账（BudgetLedger）；
  模型选择/eligibility/fallback 编排（application use case）。

### ToolProvider（`ports/tool_provider.py`）

- 职责：按 ToolProviderSpec 执行 ToolCallRecord，返回归一化 ToolResultRecord
  （输出只存 digest，内容经 ArtifactStore 持久化）。
- 非职责：Skill/Capability 装配（P1 ToolResolver）；frozen tool set 约束由
  调用方执行；tool credential 独立信任域（ADR-0012）。

### WorkspaceBackend（`ports/workspace_backend.py`）

- 职责：工作区创建、Lease 获取/续期/释放、快照/恢复/合并；
  无 Lease 不得写入（ADR-0006）。
- 非职责：不执行命令（ExecutionBackend）。

### ExecutionBackend（`ports/execution_backend.py`）

- 职责：执行 ExecutionSpec，返回 ExecutionRun；timeout 产生
  ExecutionStatus.TIMED_OUT；compute usage 摘要返回。
- 非职责：不管理文件布局（WorkspaceBackend）；不记账
  （BudgetLedger 仅收 application 归账后的数字）。

### ArtifactStore（`ports/artifact_store.py`）

- 职责：内容寻址 put/get/verify/list/mark/archive/delete；digest 校验；
  状态流转 STAGED→VERIFIED/QUARANTINED→ACTIVE（合法迁移强制）；
  delete 为 tombstone（内容立即不可读，元数据保留 DELETED_TOMBSTONE；
  ACTIVE/ARCHIVED 均可直接删除，M5 复审修正）。
- 非职责：不承担 Evidence/Claim truth（DATA_LIFECYCLE.md 事实源划分：
  PostgreSQL 实体为真相，对象存储只保存内容）。

### EventPublisher（`ports/event_publisher.py`）

- 职责：publish(EventEnvelope)，event_id 幂等；Consumer 按 event_id 去重。
- 非职责：不做 Outbox 持久化（M7）；不做 telemetry；
  Domain Event ≠ runtime event ≠ telemetry（OBSERVABILITY.md）。

### PolicyEvaluator（`ports/policy_evaluator.py`）

- 职责：evaluate(Actor + Capability + Scope + Resource) →
  ALLOW / DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS；决策 deterministic；
  decision log 不记录 secret。
- MVP 实现：`NativePolicyEvaluator`（ADR-0018）；OPA 等生产实现（P2）同契约。

### CredentialResolver（`ports/credential_resolver.py`）

- 职责：resolve(ref) → SecretValue（repr 脱敏；永不向 Agent/日志/异常/
  telemetry 暴露明文）；未解析抛 `InvalidInputError`（统一错误模型，
  M5 P2 清偿：KeyError/ValueError 语义收敛，EndpointStore 的 not-found
  KeyError 不在此列）。
- 非职责：不持久化凭据；不判断使用 scope（调用方执行授权）。

### MemoryStore（`ports/memory_store.py`）

- 职责：commit(MemoryWriteProposal) 执行 provenance gate 后写入 MemoryRecord；
  读取/查询/删除；删除协调 derived index 重建。
- 非职责：不做记忆语义判断（curator/gate 策略由调用方提供）。

### BudgetLedger（`ports/budget_ledger.py`，收编原 BudgetReservationPort）

- 职责：reserve（预算预留，确定性引用）+ release（幂等释放预留，
  run 收敛到成功/失败/取消后归还配额，未知/已释放引用为 no-op）+
  record_usage（append-only，拒绝重复 entry_id）+ snapshot（只读视图）。
- 非职责：不做 usage 采集（ModelGateway / ExecutionBackend 上报原始用量，
  application 归账后入 ledger）；不伪造 cost（UNKNOWN 语义）。

### 收编 Port

- EndpointStore（`ports/endpoint_store.py`）：LLMEndpoint CRUD。
- ResourceCatalog（`ports/resource_catalog.py`）：preflight 只读目录 +
  PreflightContext DTO。

## 3. Fake 实现（`adapters/fakes/`）

- Fake 是 test-double adapter：与真实 adapter 遵守相同 Port Contract
  （tests/contracts 强制），不绕过签名/错误分类/幂等规则。
- deterministic（显式脚本驱动，无随机）；可错误注入（`set_script`）；
  可记录调用（CallRecord，不记录 secret 明文）；close 语义。
- call recording 覆盖成功与失败路径：业务校验失败（InvalidInputError
  等）同样记录 error 后抛出（M5 复审修正，契约测试锁定）。
- 错误注入统一走 `FakeBase.set_script` 脚本机制；Fake 特有的结果形态注入
  （如 `FakeModelGatewayOptions` 的失败快照/usage 开关）与故障注入语义分离
  （探测失败返回 ok=False 快照而非异常，M5 P2 清偿）。
- `FakeAgentRuntime.advance()` 为 test-only 中间态驱动器（非 Port 方法），
  沿 domain 状态机显式推进 INITIALIZING/WAITING_FOR_APPROVAL/PAUSED/STUCK，
  供 M6 adapter 中间态映射测试对照（M5 P2 清偿）。
- 不依赖网络、API Key、Docker、OpenHands 或外部服务
  （import-linter 契约 `.importlinter.fakes` 锁定）。
- 覆盖 14 个 Port 全集：12 个行为 Port + EndpointStore / ResourceCatalog
  收编 Port 均有 Fake 实现并注册进 contract registry（M5 复审补齐）。

## 4. Contract Suite（`tests/contracts/`）

- 注册表 `tests/contracts/registry.py` 是单一事实源；M6/M7 真实 adapter
  注册工厂后同一套 suite 自动复用。
- 通用矩阵（test_common_contract.py）：正常调用、invalid input、
  transient/permanent 失败注入、close 后不可用、call recording、
  deterministic replay、serialization boundary、secret 不进入记录、
  provider 类型不泄漏、14 Port 接口兼容矩阵。
- Port 特定（test_agent_runtime_contract.py、test_ports_semantics.py、
  test_ports_persistence.py、test_ports_regressions.py）：cancellation、
  at-least-once 幂等分发、终端状态为最终、event 幂等保留首次 payload、
  lease 过期/续期、artifact digest/状态流转/tombstone、event 顺序/去重、
  budget append-only、memory provenance gate、tool operation_key 幂等、
  policy 决策矩阵、timeout 分类、malformed provider result、
  ExecutionBackend domain invariant、错误路径 call recording、
  transient 重试恢复 / permanent 不重试（retry boundary）、
  FakeAgentRuntime 中间态驱动 / FakeModelGateway 失败快照注入
  （127 项，M5 复审 + P2 清偿扩充）。

## 5. 与 M5R / M6 / M7 的输出契约

- M5R：以本文件 + Port 签名 + contract suite 为反向验证 harness；
  只验证不改（除非真实 upstream 证据驱动修正，修正须在 M6 前）。
- M6：OpenHandsRuntimeAdapter 必须实现 AgentRuntime Port 并通过
  agent_runtime contract suite；UPSTREAM_COMPONENTS.yaml 中 openhands_sdk
  controls 逐项映射到 contract suite 检查项。
- M7：WorkflowEngine Port + Fake 语义冻结；PostgreSQL queue/lease/outbox
  实现以 contract suite 为验收。

## 6. M5 决策记录（M5R 可基于 upstream 证据复审）

- D1 WorkflowEngine 纳入 M5（CODEX_BOOTSTRAP/MILESTONES 为准；BACKLOG M7
  首项冲突已记录；持久化仍在 M7）。
- D2 全部 Port 同步语义；cancellation 协作式（AGENT_RUNTIME.md §1 的 async
  签名按契约资产规则同步修正为 sync）。
- D3 Port 权威位置 packages/application/ports/；ModelRelayGateway 更名
  ModelGateway；BudgetReservationPort 收编进 BudgetLedger。
- D4 Evaluator 不入 M5（无使用场景，P1 Evaluation）。
- D5 不新增 JSON schema（Port 规范以 Python 类型为权威）。
- D6 Fake 位置 adapters/fakes/（test-double adapter，同一依赖方向）。