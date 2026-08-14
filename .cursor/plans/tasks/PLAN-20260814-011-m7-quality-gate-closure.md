---
id: PLAN-20260814-011
slug: m7-quality-gate-closure
title: M7 Post-Completion Quality Gate Closure
status: DONE
created_at: 2026-08-14
updated_at: 2026-08-14
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "用户明确指示执行第二步：修复 ruff 4 errors + mypy 16 errors，使 m0 profile 恢复全绿"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260814-011-m7-quality-gate-closure.md
memory_entries:
  - MEM-20260814-011
---

# PLAN-20260814-011 — M7 Post-Completion Quality Gate Closure

## 目标

修复 M7 交付后遗留的确定性门禁红灯（2026-08-14 m0 profile 实测）：
`python/product-lint` 4 errors、`python/format-check` 12 files、
`python/typecheck`（mypy strict）16 errors；使 m0 profile 全绿，作为
后续产品能力建设的确定性前提。learning-evals 问题（LEARN registry）
不在本任务范围（独立 P2 项）。

## 范围

- 包含：ruff lint 3 个文件手动修复 + format 12 个文件机械格式化；mypy
  strict 5 处类型修复；全量回归（m0 profile + 双 validator + pytest）；
  BACKLOG/CHANGELOG 更新；recheck + 工程记忆；semantic commit + push。
- 不包含：learning-evals registry 修复；任何行为/语义变更（本任务只做
  类型注解、import 排序、格式化与 unused import 清理）；产品功能开发。

## 架构与数据流

无行为变更。修复面：
- `packages/application/run_orchestration/__init__.py`（import 排序）、
  `service.py`（unused imports）；
- `packages/application/preflight/preflight.py`（frozen_contracts 类型注解
  与 RunManifest.task_contracts 对齐，`dict[str, object]`）；
- `tests/`：`test_m2_policy_budget.py`（Reserver 补齐 BudgetLedger
  protocol 的 release）、`test_run_rejections.py`（capabilities 键改用
  ModelCapability 枚举）、`test_fault_convergence.py`（_start 返回类型
  修正为 RunOutcome）、`test_cancel_resume.py`（_drift_parts 用 TypedDict
  精确类型化）、`test_orchestration_convergence.py`（import 排序）。

## 验收条件

- [x] AC-01：`ruff check packages adapters tests` 0 errors。
- [x] AC-02：`ruff format --check`（m0 profile 同款命令）0 unformatted。
- [x] AC-03：`mypy`（m0 profile 同款 strict 配置）0 errors。
- [x] AC-04：pytest 全量通过（与 989 基线一致或更高）。
- [x] AC-05：validate_bundle + governance validate 均 PASS。
- [x] AC-06：m0 profile 全绿（除 learning-evals 既有 P2 项外）。
- [x] AC-07：BACKLOG 第 1、2 项标记完成；CHANGELOG 增补条目。

## 实施清单

- [x] STEP-01：创建立项记录并注册 ALL_PLAN（本计划）。
- [x] STEP-02：ruff lint 手动修复（__init__.py / service.py /
      test_orchestration_convergence.py）+ ruff format 12 files。
- [x] STEP-03：mypy strict 5 处修复（preflight.py / test_m2_policy_budget /
      test_run_rejections / test_fault_convergence / test_cancel_resume）。
- [x] STEP-04：全量回归：m0 profile（uv run --frozen --no-sync）+ 双
      validator + pytest。
- [x] STEP-05：BACKLOG/CHANGELOG 更新；recheck + 工程记忆；semantic
      commit + push。

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波
完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 基线 | check | m0 profile（2026-08-14 对账会话） | product-lint 4 errors / format 12 files / mypy 16 errors / pytest 989 passed |
| EV-02 | STEP-02 | check | `ruff check packages adapters tests` + `ruff format --check` | 0 errors；244 files already formatted（2026-08-14） |
| EV-03 | STEP-03 | check | `python -m mypy` | Success: no issues found in 227 source files（2026-08-14） |
| EV-04 | STEP-04 | test | `uv run --frozen --no-sync ... run_all_checks.py --profile m0 --keep-going` | pytest 989 passed；双 validator PASS；TypeScript 全 PASS；唯一 FAIL 为 learning-evals（P2，范围外） |
| EV-05 | STEP-05 | check | validate_bundle + governance validate + git log | 双 validator PASS（2026-08-14）；commit 待 push 后记录 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-14 | learning-evals 不并入本任务 | 属 `.cursor/learning/` 资产（P2），与产品代码门禁无关 | BACKLOG 独立跟踪 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-14 | — | IN_PROGRESS | 用户明确授权执行 M7 收尾工程债 | 用户指示 |

## 影响报告

- Domain/API/schema：无运行时行为变化；仅类型注解与 import 调整。
- 安全/凭据：无。
- 兼容性/迁移：无；mypy 注解收紧不改序列化契约。
- 上游版本：openhands-sdk v1.42.0 不变。
- 下一项任务：m0 profile 全绿后，可进入 BACKLOG Next Product Capability
  （Research Tool Plane）或 learning-evals P2 修复。