---
id: PLAN-20260812-004
slug: m4-role-team-task
title: M4 Role / Team / Task 实施
status: DONE
created_at: 2026-08-12
updated_at: 2026-08-12
cursor_plan_uri: "m4-role-team-task"
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "M4 — Role / Team / Task（用户批准，planUri m4-role-team-task_149d1db1）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260812-004-m4-role-team-task.md
memory_entries:
  - .cursor/memory/entries/MEM-20260812-004-m4-role-team-task.md
---

# PLAN-20260812-004 — M4 Role / Team / Task 实施

## 目标

在 M1/M2/M3 基础上把 Role/Agent/Task 概念补齐为可配置、可解析、可验证的
Research Team：Role activation/collapsing、Agent 全配置面、TaskContract /
AcceptanceCriteria / HandoffBundle、required_roles 稳定解析与 Preflight 集成，
为 M5 Ports/Fakes、M6 OpenHands Runtime、M7 Vertical Slice 提供稳定契约。
不实现 OpenHands Runtime / WorkflowEngine / Agent Principal（阶段边界）。

## 范围

- 包含：TaskContract 三字段（input_schema/budget/failure_policy）、AcceptanceCriterion
  结构化参数与求值器、HandoffBundle 结构化（created_at/producer refs）+ loader、
  RoleDefinition（default_skills/forbidden_capabilities）、AgentSpec 全配置面
  （skill_refs/capability_refs/context/runtime_kind/budget_policy_ref）、Skill 目录、
  Role activation/collapsing 引擎、RolePool selection_strategy、phase→role→agent
  绑定投影、role 类 PreflightFindingCode 与 checks、heterogeneous reviewer 约束。
- 不包含：M5 全量 Ports/Fakes、M6 OpenHands 执行、M7 队列/lease/outbox/执行期
  retry、真实外部 LLM/网络/凭据、AgentRun 状态机与 Agent Principal 实体。

## 验收条件

- [x] AC-01：26 Role fixtures、3 模板、6 Skill 机器可加载；Role 不绑定具体模型。
- [x] AC-02：per-Agent model binding 完整配置面（model/skill/capability/workspace/context/runtime/budget）。
- [x] AC-03：同一 Role 多 Agent 异构模型（reviewer_a/reviewer_b 不同主模型）。
- [x] AC-04：TaskContract 三字段不静默丢弃；HandoffBundle 结构化字段 + loader + digest 强校验。
- [x] AC-05：AcceptanceCriteria 求值器覆盖 9 类，SCHEMA_VALID 经 jsonschema，fail-closed。
- [x] AC-06：Role activation/collapsing 引擎纯函数实现；折叠仅在声明等价 Skill 时允许。
- [x] AC-07：required_roles → phase→role→agent 稳定绑定投影进入 CompiledRunPlan。
- [x] AC-08：Preflight 集成：ROLE_DISABLED/AGENT_PERMISSION_DENIED/HETEROGENEITY_VIOLATION。
- [x] AC-09：Reviewer read-only / Writer 不得改 Claim truth / Experiment metric 有 permission deny 测试。
- [x] AC-10：角色缺失/Agent 缺失/模型能力/权限问题在启动前 FAIL（机器可读 finding）。
- [x] AC-11：不引入 OpenHands/LiteLLM/厂商 SDK 到 Domain（import-linter 守护）。
- [x] AC-12：全量 test/lint/typecheck/architecture/bundle/governance 门禁通过。

## 实施清单

- [x] STEP-01：基线核对（m0 18 checks 全绿，HEAD c31c8b7）。
- [x] STEP-02：TaskContract/HandoffBundle/求值器 + domain 测试。
- [x] STEP-03：Role/Agent 配置面 + skill schema/loader/fixtures + validator 同步。
- [x] STEP-04：activation/collapsing 引擎 + selection_strategy。
- [x] STEP-05：phase→agent 绑定投影 + role 未注册分支 + 编译测试。
- [x] STEP-06：Preflight role checks + 端到端测试。
- [x] STEP-07：文档漂移修复 + BACKLOG/CHANGELOG 更新。
- [x] STEP-08：全量门禁 + 独立 recheck + DoD 报告。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | AC-01~03 | file/test | `examples/config/{roles,agents,team_templates,skills}.yaml`；`tests/loaders/test_contract_loaders.py`（26 roles/8 agents/3 templates/6 skills） | PASS |
| EV-02 | AC-04 | file/test | `packages/domain/tasks.py`、`adapters/contracts/tasks_loaders.py`；`tests/domain/test_tasks_acceptance.py`、`tests/loaders/test_contract_loaders.py` | PASS |
| EV-03 | AC-05 | file/test | `packages/domain/acceptance.py`（9 类求值器，48 项 domain 断言） | PASS |
| EV-04 | AC-06 | file/test | `packages/domain/activation.py`；`tests/domain/test_activation.py`（12 项） | PASS |
| EV-05 | AC-07 | file/test | `packages/application/protocol_compile/{resolution,assignments,selection}.py`；`tests/application/test_m4_resolution_extended.py`（7 项） | PASS |
| EV-06 | AC-08~10 | file/test | `packages/application/preflight/role_checks.py`；`tests/application/test_m4_preflight_roles.py`（8 项）；`tests/loaders/test_example_protocol_integration.py`（端到端） | PASS |
| EV-07 | AC-11 | check | `.importlinter.domain` 0 broken；mypy 122 files success | PASS |
| EV-08 | AC-12 | check | `run_all_checks.py --profile m0 --keep-going` 18/18 PASS；`validate_bundle.py` PASS；`governance validate.py` PASS；全量 pytest 528 passed | PASS |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-12 | RolePool.activation_policy 改为可选（None=继承 Role activation_default） | 模板 fixture 均未显式配置，原 ON_DEMAND 默认值会掩盖 role 默认策略 | 激活语义由 role 默认策略驱动 |
| 2026-08-12 | heterogeneous 约束以编译期检查实现，不加 model_diversity_rule 字段 | 文档字段无 schema/代码承载，约束语义更简单 | 计划决策：以约束替代字段 |
| 2026-08-12 | COST_AWARE/EVAL_SCORE_AWARE 编译期退化为 FIXED | 运行时成本/评分数据源在 M5+ | 文档记录退化语义 |
| 2026-08-12 | handoff fixture 顶层为单条对象（非集合） | 与 validator 的 validate_strict_instance 一致 | loader 为单条加载 |
| 2026-08-12 | rigorous 模板不扩展 literature_scout | fixture 与文档声明冲突，以最小契约为准修正文档 | TEAM_TEMPLATES.md 已对齐 |
| 2026-08-12 | 独立复审修复：reviewer_b 主模型 research_alpha → coding_beta | 原配置使 writer(review_alpha) 与 reviewer_b 共享模型，与 HETEROGENEITY_VIOLATION 前置相悖 | 真实 fixtures 现在 writer/reviewer 模型不相交（集成测试守护） |
| 2026-08-12 | 独立复审修复：check_heterogeneity 按 role 聚合模型并逐对输出 | 原实现 Reviewer 角色缺位时 set().union() 崩溃；单条笼统 message 不可读 | 崩溃场景与 message 可读性均有测试 |
| 2026-08-12 | 独立复审修复：AgentSpec.workspace_policy 改 Optional（None=继承 Role），编译期 WORKSPACE_POLICY_VIOLATION + agent_workspace_policies 投影 | 原默认 READ_ONLY 无法区分“显式 read_only”与“未配置”，ExperimentEngineer 的 isolated_writable 继承语义丢失 | schema/loader/domain/compiler 同步；engineer 有效策略投影为 isolated_writable |
| 2026-08-12 | 独立复审修复：domain_researcher 增加 evidence.read | skill evidence_modeling 展开 evidence.read 越出角色请求面，真实 assets 端到端出现 AGENT_PERMISSION_DENIED | 集成测试断言该 finding 不在真实 assets 报告内 |
| 2026-08-12 | 技术债收口：agent_workspace_policies 在 compiled-run-plan schema 改必填 | 旧为可选，序列化契约不强制 | fixture 同步 `{}`；validate_strict_instance 强制 |
| 2026-08-12 | 技术债收口：COST_AWARE/EVAL_SCORE_AWARE 退化产生 SELECTION_STRATEGY_DEGRADED（INFO） | 原静默退化为 FIXED，退化不可观测 | compiler 不再丢弃非空 findings（INFO/WARNING 随计划携带）；新增 2 项测试 |
| 2026-08-12 | 技术债收口：写面 capability 与有效 workspace policy 静态交叉验证 | 原一致性留给执行期 Policy Wrapper | workspace_policy.py 增加 check_workspace_capability；preflight 拒绝 workspace.write.code 等与 read_only/notes_only 组合 |
| 2026-08-12 | 技术债收口：异构评审角色迁移为 RoleDefinition.review_panel_role 属性 | 原 _WRITER_ROLES/_REVIEWER_ROLES 常量无法支持自定义角色 | enums/schema/loader/fixtures/validator/preflight 同步；自定义 role id 测试通过 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-12 | — | APPROVED | 用户批准 Cursor Plan | `m4-role-team-task_149d1db1` |
| 2026-08-12 | APPROVED | IN_PROGRESS | 开始实施 | STEP-01 |
| 2026-08-12 | IN_PROGRESS | DONE | 全部 AC 有可复现证据；独立复审 PASS | RECHECK-20260812-004；m0 18/18 |

## 影响报告

- Domain/API/schema：TaskContract 增加 input_schema/budget/failure_policy；HandoffBundle 增加
  created_at/producer_agent_id/producer_role_id；RoleDefinition 增加 default_skills/
  forbidden_capabilities；AgentSpec 增加 skill_refs/capability_refs/context/runtime_kind/
  budget_policy_ref；新增 team_plan（RoleActivationRecord/PhaseAssignment）、activation、
  acceptance 模块；PreflightFindingCode 增加 ROLE_DISABLED/AGENT_PERMISSION_DENIED/
  HETEROGENEITY_VIOLATION；schema 新增 skill/domain_discovery_input_v1/experiment_run_input_v1，
  扩展 role-definition/agent-spec/compiled-run-plan/handoff-bundle/task-contract。
- 安全/凭据：无新凭据；权限差异以 forbidden_capabilities + preflight 检查承载；Reviewer 只读
  有 deny 测试。
- 兼容性/迁移：VERSION 保持 0.4.0；新字段均为向后兼容扩展；compiled-run-plan schema 新增
  可选 role_activations/phase_assignments；handoff digest 收紧为 sha256 格式（fixture 已更新）。
- 上游版本：零新增依赖。
- 下一项任务：M4 已完成，停在阶段边界；M5 Ports/Fakes 就绪（TaskContract/HandoffBundle/
  TeamTemplate/AgentSpec/RoleDefinition 稳定契约 + AgentSpec 全配置面）；M6 可直接消费
  AgentSpec 构成 AgentSessionSpec；M7 全链路闭环具备契约基础。