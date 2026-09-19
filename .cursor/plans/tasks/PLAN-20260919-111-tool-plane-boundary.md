---
id: PLAN-20260919-111
slug: tool-plane-boundary
title: 工具面边界：唯一公共执行入口 + 会话内 Tool Set 不可改写 + MCP/tool provider 接入边界如实登记（EC-05）
status: DONE
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 5 = EC-05。授权来源：2026-09-19 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`。本 PLAN 遵守：默认 runtime 保持 Fake、不引入新依赖、不改上游 pin、真实端点调用永不进默认 CI、默认 deny 姿态不得放松、不改 Accepted ADR / Canonical State 边界；本 EC **不新增 MCP / tool provider 接入面**。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260919-111-tool-plane-boundary.md
memory_entries:
  - .cursor/memory/entries/MEM-20260919-083-tool-plane-boundary.md
---

# PLAN-20260919-111 — 工具面边界（GOAL-007 cycle 5 = EC-05）

## 目标

把「工具执行只有一条门控入口」「会话的有效 Tool Set 冻结」「MCP / tool provider
接入边界」三件事变成**可判事实**（结构判据 + 运行时判据 + 逐条登记），而不是文档里的
自我声明。**本 EC 不新增任何接入面**（新增即 escalation）。

## 本轮勘察事实（只读，2026-09-19；均给出路径，可复核）

| # | 事实 | 位置 |
| --- | --- | --- |
| 1 | 唯一的**公开**门控执行入口是 `execute_tool_call`（先 `evaluate_execution_policy`，DENY/需批准在 `provider.execute` 之前抛出） | `packages/application/tool_plane/execution.py:72`、`:98-111` |
| 2 | 该入口在生产**零调用点**（只被 `tests/**` 调用）；`docs/audits/SYSTEM_REAUDIT_SA1R_M12_GATE.md:68` 已登记 S-FIND-01/03/04 | 全仓 grep |
| 3 | adapter 侧直通执行的**唯一**包装面是 `PolicyWrappedToolExecutor.execute`（先 `evaluate_tool_call` 再 `execute_tool`） | `adapters/openhands/policy_wrapper.py:100-116` |
| 4 | agent loop 侧门禁是 `PolicyEnforcingAgent._execute_action_event`（SDK 私有执行点；DENY/审批返 `AgentErrorEvent`，不触达 executor）；registry 缺失 ⇒ **默认 DENY** | `adapters/openhands/policy_enforcing_agent.py:95-121` |
| 5 | 装配面 `assemble_agent` 的包装是**条件式**：`build_agent` 返回非 `OpenHandsAgent` 时原样透传（生产不传 `build_agent`，故今天不可达；但无判据固定） | `adapters/openhands/session_builder.py:79-101` |
| 6 | 冻结集来源是 `flatten_tool_providers(plan)` 的**tool provider id 并集**（`openhands_workspace` / `m12_artifact` / `ncbi_eutils`），进入 `AgentSessionSpec.frozen_tool_set`（frozen dataclass） | `packages/application/run_orchestration/session_resolution.py:30-33`、`packages/application/ports/agent_runtime.py:29,43` |
| 7 | `ToolResolver` 的 `freeze_tool_set` / `require_frozen_tool_set` **生产零调用点**（`TOOL_RUNTIME.md:30-43` 的 policy ∩ health ∩ credential 交集公式在生产未落地；生产是裸并集） | `packages/application/tool_plane/resolver.py:163`、`execution.py:123` |
| 8 | provider id → SDK tool name 的**映射全仓不存在**（`tool_mapping.tools_for_frozen_set` 是 1:1 透传且零调用；`deps.register_tools` 两个组合根都不传；`openhands.tools` 子包未安装）⇒ 实测行为是**点名失败**（EC-03 已固定） | `adapters/openhands/tool_mapping.py:18-24`、`tests/e2e/test_ec03_real_runtime_offline_chain.py:260-274` |
| 9 | fork 的 `tool_set_override` 能**无门禁地**替换有效工具集（无 policy 裁决、无子集校验、`manifest_revision_ref` 只做转写） | `adapters/openhands/session_builder.py:103-142` |
| 10 | `runtime.fork` 在生产**零调用点**（仅 adapter 契约/用例），Fake 侧同语义 | `adapters/fakes/agent_runtime.py:160-172` |
| 11 | MCP **客户端已实现**（stdio + streamable_http，凭据按 `credential_ref` 注入，禁 token passthrough），但**生产没有任何 ToolProvider 实例**（`ApiDeps.tool_providers` 恒空 dict） | `adapters/mcp/provider.py:55-173`、`services/api/composition.py:137`、`services/api/preflight_support.py:159-161` |
| 12 | 治理写面已存在（provider 注册 / 健康 / ToolPack 生命周期），本 EC **只登记不新增** | `services/api/routers/tool_registrations.py`、`tool_providers.py`、`tool_packs.py` |
| 13 | 运行时 DENY 不触达 executor 的证据**已存在**（多条，含真实 adapter + 真实 SDK） | `tests/adapters/openhands/test_policy_enforcement.py:115-154`、`test_tool_policy.py:46-67`、`tests/application/test_tool_plane_execution.py:210-241`、`tests/integration/test_capability_plane.py:114-118` |
| 14 | 「唯一公共执行入口 / 直通面在组合路径上不可达」的**结构判据不存在**（可借用范式：EC-01 的 AST 组合根扫描） | `tests/api/test_runtime_selection_surface.py:74-105` |

## 口径（本 PLAN 的判据定义）

- **「唯一公共执行入口」**：以**结构判据**固定——`services/`、`packages/application/`、
  `adapters/` 三个生产源码树里，`conversation.execute_tool` 只允许出现在
  `policy_wrapper`／`runtime_adapter.execute_tool_gated`／`PolicyEnforcingAgent` 三处
  门控面内；且组合根不得构造未包门禁的执行体。
- **「会话内 Tool Set 不可改写」**：三层证据——（i）spec 是 frozen dataclass（写入即
  `FrozenInstanceError`）；（ii）生产源码里**没有**给 `entry.spec` / `entry.conversation`
  重新赋值的语句（AST 判据）；（iii）SDK 侧工具列表在装配时按冻结集构造，会话建立后本仓
  不再写它。**另**：fork 是「新建会话」的正规路径（ADR-0004 / AGENTS.md §5 允许在显式
  Fork Run / Manifest Revision 下改变），本条**加一个窄门**：`tool_set_override` 必须同时
  声明 `manifest_revision_ref`，否则拒绝（fail-closed，且不放松任何既有 allow）。
- **登记而非扩面**：MCP / tool provider 的已覆盖与未覆盖逐条点名；**不新增**注册端点、
  不新增 MCP 配置面、不把 provider 实例塞进 `ApiDeps`（那会改变生产行为）。
- **不加新 policy capability**：今天的门禁用「capability = SDK tool name」求值（与
  exposure-time 的 Research OS capability 语义不同，S-FIND-02）；补 `tool.*` 词表属于
  **核心安全策略**变更 ⇒ 出本 EC 射程，如实登记（不自行改 policy 语义）。

## 验收条件

- **AC-01**：结构判据——生产源码里到达 `conversation.execute_tool` 的路径**只有**门控面
  （AST 扫全仓 + 逐点白名单，白名单外的出现即红）。
- **AC-02**：结构判据——两个组合根不构造未门禁的 Tool 执行体；`build_agent_runtime` 缺
  policy evaluator 时**点名拒绝**（沿用 EC-01/EC-02 的门链）。
- **AC-03**：运行时判据——DENY 时 executor **未被触达**（复用既有用例实跑，逐条引用，
  并新增一条覆盖 `execute_tool_call` 的 provider 面判据）。
- **AC-04**：会话内 Tool Set 不可改写——（i）spec 写入即抛；（ii）AST 证明无写入语句；
  （iii）fork 改工具集而未声明 `manifest_revision_ref` ⇒ **拒绝**（新增窄门 + 用例，
  真实 adapter 与 Fake 两实现同步）。
- **AC-05**：反证——把门控面拆掉（直通可达）⇒ AC-01 红；把窄门拆掉 ⇒ AC-04 的 fork 用例红。
- **AC-06**：MCP / tool provider 接入边界逐条登记（已覆盖 / 未覆盖 / 未实现），**不新增
  接入面**；文档与 `docs/INDEX.md` 同源。
- **AC-07**：既有边界不放松：默认 deny、host shell、凭据面、真实端点门控均无变化。
- **AC-08**：尺寸门 / `ruff` / `mypy` / 受影响套件 / m0 23 项绿；web 六门不受影响（本 EC
  不动前端，仍复跑确认）。

## 实施清单

- [x] **WP-A** 结构判据：门控入口唯一性（AST + 「必须作为参数进包装」）+ 组合根不构造执行体 + Port 无执行方法
- [x] **WP-B** 冻结判据：会话内不可改写（三层）+ fork 窄门 + **重建 agent 用改写后的 spec**（真实 adapter 与 Fake 同步）
- [x] **WP-C** 运行时判据：adapter 公开面只有 `execute_tool_gated` + 既有四条 DENY 用例引用实跑
- [x] **WP-D** 接入边界登记：`TOOL_RUNTIME.md` 新增 §9（含未覆盖面、SDK 上游动态面、手工脚本旁路、`GovernedExecution` 另一条门）
- [x] **WP-E** 文档同源收敛（`TOOL_RUNTIME.md` §3/§8、`AGENT_RUNTIME.md`、`OPENHANDS_ADAPTER.md`）

## 证据

| 项 | 证据 |
| --- | --- |
| 结构判据（AC-01/AC-02） | `tests/architecture/python/test_tool_plane_boundary.py`（6 passed）：唯一提及点 = `runtime_adapter.py:285` 且必须是包装调用的参数；组合根零执行体构造；`AgentRuntime` 公开面无 `execute*` |
| 运行时判据（AC-03） | `tests/adapters/openhands/test_policy_enforcement.py::test_the_adapter_exposes_exactly_one_tool_execution_entry` + 既有 `_EXECUTIONS == []` 两条 + `tests/application/test_tool_plane_execution.py` 的 `provider.method_calls("execute") == 0` 两条（实跑） |
| 冻结判据（AC-04） | spec 就地写抛 `FrozenInstanceError`；AST 全树无 `spec`/`conversation` 重赋值；fork 窄门（`InvalidInputError` 点名 `manifest_revision_ref`）由 `tests/contracts/test_agent_runtime_contract.py` 对 **Fake + 真实 adapter** 参数化判；`test_fork_tool_set_override_rebuilds_the_agents_tools` 读**重建 agent 的 tools** 证明 override 真生效 |
| 反证（AC-05） | F-3 直接调用 SDK 执行点 ⇒ 结构判据红（消息点名「does not pass the SDK entry into the policy wrapper」）；F-2 窄门短路 ⇒ 真实 adapter 契约分支红；F-1 撤销"改写后 spec" ⇒ 重建判据红。均记录在 RECHECK-20260919-111 并已复原 |
| 接入边界（AC-06） | `docs/architecture/TOOL_RUNTIME.md` §9（已覆盖 3 条 / 未覆盖 5 条逐条点名）；本 PLAN **零新增端点、零新增配置面** |
| 不放松既有边界（AC-07） | 未改 policy.yaml、未改能力词表、未改 host shell / 凭据面 / 真实端点门控；窄门是**收紧**（fail-closed） |
| 门禁（AC-08） | 尺寸门 949 passed；`ruff check`（产品树）+ `format --check` 绿；`mypy` 939 files 绿；受影响套件 1608 passed / 6 skipped；m0 **23/23 PASS** |

## 影响报告

- **Domain/API/schema 变化**：无新增 DTO / 路由 / 迁移。`ForkSpec` 的**契约语义**收紧：
  `tool_set_override` 必须伴随 `manifest_revision_ref`（两个实现同契约），拒绝消息点名缺哪条事实。
- **行为变化**：fork 改工具集时，重建 agent 现在真的用改写后的工具集（此前只写进会话记录）。
  无 override 的 fork、model_override 的 fork 行为不变。
- **安全/凭据变化**：无凭据面变化；门控姿态**收紧**（改工具集需显式 revision），默认 DENY 未放松。
- **兼容性/迁移风险**：任何（今日不存在的）生产 fork 调用若只带 `tool_set_override` 会在运行时被拒；
  文档与契约测试同步说明。`ApiDeps` / 组合根 / 存储均未改。
- **上游版本影响**：无（未引入依赖、未改 pin、未改 SDK 用法）。
- **下一项任务**：EC-06（`tool_pack.*` / 脚本策略二选一终态）——cycle 3 实测的
  「`session_message` 键名 vs 合约 `analysis_report`」属该项产品决策。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 5 建档（EC-05）；只读勘察 14 条事实回填（其中三条是结构性发现：门控入口零生产调用点、fork override 无门禁、provider→SDK 映射不存在） |
| 2026-09-19 | DONE | WP-A…WP-E 全部落地（含一次实测缺陷修复与三处反证）；RECHECK-20260919-111 = PASS_WITH_WARNINGS（W-1…W-7）；m0 23/23 |
