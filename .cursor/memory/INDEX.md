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
| [MEM-20260915-034](entries/MEM-20260915-034-digest-addressed-snapshot-read-surface.md) | ACTIVE | repository | 0.90 | 2027-09-15 | PLAN-20260915-058 |
| [MEM-20260915-035](entries/MEM-20260915-035-write-surface-must-be-consumed-by-read-surface.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-059 |
| [MEM-20260915-036](entries/MEM-20260915-036-registration-state-derives-trust.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-060 |
| [MEM-20260915-037](entries/MEM-20260915-037-delete-must-refuse-when-referenced.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-061 |
| [MEM-20260915-038](entries/MEM-20260915-038-structural-signature-complements-pixel-gate.md) | ACTIVE | repository | 0.92 | 2027-09-16 | PLAN-20260915-063 |
| [MEM-20260915-039](entries/MEM-20260915-039-tool-pack-install-binds-content-digest.md) | ACTIVE | repository | 0.92 | 2027-09-16 | PLAN-20260915-064 |
| [MEM-20260915-040](entries/MEM-20260915-040-pending-must-be-visible-in-ui.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-065 |
| [MEM-20260915-041](entries/MEM-20260915-041-scheduler-remains-the-executor.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-066 |
| [MEM-20260915-042](entries/MEM-20260915-042-sigterm-cannot-break-a-blocked-read.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-067 |
| [MEM-20260915-043](entries/MEM-20260915-043-stub-must-enforce-the-contract-it-stands-in-for.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-068 |
| [MEM-20260915-044](entries/MEM-20260915-044-schema-digest-is-a-state-not-an-event.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-069 |
| [MEM-20260915-045](entries/MEM-20260915-045-shared-connection-is-not-concurrency-safety.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-070 |
| [MEM-20260915-046](entries/MEM-20260915-046-statement-serialization-is-not-read-atomicity.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-071 |
| [MEM-20260915-047](entries/MEM-20260915-047-declared-but-unconsumed-config-is-a-lie.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-072 |
| [MEM-20260915-048](entries/MEM-20260915-048-nonportable-counterexamples-are-not-gates.md) | ACTIVE | repository | 0.90 | 2027-09-16 | PLAN-20260915-073 |
| [MEM-20260915-049](entries/MEM-20260915-049-presence-check-is-not-a-resolve.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260915-074 |
| [MEM-20260915-050](entries/MEM-20260915-050-a-promise-with-two-entry-points.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260915-075 |
| [MEM-20260915-051](entries/MEM-20260915-051-enumerate-the-boundary-then-gate-it.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260915-076 |
| [MEM-20260915-052](entries/MEM-20260915-052-the-transaction-was-the-connection-not-the-operation.md) | ACTIVE | repository | 0.93 | 2027-09-17 | PLAN-20260915-077 |
| [MEM-20260915-053](entries/MEM-20260915-053-a-declared-state-with-no-driver.md) | ACTIVE | repository | 0.92 | 2027-09-17 | PLAN-20260915-078 |
| [MEM-20260915-054](entries/MEM-20260915-054-retry-backoff-and-its-clock.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260915-079 |
| [MEM-20260915-055](entries/MEM-20260915-055-one-attempt-one-ledger.md) | ACTIVE | repository | 0.92 | 2027-09-17 | PLAN-20260915-080 |
| [MEM-20260915-056](entries/MEM-20260915-056-terminal-state-orphans-the-declared-retry.md) | ACTIVE | repository | 0.92 | 2027-09-18 | PLAN-20260915-081 |
| [MEM-20260915-057](entries/MEM-20260915-057-dispatcher-transition-first-and-visible.md) | ACTIVE | repository | 0.92 | 2027-09-18 | PLAN-20260915-082 |
| [MEM-20260915-058](entries/MEM-20260915-058-process-context-is-not-a-continuation.md) | ACTIVE | repository | 0.93 | 2027-09-18 | PLAN-20260915-083 |
| [MEM-20260917-059](entries/MEM-20260917-059-freeze-the-bytes-not-the-pointer.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-084 |
| [MEM-20260917-060](entries/MEM-20260917-060-parked-semantics-become-read-surface-facts.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-085 |
| [MEM-20260917-061](entries/MEM-20260917-061-declared-policy-needs-a-consumer-or-a-name.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-086 |
| [MEM-20260917-062](entries/MEM-20260917-062-convergence-facts-come-from-the-event-chain.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-087 |
| [MEM-20260917-063](entries/MEM-20260917-063-per-thread-connections-and-the-proxy-surface.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-088 |
| [MEM-20260917-064](entries/MEM-20260917-064-unified-dispatch-read-surface.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-089 |
| [MEM-20260917-065](entries/MEM-20260917-065-resume-failure-compensation.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-090 |
| [MEM-20260917-066](entries/MEM-20260917-066-security-audit-terminal-state.md) | ACTIVE | repository | 0.90 | 2027-09-17 | PLAN-20260917-091 |
| [MEM-20260918-067](entries/MEM-20260918-067-security-audit-residual-recheck.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-093 |
| [MEM-20260918-068](entries/MEM-20260918-068-approval-resume-compensation.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-094 |
| [MEM-20260918-069](entries/MEM-20260918-069-dead-declarations-get-removed-not-invented.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-095 |
| [MEM-20260918-070](entries/MEM-20260918-070-clock-injection-discipline.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-096 |
| [MEM-20260918-071](entries/MEM-20260918-071-batch-read-must-share-one-assembly.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-097 |
| [MEM-20260918-072](entries/MEM-20260918-072-rebuild-readiness-names-the-missing-fact.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-098 |
| [MEM-20260918-073](entries/MEM-20260918-073-single-statement-snapshot-for-composite-reads.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-100 |
| [MEM-20260918-074](entries/MEM-20260918-074-unconsumed-declaration-becomes-a-decidable-record.md) | ACTIVE | repository | 0.88 | 2027-09-18 | PLAN-20260918-101 |
| [MEM-20260918-075](entries/MEM-20260918-075-page-consumes-read-surface-parity-e2e.md) | ACTIVE | repository | 0.88 | 2027-09-18 | PLAN-20260918-102 |
| [MEM-20260918-076](entries/MEM-20260918-076-phase-facts-not-scheduler-products.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-103 |
| [MEM-20260918-077](entries/MEM-20260918-077-batch-cap-contract-and-weak-equivalence-axes.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-104 |
| [MEM-20260918-078](entries/MEM-20260918-078-compensation-failure-must-leave-a-trace.md) | ACTIVE | repository | 0.90 | 2027-09-18 | PLAN-20260918-105 |
| [MEM-20260919-079](entries/MEM-20260919-079-runtime-selection-vocabulary-and-honest-fingerprint.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-107 |
| [MEM-20260919-080](entries/MEM-20260919-080-egress-gate-chain-probe-is-the-egress-port.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-108 |
| [MEM-20260919-081](entries/MEM-20260919-081-real-runtime-offline-full-chain.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-109 |
| [MEM-20260919-082](entries/MEM-20260919-082-honest-substrate-disclosure.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-110 |
| [MEM-20260919-083](entries/MEM-20260919-083-tool-plane-boundary.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-111 |
| [MEM-20260919-084](entries/MEM-20260919-084-toolpack-capability-policy-pending.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-112 |
| [MEM-20260919-085](entries/MEM-20260919-085-goal-record-drift.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-113 |
| [MEM-20260919-086](entries/MEM-20260919-086-sdk-local-action-subclass-poisons-process.md) | ACTIVE | repository | 0.90 | 2027-09-19 | PLAN-20260919-113 |
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
