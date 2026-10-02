---
id: PLAN-20261001-269
slug: goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility
title: GOAL-028 cycle 2（EC-02）：活检索 — 第三方 MCP 勘察结论 + 自建 server 真上游模式 + 非预置语料判据
status: DONE
created_at: 2026-10-01
updated_at: 2026-10-01
latest_recheck: .cursor/plans/rechecks/RECHECK-20261001-270-goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility.md
memory_entries:
  - .cursor/memory/entries/MEM-20261001-181-tools-is-not-a-package-so-load-by-path.md
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

- [x] **WP-A 勘察**：第三方 MCP 可行性结论（许可 / pin / 凭据 / 稳定性），落
      `docs/integration/MCP_TOOL_PROVIDERS.md` §6.4；结论 = **不可行**（今天无满足四条的候选），
      活检索走 §6.5 的自建 server 扩展。⇒ commit `19d52f7`
- [x] **WP-B 真实上游模式**：`tools/research_mcp_live.py`（149 行）+ server 的
      `build_server(live=None)` 缺省不变 + 显式开关 + 按路径加载（`tools/` 不是包）。⇒ commit `19d52f7`
- [x] **WP-C 判据**：非预置语料正反两向 + 两模式同形 + 触网前策略零请求（含正控制）+
      默认零出站 + **协议往返**（in-memory 会话真 `call_tool`）。⇒ commit `9b53c21`
- [x] **WP-D 记录 + 门 + 提交**：本回写提交 + `RECHECK-20261001-270`。

## 证据

**交付物**

| 面 | 文件 | 作用 |
| --- | --- | --- |
| 勘察结论 | `docs/integration/MCP_TOOL_PROVIDERS.md` §6.4 / §6.5 | 四维判定表 + 综合判定 + 活检索模式说明 |
| 活检索 | `tools/research_mcp_live.py`（149 行） | 真打 Europe PMC REST；复用既有 provider 零件；触网前策略 |
| 模式开关 | `tools/research_mcp_server.py`（294 行） | `build_server(live=None)`；开关 `RESEARCHOS_MCP_LIVE_RETRIEVAL=1`；按路径加载 |
| 判据 | `tests/contracts/test_mcp_live_retrieval_offline.py`（298 行） | 14 passed |
| 射程 | `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **纯追加**一条 |

**实测结果**

- 新判据：**14 passed**；
- `tests/contracts` 全量：**1596 passed / 69 skipped**（既有三份 MCP 判据**一字未改**）；
- `tests/tooling` 四道门：**8 passed**；
- MockTransport 冒烟：真解析取回 `{pmid: 99000001, doi: 10.9999/goal028.live.1, ...}`
  与内容寻址 digest，请求计数 1。

**非预置语料正反两向（原文口径）**：正向 —— 专属 PMID `99000001`（**不在** `CORPUS` 里）
经真协议栈取回，digest 重算相等；反向 —— 冻结模式下同一 id 落 `missing` 被**点名**；
另断言两模式**字段集逐字相同**（同一条记录经两条路产出相等）。

**离线取证**：全部用例在 `httpx.MockTransport` 上；未开关 ⇒ `_live_settings()` 返回 `None`
（**不构造 client**）；开关值 `true`/`yes`/`0`/`''` 一律不启用；声明外 host / 空声明 ⇒
拒绝且 **`settings.requests == []`**；**正控制**：合法 host ⇒ 请求真发出。

**按压 P-2（先红后绿 + 逐字节复原）**：架空 `assert_url_allowed` ⇒ 两条零请求判据
**2 failed**；恢复后 `sha256sum -c` 逐字节一致（`research_mcp_live.py` = `8049c2a6…`、
`research_mcp_server.py` = `c1b8381c…`）且 14 passed。

## 影响报告

- **Domain/schema 变化**：无（未动域类型、未动 schema）。
- **API 变化**：无新路由、无 DTO 变化。
- **安全/凭据变化**：活检索**不解析任何凭据**（Europe PMC 检索无需凭据 ⇒ 不声明
  `credential_ref`，也就不可能转发别的域的令牌）；出站走**既有** `assert_url_allowed`
  （仅 http/https + 保留类拒绝 + host ∈ 声明域名），触网前判定。
- **网络姿态**：**默认门仍离线**（未开关不构造 client）；`tests/egress_guard.py` 未改；
  真实出网按既有 `requires_live_llm` 口径，本轮**未开**（`W-1`）。
- **兼容性/迁移风险**：无迁移。默认路径（未开关）行为逐字节不变，由既有三份 MCP 判据守住。
- **上游版本影响**：无依赖改动（`mcp`/`httpx` 均为既有依赖）。
- **下一项任务**：GOAL-028 **EC-03**（默认装配上的完整闭环）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | cycle 2 派生：EC-02（活检索 + 第三方 MCP 勘察结论）。 |
| 2026-10-01 | DONE | 四件 WP 全部落树；判据 14 passed、`tests/contracts` 1596 passed、既有 MCP 判据一字未改；按压 P-2 先红后绿 + 逐字节复原；`RECHECK-20261001-270` = `PASS_WITH_WARNINGS`（六条 WARNING 如实登记，尤以 `W-1`「机制成立 ≠ 已实跑联网」）。 |
