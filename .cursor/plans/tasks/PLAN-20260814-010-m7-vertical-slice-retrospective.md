---
id: PLAN-20260814-010
slug: m7-vertical-slice-retrospective
title: M7 Reliable Mock Vertical Slice — Retrospective Reconstruction
status: DONE
created_at: 2026-08-14
updated_at: 2026-08-14
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "M0-M7 Documentation Reconciliation & Completion Prompt：为缺失 Plan 的阶段创建 retrospective stage record"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md
memory_entries:
  - MEM-20260814-010
---

# PLAN-20260814-010 — M7 Retrospective Reconstruction

> RETROSPECTIVE_RECONSTRUCTION: true
>
> 本记录由 2026-08-14 文档对账任务依据 git history、当前代码/测试与
> 可执行 validator 事后重建。M7 开发窗口（2026-08-13 ~ 2026-08-14）当时
> 未创建独立任务计划、复检与工程记忆文件（M6 复检仅以"下一项任务"前向
> 引用 M7）；本记录不声称这些文件在开发时已存在，也不虚构当时的讨论、
> 评审或测试结果。

## 目标（原 M7 定义）

按 `CODEX_BOOTSTRAP.md` 与 `docs/roadmap/VERTICAL_SLICE_V0_4_0.md` 的 M7
定义：Reliable Mock Vertical Slice —— 以 mock/可执行环境跑通
Compile → Preflight → Manifest Freeze → Task/Lease → Agent Session →
Tool/Handoff/Artifact/Evidence/Claim/Evaluation → Complete 全链路，并注入
transient model failure、duplicate task delivery、tool timeout、worker
crash、budget exhaustion、user pause/cancel 等故障验证可靠性语义。

## 验收条件（retrospective 重建记录自身的验收）

- [x] AC-01：本记录全部陈述可由 git history、当前代码/测试或可执行
      validator 直接支持；无虚构的讨论、评审或测试结果。
- [x] AC-02：M7 的 DoD（CODEX_BOOTSTRAP / VERTICAL_SLICE）逐项有当前
      证据（tests/e2e 与 commit `782887d`）。
- [x] AC-03：重建记录通过 governance validator（章节/ID/状态机）与
      bundle validator（链接/版本引用）。
- [x] AC-04：retrospective 性质在文件头显式标注
      `RETROSPECTIVE_RECONSTRUCTION: true`。

## 实际实现范围

- `packages/application/run_orchestration/`（11 个模块）：服务层 +
  phase runner + task executor + commands + handoff builder +
  evaluation gate + convergence；`ResearchRun` 实体与 Run 状态机真实迁移
  （`packages/domain/run.py`）。
- `adapters/sqlite/`（10 个模块）：`SqliteWorkflowEngine`
  （tasks/leases/idempotency_records/outbox_events）、`SqliteArtifactStore`
  （内容寻址 blob）、`SqliteOutboxEventPublisher`（Transactional Outbox）、
  db/serialization/projections。
- TaskLease + heartbeat + `recover_expired_leases` 重启恢复；IdempotencyRecord
  （submit 幂等去重 + request_digest）；retry/backoff（TransientPortError +
  retryable_categories 门控）；协作式 cancellation + lease 释放 +
  CANCELLED 事件；Pause/Resume（frozen manifest 语义 + digest mismatch
  拒绝，`task_executor._assert_frozen_manifest` 落实 AGENTS.md §5）。
- Reference Scenario：`examples/protocols/sort_analysis_v1.yaml`
  （2-phase execution→review 线性 DAG，review 带 QUALITY_GATE；
  id `sort_analysis_v1_0_1` / version 0.4.0）。
- E2E 测试：`tests/e2e/`（12 文件：vertical slice happy path、
  fault injection matrix F-01..F-12、fault convergence、idempotency、
  cancel/resume、restart recovery、run rejections、orchestration
  convergence）+ `tests/adapters/sqlite/`（2 文件）。
- `tests/contracts/` 注册表驱动共享契约套件对 SQLite 持久化实现的验收
  （M5 语义冻结 → M7 以 contract suite 验收持久化实现）。

## 非目标

- PostgreSQL task queue（生产升级路径，同 Port 契约；跨进程分布式调度属
  Temporal 阶段）。
- DockerWorkspace 容器链路全量验证（M6 遗留；仅映射代码 + 探测式 smoke）。
- MCP live 集成、真实付费 LLM、Research Console / UI。
- usage 归账到 BudgetLedger 的真实 relay 链路闭环（需真实 E2E 前置）。
- 定时自愈调度（recover_expired_leases 当前为 start_run 懒触发）。

## Dependencies

- M6（OpenHandsRuntimeAdapter + run_orchestration 初版，commit `f4b2168`）；
  M5（14 Port + 12 Fake + contract suite）；M2/M4（Protocol Compiler /
  Preflight / Role / Task）；M1（Domain Kernel）；M0（工程门禁）。
- 真实完成顺序（git 证据）：M0(08-11) → M1(08-11) → M3(08-11) → M2(08-12)
  → M4(08-12) → M5(08-12) → M5R(08-12/13) → M6(08-13) → M7(08-14)。
  M7 是 Core Infrastructure 阶段的 Integration Milestone。

## Architecture boundaries

- Canonical State：PostgreSQL Domain Entity 为业务真相（ADR-0002）；
  M7 垂直切片经同一 WorkflowEngine/ArtifactStore/EventPublisher Port
  使用 SQLite 实现，SQLite 是可替换实现而非 Canonical State 变更。
- 可靠性语义：at-least-once + idempotency + deduplication（AGENTS.md §7）；
  业务写入与事件同事务（Transactional Outbox）。
- OpenHands 细节严格停留在 `adapters/openhands/`；M7 在 Fake 与真实
  adapter 共用的 contract suite 上验收编排层。

## 主要 implementation artifacts

| 类型 | 位置 |
| --- | --- |
| 编排 | `packages/application/run_orchestration/`（service / phase_runner / task_executor / commands / handoff_builder / evaluation_gate / convergence） |
| 持久化 | `adapters/sqlite/`（db / workflow_engine / artifact_store / event_publisher / outbox / leases / projections / serialization） |
| 领域增量 | `packages/domain/run.py`（ResearchRun + Run 状态机迁移） |
| 参考场景 | `examples/protocols/sort_analysis_v1.yaml` |
| E2E | `tests/e2e/`（12 文件，scenario_catalog.py 构造 m7_catalog/m7_project/m7_preflight_context） |
| 持久化验收 | `tests/adapters/sqlite/`、`tests/contracts/`（注册表共享套件） |

## Git commits

- `782887d`（2026-08-14）feat(m7): reliable vertical slice with
  independent review fixes（M7 唯一实现 commit；含独立复审修复）。
- 前序支撑：`f4b2168`（M6，08-13）、`c75db51`（M5，08-12）。

## Tests / validation

- `tests/e2e/test_vertical_slice_happy_path.py`：Preflight → ManifestFreeze
  → E2E happy path（2 tasks、2 agents、4 artifacts、event 流断言）。
- `tests/e2e/test_fault_injection_matrix.py` / `test_fault_injection_gates.py`
  / `test_fault_matrix.py` / `test_fault_convergence.py`：F-01..F-12 故障
  注入矩阵与收敛。
- `tests/e2e/test_idempotency.py`：duplicate delivery 无重复副作用。
- `tests/e2e/test_cancel_resume.py` / `test_restart_recovery.py`：cancel
  收敛、lease 恢复。
- `tests/e2e/test_run_rejections.py` / `test_orchestration_convergence.py`。
- 全量回归：pytest（M7 完成后全量绿）、mypy strict、ruff、m0 profile、
  validate_bundle、governance（本重建记录由 RECHECK-20260814-010 于
  2026-08-14 重跑验证）。

## DoD

按 CODEX_BOOTSTRAP / VERTICAL_SLICE DoD 核对：

- [x] validate_bundle.py 通过（M7 完成后 bundle validator PASS）。
- [x] Domain tests 通过（tests/domain 全绿，含 run 状态机迁移）。
- [x] Role/Model/Protocol references 完整（sort_analysis_v1 场景 fixture）。
- [x] Preflight 能拒绝不兼容模型（test_run_rejections + M4 preflight role
      检查）。
- [x] duplicate task 不产生重复副作用（test_idempotency + F-07）。
- [x] Run resume 不允许静默模型漂移（`_assert_frozen_manifest` +
      digest mismatch 拒绝）。
- [x] tool credentials 与 LLM credential 隔离（M3/M6 边界，M7 沿用）。
- [x] Reviewer read-only / Writer 不能升级 Claim truth（M4 权限语义，
      E2E 场景覆盖）。
- [x] OpenHands adapter contract 通过（M6 contract suite 共享，M7 回归）。

## 发现过的重要问题

- M7 完成后发现 BACKLOG M6 节 `resume Manifest check` 行勾选状态缺失（该
  行未勾选）但注释"→ M7 完成"（实际已由 `task_executor._assert_frozen_manifest`
  落实）：勾选状态与实现不符，由本对账任务修正。
- BACKLOG 存在未定义 "M8" 引用（usage 归账闭环标注 M8 接入），roadmap 无
  M8 定义：改为 post-M7 Next Capability 表述。
- BACKLOG 中 M7 完成日期标注为 2026-08-13，git commit `782887d` 日期为
  2026-08-14：以 commit 为准修正文档日期。

## 最终状态

- 状态：DONE（commit `782887d` + tests/e2e 全绿 + m0 profile 回归）。
- `Foundation / Executable Research Kernel = completed`；M7 后进入新的
  产品能力建设阶段（BACKLOG Next Product Capability 区）。

## 对下一阶段提供的 Contract

- 编排链契约：Compile → Preflight → Freeze → TeamResolve → Execute →
  Evidence/Claim → Gate → Complete 的调用面与事件面由 run_orchestration
  冻结，后续产品能力（Tool Plane / Real Experiment Runtime / Console）
  在其上叠加。
- 持久化 Port 契约：WorkflowEngine/ArtifactStore/EventPublisher 的
  contract suite 即 PostgreSQL 生产实现的验收基线。
- 可靠性语义：at-least-once + idempotency + outbox 已可执行验证，
  任何新副作用入口必须继承 F-01..F-12 故障矩阵。

## 已知非阻断技术债

- PostgreSQL task queue（同 Port 契约，Temporal/P2-Production 阶段）。
- `recover_expired_leases` 定时自愈（当前 start_run 懒触发，单进程安全）。
- 历史 Run 快照运营迁移（`manifest_semantic_digest=None` 旧快照不可
  resume，需重新冻结或 fork run）。
- DockerWorkspace 容器链路全量验证（M6 遗留，部署配置阶段）。
- ModelRelay + OpenHandsRuntimeAdapter usage 归账到 BudgetLedger 的真实
  链路闭环（需真实 relay E2E）。

## 实施清单（重建动作）

- [x] STEP-01：从 git log / 目录结构 / tests/e2e 提取 M7 实现证据。
- [x] STEP-02：核对 CODEX_BOOTSTRAP / VERTICAL_SLICE DoD 并逐项落证据。
- [x] STEP-03：创建本 retrospective 计划并登记 ALL_PLAN。
- [x] STEP-04：执行 retrospective recheck（RECHECK-20260814-010，
      2026-08-14 实际重跑 validators/门禁）。
- [x] STEP-05：创建工程记忆 MEM-20260814-010 并登记 INDEX。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 实现范围 | git | `782887d`（M7）；前序 `f4b2168`（M6）/ `c75db51`（M5） | 存在 |
| EV-02 | 编排与持久化 | file | `packages/application/run_orchestration/`（11）、`adapters/sqlite/`（10） | 存在 |
| EV-03 | Reference Scenario | file | `examples/protocols/sort_analysis_v1.yaml` | 存在 |
| EV-04 | E2E 证据 | test | `tests/e2e/`（12 文件：happy path / F-01..F-12 / idempotency / cancel-resume / restart） | 存在 |
| EV-05 | DoD 核对 | check | 2026-08-14 重跑 m0 profile + validate_bundle + governance + pytest | 见 RECHECK-20260814-010 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-14 | — | IN_PROGRESS | 文档对账任务创建 retrospective 重建记录 | 本计划创建 |
| 2026-08-14 | IN_PROGRESS | DONE | RECHECK-20260814-010 PASS（2026-08-14 实际重跑） | RECHECK 文件 |

## 影响报告

- Domain/API/schema：ResearchRun/Run 状态机真实迁移（M7 内完成，已在
  `packages/domain/run.py` 冻结）。
- 安全/凭据：沿用 M6 边界（host shell deny、key 不落域）；无新增面。
- 兼容性/迁移：SQLite 与 PostgreSQL 同 Port 契约；旧快照迁移为技术债。
- 上游版本：openhands-sdk v1.42.0@391fbb8d 不变。
- 下一项任务：BACKLOG Next Product Capability 首个能力立项（推荐
  Research Tool Plane，依赖 M5 ExecutionBackend Port 的真实实现）。