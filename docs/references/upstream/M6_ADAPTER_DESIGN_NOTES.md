# M6 Adapter Design Notes — OpenHandsRuntimeAdapter 设计承接

Phase: M5R
Date: 2026-08-12
Evidence base: docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md
Port matrix: docs/references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md

本文件是 M5R 对 M6 的 adapter 设计移交，不构成 M6 实施。

## 1. 总装结构

```text
Research OS AgentRuntime Port（packages/application/ports/agent_runtime.py）
→ OpenHandsRuntimeAdapter（adapters/openhands/，M6 新建）
→ OpenHands Software Agent SDK v1.42.0（openhands.sdk.*）

外部强制（不委托 OpenHands）：
→ PolicyWrappedToolExecutor（封堵 execute_tool 直通）
→ Manifest compatibility check（resume/fork 前）
→ CredentialResolver 按 scope 注入（OpenHands Secret Registry 非 vault）
→ DockerWorkspace + 网络隔离（默认 deny host shell）
```

## 2. AgentRuntime Port 映射

| Port 面 | OpenHands 对象 | Adapter 职责 |
| --- | --- | --- |
| create_session | `Conversation.__new__` → LocalConversation（agent + workspace + persistence_dir + conversation_id） | AgentSessionSpec → OpenHands Agent（由 OpenHandsAgentSettings 装配）；frozen_tool_set → agent.tools（Tool spec 列表）+ manifest_ref 保存 |
| run | `LocalConversation.run()`（同步阻塞，与 Port D2 同步语义一致） | 迭代至 FINISHED/PAUSED/STUCK/ERROR；返回 AgentSessionResult（status 收敛到 domain 终态） |
| pause | `LocalConversation.pause()` | 直接映射（步骤边界生效） |
| cancel | `LocalConversation.interrupt()` | **语义映射**：interrupt → 置 Research OS 取消信号；OpenHands 结果 PAUSED（可恢复）→ 按 Research OS 语义收敛为 CANCELLED 或 PAUSED（由调用方策略决定）；不得把 OpenHands PAUSED 误映射为 domain CANCELLED 而不做显式转换 |
| stream_events | `state.events`（Event 树，EventLog 文件回溯） | 事件归一化：ActionEvent→TOOL_CALL_REQUESTED/STEP_COMPLETED、ObservationEvent→STEP_COMPLETED、AgentErrorEvent→SESSION_FAILED 前置、ConversationStateUpdateEvent→状态映射、PauseEvent/InterruptEvent→SESSION_PAUSED/SESSION_CANCELLED；无 1:1，映射表在 adapter 内显式定义 |
| fork | `LocalConversation.fork()` | ForkSpec.model_override → 新 LLM；tool_set_override → 新工具集；manifest_revision_ref → 新 Manifest 绑定 |
| 状态 | `ConversationExecutionStatus` | IDLE/CREATED↔domain CREATED；RUNNING↔RUNNING；PAUSED↔PAUSED；STUCK↔STUCK；FINISHED↔SUCCEEDED；ERROR↔FAILED；WAITING_FOR_CONFIRMATION↔WAITING_FOR_APPROVAL；DELETING→close 处理 |

## 3. ModelGateway / M3 映射

- LLMEndpoint（base_url/api_key/model_id）→ `LLM(model=..., base_url=..., api_key=...)` 直接构造（S2 spike 已验证三要素保留与 JSON 往返）。
- LLMResponse.raw_response 暴露 litellm 类型：**LLM→Domain 转换全部在 adapter 内**，Domain 只见归一化结果。
- 能力判定：ModelCompatibilityProfile 主导（M3 probe suite），不信任 litellm 探测（中转站 + 非知名 model 时 provider 推断不可靠，审计 §5）。
- max_output_tokens cap（16384）：adapter 装配 LLM 时按 M3 配置显式设置，避免默认 cap 与 Research OS budget 冲突。
- 重试：SDK 内置 tenacity 重试（5 次、8-64s）与 Research OS retry classification 的关系在 M6 决策：Port 语义下 adapter 保留 SDK 内置重试或禁用后由外层策略执行，二选一，不双重重试。

## 4. ToolProvider / Policy 映射

- ToolProviderSpec 执行 → `ToolDefinition.__call__(action, conversation)`（注册后由 agent loop 解析）。
- ToolCallRecord 归一化 → ToolResultRecord（digest 存内容，ArtifactStore 持久化）。
- **Policy Wrapper 必须包 execute_tool 与 ToolCallEvent 拦截点**：OpenHands confirmation_mode 是 agent loop 内部行为且 execute_tool() 可绕过（审计 §6、§11）；Research OS PolicyEvaluator 决策在外层，OpenHands SecurityRisk 仅作为可选风险信号源。
- frozen tool set：Session 启动时冻结 agent.tools 列表；resume 时用 `agent.verify()`（类一致 + 工具只增不删）校验（AGENTS.md §5 成立）。

## 5. WorkspaceBackend / ExecutionBackend 映射

- 默认 MVP：DockerWorkspace（容器生命周期 = WorkspaceBackend 创建/清理面；pause/resume 近似 Lease 冻结语义）。LocalWorkspace（host shell）默认禁用，显式配置 + Policy 允许才可用。
- WorkspaceLease / WorkspaceSnapshot：**Research OS 拥有**（SDK 无对应面）；adapter 用容器生命周期 + git 状态（git_changes/git_diff）支撑快照语义。
- ExecutionBackend：受控测试路径经 workspace.execute_command；TIMED_OUT 由 adapter 显式实现（SDK 无命令级 timeout 语义，审计 §5 矩阵）；compute usage 需 M6 spike 验证（NEEDS_SPIKE 项）。

## 6. 安全承接清单（审计 §11 结论）

1. execute_tool 直通：PolicyWrappedToolExecutor 独占（AGENTS.md §5）。
2. resume 漂移：Manifest compatibility 检查在 adapter 外层（OpenHands 允许 resume 改变 LLM/context）。
3. LocalWorkspace host shell：默认 deny。
4. DockerWorkspace 网络：默认无隔离（network/enable_gpu 可选），Research OS 部署配置必须叠加网络策略。
5. 插件 pin：ResolvedPluginSource 仅 commit-SHA；Research OS digest 门禁需在引入插件时强制（升级为 digest pin 或拒绝引入）。
6. secrets：无 cipher 时持久化明文/丢失；Research OS CredentialResolver 密封语义保持，SDK Secret Registry 仅运行时注入通道。
7. 观测隐私：LLMCompletionLogEvent 含 LLM 输出，Research OS 遥测默认只记录 digest/usage（ADR-0020）。

## 7. Contract Suite 对接

UPSTREAM_COMPONENTS.yaml openhands_sdk controls 逐项映射：

| control | contract suite 检查项（M6） |
| --- | --- |
| pin_exact_version_before_adoption | tests/contracts 注册 OpenHandsRuntimeAdapter 时锁定 v1.42.0；升级走 Upgrade Gate |
| contract_tests | test_agent_runtime_contract.py 全套对真实 adapter 复用 |
| policy_wrap_direct_tool_execution | 新增 permission deny 测试：不经 Policy Wrapper 的 execute_tool 调用被拒 |
| manifest_check_on_resume | 新增 resume 漂移测试：Manifest 不匹配 → 拒绝或 Fork |
| freeze_session_tool_set | 新增 tool-set 冻结测试：resume 时工具名集合不一致 → 拒绝 |
| pin_plugin_revision | 新增插件 digest 校验测试 |

## 8. 不做的事（边界重申）

- 不把 OpenHands Conversation/Event 类型写入 Domain（AGENTS.md §6 Canonical State）。
- 不把 OpenHands 内部实现（litellm、fastmcp、EventLog 文件格式）反向影响 Port 契约。
- 不实现 OpenHands 特有语义（WAITING_FOR_CONFIRMATION 隐式确认等）到 Domain 的静默映射——每个映射在 adapter 内显式并有测试。