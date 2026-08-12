# M5 Port Compatibility Matrix — M5R 现实校验结果

Phase: M5R
Date: 2026-08-12
Upstream: OpenHands Software Agent SDK v1.42.0 (391fbb8d)
Evidence base: docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md

标记语义：
- DIRECT_MAPPING：OpenHands 存在直接对应面，adapter 可薄映射。
- ADAPTER_REQUIRED：需要 adapter 做显式转换/归一化。
- SHIM_REQUIRED：需要补丁层/兼容层，语义不完全对应。
- RESEARCH_OS_OWNED：职责必须由 Research OS 持有，不得委托 upstream。
- NOT_SUPPORTED：OpenHands 无此能力。
- NEEDS_SPIKE：静态源码不足以定论，需 executable spike 验证。

## 1. AgentRuntime

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| create_session | ADAPTER_REQUIRED | `conversation/conversation.py::Conversation.__new__` 工厂；`local_conversation.py::__init__` | AgentSessionSpec → agent + workspace + persistence_dir 映射 |
| run（同步阻塞） | DIRECT_MAPPING | `local_conversation.py::run`（line 1857） | run 即整个生命周期；与 Port 同步语义（D2）兼容 |
| pause | DIRECT_MAPPING | `local_conversation.py::pause`（line 2559） | 步骤边界生效，不打断进行中 LLM 调用 |
| cancel | SHIM_REQUIRED | `local_conversation.py::interrupt`（line 2584） | interrupt 结果为 **PAUSED（可恢复）**，非终态 CANCELLED；Research OS 取消语义需显式映射（协作式信号 → interrupt；策略性终止 → 状态迁移） |
| stream_events | ADAPTER_REQUIRED | `event/` 树 + `conversation/event_store.py::EventLog` | OpenHands 事件树（ActionEvent/ObservationEvent/AgentErrorEvent…）→ RuntimeEvent 归一化 |
| fork | ADAPTER_REQUIRED | `local_conversation.py::fork`（line 713） | ForkSpec（model/tool_set override + manifest_revision_ref）需在 adapter 内实现语义 |
| 状态 | SHIM_REQUIRED | `conversation/state.py::ConversationExecutionStatus` | IDLE/RUNNING/PAUSED/WAITING_FOR_CONFIRMATION/FINISHED/ERROR/STUCK/DELETING；**无终态 CANCELLED**；WAITING_FOR_CONFIRMATION 需映射 APPROVAL 态 |
| resume | ADAPTER_REQUIRED | `conversation/state.py::ConversationState.create`（open-or-create）+ `agent.verify` | resume = 重新构造（conversation_id + persistence_dir）；Manifest compatibility 由 Research OS 外层执行（AGENTS.md §5） |

结论：AgentRuntime Port 边界成立；cancellation 语义是主要 mismatch，需在 M6
adapter 中映射并在 contract suite 中固化（取消是协作式信号，OpenHands
interrupt 语义为"可恢复暂停"）。

## 2. ModelGateway

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| complete | ADAPTER_REQUIRED | `llm/llm.py::completion/acompletion/responses/aresponses` | LLMResponse.raw_response 暴露 litellm 类型，必须 adapter 内转换 |
| list_models | NOT_SUPPORTED | `llm/llm_registry.py` | SDK 无 `/models` 等价面；Research OS 侧 `/models` 由 relay adapter 提供（M3） |
| probe | SHIM_REQUIRED | `llm/utils/model_features.py::get_features` | 能力探测依赖 litellm 元数据 + 硬编码清单；中转站 + 非知名 model 时回落 fallback，不可信；Research OS ModelCompatibilityProfile 主导 |

结论：ModelGateway 是 Research OS 对外 LLM 面，OpenHands LLM 是 adapter 内部
对象；LLMEndpoint/ModelDefinition 映射可行（base_url/api_key/model 三要素），
但能力判定必须由 Research OS 侧主导（M3 probe suite 保持独立）。

## 3. ToolProvider

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| 执行 ToolCallRecord | ADAPTER_REQUIRED | `tool/tool.py::ToolDefinition.__call__` → Observation | 归一化 ToolResultRecord（digest 存内容）需 adapter 转换 |
| 工具定义/schema | DIRECT_MAPPING | `tool/spec.py::Tool` + `tool/schema.py::Schema.to_mcp_schema` | JSON schema 形态兼容 |
| 注册 | ADAPTER_REQUIRED | `tool/registry.py::register_tool` | 进程级注册；Research OS frozen tool set 由调用方约束 |
| direct execute 封堵 | RESEARCH_OS_OWNED | `conversation/impl/local_conversation.py::execute_tool`（docstring 明言绕过 loop/confirmation/security） | 必须 Policy Wrapper 包一层（AGENTS.md §5） |
| permission | RESEARCH_OS_OWNED | `agent/agent.py::_requires_user_confirmation`；`security/confirmation_policy.py` | OpenHands confirmation 是 loop 层策略且可被 execute_tool 绕过；Research OS Capability/Policy 必须在外层 |

结论：ToolProvider Port 边界成立；permission/confirmation 不得委托 OpenHands
（其确认策略是 agent loop 内部行为，且存在直通后门）。

## 4. WorkspaceBackend

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| workspace 创建 | ADAPTER_REQUIRED | `workspace/workspace.py::Workspace.__new__`（local/remote 分流）；`openhands-workspace` DockerWorkspace | LocalWorkspace 是 host shell（无沙箱）；Research OS 默认 deny host shell 需 adapter 强制 |
| Lease | NOT_SUPPORTED | 无 lease 概念 | WorkspaceLease 必须 Research OS 拥有（ADR-0006 成立） |
| Snapshot | NOT_SUPPORTED | 无 snapshot 语义 | WorkspaceSnapshot 必须 Research OS 拥有 |
| 文件/shell | ADAPTER_REQUIRED | `workspace/base.py::BaseWorkspace`（execute_command/file_upload/file_download/git_*） | 无 read/write 文本接口；文件走 upload/download |
| cleanup | DIRECT_MAPPING | DockerWorkspace.cleanup()/`__del__` | 容器生命周期 |

结论：WorkspaceBackend 抽象成立但 OpenHands 侧缺失 lease/snapshot/identity；
这些必须由 Research OS 拥有（ADAPTER_REQUIRED + RESEARCH_OS_OWNED）。

## 5. ExecutionBackend

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| 执行 ExecutionSpec | ADAPTER_REQUIRED | `workspace/base.py::execute_command`；`utils/command.py:62-90`（subprocess shell=True） | 命令执行走 workspace；ExecutionBackend 作为独立 Port 需要 adapter 层映射 |
| timeout | SHIM_REQUIRED | `local_conversation.py::run` 迭代上限；无命令级 timeout 语义 | ExecutionStatus.TIMED_OUT 需要 Research OS 侧驱动（adapter 内实现超时） |
| compute usage | NEEDS_SPIKE | `event/llm_completion_log.py::LLMCompletionLogEvent`（LLM 用量） | 命令级 compute usage 需 spike 验证 |

结论：ExecutionBackend 与 OpenHands 边界模糊（OpenHands 无独立执行后端，
命令走 workspace）；M6 可复用 ExecutionBackend 于受控测试路径，Timeout 需
adapter 显式实现。

## 6. ArtifactStore

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| 内容寻址 put/get | RESEARCH_OS_OWNED | OpenHands 无 artifact store | 无对应面；Research OS ArtifactStore 保持独立（事实源划分见 DATA_LIFECYCLE.md） |
| digest 校验 / 状态流转 | RESEARCH_OS_OWNED | 同上 | 同上 |

结论：ArtifactStore 完全 Research OS 拥有，OpenHands 不提供任何等价物；
Adapter 只负责把工具输出转为 artifact 引用。

## 7. EventPublisher

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| publish(EventEnvelope) | RESEARCH_OS_OWNED | OpenHands 事件是文件事件日志（`event_store.py::EventLog`） | Research OS Domain Event 独立于 OpenHands 事件树；M6 用 EventLog 作为 runtime event 源，不做 canonical |
| event_id 幂等 | RESEARCH_OS_OWNED | 同上 | 同上 |

结论：EventPublisher 完全 Research OS 拥有；OpenHands 事件历史是 runtime
派生数据，不是 canonical audit truth（AGENTS.md §6）。

## 8. PolicyEvaluator

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| evaluate → ALLOW/DENY/REQUIRE_APPROVAL | ADAPTER_REQUIRED | `security/confirmation_policy.py`；`security/risk.py::SecurityRisk`；`security/analyzer.py` | OpenHands SecurityRisk/ConfirmRisky/Ensemble 可作为 Policy 层输入，但决策由 Research OS PolicyEvaluator 做出 |
| 决策 deterministic | RESEARCH_OS_OWNED | `security/ensemble.py` fail-closed HIGH | OpenHands 含 LLM analyzer（非 deterministic）；Research OS 默认 NativePolicyEvaluator（ADR-0018） |

结论：PolicyEvaluator 是 Research OS 决策点；OpenHands 安全分析器是可选的
风险信号源，不是决策者。

## 9. CredentialResolver

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| resolve(ref) → SecretValue | RESEARCH_OS_OWNED | `secret/secrets.py::StaticSecret/LookupSecret`；`context/agent_context.py::serialize_secret` | OpenHands secrets 是提示块注入 + 懒加载；无 cipher 时持久化明文/丢失；Research OS CredentialResolver 密封语义保持 |
| 脱敏 | ADAPTER_REQUIRED | `utils/redact.py`；serialize_secret `**********` | 可作为 adapter 内辅助 |

结论：CredentialResolver 完全 Research OS 拥有；Secret 注入 OpenHands 只做
运行时提示块（M6 中凭据按 scope 注入，OpenHands Secret Registry 不是 vault）。

## 10. MemoryStore

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| commit(MemoryWriteProposal) | RESEARCH_OS_OWNED | `context/memory.py::load_memory`（MEMORY.md 6000 字符预算，exclude=True 不持久化） | OpenHands memory 是会话级提示注入，无 provenance gate；Research OS MemoryStore 完全独立 |
| provenance gate | RESEARCH_OS_OWNED | 同上 | 同上 |

结论：MemoryStore 完全 Research OS 拥有（ADR-0017）；OpenHands memory_context
是 runtime-private（官方 exclude=True），不提升为 Domain。

## 11. BudgetLedger

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| reserve/record_usage/snapshot | RESEARCH_OS_OWNED | OpenHands 无 budget ledger；仅 `llm/utils/metrics.py::Metrics`（用量采集） | 用量原始数据可从 OpenHands 采集，归账/记账 Research OS 拥有 |

结论：BudgetLedger 完全 Research OS 拥有；OpenHands Metrics 是原始用量源
（adapter 上报）。

## 12. WorkflowEngine

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| 任务分发/lease/取消传播 | RESEARCH_OS_OWNED | OpenHands 无 workflow 概念 | 无对应面；Research OS WorkflowEngine 完全独立（M7） |

结论：WorkflowEngine 完全 Research OS 拥有。

## 13. EndpointStore（收编）

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| LLMEndpoint CRUD | RESEARCH_OS_OWNED | OpenHands 无 endpoint CRUD（LLMProfile 是命名档案） | Research OS 拥有；OpenHands LLM 对象是 adapter 装配产物 |

结论：EndpointStore 完全 Research OS 拥有。

## 14. ResourceCatalog（收编）

| 契约面 | 标记 | 证据 | 说明 |
| --- | --- | --- | --- |
| preflight 只读目录 | RESEARCH_OS_OWNED | OpenHands 无等价物 | 完全 Research OS 拥有 |

结论：ResourceCatalog 完全 Research OS 拥有。

## 汇总

| Port | 判定 |
| --- | --- |
| AgentRuntime | ADAPTER_REQUIRED（cancel 语义 SHIM_REQUIRED） |
| ModelGateway | ADAPTER_REQUIRED（probe SHIM_REQUIRED） |
| ToolProvider | ADAPTER_REQUIRED（permission RESEARCH_OS_OWNED） |
| WorkspaceBackend | ADAPTER_REQUIRED（lease/snapshot NOT_SUPPORTED → Research OS 拥有） |
| ExecutionBackend | ADAPTER_REQUIRED（timeout SHIM_REQUIRED，compute usage NEEDS_SPIKE） |
| ArtifactStore | RESEARCH_OS_OWNED |
| EventPublisher | RESEARCH_OS_OWNED |
| PolicyEvaluator | RESEARCH_OS_OWNED（OpenHands 分析器为可选信号源） |
| CredentialResolver | RESEARCH_OS_OWNED |
| MemoryStore | RESEARCH_OS_OWNED |
| BudgetLedger | RESEARCH_OS_OWNED |
| WorkflowEngine | RESEARCH_OS_OWNED |
| EndpointStore | RESEARCH_OS_OWNED |
| ResourceCatalog | RESEARCH_OS_OWNED |

关键 mismatch 清单：
1. cancellation：OpenHands interrupt → PAUSED（可恢复），无终态 CANCELLED；
   Research OS 取消语义需显式映射（Fake 的 cancel→CANCELLED 保持为 Port 契约，
   adapter 内把中断映射为取消后的状态收敛）。
2. resume：OpenHands 是重新构造（conversation_id + persistence_dir），
   AgentSession 内无对象级恢复；Manifest compatibility 必须 Research OS 外层。
3. event：OpenHands 事件树与 RuntimeEvent 无 1:1；无独立 completion/cancellation
   事件类型；归一化是 adapter 职责。
4. error：OpenHands 双通道（ConversationRunError + ConversationErrorEvent +
   AgentErrorEvent），code 是字符串非枚举；重试语义在 classification 闭集。
5. 安全：execute_tool 直通、LocalWorkspace host shell、DockerWorkspace 无默认
   网络隔离、插件 pin 无 digest——全部必须 Research OS 外层强制。
6. Port 抽象检查：无 God Interface 证据；AgentRuntime 接口面与 OpenHands
   Conversation 面匹配良好；WorkspaceBackend 缺 lease/snapshot 属"抽象不足"，
   但由 Research OS 拥有（非 upstream 缺失导致 Domain 变化）。

无需 M5 结构性修正；M6 adapter 设计承接上述映射。