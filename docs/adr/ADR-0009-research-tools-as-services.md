# ADR-0009 — Prefer MCP/REST Services for Research-specific Tools

Status: Accepted

Research API/database tools change independently and need credentials/rate limits.

Default:

```text
Research Tool Service
→ MCP/REST
→ Agent Runtime
```

Native runtime tools are reserved for low-level workspace/execution integration.

This reduces Agent image churn and provider coupling.
