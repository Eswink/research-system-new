---
id: MEM-20260810-001
title: Research OS 仓库基线与 Cursor 治理边界
status: RETIRED
created_at: 2026-08-10
updated_at: 2026-08-11
scope: repository
confidence: 0.96
review_after: 2026-11-10
source_plans:
  - .cursor/plans/archive/PLAN-20260810-001-cursor-governance-bootstrap.md
source_rechecks:
  - .cursor/plans/archive/RECHECK-20260810-001-cursor-governance-bootstrap.md
  - .cursor/plans/archive/RECHECK-20260810-002-cursor-governance-bootstrap.md
supersedes: []
tags:
  - repository-baseline
  - cursor-governance
  - planning
  - supply-chain
---

# MEM-20260810-001 — Research OS 仓库基线与 Cursor 治理边界

## 做了什么

Research OS 当前是 `v0.2.2` docs-first Bootstrap：已存在产品架构、ADR、Schema、示例配置和 bundle validator，规划中的 M0 应用 monorepo 尚未创建。本次新增 `.cursor/` 工程治理层，包含七项 Rules、五项 Skills、持久计划、独立复检、工程记忆和外部 UI Skill 锁；Git 初始化为无提交的 `main`。

工程记录使用 `PLAN-*`、`RECHECK-*`、`MEM-*`，只在 Git 工作区中流转。它们不映射产品 `MemoryRecord`、`MemoryWriteProposal`、`ResearchTask`、`TaskContract`、`HandoffBundle`、`PreflightReport` 或 `RunManifest`，也不进入产品 PostgreSQL、事件流、向量索引或 Agent Runtime Context。

## 为什么这样做

产品 Memory 已由 `AGENTS.md` 与 ADR-0017 定义为经过 provenance 和 policy gate 的 Domain 能力；若复用它保存 Agent 编程日志，会污染 Canonical State 并混淆产品运行与仓库协作。独立的 Cursor 治理层既能版本化“做了什么、怎么做”，又不改变已批准的 v0.2.2 产品边界。

持久计划采用“ALL_PLAN 总索引 + 单任务计划 + 独立复检”，让进度投影、详细证据和验收职责分离。只有最新复检通过后才允许 `DONE` 和勾选，避免 checklist 自报完成。

## 怎么做与复现

1. 先读 `AGENTS.md`、`README.md`、`CODEX_BOOTSTRAP.md` 与任务相关 ADR，确认所有权和不可变边界。
2. 复杂任务先在 Cursor Plan Mode 只读调查并取得用户批准，再显式调用 `all-plan` 固化任务。
3. 实施时把证据追加到任务计划；每个用户任务最多使用 3 个子代理，且子代理禁止再委派。
4. UI 设计先路由全局 Impeccable；shadcn 组件实现路由官方 shadcn Skill；设计并实现遵循 `Impeccable → shadcn → Impeccable audit/polish`。
5. 完成前运行：
   - `python -B scripts/validate_bundle.py`
   - `python -B .cursor/skills/governance-check/scripts/validate.py`
   - `git status --short --branch`
6. 创建独立 `RECHECK-*`；通过后提炼 `MEM-*` 并更新 `ALL_PLAN.md` 完成投影。

## 适用边界

- 适用于：当前仓库的 Agent 工程协作、计划、复检、UI Skill 路由和供应链漂移检查。
- 不适用于：Research OS 产品运行时 Memory、ResearchTask、Protocol Preflight、RunManifest 或数据库 Canonical State。
- 不代表 M0 已实现；`apps/`、`services/`、`packages/` 仍只是 `CODEX_BOOTSTRAP.md` 中的目标结构。

## 失效与复核触发器

- 到达 `review_after`。
- `AGENTS.md`、Accepted ADR、`CODEX_BOOTSTRAP.md` 或 v0.2.2 发布基线发生变化。
- Cursor 改变 `.cursor/rules`、`.cursor/skills` 或 Plan Mode 的发现/持久化机制。
- Impeccable、shadcn 或其任一全局 provider 安装树 digest 变化。
- M0 仓库骨架落地，当前“docs-first Bootstrap”判断不再成立。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/archive/PLAN-20260810-001-cursor-governance-bootstrap.md` | 用户批准范围、目录结构、状态机和实施证据 |
| recheck | `.cursor/plans/archive/RECHECK-20260810-001-cursor-governance-bootstrap.md` | Bootstrap、治理校验、语法、安全和供应链检查已通过 |
| repository | `AGENTS.md`、`CODEX_BOOTSTRAP.md`、`docs/adr/ADR-0017-evidence-backed-memory.md` | 产品边界、目标工程结构和产品 Memory 写入门禁 |
| digest | `BOOTSTRAP_MANIFEST.json`、`.cursor/skills.lock.yaml` | 冻结原始包与全局 UI Skill 安装树基线 |