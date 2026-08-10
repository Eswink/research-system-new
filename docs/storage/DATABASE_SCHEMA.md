# Database Schema Sketch v0.2.2


## Identity / Governance

```text
organizations
users
service_principals
project_memberships
access_grants
data_usage_policies
retention_policies
legal_holds
```

## Project / Run

```text
projects
research_runs
run_manifests
run_manifest_revisions
protocol_versions
compiled_run_plans
preflight_reports
phase_runs
```

## Role / Agent / Task

```text
role_definitions
team_templates
role_activation_policies
agent_specs
agent_runs
agent_sessions
research_tasks
task_contracts
acceptance_criteria
handoff_bundles
task_leases
```

## Model

```text
llm_endpoints
endpoint_health_samples
model_definitions
model_capability_observations
model_probe_results
model_profiles
model_profile_members
model_runtime_fingerprints
```

## Tool

```text
skills
capabilities
tool_specs
tool_provider_specs
tool_pack_manifests
tool_installations
tool_health_samples
capability_grants
tool_call_records
tool_result_records
```

## Workspace / Execution

```text
workspaces
workspace_leases
workspace_snapshots
execution_specs
execution_runs
compute_reservations
```

## Memory / Context

```text
context_snapshots
memory_records
memory_write_proposals
memory_snapshots
```

Vector table/index 为 derived projection。

## Evidence / Experiment

```text
source_records
claims
evidence
evidence_relations
experiment_plans
experiment_runs
metrics
artifacts
artifact_retention_policies
decisions
review_findings
deliverables
```

## Budget / Approval

```text
budget_policies
budget_reservations
usage_ledger
quota_policies
approval_requests
approval_decisions
interventions
```

## Reliability / Audit

```text
failure_records
retry_attempts
compensation_actions
idempotency_records
outbox_events
domain_events
consumer_offsets
```

## Key Constraints

- Agent explicit model FK ModelDefinition；
- Tool Set hash 写入 AgentSession；
- VERIFIED Claim 必须有 EvidenceRelation；
- task idempotency key 在 scope 内唯一；
- active lease 同 Task 唯一；
- Outbox/Event ID 唯一；
- Artifact digest/size 验证；
- Endpoint 不存明文 Secret。
