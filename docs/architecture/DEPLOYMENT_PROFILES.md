# Deployment Profiles v0.4.0

## A. Local Developer

用途：单机 PoC/开发。

```text
Next.js/FastAPI
PostgreSQL via Docker Compose
Local S3-compatible store
LocalWorkflowEngine
OpenHands DockerWorkspace
single worker
```

不用于不可信多租户。

## B. Self-hosted Team

```text
separate API/worker
PostgreSQL HA baseline
MinIO/S3
Redis cache
OpenHands Agent Server pool
secret manager
OTel collector
role-based access
```

可先继续 LocalWorkflowEngine + durable DB queue，之后接 Temporal。

## C. Distributed/Hardened

```text
Temporal
worker pools
remote/hardened sandbox
OPA adapter
central secret manager
egress proxy
Kubernetes/HPC scheduler
central OTel
backup/restore
```

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
