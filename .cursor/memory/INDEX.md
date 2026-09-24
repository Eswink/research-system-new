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
| [MEM-20260925-131](entries/MEM-20260925-131-default-gate-must-not-see-live-credentials.md) | ACTIVE | repository | 0.90 | 2027-03-25 | PLAN-20260925-161 |
| [MEM-20260925-130](entries/MEM-20260925-130-order-red-needs-a-frozen-input.md) | ACTIVE | repository | 0.90 | 2027-03-25 | PLAN-20260925-161 |
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
| [MEM-20260920-087](entries/MEM-20260920-087-bundle-scan-flags-test-net-as-old-version.md) | ACTIVE | repository | 0.95 | 2027-09-20 | PLAN-20260920-114 |
| [MEM-20260920-088](entries/MEM-20260920-088-new-render-branch-may-be-invisible-to-the-design-gate.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-115 |
| [MEM-20260920-089](entries/MEM-20260920-089-read-face-lies-need-wording-gates.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-116 |
| [MEM-20260920-090](entries/MEM-20260920-090-unknown-must-not-render-as-none.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-117 |
| [MEM-20260920-091](entries/MEM-20260920-091-verdict-enums-and-runtime-derived-guards.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-118 |
| [MEM-20260920-092](entries/MEM-20260920-092-new-judges-must-be-pressed-by-falsification.md) | ACTIVE | repository | 0.92 | 2027-09-20 | PLAN-20260920-119 |
| [MEM-20260920-093](entries/MEM-20260920-093-clean-checkout-seal-and-load-flake.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-120 |
| [MEM-20260920-094](entries/MEM-20260920-094-live-gate-credential-visibility-and-designed-failed.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-121 |
| [MEM-20260920-095](entries/MEM-20260920-095-credential-availability-breaks-hermetic-tests.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-121 |
| [MEM-20260920-096](entries/MEM-20260920-096-local-gate-reads-worktree-ci-reads-commit.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-122 |
| [MEM-20260920-097](entries/MEM-20260920-097-doc-value-judges-must-name-the-missing-label.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-123 |
| [MEM-20260920-098](entries/MEM-20260920-098-evidence-must-match-the-committed-shape.md) | ACTIVE | repository | 0.90 | 2027-09-20 | PLAN-20260920-124 |
| [MEM-20260920-099](entries/MEM-20260920-099-credential-resolver-construction-semantics.md) | ACTIVE | repository | 0.90 | 2027-09-21 | PLAN-20260920-125 |
| [MEM-20260921-100](entries/MEM-20260921-100-deliverable-name-declaration-and-gate.md) | ACTIVE | repository | 0.90 | 2027-09-21 | PLAN-20260921-127 |
| [MEM-20260921-101](entries/MEM-20260921-101-evidence-source-property-and-paired-landing.md) | ACTIVE | repository | 0.90 | 2027-09-21 | PLAN-20260921-128 |
| [MEM-20260921-102](entries/MEM-20260921-102-output-schema-registration-and-test-assembly.md) | ACTIVE | repository | 0.90 | 2027-09-21 | PLAN-20260921-129 |
| [MEM-20260921-103](entries/MEM-20260921-103-model-absence-taxonomy-and-false-green-judges.md) | ACTIVE | repository | 0.90 | 2027-09-21 | PLAN-20260921-130 |
| [MEM-20260922-104](entries/MEM-20260922-104-network-judge-traps-and-egress-sources.md) | ACTIVE | repository | 0.90 | 2027-09-22 | PLAN-20260922-131 |
| [MEM-20260922-105](entries/MEM-20260922-105-closeout-recheck-script-shape.md) | ACTIVE | repository | 0.90 | 2027-09-22 | PLAN-20260922-132 |
| [MEM-20260923-106](entries/MEM-20260923-106-run-chain-evidence-key-and-source-cap.md) | ACTIVE | repository | 0.90 | 2027-09-23 | PLAN-20260922-138 |
| [MEM-20260923-107](entries/MEM-20260923-107-fixture-failure-shape-is-a-contract.md) | ACTIVE | repository | 0.90 | 2027-09-23 | PLAN-20260922-135 |
| [MEM-20260923-108](entries/MEM-20260923-108-frozen-refs-on-both-failure-paths.md) | ACTIVE | repository | 0.90 | 2027-09-23 | PLAN-20260922-139 |
| [MEM-20260923-109](entries/MEM-20260923-109-freeze-gate-policy-allowance-channel.md) | ACTIVE | repository | 0.90 | 2027-03-23 | PLAN-20260923-140 |
| [MEM-20260923-110](entries/MEM-20260923-110-multi-provider-session-judge.md) | ACTIVE | repository | 0.90 | 2027-03-23 | PLAN-20260923-142 |
| [MEM-20260923-111](entries/MEM-20260923-111-experiment-evidence-traceability-judge-shape.md) | ACTIVE | repository | 0.92 | 2027-03-23 | PLAN-20260923-144 |
| [MEM-20260923-112](entries/MEM-20260923-112-verifier-token-drift-after-amend.md) | ACTIVE | repository | 0.94 | 2027-03-23 | PLAN-20260923-146 |
| [MEM-20260923-113](entries/MEM-20260923-113-live-page-equals-read-face-judge.md) | ACTIVE | repository | 0.90 | 2027-03-23 | PLAN-20260923-147 |
| [MEM-20260923-117](entries/MEM-20260923-117-live-page-equals-read-face-writing-traps.md) | ACTIVE | repository | 0.90 | 2027-03-23 | PLAN-20260923-151 |
| [MEM-20260923-118](entries/MEM-20260923-118-governance-token-ban-in-closed-records.md) | ACTIVE | repository | 0.95 | 2027-03-23 | PLAN-20260923-151 |
| [MEM-20260923-119](entries/MEM-20260923-119-live-read-face-ownership-and-fixture-anchoring.md) | ACTIVE | repository | 0.90 | 2027-03-23 | PLAN-20260923-152 |
| [MEM-20260923-120](entries/MEM-20260923-120-recheck-root-must-follow-cwd.md) | ACTIVE | repository | 0.95 | 2027-03-23 | PLAN-20260923-152 |
| [MEM-20260923-121](entries/MEM-20260923-121-criterion-disclosure-as-first-class-asset.md) | ACTIVE | repository | 0.92 | 2027-03-24 | PLAN-20260923-153 |
| [MEM-20260923-122](entries/MEM-20260923-122-windows-trailing-dot-link-false-green.md) | ACTIVE | repository | 0.95 | 2027-03-24 | PLAN-20260923-153 |
| [MEM-20260923-123](entries/MEM-20260923-123-why-not-must-be-checkable.md) | ACTIVE | repository | 0.90 | 2027-03-24 | PLAN-20260923-154 |
| [MEM-20260924-124](entries/MEM-20260924-124-multiple-fail-sources-enumerate-before-fixing.md) | ACTIVE | repository | 0.90 | 2027-03-24 | PLAN-20260924-155 |
| [MEM-20260924-125](entries/MEM-20260924-125-seam-empty-is-not-assembly-missing.md) | ACTIVE | repository | 0.90 | 2027-03-24 | PLAN-20260924-156 |
| [MEM-20260924-126](entries/MEM-20260924-126-reachable-surface-vs-declaration-surface.md) | ACTIVE | repository | 0.90 | 2027-03-24 | PLAN-20260924-157 |
| [MEM-20260924-127](entries/MEM-20260924-127-press-restore-needs-byte-check.md) | ACTIVE | repository | 0.95 | 2027-03-24 | PLAN-20260924-157 |
| [MEM-20260924-128](entries/MEM-20260924-128-run-chain-declaration-must-cover-plan-wide-tool-set.md) | ACTIVE | repository | 0.95 | 2027-03-24 | PLAN-20260924-160 |
| [MEM-20260924-129](entries/MEM-20260924-129-press-scripts-need-an-arming-guard.md) | ACTIVE | repository | 0.90 | 2027-03-24 | PLAN-20260924-160 |
| [MEM-20260923-116](entries/MEM-20260923-116-local-m0-green-recipe.md) | ACTIVE | repository | 0.88 | 2027-03-23 | PLAN-20260923-151 |
| [MEM-20260923-115](entries/MEM-20260923-115-convergence-proof-structural-vs-semantic.md) | ACTIVE | repository | 0.90 | 2027-03-23 | PLAN-20260923-150 |
| [MEM-20260923-114](entries/MEM-20260923-114-citations-land-with-their-artifacts.md) | ACTIVE | repository | 0.93 | 2027-03-23 | PLAN-20260923-147 |
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
