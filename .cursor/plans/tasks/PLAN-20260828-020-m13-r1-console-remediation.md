---
id: PLAN-20260828-020
slug: m13-r1-console-remediation
title: M13-R1 Research Console 修复轮
status: DONE
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: c:\Users\googl\.cursor\plans\m13_console_remediation_405f5840.plan.md
owners:
  - root-agent
authorization:
  source: user-request
  ref: "补齐流程计划与文档对齐（2026-08-28 批准）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260828-020-m13-r1-console-remediation.md
memory_entries: []
---

# PLAN-20260828-020 — M13-R1 Research Console 修复轮

> 本文件记录 M13 独立复审 FAIL 后的修复轮正式计划。事实优先级：production code > Contracts > 可重复执行 > Git history > deterministic tests > audit evidence > 文档。不删除/不改写历史 Review；保留 M13 FAIL 事实（本记录为 R1 修复记录，不覆盖历史）。原执行期工作文件为 `.cursor/plans/m13_console_remediation_405f5840.plan.md`。

## 目标

对 M13 独立复审发现的 3 个 BLOCKER、7 个 MAJOR、MILESTONES.md 已声明但缺失的 4 项 UI 范围，以及全部 MINOR/打磨项执行完整修复，使 M13 达到其自身范围声明并通过独立复审重判。

## 范围

- 包含：
  - BLOCKER-B1：m0 profile 4 项 FAILED（lint/format/scripts 目录违规）
  - BLOCKER-B2：first-run wizard 端到端完成（discover/probe/失败态）
  - BLOCKER-B3.x：catalog 合并、toolpack digest、policy/health 接线、AgentStore/ProjectSettingsStore 持久化
  - MAJOR-M1..M6：Sqlite 持久化（run/approval/idempotency/budget）、run 列表、claim map 隔离、SSE 消费、fingerprint
  - Scope-S1..S5：Models/Probe、Team/Agent、Workspace Diff（诚实降级）、Experiment View、导航收口
  - MINOR-P1..P6：内联 import、intervention 语义、二次确认、degraded 处理、测试判别力、可访问性基线
- 不包含：M14/M15/M16/M18；PostgreSQL canonical state；OpenHands Agent Loop 切换（受控 Fake Runtime 保持并披露）

## 架构与数据流

- 所有者模块：
  - Entry: `services/api/`（catalog_merge.py、preflight_support.py、routers/runs.py、approvals.py、inspection.py、experiments.py）+ `apps/web/src/`（features/setup、models、team、workspace、runs）
  - Port: `packages/application/ports/{agent_store,project_settings_store,run_store,approval_store}.py`（兼容新增）
  - Adapter: `adapters/sqlite/{run_store,approval_store,idempotency_store,budget_ledger,agent_store,project_settings_store}.py`
- 输入：用户 wizard 配置（SQLite）+ examples 基底目录；ToolPack manifest（ncbi_eutils digest `sha256:947cbb…`）
- 输出：Run 列表/时间线/SSE、dry-run 投影、approval、claim map（run 隔离）、experiments 聚合、audit/export
- Canonical State：SQLite（M13 控制面）；M14 前不宣称 PostgreSQL
- 关键不变量：不伪造 digest/pin/diff；缺口诚实标注 degraded/unavailable；UI 只消费 API DTO

## 验收条件

- [x] AC-01 B1：m0 profile 全绿恢复（python 4 项 + TS + framework 全 PASS）
- [x] AC-02 B3：用户配置真实进入 preflight/run（preflight PASS、demo run SUCCEEDED）
- [x] AC-03 B2：wizard 空 DB 全流程可完成（失败态不伪装成功）
- [x] AC-04 M1/M2：控制面状态跨重启持久（run/approval/idempotency/budget）
- [x] AC-05 M3/M4/M6：claim 跨 run 隔离、SSE 实时/重连/去重、fingerprint 诚实
- [x] AC-06 S1-S5：4 项 UI 范围真实视图/诚实标注 + 导航无死链接
- [x] AC-07 P1-P6：MINOR 全部闭环
- [x] AC-08 独立复审重判 PASS（2026-08-27，m0 19 checks + 2054 passed）

## 实施清单

- [x] B1（门禁）→ B3（catalog/执行链核心）→ B2（wizard，依赖 B3）→ M1（持久化）→ M2（run 列表）→ M3/M4/M6（并行）→ S1/S2 → S3/S4 → S5 → P1-P6 → Final Regression
- [x] Final Regression：全量质量门禁重跑 + 22 节复审脚本重放 + M13_R1_COMPLETION_RECORD.md + 独立复审重判

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（修复轮以根代理串行为主；re-audit 阶段 3 个 reviewer 并行） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | B1 | check | `run_all_checks.py --profile m0`；`ruff check`；`ruff format --check`（501 files） | PASS |
| EV-02 | B3.0-B3.5 | test | `tests/api/test_catalog_merge.py`（5）；`test_team_protocol_api.py`（13）；`test_dry_run_no_side_effect.py` | PASS |
| EV-03 | B2 | test | `apps/web/tests/unit/wizard-flow.test.ts`（7）；`run-event-stream.test.ts`（4） | PASS |
| EV-04 | M1/M2 | test | `tests/contracts/test_m13_r1_store_contracts.py`（4）；`tests/api/test_api_restart_recovery.py`（5） | PASS |
| EV-05 | M3 | test | `tests/api/test_inspection_api.py::test_claim_map_does_not_leak_other_run_claims` | PASS |
| EV-06 | M6 | test | `tests/adapters/relay/test_responses_api.py`（2） | PASS |
| EV-07 | S1-S5 | file | `apps/web/src/features/{models,team,workspace}/`；`apps/web/src/App.tsx` | 真实视图 |
| EV-08 | P1-P6 | test | `tests/api/test_approvals_api.py`（10） | PASS |
| EV-09 | AC-08 | check | `docs/roadmap/M13_R1_COMPLETION_RECORD.md`；commit `b3f60a7` | M13 PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-26 | 独立复审 FAIL（3 BLOCKER + 7 MAJOR + 4 UI + 6 MINOR） | M13 初版 wiring 缺口 | 修复轮立项 |
| 2026-08-27 | 优先修 wiring 不重写 | FakeAgentRuntime 等语义保留，仅要求 UI 诚实披露 | 修复范围收敛 |
| 2026-08-27 | Workspace Diff 诚实降级 | adapter 层无文件级 manifest，不伪造 diff | remaining debt 记录 |
| 2026-08-28 | 正式计划固化 | 补齐流程计划记录 | 本文件 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-27 | — | DONE | B1/B2/B3/M1-M6/S1-S5/P1-P6 全部闭环 | commit `b3f60a7` |
| 2026-08-27 | DONE | DONE（重判 PASS） | adversarial re-audit `d5eb660` | M13_R1_COMPLETION_RECORD |
| 2026-08-28 | — | DONE | 计划固化 + 复检 PASS | 本文件 + RECHECK-20260828-020 |

## 影响报告

- Domain/API/schema：新增 5 个 Control Plane 端点（runs/agents/settings/experiments）；openapi.m13.json 426 insertions
- 安全/凭据：claim 跨 run 隔离（安全缺陷修复）；secret 十表面扫描；key 不落盘
- 兼容性/迁移：SQLite 控制面持久化（M14 前）；Evidence/Memory 仍 SQLite
- 上游版本：ncbi_eutils digest 接线；agnes relay 示例（d5eb660）
- 下一项任务：M14（`PLAN-20260828-021`）、M15 并行
