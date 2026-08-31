# M16 Remote Execution Qualification Report

- Date: 2026-08-31
- Scope: `docs/roadmap/MILESTONES.md` M16 §SWE-ReX / equivalent qualification (16 questions, M5R/M14 shape)
- Primary candidate: `SWE-agent/SWE-ReX` (remote sandboxed execution for agents)
- Baselines compared: (A) Research OS native HTTP worker gateway (built in M16 WP1–WP3); (B) Docker-over-TCP / `docker context`
- Secondary re-check: Temporal M16 re-entry conditions (per ADR-0025 / M14 report)
- Method: pinned revision via `git ls-remote` + PyPI JSON API (real, 2026-08-31), README/API-model review, import-linter boundary reasoning, contract-fit analysis against `ExecutionBackend` / `WorkspaceBackend` / `WorkflowEngine` Ports
- Inputs: `WORKSPACE_RUNTIME.md`, `WORKFLOW_RELIABILITY.md`, `PORTS.md`, `ADR-0027`, `M14_TEMPORAL_QUALIFICATION.md`, M16 plan §13

## Upstream Source (measured 2026-08-31)

| Field | Value |
|---|---|
| Repository | `https://github.com/SWE-agent/SWE-ReX` |
| Latest tag | `v1.4.0` → commit `f802b3e14d82aa4c13291d2fda5bd4fd48f36f91` (`git ls-remote --tags` measured) |
| PyPI | `swe-rex==1.4.0`, sdist `swe_rex-1.4.0.tar.gz` sha256 `14f8a24c49a63f9e251340b1109ac75a4aacbaece410f8599209de9bfca843c0` (PyPI JSON API measured) |
| License | MIT (PyPI classifier `License :: OSI Approved :: MIT License`; repo `LICENSE` not at the probed path — classifier is the recorded evidence) |
| Requires Python | `>=3.10` (compatible with Research OS 3.12) |
| Self-description | "Sandboxed code execution for AI agents, locally or on the cloud"; "a runtime interface for interacting with sandboxed shell environments, allowing you to let your agent run *any command* on *any environment*" |
| Deployment backends | local, Docker, SSH/AWS, Modal, Daytona (per README) |

> No bulk clone into the main tree; no `swe-rex` dependency added to `uv.lock`. This is a qualification, not an adoption.

## API / Contract Model (the decisive axis)

SWE-ReX is built around **stateful, interactive shell sessions**: `BashSession` objects that stay alive, accept arbitrary commands, and where SWE-ReX "recognize[s] when commands are finished, extract[s] the output and exit code" by prompt/exit-marker detection. It supports multiple concurrent sessions per environment and interactive tools (`ipython`, `gdb`).

Research OS `ExecutionBackend` is a **one-shot batch contract**: `execute(ExecutionSpec, timeout_seconds, cancelled) -> ExecutionRun`, where the run is a single command, outputs are captured to digest-verified `stdout.log`/`stderr.log` in a content-addressed workspace, and the whole thing is normalized to an `ExecutionRun` with `Digest`-typed stdout/stderr. There is no persistent interactive session in the Research OS execution model (M9/M12).

## 16-Question Decision Matrix (SWE-ReX)

| # | Question | Evidence method | Result | Evidence |
|---|---|---|---|---|
| 1 | Can it sit behind `ExecutionBackend` Port without domain import? | API-model reasoning | **NEUTRAL** | An adapter could map `execute`→create session+run command+extract output, but the session lifecycle (create/teardown) has no home in the one-shot Port; adapter would own state the Port doesn't model |
| 2 | Does business truth stay in PostgreSQL? | Architecture reasoning | **PASS** | SWE-ReX owns no Research OS domain state; it is an execution transport only |
| 3 | Isolation model matches M9/M12 sandbox posture? | README + Docker backend | **NEUTRAL** | Docker backend exists, but SWE-ReX's default isolation is its own container/session config, not Research OS's `host_config` (NetworkMode=none, CapDrop ALL, readonly rootfs, PidsLimit) which M9 qualified and M16 preserves |
| 4 | Remote execution model | README | **PASS** | Explicitly remote-first (SSH/Modal/Daytona/Docker) |
| 5 | Filesystem / workspace model | API review | **FAIL** | SWE-ReX manipulates files inside its own session; Research OS needs immutable snapshot-digest input bundles + content-addressed output bundles via ArtifactStore (M16 §10). No digest-verified bundle import/export primitive |
| 6 | Cancellation semantics | API review | **NEUTRAL** | Sessions can be killed, but the one-shot `cancelled` cooperative callback + `ExecutionStatus.CANCELLED` mapping is not native |
| 7 | Timeout semantics | API review | **NEUTRAL** | Command timeouts exist per-session; mapping to `ExecutionStatus.TIMED_OUT` + container kill is adapter work |
| 8 | Artifact transfer (digest-verified) | API review | **FAIL** | No content-addressed artifact plane; Research OS output integrity is enforced server-side by `ArtifactStore.put/verify` (M16 §10) |
| 9 | Resource / network control | Docker backend | **NEUTRAL** | Some control, but not the Research OS `resolve_resource_profile` + `host_config` default-deny surface |
| 10 | Security assumptions vs untrusted-worker model | Threat reasoning | **FAIL** | SWE-ReX assumes a trusted controller driving a remote runtime for *its own* agent; Research OS treats the *worker* as untrusted and the Control Plane as the sole authority (ADR-0027). SWE-ReX has no worker-authentication / fencing concept |
| 11 | Fencing / stale-result rejection | API review | **FAIL** | No `(task_id, lease_id, fence)` concept; Research OS rejects stale worker results at the gateway (M16 §8, scenario C) |
| 12 | Local dev / testing complexity | Spike reasoning | **FAIL** | Adds a runtime + its deployment backends to the dev loop; the native HTTP worker reuses already-pinned fastapi/uvicorn/httpx with zero new upstream |
| 13 | Deployment / operating complexity | README | **FAIL** | SWE-ReX server/runtime + backend credentials (Modal/Daytona/AWS) is a second execution control plane to operate |
| 14 | Licensing / upstream stability | PyPI + tags | **PASS** | MIT, active releases (1.4.0, 2026), monthly-ish cadence |
| 15 | Domain pollution risk | Import reasoning | **PASS** | Could be confined to an adapter; no forced domain import |
| 16 | Fit to M16 contract vs cost | Overall | **FAIL** | Interactive-session model is structurally mismatched to the one-shot `ExecutionSpec→ExecutionRun` + digest-bundle + fencing contract; adaptation cost (Q5/Q8/Q10/Q11) exceeds benefit given the native worker already satisfies the DoD |

Scoring: **PASS 4 / NEUTRAL 5 / FAIL 7**. Gates that matter most for M16 (Q5 workspace digest, Q8 artifact integrity, Q10 untrusted-worker auth, Q11 fencing) are FAIL.

## Baselines Compared

- **(A) Native HTTP worker gateway (built in M16 WP1–WP3)** — `ExecutionBackend`/`WorkspaceBackend`/`WorkflowEngine` contracts satisfied directly; worker untrusted + Control-Plane-exclusive authorization; session-token auth with generation revocation; `(task_id, lease_id, fence)` fencing; content-addressed bundle transfer with dual digest verification; zero new upstream (fastapi/uvicorn/httpx already ADOPTED). **Matches the M16 DoD.**
- **(B) Docker-over-TCP / `docker context`** — exposes the Docker daemon API over TCP to a remote host. Reuses `DockerExecutionBackend` unchanged, but the remote Docker endpoint is a *trusted* daemon: no worker authentication, no fencing, no capability/partition scheduling, no bundle integrity plane, and it hands a raw container-creation API to the network. It is a deployment shortcut, not a distributed execution plane, and it violates the untrusted-worker boundary (ADR-0027 §1). Kept as a documented fallback for single-operator LAN use, not the M16 deliverable.

## Temporal M16 Re-entry Re-check (ADR-0025 / M14 Q16)

M14 deferred Temporal pending M16 re-entry conditions: worker scale > 50, cross-run saga, or benchmark showing the Postgres queue is a bottleneck.

- **Worker scale > 50**: M16 delivers multi-worker registration/heartbeat/partition scheduling on the single Postgres queue with `FOR UPDATE SKIP LOCKED`. No evidence of >50-worker scale in the M16 scope or tests; the non-goals explicitly exclude autoscaling. **Not triggered.**
- **Cross-run saga**: M16 §9 keeps run-internal phase/session execution sequential; cross-machine parallelism comes from concurrent independent runs/jobs, not distributed sagas. **Not triggered.**
- **p95 claim latency > 200ms / queue bottleneck**: the WP4 distributed E2E exercises concurrent multi-process claim on real PostgreSQL; no benchmark shows the single-queue kernel as a bottleneck at M16 scale. **Not triggered** (and must be re-measured if scale grows).

Conclusion: **Temporal re-entry conditions are NOT triggered by M16.** The Postgres queue/lease/fence kernel remains sufficient; no fresh Temporal qualification is warranted this milestone.

## Decision: REJECT SWE-ReX for the M16 execution plane; keep native HTTP worker

SWE-ReX is a capable, actively-maintained MIT-licensed interactive-shell runtime, but its core model (stateful shell sessions, its own file/artifact handling, trusted-controller assumption) is structurally mismatched to Research OS's one-shot `ExecutionSpec→ExecutionRun` batch contract with digest-verified bundles, untrusted-worker authentication, and lease fencing. Adopting it would mean building the M16 security/fencing/integrity guarantees *on top of* an abstraction that does not model them, at higher cost than the native gateway that already satisfies the DoD with zero new upstream.

This is a REJECT with evidence, not a failure of M16: M16's deliverable is the remote-execution capability + the upstream decision evidence, both of which the native worker plane provides.

### Reconsideration conditions (for a future milestone)

Re-open SWE-ReX qualification only if a concrete need arises for **persistent interactive agent shell sessions** (e.g., an M17+ interactive debugging/HPC workflow) that the one-shot `ExecutionBackend` cannot express — and even then, evaluate it strictly behind the `ExecutionBackend` adapter boundary with upstream types kept out of Domain/Application and its persistence never canonical.

## Consequences

- `UPSTREAM_COMPONENTS.yaml`: `swe_rex` → `adoption_status: PLANNED`, `decision_status: REJECTED`, with this report + measured pins. No dependency added.
- No `swe-rex` import anywhere; `.importlinter.worker` (WP4) confines `adapters.worker`/`services.worker`.
- Temporal stays DEFERRED (ADR-0025); M16 re-entry conditions re-checked and not triggered.

## References

- `docs/adr/ADR-0027-distributed-execution-plane.md`
- `docs/references/upstream/M14_TEMPORAL_QUALIFICATION.md` (16Q shape + Temporal re-entry)
- `docs/architecture/WORKSPACE_RUNTIME.md`, `WORKFLOW_RELIABILITY.md`, `PORTS.md`
- `.cursor/plans/m16_分布式执行_1657b1d6.plan.md` §13
