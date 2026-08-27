# M7 Completion Record — Reliable Mock Vertical Slice

> 阶段状态：`DONE`（2026-08-14，git commit `782887d`）
>
> 本记录由 2026-08-14 文档对账任务基于 git history、当前代码/测试与
> 可执行 validator 建立；所有结论均引用真实测试文件或 commit，不包含
> 虚构过程描述。M7 阶段缺失原开发窗口 Plan/Recheck 的说明见
> [PLAN-20260814-010（retrospective）](../../.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md)。

## 1. Reference Scenario

`examples/protocols/sort_analysis_v1.yaml`（id `sort_analysis_v1_0_1`，
version 0.4.0）：2-phase 线性 DAG——

1. `execution`：`experiment_engineer` 在隔离 workspace 分析输入算法仓库，
   产出 `analysis_report` Artifact（`bash_read_only` Tool，Policy gate
   允许）；
2. `review`：`scientific_reviewer` 独立复核 Phase 1 输出，从 Artifact 形成
   Evidence → Claim，经 AcceptanceCriteria gate（`QUALITY_GATE`）产出
   ReviewFinding/Decision。

场景领域资源由 `tests/e2e/scenario_catalog.py` 纯代码构造（
`m7_catalog()` / `m7_project()` / `m7_preflight_context()`），
`tests/e2e/scenario.py` 提供 `M7Harness`、`StructuredOutputAgentRuntime`
与 `m7_protocol()` 注入面。

## 2. E2E Chain（逐项回答）

| 环节 | 实现/验证 | 证据 |
| --- | --- | --- |
| Protocol Compile | `packages/application/protocol_compile/`；`m7_protocol()` 编译 | `tests/e2e/test_vertical_slice_happy_path.py`；`tests/application/`（m2_*） |
| Preflight | `packages/application/preflight/`（role/budget/policy/workspace 检查） | `tests/e2e/test_run_rejections.py`（拒绝路径）；F-05/F-08 见下 |
| Manifest Freeze | RunManifest + `manifest_semantic_digest`；frozen 语义 | `tests/e2e/test_cancel_resume.py`（digest mismatch 拒绝）；`packages/domain/manifest.py` |
| Team Resolve | RolePool/AgentBinding 解析与 phase 分配 | `tests/e2e/test_vertical_slice_happy_path.py`（2 tasks、2 agents）；`tests/application/`（m4_*） |
| Task/Attempt/Lease | TaskLease + heartbeat + `recover_expired_leases` | `adapters/sqlite/leases.py`；`tests/e2e/test_workflow_restart_recovery.py`；F-06 |
| OpenHands Runtime | 编排经 AgentRuntime Port；M6 adapter 复用 | `tests/e2e/test_vertical_slice_happy_path.py`（StructuredOutputAgentRuntime 注入）；`tests/adapters/openhands/` |
| Tool | ToolProviderSpec → ToolProvider Port → Fake 注入 | `tests/e2e/scenario_catalog.py`；`tests/contracts/` |
| Workspace | WorkspaceBackend Port + 隔离 workspace 语义 | `packages/domain/workspace.py`；`tests/e2e/` |
| Artifact | `SqliteArtifactStore` 内容寻址 blob + digest 校验 | `adapters/sqlite/artifact_store.py`；`tests/e2e/test_vertical_slice_happy_path.py`（4 artifacts） |
| Evidence | Evidence 记录形成（review phase 从 Artifact 构建） | `tests/e2e/test_vertical_slice_happy_path.py` |
| Claim | Claim 回溯 Artifact/Evidence | 同上；`packages/domain/evidence.py` |
| Evaluation | AcceptanceCriteria gate（`QUALITY_GATE`，纯函数求值器） | `packages/domain/acceptance.py`；`tests/e2e/test_orchestration_convergence.py` |
| Budget | BudgetPolicy → BudgetReservation；F-08 budget exhausted → Preflight FAIL | `tests/e2e/test_fault_injection_matrix.py` |
| Retry | retry/backoff：`TransientPortError` + `retryable_categories` 门控 | F-01 model timeout（retryable）→ 重试成功；F-02 permanent → FAILED 不重试 |
| Cancel | 协作式 cancel + lease 释放 + CANCELLED 事件，幂等 | `tests/e2e/test_cancel_resume.py` |
| Fault Injection | F-01..F-12 矩阵（F-01/02/05/06/07/08 在 `test_fault_injection_matrix.py`；F-09..F-12 policy denied/cancellation/malformed/evaluator rejection 在 `test_fault_injection_gates.py`） | `tests/e2e/` |
| Idempotency | IdempotencyRecord（submit 幂等去重 + request_digest）；duplicate delivery 无重复副作用 | `tests/e2e/test_idempotency.py`；F-07 |
| Recovery boundary | `recover_expired_leases` 重启恢复（进程重启模拟）；Pause/Resume 拒绝 manifest digest mismatch | `tests/e2e/test_workflow_restart_recovery.py`；`tests/e2e/test_cancel_resume.py` |

## 3. 关键可靠性语义（AGENTS.md §7 落地）

- at-least-once + idempotency + deduplication：`SqliteWorkflowEngine`
  （tasks/leases/idempotency_records/outbox_events）同事务写入。
- Transactional Outbox：业务写入与事件同事务（`SqliteOutboxEventPublisher`）。
- 冻结 Tool Set / frozen manifest：resume 时 `task_executor._assert_frozen_manifest`
  强制（AGENTS.md §5），digest mismatch 拒绝。
- F-03/F-04 注入面说明（不可达路径不伪造）：编排层经 FakeAgentRuntime，
  不经过 ToolProvider Port；该注入面由 `tests/contracts`（FakeToolProvider
  错误注入）与 M6 PolicyWrappedToolExecutor 测试覆盖——见
  `test_fault_injection_matrix.py` docstring。

## 4. 规格偏差（有意记录，不抹平）

- Canonical State 目标为 PostgreSQL Domain Entity（ADR-0002）；M7 垂直
  切片经同一 WorkflowEngine/ArtifactStore/EventPublisher Port 使用
  `adapters/sqlite`。SQLite 是可替换实现；PostgreSQL 生产实现属于
  Remaining Technical Debt（BACKLOG）。
- ExecutionBackend 容器链路验证（DockerWorkspace）为 M6 遗留，未在 M7
  关闭；Sandbox execution 在切片中以进程内/Fake 语义执行。

## 5. 验证证据汇总

| 类型 | 结果 |
| --- | --- |
| git | `782887d` feat(m7): reliable vertical slice with independent review fixes（2026-08-14） |
| 测试 | `tests/e2e/` 12 文件全绿；`tests/adapters/sqlite/` 2 文件；全量 pytest PASS |
| 门禁 | m0 profile 全量回归 PASS（M7 完成后） |
| validator | validate_bundle PASS；governance validate PASS |
| DoD | 按 CODEX_BOOTSTRAP / VERTICAL_SLICE DoD 逐项核对通过（见 retrospective 计划 §DoD） |

## 6. 结论

M7 完成 Reliable Mock Vertical Slice：全 E2E 链可执行、故障注入矩阵
收敛、幂等/取消/恢复语义可验证。`Foundation / Executable Research Kernel
= completed`；M7 后进入产品能力建设阶段（BACKLOG Next Product
Capability）。