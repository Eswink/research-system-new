---
id: PLAN-20261001-269
slug: goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility
title: GOAL-028 cycle 2（EC-02）：活检索 — 第三方 MCP 勘察结论 + 自建 server 真上游模式 + 非预置语料判据
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
    承 GOAL-20261001-028 的 **EC-02**（活检索，收 GOAL-027 的限制 ②；含限制 ③ 的勘察结论）。
    授权沿用该 GOAL 的 `authorization.ref`：「**新增真实现的 MCP server 或对既有自建 server
    扩展**」+「新增判据 / 夹具 / 探针（落 `tests/**`）」+「修实现过程中发现的真缺陷」+
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：对既有自建 server（`tools/research_mcp_server.py`）的扩展是
    **纯新增模式**（默认行为逐字不变）；`IN_SCOPE` 只**追加**（若需拆模块）；**不修改**任何
    既有判据 / 门禁 / 阈值 / 放行面（点名：`tests/contracts/test_mcp_research_server_loopback.py`、
    `tests/contracts/test_mcp_registration_and_refutations.py`、
    `tests/e2e/test_literature_chain_run_offline.py`、`tests/egress_guard.py`、
    `tests/contracts/mcp_research_support.py` 的既有常量、规模门）；**不改**出厂
    `examples/config/tool_providers.yaml` 的 provider id 集（既有判据锁死）⇒ 活检索
    **不新增出厂 provider id**；**不改** `default_effect: DENY`、`PRODUCT_ROOTS` / m0 条数 /
    作业结构（终态行仍 `23`）；**零**新依赖；**不得**把真实凭据写进任何地方；
    **不得**放开默认网络（真实出网只在显式开关下、按既有 `requires_live_llm` 口径）；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **第三方 MCP 可行性勘察结论**（落树，逐候选评定）：许可证 / 可 pin 性
      （版本·commit·digest）/ 凭据需求 / 稳定性，给出**可行或不可行 + 理由**。
      结论必须**可复核**：点名的许可台账字段（`UPSTREAM_COMPONENTS.yaml` 的
      `spdx` / `upgrade_gate`）、pin 规则（`ProviderRegistration.pinned_revision`
      的 `sha256:<64hex>` 形态）与被判据引用的**原文位置**。
    status: PENDING
  - id: AC-2
    criterion: >-
      **自建 server 的真上游模式**（默认仍是冻结语料）：新增一个**显式开关**的
      「活检索」模式 —— 走**真实上游**（`EuropePmcProvider` 的限速 / 429⇒transient /
      4xx⇒permanent / 字段归一化 / 内容寻址 digest 语义）**且仍走 MCP 协议往返**
      （同一个 server、同一对工具名）。**默认模式逐字节不变** ⇒ 既有三份 MCP 判据
      **一字不改且全绿**。
    status: PENDING
  - id: AC-3
    criterion: >-
      **非预置语料判据（正反两向）**：① **正向** —— 判据喂入**与树内冻结语料不相交**的
      上游响应（经 `httpx.MockTransport` 走真协议栈 + 真解析），断言取到的是**上游那条**
      （真标识 + 内容寻址 digest 重算相等），且该标识**不在**树内冻结语料里；
      ② **反向** —— 同一次调用在**冻结模式**下取不到该标识（缺席被点名，不编造）。
    status: PENDING
  - id: AC-4
    criterion: >-
      **离线门保持离线**：`tests/egress_guard.py` 不得放宽；活检索路径在默认门里
      **零出站**（判据断言 transport 请求计数与策略拒绝）；真实出网只在显式开关 +
      `requires_live_llm` 口径下。**触网前** URL 策略（仅 http/https + 拒绝环回 / 私有 /
      保留 + host ∈ 声明的 `network_domains`）。
    status: PENDING
  - id: AC-5
    criterion: >-
      **规模与射程**：新判据 / 新模块过四道门（ruff / format / mypy strict / 单文件 ≤ 450 行、
      单函数 ≤ 50 行）；若新增 `tools/` 脚本，**显式加入** `IN_SCOPE`（纯收紧）；
      既有判据 `git diff` 为空。
    status: PENDING
---

## 验收条件

承 GOAL-20261001-028 的 EC-02，五条 AC 见 frontmatter（AC-1…AC-5）。

**为什么 AC-2 必须是「纯新增模式」而不是「把冻结语料换成在线」**：既有三份 MCP 判据
钉住的是**确定性**（同 query 两次字节级相同 + `output_digest` 相同）与**标签语义**
（不声明网络域 ⇒ `GENERATED`）。在线检索天然不满足「同输入同字节」⇒ 换掉默认路径
等于把那些判据改成摆设（= 修改既有判据，本轮禁止）。所以活检索是**加出来的一条路**。

**为什么 AC-3 要正反两向**：只证「活模式能取到 X」还不够 —— 若 X 其实也在树内冻结语料里，
那这条判据证明不了「语料非预置」。反向臂（冻结模式下取不到 X）才把两句话分开。

## 实施清单

- [ ] **WP-A 勘察**：第三方 MCP 可行性结论（许可 / pin / 凭据 / 稳定性），落
      `docs/integration/MCP_LIVE_RETRIEVAL.md`（新文件；既有 MCP 文档同源更新）。
- [ ] **WP-B 真实上游模式**：`tools/research_mcp_server.py` 新增活检索模式（显式开关 +
      复用既有 provider 语义 + httpx.MockTransport 可注入），默认路径逐字不变。
- [ ] **WP-C 判据**：非预置语料正反两向 + 离线零出站 + 触网前 URL 策略；既有三份判据
      `git diff` 为零。
- [ ] **WP-D 记录 + 门 + 提交**：先写记录 → 记录面判据 → 全量 m0（独占、canonical DSN）
      → 显式路径提交 → push → 轮询 CI 到终态 → 台账**逐提交**。

## 证据

（执行中回填。）

## 影响报告

（收口时回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | cycle 2 派生：EC-02（活检索 + 第三方 MCP 勘察结论）。 |
