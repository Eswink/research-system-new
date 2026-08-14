# Milestones v0.4.0

`CODEX_BOOTSTRAP.md` 是里程碑详细定义；本文件提供同一编号体系的执行索引
与完成状态，不维护第二套阶段语义。

## 当前状态

```text
Foundation / Executable Research Kernel = completed（M0-M7 含 M5R，2026-08-14）
```

完成矩阵与证据见 [COMPLETION_MATRIX_M0_M7.md](COMPLETION_MATRIX_M0_M7.md)；
M7 集成里程碑记录见 [M7_COMPLETION_RECORD.md](M7_COMPLETION_RECORD.md)。
M7 之后进入产品能力建设阶段（根 `BACKLOG.md`）。

## 真实完成顺序

```text
M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7
```

与数字编号不一致：**M3 先于 M2**（M2 Preflight 的 Model eligibility 消费
M3 Model Relay 产物）。文档以真实依赖关系为准，不按编号改写历史。

## Milestone Index

| Stage | 范围 | 完成 | Status | 证据 |
| --- | --- | --- | --- | --- |
| M0 | Repository Foundation Quality Gate：可复现 Python/TypeScript 工具链、`domain/application/adapter/entry` 依赖边界、architecture/contract test 入口、Windows/Linux CI 门禁 | 2026-08-11 | DONE | commit `3cc6130`；[retrospective plan](../../.cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md) |
| M1 | Domain Kernel & Contract Assets：实体/值对象/枚举/状态机/RunManifest/Revision/digest/loaders | 2026-08-11 | DONE | commit `185a752`；[PLAN-20260811-001](../../.cursor/plans/tasks/PLAN-20260811-001-m1-domain-kernel.md)；[RECHECK-20260811-001](../../.cursor/plans/rechecks/RECHECK-20260811-001-m1-domain-kernel.md) |
| M3 | Model Relay Compatibility：用户中转站/ModelDefinition/probe/eligibility/health/熔断/fingerprint/脱敏 | 2026-08-11 | DONE | commit `7bfcd3c`；[PLAN-20260811-002](../../.cursor/plans/tasks/PLAN-20260811-002-m3-model-relay.md)；[RECHECK-20260811-002](../../.cursor/plans/rechecks/RECHECK-20260811-002-m3-model-relay.md) |
| M2 | Protocol Compiler + Preflight：Role/Agent/Model/Tool/Workspace/Budget/Policy resolution → CompiledRunPlan/PreflightReport | 2026-08-12 | DONE | commit `1035a64`；[PLAN-20260812-003](../../.cursor/plans/tasks/PLAN-20260812-003-m2-protocol-compiler-preflight.md)；[RECHECK-20260812-003](../../.cursor/plans/rechecks/RECHECK-20260812-003-m2-protocol-compiler-preflight.md) |
| M4 | Role/Team/Task：26 Role fixtures、TeamTemplate、per-Agent binding、TaskContract/AcceptanceCriteria/HandoffBundle | 2026-08-12 | DONE | commit `7c68e92`；[PLAN-20260812-004](../../.cursor/plans/tasks/PLAN-20260812-004-m4-role-team-task.md)；[RECHECK-20260812-004](../../.cursor/plans/rechecks/RECHECK-20260812-004-m4-role-team-task.md) |
| M5 | Ports + Fakes：14 inward-owned Ports、统一错误模型、12 Fake、contract suite | 2026-08-12 | DONE | commit `c75db51`；[PLAN-20260812-005](../../.cursor/plans/tasks/PLAN-20260812-005-m5-ports-fakes.md)；[RECHECK-20260812-005](../../.cursor/plans/rechecks/RECHECK-20260812-005-m5-ports-fakes.md) |
| M5R | Upstream Qualification：OpenHands v1.42.0 源码审计、14 Port 现实校验、S1-S6 spikes、revision lock | 2026-08-12/13 | DONE | commits `717545d`/`5fc23d0`；[PLAN-20260812-006](../../.cursor/plans/tasks/PLAN-20260812-006-m5r-upstream-qualification.md)；[RECHECK-20260812-006](../../.cursor/plans/rechecks/RECHECK-20260812-006-m5r-upstream-qualification.md) |
| M6 | OpenHands Runtime Adapter：用户中转站 → OpenHands Native Agent → frozen Tool Set → safe Workspace；Policy Wrapper/cancel/错误映射 | 2026-08-13 | DONE | commit `f4b2168`；[PLAN-20260813-007](../../.cursor/plans/tasks/PLAN-20260813-007-m6-openhands-runtime-adapter.md)；[RECHECK-20260813-007](../../.cursor/plans/rechecks/RECHECK-20260813-007-m6-openhands-runtime-adapter.md) |
| M7 | Reliable Mock Vertical Slice：Compile → Preflight → Freeze → Lease/Idempotency/Outbox → Agent Session → Tool/Artifact/Evidence/Evaluation，故障注入 F-01..F-12 | 2026-08-14 | DONE | commit `782887d`；[retrospective plan](../../.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md)；[M7_COMPLETION_RECORD.md](M7_COMPLETION_RECORD.md) |

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

## 里程碑详细定义

M0-M7 各阶段的原始定义保留在 `CODEX_BOOTSTRAP.md`（canonical milestone
details）与 [VERTICAL_SLICE_V0_4_0.md](VERTICAL_SLICE_V0_4_0.md)
（M7 场景/故障/DoD）；本文件不重复正文。