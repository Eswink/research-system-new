---
id: PLAN-20260828-017
slug: m12-first-real-research-workflow-retrospective
title: M12 First Real Research Workflow（回顾重建）
status: DONE
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: c:\Users\googl\.cursor\plans\m12_first_real_workflow_7ed407b2.plan.md
owners:
  - root-agent
authorization:
  source: user-request
  ref: "补齐流程计划与文档对齐（2026-08-28 批准）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260828-017-m12-first-real-research-workflow.md
memory_entries:
  - MEM-20260822-016
---

# PLAN-20260828-017 — M12 First Real Research Workflow（回顾重建）

> 本文件为 `RETROSPECTIVE_RECONSTRUCTION` 记录：依据 `docs/roadmap/M12_COMPLETION_RECORD.md`、git history（commit `2e312f3`/`c257e03`/`f1ac926` 等）、当前代码/测试与可执行 validator 事后重建，非原开发窗口文档。原始开发窗口计划为 `PLAN-20260822-016`（本文件为其回顾重建副本）。

## 目标

记录并固化 M12 First Real Research Workflow 的正式任务计划：使用生产路径端到端完成一个真实、计算型、可复现、有 Evidence / 独立 Evaluation / 成本记录并形成 Deliverable 的 Research Workflow，作为 MVP 成立判定点（GO/NO-GO）。

## 范围

- 包含：
  - Reference Research Protocol 定义（`examples/protocols/m12_reference_research_v1.yaml`，7 阶段线性 DAG）与 Compiler/Preflight/Manifest Freeze
  - 真实 Model Relay（OPENAI_COMPATIBLE）、真实 Research Tool（NCBI E-utilities REST）、真实 Experiment（DockerExecutionBackend）、Evidence/Claim/Memory 治理
  - 独立 Evaluation（M11 harness）、复现、Budget 闭环、Deliverable、故障注入与 Research Integrity 校验、MVP 判定
- 不包含：
  - Research Console 大规模 UI（M13）、Temporal/Durable 迁移（M14）、分布式 workers（M16）、GPU/HPC（M17）、多用户 RBAC（M18）、企业治理（M19）
  - 大批量工具接入或大规模基准

## 架构与数据流

- 所有者模块：
  - Domain: ProtocolDefinition/RunManifest/Role/Agent/TaskContract/HandoffBundle/Evidence/Claim/Memory/UsageLedger/EvalSpec
  - Application: protocol_compile/preflight/run_orchestration/tool_plane/experiments/evidence/memory/evaluation/model_relay
  - Adapter: relay（HTTP）、execution（Docker）、research_tools（ncbi）、workspace、index、sqlite
- 输入：Research Objective + ProtocolDefinition + ProjectSettings + CatalogSnapshot（ToolPack/Model/Skill pin）
- 输出：RunManifest(frozen) → Phase Tasks → Tool/Experiment Artifacts → Evidence/Claim → Evaluation Report → MemoryCommit → Deliverable → BudgetClosure + MVP Gate Report
- Canonical State：SQLite + Filesystem（M7/M9），Domain Entity 唯一真相；Vector/检索索引为 derived 可重建
- 策略门禁：Preflight（DAG/Role/Model/Tool/Workspace/Budget/Policy）+ Execution-time Policy + Memory 5 阶段 gate + Eval Gate fail-closed

## 验收条件

- [x] AC-01 WP1：Reference Protocol 正式定义并通过 compile_protocol / compile_and_preflight 且 report.passed，freeze_manifest 成功记录 digests
- [x] AC-02 WP2-Model：真实 OpenAI-compatible Relay 完成 probe/fingerprint/usage 入账且 Secret 不落盘（DoD-3 真实冒烟：opencode.ai/zen/go/v1 + muse-spark-1.2-contributor，5 能力通过）
- [x] AC-03 WP2-Tool：NCBI E-utilities 真实冒烟 754 hits + 17 契约测试 + ToolPack 供应链登记（digest `947cbb22…`）
- [x] AC-04 WP2-Experiment：DockerExecutionBackend 6 容器 E2E + ReproducibilityAudit PASS + NEGATIVE_RESULT 区分系统 FAILED
- [x] AC-05 WP2-Evidence：Source→Evidence→Claim 链完整（m12_chain 10 测试），contradictory 时 DISPUTED，Governed Memory 经 5 阶段 gate
- [x] AC-06 WP3-Eval：M11 harness 独立评测 10 维度，deterministic 优先，verdict PASS
- [x] AC-07 WP3-Repro/Budget：关键实验重跑一致；Model/Tool/Experiment/Eval 四源用量闭环（close_budget 6 测试）
- [x] AC-08 WP3-Deliverable：正式 Deliverable（`docs/research/M12_REFERENCE_RESEARCH_REPORT.{json,md}`）引用 Artifact/Evidence/Claim digest
- [x] AC-09 Failure/Integrity：故障注入矩阵与 Research Integrity（m12_integrity 13 测试），错误分类正确
- [x] AC-10 Gate：M12 DoD 14 项逐项 PASS，回归保持，MVP GO 判定

> 注意：AC 对应的原 `PLAN-20260822-016` 判定 PASS 已被 M12-R1 独立复审证伪并修正（见 `PLAN-20260828-019` 与 `docs/roadmap/M12_R1_COMPLETION_RECORD.md`）；本回顾计划记录 M12 主体工作事实，最终状态以 R1 修复轮为准。

## 实施清单

- [x] STEP-01 WP1-Protocol：创建 m12_reference_research_v1.yaml（7 阶段 DAG），验证 compile_and_preflight 与 freeze_manifest
- [x] STEP-02 WP2-ModelRelay：接入真实 relay 配置，完成 probe/fingerprint/eligibility 集成，闭环 usage_recording 与 BudgetLedger
- [x] STEP-03 WP2-RealTool：实现 NCBI E-utilities REST ToolProvider，注册 ToolPack，验证 health/large-result spill 与凭据隔离
- [x] STEP-04 WP2-Experiment：串联 ExperimentExecutor + DockerExecutionBackend，验证 workspace 隔离与 ReproducibilityAudit
- [x] STEP-05 WP2-Evidence-Memory：实现 EvidenceLedger→Memory gate 端到端写入与矛盾/negative 路径
- [x] STEP-06 WP3-Eval：定义 M12 EvalDataset（冻结 digest `sha256:af6630f3…`），配置 deterministic scorers
- [x] STEP-07 WP3-Repro-Budget：执行重跑与四源用量对账，落地 UsageLedger/Budget 校验
- [x] STEP-08 WP3-Deliverable：生成报告 artifact，校验其引用与 provenance
- [x] STEP-09 WP3-Fault-Integrity：执行故障注入与 Integrity 扫描
- [x] STEP-10 MVP Gate：生成 M12 DoD 逐项判定与 Final Output，执行 recheck（RECHECK-20260822-016 PASS）

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（回顾重建） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-01 | file/test | `examples/protocols/m12_reference_research_v1.yaml`；`tests/application/test_m12_manifest_freeze.py` | 11 tests PASS |
| EV-02 | AC-02 | test | `tools/m12_relay_smoke.py`；`tests/application/model_relay/test_live_probe_not_verified.py` | probe ok=True，5 能力通过 |
| EV-03 | AC-03 | file/test | `adapters/research_tools/ncbi.py`；`tests/contracts/test_ncbi_provider_contract.py`；`docs/references/UPSTREAM_FINDINGS_V0_4_0.md` | 17 tests PASS；754 hits |
| EV-04 | AC-04 | test | `tests/application/experiments/test_m12_reference_e2e.py`（requires_docker） | 6 passed |
| EV-05 | AC-05 | test | `tests/application/evidence/test_m12_chain.py` | 10 passed |
| EV-06 | AC-06 | test | `tests/evals/test_m12_evaluation.py`；`examples/eval/datasets/m12_research_v1.yaml` | 5 passed；digest `af6630f3…` |
| EV-07 | AC-07 | test | `tests/application/experiments/test_budget_closure.py` | 6 passed |
| EV-08 | AC-08 | file | `docs/research/M12_REFERENCE_RESEARCH_REPORT.{json,md}` | 引用真实 digest |
| EV-09 | AC-09 | test | `tests/application/evidence/test_m12_integrity.py` | 13 passed |
| EV-10 | AC-10 | check | `docs/roadmap/M12_COMPLETION_RECORD.md` DoD 表；RECHECK-20260822-016 | PASS（后被 R1 证伪修正） |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-28 | 回顾重建 | 原开发窗口计划 `PLAN-20260822-016` 已存在，本计划为其对照副本以固化正式流程记录 | 计划 ID 不冲突；历史 PASS 结论保留但被 R1 修正 |
| 2026-08-23 | M12 判定 FAIL/MVP NO-GO | M12-R1 独立复审证伪原 PASS | 状态以 R1 修复轮为准（见 `PLAN-20260828-019`） |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-22 | — | DONE | 原 PLAN-20260822-016 完成（RECHECK-20260822-016 PASS） | cursor_plan_uri |
| 2026-08-23 | DONE | DONE（R1 修正） | 独立复审证伪原 PASS，R1 修复轮另立计划 | `docs/roadmap/M12_R1_COMPLETION_RECORD.md` |
| 2026-08-28 | — | DONE | 回顾重建完成并复检 PASS | 本文件 + RECHECK-20260828-017 |

## 影响报告

- Domain/API/schema：`RunManifest`（M12-R1 扩展字段）、`ExperimentRunResult.semantic_metrics_digest`、`CompletionResult` token 明细（兼容新增）
- 安全/凭据：LLM Key 经 SecretValue 密封，全程未落盘
- 兼容性/迁移：SQLite 持久化；EvidenceLedger/MemoryStore 进程内 Fake（P1 → M14）
- 上游版本：opencode.ai relay（用户提供）、NCBI E-utilities（HTTP_API，`UPSTREAM_COMPONENTS.yaml` ADOPTED）
- 下一项任务：M12-R1 修复轮（`PLAN-20260828-019`）；M12 重新独立复审重判
