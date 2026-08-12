# M6 Readiness Report — OpenHands Runtime Integration

Phase: M5R
Date: 2026-08-12

## 最终裁决

- **M5R = PASS**
- **M6 OpenHands Runtime Integration readiness = READY**

前置条件：M6 实施须按 M6_ADAPTER_DESIGN_NOTES.md 承接 cancel/resume/安全映射，
并按 M6_RISK_REGISTER.md 缓解 R-01 至 R-16（无 BLOCK 级项）；UPSTREAM_COMPONENTS.yaml
openhands_sdk 由 PLANNED 转 ADOPTED 时补登记 resolution/license/upgrade_gate。

## 事实清单

| 项 | 值 |
| --- | --- |
| repository | https://github.com/OpenHands/software-agent-sdk |
| revision | v1.42.0 / commit `391fbb8d3c9cbc71212bb302669a0fd03e3dabfc`（release 2026-08-11） |
| license | MIT（`LICENSE`，Copyright (c) 2026 OpenHands contributors；无 NOTICE 文件） |
| PyPI | openhands-sdk==1.42.0（requires-python >=3.12；sdist sha256 见 revision lock） |
| clone 位置 | d:\upstream\openhands-software-agent-sdk（仓库外隔离；未修改、未 fork） |
| spike 环境 | d:\upstream\.venv-sdk（Python 3.12.13；SDK 不入 uv.lock，保持 PLANNED） |

## 关键源码路径（审计证据锚点）

- Agent：`openhands/sdk/agent/base.py`、`agent/agent.py`（stateless 配置；verify）
- Conversation：`conversation/impl/local_conversation.py`（run/pause/interrupt/fork）、
  `conversation/state.py`（ConversationExecutionStatus / open-or-create）
- LLM：`llm/llm.py`、`llm/utils/litellm_provider.py`、`llm/utils/model_features.py`
- Tool：`tool/tool.py`（ToolDefinition/execute_tool 后门在 conversation）、
  `tool/registry.py`、`tool/schema.py`
- MCP：`mcp/client.py`、`mcp/config.py`、`mcp/utils.py`（fastmcp + 凭据六策略）
- Workspace：`workspace/base.py`、`workspace/local.py`、`utils/command.py`
  （host shell 证据）；`openhands-workspace/.../docker/workspace.py`
- Events：`event/`（llm_convertible/、conversation_error.py、user_action.py、
  condenser.py）；`conversation/event_store.py`（EventLog 文件溯源）
- Context：`context/condenser/llm_summarizing_condenser.py`、`context/memory.py`
  （memory_context exclude=True）
- Persistence：`conversation/persistence_const.py`、`io/local.py`；
  agent-server `persistence/store.py`（文件存储，无 redis）
- Security：`security/`（confirmation_policy/risk/ensemble/defense_in_depth）、
  `secret/secrets.py`、`plugin/types.py`（commit-SHA pin，无 digest）

## Executed Spikes

| ID | 内容 | 结果 | Adapter 决策支撑 |
| --- | --- | --- | --- |
| S1 | import + 版本指纹 | PASS | 环境可行；状态枚举确认无 CANCELLED 终态 |
| S2 | LLM 三要素构造 / base_url 保留 / JSON 往返 / litellm kwargs | PASS | ModelGateway → LLM 映射直接可行（kwargs 无 api_base 字段，SDK 组装于请求层） |
| S3 | Agent+Conversation 建/run + 自定义工具注册 + 事件流（TestLLM） | PASS | create/run/stream_events 面验证；工具需 Tool spec + create() 返回 Sequence |
| S4 | interrupt/重复 run 语义 | PASS | interrupt 不改 FINISHED；重复 run 幂等返回同一终态——与 Fake 语义一致 |
| S5 | LocalWorkspace 文件/命令生命周期 | PASS | 文件走 upload/download 路径；execute_command 返回 CommandResult（含 timeout_occurred） |
| S6 | persistence/resume 往返（显式 conversation_id） | PASS | "Resumed conversation from persistent storage"；事件与状态完整恢复；未传 id 则新建会话 |
| — | 错误路径（真实 litellm 失败） | 观察 | ConversationRunError 包装 + ConversationErrorEvent + 持久化日志目录——双通道错误模型实证 |

每个 spike 以 mock credential 执行；无真实网络、无真实凭据、无高风险操作。

## Research OS Mapping 摘要

- AgentRuntime：ADAPTER_REQUIRED（cancel 语义 SHIM_REQUIRED）——Port 契约成立。
- ModelGateway：ADAPTER_REQUIRED（probe 由 M3 主导）。
- ToolProvider：ADAPTER_REQUIRED（permission 必须外层 Policy）。
- WorkspaceBackend：ADAPTER_REQUIRED（lease/snapshot Research OS 拥有）。
- ExecutionBackend：ADAPTER_REQUIRED（SWE-ReX 对照确认独立抽象是通用模式）。
- ArtifactStore / EventPublisher / PolicyEvaluator / CredentialResolver /
  MemoryStore / BudgetLedger / WorkflowEngine / EndpointStore /
  ResourceCatalog：RESEARCH_OS_OWNED（9/14 Port 完全自有）。
- 零 Port 结构性修正（M5_CORRECTIONS_LOG.md 记录了 5 项候选修正的驳回理由）。

## Remaining Uncertainty

1. DockerWorkspace 容器内链路（agent-server + X-Session-API-Key）未 spike（门控
   步骤，需用户确认后拉 sandbox 镜像）；R-05 缓解依赖部署配置。
2. ExecutionBackend compute usage 语义（NEEDS_SPIKE，矩阵 §5）。
3. SDK 周更频率下的版本稳定性（R-13）；revision lock 以 v1.42.0 为准。
4. Windows spike 环境与 Linux CI 的差异（R-14）；M6 需在 Linux 补跑。
5. MCP OAuth token storage（AsyncKeyValue）与 Research OS 持久化的对接细节未
   深读（审计 §7 缺口）。
6. `llm/auth/credentials.py`（订阅凭据）未深读，与 MVP 用户中转站无关。

## 结论

M5 的 14 个 Port Contract 与 Fake Implementations 经受住了真实 upstream 源码
与最小可执行实验的双重校验：无结构性缺陷，无"为像 OpenHands 而重写架构"
的需求；全部差异都有明确的 adapter 层承接路径。M6 可以按
M6_ADAPTER_DESIGN_NOTES.md 启动 OpenHandsRuntimeAdapter，并以 contract suite
（121 项 + M6 新增映射测试）为验收。

本阶段停止在 M6 边界；不自动开始 M6。