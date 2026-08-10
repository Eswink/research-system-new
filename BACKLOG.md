# Engineering Backlog v0.2.2

## P0 — Validation & Domain

- [ ] bootstrap validation script in CI
- [ ] Domain entities/enums/invariants
- [ ] JSON/YAML schema loaders
- [ ] Run/Phase/Task state machines
- [ ] RunManifest + Revision + digest
- [ ] append-only Usage Ledger
- [ ] Artifact digest/verification

## P0 — Model Relay

- [ ] LLMEndpoint CRUD + encrypted credential ref
- [ ] manual ModelDefinition
- [ ] endpoint test
- [ ] optional model discovery
- [ ] capability probe
- [ ] ModelEligibilityPolicy
- [ ] endpoint health/circuit breaker
- [ ] ModelRuntimeFingerprint
- [ ] fallback audit
- [ ] secret redaction

## P0 — Role / Team / Task

- [ ] 26 Role fixtures
- [ ] Lean/Standard/Rigorous templates
- [ ] Role activation/collapsing
- [ ] per-Agent model binding
- [ ] heterogeneous reviewer constraints
- [ ] TaskContract / AcceptanceCriteria
- [ ] HandoffBundle

## P0 — Protocol / Preflight

- [ ] Protocol compiler
- [ ] DAG validation
- [ ] Role/model/tool/workspace resolution
- [ ] BudgetReservation
- [ ] Policy preflight
- [ ] CompiledRunPlan / PreflightReport
- [ ] dry-run projection

## P0 — Reliable Runtime

- [ ] WorkflowEngine port + Fake
- [ ] PostgreSQL task queue
- [ ] TaskLease/heartbeat
- [ ] IdempotencyRecord
- [ ] Transactional Outbox
- [ ] retry/backoff/circuit breaker
- [ ] cancellation/compensation
- [ ] duplicate delivery tests

## P0 — OpenHands Adapter

- [ ] relay mapping
- [ ] Agent/Conversation lifecycle
- [ ] event normalization
- [ ] frozen Tool Set
- [ ] PolicyWrapped direct tool execution
- [ ] DockerWorkspace
- [ ] stuck mapping
- [ ] resume Manifest check
- [ ] conversation fork mapping
- [ ] plugin pin/digest

## P1 — Tool Plane

- [ ] ToolCatalog/Resolver
- [ ] Tool effect/risk classes
- [ ] MCP Streamable HTTP + stdio
- [ ] ToolPack manifest/install/update/revoke
- [ ] Tool health/circuit breaker
- [ ] Tool credential separation
- [ ] large result artifact indirection

## P1 — Memory / Evidence

- [ ] SourceRecord
- [ ] MemoryWriteProposal gate
- [ ] Memory lifecycle/delete
- [ ] derived vector index
- [ ] Claim/Evidence relations
- [ ] contradiction handling
- [ ] negative result memory

## P1 — Experiment / Artifact

- [ ] ExecutionBackend port
- [ ] WorkspaceLease/worktree
- [ ] ExperimentPlan/Run/Metric
- [ ] content-addressed Artifact Store
- [ ] retention/export bundle
- [ ] ReproducibilityAudit

## P1 — Evaluation

- [ ] Eval Harness modes
- [ ] deterministic gates
- [ ] reviewer panel
- [ ] human calibration samples
- [ ] canary/regression dashboard

## P2 — Product UI

- [ ] first-run relay wizard
- [ ] models/probe page
- [ ] team/agent model assignment
- [ ] protocol/preflight dry run
- [ ] task/run timeline
- [ ] approvals/interventions
- [ ] workspace diff
- [ ] evidence/claim map
- [ ] budget/usage
- [ ] audit/export

## P2 — Production

- [ ] Temporal adapter
- [ ] OPA adapter
- [ ] central Secret Manager
- [ ] remote/hardened sandbox
- [ ] OTel collector/dashboards
- [ ] backup/restore
- [ ] RBAC/organization scope
