---
id: PLAN-20261001-267
slug: goal-028-ec01-declarative-provider-to-sdk-tool-mapping
title: GOAL-028 cycle 1（EC-01）：provider→SDK 工具映射 — 声明式绑定 + 接进生产组合根 + 点名失败反证两向
status: IN_PROGRESS
created_at: 2026-10-01
updated_at: 2026-10-01
latest_recheck: null
memory_entries: []
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

- [ ] **WP-A（域内声明 + loader + 编译透传 + schema 纯新增）**
  - [ ] 域内新增声明类型（纯字符串对：`provider_id → sdk tool name`），落
        `packages/domain/protocols.py`；`CompiledPhase` 同字段原样透传。
  - [ ] `adapters/contracts/protocol_loaders.py` 读入（缺省空 ⇒ 既有语义逐字节不变）。
  - [ ] `schemas/protocol.schema.json` 的 `$defs.phase` **纯新增**该字段
        （既有字段与枚举一字不动）。
  - [ ] 判据：协议文档面 / 加载面 / 编译面三面逐字一致（照
        `tests/architecture/python/test_run_chain_capability_exposure.py` 的形态，**新文件**）。
- [ ] **WP-B（应用层唯一解释点 + adapter 消费）**
  - [ ] `session_resolution` 新增解析函数：冻结集 + run-chain 排除 + 绑定 ⇒ 会话工具名序列；
        越界（绑定的 provider id 不在冻结集内）⇒ **点名 ValueError**。
  - [ ] `adapters/openhands/tool_mapping.py` 新增消费函数（**不修改** `session_tool_ids`）；
        `session_builder` 用绑定后的名字装配 `Tool(name=...)`。
- [ ] **WP-C（装配面可注入缝 + 两个组合根接入）**
  - [ ] `AdapterDependencies` 新增「装配方提供的 SDK 工具实现表」（缺省 `None` ⇒ 今天的行为）。
  - [ ] `_openhands_runtime` / `build_agent_runtime` 接收并下传；
        `composition.py` / `pg_composition.py` 接入。
  - [ ] 缺少实现 ⇒ **点名失败**（消息含工具名与 provider id），发生在会话创建期、LLM 调用之前。
- [ ] **WP-D（新增判据 + 反证两向 + 默认装配实跑）**
  - [ ] 新判据文件：绑定解析三面一致 + 越界点名 + 两向反证（点名 + 零请求）+
        默认装配下 `multi_role_research_v1` 跑到 `SUCCEEDED`。
  - [ ] 既有五处判据 `git diff` 零改动取证。
- [ ] **WP-E（记录 + 门 + 提交）**
  - [ ] 先写记录（本 PLAN / RECHECK / GOAL 回写）→ 记录面判据 → 全量 m0（独占、canonical DSN）。
  - [ ] 显式路径提交 → push → 轮询 CI 到终态 → 回填台账（**逐提交**）。

## 证据

（执行中回填：判据输出、反证两向的判词原文、默认装配实跑的 run 终态、按压前后 raw `sha256`。）

## 影响报告

（收口时回填：Domain/API/schema 变化、安全/凭据变化、兼容性/迁移风险、上游版本影响、下一项任务。
执行中如需预判：本 PLAN 预期新增一个协议 phase 字段（schema 纯新增，Loader 缺省空 ⇒ 既有协议
逐字节不变）、新增装配面可注入缝（缺省 `None` ⇒ 生产行为不变）、新增判据文件与绑定层模块。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | cycle 1 派生：EC-01 主干（映射层 + 组合根 + 两向反证 + 默认装配实跑）。 |
