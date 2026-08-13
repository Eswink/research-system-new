# M5 Corrections Log — M5R 证据驱动修正记录

Phase: M5R
Date: 2026-08-12
Upstream evidence base: docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md
Port matrix: docs/references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md

## 结论

**零 M5 Port 结构修正。** M5 的 14 个 Port Contract 与 Fake Implementations 经真实
OpenHands SDK v1.42.0 源码与 6 个 executable spike 校验后，未发现需要修改
Port 契约、Domain 类型或 contract suite 的证据。（2026-08-12 独立复审复验：
结论成立；复审仅补齐 M5R 产物证据，见文末"独立复审补充修正"。）

## 评估过的候选修正（全部驳回，附理由）

| # | 候选 | 上游证据 | 驳回理由 |
| --- | --- | --- | --- |
| C1 | AgentRuntime.cancel 增加终态映射 | OpenHands `interrupt()` → PAUSED（可恢复），无终态 CANCELLED（`conversation/state.py::ConversationExecutionStatus`） | 差异在 adapter 映射层而非 Port 契约：Port 的"取消为协作式信号"语义与 OpenHands interrupt 一致；终态收敛是 M6 OpenHandsRuntimeAdapter 职责（见 M6_ADAPTER_DESIGN_NOTES.md），修改 Port 反而破坏 Fake 的领域状态机一致性 |
| C2 | WorkspaceBackend 增加 lease/snapshot 之外的接口 | OpenHands `BaseWorkspace` 无 lease/snapshot/identity（`workspace/base.py`） | 缺项恰好证明 Research OS 拥有这些职责正确（ADR-0006）；OpenHands 侧无对应面 = NOT_SUPPORTED，不属于 Port 过度/不足抽象 |
| C3 | ModelGateway 增加 capability 探测 | OpenHands `model_features.py` 依赖 litellm 元数据，中转站 + 非知名 model 时不可信 | M3 probe suite 已独立于 Port 存在；探测由 application use case 驱动，Port 保持最小调用面（D2/D3 决策不变） |
| C4 | ToolProvider 增加 permission 语义 | OpenHands confirmation 是 agent loop 层策略且 `execute_tool()` 可绕过 | 正是 Research OS PolicyEvaluator 外层强制的理由（AGENTS.md §5）；把 permission 塞进 ToolProvider 会造成职责扩散 |
| C5 | ExecutionBackend 与 WorkspaceBackend 合并 | OpenHands 把 execute_command 挂在 BaseWorkspace 上 | SWE-ReX 对照证明"命令执行独立于 workspace"是通用模式（官方定位 Disentangle agent logic from infrastructure concerns）；Research OS 拆分正确 |

## 验证证据

- 6 个 spike 全部以 mock credential 通过（S1-S6），无真实网络/凭据。
- 回归基线：m0 profile 18/18 PASS；pytest 732 passed；mypy 166 files
  Success；双 validator PASS（EV-00，本阶段新增文件不影响既有门禁——见下文
  回归复核）。

## 对 M6 的移交（非 M5 修正，属 adapter 设计承接）

1. cancel 语义映射：interrupt → Research OS 取消信号；PAUSED 状态收敛。
2. resume：Manifest compatibility 检查在 adapter 外层执行（OpenHands
   `ConversationState.create` open-or-create + `agent.verify`）。
3. 安全强制：execute_tool 必须包 Policy Wrapper；默认禁 LocalWorkspace
   host shell；DockerWorkspace 需叠加网络隔离；插件 commit-SHA pin 需升级为
   digest 门禁。

## 独立复审补充修正（2026-08-12，复审者独立重跑/重验后追加）

以下修正不改变"零 M5 Port 结构修正"结论，属 M5R 产物的证据补齐：

| # | 修正 | 证据 | 类型 |
| --- | --- | --- | --- |
| R1 | S5 spike 文件路径改为绝对路径并新增 CWD 泄漏断言 | 首版 S5 用相对目标路径，`LocalWorkspace.file_upload/file_download`（裸 Path，CWD 相对解析）把文件写到进程 CWD（仓库根目录 `spike.txt` 残留）；重跑实证 `cwd leak check: none` | spike 修复（tools/upstream-spikes/S5_local_workspace.py） |
| R2 | OPENHANDS_REVISION_LOCK.yaml sdist digest 修正 | 原记录 `e8be3e58…` 与 PyPI 实测 `4706ae2c…` 不符，且不属于 1.40.0/1.41.0/1.42.0 任何 sdist——抄录错误；已下载 sdist 实测修正。sdist 与 git tag v1.42.0 clone 内容文本级一致（llm.py/state.py/agent/base.py 0 diff） | revision lock 修正 |
| R3 | 审计 §8 补充 LocalWorkspace 文件 API 路径基准不一致（file_upload/download 裸 Path vs git_* working_dir 相对）；BaseWorkspace docstring 含过期 read_file 示例 | S5 重跑实证 + `workspace/local.py`/`workspace/base.py` 源码 | 审计文档补充 |
| R4 | M5 matrix §4 / M6 design notes §5 / risk register 增 R-17（路径解析差异） | 同上 | 文档同步 |
| R5 | M6_READINESS_REPORT contract 数量修正为实测 127 | `pytest tests/contracts` 实测 127 passed（原记 121 为早期口径） | 报告修正 |

## M6 实施增补（2026-08-13，M6 实现期间的 M5/M5R mismatch 记录）

M6 实现确认 M5 零结构修正结论成立；以下为实现过程发现并落地的
adapter 层承接与最小 Port 增补（不改变 Port 语义）：

| # | 发现 | 证据 | 处理 |
| --- | --- | --- | --- |
| M6-1 | `RuntimeEventKind` 缺少 message 投影（M5R 审计要求覆盖 message 但 Port 枚举无对应值） | `packages/application/ports/agent_runtime.py` 原枚举无 MESSAGE；OpenHands MessageEvent 是会话消息事件 | Port 增补 `MESSAGE = "message"`（最小必要修正；Fake 不产生该事件，contract suite 不受影响） |
| M6-2 | SDK 无 ConversationRunError 类；错误模型为事件驱动（ConversationErrorEvent + ErrorClassification 闭集 AUTH/QUOTA/RATE_LIMIT/CONFIG/TRANSIENT/AGENT_ACTION/INTERNAL/UNKNOWN） | PyPI 包 openhands-sdk==1.42.0 `event/conversation_error.py` + `event/error_classification.py`；run() 抛错路径为 `_emit_run_limit_error` 发事件 | error_mapping 按 ErrorClassification.kind 映射（M6_ADAPTER_DESIGN_NOTES §2 的\"ConversationRunError 双通道\"修正为事件驱动单通道 + 兜底异常） |
| M6-3 | 非知名 model + 自定义 base_url 时 litellm 无法推断 provider（`get_llm_provider` 抛错），S2 spike 未覆盖真实请求层 | S7 mock 端点实证：`relay-model` 无前缀请求被 litellm 拒绝 | llm_factory `resolve_runtime_model_name`：探测失败加 `openai/` 前缀（MVP 唯一协议 OPENAI_COMPATIBLE；变换只存在于 adapter） |
| M6-4 | `Agent.tools` 字段要求 `Tool` 对象（Pydantic 校验），不是字符串列表 | `agent/agent.py` `tools` 字段校验 + S7 实证 | runtime_adapter `_default_agent` 用 `tools_for_frozen_set` 装配 `Tool(name=...)` |
| M6-5 | SDK `ToolDefinition` 实例 name 自动推导（`__init_subclass__` snake_case），构造器不接受 name 参数 | `tool/tool.py` `name: ClassVar[str]` + `__init_subclass__` | 自定义工具类命名遵循 snake_case 推导（S3 模式）；frozen set 以推导名对齐 |

## 独立复审修正（2026-08-13，M6 完成后独立端到端复审）

复审以当前代码 + M5 契约 + pinned v1.42.0 源码为事实来源，发现并修复以下
缺陷（此前 RECHECK-20260813-007 判定 PASS 的依据不完整）：

| # | 严重度 | 发现 | 证据 | 处理 |
| --- | --- | --- | --- | --- |
| M6-6 | 阻断（DoD AC-04 未落地） | `PolicyWrappedToolExecutor` 仅单测实例化，未接入 adapter 主路径；SDK agent loop 内工具执行无 PolicyEvaluator 门禁（`execute_tool` 官方文档确认可绕过 confirmation/security） | `runtime_adapter.py` 无 policy_wrapper 引用；`conversation/impl/local_conversation.py::execute_tool` docstring；agent loop 执行链 `_execute_action_event` | 新增 `policy_enforcing_agent.py`（SDK Agent 子类覆写 `_execute_action_event`，DENY/REQUIRE_APPROVAL 不触达 executor；evaluator 经序列化安全注册表传递）；`execute_tool_gated` 独占直通面；策略门禁全链路测试 5 项 |
| M6-7 | 阻断（DoD AC-07 未落地） | `usage_entries_from_stats` 仅纯函数测试；`budget_ledger`/`usage_reporter` 只存字段从未调用，run() 后 ledger 无条目 | `runtime_adapter.py` 无 usage 引用；ledger 集成测试无 | run() 终态后经 `SessionBuilder.record_usage` 归一化写入 BudgetLedger（signal 语义，失败不阻断）；集成测试 3 项 |
| M6-8 | MAJOR | `fork()` 调用 `conversation.fork()` 无参，ForkSpec.model_override / tool_set_override / manifest_revision_ref 全部静默忽略 | SDK `fork(agent=...)` 签名（`local_conversation.py:713`）；M6_ADAPTER_DESIGN_NOTES §2 fork 映射要求 | `build_llm_for_fork` 注入点 + agent 重建（PolicyEnforcingAgent 保留门禁）；Fake 同步投影 override；测试 3 项 |
| M6-9 | MAJOR | 错误模型记录失真：M6-2 声称"SDK 无 ConversationRunError 类"；实测 `ConversationRunError` 存在（original_exception 保留原始异常），双通道错误模型成立 | `conversation/exceptions.py::ConversationRunError`；`run()` except 路径（`local_conversation.py:1997`） | `map_conversation_run_error`：事件分类优先，其次原始异常类型（LLMTimeoutError→TransientPortError 等）；run() 异常路径先投影事件再归一化；LLMContextWindowExceedError 等错误集成测试 4 项 |
| M6-10 | MAJOR | RuntimeEvent.message 未脱敏：ConversationErrorEvent.detail 含 API Key 时直接进入 SESSION_FAILED 事件消息 | 实测：LLM 异常消息含 `sk-...` 出现在事件 message | event_mapping 全部 message 构造经 `redact_exception_message`（domain redaction）；secret 不进事件/错误/结果测试 |
| M6-11 | MAJOR | 真实 adapter 从不产生 SESSION_STARTED（Fake 产生）——事件流不对称；错误事件重复风险：ConversationErrorEvent→SESSION_FAILED 与 `_finish` 追加重复 | 事件流实测 `[created, message, message, succeeded]` 无 started；`_finish` 无条件追加 | run() 首次驱动投影 SESSION_STARTED；`_finish` 对已投影终端 kind 去重（terminal_kinds_seen） |
| M6-12 | 注意 | 共享 contract suite 未断言中间事件（SESSION_STARTED/终端去重），掩盖 M6-11 | contract 只检查 kinds[0]/kinds[-1] | adapter 级测试补齐（事件流完整性 + 错误单次 SESSION_FAILED） |

复审后回归：pytest **840 passed**（含架构 8 项）；mypy strict 183 files
Success；ruff PASS；validate_bundle PASS；governance validate PASS；
依赖边界（lint-imports domain/relay）PASS。M5 Port 契约未发生结构性修正
（M6-6 至 M6-12 全部为 adapter 层修复，Fake 仅同步 fork override 投影）。