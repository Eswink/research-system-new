# ADR-0010 — User LLM Relay as the MVP Model Integration

Status: Accepted
Date: 2026-08-10

## Context

目标用户不会分别配置 OpenAI/Anthropic/DeepSeek SDK。
用户提供一个中转站：

```text
Base URL + API Key + Model IDs
```

## Decision

MVP Domain 使用：

```text
LLMEndpoint(protocol=OPENAI_COMPATIBLE)
ModelDefinition
ModelProfile
ModelBinding
```

不建立厂商专用 Provider Domain。

## Consequences

优点：

- UI 简单
- provider agnostic
- 中转站可自行聚合多模型
- Agent per-model config 简单
- 不被供应商 SDK 绑定

代价：

- 某些 provider-native 特性需要 endpoint 自身兼容或未来扩展
- capability 需要用户配置/probe
- model pricing/metadata 不一定可自动得知
