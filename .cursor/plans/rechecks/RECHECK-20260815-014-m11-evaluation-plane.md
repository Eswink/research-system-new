---
id: RECHECK-20260815-014
plan_id: PLAN-20260815-014
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-08-15
completed_at: 2026-08-15
reviewer: root-agent-independent-pass
baseline_ref: null
checked_head: working-tree
---

# RECHECK-20260815-014 — M11 Evaluation Plane 复检

## 冻结范围

- 任务计划：Cursor Plan `m11_evaluation_plane_f0943439`（用户批准，
  Plan Mode 产物）；M11 权威 DoD 唯一来源
  `docs/roadmap/MILESTONES.md` M11 节
- 验收条件：MILESTONES M11 DoD 五条（可复现运行；真实 before/after
  regression 被 gate 拦截；CI 确定性接入；评测对象可为 mock；独立复审
  PASS + m0 profile 全绿）
- 变更范围：
  - Domain 新增：`packages/domain/eval_spec.py`、`eval_result.py`、
    `eval_report_codec.py`、`eval_gate.py`
  - Application 新增：`packages/application/evaluation/`
    （`scorer_types.py`、`scorers.py`、`schema_scorer.py`、
    `scorers_runtime.py`、`registry.py`、`runner.py`、`reviewer.py`、
    `panel.py`、`regression.py`、`canary.py`、`calibration.py`、
    `report.py`、`__init__.py`）
  - Adapter 新增：`adapters/contracts/eval_loaders.py`、
    `eval_report_io.py`、`adapters/cli/eval_gate.py`、
    `adapters/fakes/reviewer.py`
  - Schemas 新增：`schemas/eval-dataset.schema.json`、
    `schemas/eval-score.schema.json`
  - 契约资产：`examples/eval/datasets/{unit_v1,integration_v1}.yaml`、
    `tools/freeze_eval_dataset.py`
  - 测试新增：`tests/evals/`（10 个测试模块 + fixtures）、
    `tests/domain/test_eval_contracts.py`、
    `test_eval_report_contracts.py`、`eval_contracts_support.py`
  - 工程面：`.github/workflows/m0-quality.yml`（eval-gate job）、
    `pyproject.toml`（requires_live_llm marker）、`.gitignore`
    （artifacts/）、`.cursor/skills/system-spec-check/scripts/
    validate_bundle.py`（schema 注册表）、`docs/INDEX.md`、
    `docs/architecture/EVALUATION.md`（§8 实现映射）、
    `docs/references/upstream/M11_EVAL_HARNESS_QUALIFICATION.md`
- 基线：M7 DONE（2026-08-14）；未创建 commit（Git Hard Boundaries 默认）

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| G-01 | 范围与架构 | 变更清单对照批准 Cursor Plan；依赖方向：`adapters/cli` 与 `adapters/contracts`（entry/infra adapter）→ application → domain；`packages/application/evaluation/` 无 adapters import（lint-imports application 契约 3/3 KEPT）；未新建平行 Evaluator Port（Reviewer 复用 ModelGateway） | PASS |
| G-02 | DoD 1 可复现 | `test_runner.py::test_replay_same_frozen_conditions_same_digest`、`test_replay_digest_ignores_report_id_and_timestamp`、`test_report.py::test_report_file_is_stable_across_writes`；CLI 连续两次运行 digest 一致（unit_v1 `sha256:ed42d6dc…`、integration_v1 `sha256:deb427f1…`） | PASS |
| G-03 | DoD 2 before/after 被拦截 | `test_regression.py::test_before_after_regression_blocked_by_gate`：canary case c1 由 PASS→FAIL，`newly_regressed=("c1",)` 且 verdict BLOCK；聚合提升不掩盖关键回归（`test_eval_gate.py::test_any_deterministic_fail_blocks_even_with_high_aggregate`） | PASS |
| G-04 | DoD 3 CI 确定性接入 | `.github/workflows/m0-quality.yml` 新增 eval-gate job（门禁 CLI + `tests/evals -m "not requires_live_llm"`，无 LLM/网络）；本地复跑 CLI exit 0 且 digest 稳定 | PASS |
| G-05 | DoD 4 mock 评测对象 | 评测输入全离线冻结（examples/eval/datasets + 显式 inputs）；Reviewer 测试用 FakeReviewer/FakeModelGateway/脚本化 gateway；真实 LLM 仅 marker `requires_live_llm` 隔离（CI 默认 skip） | PASS |
| G-06 | DoD 5 m0 全绿 | m0 profile 18/18 PASS；python/tests 1610 passed；mypy strict 346 files 无 issue；validate_bundle + governance validate PASS | PASS |
| G-07 | 反作弊 | 阈值篡改→config digest 变化（`test_eval_gate.py`）；case 跳过→input accounting/missing 可见（`test_runner.py`）；失败样本删除→dataset digest 变化（`test_eval_gate.py`）；被评对象自报 score=PASS→BLOCK（`test_self_reported_score_cannot_become_eval_result`）；scorer 异常→INFRA_ERROR 不转 PASS（`test_scorer_exception_becomes_infra_error`） | PASS |
| G-08 | 安全 | Reviewer 输入只含 rubric+material reference 不含 secret（`test_reviewer_material_carries_no_secrets`）；LlmReviewer 经 ModelGateway Port 与 SecretValue（repr 脱敏）；无新增凭据/授权系统 | PASS |

## Findings

| ID | 严重度 | 发现 | 处置 |
| --- | --- | --- | --- |
| F-01 | info | M7 编排 gate 的输入事实 100% 由被评 agent 产出（TrustLabel.GENERATED）；M11 以 `gate_outcome` scorer 将该 gate 作为被观测对象 | 不重写 M7；弱链记录于 `docs/architecture/EVALUATION.md` §8.7，归属 M12 真实工作流 Evidence 治理 |
| F-02 | info | `GateConfig.threshold` 字段进入 config digest 但 M11 verdict 不消费软分聚合（deterministic-first：任何 FAIL→BLOCK） | 版本化保留字段；软分聚合归属 M15 Eval Operations |
| F-03 | info | UsageLedgerEntry 无 latency 字段；EvalReport.usage 为可选观察维度 | 质量与成本语义分离已测试；latency 归 M15 |
| F-04 | info | `tests/evals/test_gate.py` 与既有 `tests/application/memory/test_gate.py` 模块名冲突（pytest import file mismatch） | 已重命名为 `test_eval_gate.py`（经验条目 EXP-20260813-007 佐证） |
| F-05 | info | 外部 eval framework 全部否决引入（ragas/deepeval/lm-eval-harness/pytest-benchmark/inspect-ai） | 决策与逐项缺口回答见 `M11_EVAL_HARNESS_QUALIFICATION.md` |

## 结论

- 结果：`PASS`
- 理由：M11 DoD 五条逐项有独立可执行证据（测试输出、CLI 两次运行
  digest、m0 profile 18/18）；反作弊与 Reviewer 失败语义有专项测试；
  Findings 均为已记录不阻塞项。
- 后续动作：M11 停在阶段边界；IG-1 前置剩 M8/M9/M10 已完成（
  M8/M9/M10 均已 DONE），M12 立项需用户显式启动，本复检不自动开工。
- 工程记忆：无可复用事实（M11 交付为产品代码、测试与契约资产）。