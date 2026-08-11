# Control Plane API Sketch v0.4.0

所有 mutating request 支持：

```text
Idempotency-Key
If-Match / resource version
```

## Models

```text
POST   /llm-endpoints
GET    /llm-endpoints
POST   /llm-endpoints/{id}/test
POST   /llm-endpoints/{id}/discover-models
GET    /llm-endpoints/{id}/health

POST   /models
PATCH  /models/{id}
POST   /models/{id}/probe
GET    /models/{id}/compatibility
```

不返回明文 Key。

## Roles / Teams / Agents

```text
GET    /roles
POST   /roles/custom
GET    /team-templates
POST   /team-templates/custom
POST   /projects/{id}/agents
PATCH  /agents/{id}
POST   /agents/{id}/clone
```

## Protocol / Preflight

```text
POST   /protocols/validate
POST   /projects/{id}/compile
GET    /compiled-plans/{id}
POST   /compiled-plans/{id}/preflight
```

## Runs

```text
POST   /projects/{id}/runs
GET    /runs/{id}
POST   /runs/{id}/pause
POST   /runs/{id}/resume
POST   /runs/{id}/cancel
POST   /runs/{id}/fork
GET    /runs/{id}/events
GET    /runs/{id}/usage
```

## Tasks / Approvals

```text
GET    /runs/{id}/tasks
GET    /tasks/{id}
POST   /tasks/{id}/retry
POST   /tasks/{id}/fork
GET    /approvals
POST   /approvals/{id}/decide
POST   /runs/{id}/interventions
```

## Tools

```text
POST   /tool-providers
POST   /tool-providers/{id}/test
GET    /tool-providers/{id}/health
POST   /tool-packs/install
POST   /tool-packs/{id}/approve-update
POST   /tool-packs/{id}/revoke
```

## Memory

```text
GET    /projects/{id}/memory
POST   /memory/proposals
POST   /memory/proposals/{id}/decide
DELETE /memory/{id}
```

## Event Stream

```text
GET /runs/{id}/stream       # SSE
WS  /runs/{id}/ws           # optional interactive channel
```

事件支持 cursor/resume，客户端按 event_id 去重。


## Identity / Governance

```text
GET  /me
GET  /organizations/{id}/members
POST /projects/{id}/memberships
GET  /projects/{id}/data-policy
PUT  /projects/{id}/data-policy
POST /projects/{id}/export
POST /projects/{id}/delete-request
```

所有资源查询必须按 principal/scope 授权，不依赖前端隐藏按钮。
