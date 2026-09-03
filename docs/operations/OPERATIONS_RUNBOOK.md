# Operations Runbook v0.4.0

## Health / Operational Surface（PA-1 实测校正 2026-09-03）

> 旧版列出的 `/control-plane/health`、`/database/health`、`/outbox/health`、
> `/workers/health`、`/agent-runtime/health`、`/tool-providers/health`、
> `/artifact-store/health` 在运行中的 API 上不存在（404）。实际面：

```text
GET /openapi.json                                  API 存活
GET /cluster/workers                                worker fleet 健康面
GET /evaluations/trend?dataset_id=…                评测趋势 + 回归标记
GET /runs/{run_id}/cost | /usage | /telemetry      run 级运营视图
GET /runs/{run_id}/events | /tasks | /evidence     run 审计视图
GET /llm-endpoints/{endpoint_id}/health            端点健康
```

数据库直接（psql，`docker exec research-system-postgres-1 psql -U research_os -d research_os`）：

```text
SELECT count(*) FROM leases;                       # 0 = 无孤租约
SELECT count(*) FROM outbox_events WHERE published_at IS NULL;   # outbox backlog
SELECT worker_id, state, gpu_observed_at IS NOT NULL FROM workers;   # worker/GPU 健康
SELECT status, count(*) FROM tasks GROUP BY status;    # queue 深度
```

## Daily Checks

- outbox backlog（`SELECT count(*) FROM outbox_events WHERE published_at IS NULL`）；
- expired leases（`SELECT count(*) FROM leases`，应 0）；
- stuck agents；
- endpoint/tool circuit state；
- artifact verification failures（digest mismatch 检测，[P4] fail-closed）；
- budget anomaly；
- DB/object-store capacity；
- secret expiration。

> PA-1 实测补充（2026-09-03）：PostgreSQL 重启后既有 psycopg 连接不自动
> 重连 —— 操作先停 API/gateway/worker → 重启 PG → 重启控制面；见
> PERSONAL_DEPLOYMENT.md §10 与 PA-1 记录 F2。

## Incident Classes

```text
SEV0 security/data loss
SEV1 control plane unavailable
SEV2 run degradation/provider failure
SEV3 single task/user issue
```

## Emergency Controls

- disable Endpoint；
- revoke ToolPack；
- deny network domain；
- pause all Runs；
- quarantine Artifact；
- rotate credential；
- block dependency version。

## Support Bundle

默认只包含：

- versions；
- config digests；
- redacted errors；
- trace IDs；
- health/metrics；
- no prompts/secrets/raw source content。

## Worker Fleet (M16)

- 健康面：`GET /cluster/workers`（worker_ref + state + last_heartbeat）。
- 生命周期：REGISTERING→READY→BUSY/READY→DRAINING→OFFLINE；心跳丢失由
  `WorkerReaperScheduler`（默认 15s，stale 30s，配置化）判定 LOST。
- 故障处置：
  - worker 失联：LOST 由服务端时间判定；租约经
    `recover_expired_leases`（单一权威）回到 QUEUED 供其他 worker claim；
    迟到结果被 fence 拒绝（`remote_execution.stale_result_rejected_total`）。
  - 优雅下线：`drain`（或 SIGTERM）→ 不再分配 → 既有作业按策略收尾 → OFFLINE。
  - 协议不兼容：注册即拒（`worker.protocol_mismatch_total`），不「连上算兼容」。
  - 网络分区：`tests/distributed` NetProxy 场景证据；重连不恢复旧权威。
- 入网凭据：enrollment secret 经 WORKER 凭据域；session token 仅存 sha256；
  生产必须 `RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1`（非 loopback 无 TLS 拒启）。
