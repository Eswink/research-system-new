# M12-R1 — Production Truth Closure Remediation Record

- 日期：2026-08-23
- 性质：M12（First Real Research Workflow）独立复审 FAIL 后的修复闭环；**不修改 Roadmap 编号**，不进入 M13/M14/M15
- 范围权威：`docs/roadmap/MILESTONES.md` M12 节（DoD/Exit Gate 唯一权威）
- 输入：M12 独立复审 13 项 Finding（M12 判定 FAIL / MVP NO-GO，原 PASS 结论不成立）

## 修复原则

- 事实优先级：production code > Contracts > 可重复执行 > Git history > deterministic tests > audit evidence > 文档
- 不删除/不改写历史 Review；保留 M12 FAIL 事实
- 优先修 wiring，不重写已正确的组件（NCBI provider / DockerExecutionBackend / M9-M11 机制全部保留）

## Finding → Root Cause → Fix → Regression → Revalidation

| Finding | Root Cause | Fix | Regression | Revalidation |
| --- | --- | --- | --- | --- |
| F1 RunManifest 不驱动执行链 | `tools/m12_generate_deliverable.py` 独立 Fake 链；manifest 冻结后无消费方 | `packages/application/run_orchestration/m12_composition.py`：compile→preflight→freeze 单入口，extras 冻结 M12 维度；`RunManifest` 增 endpoint/probe/fallback/image/skill/eval 字段 | `tests/application/test_m12_manifest_freeze.py` 11 tests；M2 旧测试全过 | manifest digest 覆盖全部字段；preflight 未过抛 ManifestFreezeError |
| F2 relay smoke 不可重放、fallback 未冻结、usage 未接入 | `tools/m12_relay_smoke.py` 仅打印；`gateway.usage` 未转 ledger | `packages/application/model_relay/live_probe.py`（可重放、NOT VERIFIED 占位）；`CompletionResult` 增 token 明细；`usage_collection.py` 真实事件归账 | `tests/application/model_relay/test_live_probe_not_verified.py` 4 tests | 无凭据 → verified=False 占位；有凭据 → sanitized fingerprint |
| F3 Tool 与 Evidence 平行演示 | ToolResult 止于 spill，未入 `Source→Evidence` | `packages/application/evidence/tool_evidence.py`：ToolResult→SourceRecord(GENERATED)→Evidence 唯一准入；VERIFIED provenance 不变量升级面强制 | `tests/application/evidence/test_tool_result_not_evidence.py` 6 tests | 直写 Evidence 无法升级 VERIFIED（source 未登记拒绝） |
| F4 Deliverable 用 Fake stores | `_EXPERIMENT_RESULT` 常量 + Fake 三件套唯一交付路径 | `packages/application/deliverable/builder.py`：run_id 只读聚合，artifact 内容寻址重算；旧 `tools/m12_generate_deliverable.py` 已删除 | `tests/application/test_m12_deliverable_from_state.py` 9 tests | 报告每个 digest 可由持久状态重算；缺状态抛 DeliverableBuildError |
| F5 Experiment Evidence 合成 | `_EXPERIMENT_RESULT` 合成字典不入库 | 真实链：DockerExecution→SqliteArtifactStore→`evidence_admission.register_experiment_evidence`→SqliteEvidenceLedger | `tests/application/experiments/test_evidence_admission_e2e.py`（requires_docker，本机实跑 PASS） | claim 重开后仍 VERIFIED（持久化） |
| F6 VERIFIED 来自合成 Evidence | 同上 | WP2 删除合成源；evidence 全部绑定真实 run/artifact/image/snapshot | 同上 + 契约套件 | `_EXPERIMENT_RESULT` production 0 命中 |
| F7 reproduction REFUTES 合成 | `digest_of({"repro":2})` 伪矛盾源 | 删除合成 REFUTES 路径（真实矛盾由真实重跑/文献补检产生，本轮未伪造） | 相关测试清理 | grep 0 命中合成 repro digest |
| F8 Evaluation 自证循环 | `0.745` 同源 expected/candidate | dataset 删除 expected 字面量；`scorers_m12_truth.py` 4 个独立真值 scorer（metric_correctness/direction/citation/unsupported）；8 项对抗回归 | `tests/evals/test_m12_evaluation.py` 7 + `test_m12_evaluation_adversarial.py` 8 tests | 方向反转/0.999/缺证据等全部 FAIL；dataset digest 重冻结 `sha256:50bb58f4…` |
| F9 feature_time_s 污染 digest | wall-clock 进 `metrics_digest` | `semantic_metrics_projection`（`_time_s` 后缀剔除）；`ExperimentRunResult.semantic_metrics_digest`；audit 分离 semantic/observational | `tests/application/experiments/test_reproducibility_semantic.py` 9 tests | 同配置重跑 semantic digest 稳定、raw 允许漂移 |
| F10 Budget 手工注入 | `ModelUsage(1200+800)` 等常量 | `usage_collection.py`：真实 CompletionResult/ToolResult/EvalReport 归账；缺字段 UNKNOWN；retry 幂等 | `tests/application/experiments/test_budget_real_wiring.py` 6 tests | retry 不 double-count；re-eval 独立条目 |
| F11 Report 硬编码 | 交付器代码内字典 | WP3 builder 只读聚合（见 F4） | 同上 | report 字段全部来自持久状态 |
| F12 clean-run 不可重建 | 无一键入口 | `packages/application/m12_reference/clean_run.py` + `tools/m12_reference_workflow.py` | `tests/application/test_m12_clean_run.py` 5 tests | 全链标识输出；semantic digest 跨 clean-run 稳定 |
| F13 untracked 资产 | M12 assets 未入 Git | WP10 归整（见下文） | validate_bundle 通过 | git status 分类表 |

## 新增/变更的正式契约

- `RunManifest`（domain）：M12-R1 扩展字段（optional，兼容）
- `ExperimentRunResult`（domain）：`semantic_metrics_digest`（兼容新增）
- `ReproducibilityAudit`（domain）：semantic/observational digest 分离（审计附注不入 audit digest）
- `CompletionResult`（Port）：token 明细（optional，兼容）
- `m12_research_v1.yaml`：重冻结 digest（`sha256:50bb58f463274af7a515361c2566720b291b8841d713a9ba2df5ab1c375f4816`）
- 新 adapter：`SqliteEvidenceLedger` / `SqliteMemoryStore`（M12 闭环例外，不宣称 M14 完成）
- 新 use cases：`m12_composition` / `tool_evidence` / `deliverable.builder` / `usage_collection` / `live_probe` / `scorers_m12_truth` / `m12_reference.clean_run`

## 执行顺序（真实依赖）

WP1（manifest 根）→ WP9（真实存储）→ WP2（真实证据链）→ WP4（复现语义）→
WP3（交付器）→ WP6（usage 接线）→ WP5（评测真值）→ WP7（live relay）→
WP8（clean-run）→ WP10（Git truth）→ WP11（文档纠偏）。

## 验证证据（实际执行）

```text
pytest tests/domain tests/application tests/contracts tests/adapters/sqlite tests/evals
  -m "not requires_docker" → 1080 passed（28s）
pytest tests/application/experiments/test_evidence_admission_e2e.py（requires_docker）→ 1 passed（本机 Docker 实跑）
ruff check（变更面）→ All checks passed
mypy --strict（变更面）→ Success
tools/freeze_eval_dataset.py m12_research_v1.yaml → digest 更新
```

## 已知剩余限制（诚实声明）

1. `system_fingerprint` 取决于 relay；未返回时如实标"可重复配置"（AGENTS.md §4）。
2. clean-run CLI 的 live relay 段需要 `llm_main_key` 环境变量；无凭据时 NOT VERIFIED 占位（非 Fake PASS）。
3. Evidence/Memory 持久化为 SQLite（M12 闭环所需）；PostgreSQL canonical state 仍属 M14。
4. 真实工具 Evidence（NCBI）本轮完成准入链与测试，live 文献检索需网络 opt-in 重放。

## 下一项任务

- 独立复审员凭 `git show` + `sqlite` + `EvalReport` 重算报告断言，完成 M12-R1 二次判定。
- 有凭据时执行 `python tools/m12_reference_workflow.py --clean --live-relay` 补齐 live evidence。