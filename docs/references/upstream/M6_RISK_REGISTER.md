# M6 Risk Register — OpenHands Runtime Integration

Phase: M5R
Date: 2026-08-12
Evidence base: docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md
Port matrix: docs/references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md

严重度：H(高) / M(中) / L(低)；可能性：H/M/L。缓解状态：OPEN（M6 前保持）/
ADAPTER（M6 adapter 承接）。

| ID | 风险 | 证据 | 严重度 | 可能性 | 缓解 | 状态 |
| --- | --- | --- | --- | --- | --- | --- |
| R-01 | cancel 语义错位：OpenHands interrupt → PAUSED（可恢复），Research OS 取消语义可能误映射为终态 | `local_conversation.py::interrupt`（line 2584）；`state.py::ConversationExecutionStatus` 无 CANCELLED；S4 spike 验证 interrupt 不改 FINISHED | H | H | adapter 显式映射 + contract suite 固化；Fake 的 cancel→CANCELLED 保持为 Port 契约 | ADAPTER |
| R-02 | resume 漂移：OpenHands 允许 resume 改变 LLM/context | `state.py::ConversationState.create` open-or-create + `agent.verify`（类 + 工具集）；AGENTS.md §5 | H | M | Manifest compatibility 检查在 adapter 外层；不匹配 → 拒绝或 Fork | ADAPTER |
| R-03 | execute_tool 直通绕过 Policy/Confirmation | `conversation/impl/local_conversation.py::execute_tool`（docstring 明言绕过） | H | H（若开放调用） | PolicyWrappedToolExecutor 独占；permission deny 测试 | ADAPTER |
| R-04 | LocalWorkspace host shell 无沙箱 | `utils/command.py:62-90` subprocess shell=True | H | M | 默认禁用 LocalWorkspace；显式配置 + Policy 允许 | ADAPTER |
| R-05 | DockerWorkspace 无默认网络隔离 | `openhands-workspace/.../docker/workspace.py`（network/enable_gpu 可选） | H | M | 部署配置叠加网络策略；预检检查隔离配置 | ADAPTER |
| R-06 | 插件 pin 无 digest（仅 commit SHA） | `plugin/types.py::ResolvedPluginSource` | M | M | Research OS 引入插件时强制 digest 门禁或拒绝 | ADAPTER |
| R-07 | litellm 类型/元数据泄漏进 Domain | `LLMResponse.raw_response`；`model_features.py` 依赖 litellm；`map_provider_exception` | M | M | LLM→Domain 转换全部在 adapter；ModelCompatibilityProfile 主导能力判定 | ADAPTER |
| R-08 | 中转站 + 非知名 model 时能力探测不可靠 | `litellm_provider.py::LLMProvider.from_model`（name=None 回落）；`model_features.py` | M | H | M3 probe suite 独立判定；不信任 litellm 探测结果 | ADAPTER |
| R-09 | max_output_tokens 默认 cap 16384 与预算冲突 | `llm.py::_init_model_info_and_caps` | L | M | adapter 装配 LLM 时显式设置 | ADAPTER |
| R-10 | condenser 摘要写回事件流成为派生真相 | `event/condenser.py::Condensation` 事件；`context/agent_context.py::memory_context exclude=True` | M | M | OpenHands 事件仅作 runtime 数据源；Domain 事实源保持 PostgreSQL | ADAPTER |
| R-11 | 无 cipher 时 secrets 明文/丢失持久化 | `state.py::_save_base_state`（line 421） | H | M | CredentialResolver 密封语义；SDK Secret Registry 仅运行时注入 | ADAPTER |
| R-12 | MCP 配置成为事实源风险 | `mcp/config.py::MCPServer`（settings DataModel，含 OAuth 凭据） | M | M | Research OS MCP registry 为 truth；coerce_mcp_config 做形状归一化 | ADAPTER |
| R-13 | 版本漂移（SDK 高频发布，v1.42.0 周更） | release v1.41.0→v1.42.0 间隔一天 | M | H | revision lock + Upgrade Gate；contract suite 验收 | OPEN |
| R-14 | Windows 平台差异（spike 环境 win32） | 本 M5R spike 均在 Windows 执行；LocalWorkspace 文件 API 签名与文档有出入 | L | M | M6 在 Linux CI 上补跑 spike/contract；差异记录于 spike 结论 | OPEN |
| R-15 | 重试叠加（SDK tenacity + Research OS 重试策略双重重试） | `retry_mixin.py`（5 次 8-64s） | M | M | M6 决策：保留 SDK 重试或外层统一，二选一 | ADAPTER |
| R-16 | `LLMCompletionLogEvent` 含 LLM 输出，遥测隐私 | `event/llm_completion_log.py` | M | M | ADR-0020 默认只记录 digest/usage | ADAPTER |
| R-17 | LocalWorkspace 文件 API 裸 Path（CWD 相对）解析，与 git_*（working_dir 相对）不一致；相对路径文件操作可能落在 workspace 根之外（污染宿主 CWD） | `workspace/local.py`（file_upload/file_download vs git_changes/git_diff）；S5 spike 重跑实证（首版相对路径产生 CWD 残留） | M | H | adapter 对所有文件路径显式绝对化 + 工作区根校验；默认禁用 LocalWorkspace 时风险收敛（R-04 同源） | ADAPTER |

## 汇总

- 高风险（H）7 项（R-01/02/03/04/05/11/17），全部有明确缓解路径且可在 adapter 层/部署层承接，无"必须改 Domain 架构才能解决"的项。
- 唯一 OPEN 项 R-13（版本漂移）由 revision lock + Upgrade Gate 流程覆盖（UPSTREAM_POLICY.md）。
- 独立复审新增 R-17（LocalWorkspace 文件 API 路径基准不一致），同 R-04 由 adapter 层承接；无阻断性风险（BLOCK 级）。