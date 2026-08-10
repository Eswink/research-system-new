# OpenHands Adapter Plan v0.2.2

## 1. Decision

```text
Research OS AgentRuntime Port
→ OpenHandsRuntimeAdapter
→ OpenHands Software Agent SDK
```

依赖，不 fork。

## 2. Reused Upstream

- Agent reasoning/tool loop；
- Conversation lifecycle/persistence；
- typed events；
- built-in tools；
- MCP；
- Local/Docker/Remote workspace；
- context condenser；
- security analyzer/confirmation；
- stuck detection；
- conversation fork。

## 3. Mapping

```text
Research AgentSessionSpec ↔ OpenHands Agent + Conversation
LLMEndpoint/ModelDefinition ↔ OpenHands LLM
Effective Tool Set ↔ OpenHands Tool/MCP config
WorkspaceLease ↔ OpenHands Workspace
Runtime Event ↔ normalized Research OS event
```

## 4. Non-delegated Truth

OpenHands 不拥有：

- Project/Run/Protocol canonical state；
- Manifest；
- Role/Task semantics；
- Policy truth；
- Evidence/Claim truth；
- Budget Ledger；
- Evaluation result。

## 5. Security Rules

### Direct `execute_tool`

上游直接工具执行可绕过 Agent loop 的 confirmation/security。

Research OS 只允许：

```text
PolicyWrappedToolExecutor
→ OpenHands execute_tool
```

用于受控 setup/test，不允许业务层任意调用。

### Resume

上游可能允许 LLM/context 在恢复时变化。

Research OS resume 前强制 Manifest compatibility；不匹配则 Fork/Revision。

### Tools

上游恢复要求 Tool 名集合兼容，因此 Session 启动时冻结 Effective Tool Set。

### Secrets

上游 Secret Registry 不是 canonical vault。Secret 由 Research OS CredentialResolver 按 scope 注入。

## 6. Plugins

OpenHands Plugin 可包含 Skill/Hook/MCP/Agent/Command。

Research OS 使用时必须：

- pin immutable revision；
- 保存 resolved digest；
- 审计 permissions/license；
- 不允许 floating branch 进入 RunManifest。

## 7. Contract Tests

```text
relay mapping
model probe/eligibility
create/run/pause/cancel/fork
frozen tool set
policy wrapper
workspace boundary
event normalization
stuck mapping
resume manifest mismatch
secret redaction
usage/cost mapping
```
