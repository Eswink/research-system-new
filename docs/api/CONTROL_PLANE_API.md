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
POST   /protocols/validate                 （path 或 {draft_id,draft_revision} 二选一）
POST   /projects/{id}/compile              （同上双来源；WP-B 已交付）
POST   /projects/{id}/preflight            （同上双来源）
POST   /projects/{id}/dry-run              （同上双来源）
GET    /compiled-plans/{id}                （未提供：编译产物暂无独立寻址）
POST   /compiled-plans/{id}/preflight      （未提供：见上双来源预检）
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
- WP-B（PLAN-20260910-037）：validate/compile/preflight/dry-run 与 runs 启动共用
  同一 `protocol_source` loader（互斥来源、缺失 422、未知修订 404）。

## Runs

```text
POST   /projects/{id}/runs
GET    /runs/{id}
POST   /runs/{id}/pause
POST   /runs/{id}/resume
POST   /runs/{id}/cancel
POST   /runs/{id}/fork                     （未提供：Fork/Manifest Revision 属后续能力）
GET    /runs/{id}/events
GET    /runs/{id}/usage
GET    /runs/{id}/telemetry
GET    /runs/{id}/cost
GET    /runs/{id}/artifacts                （WP-C 只读列表）
GET    /artifacts/{artifact_id}            （WP-C 元数据 + 内容级 verify）
GET    /artifacts/{artifact_id}/content    （WP-C 下载/白名单内联预览）
GET    /cost/daily                         （WP-D 跨 run 日序列，五状态盖章）
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
- `GET /cost/daily`（WP-D）— UsageLedger 全扫描按 UTC 日投影；每天按
  (pricing_version, digest) 分组，混合定价的日不求和（PARTIALLY_METERED +
  分组小计）；只含有数据的日期，无预测无插值。
- `GET /artifacts/*`（WP-C）— store 缺失 503；未知 404；tombstone/缺 blob
  410；超限 413；非白名单 media 一律 attachment + nosniff。

## Tasks / Approvals

```text
GET    /runs/{id}/tasks
GET    /tasks/{id}                         （未提供：任务详情走 /runs/{id}/tasks 投影）
POST   /tasks/{id}/retry                   （未提供：retry 属 WorkflowEngine 内部策略）
POST   /tasks/{id}/fork                    （未提供：同 runs fork）
GET    /approvals
POST   /approvals/{id}/decide
POST   /runs/{id}/interventions
```

WP-H（PLAN-20260910-037）审批注册点：协议 phase 声明
`gate: HUMAN_GATE`（preflight 呈现为 INFO 声明 + unresolved_risks，不阻断
freeze）；执行循环在该 phase 前注册 ApprovalRecord 并 emit
`approval.requested`，run 进入 WAITING_FOR_APPROVAL。decide approve 后续跑
剩余 specs 并持久化终态；进程重启导致执行上下文丢失时 approve 诚实返回
503 且不消费审批（绝不伪造恢复）。deny → APPROVAL_REJECTED → FAILED。

## Tools

```text
POST   /tool-providers                     （未提供：Tool Provider 管理面）
POST   /tool-providers/{id}/test           （未提供）
GET    /tool-providers/{id}/health         （未提供；preflight 侧 provider 三态探测已接入 WP-D）
POST   /tool-packs/install                 （未提供：供应链治理，install/approve/revoke 全组）
POST   /tool-packs/{id}/approve-update     （未提供）
POST   /tool-packs/{id}/revoke             （未提供）
```

## Experiments（WP-E）

```text
GET    /runs/{id}/experiments              （run 级 evidence 聚合视图）
GET    /projects/{id}/experiments          （项目级跨 run 视图；双路径可用）
POST   /projects/{id}/experiments          （计划预注册 DRAFT→PREREGISTERED；仅 PG store，SQLite 503）
POST   /experiments/{plan_id}/archive      （归档裁决 409/404；无 queued 状态，不伪造队列）
```

## Notifications（WP-G）

```text
GET    /notifications?limit=               （outbox 事件白名单投影；无 payload 内容）
POST   /notifications/{event_id}/read      （已读 view-state 持久化；幂等）
```

- 事件流是真相；已读是 per-event view-state（控制面 SQLite，非 canonical 研究事实）。

## Memory

```text
GET    /projects/{id}/memory               （WP-F；store 缺失 503 + scope_note）
POST   /memory/proposals                   （WP-F；完整 §8 门链直提交）
POST   /memory/proposals/{id}/decide       （未提供：域内无持久化 pending 提案）
DELETE /memory/{id}                        （WP-F；lifecycle 用例 + 幂等键）
```

- WP-F 语义修正：MemoryWriteProposal 是瞬态值对象，没有可裁决的持久化
  pending 状态；两阶段 decide 需要 proposal store + 迁移（未实现，避免伪
  造第二套事实源）。`curator_approved` 作为提案参数进入门链：
  schema → provenance（ledger.has_source 验证）→ contradiction →
  policy(None=ALLOW) → tier/curator 门 → sanitize-before-commit →
  commit + MEMORY_PROPOSED/MEMORY_COMMITTED 事件。
- capability policy 面（`_CAPABILITY_SCOPE` 镜像契约）纳入 memory.write 为
  follow-up；当前写入门槛由 provenance 白名单 + PROJECT/ORGANIZATION tier
  的 curator 门承担。

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
