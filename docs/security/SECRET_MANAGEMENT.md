# Secret Management v0.4.0

## 1. Secret 类型

```text
LLM_RELAY_KEY
TOOL_API_KEY
OAUTH_TOKEN
COMPUTE_CREDENTIAL
OBJECT_STORE_CREDENTIAL
```

## 2. Domain 只保存引用

```text
credential_ref
scope
allowed_subject
allowed_resource
expiry/version
```

## 3. Secret Broker

调用时：

```text
Actor/Task
→ Policy
→ CredentialBinding
→ Secret Broker
→ one-use/lazy injection
```

## 4. Scope

```text
organization
project
run
agent_session
tool_call
```

优先最小 scope。

## 5. Rotation

Secret rotation 不改变 RunManifest 的明文值；记录 credential version/fingerprint。

## 6. Redaction

覆盖：

- exception；
- HTTP header；
- config repr；
- tool output；
- telemetry；
- support bundle。

## 7. Storage Backend

MVP 可用本地加密/系统 Secret Store；生产通过 `CredentialResolver` 接 Vault/Infisical/云 Secret Manager 等实现，不让 Domain 绑定具体产品。
