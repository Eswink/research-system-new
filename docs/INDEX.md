# Documentation Index — v0.4.0

## 当前工程状态

```text
Foundation / Executable Research Kernel（M0-M7 含 M5R）= completed
MVP 能力平面（M8-M11）= completed（2026-08-15）
M12 First Real Research Workflow = completed（R1 修复 + 2026-08-28 重判 PASS，RECHECK-20260828-023；DoD-3 live relay 凭据闭环）
M13 Research Console = completed（R1 修复 + 独立复审 PASS，2026-08-27）
M14 Durable Workflow + PostgreSQL = completed（2026-08-28；WP-J2 重判 PASS，见 `RECHECK-20260828-022`；Temporal DEFERRED，见 ADR-0025）
M15 Observability / Cost / Eval Operations = completed（2026-08-29 首轮；2026-08-30 独立复审判定 FAIL 后修复轮 WP0–WP8 完成，6 BLOCKER 独立探针复现修复，m0 23/23 全绿；recheck PASS 见 `RECHECK-20260830-024`；ADR-0026 无内容通道观测、五状态成本投影、EvalReportStore/趋势已落地）
M16 Distributed Execution + Remote Sandbox/Worker = completed（2026-08-31；Worker 生命周期/认证、claim_next 分区 + fence、RemoteExecutionBackend + worker 子进程 E2E 场景 A–J、SWE-ReX REJECT、遥测/记账/Console cluster 视图；ADR-0027；attempt-2 独立对抗复审 PASS 2026-09-01，RECHECK-20260901-025-m16-attempt2；证据见 `roadmap/M16_COMPLETION_RECORD.md`）
RM-P2 Personal Roadmap Rebaseline = completed（2026-09-02，ADR-0028）：M17 收缩为 Remote GPU Execution / Personal Scale Baseline；M18/M19 DEFERRED；新增 SI-1 / PA-1 / PA-1R 与 Usage-driven Development；权威见 `roadmap/MILESTONES.md`
M17 Remote GPU Execution = completed（2026-09-02，ADR-0029）：真实单卡 GPU 全链 VERIFIED（capability 发现/GPU 调度/真实 CUDA 执行/无静默 CPU fallback/OOM·取消/Artifact·Evidence·Evaluation·Usage/可复现性）；physically-remote GPU host = NOT VERIFIED/DEFERRED；证据见 `roadmap/M17_COMPLETION_RECORD.md`
SI-1 Personal Scale Integration Review = PASS（2026-09-02）：真实 GPU Research Run、跨阶段回归与六类故障面均有证据
PA-1 Personal Production Acceptance = PASS（2026-09-03）：reproducible deployment / PostgreSQL+Artifact 实际 backup+restore / secret hygiene / Remote+GPU worker recovery / restart durability / 真实 GPU Research Acceptance Run / version identity / operational docs；证据见 `roadmap/PA1_COMPLETION_RECORD.md`
PA-1R Independent Personal Production Re-audit = PASS（2026-09-06）：Personal Production Baseline = COMPLETE；固定 Milestone 主线暂停，进入 Usage-driven Development；M18/M19 继续 DEFERRED
```

真实完成顺序 `M0 → M1 → M3 → M2 → M4 → M5 → M5R → M6 → M7 → M8 → M9 →
M10 → M11 → M12 → M13 → M14 → M15 → M16`（M3 先于 M2：M2 Preflight 消费 M3 Model Relay 产物；
M8-M11 为 M7 后并行组 1；M12 PASS 判定曾经 M12-R1 独立复审证伪并修复，
2026-08-28 重新独立复审重判 PASS（RECHECK-20260828-023））。已完成事项 /
技术债 / 下一能力见 `../BACKLOG.md`。

## 快速问答（新 Agent 起步）

1. **Research OS 是什么？** → [PRODUCT.md](PRODUCT.md)、[架构总览](architecture/SYSTEM_ARCHITECTURE.md)
2. **当前实现到哪里？** → `../README.md` 当前工程状态、本节状态行
3. **M0-M11 做了什么？** → [Completion Matrix](roadmap/COMPLETION_MATRIX_M0_M11.md)
4. **当前架构是什么？** → [SYSTEM_ARCHITECTURE.md](architecture/SYSTEM_ARCHITECTURE.md)、[PORTS.md](architecture/PORTS.md)
5. **哪些 Contracts 已稳定？** → [PORTS.md](architecture/PORTS.md)、`../schemas/`、`../UPSTREAM_COMPONENTS.yaml`
6. **OpenHands 在哪里？** → [OPENHANDS_ADAPTER.md](integration/OPENHANDS_ADAPTER.md)、[AGENT_RUNTIME.md](architecture/AGENT_RUNTIME.md)
7. **怎么接一个真实端点 / 怎么退回 Fake？** → [LIVE_MODEL_RUNBOOK.md](integration/LIVE_MODEL_RUNBOOK.md)（登记、凭据注入与轮换、重启边界、切换与回退、仍是 demo 的面）
7. **upstream 研究在哪里？** → [Open Source / Upstream](#open-source--upstream) 节
8. **当前如何发起改进？** → [UD 使用驱动改进模板](roadmap/USAGE_DRIVEN_IMPROVEMENT_TEMPLATE.md)；固定 Milestone 主线暂停，重新激活条件见 `roadmap/MILESTONES.md`
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
- `frontend/UI_DESIGN_PROMPTS.md` — Console 页面/组件设计约束（M13；含 UI 验收条件）
- `frontend/CONSOLE_REBUILD.md` — Console 全站重建设计说明 v2（八域；PLAN-20260908-034；页面清单、设计控件→真实契约映射、主题/布局/状态/验收基准；v1 历史保留）
- `frontend/CONSOLE_PAGE_MAP.md` — 33 规范路由逐页/逐操作 API-DTO 映射与后端能力缺口 G1–G14（PLAN-20260908-034 T02）
- `frontend/CONSOLE_DELIVERY.md` — 高保真重建交付清单：完成度、行为保证、测试命令、旧路由兼容、回退、视觉对照（PLAN-20260908-034 T32）
- `frontend/CONSOLE_FONTS.md` — 自托管字体来源、许可证（OFL-1.1）、版本与内容摘要（PLAN-20260908-034 T04）

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
- `architecture/SKILL_REGISTRY.md`
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
- `architecture/POLICY_SURFACE_AUDIT.md`

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

- `operations/REPOSITORY_HYGIENE.md` — 根目录分类归档规则：固定根锚点、专责目录、可再生垃圾与受保护本地状态
- `operations/RESEARCH_COMPOSE.md` — 默认无外网/无 Docker Socket 的六个研究服务加无凭据 loopback 代理
- `operations/PERSONAL_DEPLOYMENT.md`
- `operations/OPERATIONS_RUNBOOK.md`
- `operations/BACKUP_RECOVERY.md`
- `operations/SLO_AND_CAPACITY.md`

## Reliability

- `reliability/RUN_STATE_MACHINE.md`
- `reliability/CIRCUIT_BREAKER.md`
- `reliability/FAILURE_MODEL.md`

## Integrations

- `integration/LLM_ENDPOINTS.md`
- `integration/LIVE_MODEL_RUNBOOK.md`
- `integration/MODEL_GATEWAY.md`
- `integration/MODEL_PROBE.md`
- `integration/OPENHANDS_ADAPTER.md`
- `integration/MCP_TOOL_PROVIDERS.md`
- `integration/POLICY_ENGINE.md`
- `integration/WORKFLOW_ENGINE.md`

## Evaluation

- `evaluation/EVAL_HARNESS.md`
- `evaluation/QUALITY_GATES.md`
- `../packages/domain/eval_spec.py` / `../packages/domain/eval_result.py` / `../packages/domain/eval_gate.py` — M11 评测域契约（EvalCase/EvalDataset freeze digest、EvalReport、版本化 GateConfig）
- `../packages/application/evaluation/` — M11 Evaluation Plane 应用层（scorers/runner/reviewer/panel/regression/canary/calibration/report）
- `../schemas/eval-dataset.schema.json` — 评测数据集契约
- `../schemas/eval-score.schema.json` — EvalScore 报告契约
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
- `references/upstream/M8_MCP_QUALIFICATION.md` — MCP ecosystem qualification（M8；mcp==1.29.0 v1 stable line ADOPTED）
- `references/upstream/M9_DOCKER_QUALIFICATION.md` — Docker 执行沙盒 qualification（M9；docker-py 7.2.0 + sandbox Dockerfile ADOPTED，OpenHands DockerWorkspace mapping-only 裁决）
- `references/upstream/M11_EVAL_HARNESS_QUALIFICATION.md` — Evaluation harness 选型 qualification（M11；native 自建，不引入外部 eval framework）
- `references/upstream/M14_TEMPORAL_QUALIFICATION.md` — Temporal qualification 16Q matrix（M14；DEFERRED）
- `references/design/protocol-visual-editor/ARCHIVE_NOTE.md` — 协议可视化编辑器设计参考归档（PLAN-20260908-033；设计参考非产品契约）
- `references/upstream/M15_OTEL_QUALIFICATION.md` — OpenTelemetry qualification（M15；ADOPT：OTLP/HTTP，无内容通道）
- `references/upstream/CURSOR_SDK_QUALIFICATION.md` — Cursor SDK qualification（并行编排工具；ADOPT：BUILD_TOOLING，read-only 编排器）
- `adr/ADR-0026-otel-adapter-boundary.md` — OTel adapter 边界 + 无内容 Debug Mode 决策（M15）
- `references/upstream/M16_REMOTE_EXECUTION_QUALIFICATION.md` — 远程执行 qualification（M16；SWE-ReX REJECT，原生 HTTP worker 交付）
- `adr/ADR-0027-distributed-execution-plane.md` — Distributed Execution Plane 决策（M16；Worker untrusted、Control Plane 独占授权、HTTP worker gateway、不建第二队列/租约/Artifact 真相）
- `adr/ADR-0028-personal-scale-rebaseline.md` — Personal Scale Rebaseline 决策（RM-P2；M17 收缩为 Remote GPU Execution / Personal Scale Baseline、M18/M19 DEFERRED、SI-1/PA-1/PA-1R、Usage-driven Development）
- `references/upstream/M17_GPU_RUNTIME_QUALIFICATION.md` — GPU runtime qualification（M17；pytorch/pytorch 2.9.1-cuda12.8 digest pin、sm_89 实测、readonly-rootfs×nvidia-hook 无冲突、实际硬件事实块）
- `adr/ADR-0029-gpu-execution-boundary.md` — GPU Execution Boundary 决策（M17；单 token 调度键 vs 观测分离、freshness 四层、rootfs 不放开、无静默 CPU fallback 四层、physically-remote NOT VERIFIED）
- `roadmap/M15_COMPLETION_RECORD.md` — M15 完成记录（DoD 21/21 PASS）
- `adr/ADR-0025-temporal-defer.md` — Temporal deferral ADR（M14；DEFER 决策，M16 重评）
- `adr/ADR-0030-validation-failure-consumption.md` — 验收门拒收的处置（**Proposed / 待拍板**：`on_validation_failure` 的消费为何仍未做、选项 A–E 的代价与收益、触发条件；GOAL-20260918-006 EC-02 草案）
- `adr/ADR-0031-toolpack-capability-policy.md` — ToolPack 能力策略与「事实名 → 合约名」声明（**Proposed / 待拍板**：`tool_pack.*` 为何默认 DENY、`action: TOOL_PACK_INSTALL_OR_UPDATE` 为何按构造不可匹配、`session_message` 与 `analysis_report` 的声明权归谁；选项与代价、触发条件；GOAL-20260919-007 EC-06 草案）

## Roadmap / Versioning

- `../CODEX_BOOTSTRAP.md` — canonical milestone details（M0-M7）and M0 quality gate
- `../BACKLOG.md` — implementation projection（Completed / Tech Debt / Next Capability）
- `roadmap/COMPLETION_MATRIX_M0_M11.md` — M0-M11/M5R 完成事实总表（唯一权威；阶段、证据、commit、状态）
- `roadmap/COMPLETION_MATRIX_M0_M7.md` — M0-M7 原始完成矩阵（历史行保留，已被 M0_M11 矩阵取代为唯一权威）
- `roadmap/M7_COMPLETION_RECORD.md` — M7 Integration Milestone 完成记录（E2E chain 逐项证据）
- `roadmap/M8_COMPLETION_RECORD.md` — M8 Research Capability Plane 完成记录
- `roadmap/M9_COMPLETION_RECORD.md` — M9 Real Experiment Runtime 完成记录（DoD 证据 + M12/M17 readiness）
- `roadmap/M10_COMPLETION_RECORD.md` — M10 Evidence / Memory / Provenance 完成记录（DoD 证据 + 独立复审 5 缺陷表）
- `roadmap/M11_COMPLETION_RECORD.md` — M11 Evaluation Plane 完成记录（DoD 证据 + 反作弊专项；DOC-R1 依据 repository evidence 重建）
- `roadmap/M12_COMPLETION_RECORD.md` — M12 First Real Research Workflow 完成记录与 MVP 判定（真实工具/实验/证据/评测/预算闭环；原 PASS 判定经 M12-R1 独立复审证伪，见下行）
- `roadmap/M12_R1_COMPLETION_RECORD.md` — M12-R1 Production Truth Closure 修复记录（独立复审 FAIL 后 13 Finding → Fix → Regression → Revalidation；记录保留当时“待重判”结论，后续已于 2026-08-28 独立复审重判 PASS）
- `roadmap/M13_R1_COMPLETION_RECORD.md` — M13-R1 Research Console 修复记录（独立复审 3 BLOCKER + 7 MAJOR + 4 UI Scope + 6 MINOR → Fix → Regression → 独立复审重判 PASS）
- `roadmap/VERTICAL_SLICE_V0_4_0.md`
- `roadmap/MILESTONES.md` — M0-M11 执行索引 + Post-M7 Roadmap 唯一权威（M12-M19 编号/名称/顺序/依赖 DAG/分层/Evaluation 规则/upstream 时间表；RM-P2 2026-09-02 起：M17 = Remote GPU Execution / Personal Scale Baseline，M18/M19 DEFERRED；SI-1/PA-1/PA-1R 已完成，PA-1R 2026-09-06 PASS 后固定 Milestone 主线暂停）
- `roadmap/USAGE_DRIVEN_IMPROVEMENT_TEMPLATE.md` — Post-baseline 的 UD 使用驱动改进入口（真实使用证据、问题分类、最小范围、regression/Evaluation/真实 Research re-run/文档完成门禁，以及 M18/M19/HPC 重新激活条件）
- `roadmap/M0_M11_DOCUMENT_MATRIX.md` — DOC-R1 inventory（M0-M11 文档分类与恢复判定）
- `roadmap/DOCUMENT_RECOVERY_M0_M11.md` — DOC-R1 最终报告（inventory/重建/修正/验证结果/remaining risks）
- `audits/SYSTEM_AUDIT_M0_M11.md` — SA-1 Pre-M12 全系统审计与加固（2026-08-20；Audit Coverage Matrix / BLOCKER+MAJOR+MINOR findings / Fault Injection evidence / 延期技术债 / PASS + M12 READY）
- `audits/MIMOSA_DEEP_SCAN_20260917.md` — Mimosa 密封深扫终态记录（2026-09-17，GOAL-004 cycle 8 = EC-07；scanId + seal + 逐件摘要复核 + 36 条 findings 逐条处置 + 未覆盖范围；**不主张项目安全**）
- `audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md` — 收口后安全复核（2026-09-18，GOAL-005 cycle 1 = EC-01；干净 checkout 重扫封印 + 依赖 advisory 联网复核署名 + hook 侧 `scanner_enobufs` 根因 + 25 条 findings 逐条处置 + 动态 SQL 结构判据更正；**不主张项目安全**）
- `audits/MIMOSA_DEPENDENCY_ADVISORIES_20260918.json` — 依赖 advisory 复核证据（413 个锁定包的 OSV 查询：3 包 20 条，含 CVE 别名 / CVSS / 修复版本 / 来源与复跑命令）
- `versioning/VERSION_POLICY.md`

## 阶段工程记录（Plan / Recheck）

- 活动与最近完成计划索引：`../.cursor/plans/ALL_PLAN.md`
- M0 retrospective（2026-08-14 重建，`RETROSPECTIVE_RECONSTRUCTION`）：`../.cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md` + `../.cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md`
- M7 retrospective（2026-08-14 重建，`RETROSPECTIVE_RECONSTRUCTION`）：`../.cursor/plans/tasks/PLAN-20260814-010-m7-vertical-slice-retrospective.md` + `../.cursor/plans/rechecks/RECHECK-20260814-010-m7-vertical-slice-retrospective.md`
- M10 retrospective（2026-08-16 重建，`RETROSPECTIVE_RECONSTRUCTION`，DOC-R1）：`../.cursor/plans/tasks/PLAN-20260815-015-m10-evidence-memory-retrospective.md` + `../.cursor/plans/rechecks/RECHECK-20260815-015-m10-evidence-memory-retrospective.md`
- M12 retrospective（2026-08-28 重建，`RETROSPECTIVE_RECONSTRUCTION`）：`../.cursor/plans/tasks/PLAN-20260828-017-m12-first-real-research-workflow.md` + `../.cursor/plans/rechecks/RECHECK-20260828-017-m12-first-real-research-workflow.md`
- M13 retrospective（2026-08-28 重建，`RETROSPECTIVE_RECONSTRUCTION`）：`../.cursor/plans/tasks/PLAN-20260828-018-m13-research-console.md` + `../.cursor/plans/rechecks/RECHECK-20260828-018-m13-research-console.md`
- M12-R1 修复轮（2026-08-28 固化）：`../.cursor/plans/tasks/PLAN-20260828-019-m12-r1-production-truth-closure.md` + `../.cursor/plans/rechecks/RECHECK-20260828-019-m12-r1-production-truth-closure.md`
- M13-R1 修复轮（2026-08-28 固化）：`../.cursor/plans/tasks/PLAN-20260828-020-m13-r1-console-remediation.md` + `../.cursor/plans/rechecks/RECHECK-20260828-020-m13-r1-console-remediation.md`
- M14 完成（2026-08-28，重判 PASS）：`../.cursor/plans/tasks/PLAN-20260828-021-m14-durable-workflow-postgresql.md` + `../.cursor/plans/rechecks/RECHECK-20260828-022-m14-durable-workflow-postgresql.md`
- M1-M6/M5R/M8/M9/M11 原开发窗口记录（Plan + PASS Recheck + Memory 或 completion record）见各自 plan 文件与 `../.cursor/memory/INDEX.md`；M9/M10/M11 无 MEM 条目（覆盖缺口，见 `roadmap/DOCUMENT_RECOVERY_M0_M11.md`）
