---
id: PLAN-20261001-267
slug: goal-028-ec01-declarative-provider-to-sdk-tool-mapping
title: GOAL-028 cycle 1（EC-01）：provider→SDK 工具映射 — 声明式绑定 + 接进生产组合根 + 点名失败反证两向
status: DONE
created_at: 2026-10-01
updated_at: 2026-10-01
latest_recheck: .cursor/plans/rechecks/RECHECK-20261001-268-goal-028-ec01-declarative-provider-to-sdk-tool-mapping.md
memory_entries:
  - .cursor/memory/entries/MEM-20261001-180-sdk-tool-registry-is-process-global.md
parent_goal: GOAL-20261001-028
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261001-028 的 **EC-01**（provider→SDK 工具映射，收 GOAL-027 的限制 ①）。
    授权沿用该 GOAL 的 `authorization.ref`：「**新增 provider→SDK 工具映射层**，并把它接进生产
    组合根（这是本 GOAL 的主干）」+「新增判据 / 夹具 / 探针（落 `tests/**`）」+「修实现过程中
    发现的真缺陷」+ push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：新增件一律落**新文件**为主；对既有产品的改动**限于**「装配面新增可注入缝」
    （`services/api/runtime_support.py`、`adapters/openhands/`、`packages/domain/protocols.py`、
    `adapters/contracts/protocol_loaders.py`、`packages/application/protocol_compile/`、
    `packages/application/run_orchestration/session_resolution.py`）与 `schemas/protocol.schema.json`
    的**纯新增**字段；**不修改**任何既有判据 / 门禁 / 阈值 / 放行面（点名：
    `tests/e2e/test_ec03_real_runtime_offline_chain.py`、`tests/e2e/test_multi_role_research_offline.py`、
    `tests/application/run_orchestration/**`、`tests/architecture/python/test_run_chain_capability_exposure.py`、
    `tests/application/preflight/**`、`tests/egress_guard.py`、三道记录面判据、规模门、`tests/api/run_fixtures.py`）；
    **不改** `default_effect: DENY`、**不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；
    **零**新依赖；**不得**把 provider id 直接当 SDK 工具名；**不得**让 OpenHands 类型进 Domain；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **声明式映射层在树**：协议 phase 可声明「本 phase 的会话工具 = 哪个 provider 绑到哪个
      SDK 工具名」；域内用**纯字符串**声明（无 OpenHands 类型），loader 读入，编译器**原样透传**
      （不解释），应用层**唯一解释点**解析成绑定，adapter 侧消费。schema 同轮**纯新增**该字段。
    status: PENDING
  - id: AC-2
    criterion: >-
      **接进生产组合根**：`build_agent_runtime` / `_openhands_runtime` 能接收装配方提供的
      SDK 工具实现并以绑定名注册；两个生产调用点（`composition.py` / `pg_composition.py`）
      接入。默认（未提供实现、未声明绑定）**逐字保持今天的行为**（点名失败）。
    status: PENDING
  - id: AC-3
    criterion: >-
      **点名失败反证两向**（各自**点名**、且发生在**副作用之前**）：
      ① **删掉一条绑定声明** ⇒ 该 provider id 直落 SDK ⇒ 会话创建点名
      `ToolDefinition '<provider id>' is not registered`，且 **mock 端点零请求**；
      ② **绑定到装配方未提供的工具名** ⇒ 点名该**工具名**（与 provider id 区分），
      同样零请求。
    status: PENDING
  - id: AC-4
    criterion: >-
      **默认装配实跑**：`multi_role_research_v1` 在**生产装配路径**（`build_agent_runtime`
      的真实缺省，**非** `map_tools=True` 测试后门）上跑到 `SUCCEEDED`（离线链），
      且逐 phase 的 role / 结构化产出可复核。
    status: PENDING
  - id: AC-5
    criterion: >-
      **既有判据逐字节未改且全绿**：`tests/e2e/test_ec03_real_runtime_offline_chain.py`
      （含 `test_unmapped_tool_set_is_named_not_silently_dropped`）、
      `tests/e2e/test_multi_role_research_offline.py`、
      `tests/architecture/python/test_run_chain_capability_exposure.py`、
      `tests/application/run_orchestration/**` 全部绿（`git diff` 证明这些文件零改动）。
    status: PENDING
---

## 验收条件

承 GOAL-20261001-028 的 EC-01，五条 AC 见 frontmatter（AC-1…AC-5）。

**为什么 AC-3 是两向而不是一向**：① 覆盖「声明缺席」（今天的行为，必须不被改动波及）；
② 覆盖「声明在场但目标不存在」（新增路径的失败形态）。两向都必须**点名**且**零副作用**，
合起来才是「点名失败 ≠ 静默降级」的完整句。

**为什么 AC-5 用 `git diff` 而不是「跑一遍看看绿不绿」**：本 GOAL 的禁令是
「**修改**任何既有判据」——「跑了且绿」证明不了「没被改过」（改断言迁就同样会绿）。

## 实施清单

- [x] **WP-A（域内声明 + loader + 编译透传 + schema 纯新增）** ⇒ commit `60e0303`
- [x] **WP-B（应用层唯一解释点 + adapter 消费）** ⇒ commit `1c5ad78`
- [x] **WP-C（装配面可注入缝 + 生产组合根接入 + 真实实现）** ⇒ commit `50a58c4`
- [x] **WP-D（新增判据 + 反证两向 + 默认装配实跑）** ⇒ commit `234fb06`
- [x] **WP-D2（同源判据：五面一致 + adapter 减法则对齐）** ⇒ commit `cb5c26f`
- [x] **WP-E（记录 + 门 + 提交）** ⇒ 本回写提交

## 证据

**交付物**（全部在树）

| 面 | 文件 | 作用 |
| --- | --- | --- |
| 声明 | `packages/domain/protocols.py`（`SessionToolBinding`） | 纯字符串的 `provider_id → tool_name`（OpenHands 类型不进 Domain） |
| 读入 | `adapters/contracts/protocol_loaders.py` | 只读不解释；字段缺失 ⇒ 空（既有语义逐字节不变） |
| 透传 | `packages/application/protocol_compile/compiler.py` | 原样携带（编译不解释） |
| schema | `schemas/protocol.schema.json` | `$defs.sessionToolBinding` **纯新增**（既有字段与枚举一字未动） |
| 解释 | `packages/application/run_orchestration/session_resolution.py` | **唯一解释点**：`session_tool_face` / `session_tool_bindings`（越界、一 provider 两名字各自点名） |
| 消费 | `adapters/openhands/tool_mapping.py`（`bind_session_tools`） | 缺声明逐字返回；位置保持替换；不增减工具数 |
| 实现 | `adapters/openhands/session_tools.py` | `BoundSessionTool` + 注册面（按名绑定调用桥） |
| 桥 | `adapters/openhands/session_tool_invocation.py` | 经**同一个** `execute_tool_call` 走策略+执行门；参数经 `tool-args` 制品（digest 防篡改） |
| 组合根 | `services/api/runtime_support.py` | `register_session_tools` 可选缝（缺省 `None` ⇒ 生产行为逐字不变） |
| 判据 | `tests/e2e/test_tool_binding_on_the_default_assembly.py`（292 行） | 三面一致 + 默认装配实跑 + 两向反证 + 两向点名 |
| 判据 | `tests/architecture/python/test_session_tool_bindings_exposure.py` | 五面一致 + application/adapter 减法则逐字对齐 |
| 协议 | `examples/protocols/tool_binding_{research,partial,unwired}_v1.yaml` | 成对（差别只有声明行 ⇒ 失败可归因） |

**实测结果**

- `tests/e2e/test_tool_binding_on_the_default_assembly.py`：**13 passed**；
- `tests/architecture/python/test_session_tool_bindings_exposure.py`：**9 passed**；
- 既有判据（`test_ec03_real_runtime_offline_chain` / `test_multi_role_research_offline` /
  `test_run_chain_capability_exposure` / `tests/application/run_orchestration`）连同新判据
  **105 passed / 1 skipped**；`git diff` 对既有判据文件**为空**。

**两向点名失败（原文）**

- 反证一（删一条绑定）：`tool "ToolDefinition 'openhands_workspace' is not registered"`；
- 反证二（绑到没有实现的工具名）：`ToolDefinition 'workspace.read.unwired' is not registered`；
- **两向的 mock 端点请求数均为 0**（失败发生在任何 LLM 调用之前）。

**默认装配实跑留档**：`build_agent_runtime` 的真实缺省（**非** `map_tools=True`）+
`register_session_tools` 注入实现 ⇒ run `state=SUCCEEDED`、`protocol_id=tool_binding_research_v1_0_0`、
mock 端点被真实驱动（请求账非空）。

**按压 P-1（先红后绿 + 逐字节复原）**：架空 `session_builder` 的绑定翻译 ⇒ 三条主判据
**3 failed**（点名 provider id）；恢复后 `sha256sum -c` 逐字节一致
（`session_builder.py` = `00591f58…`、`tool_mapping.py` = `9dbc95b6…`）且 13 passed。

**同源更新**：`RECHECK-20261001-268`（`PASS_WITH_WARNINGS`，五条 `W-NN` 如实登记）。

## 影响报告

- **Domain/schema 变化**：新增 `SessionToolBinding` 值对象与两个 dataclass 字段
  （`ProtocolPhase.session_tool_bindings` / `CompiledPhase.session_tool_bindings`），
  **均为带缺省的纯新增** ⇒ 既有协议、既有构造点逐字节不变；
  `schemas/protocol.schema.json` 纯新增字段与 `$defs`，既有字段与枚举一字未动。
- **API 变化**：无新路由、无 DTO 变化；`build_agent_runtime` 新增**可选**关键字参数
  （`register_session_tools`，缺省 `None`）⇒ 既有三个调用点无需改动。
- **安全/凭据变化**：零凭据改动；桥的凭据面仍只经既有 `CredentialResolver`；
  桥不新增出网路径（provider 自己声明的 `network_domains` 判据不变）。
- **兼容性/迁移风险**：无迁移。缺省路径（未声明绑定 / 未注入注册面）行为**逐字节不变**，
  由三条既有判据 + 新判据的「未声明协议面等于冻结集」用例共同守住。
- **上游版本影响**：无依赖改动（`mcp` 未动，零新增依赖）。
- **下一项任务**：GOAL-028 **EC-02**（活检索 + 第三方 MCP 勘察结论）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | cycle 1 派生：EC-01 主干（映射层 + 组合根 + 两向反证 + 默认装配实跑）。 |
| 2026-10-01 | DONE | 六件 WP 全部落树；13 + 9 判据 passed、既有判据逐字节未改；按压 P-1 先红后绿 + 逐字节复原；`RECHECK-20261001-268` = `PASS_WITH_WARNINGS`（五条 WARNING 如实登记）。 |
