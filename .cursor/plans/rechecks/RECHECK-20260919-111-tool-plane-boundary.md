---
id: RECHECK-20260919-111
plan_id: PLAN-20260919-111
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle5
baseline_ref: 697170f
checked_head: WORKTREE
---

# RECHECK-20260919-111 — 工具面边界（GOAL-20260919-007 cycle 5 = EC-05）

## 检查范围

EC-05 的三条判据逐条对表（每条都要**实跑**证据）：

| EC-05 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| **唯一公共执行入口**是门控入口；直通面在组合装配路径上**不可达**（结构判据） | `tests/architecture/python/test_tool_plane_boundary.py`（新，6 例） | 生产源码里提及 SDK 直达执行点的地方**只有一处**且必须是"把 bound method 作为参数交给策略包装"；组合根不构造任何执行体；`AgentRuntime` Port 公开面无执行方法 |
| **运行时**证明 DENY 时 executor **未被触达** | 新增 adapter 公开面判据 + 既有四条用例实跑 | `test_the_adapter_exposes_exactly_one_tool_execution_entry`；`test_policy_enforcement.py` 的 `_EXECUTIONS == []` 两条；`test_tool_plane_execution.py` 的 `provider.method_calls("execute") == 0` 两条 |
| **工具集冻结**：会话内有效 Tool Set 不可被改写（用例证明改写被拒或不可达） | 三层判据 + fork 窄门 | spec 就地写即抛（`FrozenInstanceError`）；生产源码无 `spec`/`conversation` 重赋值（AST）；fork 改工具集必须声明 `manifest_revision_ref`（契约用例对两个实现都判） |
| **MCP / tool provider 接入边界只如实登记**，不新增接入面 | `TOOL_RUNTIME.md` §3 补现状、新增 §9 接入边界登记 | 已覆盖 / 未覆盖逐条点名；本 PLAN **零新增端点、零新增配置面**（`git diff --stat` 可核） |
| 反证：拆掉门控面 / 拆掉窄门 ⇒ 对应判据红 | 三次注入 | 见「反证与实测」F-1 / F-2 / F-3 |
| 尺寸门 / ruff / mypy / 受影响套件 / m0 | 见「门禁」 | 见「门禁」 |

## 检查结果

### 边界今天长什么样（实测，不是文档转述）

```text
                       ┌─ agent loop：PolicyEnforcingAgent._execute_action_event（先 _evaluate 再委托）
SDK 工具执行点 ────────┤
                       └─ direct：conversation.execute_tool ──→ 作为参数交给
                                                                PolicyWrappedToolExecutor.execute
                                                                （先 evaluate_tool_call 再执行）
```

- **提及 SDK 直达执行点的生产源码只有一处**：`adapters/openhands/runtime_adapter.py:285`，
  且它**不是**直接调用——该 bound method 只作为参数进了策略包装。这不是"抽查到的"，
  而是 AST 判据遍历 `services/` + `packages/application/` + `adapters/` 全树的结果
  （`test_direct_sdk_execution_is_confined_to_the_gated_faces`），白名单只有一个成员，
  多一处、少一处都会红。
- **agent loop 侧**：`PolicyEnforcingAgent._execute_action_event` 覆盖 SDK 执行点，
  结构判据要求 `_evaluate` 的调用**先于**委托调用（顺序可判，不是"里面有就行"）；
  注册表缺失时 `_evaluate` 返 **DENY**（fail-closed）。
- **组合根**：`composition.py` / `pg_composition.py` / `runtime_support.py` 不构造
  `Agent` / `Conversation` / `PolicyWrappedToolExecutor` / `Tool`（AST 判据）；
  `build_agent_runtime` 缺 policy evaluator 时点名拒绝（EC-01 既有门链）。
- **Port 面**：`AgentRuntime` 的公开方法名里**没有**任何 `execute*` ——门控入口
  （`execute_tool_gated`）是 adapter 的附加方法，不在 Port 上；运行时读数
  `dir(OpenHandsRuntimeAdapter)` 里执行相关公开名恰为 `{"execute_tool_gated"}`。

### 冻结：三层证据 + 一个**新发现的半应用缺陷**

- （i）`AgentSessionSpec` 是 frozen dataclass ⇒ `setattr` 抛 `FrozenInstanceError`（实跑）；
- （ii）生产源码里**没有**给会话条目重新赋值 `spec` / `conversation` 的语句（AST 全树）；
- （iii）SDK 侧 agent 的工具列表在装配时按冻结集构造，本仓此后不再写它。

**本轮勘察实测出的缺陷**：fork 的 `tool_set_override` 此前**只落到会话记录**——
`fork_conversation` 用**父会话的 spec** 去 `assemble_agent`，所以"重建工具集"实际没重建
（记录里换了，真在跑的没换），且改写不需要任何显式声明。两处一并修：
① 重建 agent 改用**改写后**的 spec；② 只带 `tool_set_override` 而不带
`manifest_revision_ref` 的 fork **一律拒绝**（`InvalidInputError` 点名缺哪条事实），
真实 adapter 与 Fake 走**同一条契约**（`tests/contracts/test_agent_runtime_contract.py`
对两个实现参数化）。这条窄门是 ADR-0004「Session Tool Set 冻结」与 AGENTS.md §5
「改变必须显式创建 Manifest Revision 或 Fork Run」的**落地**，不是新策略。

### 接入边界：登记了什么（不覆盖的东西也写清楚）

**已覆盖**：MCP 客户端（stdio + streamable_http，凭据按 `credential_ref` 注入、禁 token
passthrough）；provider 治理写面（目录只读 + 注册/批准/吊销/健康复核 + ToolPack 生命周期）；
ACTIVE 注册经目录合并（带 pin digest）进入计划。

**未覆盖 / 未实现（逐条点名）**：生产**没有任何 ToolProvider 实例**（`ApiDeps.tool_providers`
恒空 ⇒ 非 NATIVE provider 健康恒 UNKNOWN）；本仓**没有 MCP server**；**provider id → SDK
tool name 的映射不存在**（缺映射时会话创建**点名失败**，不静默丢工具）；SDK 上游的
MCP 动态工具面本仓**未使用**；`tools/*.py` 手工脚本可绕过门禁（开发脚本，不在控制面路径）；
experiments 侧的 `GovernedExecution` 是**另一条**独立的 policy 门。

### 语义错配（登记，不在本 EC 射程）

执行期门禁把 **SDK tool name 当 capability** 求值，exposure-time 用的是 Research OS
capability 词表；叠加 `scope=session_id` 与精确 scope 匹配，`policy.yaml` 里带 scope 的
allow 规则**不会**命中会话级请求 ⇒ 落 `default_effect: DENY`（fail-closed，安全侧）。
补 `tool.*` 词表属**核心安全策略**变更 ⇒ escalation 项，本 EC 只登记不改。

## 反证与实测

| # | 注入 | 结果 |
| --- | --- | --- |
| F-3 | `runtime_adapter.execute_tool_gated` 改成**直接调用** `entry.conversation.execute_tool(...)` | **红**：`test_direct_sdk_execution_is_confined_to_the_gated_faces` 失败，消息点名「does not pass the SDK entry into the policy wrapper」⇒ 结构判据钉的是**路径**，不是"文件里有没有这个词" |
| F-2 | `session_builder.spec_with_overrides` 的窄门条件短路（`if False and …`） | **红**：`test_agent_runtime_fork_rejects_tool_set_change_without_a_revision[_openhands_runtime_factory]` 失败（真实 adapter 那一支）⇒ 契约用例对两个实现分别判 |
| F-1 | `fork_conversation` 改回用父会话 spec 装配 agent（撤销半应用修复） | **红**：`test_fork_tool_set_override_rebuilds_the_agents_tools` 失败⇒ 「override 真的重建工具集」是被测出来的，不是被声称的 |

三次注入均已复原（`git checkout` / 反向编辑），复跑绿。

## CI 失败分类与修复（SOP ⑥，如实记录）

cycle 5 的批量推送（tip `ebabb3a`）在 CI 上红了 **2 个 job**（`quality-ubuntu-latest` /
`quality-windows-latest`，同一步「Run all M0 gates」）。

- **失败签名**：`FAILED [framework/validate]: exit 1`，唯一原因
  「**任务计划未加入 ALL_PLAN: PLAN-20260919-111**」（其余 22 项全绿）。
- **分类**：治理/记录面（不是代码、不是门禁、不是断言）。根因：derive 提交（`ff8e8f6`）
  带进了 `PLAN-20260919-111`，但 `ALL_PLAN.md` 的对应行当时还没写；而**本地**治理校验
  枚举的是**已跟踪**文件，未跟踪的 PLAN 不在枚举里 ⇒ 本地 m0 23/23 绿，CI 红。
- **修复**：把本 cycle 的回写提交（ALL_PLAN 行 + PLAN-111 DONE + 本 RECHECK + MEM-083 +
  GOAL 回写）推上去即可——**未改任何门禁、快照或断言**。
- **教训（登记）**：derive 提交必须**同时**带上 `ALL_PLAN` 行，否则"本地绿、CI 红"
  会稳定复现；这条差异来自"本地看工作树、CI 看推送内容"。

## Warnings（不阻断，如实登记）

- **W-1（最重要的一条）**：**执行期门控在生产零调用点**。`execute_tool_call` 与
  `execute_tool_gated` 今天只被测试调用——也就是说「运行时 DENY 不触达 executor」是
  **真的**，但**没有生产路径在用它**；本 EC 判的是"边界成立且可判"，不是"控制面已经在跑
  工具"。这与 `docs/audits/SYSTEM_REAUDIT_SA1R_M12_GATE.md` 的 S-FIND-01/03/04 同口径。
- **W-2**：`tool.*` capability 词表不存在，执行期门禁的 capability 语义与 exposure-time
  不一致（见「语义错配」）。默认 DENY 使这条错配**安全侧**，但"允许"也不会按预期命中。
- **W-3**：生产冻结集是 **tool provider id 的裸并集**，`TOOL_RUNTIME.md` §3 的
  `∩ Project policy ∩ Provider health ∩ Credential scope` 交集**未落地**；
  `freeze_tool_set` / `require_frozen_tool_set` 仍只有测试调用。
- **W-4**：fork 窄门今天**没有 HTTP 面**——`runtime.fork` 生产零调用点（无控制面路由）。
  因此它是"机制已就位、入口未开"；将来开 `/runs/{id}/fork` 时这条门就在路径上。
- **W-5**：SDK 上游存在本仓未使用的 MCP 动态工具面（agent 内建的工具变更回调）。
  「冻结」的边界是**本仓不写**它，而不是"上游不可能改"；一旦给 SDK 配 MCP 必须重判。
- **W-6**：`tools/*.py` 手工脚本可绕过门禁直接调 provider（开发脚本，不在控制面路径）；
  本 EC 未处理，登记在 `TOOL_RUNTIME.md` §9。
- **W-7**：`PolicyEnforcingAgent` 的包装是**条件式**（`build_agent` 返回非 `OpenHandsAgent`
  时原样透传）。生产不传 `build_agent`，所以今天不可达；本 EC 只把它纳入结构判据的射程
  （组合根不构造执行体），未加运行时守卫。
- **W-8**：本地治理校验枚举**已跟踪**文件，CI 看的是**推送内容** ⇒「derive 提交带进了
  新 PLAN 但没带 ALL_PLAN 行」这种状态在本地是绿的（本轮实测）。避免方式已写进
  「CI 失败分类与修复」节：PLAN 与 ALL_PLAN 行**同提交**。

## 结论

EC-05 **PASS_WITH_WARNINGS**：「唯一门控执行入口」由**结构判据**固定（生产源码里只有一处
提及 SDK 直达执行点，且必须作为参数交给策略包装；Port 公开面无执行方法），「DENY 不触达
executor」有运行时证据（新增一条 adapter 面判据 + 既有四条用例实跑）；「有效 Tool Set 冻结」
三层可判，并**修掉一个实测出的半应用缺陷**（fork 改工具集只写记录、不重建 agent），同时加
上必须声明 Manifest Revision 的窄门（两实现同契约）；MCP / tool provider 边界逐条登记，
**未新增任何接入面**。W-1…W-7 为如实登记的射程边界，其中 W-1（门控无生产调用点）是必须
留档的事实，不阻断本 EC。

## 门禁

| 门 | 结果 |
| --- | --- |
| 结构判据用例 | `tests/architecture/python/test_tool_plane_boundary.py` **6 passed**（F-3 反证下变红） |
| 契约判据 | `tests/contracts/test_agent_runtime_contract.py` tool_set 两例：Fake + 真实 adapter **均 passed**（F-2 下真实 adapter 那一支红） |
| adapter 面 | `tests/adapters/openhands` **4 + 既有**全绿（含新增公开面判据与 fork 重建判据；F-1 下红） |
| 尺寸门（450 行 / 50 行函数） | **949 passed** |
| `ruff check`（产品树）/ `ruff format --check` | 绿（949 files already formatted；首跑红 1 处超长行，已折行） |
| `mypy` | **939 source files, no issues**（首跑红 2 处：AST 节点窄化、`__dataclass_params__` 访问 —— 已按类型正确写法改，未加 ignore） |
| 受影响套件 | `tests/{architecture,contracts,adapters,application}` **1608 passed / 6 skipped** |
| m0（23 项） | **23/23 PASS** |
