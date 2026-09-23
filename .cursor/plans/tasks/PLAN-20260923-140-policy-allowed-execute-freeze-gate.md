---
id: PLAN-20260923-140
slug: policy-allowed-execute-freeze-gate
title: 冻结门的显式策略通道：策略允许的 EXECUTE 可冻结算 PASS（留痕 + 点名拒冻）
status: IN_PROGRESS
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260923-012
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260923-012 建档授权（2026-09-23 用户 goal 模式指令）：**用户已拍板路径 (A)**——
    授权把冻结门从「只认 PASS」改为「**策略已显式允许的 EXECUTE 可冻结算 PASS**」，作为一条
    **显式、留痕、可审计**的通道。范围严格限于：a) `classify_risk(EffectClass.EXECUTE, …) → HIGH`
    **保持不变**；b) 当且仅当「该能力/工具的 EXECUTE 风险已被**显式策略声明**允许（policy 中有对应
    allow 规则且作用域匹配）**且**该允许在 manifest/事件里**留痕**」时，冻结门的 WARN 可被接受并记为
    PASS；未声明允许时**仍拒冻**（默认 deny 不变）；c) 拒绝语义必须**点名**缺哪条策略事实。
    本 PLAN 明文不做：放宽 `classify_risk`；改 `PreflightStatus.WARN` / `PreflightReport.passed` 的语义；
    让 WARN **无条件**可冻；skip/删除测试或降低断言强度；`git add -A`；伪造或夸大验证证据；
    新增依赖或改上游 pin；改 workflow / 出站判据（`tests/egress_guard.py`）。
    **若本 PLAN 的实现需要放松 AGENTS.md §9 任一条默认 deny 面 ⇒ 立即停止并记 BLOCKED。**
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260923-140 — 冻结门的显式策略通道（GOAL-012 EC-01）

## 目标

让 `sort_analysis_v1` 这类**预检 WARN 但策略已显式允许**的计划**能冻结**：给 `freeze_manifest`
加一条**显式、留痕、可审计**的接受口径——当且仅当「该 EXECUTE 风险已被显式策略声明允许」时，
WARN 可被接受并记为 PASS，且**留痕**（哪条策略、哪个能力、何时）；**未声明允许时仍拒冻**，
消息**点名**缺失的策略事实。`classify_risk` 与 `PreflightStatus.WARN` 的语义**一字不动**。

## 计划开始前的定案（写死）

- **D-1 载体的落点**：新模块 `packages/application/preflight/policy_acceptance.py`——
  把「接受口径的判定 + 留痕构造 + 点名拒冻消息」三种事放在一处；`checks.py` / `preflight.py`
  只**接线**（`freeze_manifest` 的入口多一步），不新增第二套 policy 求值（复用 `context.policy_evaluator`）。
- **D-2 通道条件（当且仅当，全部满足才接受）**：
  1. 报告状态是 `WARN`（`FAIL` 一律拒——`FAIL` 意味着存在 ERROR finding）；
  2. 报告里**没有** `TOOL_RISK_ELEVATED` 以外的 WARNING（其它任何警示**不可转换**：
     `TOOL_HEALTH_UNPROVEN` / `TOOL_HEALTH_DEGRADED` / `POLICY_APPROVAL_REQUIRED` /
     `BUDGET_LIMIT_UNKNOWN` / `BUDGET_RESOURCE_UNMAPPED` …）；
  3. 每条 `TOOL_RISK_ELEVATED`（`subject_ref = provider:<id>`）的 provider 在冻结目录里可解析，
     且 `effect_class is EffectClass.EXECUTE`、`classify_risk(effect_class, trust_level) is HIGH`
     （**只认 EXECUTE**；`CRITICAL` 或其它 effect 一律拒）；
  4. 该 provider 服务的**每一条** `ToolRequirement`（`plan.tool_requirements` 里 `provider_ids`
     含它的那些能力）经**同一个** `PolicyEvaluator` 求值为 `ALLOW` **或** `ALLOW_WITH_CONSTRAINTS`
     （`DENY` / `REQUIRE_APPROVAL` / 求值器缺失 / 该 provider 没有任何能力需求 ⇒ 一律拒）。
  以上任一条不满足 ⇒ **拒冻**，且消息**逐条点名**缺的事实（provider / 能力 / 策略版本 / 决策）。
- **D-3 留痕的落点（两处同源，不另存副本）**：
  - `RunManifest` 新增 **optional** 字段 `accepted_policy_exceptions: list[dict]`
    （**空列表 = 未使用通道** ⇒ 既有 fixture 的 `digest()` / `semantic_digest()` **逐字不变**；
    沿用 M12-R1 已登记的「兼容新增 optional 字段」扩展口径）；
  - `frozen_payload`（`MANIFEST_FROZEN` 事件）带**同一份**列表（读面回读的就是这份 payload）。
  每条含七项：`capability` / `phase_id` / `provider_id` / `policy_version` / `decision` /
  `constraints` / `accepted_at`（= 该次冻结的时刻，与 `frozen_at` 同源）。
- **D-4 明确不改**（逐项写死，反证面）：`classify_risk`（`packages/domain/tools.py`）；
  `PreflightStatus` 成员与 `_status()`；`PreflightReport.passed`（**仍是「PASS 才 passed」**）；
  `check_policy` / `check_tools` 的 finding 生成、code 与严重级；`ManifestFreezeError` 的既有
  消息**前缀**（`cannot freeze manifest before a passing preflight`——新消息是它的**超集**，
  既有 `pytest.raises(ManifestFreezeError)` 全部保持有效）。
- **D-5 既有判据的处置（承撤回纪律）**：`tests/e2e/test_sandbox_experiment_reachability.py::`
  `test_sort_analysis_is_refused_before_freeze_on_the_risk_warning` 钉的是**旧产品行为**
  （GOAL-011 cycle 6 登记的阻断点）。产品行为由**用户授权**改变 ⇒ 该用例**按新语义重钉**：
  报告**仍为 `WARN`**、四条 `TOOL_RISK_ELEVATED` **仍在**、但冻结**现在可完成**且留痕在场；
  **同时新增成对反证**（撤掉 policy 里 `code.execute` 的允许 ⇒ 回到拒冻 + 点名 `code.execute`）。
  该文件第 2 条 `test_the_execute_provider_is_high_risk_by_construction`（`classify_risk` 不变）
  **一字不改**。**这不是「改断言迁就」**：被测行为本身是被授权的目标，且反证成对。
- **D-6 依赖与姿态**：**不新增依赖**（纯标准库 + 既有件）、不改 workflow、不动
  `tests/egress_guard.py` 与放行面；本 PLAN 全程**离线**（零出网、零真实容器）。
  真实 run（含真实容器）归 **EC-02** 的后续 cycle。

## 验收条件（逐条如实）

| # | 条件 | 判据（可复跑命令 + 期望值） | 结论 |
| --- | --- | --- | --- |
| AC-1 | **允许通道**：策略显式允许的 EXECUTE 能力 ⇒ 报告仍 `WARN` 但**冻结可完成** | 新判据文件：`report.status is WARN` 且 `report.passed is False` 且 `freeze_manifest(...)` 返回 manifest（不抛） | PENDING |
| AC-2 | **留痕**：manifest 与 `manifest.frozen` payload 里含「哪条策略 / 哪个能力 / 何时」 | 同文件：`manifest.accepted_policy_exceptions` 非空且每条含七项；`frozen_payload(...)` 同源同值（含 `code.execute` / `phase:execution` / `policy_version` / `accepted_at`） | PENDING |
| AC-3 | **拒冻反证（成对，先红后绿）**：撤掉策略允许 ⇒ **回到拒冻**且**点名**缺失事实 | 同文件：把 catalog 的 policy 换成「无 `code.execute` 允许」的版本 ⇒ `pytest.raises(ManifestFreezeError)` 且消息含 `code.execute`；复原 ⇒ 复绿 | PENDING |
| AC-4 | **留痕反证**：去掉留痕 ⇒ 判据红 | 临时把留痕列表改成空（按压）⇒ AC-2 的判据红；复原 ⇒ 绿（按压记录落 RECHECK） | PENDING |
| AC-5 | **其它警示不可转换**：非 EXECUTE 风险 / 其它 WARNING 仍**一律拒冻** | 同文件新增两条：`BUDGET_RESOURCE_UNMAPPED` ⇒ 拒；`POLICY_APPROVAL_REQUIRED` ⇒ 拒；伪装的 `CRITICAL`（DESTRUCTIVE provider）⇒ 拒 | PENDING |
| AC-6 | **语义不变**：`classify_risk` / `PreflightStatus` / `passed` / finding 生成**逐字未改** | 既有判据全绿（`tests/application/test_m2_policy_budget.py`、`test_m2_audit.py`、`test_protocol_compiler.py`、`test_m12_manifest_freeze.py`、`tests/e2e/test_orchestration_convergence.py`）+ `test_the_execute_provider_is_high_risk_by_construction` 一字未改 | PENDING |
| AC-7 | **端到端（离线、run-ready 装配）**：`sort_analysis_v1` 的 run **过冻结** | 新/重钉判据：run 的 `manifest_digest` 非空且事件链里有 `manifest.frozen`、payload 含留痕 | PENDING |
| AC-8 | **门与治理**：规模门禁（50 行函数 / 450 行文件）+ 定向套件 + m0 23/23 + `validate.py` 绿 | `make validate-all`（DSN 固化 + `LLM_MAIN_KEY=""`）+ `ruff check` / `ruff format --check` / `mypy` + `python .cursor/skills/governance-check/scripts/validate.py` | PENDING |
| AC-9 | **零出网**：本 PLAN 全程默认门离线 | 每条 pytest 输出 `egress guard: judged N; blocked 0`；未开 live 开关、未读凭据值 | PENDING |

## 实施清单

- [ ] **WP1** 产品面：`packages/application/preflight/policy_acceptance.py`（通道判定 + 留痕构造 +
      点名拒冻消息）+ `freeze_manifest` 接线 + `RunManifest.accepted_policy_exceptions` +
      `frozen_payload` 同步。
- [ ] **WP2** 判据（离线）：新文件 `tests/application/preflight/test_policy_allowed_execute_freeze.py`
      覆盖 AC-1…AC-5（含按压记录）。
- [ ] **WP3** 端到端 + 重钉：`tests/e2e/test_sandbox_experiment_reachability.py` 第 3 条按 D-5
      重钉为**成对**形态（新语义 + 撤允许反证）；必要时把「过冻结」的 e2e 判据落到同一文件。
- [ ] **WP4** 记录：`RECHECK-*`（cycle 收口）+ GOAL 回写（EC-01 status_note / 迭代日志 / 台账）。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 阻断点现状（报告 `WARN`、冻结拒） | `pytest tests/e2e/test_sandbox_experiment_reachability.py -q`（改动前：3 passed） |
| E-2 | 策略已显式允许 `code.execute` | 读 `examples/config/policy.yaml:33-36`（`allow_with_constraints`） |
| E-3 | 通道判定与留痕 | WP2 新判据的逐条输出（含按压） |
| E-4 | 规模门与治理 | `make validate-all` 23/23、`validate.py` exit 0、`ruff`/`mypy` 输出 |
| E-5 | 零出网 | 各 pytest 的 `egress guard: judged N; blocked 0` 行 |

## 影响报告

- **Domain / API / schema**：`RunManifest` **新增 optional 字段**（`accepted_policy_exceptions`，
  缺省空列表 ⇒ 既有 digest 与行为逐字不变）；**无迁移**（manifest 不进 DB 的独立列，沿用既有
  快照序列化面）。API 读面：`manifest.frozen` 事件 payload 多一个键（**加性**）。
- **产品代码**：`packages/application/preflight/preflight.py`（`freeze_manifest` 接线）、
  `packages/application/run_orchestration/eventing.py`（payload 加性）、新模块 `policy_acceptance.py`。
- **CI / workflow**：不改。
- **安全 / 凭据**：零出网、零凭据读取；**不放宽 §9 任一条默认 deny 面**；通道只接受
  **策略已显式允许**的 EXECUTE 风险，且**只**接受该一种警示。
- **上游版本影响**：无。
- **下一项任务**：EC-02（真实实验执行链：`sort_analysis_v1` 真实 LLM + 既有 Docker 后端跑到终态）。

## 状态历史

- 2026-09-23：derive（WP0）。定案 D-1…D-6 写死；未改任何产品代码、未发起任何出站。
