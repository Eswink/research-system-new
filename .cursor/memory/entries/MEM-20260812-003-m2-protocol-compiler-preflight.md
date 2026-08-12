---
id: MEM-20260812-003
title: M2 Protocol Compiler + Preflight 独立复审修复事实
status: ACTIVE
created_at: 2026-08-12
updated_at: 2026-08-12
scope: repository
confidence: 0.95
review_after: 2026-11-12
source_plans:
  - .cursor/plans/tasks/PLAN-20260812-003-m2-protocol-compiler-preflight.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260812-003-m2-protocol-compiler-preflight.md
supersedes: []
tags: [m2, protocol-compiler, preflight, finding-code, dag, module-boundaries]
---

# MEM-20260812-003 — M2 Protocol Compiler + Preflight 独立复审修复事实

## 做了什么

M2 独立复审完成，修复 8 类阻断/主要问题后 `m0` profile 19 项门禁 PASS、449 pytest 通过、bundle/governance validator 通过。落地事实：

1. 新增 `PreflightFindingCode` domain 稳定枚举（POLICY_DENIED / CREDENTIAL_MISSING / ENDPOINT_UNHEALTHY / MODEL_ELIGIBILITY / TOOL_UNAVAILABLE / SUPPLY_CHAIN_UNPINNED / WORKSPACE_UNAVAILABLE / BUDGET_MISSING / BUDGET_EXHAUSTED / BUDGET_LIMIT_UNKNOWN / POLICY_MISSING / POLICY_APPROVAL_REQUIRED / HUMAN_GATE_REQUIRED），替换 checks/compiler/dag/budget 中散落的裸字符串 code。
2. `CompileFindingCode` 新增 `DAG_ORPHAN_PHASE`（INFO 级，不阻断），`DagResult.valid` 按 ERROR/INFO 区分；编译器只对 ERROR 阻断，INFO 随 plan 携带。
3. `CompileResult` 语义修正：ERROR 时 plan 仍返回（带 findings 供诊断），新增 `compile_and_preflight` 组合器——compile 失败直接产 FAIL 报告，杜绝调用方丢弃 findings 后错误 freeze。
4. 按职责拆分：`protocol_compile/requirements.py`（TaskContract/Tool/Workspace/Budget 派生）、`preflight/policy_check.py`（policy 评估）；`PlanParts` 参数对象收敛 `_assemble_plan` 签名。
5. 契约资产修复：`examples/contracts/preflight_report.yaml` 重写（原为虚构 code + WARN 带 reservation 的矛盾语义）；`RESEARCH_PROTOCOL.md` §3 字段清单对齐 schema（phase 级无 budget/retry，retry 由 TaskContract.retry_policy 承载）。

加固（复审后追加）：

6. `BudgetCheck.unmapped_types` + `BUDGET_RESOURCE_UNMAPPED` WARNING：未映射 ResourceType（MODEL_* 等）不再静默放行，预算检查不完整时报告 WARN 阻断 freeze。
7. `ProjectSettings.from_mapping` 删除 `workspace_backend="openhands_docker"` 默认值（缺失抛错）；`project.yaml` 显式声明并由 bundle validator 校验注册。
8. `_CAPABILITY_SCOPE` 常量与 `policy.yaml` 双向一致性测试；发现并修复 `literature.read` 规则缺失（原会误 DENY）。

## 为什么这样做

- **finding code 必须可穷尽分类**：裸字符串散落导致新增失败类型无法被静态发现，也无法断言"覆盖全部 failure matrix"；domain 枚举使 `switch`/集合断言在编译期可穷尽，符合 Python Rule 的 stable enum 要求。
- **compile findings 不可丢弃**：原 `compile_protocol` 在 ERROR 时返回 `plan + findings`，`successful=False`，但调用方可绕过直接 freeze；组合器把"编译失败→FAIL 报告"固化为唯一入口，与状态机 PREFLIGHT_FAILED 语义一致。
- **DAG 检查不全**：缺失依赖/前向引用/循环已有，但孤立 phase（无前驱无后继）静默通过；INFO 级提示保留"合法但可疑"的诊断价值而不误伤单 phase 协议。
- **规模门槛是硬约束**：>300 行/函数 >50 行/参数 >5 会直接挂 `test_python_source_limits.py` 与 ruff PLR0913；M2 的 compiler/checks 职责过载，拆分比压行更干净。
- **示例契约必须与实现一致**：`preflight_report.yaml` 曾使用不存在的 code 且 WARN 携带 reservation ref，bundle validator 只做 schema 校验、不做语义校验，示例会误导下游消费者。
- **预算门禁不能静默丢弃未映射类型**：`_LIMIT_KEYS` 之外的 ResourceType 一旦出现在 reservation 中而未被检查，预算门禁形同虚设；显式 WARNING 保证"检查不完整不放行"。
- **application 层不得硬编码 Runtime 名称**：`workspace_backend` 默认值把 OpenHands 写进契约；显式声明 + validator 注册检查保持与 `backends.yaml` 一致。
- **policy scope 映射必须有单一事实源**：手工映射与 policy.yaml 漂移时，`literature.read` 案例证明会静默误 DENY；双向一致性测试锁死。

## 怎么做与复现

1. 全量门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → 19 checks PASS。
2. 单元测试：`uv run --frozen --no-sync python -B -m pytest` → 449 passed。
3. 契约 validator：`python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`、`python -B .cursor/skills/governance-check/scripts/validate.py`。
4. 依赖边界：`uv run lint-imports --config .importlinter.application` → 2 kept。

## 适用边界

- 适用于：M4+ 复用 `PreflightFindingCode` 作为 Preflight 失败分类；M5 Ports/Fakes 实现 `ResourceCatalog`/`BudgetReservationPort`/`CredentialResolver`；M7 执行期 budget accounting 接 `BudgetReservation`（当前仅 3 种资源类型入账：PARALLELISM/TOOL_REQUESTS/WALL_CLOCK）。
- 不适用于：M6 OpenHands Runtime 内部错误分类（由 adapter 映射到 `FailureCategory`）；M7 runtime usage accounting（`UsageLedger` 属执行期，不在 Preflight 职责内）；真实 LLM 集成测试（默认离线）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-12）。
- `PreflightFindingCode` 新增变体但未同步 schema/preflight-report 示例。
- Preflight 与 Compiler 的边界被重新划分（如引入独立 Preflight Port 层）。
- `test_python_source_limits.py` 或 ruff 阈值调整。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260812-003-m2-protocol-compiler-preflight.md` | M2 范围与验收 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260812-003-m2-protocol-compiler-preflight.md` | PASS 结论与发现清单 |
| repository | `packages/domain/protocols.py`（PreflightFindingCode / CompileFindingCode） | 稳定错误分类 |
| repository | `packages/application/protocol_compile/compiler.py`（compile_and_preflight 组合器） | compile 失败不 freeze |
| repository | `packages/application/protocol_compile/dag.py`（DAG_ORPHAN_PHASE） | 孤立 phase INFO 语义 |
| repository | `examples/contracts/preflight_report.yaml` | 示例契约与实现一致 |