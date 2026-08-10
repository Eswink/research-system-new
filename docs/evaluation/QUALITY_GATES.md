# Quality Gates v0.2.2

## Gate Result

```text
PASS
PASS_WITH_WARNINGS
REVISE
BLOCK
```

## Gate Examples

### Preflight

- Model eligibility；
- Tool/credential；
- budget；
- workspace；
- protocol validity。

### Evidence

- claim coverage；
- source identity；
- contradictory evidence handled。

### Experiment

- code/environment/input digest；
- expected metrics；
- exit status；
- statistical checks。

### Deliverable

- verified claim mapping；
- citation mapping；
- no fabricated metric；
- target requirements。

## Score

分数只用于排序和可视化。

任何 Hard Invariant 失败时，即使总分高也必须 BLOCK。
