# ADR-0001 — Separate WorkflowEngine and AgentRuntime

Status: Accepted

Long-running product lifecycle and per-task agent reasoning are different concerns.

Decision:

```text
WorkflowEngine = lifecycle/durability
AgentRuntime   = intelligent session/tool loop
```

MVP LocalWorkflowEngine; Temporal later.
