# MCP Tool Provider Integration v0.4.0

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

### 6.1 端点绑定（`endpoint_env`）

provider 可以用 `endpoint_env` 声明**它的端点来自哪个环境变量**：

```yaml
some_rest_provider:
  kind: REST
  transport: rest
  endpoint_env: SOME_REST_ENDPOINT   # 变量名；其值是端点 URL
```

- **env-only**：只读进程环境（`os.environ`），不读文件、不落盘；
- **凭据不走这里**：凭据仍只经 `CredentialResolver`（`credential_ref`），
  把 `NCBI_API_KEY` 这类**凭据名**写进 `endpoint_env` 是配置错误；
- **未设置即不可用**：声明了 `endpoint_env` 而变量未设置 ⇒ 健康探测**不探测**、
  如实 UNKNOWN 并点名变量（不伪装健康）；
- **读面只有指纹**：注册表读面暴露状态（`NOT_DECLARED` / `ENV_UNSET` / `BOUND`）、
  变量名与端点 `sha256` 指纹，**没有端点明文**（端点可能含内网主机名或带 token 的查询串）。
