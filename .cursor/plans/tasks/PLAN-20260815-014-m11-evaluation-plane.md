---
id: PLAN-20260815-014
slug: m11-evaluation-plane
title: M11 Evaluation Plane
status: DONE
created_at: 2026-08-15
updated_at: 2026-08-15
cursor_plan_uri: c:\Users\googl\.cursor\plans\m11_evaluation_plane_f0943439.plan.md
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: "m11_evaluation_plane（用户批准：M11 范围/DoD 以 MILESTONES.md 为唯一权威，三 work packages，批准后自主持续执行至阶段边界）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260815-014-m11-evaluation-plane.md
memory_entries: []
---

# PLAN-20260815-014 — M11 Evaluation Plane

## 目标

建立独立于 Research Runtime 的正式 Evaluation Plane：
- EvalCase/EvalDataset 冻结契约（digest 防篡改、可重放）；
- 版本化 deterministic scorers（确定性可验证问题不经 LLM）；
- EvalRunner 多模式 + 隔离 + 异常不转 PASS；
- Reviewer/Panel（失败语义结构化，绝不把设施故障映射为被评对象
  FAIL/PASS）；
- 版本化 Quality Gate（任何确定性 FAIL→BLOCK）；
- regression/canary/calibration（真实 before/after 被 gate 拦截）；
- EvalScore 报告 schema + CI 确定性门禁接入。

## 范围

- 包含：`packages/domain/eval_spec.py`、`eval_result.py`、
  `eval_report_codec.py`、`eval_gate.py`；`packages/application/
  evaluation/`（scorers/runner/reviewer/panel/regression/canary/
  calibration/report）；`adapters/contracts/eval_loaders.py`、
  `eval_report_io.py`、`adapters/cli/eval_gate.py`、
  `adapters/fakes/reviewer.py`；`schemas/eval-dataset.schema.json`、
  `eval-score.schema.json`；`examples/eval/datasets/`；
  `tests/evals/`；CI eval-gate job；upstream qualification 文档。
- 不包含：M12 真实科研工作流、production 编排、UI/Research Console、
  多租户、benchmark 服务、分布式 evaluator farm（M16）、GPU/HPC
  （M17）、真实付费 LLM 评测入默认 CI（仅显式手动）、评分模型训练。

## 架构与数据流

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
Reviewer/Panel 只处理语义判断；deterministic 证据优先，Reviewer 不得
覆盖确定性失败；Reviewer 不是 Research truth owner。
```

## 验收条件（MILESTONES M11 DoD 逐条）

- AC-01 harness 可复现运行（同输入同分数）：replay 测试 +
  CLI 两次运行 digest 一致。
- AC-02 至少一个真实 before/after regression 案例（变更被 gate
  拦截）：canary case PASS→FAIL → BLOCK。
- AC-03 CI 确定性接入：eval-gate job（离线、无 LLM）+
  `tests/evals -m "not requires_live_llm"`。
- AC-04 评测对象可为 mock：离线冻结输入 + Fake Reviewer/Gateway；
  真实 LLM 仅 `requires_live_llm` marker 显式运行。
- AC-05 独立复审 PASS + m0 profile 全绿。

## 实施记录

- 实施按 Cursor Plan 三 work packages（WP-A Harness / WP-B Scorers+
  Reviewers+Gates / WP-C Regression+Canary+Calibration）与 12 步依赖
  顺序完成；过程中修复：mypy strict 40+ 处、test_gate 模块名冲突
  （重命名 test_eval_gate）、FrozenConditions.comparison_digest 比较
  键设计（before/after 的本质区分评测配置与被评输入）、
  application→adapters 跨层 import（report 序列化下沉 adapter、
  CLI 迁移 adapters/cli）、4 个文件行数/函数长度超限拆分。
- 反作弊专项：阈值篡改、case 跳过、失败样本删除、dataset 篡改、
  自报 score=PASS 注入，均有测试证据。

## 实施清单

| ID | 内容 | 状态 |
| --- | --- | --- |
| T-01 | Domain 评测契约（eval_spec/eval_result/eval_report_codec/eval_gate）+ 单测 | DONE |
| T-02 | 纯 deterministic scorers + 版本化注册表（schema_validity 自研校验器） | DONE |
| T-03 | Case/Dataset registry + freeze digest + fixtures + 冻结/篡改测试 | DONE |
| T-04 | EvalRunner（隔离、异常不转 PASS、case 对账）+ runtime scorers | DONE |
| T-05 | Reviewer（LlmReviewer + FakeReviewer）+ 失败语义测试 | DONE |
| T-06 | Reviewer panel（独立聚合、disagreement、partial failure） | DONE |
| T-07 | Quality Gate（compute_verdict、阈值篡改/自证绕过测试） | DONE |
| T-08 | Regression + canary（真实 before/after 被 gate 拦截，DoD 2） | DONE |
| T-09 | Calibration（agree/FP/FN/ambiguous samples） | DONE |
| T-10 | EvalScore 报告 schema + 写读 + 往返测试 | DONE |
| T-11 | CI eval-gate job + marker + qualification 文档 + INDEX/EVALUATION 同步 | DONE |
| T-12 | m0 profile 全绿 + validate_bundle + 独立 recheck + DoD 判定 | DONE |

## 证据

- m0 profile 18/18 PASS：python/tests 1610 passed（95.22s）；
  mypy strict 346 files；ruff check/format 全过；dependency
  boundaries 通过；TS 五组全过；framework 组 8 项全过。
- validate_bundle PASS；governance validate PASS。
- CLI `adapters/cli/eval_gate.py` 连续两次运行 digest 一致
  （unit_v1 `sha256:ed42d6dc…`、integration_v1 `sha256:deb427f1…`）。
- `tests/evals/` 10 个测试模块全部通过；DoD 2 证据：
  `test_before_after_regression_blocked_by_gate`。
- 复检：`RECHECK-20260815-014-m11-evaluation-plane.md`。

## 状态历史

- 2026-08-15 IN_PROGRESS：Cursor Plan 批准后进入实施（Plan Mode →
  Agent Mode）。
- 2026-08-15 VERIFYING：实施完成，m0 profile 全绿，进入 DoD 逐条
  复核。
- 2026-08-15 DONE：独立 recheck PASS（RECHECK-20260815-014）。

## 影响报告

- Domain/API/schema：新增 4 个 domain 模块与 2 个 JSON Schema；
  既有 domain 未改（enums 复用 QualityGateVerdict）。
- 安全/凭据：无新增凭据；Reviewer 经 ModelGateway Port + SecretValue
  密封；评测输入不含 secret（专项测试）。
- 兼容性/迁移：全部新增文件，无既有接口变更；`tests/evals/test_gate.py`
  因模块名冲突重命名为 `test_eval_gate.py`（仅测试文件）。
- 上游版本影响：未引入任何外部 eval framework（qualification 决策
  文档记录逐项否决理由）；jsonschema/PyYAML 沿用既有 pin。
- 下一项任务：M11 停在阶段边界；IG-1 前置四项（M8/M9/M10/M11）均已
  DONE，M12 立项需用户显式启动。