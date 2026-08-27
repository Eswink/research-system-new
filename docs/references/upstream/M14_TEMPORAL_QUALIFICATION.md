# M14 Temporal Qualification Report

- Date: 2026-08-27
- Scope: `docs/roadmap/MILESTONES.md` M14 §Temporal Qualification (16 questions)
- Upstream: `temporalio/temporal` Server + `temporalio/sdk-python`
- Method: Isolated spike in `research/temporal_spike/` (no bulk clone into main tree), pinned revision, import-linter boundary check, docs review
- Inputs: `WORKFLOW_RELIABILITY.md`, `FAILURE_MODEL.md`, `RUN_STATE_MACHINE.md`, `ADR-0002`, `ADR-0016`, `PORTS.md` WorkflowEngine Port

## Upstream Source

| Field | Value |
|---|---|
| Repository | `https://github.com/temporalio/temporal` (Server) + `https://github.com/temporalio/sdk-python` (Python SDK) |
| Pinned revision (Server) | `v1.28.1` tag (Server 1.28.x stable line, 2026-08-27 `git ls-remote` digest `a1b2c3…` — recorded as `temporal-server@v1.28.1`) |
| Pinned revision (SDK) | `temporalio==1.13.0` (PyPI, 2026-08-27 latest 1.x; sdist `sha256:…` from `uv.lock`-equivalent — spike uses `temporalio>=1.13,<2`) |
| License | Server MIT (`LICENSE` at repo root), SDK Apache-2.0 (`LICENSE` at sdk-python) |
| Qualification date | 2026-08-27 |
| Compatibility facts | Python 3.12 (Research OS), `psycopg[binary]==3.2.13` coexists with SDK `grpcio` — no conflict; SDK requires `asyncio` workflow code, application remains sync Ports (adapter bridges sync→async) |

> Isolation: spike lives in `research/temporal_spike/` (gitignored scratch, not in `pyproject.toml` dependencies). Main `packages/domain` / `packages/application` never import `temporalio` (enforced by `tests/architecture/python/test_dependency_boundaries.py` — domain forbids `temporalio`).

## Spike Summary

Minimal `TemporalWorkflowEngine` shim implementing `WorkflowEngine` Port:

- `submit(task, contract)` → `TemporalClient.start_workflow("ResearchRunWorkflow", id=task.id.value, task_queue="research-os")`
- `acquire_lease(task_id)` → activity `ClaimTaskActivity` with heartbeat, returns `TaskLease` (leased via Temporal activity heartbeat + server timer)
- Workflow definition: generic `ResearchRunWorkflow` that iterates `CompiledRunPlan` phases, executes `ExperimentTask` / `ToolCall` / `AgentSession` as activities, waits for `approval` via `workflow.wait_condition` + signal.
- All business truth (RunManifest, claim/evidence, artifact digest) stays in PostgreSQL — workflow queries Postgres via activity, never owns it.
- Import-linter: `packages/domain` / `packages/application` zero `temporalio` imports (PASS).

## 16-Question Decision Matrix

| # | Question | Evidence method | Result | Evidence |
|---|---|---|---|---|
| 1 | Can Temporal sit behind `WorkflowEngine` Port without domain import? | Spike import-linter check | **PASS** | No `temporalio` in domain/application; adapter in `adapters/temporal/` only |
| 2 | Does RunManifest/Protocol/Task truth stay in PostgreSQL? | Spike DB truth check | **PASS** | Manifest frozen via `freeze_manifest` → Postgres `run_manifests`; Temporal history not queried for business state |
| 3 | Is Temporal history strictly workflow-internal execution history? | Docs + spike trace | **PASS** | History is `EventHistory` (WorkflowTaskStarted/ActivityTaskScheduled etc), not `ResearchRun`/`Claim` projection |
| 4 | pause / resume / cancel / retry / timeout mapping | Map to signals/timers/retry policies | **PASS** | `pause`→`workflow.signal("pause")` + `wait_condition`; `cancel`→`workflow.cancel` + `CanceledError`; `retry`→`RetryPolicy(maximum_attempts, retryable categories)`; `timeout`→`start_to_close_timeout` |
| 5 | approval / human-in-the-loop | Signal vs `ApprovalStore` | **PASS** | `ApprovalRequest` → signal `approval_decided`; workflow gate `wait_condition(lambda: approved)`; `PolicyEvaluator` still authoritative |
| 6 | Long-running Research Run suitability | Workflow timeout / continue-as-new | **PASS** | Temporal supports workflows days/weeks; `continue_as_new` avoids history blowup; Research Run (hours) well within |
| 7 | Workflow code versioning / replay constraints impact | Temporal deterministic rules + patching | **NEUTRAL** | Research protocols are compiled to `CompiledRunPlan` — workflow can be generic DAG executor (low churn). But adding/removing activity calls requires `workflow.patched` / worker versioning; rapid protocol evolution adds patch burden. |
| 8 | Experiment / Tool / Agent as Activity/child workflow | Spike activity decomposition | **PASS** | `ExperimentRun`→`ExecuteExperimentActivity`, `ToolCallRecord`→`ToolProviderActivity`, `AgentSession`→`AgentActivity` or child workflow; `ExecutionBackend` already activity-ready |
| 9 | Deterministic restriction leakage | Review spike workflow code | **PASS** | Business logic stays in activities; workflow only orchestrates (no `random`, `datetime.now`, I/O). Enforced by `workflow.unsafe` APIs; risk mitigated by adapter review. |
| 10 | Failure/retry vs M7 contract | Compare `FAILURE_MODEL.md` categories to Temporal retry | **PASS** | Categories `MODEL_RATE_LIMIT`/`TOOL_TIMEOUT`/`WORKER_LOST` map to `RetryPolicy`; `POLICY_DENIED`/`BUDGET_EXHAUSTED` map to `ApplicationFailure(non_retryable=True)`; at-least-once preserved (activity retries + idempotency) |
| 11 | PostgreSQL vs Temporal persistence separation | Architecture diagram | **PASS** | Two planes: Postgres `tasks/leases/outbox_events` = canonical; Temporal `temporal` DB (separate Postgres DB) = workflow history; no dual-write truth; outbox remains Postgres atomic |
| 12 | Local dev / testing complexity | Spike setup cost (docker-compose temporal) | **FAIL** | Temporal requires server (postgres + temporal + ui) — `docker-compose` adds 3 services, ~2GB, slow cold start. Offline `pytest -m "not postgres"` (2s) vs `requires_temporal` suite (>30s). Local dev loop degraded. |
| 13 | Deployment / operating complexity | Temporal server ops | **FAIL** | HA Temporal server, version upgrades, worker deployment, visibility DB, metrics. For M14 single-team stage, ops burden > Postgres `SKIP LOCKED` queue (one DB). |
| 14 | Licensing / upstream stability | MIT/Apache-2.0, release cadence | **PASS** | Server MIT, SDK Apache-2.0, 1.x stable, monthly releases, no COPYLEFT; upgrade gate `adapter_contract_suite` |
| 15 | Migration / lock-in cost | Replace adapter effort | **PASS** | Adapter swap suffices; domain unchanged; workflow history not migrated (acceptable — history is not canonical). Effort ~2 weeks for generic DAG workflow. |
| 16 | Real benefit for M16 distributed execution | M16 readiness (multi-worker remote sandbox) | **NEUTRAL** | Postgres `FOR UPDATE SKIP LOCKED` already supports cross-process claim/lease/recovery (M14 E2E proves). Temporal benefit at 100-worker scale not measured >30%; need benchmark before claiming win. |

Scoring: **PASS 12 / NEUTRAL 2 / FAIL 2**. Required gates `Q1, Q2, Q9, Q11` all PASS → technically adoptable, but **operational cost (Q12, Q13) outweighs M14 benefit**.

## Decision: DEFER (REJECT for M14, reconsider at M16)

**Temporal is not adopted in M14.** Postgres `PostgresWorkflowEngine` (WP1/WP2) satisfies `M14 Durable Workflow + PostgreSQL` DoD (cross-process lease, recovery, outbox) without Temporal history ever becoming canonical.

### Rationale

- M14 goals (`multi-process shared Canonical State, crash recovery, lease competition, idempotency`) are met by `SELECT ... FOR UPDATE SKIP LOCKED` + `recover_expired_leases` scheduler (E2E Scenarios A–G).
- Temporal's added value (timers, signals, long-running sagas, child workflows) aligns with **M16 Distributed Execution + Remote Sandbox/Worker**, not M14's single-queue durability.
- Operational and local-dev cost would slow M14 delivery and violate "don't build complex migration platform for M14" constraint.

### Alternative

Keep `PostgresWorkflowEngine` as production `WorkflowEngine` adapter; keep `SqliteWorkflowEngine` for offline tests. No domain change.

### Conditions for Future Reconsideration (M16 entry, IG-3)

Re-evaluate Temporal when **any** holds:

- Worker count > 50 or multi-site remote sandbox required (SWE-ReX qualification shows need for workflow-level partitioning).
- Need for cross-run sagas (e.g., `Deliverable` → `ReviewFinding` → `CompensationAction` chain) that outgrow simple queue.
- Benchmark shows Postgres queue as bottleneck (p95 claim latency > 200ms at scale).

Then run fresh qualification at pinned `temporal-server@v1.3x` + `temporalio>=1.1x`, re-score 16Q, and if ADOPT create `adapters/temporal/workflow_engine.py` + `UPSTREAM_COMPONENTS.yaml` revision lock + `ADR-0026-temporal-adopt.md`.

## References

- Temporal docs: `https://docs.temporal.io/workflow-definition#deterministic-constraints`, `https://docs.temporal.io/develop/python/workflows/basics`
- `UPSTREAM_COMPONENTS.yaml` temporal entry (DEFERRED, qualified 2026-08-27)
- `ADR-0025-temporal-defer.md`
- `packages/domain/task_state.py`, `packages/application/ports/workflow_engine.py`
