# Policy Engine Integration

## MVP

实现简单、类型安全的 NativePolicyEvaluator：

```text
input: Actor + Task + Capability + Resource + Context
output: ALLOW/DENY/REQUIRE_APPROVAL/CONSTRAINTS
```

## Production Adapter

预留 OPA Adapter。

OPA 适合把 policy decision 与 enforcement 分离，但 Research OS 仍拥有领域 Capability 和 Policy schema。

## Enforcement Points

```text
protocol compile
preflight
agent tool exposure
tool execution
credential resolve
workspace allocation
artifact export
external publish
```

## Decision Log

记录：

```text
policy version
input digest
decision
constraints
reason
```

不记录 Secret。
