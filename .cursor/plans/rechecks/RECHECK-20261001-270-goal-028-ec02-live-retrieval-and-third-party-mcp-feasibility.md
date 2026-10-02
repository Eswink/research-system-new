---
id: RECHECK-20261001-270
slug: goal-028-ec02-live-retrieval-and-third-party-mcp-feasibility
title: GOAL-028 EC-02 复检 — 活检索（第三方 MCP 勘察结论 + 真上游模式 + 非预置语料正反两向）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-01
updated_at: 2026-10-01
plan_id: PLAN-20261001-269
parent_goal: GOAL-20261001-028
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261001-269`（GOAL-20261001-028 的 cycle 2 子计划）——把自建 MCP server 从
「冻结快照」推进到「**另有一条真去取的路**」，并给出第三方 MCP 的**勘察结论**。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | 第三方 MCP 可行性勘察结论（许可 / pin / 凭据 / 稳定性，逐条给理由） | **PASS** | `docs/integration/MCP_TOOL_PROVIDERS.md` §6.4 四维表 + 综合判定；可复核位置逐条点名（`UPSTREAM_COMPONENTS.yaml` 的 `mcp` 条目实测 `spdx: MIT` + `upgrade_gate` 四项；`packages/domain/tool_registry.py:117-121` 的 `Digest.parse(pinned_revision)` 强制 `sha256:<64hex>`）。**结论 = 不可行**（今天没有满足四条的候选） |
| AC-2 | 自建 server 的真上游模式（显式开关；默认逐字节不变） | **PASS** | 新增 `tools/research_mcp_live.py`（149 行）；`build_server(live=None)` 缺省不读环境变量、全程冻结语料；开关 `RESEARCHOS_MCP_LIVE_RETRIEVAL=1` 才走活检索；**复用**既有 `europe_pmc_runtime` 的 `assert_url_allowed` / `request_document` / `search_params` 与 `europe_pmc_parsing` 的 `normalize_search` / `ext_id_query`（不做第二份 HTTP/解析） |
| AC-3 | 非预置语料判据**正反两向** | **PASS** | 正向：专属 PMID `99000001`（不在 `CORPUS`）经真协议栈 + 真解析取回，内容寻址 digest **重算相等**；反向：前提事实（该 id 不在冻结语料）+ 冻结模式下同一 id 在 `missing` 里**点名**；**两模式同形**：字段集与冻结语料逐字相同 |
| AC-4 | 离线门保持离线（零出站；触网前策略） | **PASS** | 所有用例都在 `httpx.MockTransport` 上跑；未开关 ⇒ `_live_settings()` 返回 `None`（不构造 client）；开关值非 `'1'` 也返回 None；声明外 host / 空声明 ⇒ 拒绝且 **`settings.requests == []`**（触网**之前**）；正控制：合法 host ⇒ 请求真发出（防零请求空真）。`tests/egress_guard.py` 未改 |
| AC-5 | 规模与射程（四道门 + `IN_SCOPE` 纯收紧 + 既有判据零改动） | **PASS** | `tools/research_mcp_live.py` 149 行 / `tools/research_mcp_server.py` 294 行（≤450）；`IN_SCOPE` **只追加**一条（既有九条未删）；`tests/contracts` 全量 **1596 passed / 69 skipped**；既有三份 MCP 判据 `git diff` 为空 |

## 按压（先红后绿 + 逐字节复原）

| 编号 | 做法 | 结果 | 复原取证 |
| --- | --- | --- | --- |
| P-2 | 架空活检索模式的**触网前** URL 策略（删 `assert_url_allowed` 调用） | **2 failed**（`TestTheUrlPolicyRunsBeforeAnyRequest` 两条零请求判据） | 恢复后 `sha256sum -c` 逐字节一致：`research_mcp_live.py` = `8049c2a6…`、`research_mcp_server.py` = `c1b8381c…`；14 passed |

## 复检发现（三处按实测校准）

1. **`tools/` 不是包 ⇒ 静态 `tools.` 导入会让同一文件有两个模块身份**（真问题）：
   live 模块首版用 `from tools.research_mcp_live import ...`，`test_in_scope_scripts_pass_mypy`
   实测判红：`Source file found twice under different module names: "research_mcp_live" and
   "tools.research_mcp_live"`。修法照**仓内既有先例**
   （`tools/verify_goal027_closeout.py::load_standard` 的 `spec_from_file_location`），
   并用 `_LiveModule` Protocol 给动态模块定形（否则 mypy 报 `object has no attribute`）。
2. **`tools/` 整目录扫描会撞 73 条历史 lint 错误**（已知边界，承 GOAL-023 `W-1`）：
   `tools/` 仍有大量历史脚本不在射程内 ⇒ 只能按 `IN_SCOPE` 逐文件扫（判据本身即如此实现）。
3. **判据首版把两模式同形写成「全字段相等」**（判据侧过强）：上游 payload 的
   `journal`/`year` 是判据自己填的，与冻结语料那条不同 ⇒ 断言自伤。改为
   「字段集逐字相同 + 上游响应里照抄的字段（pmid/doi/title）原样回来」——
   证的仍是同形，且不再依赖判据自己造的值。

## WARNINGS（逐条登记，本 EC 不消解）

- **`W-1`｜活检索的**真实出网**未在本轮实跑**：本机 DNS 走 fake-IP 代理（198.18/15），
  且默认门必须离线 ⇒ 活模式只用 `httpx.MockTransport` 验证「真协议栈 + 真解析 + 真策略」。
  **含义**：证的是**路径成立**，不是「今天上游可达」；真实出网按既有 `requires_live_llm`
  口径另行开启（本轮未开）。这条与 EC-01 的 `W-1` 同类：**机制成立 ≠ 已实跑联网**。
- **`W-2`｜默认门看不见子进程出站**（承 GOAL-028 事实层第 22 条）：`tests/egress_guard.py`
  的射程不含子进程 ⇒ stdio server 子进程内的出站不在守卫内。本 EC 的对策是
  **显式开关 + 判据自身断言**（MockTransport 计数 + 默认不构造 client），不是守卫。
  真实运行下若要更强保证，需要另设机制（未做）。
- **`W-3`｜活模式的限速是进程内的**：`LiveSettings.last_request_at` 只约束**本进程**的
  连续请求；多副本 / 多进程并发时无全局节流（上游礼貌间隔因此是「每进程」语义）。
- **`W-4`｜活模式只覆盖 `literature_search` / `literature_read`**：与冻结模式同一对工具，
  不新增工具名（这是刻意的：新增工具名会撞既有判据的工具面断言）。
- **`W-5`｜第三方结论是**静态判断**而非实测**：结论基于本仓现有 pin 规则与许可台账；
  若将来出现给出 `sha256:` 制品 digest 且已登记许可的打包型 server，判断需要重做
  （该路径已写在 §6.4 的四条前置里）。
- **`W-6`｜活检索未接进运行链**：EC-03 的「默认装配完整闭环」仍走冻结语料；
  「活检索 + 运行链」的组合不在本 EC 射程。

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

GOAL-20261001-028 的 **EC-02 达成**：① 第三方 MCP 的**勘察结论在树**
（四维判定 + 可复核位置，结论 = 以现有 pin 规则**不可行**，理由逐条）；
② 自建 server 新增**真上游模式**（默认逐字节不变、复用既有 provider 零件、触网前策略）；
③ **非预置语料正反两向**（专属标识正向取得到 / 冻结模式取不到 / 两模式同形）；
④ **离线门仍离线**（零出站 + 正控制）。
六条 `W-NN` 如实登记（尤以 `W-1`：**机制成立 ≠ 已实跑联网**）。

**本地门终态**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` = 24 / `FAILED [` = 0 /
EXIT=0 / **4969 passed / 21 skipped**；日志 `scratch/goal028-c2b-m0.log`，记录写入后独占运行、
canonical DSN pin、不接管道、零进程残留）；治理 `validate.py` 绿；记录面判据 19 passed。

**本地门首跑抓到两处（判据侧，均已修）**：① 新判据文件**格式漂移** ⇒ `python/format-check`
判红（`ruff format` 修）；② 协议往返臂直接取 `result.content[0].text` ⇒ mypy `union-attr`
（SDK 的 `content` 是文本/图片/音频/资源链接/内嵌资源的**联合**）⇒ 加 `_text_payload`
按 `type == "text"` 取并**如实判错**（找不到文本即断言失败，不静默取第一个）。
