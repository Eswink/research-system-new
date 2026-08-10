# Data Governance v0.2.2

## 1. Data Classification

```text
PUBLIC
INTERNAL
CONFIDENTIAL
RESTRICTED
```

## 2. Relay Egress

用户的 LLM Relay 是外部处理边界。

Preflight 根据项目分类检查：

- 是否允许发送到该 Endpoint；
- 是否允许发送源文件全文；
- 是否需要 redaction；
- 是否只允许自托管 Relay；
- 是否允许 telemetry/content capture。

`RESTRICTED` 默认禁止外部 Relay，除非组织策略显式批准。

## 3. Tool Egress

每个 ToolProvider 记录：

```text
network destination
data categories sent
data categories returned
credential scope
retention/terms reference
```

## 4. Source Rights

SourceRecord 尽可能记录：

- URL/DOI/source；
- access time；
- license/terms；
- author/owner；
- allowed use/export；
- content digest。

系统不应默认把所有下载内容重新分发进导出包。

## 5. PII / Secrets

- 输入扫描/标签；
- Prompt/Tool output redaction；
- 限制长期 Memory；
- deletion/export workflow；
- support bundle 默认不含内容。

## 6. Retention & Deletion

```text
active retention
archive
legal hold
user deletion
cryptographic/physical deletion where supported
tombstone + index cleanup
```

## 7. Data Residency

DeploymentProfile 可约束：

- DB region；
- Artifact region；
- Relay region；
- Tool region；
- worker region。
