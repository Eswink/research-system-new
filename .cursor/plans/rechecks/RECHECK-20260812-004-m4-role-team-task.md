---
id: RECHECK-20260812-004
plan_id: PLAN-20260812-004
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-12
completed_at: 2026-08-12
reviewer: root-agent-independent-pass
baseline_ref: c31c8b7（M1/M2/M3 DONE，m0 18 checks 全绿）
checked_head: working-tree
---

# RECHECK-20260812-004 — M4 Role / Team / Task 复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260812-004-m4-role-team-task.md`
- 验收条件：AC-01 至 AC-12
- 变更范围：TaskContract/HandoffBundle/AcceptanceCriterion、RoleDefinition/AgentSpec 配置面、
  Skill 目录与 schema、activation/collapsing 引擎、selection_strategy、phase→agent 绑定投影、
  Preflight role checks、6 个 schema 与 validator 注册、文档漂移修复、BACKLOG/CHANGELOG。
- 基线：HEAD `c31c8b7`（M2 复审 PASS 后的提交）；M4 变更处于未提交工作区，本次独立复审以
  工作区为事实来源，并独立运行行为抽查（不依赖测试名义）。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | 变更全部位于 M4 批准范围（8 个交付面）；`.importlinter.domain` 1 kept 0 broken（68 files/267 deps）；`.importlinter.application` 2 kept 0 broken；`.importlinter.relay` 1 kept 0 broken；domain 无 openhands/litellm/厂商 SDK import | PASS |
| G-02 | 验收条件 | 见下表 AC-01..AC-12 逐项独立证据 | PASS |
| G-03 | lint/typecheck/test | `run_all_checks.py --profile m0 --keep-going` 18/18 PASS；`uv run pytest` 528 passed | PASS |
| G-04 | 安全与权限 | Reviewer 写 Claim truth 经 `forbidden_capabilities` + preflight AGENT_PERMISSION_DENIED 拒绝（独立行为抽查 status=FAIL）；无新凭据；secret 处理未触碰 | PASS |
| G-05 | 兼容性与迁移 | `validate_bundle.py` PASS（4 个新 schema 注册、role/agent/skill/contract 交叉引用一致）；governance `validate.py` PASS；VERSION=0.4.0 单一版本源未变；零新增依赖 | PASS |
| G-06 | 计划、记忆、供应链 | PLAN-20260812-004 + ALL_PLAN 登记；recheck 本文件；无新增依赖（上游策略不变） | PASS |

## 验收条件逐项证据

| AC | 交付项 | 独立证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | 26 Role fixtures/3 模板/6 Skill 机器可加载；Role 不绑定模型 | `tests/loaders/test_contract_loaders.py`（26 roles 断言、teams ⊇ {lean,standard,rigorous}、skills 6 项）；`validate_bundle.py` 强制 Role Catalog/fixture parity 26；RoleDefinition 无模型字段（roles.py） | PASS |
| AC-02 | per-Agent model binding 全配置面 | `tests/loaders/test_contract_loaders.py::test_load_agents_extended_config_surface`（context/runtime_kind/budget_policy_ref/skill_refs/capability_refs）；agent-spec.schema.json 全字段 | PASS |
| AC-03 | 同 Role 多 Agent 异构模型 | agents.yaml reviewer_a（reviewer_gamma）/reviewer_b（research_alpha）不同主模型；`validate_bundle.py` reviewer_models 集合检查 | PASS |
| AC-04 | TaskContract 三字段不丢弃；HandoffBundle 结构化 + loader | `tests/loaders/test_contract_loaders.py::test_load_task_contracts_carries_extended_fields`、`test_load_handoff_bundle_from_fixture`；handoff digest 强校验（sha256 pattern） | PASS |
| AC-05 | AcceptanceCriteria 求值器 9 类 + fail-closed | `tests/domain/test_tasks_acceptance.py`（48 项断言 + 9 类参数化）；独立抽查：无 validator→False、schema 合法→True、非法→False | PASS |
| AC-06 | activation/collapsing 引擎 | `tests/domain/test_activation.py`（12 项：5 策略分支 + folding + pool override）；折叠仅在 default_skills 声明时允许 | PASS |
| AC-07 | required_roles → phase→role→agent 绑定投影 | `tests/application/test_m4_resolution_extended.py`（7 项）；独立抽查：真实 assets domain_discovery → {domain_researcher: (domain_a,), literature_scout: (scout_a, scout_b)} | PASS |
| AC-08 | Preflight 集成（3 个 role 类 finding code） | `tests/application/test_m4_preflight_roles.py`（8 项：ROLE_DISABLED/AGENT_PERMISSION_DENIED/HETEROGENEITY_VIOLATION）；`tests/loaders/test_example_protocol_integration.py` 端到端 FAIL | PASS |
| AC-09 | Reviewer 只读 / Writer 权限 deny 测试 | `tests/application/test_m4_preflight_roles.py::test_permission_check_rejects_forbidden_capability`（evidence.write 被拒）；独立抽查：Reviewer 请求 evidence.write → status FAIL + AGENT_PERMISSION_DENIED | PASS |
| AC-10 | 角色/Agent/模型能力/权限启动前 FAIL | `tests/application/test_m4_preflight_roles.py::test_compile_and_preflight_fails_on_disabled_role`（FAIL）；`test_m4_resolution_extended.py::test_unregistered_role_is_compile_finding`；真实 assets 端到端 preflight FAIL（独立抽查） | PASS |
| AC-11 | 无 OpenHands/LiteLLM/厂商 SDK 泄漏 | `.importlinter.domain` 0 broken；grep domain 无外部 SDK import；mypy 122 files success | PASS |
| AC-12 | 全部门禁 | m0 profile 18/18 PASS；`validate_bundle.py` PASS；governance `validate.py` PASS；pytest 528 passed；源码限制（300 行/50 行函数）通过 | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| R-001 | ERROR | 早期实现 `RoleActivationResult`/`PhaseAssignment` 放在 protocols.py 导致 300 行超限、`RolePool.activation_policy` 默认 ON_DEMAND 掩盖 role 默认策略 | 拆出 `team_plan.py`/`activation.py`/`assignments.py`/`selection.py`/`acceptance.py`；activation_policy 改 None=继承；全量回归 528 passed |
| R-002 | MAJOR | `_role_findings` 重构期间产生损坏代码与重复定义 | 重写 resolution.py 完整文件（295 行）并全量回归；mypy/lint/format 全绿 |
| R-003 | INFO | ROLE_DISABLED 为防御性 check（编译期不会产生"未激活但被分配"状态，DISABLED 已在编译期以 ROLE_CAPACITY 阻断） | 测试以手工构造 plan 验证 check 行为，语义保留为纵深防御 |
| R-004 | INFO | COST_AWARE/EVAL_SCORE_AWARE 编译期无数据源退化 FIXED | 已在 selection.py 与 ROLE_MODEL.md §7 文档记录 |

## 结论

- 结果：`PASS`
- 理由：AC-01~AC-12 均有可复现测试/校验证据；独立行为抽查（真实 assets 端到端、权限 deny、
  求值器 fail-closed）与测试一致；m0 18 项门禁全 PASS；双契约 validator 全 PASS；依赖边界
  3 份 import-linter 契约 0 broken；VERSION 未变、零新增依赖。M4 未降低 DoD、未修改验收标准、
  未删除失败测试、未放宽权限/Preflight gate。
- 后续动作：M4 判定 DONE 并停在阶段边界；更新 ALL_PLAN provenance；后续评估 M5 Ports/Fakes
  就绪度，不自动开始下一开发阶段。