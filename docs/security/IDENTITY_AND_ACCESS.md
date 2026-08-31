# Identity & Access v0.4.0

## 1. MVP 与未来

MVP 可以单用户运行，但 Domain/API 不把“当前用户”写死为全局管理员。

预留：

```text
Organization
User
ServicePrincipal
AgentPrincipal
ProjectMembership
AccessGrant
```

## 2. Human Roles

```text
SYSTEM_ADMIN
ORG_ADMIN
PROJECT_OWNER
RESEARCHER
REVIEWER
OBSERVER
```

Reviewer 的人类权限与 ScientificReviewer Agent 的 RoleDefinition 是不同概念。

## 3. Agent Principal

AgentSession 获得临时 Principal：

```text
agent_session_id
run/task scope
capabilities
workspace lease
credential bindings
expiry
```

Agent 不继承发起用户的全部权限。

## 4. Service-to-Service

API、Worker、Tool Gateway、Agent Server 使用独立 service identity 和最小权限。

## 5. Authorization

```text
Human/Service identity
+ Project membership
+ Task/Agent capability
+ Resource scope
→ Policy Decision
```

## 6. Audit

所有变更记录：

```text
actor_type
actor_id
impersonation/delegation chain
resource
action
policy decision
trace
```

## 7. Multi-tenancy

生产多租户需要：

- tenant-scoped queries；
- artifact namespace；
- secret namespace；
- worker/sandbox isolation；
- quota；
- cross-tenant test。

在这些完成前，不宣称支持不可信多租户。

## Worker Identity (M16)

- 入网：预共享 enrollment secret 经 `CredentialResolver`（WORKER 凭据域，
  与 TOOL/MODEL 隔离），`hmac.compare_digest` 常量时间比较。
- 会话：注册成功签发 256-bit session token（仅返回一次；服务端只存
  sha256 + `registration_generation`）；`Authorization: Bearer` 按 hash 查表。
- 反冒充/反重放：请求体 worker_id 必须与 token 身份一致；generation 单调，
  重新注册作废旧 token，旧 session fail closed。
- 传输：默认要求 TLS（`RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1`）；
  绑定非 loopback 且未启用 TLS 拒绝启动。
- Worker 不持有 Control Plane 数据库凭据；Console 只经只读 API 观察集群。
