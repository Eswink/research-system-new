---
id: PLAN-20260812-003
slug: m2-protocol-compiler-preflight
title: M2 Protocol Compiler + Preflight 实施
status: DONE
created_at: 2026-08-12
updated_at: 2026-08-12
cursor_plan_uri: "m2_protocol_compiler_+_preflight_4b241e47"
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "M2 Protocol Compiler + Preflight（用户批准）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260812-003-m2-protocol-compiler-preflight.md
memory_entries:
  - .cursor/memory/entries/MEM-20260812-003-m2-protocol-compiler-preflight.md
---

# PLAN-20260812-003 — M2 Protocol Compiler + Preflight 实施

## 目标

将声明式 `ProtocolDefinition` 确定性编译为可序列化、可验证并带 digest 的
`CompiledRunPlan`，在 `ResearchRun` 启动前解析运行资源并产出机器可读
`PreflightReport`；只有 PASS 才能冻结 `RunManifest`。M2 消费 M3 模型
eligibility，不执行 Agent，也不引入 OpenHands 或 WorkflowEngine。

## 范围

- 包含：Protocol loader、Phase DAG、Role/Agent/Model/Tool/Workspace/Credential/Policy/
  Budget 解析、M3 eligibility 消费、dry-run projection、Manifest freeze、结构化 failure
  matrix、状态机 PREFLIGHT 成败语义、Schema/示例/测试/门禁。
- 不包含：M4 的 Role fixture 与完整 Task/Handoff 行为、M5 全量 Ports/Fakes、M6
  OpenHands、M7 WorkflowEngine/lease/outbox/执行期 retry、真实外部 LLM/网络/凭据。

## 架构与数据流

```text
adapters/contracts + adapters/relay
    → packages/application/protocol_compile + policy + preflight
    → packages/domain

ProtocolDefinition
    → compile（纯确定性解析）
    → CompiledRunPlan
    → preflight（Port 查询 + 纯决策）
    → PreflightReport
    → PASS only: RunManifest freeze
```

编译期依赖保持 `adapters → application → domain`；domain 不 import 外层。
Application 通过内层拥有的 Port 查询 Credential/Endpoint/Workspace/Policy/预算资源。

## 验收条件

- [x] AC-01：Protocol loader 校验并加载真实 protocol 示例。
- [x] AC-02：PhaseStrategy 与 ProtocolPhase 对齐已冻结 schema 外部契约。
- [x] AC-03：DAG 缺失依赖、前向引用和循环产生机器可读 finding；合法 DAG 输出稳定。
- [x] AC-04：TeamTemplate capacity、Agent/ModelBinding 与 M3 eligibility 可解析且可阻断。
- [x] AC-05：Tool/Capability、Provider health/credential、Workspace/Compute 可解析且可阻断。
- [x] AC-06：Budget 聚合/预留和 NativePolicyEvaluator 在启动前完成。
- [x] AC-07：CompiledRunPlan 完整、确定性可序列化并有 canonical digest。
- [x] AC-08：PreflightReport 覆盖 failure matrix；FAIL 必有 ERROR，WARN 不进入 freeze。
- [x] AC-09：只有 PASS 才冻结 RunManifest，记录 protocol/compiled-plan digest。
- [x] AC-10：ResearchRun 状态机支持 PREFLIGHT_OK 与 PREFLIGHT_FAILED。
- [x] AC-11：dry-run 投影包含 Role/Model/Tool/Workspace/Compute/预算/审批。
- [x] AC-12：不执行 Agent，不 import OpenHands/WorkflowEngine，依赖门禁通过。
- [x] AC-13：全量 test/lint/typecheck/architecture/bundle/governance 门禁通过。

## 实施清单

- [x] STEP-01：新增 compiled-run-plan/budget-policy/policy/workspace Schema、示例与 validator 注册。
- [x] STEP-02：扩展 domain protocols、compile finding 与 run state machine。
- [x] STEP-03：新增 protocol 与运行资源 contract loaders。
- [x] STEP-04：实现 protocol_compile、NativePolicyEvaluator、preflight、budget、dry-run 与 freeze。
- [x] STEP-05：接入 import-linter/mypy/export 边界。
- [x] STEP-06：补全 domain/application/loader/contract tests 与 failure matrix。
- [x] STEP-07：运行全量门禁、DoD 复检并修复发现。

## 子代理使用

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| 1 | M1 domain 事实、M3 可消费接口、M2 规格/契约/测试现状 | 3 | 完成 | 调查结论已并入批准的 Cursor Plan |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-BASE-01 | 基线 | test | `uv run --frozen --no-sync python -B -m pytest` | 386 passed |
| EV-BASE-02 | 基线 | check | `validate_bundle.py` | PASS |
| EV-BASE-03 | 基线 | check | `governance validate.py` | PASS |
| EV-01 | STEP-01 | file/test/check | schemas/{protocol,compiled-run-plan,preflight-report,budget-policy,policy,workspace}.schema.json；`validate_bundle.py` | PASS |
| EV-02 | STEP-02 | file/test | `packages/domain/protocols.py`（ProtocolDefinition/CompiledRunPlan/PreflightReport/PreflightFindingCode）；`tests/domain/test_state_machines.py` | PASS |
| EV-03 | STEP-03 | file/test | `adapters/contracts/protocol_loaders.py`、`resource_loaders.py`；`tests/loaders/test_contract_loaders.py` | PASS |
| EV-04 | STEP-04 | file/test | `packages/application/{protocol_compile,preflight,policy}`；`tests/application/*` | PASS |
| EV-05 | STEP-05 | check | import-linter `.importlinter.application` 2 kept；mypy 112 files success | PASS |
| EV-06 | STEP-06 | test | `test_m2_audit.py`（13 项）、`test_example_protocol_integration.py`；全量 pytest 449 passed | PASS |
| EV-07 | STEP-07 | check/recheck | `run_all_checks.py --profile m0 --keep-going` 19/19 PASS；RECHECK-20260812-003 PASS | PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-12 | Domain PhaseStrategy 对齐 schema 六种外部策略 | schema、示例与 validator 已冻结，domain 占位零使用/零测试 | 消除双枚举与双向映射 |
| 2026-08-12 | 新增 PREFLIGHT_FAILED 并修正 PREFLIGHT_OK | 当前事件名语义错误且失败无落态 | 明确启动前阻断语义 |
| 2026-08-12 | DAG 复用 stdlib graphlib | 无已登记上游 DAG 依赖，能力简单确定性 | 零新增依赖 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-12 | — | APPROVED | 用户批准 Cursor Plan | `m2_protocol_compiler_+_preflight_4b241e47` |
| 2026-08-12 | APPROVED | IN_PROGRESS | 开始契约资产实施 | STEP-01 |
| 2026-08-12 | IN_PROGRESS | DONE | 独立复审修复全部阻断项；AC-01~AC-13 有可复现证据 | RECHECK-20260812-003 PASS；m0 profile 19/19 |

## 影响报告

- Domain/API/schema：新增 `PreflightFindingCode` 稳定枚举；`CompileFindingCode` 新增 `DAG_ORPHAN_PHASE`；`ProtocolPhase` 归一化 `task_contract` 到 `task_contracts`；删除 `CompiledRunPlan.role_pool_refs` 占位投影；新增 `compile_and_preflight` 组合器；`examples/contracts/preflight_report.yaml` 与实现对齐。
- 安全/凭据：只解析 credential ref，不持久化或记录明文；secret 不进入 CompiledRunPlan/PreflightReport/Manifest 序列化（有测试）。
- 兼容性/迁移：VERSION 保持 0.4.0；finding code 从裸字符串迁移为枚举，字符串值不变，无外部消费者破坏；DAG_ORPHAN_PHASE 为新增 INFO 级，不阻断既有合法协议。
- 上游版本：零新增依赖（DAG 继续使用 stdlib graphlib）。
- 下一项任务：M2 已完成，停在阶段边界；评估 M5/M7 readiness，不自动开始下一开发阶段。