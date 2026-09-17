# Ports Contract — v0.4.0

本文件是 Research OS 全部外部能力边界 Port 的集中式规格。基线为 M5
产物（14 Port：12 行为 Port + EndpointStore/ResourceCatalog 收编）；
M8 增补 `ToolPackStore`，M10 增补 `EvidenceLedger` / `RetrievalIndex`，
当前共 **17 个 Port 模块**（`packages/application/ports/`，contract
registry 同步）。Port 由 Research OS 拥有（inward-owned）；adapter
实现这些接口，不反向控制 Domain。Port 输入输出只使用 `packages.domain`
类型与本包 DTO，禁止 provider-specific 类型泄漏（架构测试锁定：
`tests/contracts/test_common_contract.py`）。

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

### AgentRuntime（`packages/application/ports/agent_runtime.py`）

- 职责：AgentSession 生命周期 create/run/pause/cancel/stream_events/fork；
  输出归一化 runtime event 与终端结果；状态来自 domain `AgentSessionState`。
- 非职责：不编排 run/phase/task（WorkflowEngine）；不选模型（ModelGateway）；
  不记账（BudgetLedger）；runtime event 不替代 Domain Event（EventPublisher）。
- 不预设上游 Runtime 的 Conversation/Event 类型；上游状态由 adapter 显式映射。

### WorkflowEngine（`packages/application/ports/workflow_engine.py`）

- 职责：任务分发（at-least-once + idempotency 去重）、lease 获取/心跳、
  取消传播、recover_expired_leases（过期 lease 收敛，返回恢复数量；
  orchestration 在 start_run 前懒触发，见 WORKFLOW_RELIABILITY.md §2）。
- 非职责：不执行 Agent 循环（AgentRuntime）；不持久化
  （M7 PostgreSQL task queue/outbox，见 BACKLOG.md M7）。
- 幂等语义：重复 submit（同 task.id 或同 idempotency_key）静默幂等——
  返回首次结果、不抛错、不覆盖首次契约（M5 复审修正）。

### ModelGateway（`packages/application/ports/model_gateway.py`，收编原 ModelRelayGateway）

- 职责：OpenAI-compatible 网关最小调用面 complete/list_models/probe。
- 非职责：凭据解析（CredentialResolver）；预算记账（BudgetLedger）；
  模型选择/eligibility/fallback 编排（application use case）。

### ToolProvider（`packages/application/ports/tool_provider.py`）

- 职责：按 ToolProviderSpec 执行 ToolCallRecord，返回归一化 ToolResultRecord
  （输出只存 digest，内容经 ArtifactStore 持久化）。
- 非职责：Skill/Capability 装配（P1 ToolResolver）；frozen tool set 约束由
  调用方执行；tool credential 独立信任域（ADR-0012）。

### WorkspaceBackend（`packages/application/ports/workspace_backend.py`）

- 职责：工作区创建、Lease 获取/续期/释放、快照/恢复/合并；
  无 Lease 不得写入（ADR-0006）。
- 非职责：不执行命令（ExecutionBackend）。

### ToolPackStore（`packages/application/ports/tool_pack_store.py`，M8 增补）

- 职责：ToolPack manifest 生命周期（install/update/revoke/查询），
  供应链 pin（digest）校验与 tool credential 域门禁（安装时强制
  TOOL 域，M8 独立复审 F-06 收敛）；large result artifact indirection
  的存储面。
- 非职责：不执行 ToolCallRecord（ToolProvider）；不做 Skill/Capability
  路由（Skill Registry use case）。

### ExecutionBackend（`packages/application/ports/execution_backend.py`）

- 职责：执行 ExecutionSpec，返回 ExecutionRun；timeout 产生
  ExecutionStatus.TIMED_OUT；compute usage 摘要返回。
- 非职责：不管理文件布局（WorkspaceBackend）；不记账
  （BudgetLedger 仅收 application 归账后的数字）。
- M9 扩展（向后兼容可选字段）：ExecutionSpec 增加 `workspace_path`
  （容器 bind-mount 宿主路径）、`environment`（env 白名单映射，由
  application use case 构造）、`workdir`（容器内工作目录，默认
  `/workspace`）；ExecutionRun.compute_usage_summary 增加
  `image_digest`/`oom_killed`/`elapsed_seconds`（真实容器实现
  `adapters/execution/` 上报，供 ReproducibilityAudit 绑定）。

### ArtifactStore（`packages/application/ports/artifact_store.py`）

- 职责：内容寻址 put/get/verify/list/mark/archive/delete；digest 校验；
  状态流转 STAGED→VERIFIED/QUARANTINED→ACTIVE（合法迁移强制）；
  delete 为 tombstone（内容立即不可读，元数据保留 DELETED_TOMBSTONE；
  ACTIVE/ARCHIVED 均可直接删除，M5 复审修正；M9 扩展：
  QUARANTINED 可删除以支持 retention 清理）。
- 非职责：不承担 Evidence/Claim truth（DATA_LIFECYCLE.md 事实源划分：
  PostgreSQL 实体为真相，对象存储只保存内容）。

### EventPublisher（`packages/application/ports/event_publisher.py`）

- 职责：publish(EventEnvelope)，event_id 幂等；Consumer 按 event_id 去重。
- 非职责：不做 Outbox 持久化（M7）；不做 telemetry；
  Domain Event ≠ runtime event ≠ telemetry（OBSERVABILITY.md）。

### PolicyEvaluator（`packages/application/ports/policy_evaluator.py`）

- 职责：evaluate(Actor + Capability + Scope + Resource) →
  ALLOW / DENY / REQUIRE_APPROVAL / ALLOW_WITH_CONSTRAINTS；决策 deterministic；
  decision log 不记录 secret。
- MVP 实现：`NativePolicyEvaluator`（ADR-0018）；OPA 等生产实现（P2）同契约。

### CredentialResolver（`packages/application/ports/credential_resolver.py`）

- 职责：resolve(ref) → SecretValue（repr 脱敏；永不向 Agent/日志/异常/
  telemetry 暴露明文）；未解析抛 `InvalidInputError`（统一错误模型，
  M5 P2 清偿：KeyError/ValueError 语义收敛，EndpointStore 的 not-found
  KeyError 不在此列）。
- 非职责：不持久化凭据；不判断使用 scope（调用方执行授权）。

### MemoryStore（`packages/application/ports/memory_store.py`）

- 职责：commit(MemoryWriteProposal) 执行 provenance gate 后写入 MemoryRecord；
  读取/查询/删除；删除协调 derived index 重建。
- 非职责：不做记忆语义判断（curator/gate 策略由调用方提供）。

### BudgetLedger（`packages/application/ports/budget_ledger.py`，收编原 BudgetReservationPort）

- 职责：reserve（预算预留，确定性引用）+ release（幂等释放预留，
  run 收敛到成功/失败/取消后归还配额，未知/已释放引用为 no-op）+
  record_usage（append-only，拒绝重复 entry_id）+ snapshot（只读视图）。
- 非职责：不做 usage 采集（ModelGateway / ExecutionBackend 上报原始用量，
  application 归账后入 ledger）；不伪造 cost（UNKNOWN 语义）。

### EvidenceLedger（`packages/application/ports/evidence_ledger.py`，M10 增补）

- 职责：Source/Evidence/Claim 登记与关系挂接（register_source /
  register_evidence / register_claim / update_claim / attach_relation /
  get_* / relations_for_claim / has_source / claims）；Claim 状态升级
  唯一入口 `promote_claim_to_verified`（PROPOSED→VERIFIED，gate PASS +
  合法 provenance 前置）；REFUTES 争议经
  `register_evidence_with_contradiction_check` 转 DISPUTED（旧证据保留）。
- 非职责：不承载长期记忆（MemoryStore）；不拥有检索投影
  （RetrievalIndex）；跨 run 持久化属 M14（MVP 为进程内 Fake）。

### RetrievalIndex（`packages/application/ports/retrieval_index.py`，M10 增补）

- 职责：derived index 生命周期 rebuild/upsert/remove/search/entries/clear；
  `content_hash_of` 等价契约（重建可验证一致）；只读 drift 检测
  （check_index_consistency，5 类）与显式修复（rebuild_index）。
- 非职责：不是 Canonical State（ADR-0002：PostgreSQL Domain Entity 为
  真相，index 为可重建投影）；不绑定 embedding/vector DB（MVP 为
  确定性 token 检索）。

### 收编 Port

- EndpointStore（`packages/application/ports/endpoint_store.py`）：LLMEndpoint CRUD。
- ResourceCatalog（`packages/application/ports/resource_catalog.py`）：preflight 只读目录 +
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
- 覆盖 17 个 Port 全集：15 个行为 Port + EndpointStore / ResourceCatalog
  收编 Port 均有 Fake 实现并注册进 contract registry（M5 复审补齐 14
  个基线；M8 增补 ToolPackStore、M10 增补 EvidenceLedger / RetrievalIndex
  时同步补齐 Fake 与 registry）。

## 4. Contract Suite（`tests/contracts/`）

- 注册表 `tests/contracts/registry.py` 是单一事实源；M6/M7 真实 adapter
  注册工厂后同一套 suite 自动复用。
- 通用矩阵（test_common_contract.py）：正常调用、invalid input、
  transient/permanent 失败注入、close 后不可用、call recording、
  deterministic replay、serialization boundary、secret 不进入记录、
  provider 类型不泄漏、17 Port 接口兼容矩阵。
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

## 7. M15 新增 Port

### TelemetrySink（`packages/application/ports/telemetry_sink.py`）

- `begin_operation / end_operation / record_metric`;fail-open——实现不得抛出;
  不是 Audit Store(可 sampled/delayed/dropped),业务决策绝不回读。
- 实现:`NullTelemetrySink`(默认 off)/`FakeTelemetrySink`(contract suite)/
  `OtelTelemetrySink`(经 `FailSafeTelemetrySink` 兜底,adapters/otel)。
- 消费者(自 M15 起为真实使用,非形式化):relay gateway、tool_plane 执行用例、
  PolicyWrappedToolExecutor、sqlite/pg workflow 引擎、outbox relay、schedulers、
  docker execution backend、eval runner、run orchestration。

### EvalReportStore（`packages/application/ports/eval_report_store.py`）

- `put(StoredEvalReport) / get(report_digest) / query(EvalReportQuery)`;
  verbatim 报告字节为 canonical truth,索引列可重建;
  put 幂等(UPSERT by report_digest),query 确定性排序。
- 实现:Fake / SQLite / Postgres(005_eval_state.sql),contract suite 覆盖。

## 8. M16 新增 Port

### WorkerRegistry（`packages/application/ports/worker_registry.py`）

- `register / heartbeat / transition / drain / mark_lost / set_session_token /
  authenticate / list_stale / get / list_workers`;
  服务端时间是唯一权威（`last_heartbeat` 幂等取 `greatest(stored, now)`，
  绝不回拨；worker 自报时间不参与 expiry/fence/ordering）。
- 状态机：`packages/domain/workers.py` `WorkerState`
  （REGISTERING/READY/BUSY/DRAINING/OFFLINE/LOST，转移表穷尽测试）。
- 实现：FakeWorkerRegistry / PostgresWorkerRegistry（008_worker_plane.sql），
  contract suite 覆盖（tests/contracts/test_worker_registry_contract.py）。
- session token 仅存 sha256（`set_session_token` 按 generation 绑定，
  `authenticate` 只匹配当前世代）；重注册作废旧 token。

### WorkflowEngine 增量（M16）

- 新增 `claim_next(ClaimRequest) -> TaskLease | None`：kind=EXECUTION +
  capability/partition 过滤 + `FOR UPDATE SKIP LOCKED`（PG）；
  SQLite 为单进程诚实实现；Fake 同语义。
- `TaskLease` 增补 `worker_id` / `fence`（默认值兼容既有构造）；
  `tasks.fence_seq` 单调递增，每次 (re)claim 写入 `leases.fence`，
  completion 校验 `(task_id, lease_id, fence)`（stale generation 拒绝）。

### WorkflowEngine 增量（GOAL-004 cycle 2）

- 新增 `retry_schedule(run_id) -> RetrySchedule`：该 run 的重排读面
  （`scheduled` 未到期条数 / `due` 已到期条数 / `next_retry_at` 最近未到期期限）。
  与 `due_retry_task_ids` **同一列同一判据、同一个权威时钟**（分类在 adapter 内：
  生产 DB 时钟、测试注入时钟）；调用方不自己拿"现在"比较、不逐任务问。
  控制面 `GET /runs/{id}` 的 `paused_dispatch` 是它目前的唯一用途（详见
  `docs/api/CONTROL_PLANE_API.md`）。
- Fake 没有写 `RETRY_SCHEDULED` 的路径 ⇒ 它的两个读面永远回答"没有重排"；
  这条限制在 `tests/contracts/test_retry_schedule_contract.py` 里显式钉住。

### ExecutionJobQueue（`packages/application/ports/execution_job_queue.py`）

- `enqueue / describe / poll / record_result / request_cancel /
  cancel_requested`：EXECUTION 作业的 payload 投影与 settle 写入路径；
  **不是第二队列**（tasks.kind='EXECUTION' + execution_jobs 行，
  与 experiment_plans 同型）。`record_result` 在同一事务内校验活跃租约
  `(task_id, lease_id, fence)`，stale result 被拒绝。

### ExecutionBackend / WorkspaceBackend 增量（M16）

- `ExecutionBackend.execute` 增可选 `cancelled` 回调（默认 None，行为不变；
  DockerExecutionBackend 轮询 -> CANCELLED）。
- `WorkspaceBackend` 新增 `export_bundle(lease, snapshot) -> bytes` /
  `import_bundle(workspace_id, bundle, expected_digest) -> WorkspaceSnapshot`；
  bundle 为 canonical 编码（adapters/workspace/bundle.py），导入重验工作区树
  digest，拒绝路径穿越/符号链接/截断。
