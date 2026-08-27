---
id: PLAN-20260828-019
slug: m12-r1-production-truth-closure
title: M12-R1 Production Truth Closure 修复轮
status: DONE
created_at: 2026-08-28
updated_at: 2026-08-28
cursor_plan_uri: c:\Users\googl\.cursor\plans\m12-r1_remediation_plan_aaca9616.plan.md
owners:
  - root-agent
authorization:
  source: user-request
  ref: "补齐流程计划与文档对齐（2026-08-28 批准）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260828-019-m12-r1-production-truth-closure.md
memory_entries: []
---

# PLAN-20260828-019 — M12-R1 Production Truth Closure 修复轮

> 本文件记录 M12 独立复审 FAIL（13 Finding）后的修复轮正式计划。事实优先级：production code > Contracts > 可重复执行 > Git history > deterministic tests > audit evidence > 文档。M12 按 FAIL/MVP NO-GO 处理，保留原 FAIL 审查记录，不改写历史。原执行期工作文件为 `.cursor/plans/m12-r1_remediation_plan_aaca9616.plan.md`（含全部 13 Finding 根因分析）。

## 目标

将 M12 从 synthetic Fake 闭环修正为单一真实 RunManifest 驱动的生产真相链，使 Tool / Experiment / Artifact / Evidence / Claim / Memory / Budget / Deliverable / Evaluation 均来自同一 run_id 持久状态，消除手工常量与自证循环，恢复可重放、可审计的 MVP 判定能力。

## 范围

- 包含：
  - WP1 单一生产 Run 组合（compile→preflight→freeze→执行真链路）
  - WP2 删除合成链，真实准入进 Evidence/Claim/Memory
  - WP3 交付器 run_id 只读聚合（报告事实来自持久状态）
  - WP4 raw/semantic digest 分离、variance 诚实报告
  - WP5 消除 eval 自证循环、独立 scorer + 对抗回归
  - WP6 真实 usage 归账闭环（缺字段 UNKNOWN、重试幂等）
  - WP7 可重放 live relay 链（NOT VERIFIED 占位、指纹持久化）
  - WP8 一键 clean-run harness；WP9 真实持久化存储（SqliteEvidenceLedger/MemoryStore）；WP10 Git truth；WP11 文档纠偏
- 不包含：M13/M14/M15；批量工具接入；新 Fake-only 核心路径

## 架构与数据流

- 所有者模块：
  - Application: `packages/application/run_orchestration/m12_composition.py`（manifest 根）、`evidence/tool_evidence.py`（唯一准入）、`deliverable/builder.py`（只读聚合）、`model_relay/live_probe.py`、`usage_collection.py`、`experiments/budget_closure.py`、`evaluation/scorers_m12_truth.py`、`m12_reference/clean_run.py`
  - Adapter: `adapters/sqlite/`（evidence_ledger、memory_store、artifact_store）
- 输入：M12 原交付链（Fake 合成）+ 真实 NCBI/DockerExecution 链路
- 输出：真实 RunManifest → 真实 Evidence/Claim → 真实 EvalReport → 真实 BudgetLedger → 正式 Deliverable（全部 run_id 可溯源）
- Canonical State：SQLite（M12 闭环例外，不宣称 M14 完成）
- 关键不变量：`ToolResult != Evidence`；`_EXPERIMENT_RESULT` 常量 0 命中；`digest_of({"repro":2})` 合成矛盾源删除；eval 无 expected 字面量

## 验收条件

- [x] AC-01 F1-F13 全部闭环（manifest 根、真实证据链、deliverable 从状态、usage 归账、eval 真值、clean-run、git truth、doc repair）
- [x] AC-02 回归测试对原缺陷有判别力（对抗性回归 8+8 项）
- [x] AC-03 m0 面全绿（非 docker 1080 passed；docker e2e 1 passed；ruff/mypy strict PASS）
- [x] AC-04 M12 待重新独立复审状态如实保留（本修复轮不自行判定 MVP GO）

## 实施清单

- [x] WP1-manifest-composition：单一生产 Run 组合，冻结全部 M12 维度与 fallback 语义
- [x] WP9-persistence-boundary：SqliteEvidenceLedger/MemoryStore 落地，生产不再使用 Fake
- [x] WP2-real-evidence-chain：删除合成链，Docker 产物与 ToolResult 经真实准入进入 Evidence/Claim/Memory
- [x] WP4-repro-semantics：raw/semantic digest 分离，feature_time_s 归 observational
- [x] WP3-deliverable-from-state：交付器重构为 run_id 只读聚合
- [x] WP6-usage-budget：真实事件→UsageLedger→Budget 闭环，缺字段/重试幂等
- [x] WP5-eval-ground-truth：独立 scorer + 8 项对抗回归，重冻结 dataset
- [x] WP7-replayable-relay：live 链可重放，NOT VERIFIED 占位、指纹持久化、usage 入账
- [x] WP8-clean-run：一键 clean-run harness，从空状态重建同一真相
- [x] WP10-git-truth：untracked 资产归整
- [x] WP11-doc-repair：保留 FAIL 历史，修正文档误述，新增 M12-R1 证据记录
- [x] final-regression-gate：validators + m0 profile + 独立复审重放

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用（修复轮以根代理串行为主） | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | WP1 | test | `tests/application/test_m12_manifest_freeze.py` | 11 tests PASS |
| EV-02 | WP2 | test | `tests/application/evidence/test_tool_result_not_evidence.py`（6）；`test_evidence_admission_e2e.py`（docker 1） | PASS |
| EV-03 | WP3 | test | `tests/application/test_m12_deliverable_from_state.py` | 9 tests PASS |
| EV-04 | WP4 | test | `tests/application/experiments/test_reproducibility_semantic.py` | 9 tests PASS |
| EV-05 | WP5 | test | `tests/evals/test_m12_evaluation.py`（7）+ `test_m12_evaluation_adversarial.py`（8） | PASS |
| EV-06 | WP6 | test | `tests/application/experiments/test_budget_real_wiring.py` | 6 tests PASS |
| EV-07 | WP7 | test | `tests/application/model_relay/test_live_probe_not_verified.py` | 4 tests PASS |
| EV-08 | WP8 | test | `tests/application/test_m12_clean_run.py` | 5 tests PASS |
| EV-09 | WP10/11 | check | git status 分类表；`docs/roadmap/M12_R1_COMPLETION_RECORD.md` | 保留 FAIL 历史 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-23 | M12 FAIL / MVP NO-GO | 独立复审证伪原 PASS（13 Finding） | 修复轮立项 |
| 2026-08-23 | 修复轮完成 | WP1-WP11 + final regression | M12 待重新独立复审 |
| 2026-08-28 | 正式计划固化 | 补齐流程计划记录 | 本文件 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-23 | — | DONE | WP1-WP11 完成 + final regression | `2e312f3`/`c257e03`/`f1ac926` |
| 2026-08-28 | — | DONE | 计划固化 + 复检 PASS | 本文件 + RECHECK-20260828-019 |

## 影响报告

- Domain/API/schema：`RunManifest` 扩展字段（optional）、`ExperimentRunResult.semantic_metrics_digest`、`CompletionResult` token 明细（兼容新增）
- 安全/凭据：Key 全程 SecretValue 密封；live relay 无凭据时 NOT VERIFIED 占位（非 Fake PASS）
- 兼容性/迁移：SqliteEvidenceLedger/MemoryStore（M12 闭环例外）；PostgreSQL 属 M14
- 上游版本：NCBI E-utilities ADOPTED；opencode.ai relay 用户提供
- 下一项任务：M12 重新独立复审重判；通过后 M14/M15 并行（MILESTONES DAG）
