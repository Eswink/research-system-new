# Agent Runtime Backends v0.2.2

## MVP

```text
OPENHANDS_NATIVE
```

使用用户中转站 ModelDefinition。

## Optional Future

```text
SPECIALIZED_LANGGRAPH
EXTERNAL_AGENT_ACP
CLINE_SDK
CUSTOM_RUNTIME
```

这些不进入默认路径。

## Backend Eligibility

Runtime 需满足：

- Tool/Workspace contract；
- pause/cancel/event；
- usage/accounting；
- secret isolation；
- manifest compatibility；
- security tests。

## Exit Strategy

所有 Runtime Adapter 通过统一 contract suite，避免 OpenHands 成为 Domain lock-in。
