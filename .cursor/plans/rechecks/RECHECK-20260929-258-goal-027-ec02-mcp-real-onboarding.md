---
id: RECHECK-20260929-258
slug: goal-027-ec02-mcp-real-onboarding
title: GOAL-027 EC-02 复检：MCP 真回环 / 空参数缺陷修复与按压 / 注册面与三反证 / 冻结语料 provenance / 回归面
plan_id: PLAN-20260929-257
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-30
completed_at: 2026-09-30
owners:
  - root-agent
---

# RECHECK-20260929-258 — GOAL-027 EC-02 复检

**复检口径**：不采信工具自己的叙述，也不采信「源码里写着判据」；本文件给出**可复核观察面**
（命令 / 判词行 / `rc` / raw `sha256` / 实测计数）。**未实跑的不记通过**。

## 检查结果

### 1. 交付物属实：自建 MCP server 在树、过四道门、`IN_SCOPE` 显式追加

- 新增 `tools/research_mcp_server.py`（**209 行**）：stdio MCP server，两个工具
  `literature_search` / `literature_read`，服务一份**冻结的真实文献语料**（7 条记录，
  2026-09-30 经 Europe PMC REST `resultType=lite` 实取；真 PMID / DOI / 标题 / 期刊 /
  年份逐字保留，只收标题无 XML 标记的记录）。
- 新增 `tests/mcp_server/raw_shapeless_tools.py`（**91 行**）：申报一条 `name` 为空串的
  工具声明的 raw stdio 夹具（绕开 FastMCP，直讲 JSON-RPC；`initialize` 回显调用方
  请求的协议版本）。
- 四道门实测：`ruff format --check` 通过；`ruff check` `All checks passed!`；
  `mypy`（strict）`Success: no issues found`；规模 209 行、无超 50 行函数。
- `IN_SCOPE` **纯收紧**：`tests/tooling/test_tooling_scripts_meet_product_gates.py` 只追加
  `"tools/research_mcp_server.py"` 一个条目 ⇒ 受判下界由 7 条变 8 条；分区判据
  （`test_scope_partitions_every_tools_script_explicitly`）与必备清单判据复跑绿。

**语料 provenance 的独立复核**（不采信 server 自述）：判据
`test_the_declared_literals_match_the_frozen_corpus` 把逐字断言的常量与语料对照；
`test_search_result_matches_the_corpus_record_for_record` 把**工具面搬回来的记录**
与语料逐条逐字段比较。两份独立来源（判据常量 vs 语料）互证 **PMID `42796516` /
DOI `10.3390/molecules31183228` / 标题 "Molecular Docking of Natural Products:
Critical Appraisal of Current Methodology and Practical Guidelines."** 一致。

**语料是快照、不是实时检索**（如实边界）：server 无网络、无时钟、无随机；同一输入
两次调用 spill 字节逐字节相同（判据实测）。**不证明**任何第三方 MCP server 可 pin 可用
（本 GOAL 明写的「不证明」范围）。

### 2. 空参数真缺陷：修复属实、且修的是**对的层**（AC-2 的核心）

修复前（`adapters/mcp/provider.py:173` 附近）：`session.call_tool(tool_name, {})` —— 空参数、
不读 ArtifactStore、不校验 `argument_digest`。修复后：`_execute_async` 先 `_read_args(call)`，
再开会话；`_read_args` 按 `tool-args:{task_id}:{operation_key}` 读回制品、
**`Digest.of_bytes` 重算比对 `call.argument_digest`**；制品**缺席**时仅当声明值恰为
`{}` 的 canonical 序列化（`json.dumps({}, sort_keys=True)` 的字节）才回落空参数，
其余 fail closed（`InvalidInputError` ⇒ 既有映射 `CONFIGURATION`）。

**与 REST 适配器的对照**（说明这是"同形 + 一处有理由的差别"）：`ncbi.py::_read_args`
直接 `store.get`（缺失即抛）；MCP 的缺席分支是**新增**的（MCP 调用可合法地声明空参数），
且方向是 **fail closed**：声明了非空参数却没有制品 ⇒ 点名拒绝，**不**静默降级成空参数
（否则缺陷以另一种形态复活）。

判据实测（`tests/contracts/test_mcp_provider_arguments.py`，13 条）：

```text
uv run --frozen --no-sync python -B -m pytest \
  tests/contracts/test_mcp_provider_arguments.py tests/contracts/test_tool_provider_contract.py -q
⇒ 31 passed
```

- 正向：两个不同 query ⇒ 工具回显两个不同对象；真标识（`EXT_ID:` + 真 PMID + 真 DOI）
  原样穿过参数面；内容寻址（`Digest.of_bytes(store.get(...)) == output_digest`）；
- fail closed：声明非空但无制品 ⇒ 拒 + **不留**结果制品；篡改成**语义合法**的另一参数
  ⇒ digest 不符拒；非对象 JSON ⇒ 拒；`operation_key` 隔离（一个键的制品不服务另一个键）；
- 空声明仍可用（真调用、非空结果）⇒ 修复未把"声明空参数"一并打死。

### 3. 真回环（AC-3）：真连真调真取结果（实测矩阵）

```text
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_mcp_research_server_loopback.py -q
⇒ 11 passed in 10.72s
⇒ egress guard: judged 15 connection attempt(s); blocked 0（全部被拒的"连接"是测试内 MockTransport 计数，无外发）
```

| 面 | 实测 |
| --- | --- |
| 工具名 | `{literature_search, literature_read}`；`provider_kind=MCP`、`effect_class` 与 spec 一致 |
| 检索（真标识） | `molecular docking` ⇒ `hitCount=4`、ids `['42803750','42796516','42740546','42772441']`；首条 `pmid=42803750`、`doi=10.1002/cns.71179` |
| 互证 | 语料记录 `42796516` / `10.3390/molecules31183228` 与判据常量逐字相等 |
| 内容寻址 | spill 字节重算 == `output_digest`；`text[0]` 解析 == `structured`（信封一致） |
| 参数往返 | `molecular docking ≠ carbon footprint` 两个 id 集（空参数会让两者相同）；同 query 两次 ⇒ 字节级相同 |
| 读取往返 | `['42796516','99999999']` ⇒ `ids=['42796516']`、`missing=['99999999']`；两条路径同记录逐字段相等 |
| 子进程证据 | 未注册工具的错误 `Unknown tool: ghost_tool` 来自**子进程**（本地桩不可能产出该消息） |
| 健康 | `HEALTHY`；两次探测 schema 指纹相同 |

### 4. 注册面 + 三条点名反证 + 执行面（AC-4）

（本正文档内以中文态名表述注册状态（登记 / 已批准 / 已吊销）；三个 wire 值（登记态 / 已批准态 / 已吊销态）以判据断言为准 —— 见 `tests/contracts/test_mcp_registration_and_refutations.py` 的逐字断言。）

```text
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_mcp_registration_and_refutations.py -q
⇒ 13 passed
```

- **全生命周期**：`POST ⇒ 登记（待批准）`（`UNTRUSTED`；不进目录 / 不进 pin 表 / 不进编译产物）→
  `approve ⇒ ACTIVE`（`USER_APPROVED`；进目录 + pin 入表 + 协议编译 `provider_ids` 出现）
  → `revoke ⇒ REVOKED`（退出目录与 pin 表）；`pinned_revision="v1.2.3"` ⇒ 422（点名 `digest`）。
- **反证① 未 pin**：目录内 provider + 空 `tool_pack_digests` ⇒ preflight
  `SUPPLY_CHAIN_UNPINNED`（`{provider_id} has no pinned ToolPack digest`）；补 pin 后不报（成对）。
- **反证② 未批准**：登记态时编译产物 `provider_ids` 无该 id；`require_frozen_tool_set`
  ⇒ `POLICY_DENIED` 且消息含 provider id；批准后同一调用通过（成对）。
- **反证③ schema 不符**：raw 夹具（空名字工具声明）⇒ `list_tools` 抛
  `TOOL_SCHEMA_MISMATCH`、消息点名 `tool id must not be empty`（**不得**静默丢弃该声明）；
  `check_health` ⇒ `OPEN_CIRCUIT` 且 `observed_schema_digest is None`（不伪装健康）；
  畸形参数字节（digest 自洽）⇒ 触达 server 之前 `TOOL_SCHEMA_MISMATCH`（`mcp protocol error`）。
- **执行面**：`execute_run_chain_capabilities` 用真 MCP provider + 目录口径 spec 跑两步链
  （检索 → 读取，`ids_from_previous="structured.ids"`）：两条证据
  `tool_refs=(research_mcp_tools, literature_search)` / `(…, literature_read)`；
  读取步 id 含真 PMID；来源性质两向——不声明 `network_domains` ⇒ `GENERATED`，
  声明 ⇒ `RETRIEVED`（由 `_trust_label_for` 按**声明**判定，两向都在判据里）。

### 5. `phase_capabilities.py` 的点分路径：为什么改产品而不是改判据

MCP 的溢出内容是**一层信封** `{"text": [...], "structured": {...}}`；`ids_from_previous`
原先只查顶层键 ⇒ 信封形结果取不到 `ids`。MCP result 信封是 **adapter 的产品契约**
（`_serialize_call_tool_result`），不是夹具巧合 ⇒ 链式传参要能表达"从信封里取"。
修法 = `ids_from_previous` 支持点分路径（与 `arguments_from_input` **同一** `_lookup`），
**非点分名字走原样分支**：既有 15 条链判据逐字节未改、复跑全绿（行为零变化）。
**未选**在判据里预拆信封——那会让运行链对信封形态无感知，缺陷留给下一位装配者。

### 6. 按压矩阵（四条，先红后绿 + 逐字节复原）

留档：`adapters/mcp/provider.py` 基线 raw `sha256` = `fcb5c065b32f7bc260c3a34774c516e30
5cbb7ba38220521323f6f176aa3f51a`（修复后、按压前）；`phase_capabilities.py` 基线 =
`e0dc7699b6238e163785631d6aae935eba5e8d33f39cbfb0e50d69093ea5b2f2`。

| 按压 | 改动 | 实测（红） | 复原验证 |
| --- | --- | --- | --- |
| P-A | `_execute_async` 回退成 `{}`（缺陷原形） | **15 failed / 9 passed**（含 `_read_args` 自身 5 条 fail-closed + 回环 6 条） | sha256 == 基线 ⇒ 55 passed（四套件） |
| P-B | 只删 `list_tools` 的空名字把关 | **2 failed**（schema 判据两条；参数面 1 条仍绿 ⇒ 只钉声明面） | sha256 == 基线 |
| P-D | 只删 `_read_args` 的 digest 比对 | **1 failed**（篡改用例；其余 12 passed ⇒ 只钉篡改面） | sha256 == 基线 |
| P-E | 删 `ids_from_previous` 点分分支 | **2 failed**（执行面两条） | sha256 == 基线 ⇒ 101 passed（含既有链 15 条） |

**P-A 的观察**：判据大面转红说明修复不是「一处装饰」——没有它，MCP 参数面整体断链
（工具只会收到 `{}`；`_read_args` 的存在本身也被绕过）。

### 7. 判据设计的三处教训（如实登记，均为判据侧修正）

1. **类别断言的实测校准**：首轮 `test_tampered_artifact_content_is_rejected` 断言
   `VALIDATION_FAILURE`，实测 `CONFIGURATION`——因为 MCP `execute()` 把
   `InvalidInputError` 统一归 `CONFIGURATION`（**既有**映射，被 18 条既有判据依赖）。
   错的是我的假定 ⇒ **改判据侧**（并在 docstring 写明口径），产品代码未动。
   探针 `scratch/probe_mcp_schema_20260930.py` 实测三种形态：
   制品内容违规 ⇒ `CONFIGURATION`；声明违规 ⇒ `TOOL_SCHEMA_MISMATCH`；
   server 侧工具错误 ⇒ `FAILED` 记录。
2. **畸形参数反证的自洽前提**：首轮把畸形字节配上**不匹配**的 digest ⇒ 被 digest 分支
   先拒、`mcp protocol error` 断言不成立。修法 = 用 `_call_with_raw_args` 让 digest 与
   字节**自洽**（先过防篡改关，再验 JSON 解析关）——两关各自可证。
3. **mypy 收窄不只是过门**：`run_tool` 6 参超 `max-args` ⇒ 收进 `ToolInvocation`
   frozen dataclass（未用 `noqa`）；`dict[str,str]` 字面量的 `arg-type` ⇒ 显式标注
   `dict[str, object]`；`object` 索引 ⇒ 支持件新增 `text_field` / `int_field` / `id_list` /
   `article_list` 四个**带形状断言的取数器**（判据不再靠 `str()` 掩盖形状漂移）。

### 8. 回归面（既有判据逐字节未改）

| 套件 | 结果 |
| --- | --- |
| `tests/contracts/`（492 passed, 69 skipped） | 含既有 MCP 契约 18 条 + Europe PMC 三份 + NCBI 契约，全部原样复跑 |
| `tests/application/` + `tests/integration/test_capability_plane*.py` + `tests/tooling/` | **2002 passed, 1 skipped** |
| `test_run_chain_capabilities.py`（链，15 条） | 绿（点分路径**行为零变化**） |
| `test_tooling_scripts_meet_product_gates.py` | 绿（`IN_SCOPE` 只追加 1 条；分区 / 下界 / 人坏脚本按压全绿） |
| `tests/api/` + 离线 e2e + `tests/architecture/python/` | 见 §10（canonical DSN pin） |

### 9. 离线纪律（实测）

全部新判据不触网：MCP 路径是 **stdio 子进程**（真进程、无网络）；egress guard 在新判据
运行时的记录为 `judged N connection attempt(s); blocked 0`，其中 N 是**判据内部**的
MockTransport 计数（Europe PMC 系历史文件），MCP 三份新判据**零出站**。
默认门离线口径未被放宽（`tests/egress_guard.py` 一字未改）。

### 10. 定向消费者复跑（canonical DSN pin，一次合并运行）

```text
RESEARCHOS_POSTGRES_DSN=<test DSN> DATABASE_URL= POSTGRES_DSN= RESEARCHOS_DATABASE_URL= uv run --frozen --no-sync python -B -m pytest   tests/api/ tests/e2e/test_run_chain_retrieval_offline.py tests/architecture/python/ -q
⇒ 799 passed, 4 skipped, 2 warnings in 131.90s（EXIT=0）
```

覆盖含：`test_runs_api` / `test_catalog_merge` / `test_tool_registrations_api` /
`test_tool_registration_health_drift`（注册面既有判据）、离线链读面快照、
`tests/architecture/python/` 的边界 / 记录面 / 措辞三条判据。
`egress guard: BLOCKED …` 的若干行是**该守卫自己的用例**（它们故意构造被拒连接并断言
点名），不是失败（既有口径）。

### 11. as-is 本机 m0 到 23/23（记录写入之后，独占运行，首跑即终态）

```text
uv run --frozen --no-sync python -B \n  .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4908 passed, 21 skipped（python/tests 段 in 679.26s）
⇒ 日志 scratch/goal027-c2-m0.log（canonical DSN pin；**零 python 残留**）
```

**首跑即终态**（无红点）。用例数 4908（cycle 1 收口 4866）⇒ 只增不减。
环境口径：`RESEARCHOS_POSTGRES_DSN`=test DSN + `DATABASE_URL` / `POSTGRES_DSN` / `RESEARCHOS_DATABASE_URL` 置空 + `LLM_MAIN_KEY=""`（复现 CI 的「无凭据」条件）。

### 12. CI 台账到终态（推送 `5f44fa5`；原始 JSON 实查）

M0 [**36668265638**](https://github.com/Eswink/research-system-new/actions/runs/36668265638) 八 job 全 `success`；Push-on-main（CodeQL）[**36668265126**](https://github.com/Eswink/research-system-new/actions/runs/36668265126) 3/3 `success`。两者 `run_attempt=1`（一次成功、无 flake）。原始 JSON 实查：

```text
run=36668265638 name='M0 Quality Gates' status=completed conclusion=success attempt=1 head=5f44fa56
  jobs=8 ok=8 bad=[]
run=36668265126 name='Push on main' status=completed conclusion=success attempt=1 head=5f44fa56
  jobs=3 ok=3 bad=[]
```

轮询日志 `scratch/goal027-c2-ci-poll.log`；取值文件 `scratch/goal027-c2-run-{36668265638,36668265126}{,-jobs}.json`。空集合 / 空字段一律按「未取证」处理（本轮到终态，无 cancelled）。

**一次 flake 已按既有配方处置（如实登记）**：该 run 的 `run_attempt=1` 时 `console-frontend` 判红于 `tests/e2e/live-schedules-write.spec.ts:48` 实测 `2 次 · 2026-09-30 04:43 · OK`（期望 `1 次`）—— 该 spec 以 120s 间隔登记后立刻手动触发，在负载下守护线程的定时 tick 与手动触发**同时**落账 ⇒ 双计数。该提交是**纯记录提交**（3 个 markdown，零产品文件），同一 job 在上一个代码提交 `5f44fa5` 上绿 ⇒ 归类**定时竞态 flake**，未改 spec、未动阈值；`rerun-failed-jobs` ⇒ `run_attempt=2` **八 job 全 `success`**（`jobs=8 ok=8 bad=[]`）。取证：`scratch/goal027-c2b-cf.log`（原始 job 日志）/`scratch/goal027-c2b-run-jobs2.json`（重跑后逐 job 结论）。

### 13. 未覆盖范围（明写，不夸大）

- **不证明**任何**第三方** MCP server 可 pin 可用（自建 server 走通了治理链，第三方未测）。
- 冻结语料是**快照**（非实时检索）；MCP server **不触网**（stdio 离线路径）。
- 生产组合根**未注册** MCP provider 实例 ⇒ 控制面读面对该 provider 的健康诚实 UNKNOWN
  （执行面证据由测试装配注入真 provider 实例——与既有 `ncbi_eutils` 的 injection 模式同形）。
- `ids_from_previous` 点分路径只覆盖**一层**信封写法（深层嵌套未测）。
- 读面认证 / 多租户 / BOLA·BFLA / 部署面 / `R-M1` —— 承继 GOAL-027 的未覆盖范围，逐条仍在位。
- **不宣称**项目安全（`R-M1` 未收口）；**不宣称**投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 结论

`PASS_WITH_WARNINGS`。六条 AC 全部 PASS：server 在树并过四道门（AC-1）；空参数缺陷
修复 + 按压两向 + `sha256` 逐字节复原（AC-2）；真回环真标识真取结果（AC-3）；
注册面全生命周期 + 三条点名反证 + 批准后执行面（AC-4）；既有判据逐字节未改、
消费者套件全绿（AC-5）；四道静态门 + 四条按压（AC-6）。

**警告（残余，逐条在位）**：

- `W-1`：MCP 注册的目录消费面只到**编译产物**（`tool_requirements` / 冻结集）；
  执行面的 provider 实例仍由装配方注入（生产组合根未装配 MCP 实现）——与既有
  `ncbi_eutils` 同形，但「注册后自动可执行」尚不成立。
- `W-2`：冻结语料是**真实记录的冻结快照**，不是实时检索；对端 API 变更不影响本 server
  （也因此**不验证**对端 API 兼容性）。
- `W-3`：既有 `test_tool_provider_contract.py` 不覆盖参数面（本 EC 新增判据补上）；
  两文件的分工靠注释说明，无机制强制（改注释不会判红）。
- `W-4`：点分路径只支持单层信封写法；更深的嵌套（如需从 `structured.a.b` 取）未测。
- `W-5`：**不证明**第三方 MCP server 可 pin 可用；**不证明** live 网络下 MCP 可用。
- `W-6`：证据链的执行面用例用受控 `FakePolicyEvaluator`（默认 ALLOW）——
  策略 DENY 面的既有判据在 `test_run_chain_capabilities.py` 覆盖（MCP 未重测该面）。
