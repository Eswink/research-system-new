# Deployment Profiles v0.4.0

## A. Local Developer

用途：单机 PoC/开发。

```text
React/Vite Console + FastAPI
PostgreSQL via Docker Compose
Content-addressed local Artifact Store
PostgreSQL WorkflowEngine
validation worker（deterministic，非真实 execution plane）
```

`infra/compose/research-validation.yaml` 实现该本地集成/验证 profile：六个研究服务只连接 internal
network，由无凭据、固定目标的 host proxy 发布 loopback 端口；边缘 bridge 关闭 IP
masquerade。默认不挂 Docker Socket、不开放公共网络，也不传入 LLM 凭据。真实 Docker/GPU Worker 仍按个人部署指南在显式授权的 Worker host 上运行；
不得把 validation worker 的注册成功描述为真实实验执行验证。

不用于不可信多租户。

## B. Self-hosted Team

```text
separate API/worker
PostgreSQL HA baseline
MinIO/S3
Redis cache
OpenHands Agent Server pool
secret manager
OTel collector（`infra/compose/otel-evidence.yaml`：
`otel/opentelemetry-collector-contrib@sha256:faf125d…`，OTLP/HTTP :4318，
batch + debug/file exporter，无 vendor 后端；应用侧经
`RESEARCHOS_OTEL_ENABLED=1` + `RESEARCHOS_OTEL_ENDPOINT` 接入）
role-based access
```

可先继续 LocalWorkflowEngine + durable DB queue，之后接 Temporal。

## C. Distributed/Hardened

```text
worker gateway（/worker/v1，RESEARCHOS_WORKER_GATEWAY_REQUIRE_TLS=1）
python -m services.worker pools（M16；Postgres 队列 + fence，非 Temporal）
remote/hardened sandbox（DockerExecutionBackend on worker host）
OPA adapter
central secret manager
egress proxy
Kubernetes/HPC scheduler
central OTel（同 M15 collector 拓扑，可替换 remote endpoint）
backup/restore
```

> M16 注记：M16 交付的分布式执行面（HTTP worker gateway + services.worker
> 子进程 + PostgreSQL 队列/lease/fencing）落在 Profile B（loopback/内网明文）
> 与 Profile C（非 loopback 强制 TLS，生产 TLS 终结在上游）。Temporal 仍为
> DEFERRED（ADR-0025/0027；M16 重评条件未触发）。

## D. HPC / Research Cluster

可使用：

```text
Apptainer
Slurm adapter
readonly datasets
shared artifact store
```

## Client Strategy

第一阶段 B/S。

后续 C/S 可以使用轻量 Desktop Shell 连接同一 Control Plane，不自研 IDE 内核。
