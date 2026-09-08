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

## Protocol Drafts（PLAN-20260908-033）

```text
GET    /protocol-templates
GET    /protocol-templates/{template_id}
POST   /protocol-drafts/validate          （零副作用；分析类 POST）
POST   /projects/{id}/protocol-drafts     （创建草稿；Idempotency-Key）
GET    /projects/{id}/protocol-drafts
GET    /protocol-drafts/{draft_id}
PUT    /protocol-drafts/{draft_id}        （保存新修订；If-Match + expected_revision；冲突 412）
GET    /protocol-drafts/{draft_id}/revisions
GET    /protocol-drafts/{draft_id}/revisions/{revision}
POST   /projects/{id}/runs                （扩展：{draft_id, draft_revision} 引用，与 path 二选一）
```

- 修订 append-only、不可变；修订号是草稿内部版本（非工程版本、非 RunManifest Revision）。
- 启动使用已保存修订时，服务端加载该不可变修订并重新 Compile → Preflight → Freeze；
  草稿后续变化不改写已冻结运行。
- 旧 `protocol_path` 请求保持兼容。

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
GET    /runs/{id}/telemetry
GET    /runs/{id}/cost
GET    /evaluations/trend
GET    /cluster/workers
GET    /runs/{id}/placement
```

M15 Operations（只读投影）：

- `GET /runs/{id}/telemetry` — canonical state + sink 计数器组成的
  telemetry summary(任务状态计数、outbox pending、exporter drop/last_error);
  不含任何 telemetry vendor 数据。
- `GET /runs/{id}/cost` — UsageLedger × 版本化定价快照的五状态成本视图
  (ACTUAL/ESTIMATED/MONETARY_UNAVAILABLE/USAGE_UNKNOWN/ZERO +
  pricing_version/digest 盖章)。
- `GET /evaluations/trend` — 分段可比趋势 + 回归标记(判定来自
  `compare_reports`)+ 缺失评测第三态;可选 `dataset_id` 过滤。

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

### M16 Cluster（只读投影）

- `GET /cluster/workers` — worker 集群视图：`worker_ref`（worker_id 的
  sha256 短 digest，原始 id/凭据不出控制面）、state（WorkerState）、
  protocol/runtime 版本、generation、drain 标记、服务端时间的心跳。
- `GET /runs/{id}/placement` — run 的 EXECUTION 任务与其 worker placement。
- registry 未配置 → 503（不伪装空集群）。Console（useCluster/ClusterPanel）
  只消费这两个端点，不直连 Worker。
