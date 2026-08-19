# M0–M11 Completion Matrix v0.4.0

> 本矩阵是 M0–M11（含 M5R）的**唯一完成事实总表**，由 DOC-R1 文档恢复/
> 校正任务（2026-08-16）在 `COMPLETION_MATRIX_M0_M7.md`（2026-08-14 文档
> 对账建立）之上扩展 M8–M11 建立。任何 `DONE` 均有 commit、源码与测试
> 三方可执行证据支撑，不依据 Markdown 声称推断。M8–M11 行依据各阶段
> completion record 与对应 commits 建立；不在此维护第二套 milestone
> truth。

## 真实完成顺序（git 证据）

```text
M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7 → M8 → M9 → M10 → M11
```

M0–M7 段与数字编号不一致：**M3 先于 M2**（M2 Preflight 的 Model
eligibility 消费 M3 Model Relay 产物）。文档记录真实依赖关系，不按编号
改写历史。M8–M11 为 M7 后并行组 1（互不阻塞，按各自阶段完成）。

## Completion Matrix

| Stage | Scope | Implementation | Plan | Review/Recheck | Completion Record | Git Evidence | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | Repository Foundation Quality Gate：Python/TS 工具链、依赖边界、CI 门禁 | `pyproject.toml`、`uv.lock`、`pnpm-lock.yaml`、`.importlinter*`、`tests/architecture/`（python+typescript 正反向夹具）、`.github/workflows/m0-quality.yml` | [PLAN-20260814-009（retrospective）](../../.cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md) | [RECHECK-20260814-009（retrospective）](../../.cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md) PASS_WITH_WARNINGS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `3cc6130`（08-11）；前身 `5045c59`（08-10） | DONE |
| M1 | Domain Kernel & Contract Assets：实体/值对象/枚举/状态机/Manifest+digest/UsageLedger/Artifact 校验 | `packages/domain/`、`adapters/contracts/`（7 loaders） | [PLAN-20260811-001](../../.cursor/plans/tasks/PLAN-20260811-001-m1-domain-kernel.md) | [RECHECK-20260811-001](../../.cursor/plans/rechecks/RECHECK-20260811-001-m1-domain-kernel.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `185a752`（08-11） | DONE |
| M2 | Protocol Compiler + Preflight：DAG/角色/模型/工具/工作区/预算/策略解析 | `packages/application/protocol_compile/` + `preflight/` | [PLAN-20260812-003](../../.cursor/plans/tasks/PLAN-20260812-003-m2-protocol-compiler-preflight.md) | [RECHECK-20260812-003](../../.cursor/plans/rechecks/RECHECK-20260812-003-m2-protocol-compiler-preflight.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `1035a64`（08-12） | DONE |
| M3 | Model Relay Compatibility：端点 CRUD/probe/eligibility/熔断/指纹/回退/脱敏 | `packages/application/model_relay/` + `policy/`、`adapters/relay/` | [PLAN-20260811-002](../../.cursor/plans/tasks/PLAN-20260811-002-m3-model-relay.md) | [RECHECK-20260811-002](../../.cursor/plans/rechecks/RECHECK-20260811-002-m3-model-relay.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `7bfcd3c`（08-11） | DONE |
| M4 | Role/Team/Task：26 Role fixtures/异构评审/TaskContract/HandoffBundle/权限 deny | `packages/domain/`（roles/tasks/team_plan/activation 增量）、`preflight/role_checks.py` | [PLAN-20260812-004](../../.cursor/plans/tasks/PLAN-20260812-004-m4-role-team-task.md) | [RECHECK-20260812-004](../../.cursor/plans/rechecks/RECHECK-20260812-004-m4-role-team-task.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `7c68e92`（08-12） | DONE |
| M5 | Ports + Fakes：14 Port/统一错误模型/12 Fake/contract suite | `packages/application/ports/`（M5 时 16 模块）、`adapters/fakes/` | [PLAN-20260812-005](../../.cursor/plans/tasks/PLAN-20260812-005-m5-ports-fakes.md) | [RECHECK-20260812-005](../../.cursor/plans/rechecks/RECHECK-20260812-005-m5-ports-fakes.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `c75db51`（08-12） | DONE |
| M5R | Upstream Qualification：OpenHands v1.42.0 源码审计/14 Port 现实校验/6 spikes/revision lock | `tools/upstream-spikes/`（S1-S6）、`docs/references/upstream/`（7 文档 + revision lock） | [PLAN-20260812-006](../../.cursor/plans/tasks/PLAN-20260812-006-m5r-upstream-qualification.md) | [RECHECK-20260812-006](../../.cursor/plans/rechecks/RECHECK-20260812-006-m5r-upstream-qualification.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `717545d` + `5fc23d0`（08-12/13） | DONE |
| M6 | OpenHands Runtime Adapter：6 方法 Protocol/LLM Relay/cancel 收敛/Policy Wrapper/错误映射/Workspace 安全/Usage 入账 | `adapters/openhands/`（12 模块）、`packages/application/run_orchestration/` 初版 | [PLAN-20260813-007](../../.cursor/plans/tasks/PLAN-20260813-007-m6-openhands-runtime-adapter.md) | [RECHECK-20260813-007](../../.cursor/plans/rechecks/RECHECK-20260813-007-m6-openhands-runtime-adapter.md) PASS | [COMPLETION_MATRIX_M0_M7.md 行](COMPLETION_MATRIX_M0_M7.md) | `f4b2168`（08-13） | DONE |
| M7 | Reliable Mock Vertical Slice：E2E 编排链 + SQLite 持久化 + 故障注入矩阵 | `packages/application/run_orchestration/`、`adapters/sqlite/`、`examples/protocols/sort_analysis_v1.yaml` | [PLAN-20260814-010（retrospective）](../../.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md) + [PLAN-20260814-011](../../.cursor/plans/tasks/PLAN-20260814-011-m7-quality-gate-closure.md) | [RECHECK-20260814-010（retrospective）](../../.cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md) + [RECHECK-20260814-011](../../.cursor/plans/rechecks/RECHECK-20260814-011-m7-quality-gate-closure.md) PASS | [M7_COMPLETION_RECORD.md](M7_COMPLETION_RECORD.md) | `782887d` + `52c8b8b`（08-14） | DONE |
| M8 | Research Capability Plane：Tool Plane + Skill Registry + MCP adapter | `packages/application/tool_plane/`、`skill_registry/`、`adapters/mcp/`、`packages/application/ports/tool_pack_store.py` | [PLAN-20260814-012](../../.cursor/plans/tasks/PLAN-20260814-012-m8-research-capability-plane.md) | [RECHECK-20260814-012](../../.cursor/plans/rechecks/RECHECK-20260814-012-m8-research-capability-plane.md) PASS + [RECHECK-20260814-013（独立复审）](../../.cursor/plans/rechecks/RECHECK-20260814-013-m8-independent-recheck.md) | [M8_COMPLETION_RECORD.md](M8_COMPLETION_RECORD.md) | `4c2c16d`（08-14） | DONE |
| M9 | Real Experiment Runtime：容器执行 + ExperimentRun 生命周期 + ReproducibilityAudit | `adapters/execution/`、`adapters/workspace/`、`packages/domain/experiments.py`、`packages/application/experiments/` | [PLAN-20260815-013](../../.cursor/plans/tasks/PLAN-20260815-013-m9-real-experiment-runtime.md) | [RECHECK-20260815-013](../../.cursor/plans/rechecks/RECHECK-20260815-013-m9-real-experiment-runtime.md) PASS | [M9_COMPLETION_RECORD.md](M9_COMPLETION_RECORD.md) | `4156238` + `b8560ee`（08-15） | DONE |
| M10 | Evidence / Memory / Provenance：EvidenceLedger + Memory gate 全链路 + 可重建检索投影 | `packages/application/evidence/`、`memory/`、`packages/application/ports/{evidence_ledger,retrieval_index}.py`、`adapters/index/` | [PLAN-20260815-015（retrospective）](../../.cursor/plans/tasks/PLAN-20260815-015-m10-evidence-memory-retrospective.md) | [RECHECK-20260815-015（retrospective）](../../.cursor/plans/rechecks/RECHECK-20260815-015-m10-evidence-memory-retrospective.md) PASS | [M10_COMPLETION_RECORD.md](M10_COMPLETION_RECORD.md) | `900c1b1`（08-15） | DONE |
| M11 | Evaluation Plane：Eval Harness + deterministic gates + reviewer/panel + regression/canary/calibration + CI 门禁 | `packages/domain/eval_{spec,result,report_codec,gate}.py`、`packages/application/evaluation/`、`adapters/cli/eval_gate.py`、`schemas/eval-*.schema.json` | [PLAN-20260815-014](../../.cursor/plans/tasks/PLAN-20260815-014-m11-evaluation-plane.md) | [RECHECK-20260815-014](../../.cursor/plans/rechecks/RECHECK-20260815-014-m11-evaluation-plane.md) PASS | [M11_COMPLETION_RECORD.md](M11_COMPLETION_RECORD.md) | `0846765` + `0cc6361`（08-15） | DONE |

## 工程记录覆盖

- 原开发窗口记录（Plan + Recheck PASS + Memory）：M1、M3、M2、M4、M5、
  M5R、M6、M8（含独立复审 RECHECK-013）、M9、M11。
- Retrospective Reconstruction（事后重建，证据来源为 git history、完成
  记录、当前代码/测试与重跑的 validator）：M0（2026-08-14）、M7
  （2026-08-14）、M10（2026-08-16，DOC-R1）。
- 工程记忆：M0–M8 有 MEM 条目；M9、M10、M11 无 MEM 条目（覆盖缺口，
  见 `DOCUMENT_RECOVERY_M0_M11.md` remaining risks）。
- 全部阶段 DoD 证据见各 completion record 与上表测试/validator 列；每个
  DONE 均通过 m0 profile 全量回归。

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
→ M8（Research Capability Plane）  ∥ M9（Real Experiment Runtime） ∥
  M10（Evidence/Memory/Provenance） ∥ M11（Evaluation Plane）
→ IG-1（M12 entry：M8+M9+M10+M11 全部独立复审通过 + m0 profile 全绿）
```

## 正式工程状态

```text
Foundation / Executable Research Kernel（M0-M7 含 M5R）= completed
MVP 能力平面（M8-M11）= completed（2026-08-15）
IG-1（M12 entry）前置 = 齐备
```

M0–M7 的完成事实细节保留在 `COMPLETION_MATRIX_M0_M7.md`（本矩阵的前身，
历史行不回改）；M8–M11 细节见各阶段 completion record。未来里程碑
（M12–M19）的编号、名称、顺序与依赖 DAG 以
[MILESTONES.md](MILESTONES.md) 的 Post-M7 Roadmap 节为唯一权威；执行
映射见根 `BACKLOG.md`。

## 证据来源与边界

- 本矩阵仅记录可执行证据；不包含任何对开发窗口内讨论、评审或时间线的
  重构（M0/M7/M10 的 retrospective 记录为事后重建，链接指向对应计划
  文件并在其中显式标注 `RETROSPECTIVE_RECONSTRUCTION: true`）。
- M11 完成记录为 DOC-R1 依据 repository evidence 重建
  （`Reconstructed from repository evidence` 标注在文件头）。
- 发现但未纳入本表的历史文档不一致由 DOC-R1 修正并在
  [CHANGELOG](../../CHANGELOG.md) 与
  [DOCUMENT_RECOVERY_M0_M11.md](DOCUMENT_RECOVERY_M0_M11.md) 中记录。