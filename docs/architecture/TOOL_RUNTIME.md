# Tool Runtime v0.4.0

## 1. 分层

```text
Role/Agent
→ Skill
→ Capability
→ ToolResolver
→ ToolSpec
→ ToolProvider
```

## 2. Tool Effect Class

每个 Tool 标注：

```text
READ_ONLY
WRITE
EXECUTE
NETWORK
SECRET_USE
DESTRUCTIVE
EXTERNAL_PUBLISH
```

Effect Class 影响审批、Workspace、审计和重试。

## 3. Effective Tool Set

```text
Role requested capabilities
+ Agent override
∩ Project policy
∩ Phase policy
∩ Autonomy level
∩ WorkspaceLease
∩ Provider health
∩ Credential scope
=
Effective Tool Set
```

AgentSession 启动后冻结 Tool Set。

如需改变 Tool Set，默认新建 Session 或 Fork。

**实现现状与判据（GOAL-20260919-007 EC-05，2026-09-19 实测）**：

- 「冻结」今天由三层证据支撑：`AgentSessionSpec` 是 frozen dataclass（就地写即抛）、
  生产源码里没有给会话条目重新赋 `spec` / `conversation` 的语句（AST 判据）、SDK 侧
  agent 的工具列表在装配时按冻结集构造后本仓不再写它。
- 「改变 Tool Set」的**唯一**实现路径是 fork，且已加窄门：`ForkSpec.tool_set_override`
  必须同时声明 `manifest_revision_ref`，否则两个实现（真实 adapter 与 Fake）都拒绝
  （`InvalidInputError`，消息点名缺哪条事实）。声明 revision 后 override 真的重建工具集
  ——不是只写进记录。
- **尚未落地**（如实登记，不声称覆盖）：上式的 `∩ Project policy ∩ Provider health ∩
  Credential scope` 交集在生产**未实现**；生产冻结集是
  `session_resolution.flatten_tool_providers(plan)` 的 **tool provider id 并集**。
  `tool_plane/resolver.py::freeze_tool_set` 与 `execution.py::require_frozen_tool_set`
  今天只有测试调用（`docs/audits/SYSTEM_REAUDIT_SA1R_M12_GATE.md` 的 S-FIND-01/03/04
  同口径）。
- **语义错配（登记）**：执行期门禁用 **SDK tool name** 当 capability 求值
  （`policy_wrapper` / `PolicyEnforcingAgent`），而 exposure-time 用的是 Research OS
  capability 词表；叠加 `scope=session_id` 与 `policy.yaml` 的精确 scope 匹配，带 scope
  的 allow 规则不会命中会话级请求 ⇒ 落到 `default_effect: DENY`（fail-closed，安全侧）。
  补 `tool.*` capability 词表属**核心安全策略**变更，不在 EC-05 射程。

## 4. Provider Types

```text
NATIVE
MCP
REST
CLI
REMOTE_WORKER
```

## 5. ToolPack

```text
ToolPackManifest
├ id/version
├ source
├ digest/signature
├ license
├ tools
├ skills
├ MCP config
├ requested permissions
└ compatibility
```

安装前执行供应链验证。

## 6. Double Enforcement

### Exposure-time
只暴露允许的 Tool Schema。

### Execution-time
调用前重新检查：

- capability
- scope
- arguments
- budget
- credential
- network
- timeout
- idempotency
- risk/gate

四个执行面语义对齐（use case `execute_tool_call`、OpenHands agent loop
`PolicyEnforcingAgent`、OpenHands direct `PolicyWrappedToolExecutor`、
resolver fail-closed）：

- `DENY` → 阻断（POLICY_DENIED），不触达 provider；
- `REQUIRE_APPROVAL` → 阻断（APPROVAL_REJECTED），审批通道接通前
  不得静默放行；
- `ALLOW` / `ALLOW_WITH_CONSTRAINTS` → 执行（约束由调用方落实）。

Resolver 面 fail-closed：无显式 per-capability 决策时按 DENY 处理，
`default_decision=ALLOW` 不是解析面放行依据。

## 7. Large Results

Tool 返回：

```text
summary
structured_data_ref
artifact_refs
logs_ref
provenance
continuation_hint
```

大结果不直接塞进模型上下文。

## 8. OpenHands Direct Tool Execution

任何绕过 Agent loop 的直接工具执行都必须先经过 Research OS Policy Wrapper。

禁止业务代码直接调用高风险 `execute_tool()`。

**判据（GOAL-20260919-007 EC-05）**：生产源码里**唯一**提及 SDK 直达执行点
（`conversation.execute_tool`）的地方是 `adapters/openhands/runtime_adapter.py` 的
`execute_tool_gated`，且它是把该 bound method **作为参数**交给
`PolicyWrappedToolExecutor.execute`（先 `evaluate_tool_call` 再执行），不是直接调用；
agent loop 侧的 SDK 执行点由 `PolicyEnforcingAgent._execute_action_event` 覆盖，先
`_evaluate` 再委托。两处均由结构判据固定（`tests/architecture/python/test_tool_plane_boundary.py`），
`AgentRuntime` Port 的公开面里没有任何"直接执行工具"的方法。

## 9. 接入边界登记（MCP / tool provider）

本节的用途是**如实点名已覆盖与未覆盖**，防止把"代码里存在"读成"生产可用"。

**已覆盖**：

- MCP **客户端**已实现（stdio 与 streamable_http 两种 transport，schema 校验）；
  凭据经 `CredentialResolver` 按 `credential_ref` 注入，**禁止 token passthrough**。
- provider 治理写面已存在：`GET /tool-providers`（只读目录 + 三态健康）、
  `POST/PATCH /tool-provider-registrations` + `/approve` + `/revoke` + `/health-check`
  （PENDING → ACTIVE → REVOKED），以及 ToolPack 的
  `GET /tool-packs` + `install` + `approve-update` + `revoke`。
- 冻结集消费链：ACTIVE 注册经目录合并（带 pin digest）→ 计划 → 会话冻结集。

**未覆盖 / 未实现**（逐条点名）：

- **生产没有任何 ToolProvider 实例**：`ApiDeps.tool_providers` 恒为空 dict，因此
  preflight 对非 NATIVE provider 的健康恒为 UNKNOWN（如实回"控制面未注册可探测的
  provider 实例"）。`McpToolProvider` / `NcbiEutilsProvider` 今天只被测试与
  `tools/*.py` 手工脚本构造。
- **本仓没有 MCP server**（`tests/mcp_server/` 是 contract 用的 stdio 测试服务）。
- **provider id → SDK tool name 的映射不存在**：SDK 侧期望的是类名（如 `TerminalTool`），
  而冻结集里是 Research OS 的 provider id；缺映射时会话创建**点名失败**（不静默丢工具）。
- **SDK 上游有一块本仓未使用的动态面**：OpenHands agent 内建 MCP 工具变更回调
  （`_on_mcp_tools_changed` 之类）；Research OS 未给它配任何 MCP，因此该面今天不生效——
  登记它是为了说明"冻结"的边界在哪里。
- **`tools/*.py` 手工脚本可绕过门禁**直接调用 provider（开发脚本，不在控制面路径上）。
- **experiments 侧的 `GovernedExecution` 是另一条独立的 policy 门**，与本节的工具面
  不共用判据；两处的口径统一属后续工作。
