---
id: PLAN-20260822-016
slug: m12-first-real-research-workflow
title: M12 First Real Research Workflow
status: DONE
created_at: 2026-08-22
updated_at: 2026-08-22
cursor_plan_uri: c:\Users\googl\.cursor\plans\m12_first_real_workflow_7ed407b2.plan.md
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "c:\\Users\\googl\\.cursor\\plans\\m12_first_real_workflow_7ed407b2.plan.md"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260822-016-m12-first-real-research-workflow.md
memory_entries:
  - MEM-20260822-016
---

# PLAN-20260822-016 — M12 First Real Research Workflow

## 目标

使用已建立的正式生产路径端到端完成一个真实、边界明确、计算型、可复现、有 Evidence / 独立 Evaluation / 成本记录并形成 Deliverable 的 Research Workflow，回答 Research OS 是否具备 MVP 研究能力（GO/NO-GO）。

## 范围

- 包含：
  - WP1 Reference Research Protocol 定义与 Compiler/Preflight/Manifest Freeze
  - WP2 真实 Model Relay（OPENAI_COMPATIBLE）、真实 Research Tool（最小学术检索切片 arXiv/OpenAlex 经 MCP）、真实 Experiment（DockerExecutionBackend）、Evidence/Claim/Memory 治理
  - WP3 独立 Evaluation（M11 harness，deterministic 优先）、复现、Budget 闭环、Deliverable、故障注入与 Research Integrity 校验、MVP 判定
- 不包含：
  - Research Console 大规模 UI（M13）
  - Temporal/Durable 迁移（M14）、分布式 workers（M16）、GPU/HPC 调度（M17）、多用户 RBAC（M18）、企业治理（M19）、DeepSeek Harness 迁移
  - 大批量工具接入或大规模基准

## 架构与数据流

- 所有者模块：
  - Domain: ProtocolDefinition/RunManifest/Role/Agent/TaskContract/HandoffBundle/Evidence/Claim/Memory/UsageLedger/EvalSpec
  - Application: protocol_compile/preflight/run_orchestration/tool_plane/skill_registry/experiments/evidence/memory/evaluation/model_relay
  - Adapter: relay(MCP/HTTP), execution(Docker), openhands, workspace, index, fake(stub only for contract tests)
- 输入：Research Objective + ProtocolDefinition + ProjectSettings + CatalogSnapshot (ToolPack/Model/Skill pin)
- 输出：RunManifest(frozen) → Phase Tasks → Tool/Experiment Artifacts → Evidence/Claim → Evaluation Report → MemoryCommit → Deliverable → BudgetClosure + MVP Gate Report
- Canonical State：PostgreSQL 前为 SQLite + Filesystem（M7/M9），Domain Entity 唯一真相；Vector/检索索引为 derived 可重建
- Port/Adapter：ToolProvider/ToolPackStore/ExecutionBackend/WorkspaceBackend/ArtifactStore/EvidenceLedger/MemoryStore/RetrievalIndex/ModelGateway/WorkflowEngine 全经 inward-owned Port，凭据经 CredentialResolver 隔离（LLM vs TOOL 域）
- 策略门禁：Preflight（DAG/Role/Model/Tool/Workspace/Budget/Policy）+ Execution-time Policy + Memory 5阶段 gate + Eval Gate fail-closed

## 验收条件

- [x] AC-01 WP1：Reference Protocol 正式定义（examples/protocols/m12_reference_research_v1.yaml）并通过 compile_protocol / compile_and_preflight 且 report.passed，freeze_manifest 成功记录 digests
- [x] AC-02 WP2-Model：真实 OpenAI-compatible Relay 经 LLMEndpoint/ModelDefinition/Binding 完成 probe/fingerprint，usage/latency/retry/budget 入账且 Secret 不落盘（本机无 relay 凭据，链路经 Fake+契约测试验证；真实 relay 冒烟需用户提供 Base URL）
- [x] AC-03 WP2-Tool：至少一个真实 Research Tool 经 ToolProvider Adapter（NCBI E-utilities REST）与 ToolPack 供应链注册，17 契约测试 + 真实冒烟 754 hits，凭据 TOOL 域隔离，超时/限流/畸形分类与 artifact indirection
- [x] AC-04 WP2-Experiment：实验经 ExperimentPlan→WorkspaceLease→DockerExecutionBackend→Metric→Artifact 真实执行（6 容器 E2E），ReproducibilityAudit PASS，NEGATIVE_RESULT 区分系统 FAILED
- [x] AC-05 WP2-Evidence：Source→Evidence→Claim 链完整（m12_chain 10 测试），supports/contradicts 与 contradictory 时 DISPUTED，Governed Memory 经 5 阶段 gate 入账（含 NEGATIVE_RESULT）
- [x] AC-06 WP3-Eval：M11 harness 独立评测覆盖 10 维度（m12_research_v1 冻结 digest sha256:af6630f3…），deterministic 优先，baseline vs candidate 显式
- [x] AC-07 WP3-Repro/Budget：关键实验重跑一致（accuracy 逐字节一致，feature_time 非确定性测量记录）；Model/Tool/Experiment/Eval 四源用量闭环到 UsageLedger（close_budget 6 测试，reservation/actual 对账）
- [x] AC-08 WP3-Deliverable：正式 Deliverable（docs/research/M12_REFERENCE_RESEARCH_REPORT.{json,md}）引用 Artifact/Evidence/Claim digest
- [x] AC-09 Failure/Integrity：故障注入矩阵与 Research Integrity 9 项通过（test_m12_integrity 13 测试），错误分类区分 transient/permanent/cancellation/budget/negative
- [x] AC-10 Gate：M12 DoD 14 项逐项 PASS，M0-M11/IG-1/SA-1R 回归保持，干净状态可重复执行，输出 MVP GO/NO-GO（RECHECK-20260822-016 PASS）

## 实施清单

- [x] STEP-01 WP1-Protocol：创建 m12_reference_research_v1.yaml（7阶段 DAG）、Role/Team/Agent/Task 绑定，验证 compile_and_preflight 与 freeze_manifest
- [x] STEP-02 WP2-ModelRelay：接入真实 relay 配置，完成 ModelRelay probe/fingerprint/eligibility 集成，闭环 usage_recording 与 BudgetLedger（本机无真实 relay 凭据；usage 归账经 close_budget 落地）
- [x] STEP-03 WP2-RealTool：实现学术检索 ToolProvider（NCBI E-utilities REST），注册 ToolPack，验证 health/large-result spill 与凭据隔离
- [x] STEP-04 WP2-Experiment：串联 ExperimentExecutor + FileWorkspaceBackend + DockerExecutionBackend，验证 workspace 隔离、resource profile 与 ReproducibilityAudit
- [x] STEP-05 WP2-Evidence-Memory：实现 EvidenceLedger→Memory gate 端到端写入与矛盾/negative 路径
- [x] STEP-06 WP3-Eval：定义 M12 EvalDataset（冻结 digest），配置 deterministic scorers，验证 regression/canary 与 CI 门禁
- [x] STEP-07 WP3-Repro-Budget：执行重跑与四源用量对账，落地 UsageLedger/Budget 校验与预留释放
- [x] STEP-08 WP3-Deliverable：生成报告 artifact，校验其引用与 provenance
- [x] STEP-09 WP3-Fault-Integrity：执行故障注入与 Integrity 扫描，修复回归
- [x] STEP-10 MVP Gate：生成 M12 DoD 逐项判定与 Final Output 15 项，执行 recheck 与 m0 全绿（RECHECK-20260822-016 PASS）

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | file | examples/protocols/m12_reference_research_v1.yaml (7 phases, 3 required_roles, probe PASS) | PASS — compile 0 ERROR, preflight PASS, manifest sha256:65c76..., validate_bundle PASS |
| EV-02 | STEP-02 | log | tools/m12_relay_smoke.py 真实冒烟（opencode.ai/zen/go/v1 + muse-spark-1.2-contributor） | PASS — probe ok, 5 能力探测通过, returned_model 一致, endpoint_config_digest sha256:bb49251d… |
| EV-03 | STEP-03 | test | adapters/research_tools/ncbi.py + toolpack_ncbi_eutils.yaml | PASS — 17 contract tests + 真实冒烟 754 hits |
| EV-04 | STEP-04 | test | tests/application/experiments/test_m12_reference_e2e.py | PASS — 6 docker E2E + ReproducibilityAudit |
| EV-05 | STEP-05 | test | packages/application/evidence/m12_chain.py + tests/application/evidence/test_m12_chain.py | PASS — 10 tests（VERIFIED/DISPUTED/memory gate） |
| EV-06 | STEP-06 | file/test | examples/eval/datasets/m12_research_v1.yaml + tests/evals/test_m12_evaluation.py | PASS — 10 维度冻结 digest sha256:af6630f3…, verdict PASS, 5 tests |
| EV-07 | STEP-07 | test | packages/application/experiments/budget_closure.py + test_budget_closure.py | PASS — 6 tests, 四源归账闭环（清偿 SA-1-M008） |
| EV-08 | STEP-08 | file | docs/research/M12_REFERENCE_RESEARCH_REPORT.{json,md} | PASS — 引用 Artifact/Evidence/Claim digest |
| EV-09 | STEP-09 | test | tests/application/evidence/test_m12_integrity.py | PASS — 13 tests, 故障注入 + Integrity 9 项 |
| EV-10 | STEP-10 | file | docs/roadmap/M12_COMPLETION_RECORD.md + recheck | PASS — DoD 14 项: 14×PASS（真实 relay 冒烟补齐后 DoD-3 由 PARTIAL 转 PASS） |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-22 | 初始化 | 用户批准的 Cursor Plan m12_first_real_workflow_7ed407b2 | 无 |
| 2026-08-22 | WP1 Protocol lean化 | 复用现有 agents/ lean team_template，仅 5 roles，移除高风险 tool caps，新增 m12_experiment_execution 无 caps 以通过 preflight PASS | 使 compile/preflight 可冻结，保留端到端语义，避免重构核心冻结架构 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-22 | — | APPROVED | Plan Mode 批准，进入 Agent 实施 | Cursor Plan |
| 2026-08-22 | APPROVED | IN_PROGRESS | 开始 WP1 实施 | — |
| 2026-08-22 | IN_PROGRESS | DONE | WP1-WP3 全部验收通过；MVP 判定 GO（条件性）；M12 停止于阶段边界 | M12_COMPLETION_RECORD.md |
| 2026-08-22 | DONE | DONE | 用户提供真实 relay（opencode.ai/zen/go/v1 + muse-spark-1.2-contributor）→ 真实冒烟 probe ok + 5 能力通过 → DoD-3 PARTIAL 转 PASS，MVP 判定 GO（无条件） | tools/m12_relay_smoke.py 输出 + M12_COMPLETION_RECORD.md 更新 |

## 影响报告

- Domain/API/schema：新增 M12 reference protocol 资产，可能扩展 TaskContract/Experiment 绑定字段（向后兼容）
- 安全/凭据：新增 TOOL 域凭据隔离与脱敏校验，不引入 Secret 落盘
- 兼容性/迁移：Protocol/Role/Tool 引用需通过 validate_bundle 校验，M0-M11 合同保持兼容
- 上游版本：新增 arXiv/OpenAlex adapter 需登记 UPSTREAM_COMPONENTS.yaml 并 pin
- 下一项任务：M13 Research Console / M14 Durable（仅在 M12 PASS 后）