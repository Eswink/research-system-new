---
id: MEM-20260810-003
title: 治理规则审计修正与自动提交安全边界
status: ACTIVE
created_at: 2026-08-10
updated_at: 2026-08-10
scope: repository
confidence: 0.93
review_after: 2026-11-10
source_plans:
  - .cursor/plans/tasks/PLAN-20260810-003-governance-rules-audit-fix.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260810-004-governance-rules-audit-fix.md
supersedes:
  - .cursor/memory/entries/MEM-20260810-002-git-auto-commit-and-code-governance.md
tags:
  - governance
  - git
  - hooks
  - code-quality
---

# MEM-20260810-003 — 治理规则审计修正与自动提交安全边界

## 做了什么

- 将 `.cursor/hooks/snapshot_commit.py` 从"stop 事件自动快照提交"改为**只审计**模式：只报告残留变更分类（modified / 白名单未跟踪 / 敏感 / 白名单外），绝不执行 `git add` / `git commit` / `git push`。语义提交仅由 agent 在任务复检通过后按 43 规则显式执行。
- 治理校验器 `validate.py`：`EXPECTED_RULES` 补齐 42/43/44；新增期望元数据断言（alwaysApply/globs）；`check_hooks` 断言 stop 脚本不含 `git commit/push`（剥离 docstring/注释后匹配）；DONE 任务 memory 改为条件性（无 memory 时必须声明"无可复用事实"）。
- 修正规则：40/41 globs 收窄到 M0 目录（`apps/ services/ packages/ adapters/ tests/`）并加冻结/治理脚本豁免段；44 依赖方向改为 `adapter/infra → application → domain`（与 SYSTEM_ARCHITECTURE 一致）并删除重复数值；43 修正 `.cursor/hooks.json` 路径、删"提交后写回"条款、明确 `.env.example` 样例边界；30 增加 globs；50 覆盖根级冻结契约；42 移除本机版本号；20/00 明确 all-plan/recheck/engineering-memory 为显式调用流程。

## 为什么这样做

- 原 stop hook 会在 aborted/error 会话把全部 tracked 修改（含任务前已有、预先暂存的无关改动）直接提交，存在越权提交风险，与"不回退无关改动"冲突；审计确认后用户选择"只审计不自动提交"。
- 300 行/50 行硬阈值若覆盖 `**/*.py` 会立即违反冻结的 `scripts/validate_bundle.py`（377 行）与治理校验器（627 行），且 `BOOTSTRAP_MANIFEST.json` 禁止修改前者；用户确认阈值仅作用于未来 M0 产品代码。
- 依赖方向原写 `domain → application → adapter/infra` 并称"依赖只能自上而下"，与下一行"Domain 不得依赖外层"及产品契约矛盾，必须区分"源码依赖方向"与"调用/数据流方向"。

## 怎么做与复现

1. 审计基线：`git status` 应干净；两个 validator 全绿；子代理预算 ≤3。
2. hook 只审计回归：`git init` 临时仓库 → 制造 modified/白名单未跟踪/敏感/白名单外四类变更 → `SNAPSHOT_HOOK_ROOT=<temp> python .cursor/hooks/snapshot_commit.py --debug` → 只输出分类报告，`git log` 无新提交。
3. 校验：`python -B scripts/validate_bundle.py`；`python -B .cursor/skills/governance-check/scripts/validate.py`；`python -m py_compile .cursor/hooks/snapshot_commit.py .cursor/skills/governance-check/scripts/validate.py`。
4. 语义提交（仅由 agent 收尾执行）：白名单 `git add`（禁止 `-A`）→ Conventional Commits → 双 validator 门禁 → 仅本地；push 需用户显式授权。

## 适用边界

- 适用于：Research OS 仓库 Cursor 治理层与未来 M0 业务代码约束。
- 不适用于：产品 Domain 语义（以 AGENTS.md 与已批准 ADR 为准）；冻结发布资产（BOOTSTRAP_MANIFEST 所列文件）仅在显式发布流程中变更。
- 本条目取代 MEM-20260810-002 中"stop hook 兜底快照提交"的结论；提交策略整体仍以 43 规则为准。

## 失效与复核触发器

- 到达 `review_after`（2026-11-10）。
- Cursor Hooks 事件/路径变化（`.cursor/hooks.json` 迁移、stop 事件语义变化）。
- M0 建包落地 ruff/ESLint 配置后，40/41/44 阈值映射需与实际配置复核。
- 发布新版本使 `AGENTS.md` 等冻结资产解除冻结后，工程命令与 §9 deny 的边界需并入 AGENTS。

## 来源

| 类型 | 引用 | 支持的结论 |
| --- | --- | --- |
| plan | `.cursor/plans/tasks/PLAN-20260810-003-governance-rules-audit-fix.md` | 目标、范围、验收条件与证据 |
| recheck | `.cursor/plans/rechecks/RECHECK-20260810-004-governance-rules-audit-fix.md` | PASS_WITH_WARNINGS，AC 全部通过 |
| repository | `.cursor/hooks/snapshot_commit.py` | 只审计实现与敏感文件分类 |
| repository | `.cursor/rules/43-git-commit-policy.mdc` | 语义提交与 push 授权边界 |
| repository | `.cursor/rules/44-code-architecture.mdc` | 依赖方向修正 |
| repository | `docs/architecture/SYSTEM_ARCHITECTURE.md` §3 | Domain 不依赖具体实现 |