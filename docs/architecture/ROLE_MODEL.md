# Role, Team & Agent Model v0.4.0

## 1. 分层

```text
RoleDefinition
      ↓ instantiate
AgentSpec
      ↓ assignment
ResearchTask
      ↓ execution
AgentRun / AgentSession
```

Role 定义职责；Agent 定义模型、Skill、Capability、Workspace、预算和 Runtime；Task 定义本次要完成什么。

## 2. TeamTemplate

用户不应该第一次就配置 26 个 Role。

系统提供：

```text
LEAN
STANDARD
RIGOROUS
CUSTOM
```

Template 只定义候选 RolePool 和默认实例数，不强制全部启动。

## 3. RoleActivationPolicy

```text
ALWAYS
REQUIRED_BY_PROTOCOL
ON_DEMAND
BUDGET_PERMITTING
DISABLED
```

实现：`packages/domain/activation.py::activate_roles`（纯函数）。Protocol Compiler 按
phase 聚合 required roles 后生成 `RoleActivationRecord` 投影进入 `CompiledRunPlan`；
DISABLED 且被协议要求时产生 ERROR finding，Preflight 不放行。Role 未声明等价
Skill 时 REQUIRED_BY_PROTOCOL / ON_DEMAND 折叠只产生"未激活"决策，不产生 agent。

## 4. Role Collapsing

简单项目中：

```text
CitationGraphResearcher → LiteratureScout 的 Skill
ScientificEditor        → ResearchWriter 的 Skill
```

Role 通过 `default_skills` 声明可折叠等价 Skill；折叠只在 Role 显式声明时允许
（RESEARCH_PROTOCOL.md §6），未声明的角色不折叠。不要为了角色目录而实例化 Agent。

## 5. Per-Agent Model Binding

```text
Agent explicit ModelDefinition
→ Role default ModelProfile
→ TeamTemplate override
→ Project default
→ System default
```

解析结果在 Preflight 和 RunManifest 中冻结。

### Workspace Policy

Agent 未显式配置 `workspace_policy` 时继承 Role 默认策略；有效值投影进
CompiledRunPlan 的 `agent_workspace_policies`（Preflight 冻结）。显式配置不得
宽于 Role 边界（WORKSPACE_RUNTIME.md §3 的 Role-aware Policy）：

- Role `read_only` → Agent 只能 `read_only`；
- Role `notes_only` → Agent ∈ {`read_only`, `notes_only`}；
- Role `deliverable_only` → Agent ∈ {`read_only`, `deliverable_only`}；
- Role `isolated_writable` → Agent 任意。

越界配置在编译期产生 `WORKSPACE_POLICY_VIOLATION` finding，Preflight 不得放行。
示例：`experiment_engineer` 未配置 → 继承 `isolated_writable`；`reviewer_a/b`
显式 `read_only` 与 Role 一致。

## 6. Heterogeneous Panel

```text
ScientificReviewer-A → model-alpha
ScientificReviewer-B → model-beta
EvidenceReviewer     → model-gamma
MetaReviewer         → model-alpha
```

同一模型不应同时承担 Writer、所有 Reviewer 和最终 MetaReviewer，除非用户明确选择
低成本模式。实现：`packages/application/preflight/role_checks.py::check_heterogeneity`
（HETEROGENEITY_VIOLATION），`Preflight` 在启动前拦截 writer/reviewer 共享模型的
配置；示例 fixture 中 reviewer_a/reviewer_b 使用两个不同主模型（validate_bundle 校验）。

RoleDefinition 通过可选字段 `review_panel_role`（`WRITER` / `REVIEWER` / `NONE`，
缺省 `NONE`）声明在评审面板中的角色；异构约束按该属性聚合，不依赖 role id，
因此自定义角色也可以进入独立评审面板。示例中 `research_writer` / `scientific_editor`
为 WRITER，`scientific_reviewer` / `evidence_reviewer` / `meta_reviewer` 为 REVIEWER，
其余角色 NONE（不参与异构计算）。

## 7. Agent Pool

RolePool 支持：

```text
min_instances
max_instances
concurrency
selection_strategy
activation_policy
```

Selection Strategy：

```text
FIXED
ROUND_ROBIN
CAPABILITY_BEST_FIT
COST_AWARE
EVAL_SCORE_AWARE
```

实现：`packages/application/protocol_compile/selection.py::select_agents`。编译期
无运行时成本/评分数据源，COST_AWARE / EVAL_SCORE_AWARE 确定性退化为 FIXED，且
编译期产生 `SELECTION_STRATEGY_DEGRADED`（INFO finding，subject=`role:<id>`）使
退化可见；运行时数据源接入（M5+）后应回填真实选择并移除该 finding。
CAPABILITY_BEST_FIT 按 agent.capability_refs 与 phase 所需 capabilities 交集排序。

## 8. User-defined Role

允许自定义 Role，但必须：

- schema valid；
- requested capabilities 可审计；
- output contract 明确；
- 不绕过 Policy；
- 不直接获取 Secret。
