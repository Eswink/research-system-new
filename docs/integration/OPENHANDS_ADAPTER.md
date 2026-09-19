# OpenHands Adapter v0.4.0 — M6 实现状态

> 本文档原为 M5R 规划（Plan v0.4.0）；M6 已将规划落地为
> `adapters/openhands/` 实现并通过 contract suite。本节记录实现事实，
> 规划章节保留为设计意图与约束。

## M6 实现事实（2026-08-13，含独立复审修正）

- 实现位置：`adapters/openhands/`（runtime_adapter / session_builder /
  llm_factory / tool_mapping / policy_wrapper / policy_enforcing_agent /
  event_mapping / error_mapping / workspace_adapter / usage_mapping）。
- 采用版本：openhands-sdk==1.42.0（PyPI，sdist sha256 见
  UPSTREAM_COMPONENTS.yaml / OPENHANDS_REVISION_LOCK.yaml；revision lock
  status 已由 RESEARCH_LOCKED_NOT_ADOPTED 更新为 ADOPTED）。
- OpenHands 类型只存在于 `adapters/openhands/`；Domain/Port 零 import
  （fault injection 负测覆盖）。
- AgentRuntime Port 六方法全部实现并通过 M5 contract suite 复用
  （Fake 与真实 adapter 共享同一套通用契约测试）。
- cancel 语义（R-01）：SDK interrupt → PAUSED，adapter 显式收敛为
  domain CANCELLED 终态；重复 cancel 幂等；终端后 cancel no-op；
  run 进行中 cancel 真实并发测试覆盖（工具执行中取消 → CANCELLED）。
- 错误映射（R-07 修正）：SDK 双通道错误模型——ConversationErrorEvent
  （ErrorClassification 闭集）与 ConversationRunError（original_exception
  保留原始异常）均被归一化；事件分类优先，其次原始异常类型
  （LLMTimeoutError → TransientPortError 等）；SDK 异常类型不越过边界。
- LLM Relay：base_url/api_key/model 三要素透传；非知名 model +
  自定义 base_url 时 runtime model identifier 加 `openai/` 前缀变换
  （R-08 实证；变换只存在于 llm_factory）。**出网门禁不在本层**：base_url 的
  URL 策略由受控出网门链在 run 路径上先裁决（GOAL-007 EC-02，见
  `docs/architecture/AGENT_RUNTIME.md` §3.2）；`build_llm` 不做 host 判断，
  也不得自行新造一份——host 分类全仓只有 `endpoint_policy.py` 一处。
  **三要素的来源**（GOAL-007 EC-03，见 §3.3）由 `AgentSessionSpec` 携带：
  `endpoint`/`model` 在上层（orchestration，catalog 在手处）解析，凭据**值**由
  adapter 经注入的 `CredentialResolver` 按 `spec.endpoint.credential_ref` 取；
  生产装配的 `build_llm` 是 `session_llm_factory` 返回的 **spec 驱动**工厂，
  它在构造 LLM **之前**按 `URL 策略 → 凭据存在性` 拒绝并点名事实（零出站）。
- Policy（R-03 修正）：PolicyEnforcingAgent 在 SDK agent loop 工具执行点
  （_execute_action_event）强制 PolicyEvaluator——DENY/REQUIRE_APPROVAL
  返回拒绝反馈且不触达工具 executor；REQUIRE_APPROVAL 额外投影
  approval.requested 事件；execute_tool 直通面由 PolicyWrappedToolExecutor
  独占门禁（adapter.execute_tool_gated）。
- Workspace（R-04/R-17）：LocalWorkspace 默认 deny host shell；文件路径
  绝对化 + 工作区根校验；DockerWorkspace 映射代码 + 探测式 smoke
  （容器链路验证延后至 M9 Real Experiment Runtime，见 BACKLOG 技术债）。
- Usage（R-16 记账面）：run() 终态后 ConversationStats →
  UsageLedgerEntry 归一化并实际写入 BudgetLedger（signal 语义，记账
  失败不阻断结果）；BudgetLedger 仍 Research OS 拥有。条目按 `task_id` 与
  `model_id` 归因（EC-03：spec 携带执行目标后 model 归因在 adapter 侧可见）。
- fork（复审 F-4 修正）：ForkSpec.model_override 经注入的
  build_llm_for_fork 重建 LLM；tool_set_override 重建工具集；
  manifest_revision_ref 投影到新会话 spec。
- 事件投影（复审 F-5/F-10 修正）：run() 启动投影 SESSION_STARTED（与
  Fake 对齐）；终端 kind 已由事件映射投影时不重复追加；RuntimeEvent
  message 经 domain redaction 脱敏。
- 结构化输出（GOAL-007 EC-03）：run() 收敛到 SUCCEEDED 时携带**最小交付物**
  `{"session_message": {content, message_count, conversation_id, session_id}}`，
  content 取自**已映射**的 `RuntimeEvent.MESSAGE`（复用同一份 redact 与截断，
  不新开绕过脱敏的通道）。非成功终态返回空——失败会话没有结论，把它中间的文本
  登记进 canonical 会把「没做完」伪装成「有产出」（与 Fake 侧同口径）。键名
  `session_message` 是**事实名**：真实交付物与合约声明的 artifact 名之间的映射
  （谁能声明 `analysis_report`）是产品决策，adapter 不自行发明。
- Persistence Boundary：OpenHands conversation 持久化仅 runtime 参考，
  不替代 PostgreSQL Run/AgentRun/Manifest/Domain Event。

## 1. Decision

```text
Research OS AgentRuntime Port
→ OpenHandsRuntimeAdapter
→ OpenHands Software Agent SDK
```

依赖，不 fork。

## 2. Reused Upstream

- Agent reasoning/tool loop；
- Conversation lifecycle/persistence；
- typed events；
- built-in tools；
- MCP；
- Local/Docker/Remote workspace；
- context condenser；
- security analyzer/confirmation；
- stuck detection；
- conversation fork。

## 3. Mapping

```text
Research AgentSessionSpec ↔ OpenHands Agent + Conversation
LLMEndpoint/ModelDefinition ↔ OpenHands LLM
Effective Tool Set ↔ OpenHands Tool/MCP config
WorkspaceLease ↔ OpenHands Workspace
Runtime Event ↔ normalized Research OS event
```

## 4. Non-delegated Truth

OpenHands 不拥有：

- Project/Run/Protocol canonical state；
- Manifest；
- Role/Task semantics；
- Policy truth；
- Evidence/Claim truth；
- Budget Ledger；
- Evaluation result。

## 5. Security Rules

### Direct `execute_tool`

上游直接工具执行可绕过 Agent loop 的 confirmation/security。

Research OS 只允许：

```text
PolicyWrappedToolExecutor
→ OpenHands execute_tool
```

用于受控 setup/test，不允许业务层任意调用。

### Resume

上游可能允许 LLM/context 在恢复时变化。

Research OS resume 前强制 Manifest compatibility；不匹配则 Fork/Revision。

### Tools

上游恢复要求 Tool 名集合兼容，因此 Session 启动时冻结 Effective Tool Set。

### Secrets

上游 Secret Registry 不是 canonical vault。Secret 由 Research OS CredentialResolver 按 scope 注入。

## 6. Plugins

OpenHands Plugin 可包含 Skill/Hook/MCP/Agent/Command。

Research OS 使用时必须：

- pin immutable revision；
- 保存 resolved digest；
- 审计 permissions/license；
- 不允许 floating branch 进入 RunManifest。

## 7. Contract Tests

```text
relay mapping
model probe/eligibility
create/run/pause/cancel/fork
frozen tool set
policy wrapper
workspace boundary
event normalization
stuck mapping
resume manifest mismatch
secret redaction
usage/cost mapping
```
