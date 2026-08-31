# ADR-0027 — Distributed Execution Plane (M16)

Status: Accepted
Date: 2026-08-31
Deciders: Research OS Architecture (M16)
Scope: Distributed Execution Plane — `docs/roadmap/MILESTONES.md` M16;
`WorkflowEngine` claim-next extension, `WorkerRegistry` Port, worker gateway,
remote `ExecutionBackend`

## Context

M14 delivered a durable PostgreSQL queue/lease/fencing kernel
(`tasks`/`leases`/`lease_id` rotation/`recover_expired_leases` with
`FOR UPDATE SKIP LOCKED`). M16 requires multi-worker registration/heartbeat/
drain, capability/partition scheduling, remote sandbox execution, and
cross-machine failover evidence — without eroding the M14 invariants
(AGENTS.md §6 Canonical State, §7 at-least-once + idempotency + fencing).

Two forces constrain the design:

1. Remote hosts must execute commands, but a remote host is not trusted with
   business truth, credentials beyond job scope, or the database.
2. The queue/lease/artifact authorities already exist in PostgreSQL; a second
   implementation (new broker, worker-local state, direct DB access from
   workers) would create split-brain risk that M14 deliberately avoided.

## Decision

1. **Workers are untrusted execution parties.** A worker process may only:
   register, heartbeat, claim work through the authenticated worker gateway,
   execute in its local sandbox, and submit results/digests. It never holds
   PostgreSQL credentials, never reads back its own claims as truth, and its
   self-reported timestamps/digests are always re-verified server-side.
2. **Control Plane holds exclusive authorization.** All authoritative writes
   (lease grant, completion acceptance, artifact publication, final status,
   retry) happen in Control Plane PG transactions gated on
   `(task_id, lease_id, fence)`. `tasks.fence_seq` is a monotonic generation
   counter added on top of the existing `lease_id` rotation — auditable, not a
   second mechanism.
3. **HTTP/JSON worker gateway** (`services/api/worker_gateway/`, independent
   ASGI app, `/worker/v1`) reusing already-pinned `fastapi`/`uvicorn`/`httpx`.
   Rejected alternatives: workers connecting directly to PostgreSQL (hands the
   whole canonical store + secrets to every remote host); gRPC/Redis/NATS/
   RabbitMQ (new pinned upstreams + de-facto second queue). Auth: pre-shared
   enrollment secret via `CredentialResolver` (new WORKER credential domain,
   isolated from TOOL/MODEL), `hmac.compare_digest`; 256-bit session tokens
   stored only as sha256 with monotonic `registration_generation` replay
   revocation; non-loopback binding without TLS refuses to start.
4. **No second queue / lease / artifact truth.** Execution jobs reuse `tasks`
   with `kind='EXECUTION'` (default `AGENT_SESSION` keeps existing tasks
   unaffected) plus an `execution_jobs(task_id PK)` typed payload projection —
   same pattern as `experiment_plans`. `leases` remains the single ownership
   authority; `partition` (sha256(run_id) mod 16) is only a claim filter, so
   double ownership is structurally impossible. Large results move as
   content-addressed ArtifactStore refs, never RPC bodies.
5. **Remote execution stays behind the existing `ExecutionBackend` Port.**
   `RemoteExecutionBackend` (submit job → poll with deadline → verify outputs →
   normalize `ExecutionRun`) and `DockerExecutionBackend` are two adapters;
   Application has zero local/remote branching. `WorkspaceBackend` gains
   `export_bundle`/`import_bundle` with dual digest verification and
   symlink/traversal rejection.

## Consequences

- Migration `008_worker_plane.sql` is fully additive (`workers` table;
  `tasks.kind/partition/required_capability/fence_seq`; `leases.worker_id/
  fence`; `execution_jobs`).
- Lease expiry comparison moves to a database-side time source abstraction
  (production `now()`, injectable test clock); worker clock skew cannot affect
  expiry/fence/ordering.
- `WorkerRegistry` becomes a new Port with Fake + PG implementations under the
  existing contract-suite registry; `.importlinter.worker` gates
  `adapters.worker` + `services.worker`, and Domain/Application stay free of
  worker/RPC types.
- M12 reference workflow critical path is untouched: agent-session tasks keep
  the default kind and are never claimable by remote workers.
- SWE-ReX (or equivalent) is qualified, not presumed: see
  `docs/references/upstream/M16_REMOTE_EXECUTION_QUALIFICATION.md` for the
  ADOPT/REJECT/DEFER verdict; Temporal M16 re-entry conditions are re-checked
  there per ADR-0025.

## Alternatives Considered

- **Worker → direct PostgreSQL**: zero new surface, but violates the
  untrusted-executor boundary (whole-DB authority per remote host). Rejected.
- **Message broker (Redis/NATS/RabbitMQ) or gRPC**: new pinned upstreams and a
  de-facto second queue competing with `tasks`/`leases`. Rejected for M16.
- **Adopt SWE-ReX as the execution plane**: interactive-shell session model
  vs. Research OS one-shot `ExecutionSpec → ExecutionRun` batch contract;
  structural mismatch pending spike evidence. Deferred to qualification.

## References

- `docs/roadmap/MILESTONES.md` M16; `AGENTS.md` §6, §7, §9
- `ADR-0025-temporal-defer.md` (M16 re-entry conditions)
- `docs/architecture/WORKFLOW_RELIABILITY.md`, `PORTS.md`, `THREAT_MODEL.md`
- `.cursor/plans/m16_分布式执行_1657b1d6.plan.md`
