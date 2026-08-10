---
id: PLAN-20260810-001
slug: cursor-governance-bootstrap
title: Cursor 工程治理初始化
status: DONE
created_at: 2026-08-10
updated_at: 2026-08-10
cursor_plan_uri: "C:/Users/googl/.cursor/plans/cursor_工程治理初始化_ce17363a.plan.md"
owners:
  - root-agent
subagent_budget: 3
subagents_used: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260810-002-cursor-governance-bootstrap.md
memory_entries:
  - .cursor/memory/entries/MEM-20260810-001-repository-baseline.md
---

# PLAN-20260810-001 — Cursor 工程治理初始化

## 目标

在不创建 M0 业务代码、不改变 Research OS 产品 Domain/API/schema 的前提下，初始化可版本化的 Cursor Rules、Skills、持久计划、工程记忆、复检与离线治理校验闭环。

## 范围

- 包含：`.cursor/` 项目治理资产、全局 Impeccable/shadcn 技能锁、Git `main` 元数据初始化、首个自举计划与复检。
- 不包含：`apps/`、`services/`、`packages/`、业务依赖、产品数据库实体、Runtime Memory、发布提交和远程推送。
- 冻结边界：不修改 `BOOTSTRAP_MANIFEST.json` 中列出的 v0.2.2 原始文件。

## 架构与数据流

```text
AGENTS.md / Accepted ADR
→ scoped Cursor Rules
→ approved Cursor Plan
→ .cursor/plans/tasks/PLAN-*
→ implementation evidence
→ .cursor/plans/rechecks/RECHECK-*
→ .cursor/memory/entries/MEM-*
→ .cursor/plans/ALL_PLAN.md completion projection
```

工程治理层只存在于 Git 工作区。它不写入产品 PostgreSQL、事件流、向量索引或 Agent Runtime Context，也不复用 `MemoryRecord`、`ResearchTask`、`TaskContract` 等 Domain 类型。

## 验收条件

- [x] AC-01：七项 Project Rules 具有合法 `.mdc` frontmatter，并明确产品边界、子代理预算、计划/复检、UI 路由和语言约束。
- [x] AC-02：五项 Project Skills、三个模板和离线治理校验器可被 Cursor 发现并通过校验。
- [x] AC-03：每个用户任务子代理累计最多 3 个，只有根代理可委派，子代理禁止嵌套委派。
- [x] AC-04：Impeccable 与 shadcn 只引用全局安装，来源 revision、许可证和本地安装树 digest 已锁定。
- [x] AC-05：ALL_PLAN、任务计划、独立复检和工程记忆交叉引用一致；无通过复检不得勾选完成。
- [x] AC-06：原始 Bootstrap 校验与 Cursor 治理校验均通过，冻结 v0.2.2 文件 digest 未漂移。
- [x] AC-07：Git 已初始化为 `main`，但未暂存、未提交、未推送。

## 实施清单

- [x] STEP-01：复验 v0.2.2 Bootstrap，并初始化无提交的 Git `main` 分支。
- [x] STEP-02：创建 `.cursor/README.md`、技能锁和七项 Rules。
- [x] STEP-03：实现项目定向、all-plan、工程记忆、复检和治理校验 Skills 及模板。
- [x] STEP-04：创建 ALL_PLAN、首个独立复检与仓库基线工程记忆。
- [x] STEP-05：运行最终门禁，仅在证据通过后更新 `DONE` 投影。

## 子代理使用

| 序号 | 职责 | 状态 | 证据 |
| --- | --- | --- | --- |
| 1 | 核查产品 Memory 与工程记录边界 | 完成 | 已批准 Cursor Plan 的“范围与基线”“持久计划状态机” |
| 2 | 核查仓库成熟度、Cursor 目录与校验入口 | 完成 | 已批准 Cursor Plan 的“目标目录”“项目级 Rules/Skills” |
| 3 | 核查 Impeccable/shadcn 路由与供应链 | 完成 | 已批准 Cursor Plan 的“外部技能锁”“UI 技能路由” |

所有调查子代理均由根代理直接创建，提示中禁止再次委派；本任务预算已用满，不再创建子代理。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 / AC-07 | command | `python -B scripts/validate_bundle.py`；`git init -b main`；`git status --short --branch` | Bootstrap 通过；`main` 无提交 |
| EV-02 | STEP-02 / AC-01 | files | `.cursor/rules/*.mdc`、`.cursor/README.md` | 7 项 Rules 已创建 |
| EV-03 | STEP-03 / AC-02 | files | `.cursor/skills/**/SKILL.md`、模板、`governance-check/scripts/validate.py` | 5 项 Skills 与校验器已创建 |
| EV-04 | AC-04 | digest | `skills.lock.yaml`；shadcn `70af5a...`；Impeccable agents `730ca9...`、claude `7ea30a...`、cursor `556b2d...` | 所有可发现安装树已锁定 |
| EV-05 | STEP-04 / AC-05 | files/review | `RECHECK-20260810-001`；`MEM-20260810-001`；ALL_PLAN 与 Memory INDEX | attempt 1 `PASS_WITH_WARNINGS`，基线记忆已建立 |
| EV-06 | STEP-05 / AC-06 | test/review | Bootstrap validator、governance validator、Python AST、ReadLints、Git status、`RECHECK-20260810-002` | 最终门禁通过；attempt 2 `PASS_WITH_WARNINGS` |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-10 | 仅初始化 Cursor 工程治理层 | 用户明确选择，不提前生成 M0 骨架 | Domain/API/schema 无变化 |
| 2026-08-10 | 使用 ALL_PLAN 总索引 + 单任务计划 + 独立复检 | 用户明确选择，避免单文件状态与证据耦合 | 增加交叉引用校验 |
| 2026-08-10 | 初始化 Git 但不提交 | 用户明确授权，首次提交仍需另行请求 | 当前所有文件保持未跟踪 |
| 2026-08-10 | 不修改冻结 Bootstrap Manifest | 原发布包已通过审核，治理层不应伪装成 v0.2.2 原包 | 新增资产由独立 validator 管理 |
| 2026-08-10 | Impeccable 标记为可重复本地配置而非完全上游等价 | 安装树声明 4.0.4，但与 tag 源树存在安装转换差异 | 以本地 tree digest 阻止漂移 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-10 | — | DRAFT | Cursor Plan Mode 完成调查 | Cursor Plan |
| 2026-08-10 | DRAFT | APPROVED | 用户确认初始化范围与计划结构 | 已批准 Cursor Plan |
| 2026-08-10 | APPROVED | IN_PROGRESS | 开始创建治理资产 | EV-01 |
| 2026-08-10 | IN_PROGRESS | VERIFYING | attempt 1 通过并建立基线工程记忆 | EV-05 |
| 2026-08-10 | VERIFYING | DONE | attempt 2 最终复检通过 | EV-06 |

## 影响报告

- Domain/API/schema：无变化。
- 安全/凭据：未写入凭据；新增敏感内容扫描和外部 Skill digest 门禁。
- 兼容性/迁移：依赖 Cursor 官方 `.cursor/rules` 与 `.cursor/skills` 发现机制；无产品迁移。
- 上游版本：Impeccable 4.0.4 的三个 provider 安装树和 shadcn Skill 提交已锁定；未来升级必须显式复检。
- 下一项任务：由用户决定是否创建首次 Git 提交，或进入 `CODEX_BOOTSTRAP.md` 的 M0 Repository Foundation 计划。