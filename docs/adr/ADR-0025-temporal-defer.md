# ADR-0025 — Temporal Deferral for Durable Workflow (M14)

Status: Accepted
Date: 2026-08-27
Deciders: Research OS Architecture (M14)
Scope: `WorkflowEngine` Port durability — `docs/roadmap/MILESTONES.md` M14

## Context

M14 requires `PostgreSQL Canonical State + cross-process durable execution`
and a *Temporal ADOPT or REJECT with evidence* (explicit non-default).
PostgreSQL `PostgresWorkflowEngine` (WP1/WP2) already delivers at-least-once
+ idempotency, lease fencing (`lease_id` generation), transactional outbox,
and `recover_expired_leases` with `FOR UPDATE SKIP LOCKED` (Scenarios A–G).

## Decision

**DEFER Temporal for M14.** `WorkflowEngine` production adapter remains
`PostgresWorkflowEngine` (`adapters/postgres/workflow_engine.py`); SQLite
kept for offline tests. Temporal history is never canonical (ADR-0002).

## Qualification

16-question matrix in `docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md`:
PASS 12 / NEUTRAL 2 / FAIL 2. Gates Q1/Q2/Q9/Q11 PASS. Operational cost
(Q12 local dev, Q13 ops) outweighs M14 benefit; Temporal value aligns with
M16 Distributed Execution.

Pinned upstream inspected:
- `temporalio/temporal` Server `v1.28.1` (MIT) → commit `bc2433d037b163568ed4420f70023dde1a4ae5b5`
- `temporalio/sdk-python` `temporalio==1.13.0` (Apache-2.0) → sdist sha256
  `5a979eee5433da6ab5d8a2bcde25a1e7d454e91920acb0bf7ca93d415750828b`
- No bulk clone; spike in `research/temporal_spike/` (scratch)

> 注：Server commit 与 SDK sdist sha256 于 2026-08-28 复核并登记真实值
> （原为占位符 `a1b2c3…` / `sha256:…`），已同步 UPSTREAM_COMPONENTS
> （digest_status: VERIFIED）。DEFER 决策围绕 Q12/Q13 运维成本，不依赖
> pin 真实性；PyPI 当前最新 1.32.0，M16 重评须以当时最新版本重新评估。

## Consequences

- Keep `UPSTREAM_COMPONENTS.yaml` `temporal` as `PLANNED / DEFERRED` with
  `qualification_date: 2026-08-27` and controls.
- No `temporalio` import in `packages/domain` / `packages/application`
  (import-linter enforced).
- Future reconsideration at M16 (IG-3) if worker scale >50, cross-run sagas,
  or benchmark shows queue bottleneck — then fresh qualification + possible
  `ADR-0026-temporal-adopt.md`.

## Alternatives Considered

- ADOPT now: technically feasible (PASS gates) but ops burden premature.
- REJECT permanently: too strong; deferral allows M16 re-entry.

## References

- `docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md`
- `AGENTS.md` §6 (Canonical State), §12 (Upstream policy)
- `WORKFLOW_RELIABILITY.md`, `FAILURE_MODEL.md`
