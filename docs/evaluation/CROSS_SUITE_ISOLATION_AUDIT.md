# 跨套件隔离普查（Cross-Suite Isolation Audit）

**GOAL-015 EC-01 的事实底表**：把「本地质量门为什么不是 23/23」逐项拆成**可复现的最小命令**，
每条给出**根因**、**分类**与**修法 / 终态**。本表是**判定事实**，不是待办清单，也不是
「可以放宽某条门禁」的依据。

- **普查口径**：既有 m0 全量配方（`run_all_checks.py --profile m0 --keep-going`）+ DSN 固化
  （`RESEARCHOS_POSTGRES_DSN` pin 到 postgres-test DSN，`DATABASE_URL` / `POSTGRES_DSN` 清空
  —— 本机 `.env` 会被上游 `load_dotenv()` 注入，见 R-2）。m0 **独占运行**（避免
  `evolution_state.json` 的 `WinError 5`）。
- **三条分类**（GOAL-015 EC-02 的口径）：**(i) 真实缺陷** ⇒ 修代码；**(ii) 环境专属** ⇒
  附可复现命令 + 干净基线对照，登记为环境项，**不改判据**；**(iii) 门禁 scoping** ⇒
  **只登记**（进 GOAL-015 EC-03 的决策简报），不在循环内改门禁。

## 0. 结论摘要（2026-09-25 实测）

as-is 本机 m0 = **21/23**，两条未绿项，拆成**四个可独立复现的红项**：

| ID | 红项 | 分类 | 终态 |
| --- | --- | --- | --- |
| R-1 | 草稿列表序 tie（`python/tests` 内的 1 failed） | (i) 真实缺陷 | **已修**（三实现 tie-break 与新近一致 + 新判据） |
| R-2 | 默认门凭据泄漏（`python/tests` 的整轮红灯） | (i) 真实缺陷（测试隔离） | **已修**（夹具隔离 + 与出厂目录双向对齐判据） |
| R-3 | `framework/validate_bundle` 判红（仓库外文件） | (iii) 门禁 scoping | **只登记**（进 EC-03 决策简报） |
| R-4 | postgres 标记的跳过只在加载 `tests/postgres/conftest.py` 时生效 | (i) 真实缺陷（测试隔离） | **登记为 cycle 2（EC-02）的实施项**（本 cycle 只普查） |

## 1. R-1｜草稿列表序 tie（「按新近」不是全序）

- **判词原样**（as-is m0 的 `python/tests`）：
  `FAILED tests/contracts/test_protocol_draft_store_contract.py::test_list_orders_by_recency_and_filters_project`
  且 `1 failed, 4445 passed, 19 skipped ... in 569.15s`；断言体
  `AssertionError: assert ['pdraft_00000001', 'pdraft_00000002'] == ['pdraft_00000002', 'pdraft_00000001']`。
- **单独跑（绿）**：`pytest tests/contracts/test_protocol_draft_store_contract.py -q`
  ⇒ `9 passed`，`egress guard: judged 0 connection attempt(s); blocked 0`。
- **确定性最小复现**（0.4s，不依赖时钟运气）：
  `pytest tests/contracts/test_protocol_draft_store_order_tie.py -q`（本 cycle 新增的判据）
  ⇒ 修前 **3 failed**（SQLite / PostgreSQL / InMemory 三实现全红）。
- **根因**：`created_at` 相同时，`list()` 的 tie-break 是 `draft_id` **升序**
  （`adapters/sqlite/protocol_draft_store.py` 与 `adapters/postgres/protocol_draft_store.py` 的
  `ORDER BY d.created_at DESC, d.draft_id`；`InMemoryProtocolDraftStore.list` 的
  `sorted(key=created_at, reverse=True)` 在**稳定排序**下同样退化为插入序）⇒ 返回**旧的在先**，
  与契约用例断言的「最新在前」相反。Windows 时钟粒度约 15.6ms，同刻插入在**整轮**里必然偶发
  ⇒ 「合并跑红、单独跑绿」。**不是**历史记录里写的「共享 postgres-test 库被前序用例污染」：
  该用例用的是 `tmp_path` 下的独立 SQLite 文件。
- **修法（真实来源）**：tie-break 与新近一致（`draft_id DESC` / 排序键 `(created_at, draft_id)`
  反序）⇒ 「按新近」成为**全序**。**既有契约断言一字未改**。

## 2. R-2｜默认门凭据泄漏（出站判据按设计判红整轮）

- **判词原样**（as-is m0 的 `python/tests`）：
  `egress guard: FAIL — the default gate attempted 2 non-loopback destination(s) that no live marker allows:`
  `198.18.0.83:443 (kind=private) by tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure :: preflight_support.py:43:build_endpoint_health <- ... <- transport.py:108:_execute_request`；
  该轮 `judged 803 connection attempt(s); blocked 10`（2 条产品端点域名 + 8 条判据自身探针）。
- **单独跑（绿）**：`pytest tests/api -q` ⇒ `507 passed`、`blocked 0`。
- **确定性最小复现（2.75s，取代 569s 全量）**：
  `LLM_MAIN_KEY=<任意值> pytest tests/api/test_runs_api.py -q` ⇒ 修前 `blocked 2` + 整轮判红；
  修后 `blocked 0`、`16 passed`。
- **根因链**：`litellm` 在**导入期**调用 `load_dotenv()`（`litellm/__init__.py:27`）⇒ 本机
  gitignored `.env` 的凭据键进了**进程环境**；`services/api/preflight_support.py:92` 先
  `credentials.resolve(endpoint.credential_ref)`（`credential_ref: LLM_MAIN_KEY`），凭据**可解析**
  才继续到 `probe_connectivity` ⇒ 一个自称 hermetic（只删 DSN 键）的「未配置控制面」用例，
  于是真的去探出厂端点 `https://apihub.agnes-ai.com/v1`。出站判据在**任何数据包之前**拦下并
  判红整轮——**判据没有错，漏的是隔离**。
- **一处与既有记录的**事实更正**（本表优先）**：该红**不是**「本机 fake-IP DNS 特殊」造成的。
  `tests/egress_guard.py` 的放行面只有 `localhost`（`ALLOWED_KINDS`），任何**可解析**的非环回
  目的地都会被拦并判红；本机只是把域名解析成 `198.18.0.0/15` 使 `kind` 显示为 `private`。
  「凭据在场」才是红的原因（CI 无 `.env` ⇒ 不可解析 ⇒ 不探端点 ⇒ 全绿）。
  **处置因此是修隔离，而不是登记为环境项、更不是豁免 fake-IP 段。**
- **修法（真实来源）**：`tests/default_gate_credentials.py` 定义名单 +
  `tests/conftest.py` 的 autouse 夹具：未标记 `requires_live_llm` 的用例不得看见出厂目录声明的
  凭据键（用例结束自动还原）；名单与出厂目录的 active `credential_ref` 由
  `tests/architecture/python/test_default_gate_credential_isolation.py` **双向对齐**，并带
  **子进程按压**（注入凭据键跑默认门 ⇒ 必须 `blocked 0`）。**判据一字未动**。

## 3. R-3｜`framework/validate_bundle`：仓库外并发写者文件

- **判词**：`FAILED [framework/validate_bundle]: exit 1`（as-is m0 的唯一 framework 红）。
- **归因（既有 `R-F3` 口径，本 cycle 复测仍在）**：`scratch/self-governance-bootstrap-prompt.md`
  （**gitignored**、仓库外并发写者的在制品，**实测 `69944` B /
  `sha256:7af3209304a73d10afbfab3bf70eda29eb1982cc1aac076ff8914e05324f12c2`**）正文里的正则
  字面量被该检查的**纯文本链接扫描**读成本地链接。
- **成对归因**：同一脚本换 `CURSOR_FRAMEWORK_ROOT`，主树 `exit 1`（只此一条）、干净 worktree
  （无 `scratch/`）`exit 0` 全绿；CI 检出无 `scratch/` ⇒ **CI 不受影响**。
- **分类**：**(iii) 门禁 scoping**——该检查扫描了**不属于仓库**的目录（`scratch/` 是
  gitignored 工作区）。按 GOAL-015 授权：**不在本循环改门禁**，改为产出 EC-03 决策简报条目
  （「检查项 / 扫描范围是否应排除 gitignored 工作区」）。
- **本 cycle 的处置**：如实登记 + 提供**可复跑的归因命令**（EC-02 的归因脚本）；
  **不删不改外来在制品**（并发工作树纪律）。

## 4. R-4｜postgres 标记的跳过依赖「谁被收集」

- **A（定向跑，不收集 `tests/postgres`，PG 不可达）**：
  `RESEARCHOS_POSTGRES_DSN=postgresql://research_os@127.0.0.1:1/research_os pytest tests/api/test_worker_plane_composition.py -q`
  ⇒ **挂死**（120s 上限内无输出，`timeout` 杀掉，exit 143）。既**不跳过**也**不快失败**。
- **B（同一文件 + 收集 `tests/postgres`，PG 不可达）**：同一条 DSN 下
  `pytest tests/api/test_worker_plane_composition.py tests/postgres -q` ⇒ `16 passed, 93 skipped in 4.22s`
  （`tests/api` 里 3 条 `postgres` 标记用例被跳过）。
- **根因**：跳过逻辑只写在 `tests/postgres/conftest.py`（与 `tests/distributed/conftest.py`）的
  `pytest_collection_modifyitems`；conftest 只在 pytest 真的收集到该目录时才加载 ⇒
  「跨目录的 `postgres` 标记」在定向跑里**没有**这道守卫。
- **分类**：**(i) 真实缺陷（测试隔离）**。**修法**：把该守卫提为**加载无关**（根级 conftest 或
  共享模块），保持同一判据（PG 不可达才 skip；`RESEARCHOS_REQUIRE_POSTGRES=1` 仍 fail-closed）。
- **本 cycle 处置**：**只普查**，实施放 **cycle 2（EC-02 的本地跑法协议）**——它是「本地判定确定性」
  的直接输入（定向跑挂死会污染本地判决），不是 EC-01 的顺序依赖。

## 5. 历史签名（普查必须点名，但**今天不再复现**）

| 签名 | 出处 | 2026-09-25 实测 |
| --- | --- | --- |
| `W-D`：`test_worker_plane_composition`×3 + `test_pg_crash_restart` 合并跑红、单独跑绿 | GOAL-012 cycle 1 登记，GOAL-013/014 承继 | **不再复现**：`pytest tests/api/test_worker_plane_composition.py tests/e2e/test_pg_crash_restart.py -q` ⇒ `7 passed`（PG 在线）。**形态已由后续改动消解**；本表不再把它列为在册红项 |
| 同类历史修法（GOAL-007）：函数内定义 SDK Action 子类污染判别联合 ⇒ 提为模块级 | 既有工程记忆 | 仍是**同类修法口径**的范例：修共享来源，不调用例 |

## 6. 本表**不是**什么

- 不是「门禁太严」的清单：R-1 / R-2 / R-4 的修法都在**被测系统或测试隔离**一侧，
  R-3 是**唯一**指向门禁的条目，且按授权**只登记不改**。
- 不是「可以 skip」的许可：本表不产生任何 skip / xfail / 收集顺序调整。
- 不是「本机已全绿」的声明：R-3 仍在（见第 3 节），as-is 本地 m0 仍**不是** 23/23。
