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

在 STANDARD 基础上：

- 多模型 LiteratureScout；
- NoveltyReviewer；
- MethodologyReviewer 扩容；
- StatisticalReviewer；
- TargetFitReviewer；
- 更严格的 ReproducibilityAuditor 审计与 Quality Gate；
- ScientificEditor；

## 重要规则

Template 是候选配置，不等于所有 Role 同时常驻。

Protocol Compiler 按 Phase 动态激活。

每个 Agent 仍可单独选择 ModelDefinition。


## Inheritance Semantics

`extends` 使用确定性 deep merge：

- parent roles 先加载；
- child 同名 Role 完整覆盖 min/max/override；
- child 新 Role 追加；
- 不允许循环继承；
- Compiler 输出 flatten 后的 TeamTemplate digest。
