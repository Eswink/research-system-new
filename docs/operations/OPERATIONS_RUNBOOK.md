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

> PA-1 实测补充（2026-09-03）：PostgreSQL 重启后 adapter 连接已自动重连
> （F2 修复，`ReconnectableConnection`；事务中失败不重试）——重启 PG 后
> 控制面进程无需重启，过期租约自动收敛；见 PERSONAL_DEPLOYMENT.md §10。

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
  - 服务端 drain：`drain` → 不再分配 → 既有作业正常收尾 → OFFLINE。
  - 进程关停：SIGTERM → 不再认领 + **中断在途执行**（复用协作式 cancel 通道，
    不等待长作业跑完）→ 该次尝试**不提交结果**，租约由控制面按 LOST 路径回收
    （at-least-once，与硬杀一致）；心跳睡眠与重连退避可被打断，进程即刻退出。
    **在途网关读**（连上了但读不到数据）另有独立上界：`RESEARCHOS_WORKER_DRAIN_SECONDS`
    （默认 5s，取值域 0.1~60）到期即**放弃**该次调用，进程随即按有序停机退出（退出码 0）
    ——本轮之前这个上界等于客户端超时 30s（SIGTERM 处理器只置标志，被中断的 read 会被
    系统调用重试）。被放弃的请求**可能已到达服务端，也可能没有**：这是 at-least-once
    允许的模糊点，由幂等键与租约恢复覆盖，不得读成「一定没发生」。
  - 协议不兼容：注册即拒（`worker.protocol_mismatch_total`），不「连上算兼容」。
  - 网络分区：`tests/distributed` NetProxy 场景证据；重连不恢复旧权威。
- 入网凭据：enrollment secret 经 WORKER 凭据域；session token 仅存 sha256；
  生产必须 `RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1`（非 loopback 无 TLS 拒启）。

## Experiment Queue (G14)

- 控制面进程内的队列消费者 `ExperimentQueueDispatcher`（默认 15s，随 API 生命周期
  启停）：认领到期条目 → 走与 `POST /runs` 相同的装配链启动 run → 把 `run_id`
  写回条目（`DISPATCHED`）或把失败原因写回（`FAILED`）。
- 认领是原子的（PG `FOR UPDATE SKIP LOCKED` / SQLite 条件更新）；认领超过 300s
  的条目（进程崩溃或停机中断）回到 `QUEUED` 重新派发 = **at-least-once**，
  不假装 exactly-once（同一排期条目可能对应两次启动尝试，条目上的 `run_id`
  是最近一次的结果）。
- 派发顺序：`COALESCE(not_before, created_at)` 升序；派发是**串行**的（进程内 run
  同步执行），因此队列吞吐与 API 侧 run 吞吐同阶，不因队列而上行。
- 失败处置：失败是终态（不静默重试）。运维重新排队是显式动作；计划被归档后
  到期的条目按 `FAILED`（原因含 `ARCHIVED`）落地，不启动 run。
- 观测：`experiment_queue.dispatch_pass` operation span + 
  `research_os.experiment_queue.dispatch_total` 计数（每次派发尝试一次）。
