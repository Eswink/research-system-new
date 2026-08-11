# Engineering Memory Index

工程记忆只收录有计划、复检和仓库证据支撑的可复用事实。产品 `MemoryRecord`、聊天摘要、凭据和未经验证推断不进入本目录。

## 生命周期

- `ACTIVE`：当前可用。
- `SUPERSEDED`：被新证据取代，保留历史。
- `RETIRED`：不再适用，保留 provenance。
- 到达复核日期或命中失效触发器时，先复检再引用。

## Entries

| ID | Status | Scope | Confidence | Review After | Source Plan |
| --- | --- | --- | --- | --- | --- |
| [MEM-20260811-002](entries/MEM-20260811-002-m3-model-relay-wiring.md) | ACTIVE | repository | 0.95 | 2026-11-11 | PLAN-20260811-002 |
| [MEM-20260811-001](entries/MEM-20260811-001-m1-domain-kernel-wiring.md) | ACTIVE | repository | 0.95 | 2026-11-11 | PLAN-20260811-001 |
| [MEM-20260810-001](entries/MEM-20260810-001-repository-baseline.md) | RETIRED | repository | 0.96 | 2026-11-10 | PLAN-20260810-001 |
| [MEM-20260810-002](entries/MEM-20260810-002-git-auto-commit-and-code-governance.md) | SUPERSEDED | repository | 0.92 | 2026-11-10 | PLAN-20260810-002 |
| [MEM-20260810-003](entries/MEM-20260810-003-governance-rules-audit-fix.md) | RETIRED | repository | 0.93 | 2026-11-10 | PLAN-20260810-003 |

这些条目记录历史工程事实；当前行为以 `AGENTS.md`、`.cursor/rules/`、Accepted ADR 和最新通过的复检为准。
