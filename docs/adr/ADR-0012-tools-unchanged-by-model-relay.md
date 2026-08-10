# ADR-0012 — LLM Relay Does Not Change Tool/Workspace Architecture

Status: Accepted
Date: 2026-08-10

## Decision

用户自定义中转站仅改变 Model Integration。

以下保持独立且不变：

```text
Tool/Skill/Capability
MCP/REST providers
Workspace
Sandbox
Evidence
Protocol
Evaluation
```

## Reason

LLM endpoint 与 Research Tool endpoint 属于不同信任域、凭据域和生命周期。
