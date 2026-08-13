# OpenHands Software Agent SDK Source Audit — v1.42.0

Audit date: 2026-08-12
Repository: https://github.com/OpenHands/software-agent-sdk
Revision: v1.42.0 (commit `391fbb8d3c9cbc71212bb302669a0fd03e3dabfc`)
License: MIT (see `LICENSE`, Copyright (c) 2026 OpenHands contributors)
Clone: `d:\upstream\openhands-software-agent-sdk`（仓库外隔离，detached HEAD，未修改 upstream）

本文件是 M5R 源码级调查的权威汇总。所有结论均引用具体源码路径 / 符号 / 测试；
未确认项显式标注。调查覆盖 SDK 主包 `openhands-sdk`、工具包 `openhands-tools`、
工作区包 `openhands-workspace` 与 `openhands-agent-server`（均为 v1.42.0 工作区成员）。

---

## 1. Agent

### 结论

- Agent 是 Pydantic 冻结模型（`frozen=True`），类注释明确 "Agents are stateless and
  should be fully defined by their configuration"（`openhands/sdk/agent/base.py`）。
- 构造参数核心为 `llm`（必填）、`tools`、`mcp_config`、`condenser`、`critic`、
  `agent_context` 等（`AgentBase` / `Agent`）。
- 生命周期没有 start/stop；只有 `init_state`（首次调用时惰性初始化工具）与
  `close()`（清理 executor / ACP 子进程）。
- Agent 持有 LLM 和 Tool；**不持有 Workspace**——workspace 在 ConversationState 上，
  经 `agent.step(conversation, ...)` 传入。
- 内部不可替代状态全部是 `PrivateAttr`：`_tools` 工具表、`_tools_lock`、
  `_initialized`、`_parallel_executor`——即 runtime-private。
- 对外暴露：`tools_map`、`static_system_message`、`get_dynamic_context`、
  `get_all_llms`、`verify`（resume 兼容校验：agent 类一致 + 工具只增不删）。

### 证据

- `openhands/sdk/agent/base.py`：`AgentBase` docstring；`llm: LLM = Field(...)`；
  `verify()`（persisted vs runtime：类一致 + 工具不得移除）。
- `openhands/sdk/agent/agent.py`：`Agent`、`_parallel_executor: PrivateAttr`、
  `init_state`（发射 SystemPromptEvent）、`step/astep(conversation, on_event, on_token)`。
- `openhands/sdk/settings/model.py`：`OpenHandsAgentSettings(AgentSettingsBase)`，
  "fields here build the default Agent"。
- `openhands/sdk/profiles/agent_profile.py` + `profiles/resolver.py::resolve_agent_profile`
  （line 302）：AgentProfile 是持久化命名档案，`llm_profile_ref` 引用 LLM profile
  （不存凭据）。
- 测试：`tests/sdk/agent/test_agent_immutability.py`、`test_agent_serialization.py`、
  `test_agent_tool_init.py`。

### M5R 含义

- Agent 是"可重建配置"，无不可替代领域状态；Research OS 的 RoleDefinition/AgentSpec
  与其边界清晰：OpenHands Agent 完全可作为 adapter 层配置对象，不进 Domain。
- `verify()` 机制是 resume 时 Tool Set 冻结的官方支撑点（AGENTS.md §5 约束成立）。

## 2. Conversation / Session

### 结论

- `Conversation` 是工厂（`__new__`），按 workspace 类型分发到 `LocalConversation`
  （本地）或 `RemoteConversation`（WebSocket 连 agent-server）。
- 本地构造参数：agent（必填）、workspace、persistence_dir、conversation_id、
  callbacks、hook_config、max_iteration_per_run=500、stuck_detection 等。
- 消息输入是 `send_message()`（仅接受 role="user"）。
- `run()` 是**同步阻塞循环**直到 FINISHED/PAUSED/STUCK/WAITING_FOR_CONFIRMATION
  或超迭代；`arun()` 是异步等价物；**没有 start/join 分离**；resume 就是再次
  调用 run()（"Calling run() on an already paused agent will resume it"）。
- cancel：`interrupt()` 取消 `_arun_task`（CancelledError → PAUSED + InterruptEvent）；
  同步 run 时退化为 `pause()`（仅步骤间生效）。pause 不打断进行中的 LLM 调用。
- persistence：`ConversationState.create` open-or-create（base_state.json +
  events/ 目录），`agent.verify` 校验后恢复；无独立恢复 API。
- error：run 异常包装为 `ConversationRunError(RuntimeError)`；事件侧
  `ConversationErrorEvent`（code/detail/classification，不回流 LLM）。
- 完成没有显式 result 对象：完成 = `execution_status==FINISHED` + 事件流；
  `get_agent_final_response(events)` 辅助提取文本。

### 证据

- `openhands/sdk/conversation/conversation.py`：`Conversation.__new__` 工厂分发。
- `openhands/sdk/conversation/impl/local_conversation.py`：`__init__`（line 200）、
  `send_message`（line 1761，FINISHED/STUCK→IDLE 重置）、`run`（line 1857）、
  `arun`（line 2023）、`pause`（line 2559，"will not take effect until the current
  LLM call completes"）、`interrupt`（line 2584）、`fork`（line 713）。
- `openhands/sdk/conversation/state.py`：`ConversationState.create`（open-or-create；
  resume 路径 `agent.verify`）。
- `openhands/sdk/conversation/exceptions.py`：`ConversationRunError(RuntimeError)`。
- `openhands/sdk/conversation/response_utils.py::get_agent_final_response`（line 11）。
- 测试：`tests/sdk/conversation/local/test_agent_status_transition.py`、
  `test_conversation_pause_functionality.py`、`test_run_exception_includes_conversation_id.py`。

### M5R 含义

- OpenHands Conversation ≈ Research OS AgentSession + AgentRun 合并体：一次实例承载
  "会话状态 + 运行循环 + 事件历史 + 持久化"。
- 生命周期 mismatch：run 即整个生命周期；resume 是重新构造（conversation_id +
  persistence_dir）而非对象内恢复。
- cancellation mismatch：取消结果是 **PAUSED（可恢复）**，不是终态 CANCELLED；
  Research OS `AgentSessionState` 若含独立 cancelled 终态，必须显式映射
  （interrupt/pause → Research OS PAUSED，策略性取消 → 显式状态迁移）。

## 3. Events

### 结论

- 事件树根为 `Event`（Pydantic 冻结模型：id=UUID、timestamp、source∈
  {agent,user,environment,hook}、parent_id 树指针）；`LLMConvertibleEvent` 派生
  LLM 可见事件。
- 分类映射：agent 消息=MessageEvent(source=agent)；用户消息=MessageEvent(source=user)；
  工具调用=ActionEvent；工具结果=ObservationEvent；hook/用户拒绝=UserRejectObservation；
  工具错误=AgentErrorEvent（source=agent，LLM 可回流）；系统提示=SystemPromptEvent；
  运行级错误=ConversationErrorEvent（不回流 LLM）；状态同步=ConversationStateUpdateEvent；
  暂停/打断=PauseEvent/InterruptEvent；token 流=TokenEvent/StreamingDeltaEvent；
  压缩=Condensation/CondensationRequest/CondensationSummaryEvent；
  ACP 侧=ACPToolCallEvent；观测=HookExecutionEvent/LLMCompletionLogEvent。
- `types.py` 的 `EventType` 只是 `Literal["action","observation","message",
  "system_prompt","agent_error"]`，判别主要靠类层次，不是运行时枚举驱动。
- 序列化 = Pydantic JSON；存储 = EventLog 文件（`events/event-{idx:05d}-{id}.json`，
  进程安全锁），检索 = `state.events` / `path_to_root` / `active_branch` / `state.view`。

### 证据

- `openhands/sdk/event/base.py`、`event/types.py`、`event/llm_convertible/`
  （action.py:24 / message.py:25 / observation.py:32,86,138 / system.py:12）、
  `event/conversation_error.py:11`（"NOT sent back to the LLM"）、
  `event/user_action.py`、`event/token.py`、`event/streaming_delta.py`、
  `event/conversation_state.py:18`、`event/condenser.py`、`event/acp_tool_call.py:46`。
- `openhands/sdk/conversation/event_store.py`：EventLog 文件背靠背。
- 测试：`tests/sdk/event/test_event_serialization.py`、`test_events_to_messages.py`。

### M5R 含义

- OpenHands 事件是**持久化存储的单一树 + 类判别**，无独立 completion/cancellation
  事件类型；Research OS RuntimeEvent（归一化流式投影）必须自行定义映射。
- event mismatch 证据点：OpenHands event history 是文件事件日志，不是
  Research OS canonical audit truth（AGENTS.md §6 成立）。

## 4. 状态机

### 结论

- 状态枚举 `ConversationExecutionStatus`（`conversation/state.py`）：
  IDLE/RUNNING/PAUSED/WAITING_FOR_CONFIRMATION/FINISHED/ERROR/STUCK/DELETING；
  终态 = FINISHED/ERROR/STUCK。
- 迁移：run() 从 IDLE/PAUSED/ERROR/STUCK→RUNNING；WAITING_FOR_CONFIRMATION→RUNNING
  （下一次 run 即隐式确认）；send_message 把 FINISHED/STUCK→IDLE；
  pause() 仅 IDLE/RUNNING→PAUSED；interrupt→PAUSED；超迭代/异常→ERROR；
  stuck→STUCK；FinishTool→FINISHED。
- stuck 检测：`StuckDetector`（`conversation/stuck_detector.py`）4 个活跃模式
  （同 action+同 observation 重复、同 action 重复 error、agent 独白、交替 A/B 循环）
  + context-window 循环（TODO 恒 False）；扫描窗口 20 事件；命中即 STUCK 停循环。

### 证据

- `openhands/sdk/conversation/state.py`：`ConversationExecutionStatus` + `is_terminal`。
- `openhands/sdk/conversation/stuck_detector.py`：5 个 `_is_stuck_*` 方法。
- `openhands/sdk/conversation/impl/local_conversation.py::_check_stuck_or_nudge`（line 660）。
- 测试：`tests/sdk/conversation/local/test_agent_status_transition.py`（迁移矩阵）、
  `test_stuck_detector_nudge.py`。

### M5R 含义

- 状态枚举与 Research OS `AgentSessionState` 高度对应（IDLE/CREATED、RUNNING、
  PAUSED、STUCK、FAILED、SUCCEEDED），差异在 cancelled：OpenHands 无终态 CANCELLED。

## 5. LLM / 中转站

### 结论

- `LLM` 是 pydantic 模型：`model`（str，必填）、`api_key`（SecretStr）、
  `base_url`（str|None）；支持任意自定义 base_url（原样透传给 LiteLLM，
  仅 `https://api.openai.com` 会被置 None 让 LiteLLM 用默认）。
- model 标识变换：`openhands/` → `litellm_proxy/` 前缀 + 默认
  `https://llm-proxy.app.all-hands.dev`（`openhands_provider.py`）；
  `LLMProvider.from_model` 用 `litellm.get_llm_provider` 解析 provider，
  `api_base` 保留用户值原样。
- 重试：tenacity 指数退避，默认 5 次、8-64s、multiplier 8；只重试 6 类可恢复
  异常（APIConnectionError, RateLimitError, ServiceUnavailableError,
  LiteLLMTimeout, InternalServerError, LLMNoResponseError）。
- streaming：`streaming.py` TokenCallbackType；无 on_token 时降级非流式。
- tool calling：`mixins/non_native_fc.py`（非原生 tool calling 时 prompt mock +
  解析回 tool calls）；`mixins/fn_call_converter.py`（双向转换）。
- 结构化输出：**LLM 层无 response_format/json_object 参数**（全 sdk grep 无匹配）；
  结构化输出走 Tool 层 `response_schema`（合并进 tool schema 参数，模型在 tool
  call 里返回结构化字段）。
- usage：`utils/metrics.py::Metrics`（costs/latencies/token_usages）；
  `utils/telemetry.py`（litellm_completion_cost 算 cost）；
  `event/llm_completion_log.py::LLMCompletionLogEvent`。
- 错误：`llm/exceptions/`（LLMError 家族 + UserCancelled/OperationCancelled）；
  `classifier.py` 文本模式分类；`mapping.py::map_provider_exception` 映射 SDK 类型；
  `fallback_strategy.py` 与重试集相同异常集触发 fallback。
- 自定义 base_url + 非知名 model ID 时 provider 推断 name=None，能力探测回落
  fallback；`_init_model_info_and_caps` 对 max_output_tokens 强制 cap 到 16384。

### 证据

- `openhands/sdk/llm/llm.py`（model/api_key/base_url 字段；LLM_RETRY_EXCEPTIONS；
  `_make_retry_decorator`；`_coerce_inputs`；`_init_model_info_and_caps`）。
- `openhands/sdk/llm/utils/retry_mixin.py`（tenacity 封装）；
  `utils/litellm_provider.py::LLMProvider.from_model`、`as_litellm_call_kwargs`；
  `utils/openhands_provider.py::litellm_call_kwargs`、`canonicalize_openhands_llm_payload`；
  `utils/model_features.py`（能力探测）。
- `openhands/sdk/llm/streaming.py`；`llm/mixins/non_native_fc.py`、`fn_call_converter.py`。
- `openhands/sdk/tool/tool.py`（set_response_schema/_split_response_arguments/parse_response）。
- 测试：`tests/sdk/llm/test_llm.py`（test_llm_forwards_custom_base_url_as_is 等）、
  `tests/sdk/llm/test_litellm_provider.py`（test_llm_provider_keeps_requested_api_base_verbatim）。

### M5R 含义

- M3 的 LLMEndpoint/ModelDefinition/CompatibilityProfile 进入 adapter 可行：
  base_url/api_key/model 三要素直接映射。
- provider 类型泄漏风险：`LLMResponse.raw_response` 暴露 litellm 类型；
  异常分类依赖 litellm.exceptions 类型 + 文本启发式——LLM→Domain 转换必须在
  adapter 内完成；ModelCompatibilityProfile 必须主导能力判定，不能信任
  litellm 探测结果（中转站 + 非知名 model 场景）。

## 6. Tool

### 结论

- `ToolDefinition`：name/description/action_type/observation_type/annotations/
  executor/response_schema；必实现 `create()`；执行入口
  `__call__(action, conversation)` 返回 `Observation`（content + is_error）。
- JSON schema 由 `Schema.to_mcp_schema()` 生成（$ref/anyOf/循环引用处理）；
  MCP schema 反向 `from_mcp_schema()` 动态建 Pydantic 模型。
- 注册：进程级 `register_tool(name, instance|subclass)`（`tool/registry.py`）；
  `tool/spec.py::Tool`（name+params 延迟解析）。
- 确认机制**不在工具内部**，在 agent loop 层（confirmation_policy +
  security_analyzer）；`execute_tool()` 直接执行 API docstring 明言绕过
  agent loop、confirmation 与 security analyzer。
- built-in：Finish/Think（每 agent 默认）+ InvokeSkill/SwitchLLM/VisionInspect
  （条件附加）；openhands-tools 提供 terminal/file_editor/task_tracker 等。
- 自定义工具：registry 两种注册方式；`tool/client_tool.py`（纯 JSON spec）。

### 证据

- `openhands/sdk/tool/tool.py`（ToolDefinition/ToolExecutor/ToolAnnotations/
  DeclaredResources；`_get_tool_schema` 按 readOnlyHint 注入 security_risk）。
- `openhands/sdk/tool/schema.py`、`tool/registry.py`、`tool/spec.py`、`tool/defaults.py`、
  `tool/builtins/__init__.py`、`tool/client_tool.py`。
- `openhands/sdk/conversation/impl/local_conversation.py::execute_tool`
  （line 2958-2965："bypasses the agent loop, including confirmation policies and
  security analyzer checks"）；`conversation/base.py::execute_tool`（line 368）。
- `openhands/sdk/agent/agent.py::_requires_user_confirmation`（line 1015-1050）。
- 测试：`tests/sdk/tool/` 系列 + `examples/02_remote_agent_server/06_custom_tool`。

### M5R 含义

- ToolProvider/ToolSpec/ToolResolver 与 OpenHands 工具边界兼容（定义/注册/执行
  形态接近）；但 ToolAnnotations 仅是声明性 hint，confirmation 是 loop 层策略——
  Research OS Capability/Policy 必须在 OpenHands 外层强制执行，且必须封堵
  `execute_tool()` 直通路径（AGENTS.md §5 成立）。

## 7. MCP

### 结论

- 基于 **fastmcp**（`MCPClient` 继承 `fastmcp.Client`），非自研协议层。
- server 配置 `MCPServer`（settings DataModel）：url/transport（stdio|http|
  streamable-http|sse）/command/args/env/cwd/headers/auth/enabled；凭据完整
  （none/api_key/bearer/basic/header/oauth2 六种策略，SecretStr + cipher 加密，
  OAuth token storage 可插拔）。
- 发现：connect 后 `list_tools()` → `MCPToolDefinition.create`（动态 Schema，
  LRU 缓存 512）；订阅 `notifications/tools/list_changed` 增量对账
  （add/update/remove + 回调）。
- 生命周期：`create_mcp_tools()` 管理（连接/超时清理/sync_close；断开时
  MCPToolExecutor 自动重连一次）；MCP 工具调用的 action 中 `$VAR` secret 展开
  + 输出 masking。
- 错误：`MCPError/MCPTimeoutError` 或 `Observation(is_error=True)`。

### 证据

- `openhands/sdk/mcp/client.py`、`mcp/config.py`（MCPServer/MCPAuthCredential/
  coerce_mcp_config）、`mcp/utils.py`（create_mcp_tools/_connect_and_list_tools/
  _refresh_tools）、`mcp/tool.py`（MCPToolExecutor/MCPToolDefinition）、
  `mcp/exceptions.py`。
- 测试：`tests/sdk/mcp/test_create_mcp_tool.py`（http/sse/stdio、auth headers、
  timeout error message、skips disabled）、`test_mcp_tool_list_changed.py`、
  `test_mcp_secret_expansion.py`、`test_mcp_config_secrets.py`。

### M5R 含义

- MCP 配置是 adapter 层配置（settings DataModel 持久化用户配置），工具实例化在
  runtime materializer——不是 domain truth；Research OS ToolProvider(MCP) 适配时
  以自身 MCP registry 为 truth，用 coerce_mcp_config 形状归一化做转换。

## 8. Workspace

### 结论

- `BaseWorkspace` 接口：`execute_command` / `file_upload` / `file_download` /
  `git_changes` / `git_diff`；**无 read/write file 文本接口**；可选 pause/resume。
- `Workspace.__new__`：无 host → LocalWorkspace；有 host → RemoteWorkspace。
- **LocalWorkspace.execute_command 用 subprocess + shell=True（字符串命令）即
  直接 host shell，无沙箱**。
- Docker/隔离实现在独立包 `openhands-workspace`（DockerWorkspace/
  ApptainerWorkspace/OpenHandsCloudWorkspace/APIRemoteWorkspace）；SDK 主包无
  docker 实现；DockerWorkspace 无默认网络隔离（network/enable_gpu/extra_ports
  可选），容器内 agent-server 由 DockerWorkspace 以 HTTP API 消费。
- RemoteWorkspace 经 agent-server HTTP API（`/api/bash/start_bash_command` +
  轮询）执行命令；identity 仅 host/api_key/working_dir，无 workspace id。
- 生命周期：上下文管理器；DockerWorkspace 在 `model_post_init` 启动容器、
  `cleanup()`/`__del__` 停止删除；workspace 状态本身不跨会话保留。

### 证据

- `openhands/sdk/workspace/base.py`、`workspace/local.py`、
  `utils/command.py:62-90`（subprocess.Popen shell=True）、`workspace/workspace.py`、
  `workspace/remote/`（remote_workspace_mixin.py / base.py）、`workspace/repo.py`。
- `openhands-workspace/openhands/workspace/__init__.py`；`docker/workspace.py`
  （_start_container/cleanup/pause/resume）。
- 测试：`tests/sdk/workspace/test_local_workspace.py`、
  `tests/workspace/test_docker_workspace.py`、`test_workspace_pause_resume.py`。

### 独立复审补充（2026-08-12，S5 spike 重跑实证）

- **LocalWorkspace 文件 API 路径解析不一致**：`file_upload`/`file_download`
  （`workspace/local.py`）对参数做**裸 `Path()` 解析，不基于 `working_dir`**——
  相对路径落在进程 CWD；而 `git_changes`/`git_diff` 显式
  `Path(self.working_dir) / path` 基于 working_dir。S5 首版 spike 用相对目标
  路径时，文件往返实际发生在 CWD 而非 workspace（"roundtrip PASS"是假象），
  且残留 `spike.txt` 于仓库根目录；已改为绝对路径并新增 CWD 泄漏断言
  （`cwd leak check: none`）后重跑 PASS。
- `BaseWorkspace` docstring 示例含 `read_file`，但接口无 read/write 文本方法
  （`base.py` 仅 execute_command/file_upload/file_download/git_changes/git_diff），
  属 docstring 过期文本；审计结论"无 read/write 文本接口"不受影响。
- 含义：M6 WorkspaceBackend 适配时，文件路径必须由 adapter 显式归一化
  （绝对化 + 工作区根校验），不得信任相对路径解析；文件 API 与命令 API
  （cwd=working_dir）的路径基准不一致是 OpenHands 既有行为，不是 spike 错误。

### M5R 含义

- WorkspaceBackend/Workspace/WorkspaceLease/WorkspaceSnapshot 映射：OpenHands 只有
  接口层（BaseWorkspace）与容器生命周期（DockerWorkspace）；**lease/snapshot/
  identity 在 SDK 中不存在**，必须由 Research OS 外层定义（ADR-0006 成立）。
- LocalWorkspace = host shell 是高风险面：Research OS 默认 deny host shell 的
  安全策略必须在 adapter 层强制（默认配置禁止 LocalWorkspace 或强制 Docker/远程）。
- runtime-private：docker 容器文件系统、event log 均不提升为 Domain。

## 9. Context / Compaction

### 结论

- context 由 `AgentContext`（REPO_CONTEXT / available_skills / CUSTOM_SECRETS /
  MEMORY_CONTEXT）经 prompts section registry 渲染；`view/View` 是发给 LLM 的
  事件线性投影（manipulation_indices 保证 tool-call 原子性）。
- condenser 触发：`agent/utils.py::prepare_llm_messages` 每次 agent step 调用
  `condenser.condense(view, agent_llm=llm)`；`LLMSummarizingCondenser` 阈值
  max_size（默认 240，标准默认 80）/max_tokens（HARD/SOFT）；用独立 LLM 把遗忘段
  摘要成 `Condensation` 事件写回历史；`Conversation.condense()` 显式强制压缩。
- runtime private memory：`context/memory.py::load_memory` 读
  `~/.openhands/memory/MEMORY.md` 与 `<workspace>/.openhands/memory/MEMORY.md`
  （6000 字符预算），由 LocalConversation 惰性解析进
  `AgentContext.memory_context`，字段 `exclude=True` **不序列化**。

### 证据

- `openhands/sdk/context/agent_context.py`（memory_context exclude=True）、
  `context/view/view.py`、`context/condenser/base.py`（CondensationRequirement
  HARD/SOFT）、`context/condenser/llm_summarizing_condenser.py`（Reason
  REQUEST/TOKENS/EVENTS、max_size=240、keep_first=2、minimum_progress=0.1、
  default_condenser max_size=80/keep_first=4）、`context/memory.py`。
- `openhands/sdk/agent/utils.py:621`（condensation 调用点）。
- 测试：`tests/sdk/context/condenser/test_llm_summarizing_condenser.py`、
  `test_rolling_condenser.py`。

### M5R 含义

- OpenHands View+Condensation 是**发给 LLM 的输入投影**（可丢弃、可重建、含摘要
  副作用），与 Research OS ContextSnapshot（不可变业务事实）不同类；condenser
  摘要写回事件流属运行时派生数据，不得进入 canonical。

## 10. Persistence

### 结论

- conversation 持久化是**文件事件溯源**：`<base>/<conversation_id.hex>/` 内含
  `base_state.json`（ConversationState 快照；secrets 有 cipher 则加密、无 cipher
  则脱敏丢弃）+ `events/event-{idx:05d}-{id}.json`（每事件一文件，EventLog 带
  `.eventlog.lock` 文件锁，支持跨进程追加与恢复）。
- 无显式 save/load API：`ConversationState.create()` 是 open-or-create 工厂；
  事件随 append 即时落盘。
- agent-server 持久化也是纯文件：FileSettingsStore/FileSecretsStore/
  FileWorkspacesStore（settings.json/secrets.json/workspaces.json，0o600/0o700、
  原子写、文件锁、可选 OH_SECRET_KEY 加密），conversation 存
  `workspace/conversations/` + `meta.json`；**无 redis**。
- 无 schema 约束 / 无事务 / 无关系完整性 / 无审计。

### 证据

- `openhands/sdk/conversation/persistence_const.py`（BASE_STATE/EVENTS_DIR/
  EVENT_FILE_PATTERN）、`conversation/event_store.py`（EventLog）、
  `conversation/state.py::_save_base_state`（line 421）/`create`（line 445）。
- `openhands/sdk/io/local.py`（LocalFileStore commonpath 防逃逸 + FileLock）、
  `io/memory.py`、`io/cache.py`。
- `openhands-agent-server/.../persistence/store.py`（FileSettingsStore 等 +
  _credential_versions 凭据版本轮换）、`config.py:245`（conversations_path）、
  `event_service.py:162/224`（meta.json）。
- 测试：`tests/sdk/io/test_filestore_cache.py`、`test_local_filestore_security.py`。

### M5R 含义

- 直接支撑 "OpenHands persistence ≠ Research OS canonical PostgreSQL state"：
  文件事件日志无 schema/事务/审计，且 secrets 无 cipher 时明文或丢失。
  Research OS PostgreSQL Domain Entity 保持唯一业务真相（AGENTS.md §6 成立）。

## 11. Security / Credential

### 结论

- secret 模型：`StaticSecret`（SecretStr）与 `LookupSecret`（URL 懒拉取，SDK 不
  接触明文，由 agent-server `/api/settings/secrets/{name}` 解析）；序列化走
  `serialize_secret`（cipher 加密或 `**********` 脱敏）；注入 = 渲染进
  `<CUSTOM_SECRETS>` 提示块 +（ACP 时）子进程 env。
- 确认机制：`SecurityAnalyzerBase.security_risk(ActionEvent) → SecurityRisk`
  （HIGH/MEDIUM/LOW/UNKNOWN）；`should_require_confirmation`（HIGH 恒确认；
  UNKNOWN 无 analyzer 时确认）；策略 `AlwaysConfirm/NeverConfirm/ConfirmRisky`；
  settings `confirmation_mode` + `security_analyzer` 映射。
- 本地分析器：PatternSecurityAnalyzer（正则双语料）、PolicyRailSecurityAnalyzer
  （fetch-to-exec/raw-disk-op/catastrophic-delete 三条 rail→HIGH）、
  EnsembleSecurityAnalyzer（max、fail-closed HIGH）；LLM 类：LLMSecurityAnalyzer、
  ToolShieldLLMSecurityAnalyzer（可选 toolshield 包，MCP 安全入口）。
- shell 安全：`shell_parser.py`（tree-sitter-bash）+ `_shell_ast.py`（AST 视图）。
- 插件：`PluginSource(source, ref, repo_path)` → `Plugin.fetch`（git clone 到
  `~/.openhands/cache/plugins/`，可 pin branch/tag/commit）；
  `ResolvedPluginSource.resolved_ref` 是解析后的 commit SHA——**可 pin commit，
  无 digest 校验**；repo_path 校验防 `..` 穿越。
- hooks：PreToolUse/PostToolUse/UserPromptSubmit/SessionStart/End/Stop 事件点
  运行子进程 hook，可 block action。
- 外部进程边界：`Conversation.execute_tool()` 显式绕过 confirmation policy 与
  security analyzer。

### 证据

- `openhands/sdk/secret/secrets.py`、`context/agent_context.py`
  （_decrypt_secrets/_serialize_secrets）、`security/risk.py`、`security/analyzer.py`、
  `security/confirmation_policy.py`、`security/ensemble.py`、
  `security/defense_in_depth/policy_rails.py`、`security/shell_parser.py`、
  `security/_shell_ast.py`、`security/toolshield_helpers.py`。
- `openhands/sdk/settings/model.py:1024-1138`（confirmation_mode/security_analyzer）。
- `openhands/sdk/plugin/types.py`（PluginSource/ResolvedPluginSource）、
  `plugin/plugin.py`、`plugin/source.py`（resolve_source_path）。
- `openhands/sdk/hooks/conversation_hooks.py`（HookEventProcessor._handle_pre_tool_use）。
- `openhands-workspace/.../docker/workspace.py`（network/enable_gpu/extra_ports）。
- 测试：`tests/sdk/security/test_confirmation_policy.py`、`test_security_risk.py`、
  `defense_in_depth/test_policy_rails.py`、`test_adversarial.py`、
  `test_shell_parser_bypasses.py`、`test_ensemble.py`。

### M5R 含义

- 可复用：SecurityRisk/ConfirmRisky/Ensemble/defense_in_depth rails/shell AST
  可作为 Research OS Policy 层输入参考。
- 必须外层强制：`execute_tool()` 直通（Policy Wrapper）、LocalWorkspace host
  shell（默认 deny）、DockerWorkspace 无默认网络隔离、插件 pin 无 digest
  （Research OS 门禁要求 digest）、secrets 无 cipher 时明文/丢失
  （Research OS CredentialResolver 保持密封语义）。
- 未确认项：SDK 内未发现 MCP 专用安全模块（MCP 安全仅经 toolshield
  safety_experiences_for_mcp_config 与 settings mcp_config 承载）。

## 12. 跨领域未确认项

- `remote_conversation.py` 的 run 细节（REST+WebSocket 双通道）只做了方法定位，
  未全文读；`goal/` 与 `visualizer/` 未深入（与 Port 校验无关）。
- agent-server 是否在特定部署（如 Cloud）使用外部存储未在仓库源码确认
  （仓库内只有文件存储）。
- `llm/auth/credentials.py` 细节未深读（订阅凭据存储，owner-only 权限）。

## 13. 对照 upstream 说明

### SWE-ReX（README 级对照，2026-08-12）

对照问题："命令执行挂 workspace（OpenHands 设计）vs 独立 ExecutionBackend
（Research OS 设计）是 OpenHands 特有还是通用模式？"

结论：**通用模式是独立抽象**。SWE-ReX 官方定位为 "runtime interface for
interacting with sandboxed shell environments"，核心价值是
"Disentangle agent logic from infrastructure concerns"，支持本地 / Docker /
远程 / 并行 shell 会话，agent 代码不感知执行后端。OpenHands 把 execute_command
作为 BaseWorkspace 接口方法属其特有设计（workspace 同时承载文件与命令）。
这支撑 Research OS ExecutionBackend 独立 Port 的边界（Port 抽象成立）。

Source: https://github.com/SWE-agent/SWE-ReX（官方 README，MIT，registry 中
decision_status: OPTIONAL）

### Cline SDK

未纳入对照：Cline 在 UPSTREAM_COMPONENTS.yaml 中为 REFERENCE_ONLY（task
worktree 参考），非 Agent Runtime；本阶段 Runtime/Execution 抽象问题已由
SWE-ReX 对照回答，无需额外对照。