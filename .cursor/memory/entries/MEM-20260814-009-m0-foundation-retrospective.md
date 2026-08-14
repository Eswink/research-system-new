---
id: MEM-20260814-009
title: M0 Repository Foundation Quality Gate 完成事实（retrospective）
status: ACTIVE
created_at: 2026-08-14
updated_at: 2026-08-14
scope: repository
confidence: 0.9
review_after: 2026-11-14
source_plans:
  - .cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md
supersedes: []
tags: [m0, foundation, retrospective, quality-gate]
---

# MEM-20260814-009 — M0 Repository Foundation Quality Gate 完成事实

## 做了什么

M0（Repository Foundation Quality Gate）以 commit `3cc6130`
（2026-08-11）落地 v0.4.0 工程基线：Python 3.12 + uv exact lockfile
（ruff/mypy strict/import-linter/pytest）、TypeScript 22.18.0 + pnpm
（ESLint 自定义架构规则 + dependency-cruiser）、双语言依赖边界正反向
夹具（`tests/architecture/python` 与 `tests/architecture/typescript`）、
CI 门禁（`.github/workflows/m0-quality.yml`）与质量聚合入口
（`.cursor/skills/cursor-framework-check/scripts/run_all_checks.py`，
m0 profile 18 项确定性门禁）。M0 未创建空生产包。

本记忆由 2026-08-14 文档对账任务事后重建（M0 原开发窗口无独立
Plan/Recheck/Memory）；事实证据为 git log、当前工作区文件与重跑的
validator，详见 PLAN-20260814-009。

## 为什么这样做

M0 是全部后续阶段的门禁基线：每阶段（M1-M7）验收均以 m0 profile 全量
回归为确定性证据；依赖边界正反向夹具是 `domain / application / adapter`
分层唯一机器可验证的 enforcement 点。事后重建用于补全工程记录缺口，
不改变当时的实现事实。

## 怎么做与复现

1. 验证 M0 门禁：`python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`
2. 验证边界：`pytest tests/architecture tests/tooling`
3. 验证契约资产：`python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`
4. 验证治理资产：`python -B .cursor/skills/governance-check/scripts/validate.py`

## 适用边界

- 适用于：M0 完成状态与证据入口的引用；新生产模块进入时对依赖边界
  门禁的更新义务（`.importlinter.*` / dependency-cruiser /
  `tests/architecture/` 同步）。
- 不适用于：M0 开发窗口内讨论、评审或时间线的重建（本记忆不包含
  此类陈述）；产品业务能力的实现状态（见 M1-M7 各记忆）。

## 失效与复核触发器

- 到达 `review_after`（2026-11-14）时先复核再引用。
- 工具链（ruff/mypy/import-linter/dependency-cruiser）或门禁脚本变更时，
  以 `run_all_checks.py` 与 CI 定义为当前事实源。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260814-009-m0-foundation-retrospective.md` | M0 重建记录与 DoD 核对 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260814-009-m0-foundation-retrospective.md` | 2026-08-14 实际重跑验证 |
| git | `3cc6130` / `5045c59` | M0 基线与前身 |
| repository | `pyproject.toml` / `uv.lock` / `pnpm-lock.yaml` / `.importlinter*` | 工具链与边界契约 |
| repository | `tests/architecture/`（python + typescript） | 正反向夹具 |