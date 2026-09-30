---
id: MEM-20260930-175
title: "MCP 的溢出内容是一层信封（{text[], structured}）⇒ 运行链的 ids_from_previous 需要路径而不只是顶层键；空参数缺陷的缺席分支必须 fail closed，否则缺陷以另一种形态复活"
status: ACTIVE
created_at: 2026-09-30
updated_at: 2026-09-30
scope: repository
confidence: 0.90
review_after: 2027-03-30
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-257-goal-027-ec02-mcp-real-onboarding.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-258-goal-027-ec02-mcp-real-onboarding.md
supersedes: []
tags: [mcp, tool-provider, run-chain, envelope, fail-closed, press-test, goal-027, ec-02]
---

## 做了什么

把 MCP 从「只跑 mock」推进到「自建 server 真回环」，修掉 `adapters/mcp/provider.py`
的空参数真缺陷，并把链式传参打通到信封形结果。五条**实测**得到的事实：

- **MCP 的溢出内容是信封，不是纯对象**：`_serialize_call_tool_result`
  （`adapters/mcp/provider.py` 尾）产出 `{"text": [json 字符串], "structured": {...}}`；
  `text[0]` 解析后与 `structured` 逐字段相等。运行链的 `ids_from_previous`
  **原先只查顶层键** ⇒ `ncbi_eutils`（纯对象 `{"ids": [...]}`）能链、MCP 不能链
  （实测 `previous step carries no 'ids' ids for run-chain tool literature_read`）。
  修法 = `ids_from_previous` 支持**点分路径**（与 `arguments_from_input` 同一 `_lookup`），
  非点分名字走原样分支（既有 15 条链判据逐字节未改、行为零变化）。
- **空参数缺陷 + 缺席分支的 fail-closed 设计**：`_read_args` 按
  `tool-args:{task_id}:{operation_key}` 读制品、`Digest.of_bytes` 重算比对
  `call.argument_digest`；制品**缺席**时仅当声明值恰为 `{}` 的 canonical 序列化
  （`b"{}"`）才回落空参数，其余 **fail closed**——「声明了非空参数却没有制品」是调用方
  bug，不静默降级成空参数（否则原缺陷以另一种形态复活）。
- **SDK 失败分类的实测三态**（探针 `scratch/probe_mcp_schema_20260930.py`）：
  制品**内容**违规（非对象 / 畸形 JSON / digest 不符）⇒ `CONFIGURATION`
  （`execute()` 对 `InvalidInputError` 的既有映射）；工具**声明**违规 ⇒
  `TOOL_SCHEMA_MISMATCH`（如空名字：`mcp protocol error: tool id must not be empty`）；
  server 侧工具错误 ⇒ `FAILED` **记录**（`Unknown tool: …`，不是异常）。
  断言类别前先探针实测，别按直觉写 `VALIDATION_FAILURE`（我这么写过，被测红纠正）。
- **畸形参数反证必须自洽**：用 `put_raw_args` 落**任意字节**时，调用记录的
  `argument_digest` 必须由**同一批字节**算出（`Digest.of_bytes(raw)`），否则先被
  digest 分支拒、JSON 解析面的断言永远不成立——防篡改关与解析关要**各自可证**。
- **`check_health` 对声明违规的形态**：`OPEN_CIRCUIT` + `observed_schema_digest is None`
  （探测失败**不留** schema 指纹）——判据两样都断言，避免"健康失败但指纹还在"的伪装面。

## 为什么这样做

- **信封是产品契约不是夹具巧合**：MCP 结果信封由 adapter 产出、经 spill 落盘
  ⇒ 链式传参的声明面（`RunChainCall`）必须能表达"从信封里取"；在判据里预拆信封会让
  运行链对信封形态无感知，缺陷留给下一位装配者（实测 P-E：删点分分支 ⇒ 执行面 2 条红）。
- **缺席分支的方向性**：REST 适配器（`ncbi.py::_read_args`）直接 `store.get` 缺失即抛；
  MCP 允许**合法空参数**（`tools/list` 型工具），所以引入缺席分支——但方向必须是
  **fail closed**：只有声明值恰为 `b"{}"` 才回落。任何"读不到就当空"的写法都会让
  参数面悄悄失能（按压 P-A：回退成 `{}` ⇒ 15 failed）。
- **注册面的消费面分三段**：`PENDING` 不进目录/不进 pin 表/不进编译产物；
  `ACTIVE` 三段全进（`merged_catalog_snapshot` 只合并 ACTIVE）；`REVOKED` 三段全退。
  「未批准不可用」是**结构事实**（PENDING 不合并），判据只需补上它在各消费者上的证据。

## 怎么做与复现

1. 探针（只读、一次性）：`PYTHONPATH=. uv run --frozen --no-sync python -B
   scratch/probe_mcp_schema_20260930.py` ⇒ 打印三态分类的实测结果。
2. 真回环：`uv run --frozen --no-sync python -B -m pytest
   tests/contracts/test_mcp_research_server_loopback.py tests/contracts/test_mcp_registration_and_refutations.py
   tests/contracts/test_mcp_provider_arguments.py tests/contracts/test_tool_provider_contract.py -q`
   ⇒ 55 passed（既有契约 18 条逐字节未改）。
3. 按压配方：`_execute_async` 回退成 `{}`（P-A）；删 `list_tools` 的空名字把关（P-B）；
   删 digest 比对（P-D）；删点分分支（P-E）。每条复原后 raw `sha256` 与基线相等
   （`provider.py` = `fcb5c065…f51a`；`phase_capabilities.py` = `e0dc7699…b2f2`）。
4. server 自查：`uv run --frozen --no-sync python -B -m pytest tests/tooling/test_tooling_scripts_meet_product_gates.py -q`
   （`IN_SCOPE` 含 `tools/research_mcp_server.py`）。

## 适用边界

- 冻结语料是**真实记录的快照**（2026-09-30 经 Europe PMC REST 实取），**不是**实时检索；
  **不证明**任何第三方 MCP server 可 pin 可用（明写不证明）。
- 点分路径只覆盖**一层**信封写法（如 `structured.ids`）；更深的嵌套未测。
- 生产组合根**未注册** MCP provider 实例 ⇒ 目录读面健康诚实 UNKNOWN；执行面证据由
  测试装配注入真 provider（与 `ncbi_eutils` 的 injection 模式同形）⇒
  「注册后自动可执行」**尚不成立**（W-1）。
- 本 EC **未改动**任何既有判据 / 门禁 / 阈值；`IN_SCOPE` 的追加是**纯收紧**（只增不删）。
- **不得**据此宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 来源

- `PLAN-20260929-257`（GOAL-027 EC-02）与 `RECHECK-20260929-258`（§2 / §5 / §7）；
- 留档：`scratch/probe_mcp_schema_20260930.py`、`scratch/rehearse_mcp_server_20260930.py`；
- 相关代码：`tools/research_mcp_server.py`、`tests/mcp_server/raw_shapeless_tools.py`、
  `adapters/mcp/provider.py`、`packages/application/run_orchestration/phase_capabilities.py`、
  `tests/contracts/mcp_research_support.py`、`tests/contracts/test_mcp_*.py`；
- 同族记忆：[[model-absence-has-no-own-failure-category]]（分类要先实测）、
  [[press-tests-need-real-failures-not-skips]]（按压纪律）、
  [[provider-id-to-sdk-tool-mapping-missing]]（provider id 与 SDK 工具名的映射缺口的档案；
  本条是**运行链执行**路径而非会话工具路径）。
