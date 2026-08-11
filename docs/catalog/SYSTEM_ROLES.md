# System Role Catalog v0.4.0

系统角色是可覆盖的模板，不绑定具体 Model ID。

---

## A. Management

### 1. ResearchDirector

**职责**：研究战略、方向选择、重大 Pivot/Stop/Continue 决策。

推荐 Skill：

- research_strategy
- decision_review

Capabilities：

- research_state.read
- evidence.read
- experiment.read
- decision.propose

Workspace：默认只读。

推荐 ModelProfile：`research_strong`

---

### 2. ResearchPlanner

**职责**：把研究目标拆成 Phase/Task/依赖/资源。

Skill：

- task_decomposition
- protocol_planning

Capabilities：

- research_state.read
- protocol.propose
- budget.read

推荐 ModelProfile：`research_strong`

---

### 3. Supervisor

**职责**：监控偏题、死循环、失败、预算异常，并提出人工/策略升级。

注意：retry/timeout/budget hard limit 由 deterministic controller 执行。

Capabilities：

- run.read
- agent_run.read
- budget.read
- decision.propose

推荐 ModelProfile：`research_fast`

---

## B. Discovery & Evidence

### 4. DomainResearcher

**职责**：领域级搜索与建模：术语、经典路线、子领域、关键团队、技术演化。

Skills：

- domain_mapping
- research_landscape

Capabilities：

- literature.search
- literature.search
- literature.read
- workspace.write.notes
- evidence.propose

推荐 ModelProfile：`research_strong`

---

### 5. LiteratureScout

**职责**：论文/资料发现、筛选、扩展 citation graph、追踪近期工作。

Skills：

- literature_discovery
- citation_chaining

Capabilities：

- literature.search
- literature.read
- citation.inspect
- workspace.write.notes

推荐 ModelProfile：`research_fast`

支持多实例并行。

---

### 6. EvidenceCurator

**职责**：把来源整理成结构化 Evidence，而不是继续泛搜。

输出重点：

```text
Claim
Evidence
Method
Dataset
Metric
Limitation
Contradiction
```

Capabilities：

- literature.read
- evidence.read
- evidence.write
- artifact.read

推荐 ModelProfile：`research_strong`

---

### 7. CitationGraphResearcher

**职责**：专门追踪引用链、研究 lineage、相关工作簇。

Capabilities：

- literature.search
- citation.inspect
- evidence.propose

推荐 ModelProfile：`research_fast`

可在简单项目中退化为 Skill，而非独立 Agent。

---

## C. Exploration & Ideation

### 8. OpportunityExplorer

**职责**：研究 Frontier、矛盾、空白、局限、未验证假设、跨领域机会。

Capabilities：

- evidence.read
- research_map.read
- idea.write

推荐 ModelProfile：`research_strong`

---

### 9. IdeaGenerator

**职责**：生成候选 Research Idea / Hypothesis。

可使用不同 strategy：

- conservative
- cross_domain
- contrarian
- failure_mode
- theory

Capabilities：

- evidence.read
- idea.write

推荐 ModelProfile：`research_strong`

支持多实例 population search。

---

### 10. NoveltyReviewer

**职责**：判断候选是否已有近似工作、是否只是重组、创新声明是否过强。

Capabilities：

- literature.search
- literature.read
- evidence.read
- idea.review

推荐 ModelProfile：`critic_independent`

---

### 11. Skeptic

**职责**：主动寻找反例、trivial explanation、confounder、不可证伪问题和价值不足。

Capabilities：

- evidence.read
- idea.review
- experiment.read

推荐 ModelProfile：`critic_independent`

---

## D. Experiment

### 12. Methodologist

**职责**：研究设计、baseline、control、ablation、metric、validity。

Capabilities：

- evidence.read
- experiment_plan.read
- experiment_plan.write

推荐 ModelProfile：`research_strong`

---

### 13. ExperimentDesigner

**职责**：把 Hypothesis 转成结构化 ExperimentPlan。

输出：

```text
inputs
baseline
variables
controls
metrics
expected result
falsifier
resource estimate
stop criteria
```

Capabilities：

- experiment_plan.write
- dataset.read
- workspace.read

推荐 ModelProfile：`research_strong`

---

### 14. ExperimentEngineer

**职责**：代码、调试、执行、观察、迭代。

Capabilities：

- workspace.read
- workspace.write.code
- code.execute
- git.diff
- experiment.execute
- artifact.read
- artifact.write

Workspace：隔离可写 sandbox/worktree。

推荐 ModelProfile：`coding_strong`

---

### 15. ResultAnalyst

**职责**：分析 metrics、曲线、baseline 差异、异常、confounders，形成 Evidence 候选。

Capabilities：

- experiment.read
- artifact.read
- statistics.execute
- evidence.propose

推荐 ModelProfile：`research_strong`

---

### 16. Statistician

**职责**：统计设计和统计解释。

确定性统计计算必须调用 Tool，不让 LLM 心算。

Capabilities：

- experiment.read
- statistics.execute
- evidence.propose

推荐 ModelProfile：`research_strong`

---

### 17. ReproducibilityAuditor

**职责**：检查 code/environment/seed/dataset/command/artifact/metric lineage。

Capabilities：

- workspace.read
- experiment.read
- artifact.read
- provenance.read
- audit.write

Workspace：只读。

推荐 ModelProfile：`critic_independent`

---

## E. Evaluation & Peer Review

### 18. ScientificReviewer

**职责**：整体科学合理性、论证链、重要性、替代解释。

Capabilities：

- research_state.read
- evidence.read
- experiment.read
- literature.search
- review.write

Workspace：只读。

推荐 ModelProfile：`critic_independent`

---

### 19. MethodologyReviewer

**职责**：实验和方法设计审查。

Capabilities：

- experiment_plan.read
- experiment.read
- evidence.read
- review.write

推荐 ModelProfile：`critic_independent`

---

### 20. StatisticalReviewer

**职责**：独立审查统计结论、effect size、variance、sampling、robustness。

Capabilities：

- experiment.read
- statistics.execute
- review.write

推荐 ModelProfile：`critic_independent`

---

### 21. EvidenceReviewer

**职责**：逐 Claim 审核支持、反证和引用强度。

Capabilities：

- claim.read
- evidence.read
- literature.read
- review.write

推荐 ModelProfile：`critic_independent`

---

### 22. TargetFitReviewer

**职责**：根据 TargetProfile 检查 scope、贡献类型、rubric 和交付要求。

Capabilities：

- target.read
- claim.read
- artifact.read
- review.write

推荐 ModelProfile：`research_strong`

---

### 23. MetaReviewer

**职责**：聚合多 Reviewer finding，处理冲突并生成统一 Decision 建议。

Capabilities：

- review.read
- evidence.read
- decision.propose

推荐 ModelProfile：`research_strong`

---

## F. Deliverable

### 24. ResearchWriter

**职责**：从 Verified Claims、Evidence、Experiment、Decision 组装研究交付物。

可能输出：

- technical report
- research memo
- benchmark report
- reproduction report
- manuscript

Capabilities：

- claim.read
- evidence.read
- experiment.read
- artifact.read
- deliverable.write

推荐 ModelProfile：`research_strong`

ResearchWriter 不能直接把 unsupported prose 变成 VERIFIED Claim。

---

### 25. ScientificEditor

**职责**：结构、语言、逻辑、术语和一致性编辑。

Capabilities：

- deliverable.read
- deliverable.edit

禁止：

- 修改 Claim truth status
- 修改 Experiment metric
- 创建 Evidence

推荐 ModelProfile：`research_fast`

---

### 26. CitationAuditor

**职责**：引用存在性、映射、claim-attribution、一致性审核。

Capabilities：

- deliverable.read
- claim.read
- evidence.read
- literature.read
- citation.validate
- audit.write

推荐 ModelProfile：`critic_independent`

大量规则应 deterministic。

---

## Role 使用原则

1. 一个 Run 不会启动所有 Role。
2. Protocol 决定所需 Role。
3. 同 Role 可以启动多个 Agent。
4. 每个 Agent 可以绑定不同 ModelDefinition。
5. 简单 Role 可退化为 Skill，避免 Agent proliferation。
6. Reviewer 默认 Workspace read-only。
7. ExperimentEngineer 等执行角色使用隔离 Workspace。


## v0.4.0 Role Runtime Matrix

| Role Group | Typical Workspace | Model Hard Requirement | Default Effect |
|---|---|---|---|
| Management | read-only | chat/structured output | decision/proposal |
| Discovery | notes write | chat; tool calling for search | read/network/notes |
| Exploration | read-only + idea output | chat/structured output | proposal |
| ExperimentEngineer | isolated writable | reliable tool calling | write/execute |
| Result/Statistics | artifact read | structured output; tools for calculation | read/analysis |
| Review | read-only | chat/structured output | review only |
| Writer/Editor | deliverable scope | chat | deliverable write |

Role 是否启动由 Protocol Compiler 和 TeamTemplate 决定，不因目录存在而自动实例化。
