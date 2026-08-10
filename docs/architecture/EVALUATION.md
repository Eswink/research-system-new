# Evaluation Architecture v0.2.2

## 1. 五层评测

```text
Software Correctness
Runtime/Tool Correctness
Security/Policy Correctness
Research Process Correctness
Deliverable Quality
```

## 2. Preflight Evaluation

运行前：

- Model eligibility；
- Tool availability；
- Workspace/compute；
- budget；
- policy；
- protocol/task contract。

## 3. Runtime Evaluation

- schema/output validity；
- stuck/dead loop；
- tool misuse；
- unsupported claim；
- artifact lineage；
- budget adherence。

## 4. Reviewer Panel

```text
ScientificReviewer
MethodologyReviewer
StatisticalReviewer
EvidenceReviewer
TargetFitReviewer
ReproducibilityAuditor
MetaReviewer
```

可绑定不同 ModelDefinition。

多模型只能降低相关性，不能代替确定性验证或人类校准。

## 5. Quality Gate

```text
PASS
PASS_WITH_WARNINGS
REVISE
BLOCK
```

Gate 读取结构化 finding，不从自然语言猜结论。

## 6. Regression

任何变更：

- model
- role
- prompt/context
- tool
- runtime
- protocol
- policy

都需要在固定 Eval Suite 比较。

## 7. Canary

新 Model ID/ToolPack/Runtime Version 先进入 shadow/canary，再成为默认。
