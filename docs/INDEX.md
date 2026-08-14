# Documentation Index — v0.4.0

## 当前工程状态

```text
Foundation / Executable Research Kernel = completed（M0-M7 含 M5R，2026-08-14）
```

真实完成顺序 `M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7`（M3 先于
M2：M2 Preflight 消费 M3 Model Relay 产物）。M7 后进入产品能力建设阶段；
已完成事项 / 技术债 / 下一能力见 `../BACKLOG.md`。

## 快速问答（新 Agent 起步）

1. **Research OS 是什么？** → [PRODUCT.md](PRODUCT.md)、[架构总览](architecture/SYSTEM_ARCHITECTURE.md)
2. **当前实现到哪里？** → `../README.md` 当前工程状态、本节状态行
3. **M0-M7 做了什么？** → [Completion Matrix](roadmap/COMPLETION_MATRIX_M0_M7.md)
4. **当前架构是什么？** → [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)、[PORTS.md](architecture/PORTS.md)
5. **哪些 Contracts 已稳定？** → [PORTS.md](architecture/PORTS.md)、`../schemas/`、`../UPSTREAM_COMPONENTS.yaml`
6. **OpenHands 在哪里？** → [OPENHANDS_ADAPTER.md](integration/OPENHANDS_ADAPTER.md)、[AGENT_RUNTIME.md](architecture/AGENT_RUNTIME.md)
7. **upstream 研究在哪里？** → [Open Source / Upstream](#open-source--upstream) 节
8. **当前下一阶段是什么？** → `roadmap/MILESTONES.md` Post-M7 Roadmap 节（唯一权威）；执行映射见 `../BACKLOG.md`
9. **BACKLOG 在哪里？** → `../BACKLOG.md`
10. **如何验证当前仓库？** → `../README.md` 校验节（m0 profile 全量回归 + validators）

## Start

- `../README.md`
- `../AGENTS.md`
- `../CODEX_BOOTSTRAP.md`
- `PRODUCT.md`

## Contract / Decision Assets

- [Accepted ADRs](adr/)
- [JSON Schemas](../schemas/)
- [Configuration and contract examples](../examples/)
- [Pinned/planned upstream component registry](../UPSTREAM_COMPONENTS.yaml)

## Product

- `product/END_TO_END_USER_JOURNEY.md`
- `product/CONSOLE_INFORMATION_ARCHITECTURE.md`

## Architecture

- `architecture/SYSTEM_ARCHITECTURE.md`
- `architecture/PORTS.md`
- `architecture/DOMAIN_MODEL.md`
- `architecture/DETERMINISTIC_SERIALIZATION.md`
- `architecture/ROLE_MODEL.md`
- `architecture/TASK_HANDOFF.md`
- `architecture/AGENT_RUNTIME.md`
- `architecture/AGENT_BACKENDS.md`
- `architecture/MODEL_COMPATIBILITY.md`
- `architecture/TOOL_RUNTIME.md`
- `architecture/WORKSPACE_RUNTIME.md`
- `architecture/CONTEXT_ENGINE.md`
- `architecture/CAPABILITY_SECURITY.md`
- `architecture/RESEARCH_PROTOCOL.md`
- `architecture/WORKFLOW_RELIABILITY.md`
- `architecture/BUDGET_QUOTA.md`
- `architecture/DATA_LIFECYCLE.md`
- `architecture/OBSERVABILITY.md`
- `architecture/DEPLOYMENT_PROFILES.md`
- `architecture/EVENT_MODEL.md`
- `architecture/EVALUATION.md`

## Roles / Configuration

- `catalog/SYSTEM_ROLES.md`
- `configuration/USER_CONFIGURATION.md`
- `configuration/TEAM_TEMPLATES.md`
- `configuration/AUTONOMY_AND_GATES.md`

## Security

- `security/THREAT_MODEL.md`
- `security/PLUGIN_TOOL_SUPPLY_CHAIN.md`
- `security/SECRET_MANAGEMENT.md`
- `security/IDENTITY_AND_ACCESS.md`

## Governance

- `governance/DATA_GOVERNANCE.md`
- `governance/RESEARCH_INTEGRITY.md`

## Operations

- `operations/OPERATIONS_RUNBOOK.md`
- `operations/BACKUP_RECOVERY.md`
- `operations/SLO_AND_CAPACITY.md`

## Reliability

- `reliability/RUN_STATE_MACHINE.md`
- `reliability/CIRCUIT_BREAKER.md`
- `reliability/FAILURE_MODEL.md`

## Integrations

- `integration/LLM_ENDPOINTS.md`
- `integration/MODEL_GATEWAY.md`
- `integration/MODEL_PROBE.md`
- `integration/OPENHANDS_ADAPTER.md`
- `integration/MCP_TOOL_PROVIDERS.md`
- `integration/POLICY_ENGINE.md`
- `integration/WORKFLOW_ENGINE.md`

## Evaluation

- `evaluation/EVAL_HARNESS.md`
- `evaluation/QUALITY_GATES.md`

## API / Storage

- `api/CONTROL_PLANE_API.md`
- `api/EVENT_STREAM_API.md`
- `storage/DATABASE_SCHEMA.md`
- `storage/ARTIFACT_STORE.md`

## Open Source / Upstream

- `references/OPEN_SOURCE_REUSE_AUDIT.md`
- `references/UPSTREAM_FINDINGS_V0_4_0.md`
- `references/LICENSE_MATRIX.md`
- `references/SOURCE_SNAPSHOT.md`
- `references/UPSTREAM_POLICY.md`
- `references/upstream/OPENHANDS_REVISION_LOCK.yaml` — OpenHands SDK v1.42.0 机器可读 revision lock（M5R 锁定；M6 ADOPTED）
- `references/upstream/OPENHANDS_SOURCE_AUDIT.md` — OpenHands SDK 源码级审计（M5R）
- `references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md` — M5 Port 现实校验矩阵（M5R）
- `references/upstream/M5_CORRECTIONS_LOG.md` — M5 修正记录（零代码修正，M5R；M6 实施增补 M6-1..M6-5）
- `references/upstream/M6_ADAPTER_DESIGN_NOTES.md` — M6 Adapter 设计承接（M5R）
- `references/upstream/M6_RISK_REGISTER.md` — M6 风险登记（M5R）
- `references/upstream/M6_READINESS_REPORT.md` — M6 Readiness 报告（M5R；M6 完成后基线更新 2026-08-13）

## Roadmap / Versioning

- `../CODEX_BOOTSTRAP.md` — canonical milestone details and M0 quality gate
- `../BACKLOG.md` — implementation projection（Completed / Tech Debt / Next Capability）
- `roadmap/COMPLETION_MATRIX_M0_M7.md` — M0-M7/M5R 完成事实矩阵（阶段、证据、commit、状态）
- `roadmap/M7_COMPLETION_RECORD.md` — M7 Integration Milestone 完成记录（E2E chain 逐项证据）
- `roadmap/VERTICAL_SLICE_V0_4_0.md`
- `roadmap/MILESTONES.md` — M0-M7 执行索引 + Post-M7 Roadmap 唯一权威（M8-M19 编号/名称/顺序/依赖 DAG/分层/Evaluation 规则/upstream 时间表/下一阶段推荐）
- `versioning/VERSION_POLICY.md`

## 阶段工程记录（Plan / Recheck）

- 活动与最近完成计划索引：`../.cursor/plans/ALL_PLAN.md`
- M0 retrospective（2026-08-14 重建，`RETROSPECTIVE_RECONSTRUCTION`）：`../.cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md` + `../.cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md`
- M7 retrospective（2026-08-14 重建，`RETROSPECTIVE_RECONSTRUCTION`）：`../.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md` + `../.cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md`
- M1-M6/M5R 原开发窗口记录（Plan + PASS Recheck + Memory）见各自 plan 文件与 `../.cursor/memory/INDEX.md`
