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
- `temporalio/temporal` Server `v1.28.1` (MIT)
- `temporalio/sdk-python` `temporalio==1.13.0` (Apache-2.0)
- No bulk clone; spike in `research/temporal_spike/` (scratch)

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
