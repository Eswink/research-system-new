# Backup & Recovery v0.4.0

## Backup Scope

```text
PostgreSQL
Object Store
Secret Store metadata/config
Protocol/Role/Tool manifests
Deployment config
```

Runtime ephemeral workspace 不是唯一备份源。

## Restore Order

```text
Database
→ Artifact Store
→ Secret references
→ Tool/Model configs
→ Outbox/consumer offsets
→ workers/runtime
```

## Integrity

- DB backup restore test；
- Artifact digest sample verify；
- Manifest/Artifact reference reconciliation；
- orphan scan；
- encrypted backup key rotation。

## Suggested Targets

目标由部署方设定：

```text
RPO
RTO
backup frequency
retention
cross-region copy
```

不在架构文档中承诺固定 SLA。

## Run Recovery

恢复后：

- 过期 Lease 失效；
- RUNNING Task 重新评估；
- 非幂等操作进入人工确认；
- Manifest compatibility 再验证。
