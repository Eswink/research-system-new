# Team Templates v0.4.0

## LEAN

适合验证链路/低预算。

```text
ResearchDirector
DomainResearcher
LiteratureScout ×1
EvidenceCurator
ExperimentDesigner
ExperimentEngineer
ResultAnalyst
ScientificReviewer
ResearchWriter
```

部分 Reviewer/Editor 作为 Skill。

## STANDARD

```text
ResearchDirector
ResearchPlanner
DomainResearcher
LiteratureScout ×2
EvidenceCurator
OpportunityExplorer
IdeaGenerator ×2
Skeptic
Methodologist
ExperimentDesigner
ExperimentEngineer
ResultAnalyst
Statistician
ScientificReviewer ×2
EvidenceReviewer
MethodologyReviewer
MetaReviewer
ResearchWriter
ReproducibilityAuditor
CitationAuditor
```

## RIGOROUS

在 STANDARD 基础上（fixture `examples/config/team_templates.yaml`，`extends: standard`）：

- NoveltyReviewer；
- MethodologyReviewer 扩容（min/max 提高）；
- StatisticalReviewer；
- TargetFitReviewer；
- ReproducibilityAuditor 扩容审计与 Quality Gate；
- ScientificEditor；

注：文档早期版本的"多模型 LiteratureScout"声明已移除——fixture 未对
literature_scout 覆盖模型配置；异构评审约束由 Preflight 的
HETEROGENEITY_VIOLATION 检查承载（见 ROLE_MODEL.md §6）。

## 重要规则

Template 是候选配置，不等于所有 Role 同时常驻。

Protocol Compiler 按 Phase 动态激活（`packages/domain/activation.py`），
激活/折叠结果进入 CompiledRunPlan 的 role_activations / phase_assignments 投影。

每个 Agent 仍可单独选择 ModelDefinition（`model_binding`：EXPLICIT_MODEL /
MODEL_PROFILE / INHERIT）。


## Inheritance Semantics

`extends` 使用确定性 deep merge：

- parent roles 先加载；
- child 同名 Role 完整覆盖 min/max/override；
- child 新 Role 追加；
- 不允许循环继承；
- Compiler 输出 flatten 后的 TeamTemplate digest。
