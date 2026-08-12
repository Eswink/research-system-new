---
id: RECHECK-20260812-005
plan_id: PLAN-20260812-005
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-12
completed_at: 2026-08-12
reviewer: root-agent-independent-pass
baseline_ref: PLAN-20260812-005 VERIFYING（实施自报 DoD 证据齐备）
checked_head: working-tree
---

# RECHECK-20260812-005 — M5 Ports + Fakes 独立复审

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260812-005-m5-ports-fakes.md`
- 验收条件：AC-01 至 AC-08（BACKLOG M5 六项 DoD）
- 复审目标：回答“Ports 从 Research OS 自身角度是否正确、稳定、可测试、可替换？”
- 基线：计划处于 VERIFYING，实施自报 697 pytest 全绿。本次复审以工作区代码、
  可执行 Contract Tests 与 M5 DoD 为事实来源，不默认实现/Checklist/Commit 正确。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | Port inventory 与职责 | 14 Port 逐项审计（AgentRuntime/WorkflowEngine/ModelGateway/ToolProvider/WorkspaceBackend/ExecutionBackend/ArtifactStore/EventPublisher/PolicyEvaluator/CredentialResolver/MemoryStore/BudgetLedger + EndpointStore/ResourceCatalog）；见下表 | PASS |
| G-02 | Fake 契约 | 14 个 Fake 全部：deterministic / 错误注入 / 成功路径 / 失败路径记录 / close / 离线 | PASS |
| G-03 | Contract suite 资格门禁 | `pytest tests/contracts -q` 121 passed（registry 驱动，M6/M7 真实 adapter 可注册复用） | PASS |
| G-04 | lint/typecheck/test | m0 profile 18/18 PASS；pytest 727 passed；mypy strict 通过；ruff check+format clean；架构边界 8 passed | PASS |
| G-05 | 契约资产 | `validate_bundle.py` PASS；governance `validate.py` PASS；PORTS.md 同步更新 | PASS |
| G-06 | 边界确认 | 未实现 OpenHandsRuntimeAdapter；未复制 OpenHands 内部 API 进 Port；未为“绝对 provider-agnostic”抽象失真 | PASS |

## Port 审计结论（G-01 展开）

| Port | 职责判定 | 类型归属 | 泄漏/重叠 | 结论 |
| --- | --- | --- | --- | --- |
| AgentRuntime | 仅 session 生命周期；Protocol 编译/Research truth/Workflow 编排均在非职责声明；状态来自 domain AgentSessionState；无 OpenHands Conversation 模型 | domain + Port DTO | 无 | PASS |
| WorkflowEngine | at-least-once 分发/lease/heartbeat/cancel；不执行 Agent 循环 | domain | 无 | PASS |
| ModelGateway | relay/provider-independent 最小调用面；消费 LLMEndpoint/SecretValue；未重复 M3（eligibility/fallback 编排在 application use case） | domain | 无 | PASS |
| ToolProvider | 执行 ToolCallRecord→ToolResultRecord；Skill/Capability/Policy 分离；frozen tool set 由调用方执行；permission truth 不在 provider | domain | 无 | PASS |
| WorkspaceBackend | workspace/lease/snapshot 生命周期；不执行命令 | domain | 与 ExecutionBackend 边界清晰 | PASS |
| ExecutionBackend | 执行 ExecutionSpec→ExecutionRun；timeout→TIMED_OUT 状态；不记账不管理文件布局 | domain | 无 | PASS |
| ArtifactStore | 内容寻址持久化；不承担 Claim/Evidence truth | domain | 无 | PASS |
| EventPublisher | 仅 Domain Event（EventEnvelope）；runtime event/telemetry 明确不替代 | domain | 无 | PASS |
| PolicyEvaluator | evaluate→决策；deterministic；decision log 无 secret；enforcement 在调用方 | domain | 无 | PASS |
| CredentialResolver | resolve(ref)→SecretValue；repr/记录脱敏；不持久化 | Port DTO（SecretValue） | 无 | PASS |
| MemoryStore | commit 走 provenance gate；不做语义判断 | domain | 无 | PASS |
| BudgetLedger | reserve/record_usage/snapshot；与 ModelGateway/WorkflowEngine 无耦合（usage 采集在 application 归账） | domain | 无 | PASS |
| EndpointStore | LLMEndpoint CRUD（收编，真实实现存在 adapters/relay） | domain | 无 | PASS（M5 复审补齐 Fake+contract） |
| ResourceCatalog | preflight 只读目录 + PreflightContext DTO | domain + Port DTO | 无 | PASS（M5 复审补齐 Fake+contract） |

## 发现与修复（审计 → 根因 → 修复 → 测试 → 验证闭环）

| ID | 严重度 | 发现与根因 | 修复 | 回归测试 |
| --- | --- | --- | --- | --- |
| R-001 | ERROR（P0） | FakeExecutionBackend 成功路径崩溃：ExecutionRun 未填 completed_at，违反 domain invariant “SUCCEEDED run must carry completed_at”；既有 contract 测试未覆盖 happy path，suite 名义全绿 | 构造时补齐 started_at/completed_at | `test_happy_path_returns_valid_run`/`test_timed_out_run_is_valid`/`test_cancelled_run_is_valid` |
| R-002 | MAJOR（P1） | FakeAgentRuntime 终端状态被二次 run 覆盖：run→FAILED 后再 run 追加重复 terminal event，事件流不单调 | run() 终端状态直接返回结果，不追加事件 | `test_terminal_state_is_final`/`test_cancel_after_terminal_is_noop` |
| R-003 | MAJOR（P1） | FakeEventPublisher 幂等发布覆盖首次 payload：重复 event_id 用新 envelope 覆盖旧值（篡改窗口） | 首次 envelope 不可覆盖 | `test_idempotent_publish_keeps_first_payload` |
| R-004 | MAJOR（P1） | FakeWorkflowEngine.submit 抛 InvalidInputError 而非幂等（违反 PORTS.md §1“重复键返回首次结果”）；伴随 bug：idempotency_key 用 task_id 字典查重 | submit 静默幂等；新增 `_idem_keys` 映射 | `test_workflow_duplicate_submit_is_idempotent`（替换原“rejected”断言） |
| R-005 | MAJOR（P1） | FakeArtifactStore.delete 无法从 ACTIVE 删除（状态机缺迁移），且 tombstone 后内容仍可 get | 状态机补 ACTIVE/ARCHIVED→DELETED_TOMBSTONE；delete 移除内容 | `test_delete_from_active_is_legal`/`test_deleted_artifact_content_is_unreadable`/`test_delete_is_idempotent_via_state_rejection` |
| R-006 | MAJOR（P1） | 10 个 Fake 业务失败路径不记录调用（CallRecord 契约要求每次调用含失败都记录）；“Fake call history”门禁失效 | 全部业务校验失败路径补 `_record(..., error=...)` 后抛出 | `test_deny_scope_injection_records_and_rejects` + 既有 121 项套件 |
| R-007 | MINOR（P2） | EndpointStore/ResourceCatalog 无 Fake 无 contract 覆盖，14 Port 全集注册表不完整 | 新增 FakeEndpointStore/FakeResourceCatalog + 注册 + 通用矩阵扩展 | `test_crud_roundtrip`/`test_missing_endpoint_raises_key_error`/`test_snapshot_returns_injected_catalog` |
| R-008 | MINOR（P2） | dead code：FakeBase._invoke、registry.implementations() 无调用者 | 删除 | 全量回归 |

## 结论

- 结果：`PASS`
- 理由：AC-01~AC-08 全部有可复现证据；8 项问题完成修复并有回归测试锁定；
  contract suite 94→121 项；pytest 727 passed；m0 profile 18/18 PASS；
  双契约 validator PASS；架构边界 8/8 PASS；未降低 Contract、未删除失败测试、
  未让 Fake 绕过真实语义、未泄漏第三方类型、未提前实现 M6。
- M5R readiness：READY（D1-D6 决策保留，M5R 以 PORTS.md + Port 签名 + contract suite 为反向验证 harness）。
- 后续动作：M5 判定 DONE；停在阶段边界，不自动开始 M5R/M6。

## P2 技术债清偿（2026-08-12，用户批准计划后追加）

- P2-1 FakeAgentRuntime 中间态驱动：新增 test-only `advance()`（非 Port 方法），
  沿 domain 状态机推进 INITIALIZING/WAITING_FOR_APPROVAL/PAUSED/STUCK 并追加
  对应 RuntimeEvent；contract suite 新增 4 项（全迁移覆盖/事件顺序/非法迁移/
  中间态 run 收敛）。
- P2-2 FakeModelGateway 注入机制统一：删除 `_raise_if_fault` 双机制；
  fail_timeout/fail_transient 构造时预置 `set_script`；构造参数收敛为
  `FakeModelGatewayOptions` 参数对象（9 参数超限 → 1 参数）。
- P2-3 CredentialResolver 错误统一：Port docstring、Fake 与 EnvCredentialResolver
  全部改抛 `InvalidInputError`；`checks.py`/`probe.py` 消费方收紧；6 处测试断言
  同步（EndpointStore 的 not-found KeyError 语义保留）。
- P2-4 第二套手工 Fake 整合：`tests/application/relay_fakes.py` 删除；
  FakeModelGateway 补齐失败快照注入（auth/stream/tool/structured/no_usage，
  返回 ok=False 快照而非异常）与 `FakeModelGatewayOptions`；常量迁至
  `tests/application/relay_fixtures.py`；test_run_probe/test_endpoint_test
  改用 adapters.fakes；contract suite 新增 2 项失败快照语义测试。
- P2-5 保留：`CompletionRequest.messages` 的 dict 表达作为 M5R upstream
  wire-format 验证项，不纳入本次。
- 回归：contract suite 127 项；pytest 733 passed；m0 profile 18/18 PASS；
  双 validator PASS；mypy strict 92 files Success；ruff check + format clean。