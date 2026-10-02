---
id: RECHECK-20261001-268
slug: goal-028-ec01-declarative-provider-to-sdk-tool-mapping
title: GOAL-028 EC-01 复检 — provider→SDK 声明式映射（默认装配实跑 + 点名失败反证两向）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-01
updated_at: 2026-10-01
plan_id: PLAN-20261001-267
parent_goal: GOAL-20261001-028
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261001-267`（GOAL-20261001-028 的 cycle 1 子计划）——「provider→SDK 工具映射」
从**测试侧补丁**推进到**生产装配下的声明式事实**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 声明面在树（域内类型 + loader + 编译透传 + schema 纯新增） | **PASS** | `SessionToolBinding`（`packages/domain/protocols.py`，纯字符串，OpenHands 类型不进 Domain）；`protocol_loaders._session_tool_bindings`；`compiler._compiled_phases` 原样透传；`protocol.schema.json` 的 `$defs.sessionToolBinding`（既有字段与 `capability_execution` 枚举一字未动） |
| AC-2 | 接进生产组合根（可注入注册面） | **PASS** | `build_agent_runtime(..., register_session_tools=)` → `_openhands_runtime` → 复用**既有** `AdapterDependencies.register_tools`（此前全仓零调用方的死缝，未新增字段）；缺省 `None` ⇒ 生产行为逐字不变 |
| AC-3 | 点名失败反证**两向**（各自点名 + 零请求） | **PASS** | 反证一：跑 `tool_binding_partial_v1.yaml` ⇒ 点名 `ToolDefinition 'openhands_workspace' is not registered` + mock 端点零请求；反证二：跑 `tool_binding_unwired_v1.yaml` ⇒ 点名 `ToolDefinition 'workspace.read.unwired' is not registered` + 零请求（点的是**工具名**，与 provider id 可区分） |
| AC-4 | **默认装配**实跑到 `SUCCEEDED` | **PASS** | `test_the_run_reaches_success_on_the_production_assembly`：走 `build_agent_runtime` 的真实缺省（**非** `map_tools=True`），`register_session_tools` 注入真实实现，run 到 `SUCCEEDED`、`protocol_id=tool_binding_research_v1_0_0`、mock 端点真被驱动 |
| AC-5 | 既有判据**逐字节未改**且全绿 | **PASS** | `git diff` 对 `test_ec03_real_runtime_offline_chain.py` / `test_multi_role_research_offline.py` / `test_run_chain_capability_exposure.py` / `tests/application/run_orchestration/` / `tests/application/preflight/` / `run_fixtures.py` / `egress_guard.py` **均为空**；连同新判据 105 passed / 1 skipped |

## 按压（先红后绿 + 逐字节复原）

| 编号 | 做法 | 结果 | 复原取证 |
| --- | --- | --- | --- |
| P-1 | 架空 `session_builder` 的绑定翻译（`tool_ids = tool_ids`） | **3 failed**（`test_the_run_reaches_success_*` / `test_dropping_one_binding_*` / `test_binding_to_an_unimplemented_tool_name_*`），失败文本点名的正是 **provider id**（`m12_artifact`） | 恢复后 `sha256sum -c` 逐字节一致：`session_builder.py` = `00591f58…`、`tool_mapping.py` = `9dbc95b6…`；13 passed |

## 复检发现（三处按实测校准，均为**判据 / 实现规模**问题，产品语义未因此改动）

1. **反证二起初依赖用例顺序（真问题）**：首版用「换实现表 + 复用 `workspace.read`」，
   实测 run 到 `SUCCEEDED`（判据红）。根因：SDK 的 `register_tool` 是**进程级、只增不减**
   的（无撤销入口）⇒ 同进程里先跑用例注册过的名字对后跑**仍可解析** ⇒ 断言成了用例顺序
   的函数。改用**专属名字** `workspace.read.unwired`（不与任何别的装配重合）。
2. **反证一在全量门里**假绿后转真红**（真问题，同一根因的反向）**：单跑绿、**全量 m0 判红**
   —— 因为 `test_ec03_real_runtime_offline_chain.py` 的 `map_tools=True` 路径会把
   `openhands_workspace` 注册成惰性替身 ⇒ 断言「它未注册」在**单跑**时成立、在全量跑时
   被前面的用例抹掉。修法：用例**显式**从 registry 摘掉该名字
   （`registry._REG.pop(name, None)`，瞬态清理、非产品路径），让事实由本用例确定。
   **两个方向合起来**已沉淀进 `MEM-20261001-180`（不止「换表假绿」，还有「不清理假绿」）。
3. **两处规模门超限（实现侧，已修）**：`_openhands_runtime` 54 行、`resolve_sessions` 51 行
   （限 50）。按仓内既有形态**抽出小函数**（`_require_policy_faces` / `_workspace_builder` /
   `_spec_context`），**未**用 `noqa` 掩盖（唯二 `noqa: PLR0913` 是参数数上限、与既有多处同形）。
   抽出后 `test_python_source_limits` **1089 passed**。
4. **协议 fixture 起初只给一个 phase 声明绑定**：另一个 phase 仍点名失败（判据如实判红）
   ⇒ 两条 phase 各声明两条，反证协议则各少一条（差别只有声明行，失败可归因）。

## 结果

**`PASS_WITH_WARNINGS`** —— 五条 AC 全部 PASS，两向反证与按压齐备，既有判据零改动。
WARNINGS 见下（如实登记，不消解）。

## WARNINGS（逐条登记，本 EC 不消解）

- **`W-1`｜映射目标必须由装配方提供，产品侧不附带实现**：本 EC 把「工具名 → 实现」的
  责任留给装配方（`register_session_tools`）。**未提供 ⇒ 未声明绑定的协议照旧点名失败**
  （既有语义），声明的工具名无实现也点名失败。**含义**：默认配置（不注入该缝）下，
  多 role 协议仍不能在生产装配里跑起来——**本 EC 证的是机制成立，不是「出厂即可跑」**。
  接线样例见判据（测试侧），生产接线属后续工作。
- **`W-2`｜绑定是 phase 级、不是全局映射表**：同一 provider 在不同 phase 可绑到不同工具名
  （灵活，也意味着「一个 provider 一个规范名」不是本机制保证的不变量）。
- **`W-3`｜桥的实现只在判据里被真实调用**：`session_tool_invocation` 的
  「经 `execute_tool_call` 走同一扇策略门」由**代码路径**保证（复用同一函数），
  但本 EC 未新增判据专门断言「会话工具调用也受 policy DENY 拦截」——该断言由既有的
  policy 面判据与 `execute_tool_call` 自身的判据承担。
- **`W-4`｜`session_tool_bindings` 只支持「provider → 一个工具名」**：不做一对多
  （一个 provider 拆成多件会话工具）；一对多会与 `Duplicate tool names` 的既有约束交互，
  本轮不碰。
- **`W-5`｜第三方 MCP 可 pin 性仍未验证**：属 GOAL-028 EC-02 的范围，本 EC 不涉及。

## 未覆盖范围（承继，逐条在位）

1. **读面未认证** —— GET / HEAD 无认证（GOAL-019 判词 (i)：保护范围**只有写面**）；
2. **多租户未做** —— 无 organization scope、无逐调用方身份（单 token ⇒ 单主体）；
3. **BOLA·BFLA 未做** —— 无对象级 / 功能级鉴权；
4. **部署面未验证** —— 跨副本 / 真实 broker / 真实 worker 集群 / 外部队列只在登记面；
5. **`R-M1` 未收口** —— Mimosa 钩子 `scanner_enobufs` 未得完整结论 ⇒ **不得**据此宣称
   项目安全。

**可靠性口径**：本 EC 不涉及投递语义；本仓**明确否认**「恰好一次」，口径只能是
at-least-once + idempotency + deduplication。

## 结论

GOAL-20261001-028 的 **EC-01 达成**：`provider→SDK 工具映射` 从「测试侧恒等替身」推进到
「**显式声明 + 生产组合根消费**」，缺映射与错映射**各自点名**且失败发生在任何 LLM 调用
之前，默认装配下声明齐全的协议**真的跑到 `SUCCEEDED`**，既有判据逐字节未改。
五条 `W-NN` 如实登记（尤其 `W-1`：**机制成立 ≠ 出厂即可跑**）。

**本地门终态**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24 / `FAILED [` = 0 /
EXIT=0 / **4954 passed / 21 skipped**；日志 `scratch/goal028-c1c-m0.log`，记录写入后独占运行、
canonical DSN pin、不接管道、零进程残留）；治理 `validate.py` 绿；记录面判据 31 passed。
