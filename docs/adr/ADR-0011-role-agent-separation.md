# ADR-0011 — Separate RoleDefinition from AgentSpec

Status: Accepted
Date: 2026-08-10

## Decision

RoleDefinition 不绑定具体模型。

AgentSpec 实例化 Role，并可以单独绑定 ModelDefinition / ModelProfile。

同一 Role 可有多个 Agent，使用不同模型。

## Why

支持：

- heterogeneous reviewer panel
- parallel literature scouts
- user per-role model selection
- project-specific overrides
- model benchmark-driven routing

## Consequence

Protocol 请求 Role/RolePool，而不是直接请求具体 Model。
