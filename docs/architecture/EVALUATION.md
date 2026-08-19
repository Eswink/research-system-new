# Evaluation Architecture v0.4.0

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

## 8. M11 实现映射（2026-08-15）

本节把 M11 Evaluation Plane 实际实现映射到上述架构，记录当前运行事实。

### 8.1 Eval Harness & Case Registry

- `packages/domain/eval_spec.py`：`EvalCase`（oracle 必须可执行：
  expected 或 rubric 至少其一；description 不参与 digest）、
  `EvalDataset`（frozen，case 按 id 排序参与 digest，静默删除/替换/
  内容变更都会改变 digest）、`EvalScope`（UNIT/INTEGRATION/WORKFLOW）、
  `ScorerRef`（id+version）。
- `packages/domain/eval_result.py`：`ScorerFinding`（PASS/FAIL/
  INFRA_ERROR 三态，INFRA_ERROR 区分评测设施故障与被评对象不合格）、
  `EvalResult`（case+输入+finding 全链追溯）、`EvalScore`（聚合，只用于
  排序/可视化，不替代 gate verdict）、`EvalReport`（report_id/
  generated_at 不参与 digest，replay 身份 = digest）、
  `FrozenConditions`（dataset/gate/scorer/system/input digests；
  `comparison_digest()` 为回归比较键，不含被评输入 digest）。
- `packages/application/evaluation/registry.py`：dict → domain 构造与
  freeze digest 校验（`DatasetFreezeError` fail-closed）。
- `adapters/contracts/eval_loaders.py`：文件 I/O + jsonschema 校验
  （`schemas/eval-dataset.schema.json`）。
- `examples/eval/datasets/unit_v1.yaml` / `integration_v1.yaml`：CI
  确定性评测集（`tools/freeze_eval_dataset.py` 维护 digest）。

### 8.2 Deterministic Scorers

`packages/application/evaluation/scorers.py`（纯函数注册表，
`schema_validity` 实现见 `schema_scorer.py`，自研最小结构校验器，不引入
运行时 jsonschema 依赖）：

```text
exact_match / digest_match / required_fields / numeric_tolerance /
invariant（声明式谓词）/ evidence_source_distinct / schema_validity
```

`scorers_runtime.py` 经现有 Port 的 scorer 工厂：`artifact_integrity`
（ArtifactStore.verify）、`policy_compliance`（PolicyEvaluator）、
`gate_outcome`（把 M7 evaluate_task_gate 作为被观测对象包装）。
IG-1 增补 `scorers_evidence.py`：`evidence_provenance`（EvidenceLedger
校验 Claim/Evidence/Source 完整 provenance，DISPUTED 可见）与
`experiment_reproducibility`（ExperimentRun 的 image/snapshot/artifact
digest 完整性）。
Port 异常一律转换为 INFRA_ERROR。

### 8.3 Reviewer / Panel

- `packages/application/evaluation/reviewer.py`：Reviewer 契约与
  `LlmReviewer`（经 ModelGateway Port；输入只含 rubric + material
  reference，不含 secret；timeout/malformed/unavailable → 结构化
  `ReviewerFinding.failure`，绝不映射为被评对象 FAIL/PASS；记录
  returned model name 与采样参数）。
- `packages/application/evaluation/panel.py`：独立 judgments、票数、
  disagreement 显式记录、PARTIAL_FAILURE/TOTAL_FAILURE 状态；重复
  identity 不算独立 panel。
- 真实 LLM Reviewer 仅显式手动运行；默认 CI 全部 Fake
  （AGENTS.md §11）。

### 8.4 Quality Gate 语义（compute_verdict）

`packages/domain/eval_gate.py` 的 `compute_verdict`（fail-closed）：

1. 任何确定性 FAIL finding → BLOCK（聚合分数/阈值不可掩盖失败）；
2. 任何 INFRA_ERROR → REVISE（评测设施故障不得认证 PASS，也不得判
   被评对象质量失败）；
3. config 规则引用的 scorer 必须实际执行，否则 REVISE；
4. `min_pass_ratio` 不满足 → BLOCK；
5. 其余 → PASS。

`GateConfig` 版本化 + digest；阈值/规则改变即 digest 改变，不得伪装
同一基线。Reviewer judgment 不参与 deterministic gate 输入（reviewer
不是 truth owner）。

### 8.5 Regression / Canary / Calibration

- `packages/application/evaluation/regression.py`：case 集合或评测配置
  （`comparison_digest`）不一致 → 拒绝比较；per-case PASS→FAIL 记
  `newly_regressed`，存在即 BLOCK（aggregate 提升不得掩盖关键回归）；
  `newly_fixed`、failure set 均可解释。
- `packages/application/evaluation/canary.py`：按 `canary` tag 选择
  数据集子集；无 canary case fail-closed；canary 不可替代全量回归。
- `packages/application/evaluation/calibration.py`：human vs machine
  对比（agreement / false positive / false negative / ambiguous）；
  只报告统计，不做自动修正或阈值拟合。

### 8.6 EvalScore 报告与 CI

- `schemas/eval-score.schema.json` + `packages/application/evaluation/
  report.py`：canonical JSON 写读（UTF-8、jsonschema 校验、fail-closed）。
- `packages/application/evaluation/main.py`：CI 确定性门禁 CLI（离线、
  无 LLM；PASS→exit 0，REVISE/BLOCK→exit 1）。
- `.github/workflows/m0-quality.yml` 新增 `eval-gate` job：门禁 CLI +
  `tests/evals -m "not requires_live_llm"`；`requires_live_llm` marker
  已在 pyproject 注册（strict-markers 开启）。

### 8.7 已知弱链（M7 边界，M11 不重写）

M7 编排的 `phase_runner → evaluation_gate` 链路中，gate 输入事实
（structured_output/artifacts/evidence）由被评 agent 产出并以
`TrustLabel.GENERATED` 登记；M11 的 `gate_outcome` scorer 把该 gate
作为被观测对象，其输入真实性与 M12 真实工作流的 Evidence 治理挂钩。
M11 平面自身的评测输入全部经 digest 校验后消费。
