# ADR-0004 — Adopt OpenHands SDK Behind an Adapter

Status: Accepted
Updated: 2026-08-10 for v0.4.0

## Decision

使用 OpenHands Software Agent SDK 作为 MVP 通用 Agent Runtime，不 fork。

```text
Research OS AgentRuntime Port
→ OpenHandsRuntimeAdapter
→ OpenHands Native Agent
```

## Reuse

- Agent loop；
- Conversation；
- Tools/MCP；
- Workspace；
- Condenser；
- Security/Stuck/Fork 基础能力。

## Research OS Boundaries

- 用户 Relay/Model Domain；
- Protocol/Task/Role；
- Policy/Budget/Memory；
- Evidence/Evaluation；
- canonical persistence。

## Guardrails

- Direct `execute_tool()` 必须 Policy Wrapper；
- resume 必须 Manifest compatibility；
- Session Tool Set 冻结；
- Plugin revision/digest pin。

## Exit

其他 Runtime 可实现相同 Port，不改变 Domain。
