# Open-source Reuse Audit v0.2.2

Audit date: 2026-08-10.

## Primary Runtime — OpenHands Software Agent SDK

Decision:

```text
DIRECT DEPENDENCY + RESEARCH OS ADAPTER
```

Reuse:

- Agent loop;
- Conversation/persistence/fork;
- typed tools/events;
- MCP;
- context condenser;
- security analyzer/confirmation;
- stuck detector;
- Local/Docker/Remote/Apptainer workspace patterns.

Research OS retains:

- Domain/Protocol/Task/Role;
- user Relay/Model semantics;
- Policy/Budget/Memory;
- Evidence/Claim;
- Evaluation/Audit;
- canonical persistence.

Important adapter constraints:

- direct tool execution must be policy wrapped;
- resume must enforce our Manifest;
- Tool Set freezes per Session;
- plugins pin immutable revision/digest;
- Secret Registry is not canonical vault.

## Workflow — Temporal

Decision:

```text
LATER PRODUCTION ADAPTER
```

Use for durable long-running orchestration; keep LLM/Tool/Sandbox work in Activities/external workers and maintain idempotency.

## Policy — OPA

Decision:

```text
OPTIONAL PRODUCTION ADAPTER
```

MVP NativePolicyEvaluator; OPA later for centralized policy-as-code and decision logs.

## Observability — OpenTelemetry

Decision:

```text
STANDARD TELEMETRY FOUNDATION
```

Use semantic conventions where stable/applicable; GenAI content capture off by default due sensitive/PII risk.

## Tool Integration — MCP

Decision:

```text
PRIMARY RESEARCH TOOL PROTOCOL + NATIVE/REST FALLBACK
```

Use current transport/auth guidance. Do not treat Roots as access control.

## Execution

### OpenHands Docker/Remote/Apptainer

Primary workspace options.

### SWE-ReX

Optional adapter for parallel/local/remote shell execution.

### E2B or other microVM providers

Optional hardened managed backend; no core dependency.

## Product/Research Donors

- Cline Kanban: task/worktree UX;
- Claw AI Lab: research dashboard/artifacts;
- AutoResearchClaw: research workflow/failure patterns;
- PaperQA/STORM/scientific skills: future research Tool/Skill packs.

## Fork Policy

```text
dependency
→ adapter
→ service/plugin
→ compatibility shim
→ fork (last resort)
```
