# MCP Tool Provider Integration v0.2.2

## 1. 位置

```text
Research Tool Service
→ MCP Provider Adapter
→ OpenHands MCP integration
→ Agent
```

Research OS 保存自己的 ToolSpec/Capability/Policy。

## 2. Transport

```text
stdio              # local trusted process
Streamable HTTP    # remote
```

旧 SSE 仅兼容，不作为新部署默认。

## 3. Authorization

Remote MCP：

- 独立 OAuth/credential；
- resource/audience scope；
- 禁止 token passthrough；
- server state handle 不视为 authorization；
- credentials 不进入模型上下文。

## 4. Roots

MCP Roots/工作目录提示只用于上下文，不是访问控制。

真正边界由 Workspace/Sandbox/Policy 执行。

## 5. Registration

```text
server identity
protocol/capabilities
transport
schema hash
Tool list
risk/effect class
auth mode
health
```

## 6. Health

- initialize/capability probe；
- tool schema diff；
- timeout/error rate；
- circuit breaker；
- canary after update。
