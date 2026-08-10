# ADR-0022 — Agent Principals Are Task-scoped

Status: Accepted

Agent 不继承发起用户全部权限。每个 AgentSession 使用临时、Task-scoped Principal、Capabilities、WorkspaceLease 和 CredentialBindings。
