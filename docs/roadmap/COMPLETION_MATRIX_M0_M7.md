# M0-M7 Completion Matrix v0.4.0

本矩阵是 M0-M7（含 M5R）各阶段的完成事实总表，由 2026-08-14 文档对账
任务基于 git history、当前代码/测试与可执行 validator 核对建立。任何
`DONE` 均有 commit、源码与测试三方可执行证据支撑，不依据 Markdown
声称推断。

## 真实完成顺序（git 证据）

```text
M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7
```

与数字编号不一致：**M3 先于 M2**（M2 Preflight 的 Model eligibility
消费 M3 Model Relay 产物）。文档记录真实依赖关系，不按编号改写历史。

## Completion Matrix

| Stage | Scope | Implementation | Plan | Review/Recheck | DoD Evidence | Git Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | Repository Foundation Quality Gate：Python/TS 工具链、依赖边界、CI 门禁 | `pyproject.toml`、`uv.lock`、`pnpm-lock.yaml`、`.importlinter*`、`tests/architecture/`（python+typescript 正反向夹具）、`.github/workflows/m0-quality.yml`、`.cursor/skills/cursor-framework-check/scripts/` | [PLAN-20260814-009（retrospective）](../../.cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md) | [RECHECK-20260814-009（retrospective）](../../.cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md) | `tests/architecture/python`（20 文件）、`tests/architecture/typescript`、`tests/tooling/`、m0 profile 门禁 | `3cc6130`（08-11，M0 baseline）；前身 `5045c59`（08-10 bootstrap） | DONE |
| M1 | Domain Kernel & Contract Assets：实体/值对象/枚举/状态机/Manifest+digest/UsageLedger/Artifact 校验 | `packages/domain/`（29 模块）、`adapters/contracts/`（7 loaders） | [PLAN-20260811-001](../../.cursor/plans/tasks/PLAN-20260811-001-m1-domain-kernel.md) | [RECHECK-20260811-001](../../.cursor/plans/rechecks/RECHECK-20260811-001-m1-domain-kernel.md) PASS | `tests/domain/`（15 文件）、`tests/loaders/`、pytest 180 | `185a752`（08-11） | DONE |
| M3 | Model Relay Compatibility：端点 CRUD/probe/eligibility/熔断/指纹/回退/脱敏 | `packages/application/model_relay/`（9）+ `policy/`（2）、`adapters/relay/`（6） | [PLAN-20260811-002](../../.cursor/plans/tasks/PLAN-20260811-002-m3-model-relay.md) | [RECHECK-20260811-002](../../.cursor/plans/rechecks/RECHECK-20260811-002-m3-model-relay.md) PASS | `tests/application/`（relay 8 文件）、`tests/adapters/relay/`（7）、pytest 339 | `7bfcd3c`（08-11） | DONE |
| M2 | Protocol Compiler + Preflight：DAG/角色/模型/工具/工作区/预算/策略解析 | `packages/application/protocol_compile/`（8）+ `preflight/`（6） | [PLAN-20260812-003](../../.cursor/plans/tasks/PLAN-20260812-003-m2-protocol-compiler-preflight.md) | [RECHECK-20260812-003](../../.cursor/plans/rechecks/RECHECK-20260812-003-m2-protocol-compiler-preflight.md) PASS | `tests/application/`（m2_* 6 文件）、m0 19/19 | `1035a64`（08-12） | DONE |
| M4 | Role/Team/Task：26 Role fixtures/异构评审/TaskContract/HandoffBundle/权限 deny | `packages/domain/`（roles/tasks/team_plan/activation 增量）、`preflight/role_checks.py` | [PLAN-20260812-004](../../.cursor/plans/tasks/PLAN-20260812-004-m4-role-team-task.md) | [RECHECK-20260812-004](../../.cursor/plans/rechecks/RECHECK-20260812-004-m4-role-team-task.md) PASS | `tests/application/`（m4_* 5 文件）、pytest 528 | `7c68e92`（08-12） | DONE |
| M5 | Ports + Fakes：14 Port/统一错误模型/12 Fake/contract suite | `packages/application/ports/`（16 模块）、`adapters/fakes/`（16 模块） | [PLAN-20260812-005](../../.cursor/plans/tasks/PLAN-20260812-005-m5-ports-fakes.md) | [RECHECK-20260812-005](../../.cursor/plans/rechecks/RECHECK-20260812-005-m5-ports-fakes.md) PASS | `tests/contracts/`（8 文件，127 项）、`tests/architecture/python`（fakes 契约） | `c75db51`（08-12） | DONE |
| M5R | Upstream Qualification：OpenHands v1.42.0 源码审计/14 Port 现实校验/6 spikes/revision lock | `tools/upstream-spikes/`（S1-S6）、`docs/references/upstream/`（7 文档 + revision lock） | [PLAN-20260812-006](../../.cursor/plans/tasks/PLAN-20260812-006-m5r-upstream-qualification.md) | [RECHECK-20260812-006](../../.cursor/plans/rechecks/RECHECK-20260812-006-m5r-upstream-qualification.md) PASS | spikes 脚本（mock credential 全 PASS）、revision lock `v1.42.0@391fbb8d` | `717545d` + `5fc23d0`（08-12/13） | DONE |
| M6 | OpenHands Runtime Adapter：6 方法 Protocol/LLM Relay/cancel 收敛/Policy Wrapper/错误映射/Workspace 安全/Usage 入账 | `adapters/openhands/`（12 模块）、`packages/application/run_orchestration/` 初版 | [PLAN-20260813-007](../../.cursor/plans/tasks/PLAN-20260813-007-m6-openhands-runtime-adapter.md) | [RECHECK-20260813-007](../../.cursor/plans/rechecks/RECHECK-20260813-007-m6-openhands-runtime-adapter.md) PASS（含二次独立复审） | `tests/adapters/openhands/`（11 文件，含 S7 spike）、`tests/contracts` 共享套件、pytest 840 | `f4b2168`（08-13） | DONE |
| M7 | Reliable Mock Vertical Slice：E2E 编排链 + SQLite 持久化 + 故障注入矩阵 | `packages/application/run_orchestration/`（11）、`adapters/sqlite/`（10）、`examples/protocols/sort_analysis_v1.yaml` | [PLAN-20260814-010（retrospective）](../../.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md) | [RECHECK-20260814-010（retrospective）](../../.cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md) | `tests/e2e/`（12 文件：happy path/F-01..F-12/idempotency/cancel-resume/restart recovery）、`tests/adapters/sqlite/`（2） | `782887d`（08-14） | DONE |

## 工程记录覆盖

- Plan + Recheck（PASS）+ Memory：M1、M3、M2、M4、M5、M5R、M6（原开发
  窗口记录，非重建）。
- Retrospective Reconstruction（2026-08-14 重建，证据来源为 git history、
  当前代码/测试与重跑的 validator）：M0、M7。
- 全部阶段 DoD 证据见上表测试/validator 列；每个 DONE 均通过
  m0 profile 全量回归。

## 阶段依赖关系

```text
M0（工程门禁基线）
→ M1（Domain Kernel，消费 M0 门禁）
→ M3（Model Relay，早于 M2 完成）
→ M2（Protocol Compiler + Preflight，消费 M3 eligibility）
→ M4（Role/Team/Task，依赖 M1/M2 契约）
→ M5（Ports + Fakes，冻结 M1-M4 边界）
→ M5R（Upstream Qualification，对 M5 Port 现实校验）
→ M6（OpenHands Adapter，承接 M5R 审计结论）
→ M7（Reliable Vertical Slice，集成 M1-M6 全链）
```

## 正式工程状态

```text
Foundation / Executable Research Kernel = completed
```

M7 是核心基础设施阶段结束的 Integration Milestone（详见
[M7_COMPLETION_RECORD.md](M7_COMPLETION_RECORD.md)）；M7 之后仓库进入
产品能力建设阶段（见根 `BACKLOG.md` 的 Remaining Technical Debt 与
Next Product Capability 分区）。

## 证据来源与边界

- 本矩阵仅记录可执行证据；不包含任何对开发窗口内讨论、评审或时间线的
  重构。
- M0/M7 的 retrospective 记录为事后重建，链接指向对应计划文件并在其中
  显式标注 `RETROSPECTIVE_RECONSTRUCTION: true`。
- 发现但未纳入本表的历史文档不一致（如 BACKLOG 完成日期、M6 勾选状态）
  由对账任务修正并在 [CHANGELOG](../../CHANGELOG.md) 中记录。