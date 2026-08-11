# Optional External Agent Backends

不属于 v0.4.0 MVP。

未来可能接入：

- ACP-compatible coding harness；
- Cline SDK；
- specialized LangGraph runtime。

任何外部 Runtime 必须：

- 实现 AgentRuntime contract；
- 受 Workspace/Network/Credential/Budget 约束；
- 不成为 canonical model/tool/security layer；
- 通过同一 adapter/security/eval suite。
