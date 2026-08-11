# Tool Runtime v0.4.0

## 1. 分层

```text
Role/Agent
→ Skill
→ Capability
→ ToolResolver
→ ToolSpec
→ ToolProvider
```

## 2. Tool Effect Class

每个 Tool 标注：

```text
READ_ONLY
WRITE
EXECUTE
NETWORK
SECRET_USE
DESTRUCTIVE
EXTERNAL_PUBLISH
```

Effect Class 影响审批、Workspace、审计和重试。

## 3. Effective Tool Set

```text
Role requested capabilities
+ Agent override
∩ Project policy
∩ Phase policy
∩ Autonomy level
∩ WorkspaceLease
∩ Provider health
∩ Credential scope
=
Effective Tool Set
```

AgentSession 启动后冻结 Tool Set。

如需改变 Tool Set，默认新建 Session 或 Fork。

## 4. Provider Types

```text
NATIVE
MCP
REST
CLI
REMOTE_WORKER
```

## 5. ToolPack

```text
ToolPackManifest
├ id/version
├ source
├ digest/signature
├ license
├ tools
├ skills
├ MCP config
├ requested permissions
└ compatibility
```

安装前执行供应链验证。

## 6. Double Enforcement

### Exposure-time
只暴露允许的 Tool Schema。

### Execution-time
调用前重新检查：

- capability
- scope
- arguments
- budget
- credential
- network
- timeout
- idempotency
- risk/gate

## 7. Large Results

Tool 返回：

```text
summary
structured_data_ref
artifact_refs
logs_ref
provenance
continuation_hint
```

大结果不直接塞进模型上下文。

## 8. OpenHands Direct Tool Execution

任何绕过 Agent loop 的直接工具执行都必须先经过 Research OS Policy Wrapper。

禁止业务代码直接调用高风险 `execute_tool()`。
