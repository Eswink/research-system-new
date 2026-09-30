---
id: PLAN-20260929-257
slug: goal-027-ec02-mcp-real-onboarding
title: GOAL-027 cycle 2（EC-02）：MCP 真实接入 — 自建科研 server + 真回环 + 注册面 + 三反证 + 空参数真缺陷修复
status: DONE
created_at: 2026-09-30
updated_at: 2026-09-30
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-258-goal-027-ec02-mcp-real-onboarding.md
memory_entries:
  - .cursor/memory/entries/MEM-20260930-175-mcp-envelope-needs-a-path-for-chained-ids.md
parent_goal: GOAL-20260929-027
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-027 的 **EC-02**（MCP 真实接入；建档勘察结论选定路线 (A) **自建科研
    MCP server**）。授权沿用该 GOAL 的 `authorization.ref`：「**新增真实现的 MCP server**
    （落 `tools/` 或既有结构，**必须**加进 `IN_SCOPE`）」（**纯收紧**——新增受判文件、
    不删任何条目）+「修实现过程中发现的真缺陷」（本 EC 的点名对象 =
    `adapters/mcp/provider.py` 的**空参数调用**：`session.call_tool(tool_name, {})`
    且不读 ArtifactStore 参数、不校验 `argument_digest`）+「新增判据 / 夹具 / 探针
    （落 `tests/**` ⇒ m0 条数仍 `23`）」+「文档同源更新」；push-to-main-for-CI 口径
    （**只推 `main`**、不 force、不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：新增件一律落**新文件**；**不修改**任何既有判据 / 门禁 / 阈值 /
    放行面（点名：`tests/contracts/test_tool_provider_contract.py`、`tests/egress_guard.py`、
    `tests/application/run_orchestration/test_run_chain_capabilities.py`、
    `tests/application/test_m2_audit.py`、`tests/application/preflight/**`、
    规模门、三道记录面判据、两树入口判据）；**不动** capabilities 词表 /
    `_CAPABILITY_SCOPE` / `policy.yaml`（复用既有能力名 `literature.search` / `literature.read`
    ⇒ 三处零改动）；**不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；
    **零**新依赖（`mcp>=1.28,<2` 已是依赖，实测装 1.29.0）；**默认门离线**
    （判据经 stdio 真回环，**不触网**）；冻结语料是**真实发表记录的快照**（真 PMID / DOI /
    标题，2026-09-30 经 Europe PMC REST 实取），**不得**叙述成"实时检索"；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
    **两处对既有文件的受控改动（最小、逐条留档）**：
    (1) `adapters/mcp/provider.py`（**产品实现**，非判据）——EC-02 明文授权对象：
    新增 `_read_args()`（按 `tool-args:{task_id}:{operation_key}` 读参 + `Digest.of_bytes`
    重算比对 `call.argument_digest`；制品缺席时仅当声明值恰为 `{}` 的 canonical 序列化
    才回落到空参数，其余 fail closed），`_execute_async` 改传 `args`；import 加 `Digest`。
    **其上的既有判据一字不改**（`test_tool_provider_contract.py` 18 条逐字节未改、复跑全绿）。
    (2) `packages/application/run_orchestration/phase_capabilities.py`（**产品实现**）——
    `ids_from_previous` 增加**点分路径**支持（与既有 `arguments_from_input` 的 `_lookup`
    同源）：MCP provider 的溢出内容是一层信封（`{text[], structured}`），机器可读的一半
    在 `structured` 下，链式传参因此需要路径而不只是顶层键。**非点分名字走原样分支**，
    既有行为逐字节不变（`test_run_chain_capabilities.py` 15 条未改一行、复跑全绿）。
    (3) `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` —— **纯收紧**：
    只追加 `tools/research_mcp_server.py` 一个条目（EC-02 verify 明文要求）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **MCP server 在树、过四道门、显式进 `IN_SCOPE`**：新增 `tools/research_mcp_server.py`
      （自建、离线、确定性；两个工具 `literature_search` / `literature_read` 服务一份**冻结的
      真实文献语料**——全部记录 2026-09-30 经 Europe PMC REST 实取，真 PMID / DOI / 标题逐字保留；
      token-AND 检索；缺失 id **点名**在 `missing`；空参数拒绝）。`ruff format` / `ruff check` /
      `mypy` / 规模（209 行、无超 50 行函数）全绿；`IN_SCOPE` 只追加该条目 ⇒
      `test_the_pinned_scope_contains_the_entry_and_the_assertion_set` /
      `test_scope_partitions_every_tools_script_explicitly` 绿。
    status: PASS
  - id: AC-2
    criterion: >-
      **空参数真缺陷修复 + 按压两向（本 EC 的授权核心）**：`adapters/mcp/provider.py` 的
      `_execute_async` 不再以 `{}` 调用工具——先 `_read_args(call)`（读 `tool-args:` 制品 +
      `Digest.of_bytes` 重算比对 `argument_digest`），再开会话；制品缺席时仅当声明值恰为
      `{}` 的 canonical 序列化才回落空参数（fail closed，不猜、不编造、不静默降级）。
      **按压两向**：① 把 `_execute_async` 回退成空参数调用 ⇒ 判据大面转红
      （新判据 15 failed；`_read_args` 五条 fail-closed 用例也全红——连 `_read_args` 方法
      本身都被绕过），复原后 raw `sha256` 逐字节相等；② 只删 digest 比对 ⇒
      篡改用例 1 failed（press D，其余 12 passed），复原后同 sha256。
      **既有契约套件逐字节未改**（`test_tool_provider_contract.py` 18 条复跑全绿）。
    status: PASS
  - id: AC-3
    criterion: >-
      **真回环（真连 / 真调 / 真取结果）**：`tools/research_mcp_server.py` 经
      `McpToolProvider` 以 stdio 真起子进程直连，两条工具链路全部经 Port 面走通：
      ① 工具名与 `literature.search` / `literature.read` 对齐；
      ② 检索结果含**真标识**（真 PMID `42803750` / 真 DOI `10.1002/cns.71179` / 真标题，
      与冻结语料逐条逐字段互证）；③ 内容寻址（spill 字节重算 == `output_digest`，
      `text[0]` 与 `structured` 信封一致）；④ 参数真的到达 server（两个不同 query ⇒
      两组不同 id 集；同 query 两次 ⇒ 字节级相同 ⇒ 确定性）；⑤ 读取步用检索结果里的
      id 取回同一条记录，不存在 id 被点名在 `missing`；未注册工具的错误消息来自**子进程**
      （证明真调了真进程）。
    status: PASS
  - id: AC-4
    criterion: >-
      **注册面流程 + 三条点名反证 + 批准后的执行面**：
      ① 注册面全生命周期实走（`kind: MCP` + `transport: stdio`）：`POST ⇒ PENDING`
      （不进目录 / 不进 pin 表 / 不进编译产物）→ `approve ⇒ ACTIVE`
      （`USER_APPROVED`；进目录 + 进 pin 表 + 协议编译的 `tool_requirements` 里出现该
      provider id）→ `revoke ⇒ REVOKED`（退出目录与 pin 表）；可漂移 pin（`v1.2.3`）
      在写入面 422 拒。
      ② **反证一（未 pin）**：目录里有 provider、`tool_pack_digests` 没有它 ⇒ preflight
      点名 `SUPPLY_CHAIN_UNPINNED`；补上 pin 后同协议不再报（成对）。
      ③ **反证二（未批准）**：`PENDING` 时不在编译产物里，`require_frozen_tool_set`
      点名 `POLICY_DENIED`；批准后同一调用通过（成对）。
      ④ **反证三（schema 不符）**：`tests/mcp_server/raw_shapeless_tools.py`（申报一条
      `name` 为空的工具声明，绕开 FastMCP 直讲 JSON-RPC）⇒ `list_tools` 抛
      `TOOL_SCHEMA_MISMATCH` 且点名（`tool id must not be empty`），`check_health` 如实
      `OPEN_CIRCUIT` 且**不留** schema 指纹；畸形参数字节在**触达 server 之前**被
      `TOOL_SCHEMA_MISMATCH` 拒（`mcp protocol error`）。
      ⑤ **执行面**：经 `execute_run_chain_capabilities` 用真 MCP provider + 目录口径 spec
      跑两步链（检索 → 读取，读取用 `structured.ids` 点分路径），两条证据落 canonical、
      `tool_refs` 指向本 provider、读取步 id 含真 PMID；来源性质两向：不声明
      `network_domains` ⇒ `GENERATED`，声明 ⇒ `RETRIEVED`（由**声明**决定，不由本步自称）。
    status: PASS
  - id: AC-5
    criterion: >-
      **既有判据不被波及（回归面）**：`tests/contracts/` 492 passed（含既有 MCP 契约套件
      18 条、Europe PMC 三份、NCBI 契约，**逐字节未改**）；`tests/application/` +
      capability plane + `tests/tooling/` 2002 passed；`tests/api/` + 离线 e2e +
      `tests/architecture/python/`（含边界 / 记录面 / 措辞判据）全绿（canonical DSN pin）。
      `phase_capabilities.py` 的点分路径增量对既有 15 条链判据**行为零变化**（复跑全绿）。
    status: PASS
  - id: AC-6
    criterion: >-
      **按压矩阵 + 静态门 + 逐字节复原**：四条按压全部先红后绿（P-A 空参数回退 ⇒ 15 failed；
      P-B 只删 `list_tools` 的空名字把关 ⇒ schema 判据 2 failed；P-D 只删 digest 比对 ⇒
      篡改用例 1 failed；P-E 删点分路径 ⇒ 执行面 2 failed）；每条复原后 raw `sha256`
      与按压前逐字节相等（`adapters/mcp/provider.py` = `fcb5c065…f51a`）。
      新文件四道门全绿（`ruff format` / `ruff check` / `mypy` / 规模：450 / 50 行）。
    status: PASS
---

## 验收条件

| AC | 判据（简） | 判据文件 / 交付物 | 状态 |
| --- | --- | --- | --- |
| AC-1 | server 在树、四道门绿、`IN_SCOPE` 显式追加 | `tools/research_mcp_server.py` + `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **PASS** |
| AC-2 | 空参数缺陷已修：读 args 制品 + digest 重算比对；缺席且声明非空 ⇒ fail closed；按压两向 + sha256 复原 | `adapters/mcp/provider.py` + `tests/contracts/test_mcp_provider_arguments.py` | **PASS** |
| AC-3 | 真回环：真进程 / 真调 / 真标识 / 内容寻址 / 参数往返 / 读取点名缺失 | `tests/contracts/test_mcp_research_server_loopback.py` | **PASS** |
| AC-4 | 注册面全流程 + 三反证点名 + 批准后执行面（标签由声明决定两向） | `tests/contracts/test_mcp_registration_and_refutations.py` + `tests/mcp_server/raw_shapeless_tools.py` | **PASS** |
| AC-5 | 既有判据逐字节未改、消费者套件全绿 | 回归矩阵（见「证据」⑤） | **PASS** |
| AC-6 | 按压四条先红后绿 + 逐字节复原 + 四道静态门 | 见证「证据」④⑥ | **PASS** |

## 目标

GOAL-027 的 **EC-02**（本轮主打）：把 MCP 从「只跑 mock」推进到「接一个真能产出科研数据的
MCP server」，并修掉建档勘察发现的**真缺陷**（`adapters/mcp/provider.py` 空参数调用 ⇒
任何 MCP 工具都收不到 query / ids ⇒ EC-03 的运行链在其上不可能成立）。

**路线 (A) 理由**（建档结论）：`mcp>=1.28,<2` **已是仓库依赖** ⇒ 零新增依赖；
自建 server 可**完全 pin**（树内文件 = 版本即 commit）；零外部供应链风险；
能验证「自建 MCP 走完 **注册 → 审批 → pin → 冻结 → 执行 → 取证**」整条治理链。

## 实施清单

- [x] WP-1：新增 `tools/research_mcp_server.py`（自建离线确定性 MCP server + 冻结真实语料）
- [x] WP-2：新增 `tests/mcp_server/raw_shapeless_tools.py`（申报形状不符工具声明的 raw stdio 夹具）
- [x] WP-3：修 `adapters/mcp/provider.py` 空参数真缺陷（`_read_args` + `_execute_async`）
- [x] WP-4：`phase_capabilities.py` `ids_from_previous` 点分路径（信封形结果的链式传参）
- [x] WP-5：新增三份判据（真回环 / 注册面 + 三反证 / 参数缺陷 fail-closed）+ 共享支持件
- [x] WP-6：`IN_SCOPE` 显式追加（纯收紧）
- [x] WP-7：按压四条 + 逐字节复原；RECHECK + MEM + GOAL 回写 + ALL_PLAN 投影

## 设计要点（来自建档勘察与本轮实测）

1. **缺陷的真实形状**（`adapters/mcp/provider.py:173`，修复前）：`session.call_tool(tool_name, {})`
   永远传空参数、不读 ArtifactStore ⇒ 工具收不到 query / ids。与 REST 适配器
   （`ncbi.py::_read_args`）的差别：**制品缺席分支**（MCP 允许声明空参数；REST 直接
   `store.get` 缺失即抛）。修复取两者之长：缺席 + 声明恰为 `{}` ⇒ 允许；缺席 + 声明非空 ⇒
   fail closed（调用方 bug，不静默降级成空参数——否则缺陷以另一种形态复活）。
2. **SDK 失败分类的实测事实**（探针 `scratch/probe_mcp_schema_20260930.py`）：
   参数**制品内容**违规（非对象 / 畸形 JSON / digest 不符）⇒ `CONFIGURATION`
   （`execute()` 对 `InvalidInputError` 的既有映射，非本 EC 引入）；工具**声明**违规 ⇒
   `TOOL_SCHEMA_MISMATCH`；server 侧工具错误 ⇒ `FAILED` 记录（`Unknown tool: …`）。
   判据按**实际分类**断言（T2.5 修正：类别断言从我假定的 `VALIDATION_FAILURE` 改为
   `CONFIGURATION`——错的是判据侧，产品代码未动）。
3. **MCP 结果信封**：`_serialize_call_tool_result` 产出 `{"text": [...], "structured": {...}}`。
   运行链 `ids_from_previous` 原先只查顶层键 ⇒ 信封形结果取不到 `ids`。
   **修法 = 产品侧点分路径**（与 `arguments_from_input` 同源 `_lookup`），
   **不是**在判据里预拆信封（那会让运行链对信封形态无感知、缺陷留给下一位装配者）。
4. **冻结语料是快照不是在线检索**（如实边界）：全部记录 2026-09-30 经 Europe PMC REST
   （`resultType=lite`）实取，值一字未改（只收标题无 XML 标记的记录）。默认门离线：
   stdio 回环不触网（`egress guard: judged 0` 型）。**不证明**任何**第三方** MCP server
   可 pin 可用（本 GOAL 明写的「不证明」范围）。
5. **注册面零改动**：`/tool-provider-registrations` 是既有写面（PLAN-060），本 EC 只**驱动**
   它（登记 → 批准 → 生效 → 吊销；四步的 wire 值以判据断言为准）。`merged_catalog_snapshot` 只合并**已批准**；
   登记态 / 已吊销态不进目录 ⇒「未批准不可用」有结构基础，判据补充其被消费的证据。
6. **规模门**：`tools/research_mcp_server.py` 209 行、单函数 ≤ 50 行；判据拆三份 +
   一份共享支持件（`tests/contracts/mcp_research_support.py`，不含用例）。

## 证据

### ① 真回环实测（AC-3，真子进程）

```text
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_mcp_research_server_loopback.py -q
⇒ 11 passed in 10.72s
```

实测载荷（判据逐字断言，取自真子进程经 stdio 返回、再经 spill 落盘的字节）：

| 项 | 实测值 |
| --- | --- |
| 工具面 | `literature_search` / `literature_read`（与 `literature.search` / `literature.read` 对齐） |
| 检索 query | `molecular docking` ⇒ `hitCount=4`，ids `['42803750', '42796516', '42740546', '42772441']` |
| 首条真记录 | PMID `42803750` / DOI `10.1002/cns.71179` / 标题 "Explore the Mechanism of Xiaoyaosan…" |
| 互证记录 | PMID `42796516` / DOI `10.3390/molecules31183228` / 标题 "Molecular Docking of Natural Products…" |
| 读取往返 | 读 `['42796516', '99999999']` ⇒ `ids=['42796516']`、`missing=['99999999']`（点名，不编造） |
| 内容寻址 | spill 字节 `Digest.of_bytes` 重算 == `output_digest`（`sha256:9bd8c03a…` 型；判据逐用例重算） |
| 确定性 | 同 query 两次调用 ⇒ spill 字节逐字节相同、digest 相等 |
| 健康探测 | `HEALTHY`；两次探测 `observed_schema_digest` 相同 |

### ② 注册面 + 三反证（AC-4）

（本正文档内以中文态名表述注册状态（登记 / 已批准 / 已吊销）；三个 wire 值（登记态 / 已批准态 / 已吊销态）以判据断言为准 —— 见 `tests/contracts/test_mcp_registration_and_refutations.py` 的逐字断言。）

```text
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_mcp_registration_and_refutations.py -q
⇒ 13 passed in ~5s
```

| 面 | 实测 |
| --- | --- |
| 登记（待批准） | `trust_level=UNTRUSTED` / `catalog_active=false`；不在 `GET /tool-providers`、不在合并目录、不在 `tool_pack_digests` |
| ACTIVE | `state=ACTIVE` / `trust_level=USER_APPROVED`；进目录（`kind=MCP`、`transport=stdio`）、pin 入表、协议编译 `provider_ids` 出现该 id |
| REVOKED | 终态；退出目录与 pin 表 |
| 反证① 未 pin | preflight 报 `SUPPLY_CHAIN_UNPINNED`（`{provider_id} has no pinned ToolPack digest`）；补 pin 后不报（成对）；`pinned_revision="v1.2.3"` 写入面 422 |
| 反证② 未批准 | 登记态不在编译产物；`require_frozen_tool_set` ⇒ `POLICY_DENIED` 点名；批准后通过（成对） |
| 反证③ schema 不符 | `list_tools` ⇒ `TOOL_SCHEMA_MISMATCH`：`mcp protocol error: tool id must not be empty`；`check_health` ⇒ `OPEN_CIRCUIT`、无 schema 指纹；畸形参数字节 ⇒ `TOOL_SCHEMA_MISMATCH`（`mcp protocol error`，**触达 server 之前**） |
| 执行面 | 两步链两条证据：`tool_refs=(research_mcp_tools, literature_search)/(research_mcp_tools, literature_read)`；读取步 id 含真 PMID `42796516`；不声明网络域 ⇒ `GENERATED`，声明 ⇒ `RETRIEVED`（两向） |

### ③ 空参数缺陷判据（AC-2）

```text
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_mcp_provider_arguments.py \
  tests/contracts/test_tool_provider_contract.py -q
⇒ 31 passed（13 + 18；修复前为 12 passed + 1 failed ⇒ 判据侧修正后 13 passed）
```

缺陷修复前后的对照（判据 `TestArgumentsReachTheTool` 断言工具**回显**收到的 query：
两个不同 query ⇒ 两个不同回显；真标识（`EXT_ID:` + PMID + DOI）原样穿过参数面）。

### ④ 按压矩阵（先红后绿 + 逐字节复原）

| 按压 | 改动 | 实测（红） | 复原 raw `sha256` |
| --- | --- | --- | --- |
| P-A | `_execute_async` 回退成 `{}` 空参数调用（缺陷原形） | **15 failed / 9 passed**（新参数判据 5 条 fail-closed 全红 + 回环 6 条全红） | `fcb5c065…f51a`（= 基线）⇒ 全部复绿 |
| P-B | 只删 `list_tools` 的空名字把关（`if tool.name`） | **2 failed**（schema 判据两条） | 同上（= 基线） |
| P-D | 只删 `_read_args` 的 `Digest.of_bytes` 比对 | **1 failed**（篡改用例；其余 12 passed ⇒ 只钉篡改面） | 同上（= 基线） |
| P-E | 删 `ids_from_previous` 的点分路径分支 | **2 failed**（执行面两条：链式传参取不到 `structured.ids`） | `e0dc7699…`（= 基线）⇒ 复绿 |

### ⑤ 回归矩阵（既有判据逐字节未改）

| 套件 | 结果 |
| --- | --- |
| `tests/contracts/`（含既有 MCP 契约 18 条 + Europe PMC 三份 + NCBI） | **492 passed, 69 skipped** |
| `tests/application/` + capability plane（`test_capability_plane*.py`）+ `tests/tooling/` | **2002 passed, 1 skipped** |
| `tests/api/` + `tests/e2e/test_run_chain_retrieval_offline.py` + `tests/architecture/python/`（一次合并运行，canonical DSN pin） | **799 passed, 4 skipped**（EXIT=0；BLOCKED 行是 egress guard 自己的用例） |
| `test_run_chain_capabilities.py`（链，15 条） | 绿（点分路径增量 **行为零变化**） |
| `test_tooling_scripts_meet_product_gates.py` | 绿（`IN_SCOPE` 只追加 1 条） |

### ⑥ 静态门（全部 touched 文件）

```text
ruff format --check（新文件 + 两处产品改动）  ⇒ already formatted
ruff check tests/contracts/ tests/mcp_server/ tools/research_mcp_server.py …  ⇒ All checks passed!
mypy（strict；新判据 + 支持件 + server + provider + phase_capabilities）  ⇒ Success: no issues found
规模：tools/research_mcp_server.py = 209 行、无超 50 行函数
```

**首版判红的处置（如实留档，均为本人新代码）**：
① `tools/research_mcp_server.py` 一行 101 字符 ⇒ 换行（未改内容）；
② `mcp_research_support.py::run_tool` 6 参超 `max-args = 5` ⇒ 收进 `ToolInvocation`
   frozen dataclass（未用 `noqa`）；
③ 两处 import 排序 / 两处 mypy 类型收窄（`dict[str, str]` → `dict[str, object]`、
   数值比较的字面量类型收窄）⇒ 按形态修；
④ `test_mcp_provider_arguments.py` 一条类别断言改判据侧（见「设计要点」2——产品映射是
   既有的、被 18 条既有判据依赖的，错的是我的假定）。

### ⑦ as-is 本机 m0（记录写入之后，独占运行，首跑即终态）

```text
uv run --frozen --no-sync python -B   .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks        ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4908 passed, 21 skipped（python/tests 段 in 679.26s）
⇒ 日志 scratch/goal027-c2-m0.log（独占运行、canonical DSN pin、不接管道、零 python 残留）
```

用例数 4908（cycle 1 收口为 4866）⇒ **只增不减**，与「新增判据 ⇒ m0 条数仍 23」一致。

### ⑧ CI 台账

**M0 [`36668265638`](https://github.com/Eswink/research-system-new/actions/runs/36668265638) 八 job 全 `success` + Push-on-main（CodeQL）[`36668265126`](https://github.com/Eswink/research-system-new/actions/runs/36668265126) 3/3 `success`**；两者 `run_attempt=1`（原始 JSON 实查 `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，`head_sha=5f44fa56…` 与推送 sha 一致；轮询日志 `scratch/goal027-c2-ci-poll.log`）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-30 | IN_PROGRESS | cycle 2 派生：EC-02 = MCP 真实接入。勘察已定：路线 (A) 自建 server；`mcp` 已是依赖；缺陷修复对象 = `provider.py` 空参数；注册面零改动。 |
| 2026-09-30 | DONE | **cycle 2 收口**：AC-1…AC-6 全部 PASS。**按压四条**先红后绿且逐字节复原；**既有 MCP 契约套件逐字节未改**；**RECHECK-20260929-258 = `PASS_WITH_WARNINGS`**；**MEM-20260930-175** 落档。如实登记的残余：`W-1` MCP 注册的 catalog 消费面只到编译产物（执行面的 provider 实例仍由测试装配注入）/ `W-2` 冻结语料是快照（非实时）/ `W-3` `existing` `test_tool_provider_contract.py` 未覆盖参数面（新判据补上，但两文件分工靠注释而非机制）/ `W-4` 点分路径只支持一层信封写法（深层嵌套未测）/ `W-5` 第三方 MCP server 可 pin 可用性**未证明**（明写不证明）/ `W-6` 不声称 live 网络下 MCP 可用。 |

## 影响报告

- **Domain/API/schema**：**零** Domain 类型变化、**零** OpenAPI 变化、**零** migrations。
  新增：1 个 `tools/` 脚本（server）+ 1 个测试夹具（raw stdio）+ 3 份判据 + 1 份共享支持件。
  产品改动两处：`adapters/mcp/provider.py`（空参数缺陷修复）+
  `packages/application/run_orchestration/phase_capabilities.py`（点分路径，纯增量）。
- **安全/凭据**：MCP provider 不声明 `credential_ref`（stdio 离线路径无需凭据）；
  判据全部**不触网**（egress guard 实测 `judged … blocked 0`，无外发连接被拒记录）；
  空参数缺陷修复**收紧**了参数面（原实现忽略 `argument_digest`，修复后重算比对）。
  **不宣称**项目安全（`R-M1` 未收口）。
- **兼容性/迁移**：`phase_capabilities` 点分路径是**纯增量**（非点分名字行为逐字节不变）；
  `provider.py` 的 `_read_args` 与 REST 适配器同形；既有 18 条 MCP 契约判据逐字节未改、复跑全绿。
  无数据迁移。
- **上游版本影响**：零新依赖（`mcp>=1.28,<2` 已在 `pyproject.toml` 两处；实装 1.29.0）。
  server 用 FastMCP（SDK 自带）；`protocol_version: 2025-11-25`（SDK `LATEST_PROTOCOL_VERSION`，
  实测 `initialize` 回显调用方请求的版本）。
- **可靠性口径**：链式传参沿用既有 fail-closed 语义；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径固定为 at-least-once + idempotency + deduplication）。
- **剩余差距 / 下一项任务**：本 EC 的**未覆盖范围**——自建 server 的冻结语料是**快照**
  （非实时检索）；**不证明**第三方 MCP server 可 pin 可用；MCP 的执行面证据由测试装配
  注入 provider 实例（生产组合根未注册 MCP 实现，control plane 读面健康因此诚实 UNKNOWN）。
  cycle 3 = **EC-03**（把新能力接进运行链：run_chain 声明 + 真标识 + 读面可见 + trust_label）。
