# AGENTS.md — Research OS Cursor Engineering Contract v0.4.0

## 1. 不可改变的产品边界

### 用户 LLM 接入

MVP 主路径：

```text
Base URL + API Key + Model ID
```

协议：

```text
OPENAI_COMPATIBLE
```

Domain 使用：

```text
LLMEndpoint
ModelDefinition
ModelProfile
ModelBinding
ModelCompatibilityProfile
ModelRuntimeFingerprint
```

禁止把真实模型厂商写进 Domain。

### Agent Runtime

MVP：

```text
Research OS AgentRuntime Port
→ OpenHandsRuntimeAdapter
→ OpenHands Native Agent
```

Codex / Claude Code / ACP 仅为未来可选 Runtime，不进入默认实现、默认配置、默认 Vertical Slice。

### Tools

既定结构不变：

```text
Skill
→ Capability
→ ToolResolver
→ Tool
→ Native / MCP / REST / Remote Worker
```

LLM 中转站与 Tool Provider 是独立配置面、凭据域和信任域。

## 2. Role、Agent、Task 必须分离

### RoleDefinition

定义职责和默认策略，不绑定具体模型。

### AgentSpec

Role 的配置实例，可独立绑定 ModelDefinition / ModelProfile。

### ResearchTask

一次需要完成的工作单元。

### TaskContract

定义输入、输出、验收标准、权限、预算和失败策略。

### HandoffBundle

Agent/Phase 之间传递结构化结果，不依赖聊天记录作为唯一上下文。

## 3. 必须先 Compile / Preflight，再运行

```text
ProtocolDefinition
→ Protocol Compiler
→ CompiledRunPlan
→ Preflight
→ RunManifest Freeze
→ Execute
```

Preflight 至少检查：

- Protocol DAG
- Role / Agent 可解析
- Model 能力匹配
- Endpoint 健康
- Tool/Capability 可用
- Credential 可解析
- Workspace/Compute 可分配
- Budget 可预留
- Policy 允许
- 输入 Artifact 完整
- 插件/工具版本已 pin

Preflight 未通过不得进入 RUNNING。

## 4. 模型同名漂移必须可见

中转站可能在同一个 Model ID 后替换真实模型。

每次 Run 必须记录：

```text
ModelDefinition
Endpoint config digest
returned model name
system fingerprint（若有）
selected response headers（白名单）
probe suite version/hash
compatibility result
runtime fingerprint
```

无法证明底层模型完全一致时，必须明确标注“可重复配置”而非“完全模型可复现”。

## 5. OpenHands Adapter 的额外约束

- OpenHands 类型不得进入 Domain。
- OpenHands 允许 resume 时改变 LLM/context；Research OS 默认禁止，除非显式创建 Manifest Revision 或 Fork Run。
- OpenHands 的 Direct `execute_tool()` 可能绕过 Agent loop 的 confirmation/security；Research OS 不允许不经 Policy Wrapper 调用高风险工具。
- OpenHands resume 要求 Tool 集一致；AgentSession 的有效 Tool Set 必须冻结。
- Plugin/Skill/MCP 来源必须 pin 到版本/commit/digest。

## 6. Canonical State

PostgreSQL Domain Entity 是业务真相。

不是：

- OpenHands Conversation
- runtime checkpoint
- Temporal history
- logs
- vector index
- UI state

Vector/embedding 只允许作为可重建的 derived index。

## 7. 工作流可靠性

默认任务分发语义按：

```text
at-least-once
+
idempotency
+
deduplication
```

实现。

必须有：

- idempotency key
- Task lease + heartbeat
- retry classification
- exponential backoff
- circuit breaker
- dead-letter / manual recovery
- cancellation semantics
- compensation for non-idempotent actions
- transactional outbox for domain events

禁止假装实现“exactly once”。

## 8. Memory 不是自由写入的聊天摘要

Memory 写入流程：

```text
MemoryWriteProposal
→ schema validation
→ provenance check
→ policy
→ curator/automatic gate
→ commit
```

Project/Organization Memory 必须：

- 有来源
- 有置信度
- 有适用范围
- 有过期/复核策略
- 可删除
- 可重建索引

## 9. Security

默认 deny：

- host shell
- host home mount
- Docker socket
- privileged container
- unrestricted public network
- secret enumeration
- arbitrary credential forwarding
- unpinned plugin
- package install
- destructive workspace action
- external publish

MCP Roots、workspace hints 或 tool descriptions 都不是访问控制边界。

## 10. 观测隐私

OpenTelemetry/LLM tracing 默认不记录完整 Prompt、模型输入输出和 Tool 敏感参数。

只记录：

- digest
- size
- type
- latency
- token/usage
- status
- redacted metadata

显式 Debug Mode 才允许受控内容采样，并受 retention policy 管理。

## 11. 测试与发布

必须提供：

- FakeAgentRuntime
- FakeModelGateway
- FakeToolProvider
- FakeWorkspaceBackend
- FakeWorkflowEngine
- model probe mock
- idempotency/retry tests
- resume/manifest drift tests
- permission deny tests
- secret redaction tests
- tool supply-chain validation tests
- memory provenance tests
- bundle cross-reference validator

真实付费 LLM 不得成为默认 CI 依赖。

## 12. 上游策略

```text
dependency
> adapter
> external service/plugin
> compatibility shim
> fork
```

Fork 必须 ADR、patch surface、同步策略和退出计划。

## 13. Repository Path Naming

- 所有新建或重命名的仓库文件、目录和其他路径段必须使用有意义的英文语义名；
  不得使用中文、日文、韩文或其他非 ASCII 自由文本，也不得用拼音替代本可直接表达的英文概念。
- 自由命名路径必须以跨平台可移植性为默认：仅使用 ASCII 字母、数字以及按语境需要的
  `-`、`_`、`.`；不含空白，不以 `-` 开头，不以空格或 `.` 结尾，不使用 Windows
  保留字符或设备名，也不得创建仅大小写不同的并列路径。
- 生态或工具规定的 canonical filename 优先于通用 casing 规则，例如 `README.md`、
  `CHANGELOG.md`、`Dockerfile`、`Makefile`、`package.json`、`pyproject.toml`、
  `__init__.py`；这类例外不允许扩展为任意非英文命名。
- 产品代码、测试和 migration 继续遵守 `.cursor/rules/45-module-file-naming.mdc` 的
  Python、TypeScript/React、SQL 细化规则。没有更具体约定时，目录和普通文档使用
  descriptive `kebab-case`。
- Cursor 工程记录保持既有注册格式，并让描述部分使用英文 `kebab-case`，例如
  `PLAN-YYYYMMDD-NNN-topic.md`、`RECHECK-YYYYMMDD-NNN-topic.md`、
  `MEM-YYYYMMDD-NNN-topic.md`、`EXP-YYYYMMDD-NNN.md`、`LEARN-YYYYMMDD-NNN.yaml`。
  目标级自迭代循环记录使用 `GOAL-YYYYMMDD-NNN-topic.md`（位于 `.cursor/plans/goals/`，
  格式规范见该目录 `README.md`；GOAL 派生的子计划仍是普通 `PLAN-*`）。
- 不用 `final`、`new`、`old`、`tmp`、`copy` 或尾随 `vN` 表示生命周期/伪版本；
  若外部规范、不可变历史资产或明确 schema 要求特定名称，则保留该名称并记录原因。
- 既有历史路径不会仅为满足本规则而批量重命名；一旦任务本身要求重命名该路径，新的名称
  必须满足本节，除非兼容性或不可变历史约束禁止。

## 14. 完成任务时

至少报告：

- 改动
- lint/typecheck/test
- Domain/API/schema 变化
- 安全/凭据变化
- 兼容性/迁移风险
- 上游版本影响
- 下一项任务
