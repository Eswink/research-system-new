# Operations Runbook v0.4.0

## Health Endpoints

```text
/control-plane/health
/database/health
/outbox/health
/workers/health
/agent-runtime/health
/tool-providers/health
/llm-endpoints/health
/artifact-store/health
```

## Daily Checks

- outbox backlog；
- expired leases；
- stuck agents；
- endpoint/tool circuit state；
- artifact verification failures；
- budget anomaly；
- DB/object-store capacity；
- secret expiration。

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
