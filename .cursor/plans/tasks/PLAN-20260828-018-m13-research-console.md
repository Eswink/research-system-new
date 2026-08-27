---
id: PLAN-20260828-018
slug: m13-research-console-retrospective
title: M13 Research Console（回顾重建）
status: DONE
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: c:\Users\googl\.cursor\plans\m13_adversarial_re-audit_ccd4616d.plan.md
owners:
  - root-agent
authorization:
  source: user-request
  ref: "补齐流程计划与文档对齐（2026-08-28 批准）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260828-018-m13-research-console.md
memory_entries: []
---

# PLAN-20260828-018 — M13 Research Console（回顾重建）

> 本文件为 `RETROSPECTIVE_RECONSTRUCTION` 记录：依据 `docs/roadmap/M13_R1_COMPLETION_RECORD.md`、git history（commit `e5270b2`/`b3f60a7`/`d5eb660`）、当前代码/测试与可执行 validator 事后重建，非原开发窗口文档。原始执行期工作文件为 `.cursor/plans/m13_console_remediation_405f5840.plan.md` 与 `.cursor/plans/m13_adversarial_re-audit_ccd4616d.plan.md`。

## 目标

记录并固化 M13 Research Console 的正式任务计划：让用户能配置、运行、监控、审批研究工作流（落地 ADR-0008 自主产品 UI），作为 Product 层里程碑。

## 范围

- 包含：
  - first-run relay wizard、models/probe page、team/agent model assignment
  - protocol/preflight dry run、task/run timeline、approvals/interventions
  - workspace diff（诚实降级）、evidence/claim map、budget/usage、audit/export
  - Control Plane API（`services/api/`）与 `apps/web/`（M0 TS 工具链）
- 不包含：
  - 多租户（M18）、分布式集群管理（M16）、评测面板生产化（M15）
  - UI 复制 Canonical State（只消费 API DTO）

## 架构与数据流

- 所有者模块：
  - Entry: `services/api/`（FastAPI Control Plane API：endpoints/models/agents/team/protocol/runs/approvals/inspection/experiments）+ `apps/web/`（React Console：wizard/Models/Team/Workspace/RunPanel）
  - Application/Port: `packages/application/ports/`（agent_store/project_settings_store/run_store/approval_store）+ `packages/application/preflight/`、`protocol_compile/`
  - Adapter: `adapters/sqlite/`（model_store/endpoint_store/agent_store/project_settings_store/run_store/approval_store/idempotency_store/budget_ledger）
- 输入：用户 relay 配置（Base URL + API Key + Model ID）、ProtocolDefinition、ProjectSettings、CatalogSnapshot（examples 基底 + SQLite 用户配置合并）
- 输出：Run 列表/时间线/SSE 事件流、dry-run 投影、approval 记录、claim map、experiments 只读聚合、audit/export
- Canonical State：SQLite（M13 控制面；PostgreSQL 属 M14）
- 关键接线：`catalog_merge.py::merged_catalog_snapshot()`（用户优先覆盖）、`preflight_support.py`（policy evaluator + endpoint health 注入）

## 验收条件

- [x] AC-01 first-run 向导端到端可用（discover/probe/手动添加；失败态不伪装成功）
- [x] AC-02 dry run 不触发真实副作用（spy 零调用）
- [x] AC-03 审批流 deny/approve 全链路（后端强制，UI 非绕过；semantic intervention 501 诚实边界）
- [x] AC-04 审计导出可用（export 字段与持久状态一致，无 secret 泄漏）
- [x] AC-05 架构测试证明 UI 只消费 API DTO（dependency-cruiser 无违规）
- [x] AC-06 TS lint/typecheck/依赖边界门禁 PASS；m0 profile 全绿
- [x] AC-07 M13 Scope 4 项 UI（Models/Probe、Team/Agent、Workspace Diff、Experiment View）均有真实视图或诚实 unavailable 标注
- [x] AC-08 独立复审重判 PASS（2026-08-27 adversarial re-audit：m0 19 checks、pytest 2054 passed）

## 实施清单

- [x] STEP-01 控制面 API 初版（`e5270b2`：endpoints/models/agents/team/protocol/runs/approvals/inspection + openapi.m13.json）
- [x] STEP-02 R1 修复轮 B1/B2/B3.x（`b3f60a7`：catalog 合并、toolpack digest、policy/health 接线、AgentStore/ProjectSettingsStore、wizard 完成）
- [x] STEP-03 R1 修复轮 M1..M6（`b3f60a7`：Sqlite 持久化、run 列表、claim 隔离、SSE、fingerprint）
- [x] STEP-04 R1 修复轮 S1..S5（`b3f60a7`：Models/Team/Workspace/Experiment 视图 + 导航收口）
- [x] STEP-05 R1 修复轮 P1..P6（`b3f60a7`：内联 import、intervention 语义、二次确认、degraded、测试判别力、可访问性基线）
- [x] STEP-06 Adversarial re-audit（`d5eb660`：usage 隔离、Relay wizard 入口、ANTHROPIC protocol、agnes 端点）+ 独立复审重判 PASS
- [x] STEP-07 Final Regression：m0 profile 19 checks + 22 节复审脚本重放 + M13_R1_COMPLETION_RECORD.md

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（回顾重建；re-audit 阶段使用 3 个只读 reviewer subagent） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-01 | test | `tests/api/test_catalog_merge.py`（5）；`apps/web/tests/unit/wizard-flow.test.ts`（7）；`apps/web/tests/unit/run-event-stream.test.ts`（4） | PASS |
| EV-02 | AC-02 | test | `tests/contracts/test_dry_run_no_side_effect.py` | PASS（spy 零调用） |
| EV-03 | AC-03 | test | `tests/api/test_approvals_api.py`（10）；`tests/api/test_idempotency_ifmatch.py` | PASS |
| EV-04 | AC-04 | test | `tests/api/test_secret_redaction.py`；`tests/api/test_security_scan.py`；`tests/api/test_inspection_usage_api.py`（3） | PASS |
| EV-05 | AC-05 | check | `pnpm run boundaries`（depcruise 44 modules） | PASS |
| EV-06 | AC-06 | check | `run_all_checks.py --profile m0`（19 checks） | PASS |
| EV-07 | AC-07 | file | `apps/web/src/features/models/ModelsPage.tsx`、`team/TeamPage.tsx`、`workspace/WorkspaceView.tsx`（含 ExperimentsBody） | 真实视图/诚实标注 |
| EV-08 | AC-08 | check | `docs/roadmap/M13_R1_COMPLETION_RECORD.md`；commit `d5eb660` | M13 PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-26 | 独立复审 FAIL（3 BLOCKER + 7 MAJOR + 4 UI + 6 MINOR） | M13 初版存在 wiring 缺口 | 启动 R1 修复轮 |
| 2026-08-27 | 独立复审重判 PASS | R1 修复 + adversarial re-audit 证据闭环 | M13 状态 DONE |
| 2026-08-28 | 回顾重建 | 补齐正式任务计划记录 | 本文件 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-25 | — | DONE（初版） | `e5270b2` 交付控制面 + Console | 完成记录 |
| 2026-08-26 | DONE | FAIL | 独立复审 3 BLOCKER | M13_R1_COMPLETION_RECORD |
| 2026-08-27 | FAIL | DONE | R1 修复 + adversarial re-audit PASS | `b3f60a7` + `d5eb660` |
| 2026-08-28 | — | DONE | 回顾重建完成并复检 PASS | 本文件 + RECHECK-20260828-018 |

## 影响报告

- Domain/API/schema：`LLMEndpoint.protocol` 增加 ANTHROPIC；openapi.m13.json（426 insertions）；新增 5 个 Control Plane 端点
- 安全/凭据：claim map 跨 run 隔离（MAJOR-M3 修复）；secret 十表面扫描无泄漏；key 不落盘
- 兼容性/迁移：SQLite 控制面持久化；Evidence/Memory 仍 SQLite（M14）
- 上游版本：agnes-ai.com relay（示例端点）；FakeModelGateway 仅测试/契约
- 下一项任务：M14 Durable Workflow + PostgreSQL（`PLAN-20260828-021`）
