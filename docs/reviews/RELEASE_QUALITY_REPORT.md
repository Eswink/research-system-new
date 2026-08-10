# Research OS Bootstrap v0.2.2 — Release Quality Report

Release status: **APPROVED**
Release threshold: **9.2 / 10**

## Review History

| Round | Score | Result | Principal Rework |
|---|---:|---|---|
| 1 | 8.6 | Rejected | 清理旧版本资产、修正发布卫生和安全 marker |
| 2 | 8.9 | Rejected | 补齐机器可读 Role/Capability、输出 Schema、Backend registry |
| 3 | 9.1 | Rejected | 补齐身份、数据治理、研究诚信、备份、SLO/容量 |
| 4 | **9.7** | **Approved** | 端到端语义与自动化发布门禁通过 |

## v0.2.2 Improvement Summary

在完全保留 v0.2.1 固定边界的前提下，v0.2.2 新增了六类工程闭环。

### 1. Compile Before Execute

```text
ProtocolDefinition
→ Protocol Compiler
→ CompiledRunPlan
→ PreflightReport
→ RunManifest
→ Execution
```

避免在运行途中才发现模型、工具、权限、预算或 Workspace 不可用。

### 2. Contract-based Agent Collaboration

```text
ResearchTask
+ TaskContract
+ AcceptanceCriteria
+ HandoffBundle
```

Agent 不再靠无结构聊天传递关键状态。

### 3. Relay Compatibility and Drift Control

```text
LLMEndpoint
→ ModelDefinition
→ Probe/Capability Matrix
→ Role Eligibility
→ ModelRuntimeFingerprint
```

对同一 Model ID 的能力差异和中转站漂移保持可见。

### 4. Reliable Autonomous Execution

```text
at-least-once
+ idempotency
+ task lease/heartbeat
+ retry/backoff
+ circuit breaker
+ transactional outbox
+ compensation
```

负结果与系统失败正式分离。

### 5. Governed Agent Environment

```text
AgentPrincipal
+ Capability Policy
+ ToolPack Supply Chain
+ Workspace Isolation
+ Evidence-backed Memory
+ Privacy-first Telemetry
```

### 6. Production Readiness

```text
Local / Team / Hardened / HPC profiles
+ Backup/Restore
+ RPO/RTO
+ SLO/Capacity Admission
+ Data Governance
+ Research Integrity
```

## Preserved Non-negotiable Boundary

```text
User provides:
Base URL + API Key + Model IDs
```

- 每个 Agent 独立配置 ModelDefinition/ModelProfile；
- OpenHands Native 是 MVP generic runtime；
- Codex/Claude Code/ACP 不进入默认主路径；
- Tools/MCP/Workspace/Sandbox 继续复用成熟轮子；
- Research OS 自己拥有 Protocol、Role、Policy、Evidence、Evaluation 和 canonical state。

## Release Artifacts

- 完整文档与机器可读示例；
- 26 个系统 Role；
- JSON Schemas；
- ADR-0001..ADR-0024；
- Bundle validator；
- SHA-256 manifest；
- 四轮 Review 记录。

## Recommended First Engineering Slice

```text
Domain + Schemas
→ Model/Role Resolver
→ Protocol Compiler/Preflight
→ Fakes
→ OpenHands Relay Compatibility Spike
→ one Tool + one Workspace action
→ Artifact/Evidence/Claim
→ Recovery/Evaluation
```
