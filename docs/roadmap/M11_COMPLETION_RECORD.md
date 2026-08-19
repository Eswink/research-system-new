# M11 — Evaluation Plane 完成记录

> Reconstructed from repository evidence（2026-08-16，DOC-R1）
>
> 本记录由 DOC-R1 文档恢复/校正任务依据 `.cursor/plans/tasks/
> PLAN-20260815-014-m11-evaluation-plane.md`（status DONE）、
> `.cursor/plans/rechecks/RECHECK-20260815-014-m11-evaluation-plane.md`
> （result PASS）、commits `0846765` / `0cc6361`、
> `docs/references/upstream/M11_EVAL_HARNESS_QUALIFICATION.md` 与
> `docs/architecture/EVALUATION.md` §8 重建。M11 开发窗口（2026-08-15）
> 未创建独立完成记录文件（git log 确认历史上从未存在）；本记录不虚构
> 原开发窗口讨论，全部陈述可由上述证据直接支持。

- 日期：2026-08-15
- 范围权威：`docs/roadmap/MILESTONES.md` M11 节
- 前置：M7 DONE；M11 计划经 Plan Mode 批准（Cursor Plan `m11_evaluation_plane_f0943439`）
- 结论：**M11 DoD 全部满足（RECHECK-20260815-014 = PASS）**

## Final Scope

建立独立于 Research Runtime 的正式 Evaluation Plane：

- EvalCase/EvalDataset 冻结契约（freeze digest 防篡改、可重放）；
- 版本化 deterministic scorers（确定性可验证问题不经 LLM）；
- EvalRunner 多模式 + 隔离 + 异常不转 PASS（INFRA_ERROR 语义）；
- Reviewer/Panel（失败语义结构化，设施故障不映射为被评对象 FAIL/PASS）；
- 版本化 Quality Gate（任何确定性 FAIL→BLOCK）；
- regression/canary/calibration（真实 before/after 被 gate 拦截）；
- EvalScore 报告 schema + CI 确定性门禁接入（eval-gate job）。

## Implemented Contracts

| 契约 | 位置 |
| --- | --- |
| Domain 评测契约 | `packages/domain/eval_spec.py`、`eval_result.py`、`eval_report_codec.py`、`eval_gate.py` |
| Evaluation 应用层 | `packages/application/evaluation/`（scorer_types/scorers/schema_scorer/scorers_runtime/registry/runner/reviewer/panel/regression/canary/calibration/report） |
| 契约加载器与报告 IO | `adapters/contracts/eval_loaders.py`、`eval_report_io.py` |
| CLI 门禁 | `adapters/cli/eval_gate.py`（两次运行 digest 一致：unit_v1 `sha256:ed42d6dc…`、integration_v1 `sha256:deb427f1…`） |
| Fake Reviewer | `adapters/fakes/reviewer.py` |
| 报告 schema | `schemas/eval-dataset.schema.json`、`schemas/eval-score.schema.json` |
| 冻结数据集 | `examples/eval/datasets/{unit_v1,integration_v1}.yaml`、`tools/freeze_eval_dataset.py` |

## Key implementation paths

```text
EvalDataset（frozen，case 排序 digest）
  → EvalRunner（OFFLINE_FAKE 为主；显式输入，无全局状态）
    → deterministic scorers（纯函数注册表，id+version 解析）
    → runtime scorers（ArtifactStore/PolicyEvaluator/M7 gate 经 Port）
    → EvalResult（frozen_conditions + findings 全链追溯）
    → compute_verdict（FAIL→BLOCK；INFRA→REVISE；min_pass_ratio→BLOCK）
  → EvalReport（canonical JSON；report_id/generated_at 不入 digest）
  → RegressionComparison（comparison_digest 一致才可比较；
     newly_regressed 存在即 BLOCK）
```

Reviewer/Panel 只处理语义判断；deterministic 证据优先，Reviewer 不得覆盖
确定性失败；Reviewer 不是 Research truth owner。

## Architecture decisions

1. 不引入外部 eval framework：ragas / deepeval / lm-eval-harness /
   pytest-benchmark / inspect-ai 全部否决（逐项缺口与升级门禁见
   `docs/references/upstream/M11_EVAL_HARNESS_QUALIFICATION.md`），
   采用 native 自建 harness。
2. 未新建平行 Evaluator Port：Reviewer 复用 `ModelGateway` Port +
   `SecretValue` 密封（lint-imports application 契约 3/3 KEPT）。
3. deterministic-first：任何确定性 FAIL→BLOCK，聚合提升不掩盖关键回归
   （`test_eval_gate.py::test_any_deterministic_fail_blocks_even_with_high_aggregate`）。
4. frozen_conditions 参与 digest：report_id/generated_at 不入 digest
   （报告可稳定重放）；GateConfig 版本化（threshold 入 config digest）。
5. 被评对象不能自证：`test_self_reported_score_cannot_become_eval_result`
   锁定；case 跳过/失败样本删除/dataset 篡改/阈值篡改均有专项测试。
6. 真实付费 LLM 仅 `requires_live_llm` marker 显式运行，不进默认 CI。

## Tests / fault injection

- `tests/evals/` 10 个测试模块：calibration / dataset_freeze /
  deterministic_scorers / eval_gate / panel / regression / report /
  reviewer_failure / runner / runtime_scorers。
- `tests/domain/test_eval_contracts.py`、`test_eval_report_contracts.py`。
- DoD 2 证据：`test_before_after_regression_blocked_by_gate`（canary case
  c1 由 PASS→FAIL → `newly_regressed=("c1",)` 且 verdict BLOCK）。
- 反作弊故障注入：阈值篡改→config digest 变化；case 跳过→input
  accounting/missing 可见；失败样本删除→dataset digest 变化；scorer
  异常→INFRA_ERROR 不转 PASS。
- Reviewer 失败语义：`test_reviewer_failure.py`（LlmReviewer 经
  ModelGateway Port；设施故障不映射为被评对象 FAIL/PASS）。

## Independent review

- `RECHECK-20260815-014` = **PASS**（G-01..G-08 全 PASS：范围与架构 /
  DoD 1 可复现 / DoD 2 before-after 拦截 / DoD 3 CI 接入 / DoD 4 mock
  评测对象 / DoD 5 m0 全绿 / 反作弊 / 安全）。
- Findings（全部 info 级，不阻塞）：F-01 M7 gate 输入为
  TrustLabel.GENERATED（弱链记入 EVALUATION.md §8.7，归 M12 Evidence
  治理）；F-02 GateConfig.threshold 版本化保留（软分聚合归 M15）；
  F-03 UsageLedgerEntry 无 latency 字段（归 M15）；F-04 test_gate.py
  模块名冲突（已重命名 test_eval_gate.py，EXP-20260813-007 佐证）；
  F-05 外部 eval framework 全部否决。
- 收尾修复 commit `0cc6361`（2026-08-15）：harden eval gate invocation
  and reviewer score codec roundtrip（RECHECK 后 2 项修复）。

## DoD evidence（MILESTONES M11 五条）

| DoD 项 | 证据 | 结果 |
| --- | --- | --- |
| harness 可复现运行（同输入同分数） | `test_replay_same_frozen_conditions_same_digest`、`test_replay_digest_ignores_report_id_and_timestamp`、`test_report_file_is_stable_across_writes`；CLI 两次运行 digest 一致 | PASS |
| 至少一个真实 before/after regression 被 gate 拦截 | `test_before_after_regression_blocked_by_gate` | PASS |
| CI 确定性接入 | `.github/workflows/m0-quality.yml` eval-gate job（门禁 CLI + `tests/evals -m "not requires_live_llm"`，无 LLM/网络） | PASS |
| 评测对象可为 mock | 离线冻结输入 + FakeReviewer/FakeModelGateway；真实 LLM 仅 marker 隔离 | PASS |
| 独立复审 PASS + m0 profile 全绿 | RECHECK-014 PASS；m0 profile 18/18；python/tests 1610 passed；mypy strict 346 files；validate_bundle + governance validate PASS | PASS |

## Git evidence

- `0846765`（2026-08-15）feat(m11): evaluation plane with deterministic
  gates and CI integration（52 files：plan/recheck/qualification 文档 +
  domain + application + tests + 2 schema + CI job）。
- `0cc6361`（2026-08-15）fix(m11): harden eval gate invocation and
  reviewer score codec roundtrip（4 files）。

## deferred work / risks

- 软分阈值聚合消费：GateConfig.threshold 保留但 verdict 不消费（M15
  Eval Operations）。
- EvalReport.usage（latency/成本）为可选观察维度（M15）。
- M7 gate 输入 100% 由被评 agent 产出（TrustLabel.GENERATED）：M11 以
  `gate_outcome` scorer 将其作为被观测对象；弱链归属 M12 真实工作流
  Evidence 治理（EVALUATION.md §8.7）。
- 真实付费 LLM 评测不进入默认 CI（仅显式手动），M12 真实工作流评测需
  显式运行。

## 安全 / 凭据变化

无新增凭据域；Reviewer 经 ModelGateway Port + SecretValue（repr 脱敏）；
评测输入不含 secret（`test_reviewer_material_carries_no_secrets`）；
无新增授权系统。

## 上游版本影响

未引入任何外部 eval framework；jsonschema / PyYAML 沿用既有 pin。

## 下一项任务

M11 停在阶段边界。IG-1（M12 entry）前置四项 M8/M9/M10/M11 均已
DONE（M8 2026-08-14；M9/M10/M11 2026-08-15）；M12 立项需用户显式
启动，本记录不自动开工。