---
id: PLAN-20260828-024
slug: m15-observability-cost-eval-operations
title: M15 Observability / Cost / Eval Operations
status: APPROVED
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: .cursor/plans/m15_observability_cost_eval_26abd45a.plan.md
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "用户已审阅并批准 M15 计划(m15_observability_cost_eval_26abd45a.plan.md)"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260828-024 — M15 Observability / Cost / Eval Operations

## 目标

建立 Research OS 正式的 Observability + Cost Operations + Evaluation Operations:
OTel(位于 Adapter 层,genai 内容默认不采集)、UsageLedger → Cost 归集(actual /
estimated / unknown / unavailable / zero 语义正确,pricing version 不重写历史)、
EvalReport 趋势与 regression 运营(M11 唯一判定权威,不可比较不伪装 regression)。
M15 不建立第二套 Canonical State,不定义 SLO,不改 M0–M14 已验证的 Budget/Workflow/
Evidence/Evaluation 核心语义。DoD 21 条 + m0 profile 全绿 + 独立复审 PASS 后 DONE。

## 范围

- 包含:
  - WP1 Telemetry Plane + OpenTelemetry qualification(M15_OTEL_QUALIFICATION.md + ADR-0026)
  - `packages/application/observability/` 内部遥测词汇(闭集 enum、无内容通道)
  - `packages/application/ports/telemetry_sink.py`(TelemetrySink Port,立即有真实消费方)
  - `adapters/otel/`(SDK 唯一所在地)+ `adapters/fakes/telemetry_sink.py`
  - `docker-compose.m15.yml` + collector config + `tests/observability/otlp_receiver.py`
  - failure-isolation 故障注入(Collector down / timeout / 500 / slow / queue full / restart)
  - WP2 additive ledger 修正 + versioned pricing snapshot + cost projection(五状态)
  - WP3 EvalReportStore(port + migration 005)+ comparability + trend
  - Control Plane API:`GET /runs/{id}/telemetry`、`GET /runs/{id}/cost`、`GET /evaluations/trend`
  - Console operations view(只消费正式 projection)
  - privacy canary、metric cardinality、soak、架构门禁、供应链 pin、M14 regression、m0 19/19
- 不包含:
  - 完整 Prompt/Response tracing、内容 Debug Mode、logs signal
  - 多租户成本隔离(M18)、SLO/incident governance(M19)、Distributed Worker(M16)、GPU/HPC(M17)
  - 修改 `FrozenConditions` / `comparison_digest()` / `schemas/eval-score.schema.json`
  - 把 Collector 当 Audit Store;让 telemetry 成为 business truth
  - M15A/M15B 等 Roadmap 拆分编号

## 架构与数据流

- 所有者模块:
  - Application:`packages/application/observability/`(sets vocabulary)、`packages/application/cost/`、
    `packages/application/evaluation/comparability.py`、`packages/application/ports/telemetry_sink.py`、
    `packages/application/ports/eval_report_store.py`
  - Adapter:`adapters/otel/`(OTel SDK 唯一所在地)、`adapters/postgres/eval_report_store.py`、
    `adapters/sqlite/eval_report_store.py`、`adapters/fakes/{telemetry_sink,eval_report_store}.py`
  - Entry:`services/api/routers/operations.py`(DTO/mapper)、composition/settings/lifespan
- 输入:ADR-0020(OBSERVABILITY.md)、UsageLedgerEntry、M11 EvalReport/FrozenConditions、
  M12 真实 relay usage、M14 PG 域状态与 outbox
- 输出:OTLP span/metric(无内容)、Cost 五状态 projection(pricing version/digest)、
  Eval trend/comparability projection、只读 API + Console views
- Canonical State:PostgreSQL Domain Entity 唯一真相;telemetry 可采样/丢弃/延迟,
  永不回读为业务决策
- 核心语义:telemetry != audit truth;cost 只从 UsageLedger snapshot 派生;
  eval verdict 只来自 M11 `compute_verdict` / `compare_reports`;unknown != 0

## 验收条件

- [ ] AC-01 OTel qualification 有完整 evidence(M15_OTEL_QUALIFICATION.md + ADR-0026)
- [ ] AC-02 OTel 位于 Adapter boundary(.importlinter.otel 生效;禁止列表含 opentelemetry)
- [ ] AC-03 trace hierarchy 与真实 Research Run 对齐(project/run/phase/task/agent_session/llm/tool/experiment/eval)
- [ ] AC-04 Model/Tool/Workflow/Experiment/Evaluation 关键 signals 可观察
- [ ] AC-05 默认不采集 Prompt/Response/Secret/敏感 Tool 内容(词汇无内容通道 + canary)
- [ ] AC-06 实际 OTLP/Collector payload canary 通过(真实 wire bytes,非仅 unit test)
- [ ] AC-07 Collector outage 不破坏 Research canonical state(failure-isolation 全场景)
- [ ] AC-08 Audit Truth 与 Telemetry 分离(测试证明 telemetry 不回读)
- [ ] AC-09 Cost 只基于正式 UsageLedger(BudgetLedger.snapshot() 唯一输入)
- [ ] AC-10 actual/estimated/unknown/unavailable/zero 语义正确
- [ ] AC-11 pricing version 不重写历史成本
- [ ] AC-12 retry/failure usage 不漏记、不重复
- [ ] AC-13 Eval Trend 基于 M11 EvalResult(EvalReportStore 保留原文 + digest 可验证)
- [ ] AC-14 不可比较 Evaluation 不被伪装成 regression(ComparabilityVerdict 分支全覆盖)
- [ ] AC-15 Regression verdict 不由 Dashboard 创建(pass/fail/regression 来自 M11)
- [ ] AC-16 INFRA_ERROR 与 quality failure 正确区分
- [ ] AC-17 M13 Console 只消费正式 projection
- [ ] AC-18 telemetry 不造成明显资源泄漏或运行不稳定(soak + telemetry on/off 对比)
- [ ] AC-19 security/architecture tests PASS(otl boundaries + 生产边界 + openapi snapshot 修复)
- [ ] AC-20 M0–M14 critical regressions + m0 profile 全绿(19/19)
- [ ] AC-21 独立复审 PASS(recheck skill 按原始验收条件复核)

## 实施清单

- [ ] STEP-01 持久化本计划(PLAN-20260828-024 + ALL_PLAN 索引)
- [ ] STEP-02 WP1 OTel qualification + ADR-0026
- [ ] STEP-03 WP1 observability vocabulary + TelemetrySink Port(闭集 enum + sanitize)
- [ ] STEP-04 WP1 adapters/otel/ + fakes + contract registry + composition/settings/lifespan
- [ ] STEP-05 WP1 instrument sites(relay/tool/workflow/outbox/scheduler/execution/eval/orchestration)
- [ ] STEP-06 WP1 collector topology + otlp_receiver + requires_collector + DEPLOYMENT_PROFILES
- [ ] STEP-07 WP1 failure-isolation 故障注入 + canonical-state equality
- [ ] STEP-08 WP2 additive ledger corrections(quantity_status/unavailable_reason/attempt 等)
- [ ] STEP-09 WP2 pricing schema + 空 pricing.yaml + loaders + cost/pricing.py
- [ ] STEP-10 WP2 cost projection + aggregation + reconciliation 测试
- [ ] STEP-11 WP3 EvalReportStore port + migration 005 + 三 adapter + rebuild 测试
- [ ] STEP-12 WP3 comparability + trend(INFRA_ERROR/missing evaluation 隔离)
- [ ] STEP-13 API/Console:operations router/DTO/mapper + OpenAPI regen + Console view
- [ ] STEP-14 WP4 privacy canary + metric cardinality 审计
- [ ] STEP-15 WP4 architecture gates(.importlinter.otel、禁止列表、postgres 契约执行等)
- [ ] STEP-16 供应链 pin(pyproject + UPSTREAM_COMPONENTS + LICENSE_MATRIX)
- [ ] STEP-17 WP4 soak + telemetry on/off 对比 + M14 regression + m0 19/19
- [ ] STEP-18 文档收口(OBSERVABILITY/BUDGET_QUOTA/EVALUATION/PORTS/CONTROL_PLANE_API/INDEX/MILESTONES/BACKLOG/CHANGELOG + M15_COMPLETION_RECORD)+ recheck

## 子代理使用

Subagent 默认不启用。需要并行时,每个 wave 最多 3 个;多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用(初始阶段) | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-01 | file | `docs/references/upstream/M15_OTEL_QUALIFICATION.md` + `docs/adr/ADR-0026-otel-adapter-boundary.md` | 待填写 |
| EV-02 | AC-06 | check | `pytest tests/observability`(otlp_receiver 真实 wire bytes canary) | 待填写 |
| EV-03 | AC-07 | check | failure-isolation 故障注入全场景 | 待填写 |
| EV-04 | AC-10/11/12 | check | `pytest tests/application/cost tests/application/experiments` | 待填写 |
| EV-05 | AC-13/14/16 | check | `pytest tests/evals tests/application/evaluation` | 待填写 |
| EV-06 | AC-17 | check | OpenAPI snapshot + Console operations view 测试 | 待填写 |
| EV-07 | AC-19 | check | import-linter otel 契约 + 生产边界 + snapshot 修复 | 待填写 |
| EV-08 | AC-20 | check | m0 profile 19/19 deterministic checks | 待填写 |
| EV-09 | AC-21 | file | `RECHECK-20260828-024-*.md` recheck 结果 | 待填写 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-28 | 用户批准 M15 Cursor Plan(m15_observability_cost_eval_26abd45a) | Plan Mode 调查确认现状:无 telemetry 代码、无价格、无 eval 持久化 | 本计划执行范围 |
| 2026-08-28 | 无内容通道设计(词汇层结构性不可表达内容) | 比 gated Debug Mode 更强;默认不采集硬边界 | ADR-0026;canary 测试 |
| 2026-08-28 | 不修改 FrozenConditions / comparison_digest | 保持 M11 报告 digest 与 eval-score schema 稳定 | Trend 用 ComparabilityVerdict 独立计算 |
| 2026-08-28 | OTel 6 包直接 pin(uv.lock 现成版本) | 保持 lock 稳定;validator 要求 ADOPTED 直接依赖 | pyproject UPSTREAM_COMPONENTS |
| 2026-08-28 | 默认门禁用 in-repo OTLP receiver;Collector 为 requires_collector evidence run | 保持 m0 profile 离线确定性;DoD-6 真实 wire bytes | tests/observability + docker-compose.m15.yml |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-28 | — | DRAFT | 建立任务计划 | Cursor Plan 批准前 |
| 2026-08-28 | DRAFT | APPROVED | 用户批准 Cursor Plan | `m15_observability_cost_eval_26abd45a.plan.md` |
| 2026-08-28 | APPROVED | IN_PROGRESS | 计划确认,进入 Build 实施 | 本会话 |

## 影响报告

- Domain/API/schema:新增 `LedgerQuantityStatus`、`UsageLedgerEntry.quantity_status/unavailable_reason/attempt`(默认值保持兼容);新增 pricing-table.schema.json;新增 telemetry/cost/eval-store Ports;新增 3 个只读 API 端点;新增 migration 005_eval_state.sql。不改 `FrozenConditions`、`comparison_digest`、eval-score schema、reserve/release/gate/evidence 语义。
- 安全/凭据:OTLP headers 经 CredentialResolver;canary 保证 marker 不落 OTLP/log/UI;遥测词汇无内容通道。
- 兼容性/迁移:usage ledger legacy 行 decode 为 `quantity_status=KNOWN`(不重释历史数字);M13 `BudgetViewDto`/usage 端点形状不变(新字段 additive);OpenAPI snapshot 需重新生成并修复其 tautology 缺陷。
- 上游版本:`opentelemetry-*` 从传递依赖晋升为直接 pin(1.39.1 / 0.60b1,sdist digest);collector 镜像 digest pin;LICENSE_MATRIX 增补 Apache-2.0 evidence。
- 下一项任务:M15 完成记录 + recheck 后停止在阶段边界;M16/M18/M19 不自动开工。

- 无可复用事实:M15 全部运行事实将记录于 RECHECK-20260828-024 与完成记录;如出现稳定可复用工程事实再写 `.cursor/memory/`(不创建伪记忆)。