# Research OS — ALL PLAN

本文件是项目任务的唯一活动总索引。详细范围、执行日志和证据保存在单任务计划；复检和工程记忆分别保存在独立目录。

## 状态约束

- 只有任务计划状态为 `DONE` 且最新复检为 `PASS` 或 `PASS_WITH_WARNINGS` 时，Done 列才能勾选。
- `REVISE`、`BLOCK` 或失效触发器会使任务进入 `IN_PROGRESS`、`BLOCKED` 或 `REOPENED`，不得静默保留完成投影。
- 状态与链接由 `all-plan` 工作流维护，并由治理校验器交叉验证。

## 活动任务

| Done | Plan | Status | Updated | Latest Recheck | Memory |
| --- | --- | --- | --- | --- | --- |
| [x] | [PLAN-20260810-001](tasks/PLAN-20260810-001-cursor-governance-bootstrap.md) | DONE | 2026-08-10 | [RECHECK-20260810-002](rechecks/RECHECK-20260810-002-cursor-governance-bootstrap.md) | [MEM-20260810-001](../memory/entries/MEM-20260810-001-repository-baseline.md) |
| [x] | [PLAN-20260810-002](tasks/PLAN-20260810-002-git-auto-commit-and-code-governance.md) | DONE | 2026-08-10 | [RECHECK-20260810-003](rechecks/RECHECK-20260810-003-git-auto-commit-and-code-governance.md) | [MEM-20260810-002](../memory/entries/MEM-20260810-002-git-auto-commit-and-code-governance.md) |
| [x] | [PLAN-20260810-003](tasks/PLAN-20260810-003-governance-rules-audit-fix.md) | DONE | 2026-08-10 | [RECHECK-20260810-004](rechecks/RECHECK-20260810-004-governance-rules-audit-fix.md) | [MEM-20260810-003](../memory/entries/MEM-20260810-003-governance-rules-audit-fix.md) |

## 最近完成

暂无。

## 归档

归档规则见 [archive/README.md](archive/README.md)。