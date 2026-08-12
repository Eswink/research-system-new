---
id: MEM-20260812-004
title: M4 Role/Team/Task 配置面、激活引擎与 Preflight 集成事实
status: ACTIVE
created_at: 2026-08-12
updated_at: 2026-08-12
scope: repository
confidence: 0.95
review_after: 2026-11-12
source_plans:
  - .cursor/plans/tasks/PLAN-20260812-004-m4-role-team-task.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260812-004-m4-role-team-task.md
supersedes: []
tags: [m4, role, agent, team, task-contract, handoff, activation, preflight, permission]
---

# MEM-20260812-004 — M4 Role/Team/Task 配置面、激活引擎与 Preflight 集成事实

## 做了什么

M4 完成并独立复审 PASS：m0 profile 18/18 门禁、528 pytest、双契约 validator 全绿。落地事实：

1. `TaskContract` 补齐 `input_schema` / `budget`（Decimal 或 null）/ `failure_policy`
   （string/bool/int/string[] 值）；`AcceptanceCriterion` 结构化参数
   （artifact/minimum_sources/metric/operator/threshold/evaluator/description），
   求值器 `packages/domain/acceptance.py` 覆盖 9 类，SCHEMA_VALID 经 jsonschema，
   未注入校验器时 fail-closed；CUSTOM_EVALUATOR 必须由编排层执行不自动通过。
2. `HandoffBundle` 增加 `created_at`（UTC）/ `producer_agent_id` / `producer_role_id`，
   digest 强校验 `sha256:<64 hex>`；加载器 `load_handoff_bundles`（单条顶层对象，
   与 bundle validator 的 validate_strict_instance 一致）。
3. `RoleDefinition` 增加 `default_skills`（可折叠等价 Skill 声明）与
   `forbidden_capabilities`（请求与禁止交集构造时报错）；`AgentSpec` 增加
   `skill_refs` / `capability_refs` / `context`（max_context_tokens/max_iterations）/
   `runtime_kind`（BackendKind 枚举，仅配置面）/ `budget_policy_ref`。
4. `RolePool.activation_policy` 改为可选（None=继承 role 的 activation_default），
   模板 fixture 不显式配置时由 role 默认策略驱动。
5. Role activation/collapsing 引擎 `packages/domain/activation.py::activate_roles`
   纯函数：ALWAYS / REQUIRED_BY_PROTOCOL / ON_DEMAND / BUDGET_PERMITTING / DISABLED；
   折叠仅在 `default_skills` 声明时允许，DISABLED 且被协议要求产生 ERROR finding。
6. RolePool `selection_strategy` 进入编译期选择（`protocol_compile/selection.py`）：
   FIXED / ROUND_ROBIN（稳定轮转）/ CAPABILITY_BEST_FIT（capability_refs 交集排序）/
   COST_AWARE / EVAL_SCORE_AWARE（后两者编译期无数据源，确定性退化为 FIXED）。
7. `CompiledRunPlan` 增加 `role_activations` 与 `phase_assignments` 投影
   （`packages/domain/team_plan.py`）：phase→role→agent 稳定绑定，未激活 role 不分配 agent。
8. Preflight 集成 `packages/application/preflight/role_checks.py`：
   `ROLE_DISABLED`（防御性）/ `AGENT_PERMISSION_DENIED`（skill/capability 越出 role
   能力面或使用 forbidden capability）/ `HETEROGENEITY_VIOLATION`（同一模型同时承担
   Writer 与 Reviewer/MetaReviewer）。

## 为什么这样做

- **Role 与 Agent 必须分离**（ADR-0011）：Role 声明职责/能力面/权限边界，Agent 声明
  由哪个模型、哪些 Skill/Capability、什么 Workspace/Context/Runtime/Budget 执行；
  权限差异以 `forbidden_capabilities` 显式承载，Reviewer 只读与 Writer 不改 Claim truth
  有 deny 测试（AGENTS.md §11）。
- **Skill 只请求 Capability 不授予权限**：Skill 目录（`schemas/skill.schema.json` +
  `examples/config/skills.yaml`）只声明 capabilities；agent 能力面由 role.requested_capabilities
  边界约束，preflight 在启动前拦截越界。
- **验收判定必须有确定性事实源**："LLM 不能自行宣布验收通过"落实为
  `CriterionInputs` 显式注入 + fail-closed 求值，杜绝聊天记录作为唯一验收依据。
- **激活/折叠进 plan 而非只进文档**：Protocol 只请求 Role/RolePool，编译期聚合后生成
  role_activations / phase_assignments 投影，Preflight 与 Manifest 冻结可见。
- **异构评审约束以检查实现而非加字段**：`model_diversity_rule` 无 schema 承载，
  编译期检查（HETEROGENEITY_VIOLATION）语义更简单且可测试。
- **规模门槛是硬约束**：activation/acceptance/team_plan/assignments/selection 拆分
  后单文件 ≤300 行、函数 ≤50 行才过 `test_python_source_limits.py`。

## 怎么做与复现

1. 全量门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going` → 18 checks PASS。
2. 单元测试：`uv run --frozen --no-sync python -B -m pytest` → 528 passed。
3. 契约 validator：`python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`、`python -B .cursor/skills/governance-check/scripts/validate.py`。
4. 依赖边界：`uv run lint-imports --config .importlinter.domain` → 1 kept 0 broken；
   `.importlinter.application` → 2 kept 0 broken。
5. 端到端抽查：真实 assets compile → `phase_assignments[domain_discovery] =
   {domain_researcher: (domain_a,), literature_scout: (scout_a, scout_b)}`；
   AGENT_MISSING 阻断 → preflight FAIL。

## 适用边界

- 适用于：M5 Ports/Fakes 以 `TaskContract`/`HandoffBundle`/`TeamTemplate`/`AgentSpec`/
  `RoleDefinition` 为稳定契约；M6 OpenHands Adapter 以 AgentSpec 全配置面 + TaskContract
  构成 `AgentSessionSpec`；M7 以 phase_assignments 决定 phase 的 agent 实例，
  以 AcceptanceCriterion 求值器做结构化输出验收。
- 不适用于：M6 运行时执行与 resume/drift 语义（Manifest Revision 属 M6）；
  M7 队列/lease/outbox/执行期 retry（at-least-once + idempotency 在 M7 实现）；
  Agent Principal 实体（ADR-0022，M5/M6 运行时边界）；真实 LLM 集成测试（默认离线）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-12）。
- `RolePool.activation_policy` 语义变更（如恢复默认 ON_DEMAND）。
- `PreflightFindingCode` role 类新增变体未同步 preflight-report 文档与测试。
- COST_AWARE/EVAL_SCORE_AWARE 引入运行时数据源而改变退化语义。
- `test_python_source_limits.py` 或 ruff 阈值调整。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260812-004-m4-role-team-task.md` | M4 范围与验收 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260812-004-m4-role-team-task.md` | PASS 结论与发现清单 |
| repository | `packages/domain/activation.py` | 激活/折叠纯函数语义 |
| repository | `packages/domain/acceptance.py` | 9 类验收求值器 + fail-closed |
| repository | `packages/application/preflight/role_checks.py` | 3 个 role 类 finding code |
| repository | `packages/application/protocol_compile/{assignments,selection}.py` | phase 绑定投影与 selection 退化 |
| repository | `schemas/{role-definition,agent-spec,skill,task-contract,handoff-bundle,compiled-run-plan}.schema.json` | 配置面契约 |