# M5 Corrections Log — M5R 证据驱动修正记录

Phase: M5R
Date: 2026-08-12
Upstream evidence base: docs/references/upstream/OPENHANDS_SOURCE_AUDIT.md
Port matrix: docs/references/upstream/M5_PORT_COMPATIBILITY_MATRIX.md

## 结论

**零代码修正。** M5 的 14 个 Port Contract 与 Fake Implementations 经真实
OpenHands SDK v1.42.0 源码与 6 个 executable spike 校验后，未发现需要修改
Port 契约、Domain 类型或 contract suite 的证据。

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