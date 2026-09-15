# Engineering Memory Index

工程记忆只收录有计划、复检和仓库证据支撑的可复用事实。产品 `MemoryRecord`、聊天摘要、凭据和未经验证推断不进入本目录；轻量/低置信度经验条目在 `.cursor/experience/`，也不在本目录。

## 生命周期

- `ACTIVE`：当前可用。
- `SUPERSEDED`：被新证据取代，保留历史。
- `RETIRED`：不再适用，保留 provenance。
- 到达复核日期或命中失效触发器时，先复检再引用。

## Entries

| ID | Status | Scope | Confidence | Review After | Source Plan |
| --- | --- | --- | --- | --- | --- |
| [MEM-20260822-016](entries/MEM-20260822-016-m12-first-real-research-workflow.md) | ACTIVE | repository | 0.90 | 2026-12-22 | PLAN-20260822-016 |
| [MEM-20260908-017](entries/MEM-20260908-017-litellm-dotenv-gating.md) | ACTIVE | repository | 0.95 | 2026-12-08 | PLAN-20260908-033 |
| [MEM-20260910-018](entries/MEM-20260910-018-quality-gate-mechanics.md) | ACTIVE | repository | 0.90 | 2026-12-10 | PLAN-20260909-035 |
| [MEM-20260912-019](entries/MEM-20260912-019-sqlite-composition-surfacing-facts.md) | ACTIVE | repository | 0.90 | 2026-12-12 | PLAN-20260912-040 |
| [MEM-20260913-020](entries/MEM-20260913-020-goal-cycle-gate-mechanics.md) | ACTIVE | repository | 0.90 | 2026-12-13 | PLAN-20260912-041 |
| [MEM-20260913-021](entries/MEM-20260913-021-ci-guards-and-linux-only-checkers.md) | ACTIVE | repository | 0.90 | 2026-12-13 | PLAN-20260912-042 |
| [MEM-20260913-022](entries/MEM-20260913-022-linux-baseline-worktree-overlay.md) | ACTIVE | repository | 0.90 | 2026-12-13 | PLAN-20260913-043 |
| [MEM-20260914-023](entries/MEM-20260914-023-budget-ledger-sharing-and-reservation-attribution.md) | ACTIVE | repository | 0.90 | 2026-12-14 | PLAN-20260914-046 |
| [MEM-20260914-024](entries/MEM-20260914-024-live-console-artifact-fixtures-and-api-prefix.md) | ACTIVE | repository | 0.85 | 2026-12-14 | PLAN-20260914-047 |
| [MEM-20260915-025](entries/MEM-20260915-025-pause-dispatch-coordination.md) | ACTIVE | repository | 0.85 | 2026-12-15 | PLAN-20260914-048 |
| [MEM-20260915-026](entries/MEM-20260915-026-policy-capability-mirror-scopes.md) | ACTIVE | repository | 0.90 | 2026-12-15 | PLAN-20260914-049 |
| [MEM-20260915-027](entries/MEM-20260915-027-collector-quality-persistent-failures.md) | ACTIVE | repository | 0.90 | 2026-12-15 | PLAN-20260914-050 |
| [MEM-20260915-028](entries/MEM-20260915-028-collector-quality-root-causes-and-fix.md) | ACTIVE | repository | 0.95 | 2026-12-15 | PLAN-20260915-051 |
| [MEM-20260915-029](entries/MEM-20260915-029-experiment-queue-claim-and-dispatch.md) | ACTIVE | repository | 0.90 | 2026-12-15 | PLAN-20260915-052 |
| [MEM-20260915-030](entries/MEM-20260915-030-goal-closeout-verification-recipe.md) | ACTIVE | repository | 0.90 | 2027-03-15 | PLAN-20260915-053 |
| [MEM-20260915-031](entries/MEM-20260915-031-partition-injector-must-heal.md) | ACTIVE | repository | 0.90 | 2027-09-15 | PLAN-20260915-054 |
| [MEM-20260915-032](entries/MEM-20260915-032-project-lineage-merge-and-honest-unlinked-resources.md) | ACTIVE | repository | 0.90 | 2027-09-15 | PLAN-20260915-055 |
| [MEM-20260915-033](entries/MEM-20260915-033-series-projection-valued-days-only.md) | ACTIVE | repository | 0.90 | 2027-09-15 | PLAN-20260915-057 |
| [MEM-20260814-012](entries/MEM-20260814-012-m8-research-capability-plane.md) | ACTIVE | repository | 0.90 | 2026-11-14 | PLAN-20260814-012 |
| [MEM-20260814-011](entries/MEM-20260814-011-m7-quality-gate-closure.md) | ACTIVE | repository | 0.90 | 2026-11-14 | PLAN-20260814-011 |
| [MEM-20260814-010](entries/MEM-20260814-010-m7-vertical-slice-retrospective.md) | ACTIVE | repository | 0.90 | 2026-11-14 | PLAN-20260814-010 |
| [MEM-20260814-009](entries/MEM-20260814-009-m0-foundation-retrospective.md) | ACTIVE | repository | 0.90 | 2026-11-14 | PLAN-20260814-009 |
| [MEM-20260813-007](entries/MEM-20260813-007-m6-openhands-runtime-adapter.md) | ACTIVE | repository | 0.90 | 2026-11-13 | PLAN-20260813-007 |
| [MEM-20260812-006](entries/MEM-20260812-006-m5r-upstream-qualification.md) | ACTIVE | repository | 0.90 | 2026-11-12 | PLAN-20260812-006 |
| [MEM-20260812-005](entries/MEM-20260812-005-m5-ports-fakes-review.md) | ACTIVE | repository | 0.95 | 2026-11-12 | PLAN-20260812-005 |
| [MEM-20260812-004](entries/MEM-20260812-004-m4-role-team-task.md) | ACTIVE | repository | 0.95 | 2026-11-12 | PLAN-20260812-004 |
| [MEM-20260812-003](entries/MEM-20260812-003-m2-protocol-compiler-preflight.md) | ACTIVE | repository | 0.95 | 2026-11-12 | PLAN-20260812-003 |
| [MEM-20260811-002](entries/MEM-20260811-002-m3-model-relay-wiring.md) | ACTIVE | repository | 0.95 | 2026-11-11 | PLAN-20260811-002 |
| [MEM-20260811-001](entries/MEM-20260811-001-m1-domain-kernel-wiring.md) | ACTIVE | repository | 0.95 | 2026-11-11 | PLAN-20260811-001 |
| [MEM-20260810-001](entries/MEM-20260810-001-repository-baseline.md) | RETIRED | repository | 0.96 | 2026-11-10 | PLAN-20260810-001 |
| [MEM-20260810-002](entries/MEM-20260810-002-git-auto-commit-and-code-governance.md) | SUPERSEDED | repository | 0.92 | 2026-11-10 | PLAN-20260810-002 |
| [MEM-20260810-003](entries/MEM-20260810-003-governance-rules-audit-fix.md) | RETIRED | repository | 0.93 | 2026-11-10 | PLAN-20260810-003 |

这些条目记录历史工程事实；当前行为以 `AGENTS.md`、`.cursor/rules/`、Accepted ADR 和最新通过的复检为准。
