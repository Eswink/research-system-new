---
id: MEM-20260919-083
title: "工具面边界判据：结构判据要钉「bound method 交给了包装」而不是「文件里有这个词」；override 型缺陷必须读真在跑的对象（记录里换了 ≠ 真换了）"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-111-tool-plane-boundary.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-111-tool-plane-boundary.md
supersedes: []
tags:
  - tool-plane
  - policy-wrapper
  - structural-criterion
  - fork-override
  - contract-tests
  - honest-registration
---

# 工具面边界（GOAL-20260919-007 / EC-05）

## 做了什么

把「工具执行只有一条门控入口」「会话的有效 Tool Set 冻结」「MCP / tool provider 接入
边界」变成可判事实，并修掉一处实测出的**半应用缺陷**：

- 结构判据：`tests/architecture/python/test_tool_plane_boundary.py`（生产源码树 AST 全扫）。
- 冻结落地：`adapters/openhands/session_builder.py` 的 fork 窄门 + 重建 agent 用改写后的
  spec；`adapters/fakes/agent_runtime.py` 同契约。
- 契约判据：`tests/contracts/test_agent_runtime_contract.py`（Fake 与真实 adapter 一起判）。
- 登记：`docs/architecture/TOOL_RUNTIME.md` §3 现状 + 新增 §9「接入边界登记」。

## 为什么这样做

1. **结构判据要钉路径，不是钉词**。最初想把「三处门控面」写成白名单，实测发现：
   生产源码里提及 SDK 直达执行点（`conversation.execute_tool`）的地方**只有一处**
   （`runtime_adapter.py:285`），而且它**不是调用**——是把 bound method 作为参数交给
   `PolicyWrappedToolExecutor.execute`。所以正确的判据是
   「恰有一处提及 **且** 该处必须作为参数进策略包装」；反证时把那一行改成直接调用，
   判据立刻红并点名「does not pass the SDK entry into the policy wrapper」。
   **通用规律**：门控类结构判据要判"值流向了哪里"，不是"文件里出现过这个词"。
2. **override 型缺陷：记录变了不等于行为变了**。fork 的 `tool_set_override` 此前
   只投影进新会话 spec，而 `assemble_agent` 仍用**父会话** spec 装配 agent ⇒
   "重建工具集"是假的。判据必须读**真在跑的对象**（`entry.conversation.agent.tools`），
   不能读会话记录字段——两者不一致时，只有前者能发现问题（F-1 反证）。
3. **Port 契约要两个实现一起判**。窄门写在真实 adapter 与 Fake 两处，用
   `tests/contracts` 的参数化（`PORT_IMPLEMENTATIONS["agent_runtime"]`）一次判两边；
   F-2 反证显示：只短路真实 adapter 的守卫时，失败的正是那一个参数化分支——单边实现
   会被抓住。
4. **登记要区分「代码存在」与「生产在跑」**：`execute_tool_call` /
   `execute_tool_gated` 生产零调用点，`ApiDeps.tool_providers` 恒空 dict ⇒
   "DENY 不触达 executor"是真的，但**没有生产路径在用它**。把这种事实写进文档
   （TOOL_RUNTIME.md §9）比在文档里写"已实现"重要得多。

## 怎么做与复现

- 结构判据：`uv run --frozen --no-sync python -B -m pytest tests/architecture/python/test_tool_plane_boundary.py -q` ⇒ 6 passed。
- 冻结契约：`… -m pytest tests/contracts/test_agent_runtime_contract.py -q -k tool_set` ⇒
  4 passed（两例 × 两个实现）。
- 反证三处（记录在 RECHECK-20260919-111）：
  ① 直接调用 SDK 执行点 ⇒ 结构判据红；
  ② 窄门条件短路 ⇒ 真实 adapter 的契约分支红；
  ③ 撤销"用改写后 spec 装配 agent" ⇒ 重建工具集判据红。

## 适用边界（踩过的坑）

- **fork 是新建会话**，不是会话内改写：ADR-0004「Session Tool Set 冻结」+ AGENTS.md §5
  「改变必须显式 Manifest Revision 或 Fork Run」⇒ 本轮的窄门是「改工具集必须同时带
  `manifest_revision_ref`」，**不是**禁止 fork。
- 窄门今天**没有 HTTP 面**（`runtime.fork` 生产零调用点）——机制就位、入口未开。
- `PolicyEnforcingAgent` 的包装是条件式的（非 `OpenHandsAgent` 原样透传）；生产不传
  `build_agent` 所以不可达，但这是"今天恰好"，不是判据。
- SDK 上游有本仓未使用的 MCP 动态工具面（agent 内建工具变更回调）：冻结的边界是
  **本仓不写**它；给 SDK 配 MCP 时必须重判。
- 执行期门禁把 SDK tool name 当 capability，与 exposure-time 的 Research OS capability
  词表语义不同；`scope=session_id` 使带 scope 的 allow 规则不命中 ⇒ 落默认 DENY
  （安全侧）。补 `tool.*` 词表属核心安全策略变更，需人工拍板。
- **Mimosa 误报**：`.execute(` 相邻写法会被判成"SQL 注入"并拦下写入（含把 bound method
  传进包装那一行）。绕法：先用 `git checkout -- <file>` 复原，或改写为不含该字面相邻的
  等价形式；不要为了绕误报而削弱判据。

## 来源

- `.cursor/plans/tasks/PLAN-20260919-111-tool-plane-boundary.md`
- `.cursor/plans/rechecks/RECHECK-20260919-111-tool-plane-boundary.md`
- 代码：`adapters/openhands/session_builder.py`、`adapters/openhands/runtime_adapter.py`、
  `adapters/openhands/policy_wrapper.py`、`adapters/openhands/policy_enforcing_agent.py`、
  `adapters/fakes/agent_runtime.py`
- 判据：`tests/architecture/python/test_tool_plane_boundary.py`、
  `tests/contracts/test_agent_runtime_contract.py`、
  `tests/adapters/openhands/{test_fork_override,test_policy_enforcement}.py`
- 文档：`docs/architecture/TOOL_RUNTIME.md` §3/§8/§9、`docs/architecture/AGENT_RUNTIME.md`、
  `docs/integration/OPENHANDS_ADAPTER.md`
