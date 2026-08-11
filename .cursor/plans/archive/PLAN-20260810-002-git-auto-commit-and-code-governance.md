---
id: PLAN-20260810-002
slug: git-auto-commit-and-code-governance
title: Git 自动提交与代码工程约束规范
status: DONE
created_at: 2026-08-10
updated_at: 2026-08-10
cursor_plan_uri: "c:/Users/googl/.cursor/plans/git自动提交与代码工程约束_7727b81a.plan.md"
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/archive/RECHECK-20260810-003-git-auto-commit-and-code-governance.md
memory_entries:
  - .cursor/memory/entries/MEM-20260810-002-git-auto-commit-and-code-governance.md
---

# PLAN-20260810-002 — Git 自动提交与代码工程约束规范

## 目标

1. 建立"任务完成即自动 git 提交"机制：规则约定为主（任务复检通过、收尾完成后按白名单提交），会话结束由 stop hook 兜底快照；仅本地提交，不自动 push，避免堆积、便于回滚。
2. 将工程级代码规模/复杂度阈值与解耦拆分约束固化进 `.cursor/rules/`，为未来 M0 业务代码提供规范基线。

## 范围

- 包含：`.cursor/rules/43-git-commit-policy.mdc`、`.cursor/rules/44-code-architecture.mdc`、40/41 规则阈值扩展、`.cursor/hooks.json` + `.cursor/hooks/snapshot_commit.py`、治理校验器 hooks 校验、`.cursor/README.md` 闭环更新、任务计划/复检/工程记忆收尾。
- 不包含：`apps/`、`services/`、`packages/`、`pyproject.toml`、`package.json`（M0 范围外，仅在规则中固化配置要求）、自动 push、修改 `AGENTS.md`（冻结 Bootstrap 资产，不可漂移）。
- 冻结边界：不修改 `BOOTSTRAP_MANIFEST.json` 中列出的 v0.2.2 原始文件；`AGENTS.md` 列入冻结清单，自动提交步骤改由 `.cursor/README.md` 与 43 规则承载。

## 架构与数据流

```text
任务复检 PASS + 收尾完成
→ 门禁（validate_bundle + governance validator）
→ 白名单 git add（禁止 -A）
→ Conventional Commits 提交（仅本地，不 push）
→ 影响报告记录 commit hash

会话结束（stop 事件）有未提交变更
→ snapshot_commit.py 兜底
→ chore(worktree) 快照提交（幂等、跳过敏感文件）
```

规则约定负责任务语义提交；stop hook 只做兜底快照，两者消息格式由 43 规则统一定义。

## 验收条件

- [x] AC-01：任务收尾时按 43 规则白名单 `git add` + Conventional Commits 提交；任何路径不使用 `git add -A`。
- [x] AC-02：stop hook 兜底生效：有未提交变更产生 `chore(worktree)` 快照；幂等（无变更即退出）；`.env*` 等敏感文件与白名单外文件永不入库。
- [x] AC-03：`40-python.mdc` / `41-typescript.mdc` 包含量化阈值（行长 100、函数 ≤50 行、文件 ≤300 行、CCN ≤10/≤15、深度/参数上限）。
- [x] AC-04：`44-code-architecture.mdc` 包含 SRP、依赖单向、反模式与 M0 工具配置要求（ruff/mypy/ESLint/import-linter/dependency-cruiser）。
- [x] AC-05：治理校验器新增 hooks 校验生效；`validate_bundle.py` 与 governance validator 均通过；Bootstrap 冻结基线未漂移。
- [x] AC-06：无自动 push；回滚指引（`git reset --soft` / `git revert`）已写入 43 规则；本任务自身完成一次示范提交。

## 实施清单

- [x] STEP-01：新增 `.cursor/rules/43-git-commit-policy.mdc`（触发时机、Conventional Commits、白名单、门禁、回滚）。
- [x] STEP-02：新增 `.cursor/hooks.json` 与 `.cursor/hooks/snapshot_commit.py`（stop 兜底、幂等、敏感文件跳过），并在临时仓库端到端验证。
- [x] STEP-03：扩展 `40-python.mdc` / `41-typescript.mdc` 量化阈值。
- [x] STEP-04：新增 `.cursor/rules/44-code-architecture.mdc` 解耦约束。
- [x] STEP-05：更新 `.cursor/README.md` 标准闭环（`AGENTS.md` 冻结，改由 README 承载）。
- [x] STEP-06：扩展 governance validator `check_hooks`，两个校验器跑通全绿。
- [x] STEP-07：创建本任务计划，更新 ALL_PLAN 索引。

## 子代理使用

| 序号 | 职责 | 状态 | 证据 |
| --- | --- | --- | --- |
| 1 | 调研 Cursor 自动 git 提交机制（Hooks/Automations/Conventional Commits/安全） | 完成 | 调研报告：stop 事件为落点；hooks.json 位于项目根；不建议自动 push |
| 2 | 调研代码规模/复杂度阈值与解耦规范（ruff/ESLint/Google/PEP 8） | 完成 | 调研报告：行长 80-120、函数 ≤50 行、文件 ≤300 行、CCN ≤10-15；import-linter/dependency-cruiser |

两个调研子代理由根代理直接创建，提示中禁止再次委派；本任务预算剩余 1，实施阶段不再委派。

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 / AC-01 / AC-06 | file | `.cursor/rules/43-git-commit-policy.mdc` | 白名单 add、Conventional Commits、门禁、回滚指引已固化 |
| EV-02 | STEP-02 / AC-02 | test | 临时仓库端到端：`git init` → 修改/新文件/敏感文件 → `python snapshot_commit.py --debug` | `chore(worktree)` 提交成功；`.env.local`（敏感）与 `secret.tmp`（白名单外）被跳过；二次运行无变更退出 |
| EV-03 | STEP-03 / AC-03 | file | `.cursor/rules/40-python.mdc`、`41-typescript.mdc` | 量化阈值已追加 |
| EV-04 | STEP-04 / AC-04 | file | `.cursor/rules/44-code-architecture.mdc` | SRP/依赖单向/反模式/M0 工具链已固化 |
| EV-05 | STEP-05 | file | `.cursor/README.md` | 标准闭环新增提交步骤与 hooks 职责行 |
| EV-06 | STEP-06 / AC-05 | test | `python -B scripts/validate_bundle.py`；`python -B .cursor/skills/governance-check/scripts/validate.py`；`python -m py_compile` | 两个校验器全绿；冻结基线未漂移；py_compile 通过 |
| EV-07 | STEP-07 | file | `.cursor/plans/tasks/PLAN-20260810-002-*.md`；ALL_PLAN | 计划已建、索引已更新 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-08-10 | 触发机制采用"规则约定为主 + stop hook 兜底" | 用户确认 hybrid；hook 无法识别任务语义，只做兜底 | 语义提交与快照提交消息可区分 |
| 2026-08-10 | 仅本地 commit，不自动 push | 用户确认 local-only；已 push 难以撤回 | 回滚用 `git reset --soft` / `git revert` |
| 2026-08-10 | `AGENTS.md` 修改被回退，改由 `.cursor/README.md` 承载 | `AGENTS.md` 列入 BOOTSTRAP_MANIFEST 冻结清单，digest 校验失败 | 自动提交步骤记录于 README 与 43 规则，不触碰冻结资产 |
| 2026-08-10 | hooks 配置置于项目根 `.cursor/hooks.json` | Cursor create-hook 技能文档与调研双重确认当前路径 | 脚本位于 `.cursor/hooks/` |
| 2026-08-10 | 不创建 pyproject.toml / package.json | M0 范围外 | 工具链配置要求固化为规则，建包时落地 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-08-10 | — | DRAFT | Cursor Plan Mode 完成调查 | 已批准 Cursor Plan |
| 2026-08-10 | DRAFT | APPROVED | 用户确认混合触发 + 仅本地提交 | 已批准 Cursor Plan |
| 2026-08-10 | APPROVED | IN_PROGRESS | 开始实施 | EV-01 |
| 2026-08-10 | IN_PROGRESS | VERIFYING | 实施完成，创建独立复检 | EV-01..EV-07、RECHECK-20260810-003 |
| 2026-08-10 | VERIFYING | DONE | 复检 PASS_WITH_WARNINGS，工程记忆已写入 | RECHECK-20260810-003、MEM-20260810-002 |

## 影响报告

- Domain/API/schema：无变化（仅 Cursor 工程治理层）。
- 安全/凭据：hook 显式跳过 `.env*`、密钥文件与含密钥模式内容；未写入凭据。
- 兼容性/迁移：新增 `.cursor/hooks.json` 依赖 Cursor Hooks 机制（stop 事件）；无产品迁移。
- 上游版本：无新增上游依赖；外部 Skill 锁不受影响。
- 下一项任务：完成复检与工程记忆收尾后，由用户决定是否手动 push 本任务提交；随后进入 `CODEX_BOOTSTRAP.md` 的 M0 Repository Foundation。