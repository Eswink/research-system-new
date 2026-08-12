---
id: RECHECK-20260812-003
plan_id: PLAN-20260812-003
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-12
completed_at: 2026-08-12
reviewer: root-agent-independent-pass
baseline_ref: 7bfcd3cd50a9c6a99f555187ec7632a3f3127fed
checked_head: 7bfcd3cd50a9c6a99f555187ec7632a3f3127fed
---

# RECHECK-20260812-003 — M2 Protocol Compiler + Preflight

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260812-003-m2-protocol-compiler-preflight.md`
- 验收条件：AC-01 至 AC-13（原复检文本误写为 AC-15，已修正为与计划一致的 AC-01~AC-13）
- 变更范围：Schema/示例、Domain Protocol/状态机、契约 loader、Application Protocol Compiler/Policy/Preflight、测试与门禁配置。
- 基线：`main` 当前提交 `7bfcd3cd50a9c6a99f555187ec7632a3f3127fed`；M2 变更处于未提交工作区，本次独立复审以此工作区为事实来源。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | `.importlinter.application`（2 kept）；Application 不导入 adapters；M2 不 import OpenHands/Temporal/LiteLLM/FastAPI/SQLAlchemy（grep 全 packages 无匹配） | PASS |
| G-02 | 验收条件 | `tests/application/test_protocol_compiler.py`、`test_protocol_dag.py`、`test_m2_policy_budget.py`、`test_m2_resolution.py`、`test_m2_audit.py`、`tests/loaders/test_example_protocol_integration.py`、`tests/loaders/test_contract_loaders.py`、状态机测试；AC-01~AC-13 逐项见结论 | PASS |
| G-03 | lint/typecheck/test | `run_all_checks.py --profile m0 --keep-going` 19/19 PASS（engineering-lint、product-lint、format-check、typecheck、dependency-boundaries、pytest、TS 5 项、framework 7 项、release-assets-immutable） | PASS |
| G-04 | 安全与凭据 | credential 仅通过 CredentialResolver Port；secret 不进入 CompiledRunPlan/PreflightReport/Manifest 序列化（`test_secrets_never_enter_plan_report_or_manifest`）；Native policy 默认 DENY fixture；外部 ToolProvider 要求严格 `sha256:<64 hex>` pin | PASS |
| G-05 | 兼容性与迁移 | Protocol/CompiledRunPlan/PreflightReport Schema validator 全通过；`PREFLIGHT_OK`/`PREFLIGHT_FAILED` 与 RUN_STATE_MACHINE.md 迁移表一致；`examples/contracts/preflight_report.yaml` 修正为与实现一致的 code/语义 | PASS |
| G-06 | 计划、记忆、供应链 | governance validator PASS；system-spec bundle validator PASS；ALL_PLAN / PLAN / RECHECK 交叉引用一致；VERSION 0.4.0 单一版本源 | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| R-001 | INFO | `mypy` 全配置原先会扫描架构测试 fixture 的非根包路径 | 已在 `pyproject.toml` 排除 valid/invalid 架构 fixture；M2 相关 112 文件类型检查通过 |
| R-002 | ERROR | Preflight finding code 为散落裸字符串，无稳定可测试分类 | 新增 `PreflightFindingCode` domain 稳定枚举并替换 checks/compiler/dag/budget 全部裸字符串 |
| R-003 | ERROR | `checks.py` 使用字符串比较 `gate.gate.value == "HUMAN_GATE"`、`provider.kind.value != "NATIVE"` | 改为 `GateType.HUMAN_GATE` / `ProviderType.NATIVE` 枚举比较 |
| R-004 | ERROR | 死代码：`CompiledRunPlan.role_pool_refs` 占位投影、`EndpointHealthPort` 未使用 Port | 删除；无调用方 |
| R-005 | ERROR | DAG 不检测孤立/不可达 phase | 新增 `DAG_ORPHAN_PHASE` INFO finding（不阻断），`DagResult.valid` 区分 INFO/ERROR |
| R-006 | ERROR | `CompileResult` 语义歧义：plan 存在但含 ERROR findings 时 `successful` 为 False，调用方可绕过；且 ERROR+plan 可被直接 freeze | 语义修正：ERROR 时 `plan` 仍返回但 findings 必带 ERROR（供诊断）；新增 `compile_and_preflight` 组合器，compile 失败直接产 FAIL 报告，杜绝错误 freeze |
| R-007 | ERROR | `examples/contracts/preflight_report.yaml` 使用虚构 finding code（`MODEL_CAPABILITY_UNVERIFIED`）且 WARN 状态下带 `reserved_budget_ref`，与实现矛盾 | 重写为 `POLICY_APPROVAL_REQUIRED`/`BUDGET_LIMIT_UNKNOWN` + `reserved_budget_ref: null` |
| R-008 | ERROR | `docs/architecture/RESEARCH_PROTOCOL.md` §3 声明 `budget/timeout/retry` 字段，与 `schemas/protocol.schema.json` 实际契约（`timeout_seconds`、无 phase 级 budget/retry）漂移 | §3 字段清单对齐 schema，并注明 retry 由 TaskContract.retry_policy 承载 |
| R-009 | ERROR | M2 新增代码未过 format 门禁（22 文件），CI `m0` profile 失败 | ruff format 修复；后续全量门禁通过 |
| R-010 | MAJOR | 行数/参数门槛：`compiler.py` >300 行、`checks.py` >300 行、`compile_protocol` 53 行、`_assemble_plan` 8 参数、测试文件 306+ 行 | 按职责拆分：`requirements.py`（TaskContract/Tool/Workspace/Budget 派生）、`policy_check.py`（policy 评估）、`PlanParts` 参数对象、测试 payload 辅助模块 |
| R-011 | MINOR | DoD 缺口：无最小协议、多 phase、duplicate、invalid strategy、unknown enum、malformed、multi-failure 聚合、round-trip/schema、secret 边界、纯函数副作用、真实示例集成测试 | 新增 `test_m2_audit.py`（13 项）与 `tests/loaders/test_example_protocol_integration.py`（真实 assets 端到端） |
| R-012 | INFO | `compiled-run-plan.schema.json` 的 `stopConditions.budget_exhausted` 为 required，domain 默认 False，序列化不变量一致 | 已确认一致，无代码变更 |
| R-013 | MAJOR | `check_budget` 对未映射 ResourceType（MODEL_* 等）静默 `continue`，预算门禁会静默失效 | `BudgetCheck.unmapped_types` 收集未映射类型；`BUDGET_RESOURCE_UNMAPPED` WARNING 使预算检查不完整时不放行 freeze；补 2 项测试 |
| R-014 | MAJOR | `ProjectSettings.from_mapping` 默认 `workspace_backend="openhands_docker"`，把具体 Runtime 名称写进 application 契约 | 删除默认值（缺失即抛错）；`examples/config/project.yaml` 显式声明；bundle validator 增加注册检查；补测试 |
| R-015 | MAJOR | `_policy_scope` 6 项手工映射与 `policy.yaml` 漂移：`literature.read` 映射存在但 policy 无对应 allow 规则（实际会误 DENY） | 提升为 `_CAPABILITY_SCOPE` 常量；补 `literature.read` allow 规则（与注册 capability 及 provider 能力一致）；新增 policy.yaml 双向一致性测试 |
| R-016 | INFO | `estimated_cost` 恒 None 是显式设计，但无文档与测试锁定"null=未估算（非 0）"语义 | 模块 docstring 记录语义；补 null 非 0 断言测试 |

## 结论

- 结果：`PASS`
- 理由：独立复审发现 8 类阻断/主要问题并全部修复；AC-01~AC-13 均有可复现测试证据；`m0` profile 19 项门禁全 PASS；bundle/governance validator 全 PASS。M2 未降低 DoD、未修改验收标准、未删除失败测试、未放宽 Policy/Secret/Preflight gate。
- 后续动作：M2 判定 DONE 并停在阶段边界；更新 PLAN/ALL_PLAN provenance；评估 M5/M7 readiness，不自动开始下一开发阶段。