---
id: MEM-20260812-005
title: M5 Ports + Fakes 独立复审修复事实
status: ACTIVE
created_at: 2026-08-12
updated_at: 2026-08-12
scope: repository
confidence: 0.95
review_after: 2026-11-12
source_plans:
  - .cursor/plans/tasks/PLAN-20260812-005-m5-ports-fakes.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260812-005-m5-ports-fakes.md
supersedes: []
tags: [m5, ports, fakes, contract-tests, idempotency, tombstone, call-recording]
---

# MEM-20260812-005 — M5 Ports + Fakes 独立复审修复事实

## 做了什么

M5 独立复审完成，修复 8 项问题（1 P0 + 5 P1 + 2 P2）后 `m0` profile 18/18 PASS、
727 pytest 通过、contract suite 94→121 项、bundle/governance validator 通过。落地事实：

1. `FakeExecutionBackend` 成功路径补齐 `started_at/completed_at`：`ExecutionRun` domain
   invariant 要求 SUCCEEDED 必须携带 completed_at，原 Fake 直接崩溃；contract suite
   此前未覆盖 happy path，名义全绿掩盖了 P0。
2. `FakeAgentRuntime.run()` 终端状态保护：terminal 后重复 run 返回同一结果、不追加事件，
   事件流单调（原 FAILED 后再 run 会重复追加 terminal event）。
3. `FakeEventPublisher` 幂等保留首次 envelope：重复 event_id 不覆盖首次 payload
   （防同 id 篡改发布）。
4. `FakeWorkflowEngine.submit` 静默幂等（at-least-once）：重复 task.id / idempotency_key
   返回首次结果、不抛错、不覆盖首次契约；新增独立 `_idem_keys` 映射（原实现错误地
   用 task_id 字典查 idempotency_key）。
5. `FakeArtifactStore` tombstone 语义：状态机补 ACTIVE/ARCHIVED→DELETED_TOMBSTONE，
   delete 后内容不可 get/verify；原实现 ACTIVE 无法删除且 tombstone 后内容仍可读。
6. 全部 14 个 Fake 业务失败路径（InvalidInputError/KeyError 等）在 raise 前记录
   CallRecord(error=...)：CallRecord 契约要求“每次调用含失败都记录”，原实现直接
   raise 绕过记录，Fake call history 门禁失效。
7. `EndpointStore`/`ResourceCatalog` 补齐 Fake 与 contract 注册：14 Port 全集均可被
   contract suite 覆盖（M6/M7 真实 adapter 注册后自动复用）。
8. 清理 dead code：`FakeBase._invoke`、`registry.implementations()`。

## 为什么这样做

- **contract suite 名义全绿不等于 happy path 覆盖**：94 项 suite 中 ExecutionBackend
  只有 timeout/失败分类测试，成功路径从未执行；Fake 必须与真实 adapter 共享同一
  Contract Tests 资格门禁，happy path 是门禁第一项。
- **幂等语义要可防御篡改**：重复 event_id 返回首次结果是 PORTS.md §1 契约；覆盖
  payload 等于允许调用方以同 id 发布不同内容，破坏 Consumer 去重前提。
- **at-least-once 下重复提交是正常流**：duplicate submit 是 M7 故障注入矩阵的
  “duplicate task delivery” 场景；抛 InvalidInputError 会让 Fake 无法表达真实语义，
  且 idempotency_key 查重映射本身有 bug。
- **Fake 失败路径也必须可审计**：call recording 是 contract suite 对真实 adapter 的
  强制项；Fake 若在失败路径跳过记录，未来 adapter 的失败记录行为就没有对照基线。
- **Fake 与真实 Adapter 共享资格门禁**：14 个 Port 中 2 个无实现/无注册会使 registry
  驱动模式断裂；补齐后 M6/M7 注册工厂即可自动复用同一套 suite。

## 怎么做与复现

1. 全量门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0` → 18 checks PASS。
2. Contract suite：`uv run --frozen --no-sync python -B -m pytest tests/contracts -q` → 121 passed。
3. 全量测试：`uv run --frozen --no-sync python -B -m pytest -q` → 727 passed。
4. 架构边界：`uv run --frozen --no-sync python -B -m pytest tests/architecture -q` → 8 passed。
5. 契约 validator：`python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`、`python -B .cursor/skills/governance-check/scripts/validate.py`。

## 适用边界

- 适用于：M6 OpenHandsRuntimeAdapter 通过 agent_runtime contract suite 验收；M7
  PostgreSQL WorkflowEngine 以 contract suite 为验收（submit 幂等语义已在
  `test_workflow_duplicate_submit_is_idempotent` 锁定）；真实 adapter 落地时
  `tests/contracts/registry.py` 注册工厂即可复用全部 121 项。
- 不适用于：M5R upstream qualification（RECHECK-20260812-005 保留 D1-D6 决策供
  upstream 证据复审，只验证不改）；M6 OpenHands 内部事件模型（Port 不预设上游类型）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-12）。
- contract registry 新增实现但未通过全部 suite（registry 驱动模式被绕过）。
- Fake 业务失败路径再次绕过 `_record`（`test_failure_injection_records_and_raises`
  及回归套件会失败）。
- ArtifactStore 状态机或 EventPublisher 幂等语义被重新定义。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260812-005-m5-ports-fakes.md` | M5 范围与验收 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260812-005-m5-ports-fakes.md` | PASS 结论与 8 项问题清单 |
| repository | `adapters/fakes/execution_backend.py`（started/completed_at） | ExecutionRun invariant |
| repository | `adapters/fakes/event_publisher.py`（首次 envelope 保留） | event_id 幂等防篡改 |
| repository | `adapters/fakes/workflow_engine.py`（_idem_keys） | at-least-once 幂等 submit |
| repository | `adapters/fakes/artifact_store.py`（tombstone 迁移） | delete 语义 |
| repository | `tests/contracts/test_ports_regressions.py`（27 项） | 修复回归锁定 |
| repository | `docs/architecture/PORTS.md`（§2/§3/§4） | 契约规格同步 |

## P2 技术债清偿（2026-08-12 追加）

- P2-1：`adapters/fakes/agent_runtime.py` 新增 `advance()` 中间态驱动器；
  `tests/contracts/test_agent_runtime_contract.py` 4 项中间态契约测试。
- P2-2：`adapters/fakes/model_gateway.py` 删除 `_raise_if_fault`，新增
  `FakeModelGatewayOptions` 参数对象；故障注入统一走 `set_script`。
- P2-3：`packages/application/ports/credential_resolver.py`、
  `adapters/fakes/credential_resolver.py`、`adapters/relay/credential_resolver.py`
  未解析统一抛 `InvalidInputError`；`preflight/checks.py`、
  `model_relay/probe.py` 消费方收紧；6 处测试断言同步。
- P2-4：删除 `tests/application/relay_fakes.py`；`FakeModelGateway` 补齐
  失败快照注入（ok=False 快照语义）；常量迁至
  `tests/application/relay_fixtures.py`；`test_run_probe.py`/`test_endpoint_test.py`
  改用 `adapters.fakes`；`tests/contracts/test_ports_semantics.py` 新增 2 项
  失败快照/usage 契约测试。
- P2-5：保留现状，列为 M5R upstream wire-format 验证项。