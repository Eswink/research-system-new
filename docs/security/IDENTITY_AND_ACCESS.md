# Identity & Access v0.2.2

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
