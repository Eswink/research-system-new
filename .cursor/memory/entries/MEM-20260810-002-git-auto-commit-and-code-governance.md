---
id: MEM-20260810-002
title: Git 自动提交策略与代码工程约束基线
status: SUPERSEDED
created_at: 2026-08-10
updated_at: 2026-08-10
scope: repository
confidence: 0.92
review_after: 2026-11-10
source_plans:
  - .cursor/plans/tasks/PLAN-20260810-002-git-auto-commit-and-code-governance.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260810-003-git-auto-commit-and-code-governance.md
supersedes: []
tags:
  - git
  - governance
  - code-quality
---

# MEM-20260810-002 — Git 自动提交策略与代码工程约束基线

## 做了什么

- 建立任务收尾自动提交策略：规则约定为主（`.cursor/rules/43-git-commit-policy.mdc`），stop hook 兜底（`.cursor/hooks/snapshot_commit.py`）；仅本地提交，不自动 push。
- 固化代码规模/复杂度阈值：Python 行长 ≤100、函数 ≤50 行、文件 ≤300 行、CCN ≤10、参数 ≤5、深度 ≤4（`40-python.mdc`）；TypeScript 行长 ≤100、函数 ≤50 行、文件 ≤300 行、complexity ≤15、max-depth ≤4、max-params ≤3、max-nested-callbacks ≤10（`41-typescript.mdc`）。
- 固化解耦约束：SRP、依赖单向（domain → application → adapter/infra）、反模式清单与 M0 工具链要求（`44-code-architecture.mdc`）。
- 治理校验器新增 `check_hooks`：`.cursor/hooks.json` 必须存在、`version == 1`、含 `stop` 事件且命令指向存在的脚本。

## 为什么这样做

- 任务完成语义已由治理流程定义（复检 PASS → 收尾），自动提交挂在该时点避免变更堆积、便于回滚；hook 无法识别任务语义，只做兜底快照，消息固定 `chore(worktree)` 与语义提交可区分。
- 阈值取值参考 PEP 8 / Google Style / 常见 lint 默认值（ruff mccabe、ESLint max-*），并保留未来工具配置的精确映射。
- `AGENTS.md` 列入 BOOTSTRAP_MANIFEST 冻结清单，改动会导致 digest 校验失败，因此自动提交步骤改由 `.cursor/README.md` 与 43 规则承载。
- Cursor hooks 当前路径为项目根 `.cursor/hooks.json`（create-hook 技能与调研双重确认）。

## 怎么做与复现

1. 语义提交：任务复检通过后，按 43 规则白名单 `git add`（禁止 `-A`），提交前跑两个 validator，Conventional Commits 格式，仅本地。
2. 兜底提交：会话结束由 `.cursor/hooks.json` stop 事件调用 `python .cursor/hooks/snapshot_commit.py`；可用 `--debug` 在真实工作区直接执行测试。
3. 校验：`python -B scripts/validate_bundle.py`；`python -B .cursor/skills/governance-check/scripts/validate.py`。
4. hook 测试注入：设置环境变量 `SNAPSHOT_HOOK_ROOT` 指向临时仓库即可离线验证（端到端已验证：tracked 修改与白名单新文件入库，`.env.local` 与白名单外文件被跳过，二次运行幂等退出）。

## 适用边界

- 适用于：Research OS 仓库的 Cursor 治理层与未来 M0 业务代码约束。
- 不适用于：产品 Domain 语义（Memory/Task/Handoff 等仍以 `AGENTS.md` 与已批准 ADR 为准）；hook 不替代任务语义提交。

## 失效与复核触发器

- 到达 `review_after`（2026-11-10）。
- Cursor Hooks 路径/事件名变化（`.cursor/hooks.json` 迁移或 stop 事件改名）。
- M0 建包时工具链配置落地后，阈值映射（ruff/ESLint 配置项）需与实际配置复核。
- `AGENTS.md` 解除冻结（用户批准发布新版本）后，第 13 节提交步骤的承载位置需同步。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260810-002-git-auto-commit-and-code-governance.md` | 目标、范围、验收条件与证据 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260810-003-git-auto-commit-and-code-governance.md` | PASS_WITH_WARNINGS，AC 全部通过 |
| repository | `.cursor/rules/43-git-commit-policy.mdc` | 提交策略与回滚指引 |
| repository | `.cursor/hooks/snapshot_commit.py` | 兜底实现与敏感文件过滤 |
| repository | `.cursor/rules/40-python.mdc`、`41-typescript.mdc`、`44-code-architecture.mdc` | 阈值与解耦约束 |