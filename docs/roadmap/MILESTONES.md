# Milestones v0.4.0

`CODEX_BOOTSTRAP.md` 是里程碑详细定义；本文件只提供同一编号体系的执行索引，不维护第二套阶段语义。

## M0 — Repository Foundation Quality Gate

可复现 Python/TypeScript 工具链、`domain/application/adapter/entry` 依赖边界、architecture/contract test 入口和 Windows/Linux CI。M0 用正反向架构夹具证明门禁语义，不创建空生产包，也不实现产品业务能力。

## M1 — Domain Kernel & Contract Assets

稳定实体、值对象、枚举、状态机、RunManifest/Revision、JSON/YAML Schema、确定性 digest 与 invariant tests。

## M2 — Protocol Compiler + Preflight

Role/Agent/Model/Tool/Workspace/Budget/Policy resolution，生成 CompiledRunPlan 与机器可读 PreflightReport。

## M3 — Model Relay Compatibility

用户中转站、ModelDefinition、capability probe、eligibility、health/circuit breaker、runtime fingerprint 与 secret redaction。

## M4 — Role / Team / Task

26 个 Role fixtures、TeamTemplate 解析、per-Agent model binding、TaskContract、AcceptanceCriteria 与 HandoffBundle。

## M5 — Ports + Fakes

WorkflowEngine、AgentRuntime、ModelGateway、ToolProvider、WorkspaceBackend、ArtifactStore 等 inward-owned Ports、Fake 实现和 contract suite。

## M6 — OpenHands Spike

用户中转站 → OpenHands Native Agent → frozen Tool Set → safe Workspace；验证 Policy Wrapper、resume drift、Fork 与 plugin pin。

## M7 — Reliable Mock Vertical Slice

Compile → Preflight → Manifest Freeze → Lease/Idempotency/Outbox → Agent Session → Tool/Handoff/Artifact/Evidence/Evaluation，并注入重复投递、超时、worker 丢失、预算与取消故障。
