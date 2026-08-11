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
