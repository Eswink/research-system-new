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

Protocol Compiler 根据：

- Phase；
- Task complexity；
- budget；
- model/tool availability；
- quality target；

生成实际 Team Plan。

## 4. Role Collapsing

简单项目中：

```text
CitationGraphResearcher → LiteratureScout 的 Skill
ScientificEditor        → ResearchWriter 的 Skill
```

不要为了角色目录而实例化 Agent。

## 5. Per-Agent Model Binding

```text
Agent explicit ModelDefinition
→ Role default ModelProfile
→ TeamTemplate override
→ Project default
→ System default
```

解析结果在 Preflight 和 RunManifest 中冻结。

## 6. Heterogeneous Panel

```text
ScientificReviewer-A → model-alpha
ScientificReviewer-B → model-beta
EvidenceReviewer     → model-gamma
MetaReviewer         → model-alpha
```

同一模型不应同时承担 Writer、所有 Reviewer 和最终 MetaReviewer，除非用户明确选择低成本模式。

## 7. Agent Pool

RolePool 支持：

```text
min_instances
max_instances
concurrency
selection_strategy
model_diversity_rule
```

Selection Strategy：

```text
FIXED
ROUND_ROBIN
CAPABILITY_BEST_FIT
COST_AWARE
EVAL_SCORE_AWARE
```

## 8. User-defined Role

允许自定义 Role，但必须：

- schema valid；
- requested capabilities 可审计；
- output contract 明确；
- 不绕过 Policy；
- 不直接获取 Secret。
