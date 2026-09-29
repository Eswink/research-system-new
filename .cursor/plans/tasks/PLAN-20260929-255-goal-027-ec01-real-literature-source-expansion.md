---
id: PLAN-20260929-255
slug: goal-027-ec01-real-literature-source-expansion
title: GOAL-027 cycle 1（EC-01）：真实文献能力扩容 — Europe PMC provider + pin + 登记 + 反证两向 + 离线实跑取证
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-256-goal-027-ec01-europe-pmc-literature-source.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-174-provider-capability-reuse-widens-the-pin-face.md
parent_goal: GOAL-20260929-027
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-027 的 **EC-01**（真实文献能力扩容：在既有 `ncbi_eutils` 之外**新增至少一个
    真实文献源**）。授权沿用该 GOAL 的 `authorization.ref`（**用户明确要求方向切换为真实科研能力**）：
    「**新增 provider**（REST / MCP 均可）」+「新增判据 / 夹具 / 探针（落 `tests/**` ⇒ m0 条数仍 `23`）」+
    「修实现过程中发现的真缺陷」+「文档同源更新」；push-to-main-for-CI 口径（**只推 `main`**、不 force、
    不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：新增件一律落**新文件**；**不修改**任何既有判据 / 门禁 / 阈值 / 放行面
    （点名：`tests/contracts/test_ncbi_provider_contract.py`、`tests/contracts/test_tool_provider_contract.py`、
    `tests/egress_guard.py`、`tests/application/test_m2_audit.py`、`tests/application/preflight/**`、
    规模门、三道记录面判据）；**不动** `examples/config/capabilities.yaml` 词表 /
    `packages/application/preflight/policy_check.py` 的 `_CAPABILITY_SCOPE` /
    `examples/config/policy.yaml`（三处并集由既有测试锁死；新增文献源**复用既有能力名**
    `literature.search` / `literature.read` ⇒ 三处零改动）；**不改** `PRODUCT_ROOTS` / m0 条数 /
    作业结构（终态行仍 `23`）；**零**新依赖（`httpx` / 标准库是现有栈）；**默认门离线**
    （判据用 `httpx.MockTransport`，**不触网**）；示例与夹具一律**明显不可用的合成值**；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称 exactly-once（**明确否认**；口径只能是
    at-least-once + idempotency + deduplication）。
    **一处对既有文件的例外（受控、最小、逐字节留档）**：`tests/api/run_fixtures.py` 的
    `_PROVIDERS` 是**整表替换**的 pin 源；新 provider 复用既有能力名 ⇒ 编译期反查会把
    `europe_pmc` 加进 5 份协议的 `provider_ids` ⇒ 该表缺条目即 `SUPPLY_CHAIN_UNPINNED`（preflight
    FAIL ⇒ 拒冻），实测让**既有**协议 `real_retrieval_research_v1` / `m12_reference_research_v1`
    由 PASS 变 FAIL。故本 PLAN 只在该元组**追加一个条目**（`"europe_pmc"`），
    不动该文件的任何断言 / 其它逻辑。
exit_criteria:
  - id: AC-1
    criterion: >-
      **Europe PMC 适配器在树且按 `ncbi.py` 的形态写**：新增
      `adapters/research_tools/europe_pmc.py`（同步 `ToolProvider` Port：`execute` / `list_tools` /
      `check_health` / `close`；`httpx` 客户端注入；transient/permanent 错误分类；
      参数经 ArtifactStore 以 `tool-args:{task_id}:{operation_key}` 传递并校验 `argument_digest`
      防篡改；大结果经 `spill_large_result`；内容寻址 digest）。**不修改** `ncbi.py` / `parsing.py`。
    status: PASS
  - id: AC-2
    criterion: >-
      **URL 策略在触网之前（本 EC 的独有交付）**：适配器在**发请求之前**校验目标 host ——
      ① 仅 http/https；② 复用 `packages/application/model_relay/endpoint_policy.py` 的
      `endpoint_url_refusal` 作**唯一**保留类判据（拒绝 localhost / 环回 / 私有 / 链路本地 /
      保留地址；**不新造第二个 host 谓词**）；③ host 必须落在**声明的** `network_domains` 内
      （声明来自 `ToolProviderSpec.network_domains` —— 登记声明本身，不是另一个副本）。
      任一条不满足 ⇒ 抛错且 **transport 零请求**（判据断言请求计数 == 0）。
    status: PASS
  - id: AC-3
    criterion: >-
      **pin 契约在树且形状合规**：新增 `examples/contracts/toolpack_europe_pmc.yaml`，按
      `toolpack_ncbi_eutils.yaml` 的形态含 `id` / `version` / `source` / `resolved_revision` /
      `digest` / `license` / `tools` / `skills` / `requested_capabilities` / `network_domains` /
      `credentials` / `compatibility`；**`credentials` 为空数组**（Europe PMC 检索**无需凭据**
      ⇒ 满足「只有没有它不可用才声明」）；`digest` 是 `sha256:<64hex>` 形状。
      **如实口径**：该 `digest` 是**声明值**（全仓无人重算它），**不是**「内容寻址」。
    status: PASS
  - id: AC-4
    criterion: >-
      **登记进 provider 面**：`examples/config/tool_providers.yaml` 新增 `europe_pmc` 条目
      （`kind: REST` / `trust_level: VERIFIED` / `transport: rest` / `protocol_version` /
      `capabilities: [literature.search, literature.read]` / `effect_class: READ_ONLY` /
      `network_domains: [www.ebi.ac.uk]` / `health_check: true`；**不声明** `credential_ref` 与
      `endpoint_env`）；加载器（`adapters/contracts/resource_loaders.py`）与
      `schemas/tool-provider.schema.json` 校验通过；**既有 3 个 provider 条目逐字节未改**。
    status: PASS
  - id: AC-5
    criterion: >-
      **反证两向 + 离线实跑取证（真标识 + 内容寻址 digest）**：新增判据文件用
      `httpx.MockTransport` 走**真解析**：① 正向 —— 合法 host ⇒ 请求真的发出（计数 > 0）且
      产出含**真结构化字段**（真 PMID + 真 DOI + 真标题）与**内容寻址 digest**
      （`Digest.of_bytes` 重算相等，**不得**只断言「返回了 dict」）；② 反向 ——
      把 URL host 换成**非声明域名** / 把 scheme 换成非 http(s) / 把 host 换成环回 / 私有 /
      保留 ⇒ **触网前**被拒且**请求计数 == 0**；③ 反向控制（声明内 host ⇒ 放行）证明白名单
      判定的是**声明**而非硬编码；④ 按压先红后绿 + raw `sha256` 逐字节复原。
    status: PASS
  - id: AC-6
    criterion: >-
      **既有契约不被波及（本 EC 的最大杀伤半径）**：`tests/api/run_fixtures.py` 的 `_PROVIDERS`
      是**整表替换**的 pin 源 ⇒ 新 provider 必须同轮进表，否则 5 份复用文献能力的协议
      （`ai_ml_research_v0_4_0` / `human_gate_demo_v1` / `m12_reference_research_v1` /
      `real_experiment_research_v1` / `real_retrieval_research_v1`）在 run_ready 路径上
      实测由 PASS 变 FAIL。该覆盖由**下界断言**钉死（新判据文件），且全部消费者定向套件复跑全绿。
    status: PASS
---

## 验收条件

| AC | 判据（简） | 判据文件 / 交付物 | 状态 |
| --- | --- | --- | --- |
| AC-1 | 适配器在树、Port 四方法齐全、参数防篡改、spill + 内容寻址 | `adapters/research_tools/europe_pmc*.py` | **PASS** |
| AC-2 | URL 策略在**触网之前**：仅 http(s) + `endpoint_url_refusal`（唯一保留类判据）+ 声明白名单；反证断言**零请求** | `tests/contracts/test_europe_pmc_url_policy.py` | **PASS** |
| AC-3 | pin 契约在树、字段形态同源、`credentials: []`、digest 形状合规 | `examples/contracts/toolpack_europe_pmc.yaml` | **PASS** |
| AC-4 | 登记经产品加载器 + schema；复用既有能力名；既有三条未改 | `examples/config/tool_providers.yaml` | **PASS** |
| AC-5 | 真标识（真 PMID / DOI / 标题）+ `Digest.of_bytes` 重算相等；反证两向 + 反向控制 | `tests/contracts/test_europe_pmc_provider_contract.py` | **PASS** |
| AC-6 | 夹具 pin 源同轮扩表；5 份复用协议不被波及；消费者套件全绿 | `tests/contracts/test_europe_pmc_pin_and_registration.py` | **PASS** |

## 目标

GOAL-027 的 **EC-01**：在既有 `ncbi_eutils` 之外新增**至少一个真实文献源**。
建档勘察结论选定 **Europe PMC**（`https://www.ebi.ac.uk/europepmc/webservices/rest/`）：
公开 REST JSON API、**检索无需凭据**、返回**真 PMID 与 DOI**、形态与 `ncbi` 同族。

## 实施清单

- [x] WP-1：新增 `adapters/research_tools/europe_pmc.py`（provider 本体）
- [x] WP-2：新增 `adapters/research_tools/europe_pmc_parsing.py`（纯函数解析）+ `europe_pmc_runtime.py`（URL 策略 / 请求 / 参数），保持模块规模阈值
- [x] WP-3：新增 `examples/contracts/toolpack_europe_pmc.yaml`（pin 契约）
- [x] WP-4：`examples/config/tool_providers.yaml` 新增 `europe_pmc` 条目（只追加，不动既有三条）
- [x] WP-5：新增判据（真解析 + 真标识 + digest + URL 策略反证两向 + pin/登记/夹具覆盖下界）
- [x] WP-6：`__init__` 导出 + `docs/integration/MCP_TOOL_PROVIDERS.md` 同源更新
- [x] WP-7：RECHECK + MEM + GOAL 回写 + ALL_PLAN 投影

## 设计要点（来自建档勘察的实测事实）

1. **形态对齐**：`ncbi.py` 是唯一真 provider 的范本（258 行）：同步 Port、持久 `httpx.Client`、
   `_throttle` 限速、429/5xx ⇒ transient / 4xx ⇒ permanent、`spill_large_result`、内容寻址
   `Digest.of_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode())`。
2. **参数传递**：经 ArtifactStore 的 `tool-args:{task_id}:{operation_key}`，provider 读回后
   **重算 digest** 与 `call.argument_digest` 比对（防篡改）——这条必须照抄，否则运行链接不上。
3. **URL 策略是新增面**：实测 `network_domains` **目前没有运行时出口执法**
   （`endpoint_url_refusal` 只被 LLM 端点与探针调用）⇒ 本 provider 必须在**触网前**自己判，
   这是 EC-01 ④ 的交付物（也是本 EC 相对既有 provider 的**净增量**）。
4. **policy 三处零改动**：复用既有能力名 ⇒ 不新增能力 ⇒ 不触发镜像表并集判据
   （`tests/application/test_m2_audit.py::test_policy_scope_mapping_matches_policy_yaml`）。
5. **规模门**：新文件 ≤ 450 行、单函数 ≤ 50 行；解析拆到独立模块（与 `ncbi.py` / `parsing.py`
   的拆法一致）。实测首版 `test_europe_pmc_provider_contract.py` **537 行超门** ⇒
   把共享样本与装配辅助拆到 `tests/contracts/europe_pmc_support.py`，判据分两份
   （Port 语义 / URL 策略）。
6. **`digest` 是声明不是重算**（实测）：`toolpack_ncbi_eutils.yaml` 声明的 `947cbb22…`
   **既不等于**文件字节 sha256（`d127e4dd…`）**也不等于**任何重算值；全仓只有
   `services/api/catalog.py::_load_tool_pack_digests` 读它（只读值）、preflight 的
   `_is_pinned_digest` 只做 `Digest.parse` 形状校验。⇒ 新 pack 照字段形态写、
   `digest` 记成**声明值**并在证据里写明来源配方，**不得**用「内容寻址」措辞。
7. **Europe PMC 的 `resultType` 陷阱**（实测）：默认 `resultType=lite` 返回 `journalTitle`，
   而 `resultType=core` **反而没有** `journalTitle`，在飞解析器读的正是 `journalTitle`
   ⇒ 请求里**不加** `resultType=core`（本实现用默认档，只显式传 `format` / `pageSize`）。

## 证据

### ① 真实记录样本（线上实测，2026-09-29）

`GET https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&query=EXT_ID:<pmid>`
（`resultType` 默认 `lite`）。两条记录逐字用于离线夹具：

| 字段 | 记录一 | 记录二 |
| --- | --- | --- |
| PMID | `38000001` | `31452104` |
| DOI | `10.1177/0310057x231212211` | `10.1007/978-1-4939-9752-7_10` |
| 标题 | Exploring anaesthetists' views on the carbon footprint of anaesthesia… | Molegro Virtual Docker for Docking. |
| 期刊 | Anaesth Intensive Care | Methods Mol Biol |
| 年份 | 2024 | 2019 |
| `hitCount` | 1 | 1 |

样本落 `scratch/europepmc-sample.json`（gitignored，一次性取证产物；判据里的是**同一条记录**
的逐字字段，不是另造的合成值）。

### ② 判据实跑（离线，`httpx.MockTransport` 走真解析）

```text
uv run --frozen --no-sync python -B -m pytest \
  tests/contracts/test_europe_pmc_provider_contract.py \
  tests/contracts/test_europe_pmc_url_policy.py \
  tests/contracts/test_europe_pmc_pin_and_registration.py -q
⇒ 52 passed in 0.46s
⇒ egress guard: judged 0 connection attempt(s); blocked 0
```

三条判据文件分工（规模门：单文件 ≤ 450 行、单函数 ≤ 50 行 —— 三份均远低于上限）：

| 文件 | 行数 | 覆盖 |
| --- | --- | --- |
| `tests/contracts/europe_pmc_support.py` | 266 | 共享：真实样本常量 + `Transport`（MockTransport 宿主，**请求计数**）+ Port 调用 + 装配辅助（不含用例） |
| `tests/contracts/test_europe_pmc_provider_contract.py` | 318 | AC-1 / AC-5 正向：真 PMID / 真 DOI / 真标题、`Digest.of_bytes` 重算相等、参数防篡改、失败分类四态 |
| `tests/contracts/test_europe_pmc_url_policy.py` | 198 | AC-2：13 条触网前反证（**每条断言请求计数 == 0**）+ 正控制 + 反向控制 |
| `tests/contracts/test_europe_pmc_pin_and_registration.py` | 217 | AC-3 / AC-4 / AC-6：pin 形状、登记经加载器 + schema、夹具 pin 源**下界断言** |

**反证两向的净增量证据**（AC-2，13 条 `parametrize`）：

| 被拒形态 | 断言 | 结果 |
| --- | --- | --- |
| 非声明域名 / 后缀伪装域名 | 请求计数 == 0 | 绿 |
| 非 http(s) scheme（`ftp://` / `file://`） | 请求计数 == 0 | 绿 |
| 环回（`127.0.0.1` / `localhost` / `[::1]`） | 请求计数 == 0 | 绿 |
| 私有（`10.0.0.5`） | 请求计数 == 0 | 绿 |
| 链路本地 / 云元数据（`169.254.169.254` / `[fe80::1]`） | 请求计数 == 0 | 绿 |
| 多播 / CGNAT / 文档保留段（`224.0.0.1` / `100.64.0.1` / `203.0.113.10`） | 请求计数 == 0 | 绿 |
| **正控制**（声明内 host） | 请求计数 == 1 且真解析出真标识 | 绿 |
| **反向控制**（把声明外 host 写进 `network_domains`） | 请求计数 == 1（证明判的是**声明**） | 绿 |
| 同一 transport 上先拒后准 | 累计计数 == 1（被拒路径不发请求、不推进节流） | 绿 |

### ③ pin 契约的 digest 来源（**声明值**，明写配方）

`examples/contracts/toolpack_europe_pmc.yaml` 的
`digest: sha256:ed1f2d09716a53f6fa162178a2635b60080a21242ce16cf4fdd2885d8e7c6523`
的**声明配方**：对本文件 `id` / `version` / `source` / `resolved_revision` / `license` /
`tools` / `skills` / `requested_capabilities` / `network_domains` / `credentials`
十个字段做规范化 JSON（`sort_keys=True, separators=(",",":"), ensure_ascii=False`），
取 UTF-8 字节的 sha256。取证脚本 `scratch/goal027_c1_pin_digest.py`（一次性，gitignored）。

**对照实测（证明「声明」的性质不是本文件独有）**：

| pack | 声明 digest | 文件字节 sha256 | 结论 |
| --- | --- | --- | --- |
| `toolpack_ncbi_eutils.yaml` | `947cbb22…` | `d127e4dd…` | 两者不等 ⇒ 声明值，无人重算，全仓仍绿 |
| `toolpack_europe_pmc.yaml` | `ed1f2d09…` | （同上口径，不作为判据） | 本文件显式写明配方与「非内容寻址」口径 |

### ④ 夹具 pin 源的杀伤半径（AC-6，先红后绿）

**红（登记 provider 后、未扩表）**：`tests/api/test_runs_api.py` 3 failed（`run.failed`，
预检在冻结之前判负）。诊断脚本 `scratch/goal027_c1_diag_pins.py`（gitignored）实测：

```text
providers in catalog: ['europe_pmc', 'm12_artifact', 'ncbi_eutils', 'openhands_workspace']
tool_pack_digests    : ['m12_artifact', 'ncbi_eutils', 'openhands_workspace']
  non-native europe_pmc: pinned=None          ← 缺 pin ⇒ SUPPLY_CHAIN_UNPINNED
  capability literature.search: providers=['europe_pmc', 'ncbi_eutils']   ← 复用能力名 ⇒ 反查命中
  capability literature.read  : providers=['europe_pmc', 'ncbi_eutils']
```

**绿（同轮扩表：`_PROVIDERS` 追加 `"europe_pmc"`）**：`tests/api/` ⇒ **580 passed**（0 failed）。

**该文件的改动范围**（逐字）：`tests/api/run_fixtures.py:47`

```diff
-_PROVIDERS = ("openhands_workspace", "m12_artifact", "ncbi_eutils")
+_PROVIDERS = ("openhands_workspace", "m12_artifact", "ncbi_eutils", "europe_pmc")
```

单行、只追加一个条目；该文件其余部分（`replace_catalog_with_pins` 的断言与逻辑、
`sort_analysis` 契约注入）**逐字节未动**。另有一条**下界断言**防止它下次静默落后：
`tests/contracts/test_europe_pmc_pin_and_registration.py::TestFixturePinSourceCoversTheCatalog`
断言「目录内非 NATIVE provider 集合 ⊆ 夹具 pin 源」（受判集合非空）。

### ⑤ 定向消费者复跑（全部绿，canonical DSN pin）

| 套件 | 结果 |
| --- | --- |
| `tests/contracts/`（新增三份 + 既有 NCBI / tool provider 契约） | 绿（既有逐字节未改） |
| `tests/api/`（含 `test_runs_api` / `test_catalog_merge` / `test_tool_packs_api` / lineage / worker plane） | **580 passed** |
| `tests/application/preflight/`（含 `test_policy_surface_difference_set` / `test_missing_executor_is_named`） | 绿（**放行面 / 镜像邻域未被牵动**） |
| `tests/application/run_orchestration/test_run_chain_capabilities.py` | 绿 |
| `tests/architecture/python/test_run_chain_capability_exposure.py` | 绿（其断言是字面量 ⇒ 加 provider 不判红，**未被修改**） |
| `tests/e2e/test_run_chain_retrieval_offline.py` / `test_real_experiment_research_offline.py` | 33 passed |
| `tests/postgres/test_m13_pg_run_e2e.py` / `tests/loaders/` | 36 passed |
| `tests/adapters/` | 553 passed, 3 skipped |
| `tests/architecture/python/test_dependency_boundaries.py` | 绿 |

**一条环境类干扰的归因**（不是本改动的回退）：`tests/api/test_worker_plane_composition.py`
的 3 个 `@pytest.mark.postgres` 用例首次失败于 `password authentication failed for user
"research_os"` —— 根因是操作者 `.env` 的 `RESEARCHOS_DATABASE_URL` 经 litellm `load_dotenv()`
灌进进程，**覆盖**测试 DSN（既有已知类：DSN pinning）。按 canonical 口径把
`RESEARCHOS_POSTGRES_DSN` 指向 test DSN、`DATABASE_URL` / `POSTGRES_DSN` / `RESEARCHOS_DATABASE_URL`
置空后，同一套件 **580 passed**；单跑该文件亦 6 passed。**未改任何门禁 / 断言 / 阈值。**

### ⑥ 静态门（新文件）

```text
ruff check apps services packages adapters tests        ⇒ All checks passed!
ruff check .cursor/hooks .cursor/skills --select F,I    ⇒ All checks passed!
ruff format --check apps packages adapters services tests ⇒ 1077 files already formatted
mypy（strict，1067 files）                              ⇒ Success: no issues found
```

**首版曾判红的 4 处（如实留档，均为本人新代码）**：

1. `europe_pmc.py:142` 用了 `ToolSpec` 未 import（`F821` undefined-name）⇒ 补 import；
2. `europe_pmc.py:90` `__init__` 6 参超 `max-args = 5` ⇒ **收进声明面**：删掉
   `declared_domains` 构造参数，白名单改从 `ToolProviderSpec.network_domains`（登记声明本身，
   也是唯一真值来源）取 ⇒ 构造参数降为 5；**未用 `noqa` 掩盖**；
3. `europe_pmc_parsing.py:90` `# type: ignore[arg-type]` 是 unused ⇒ 改为显式
   `_as_count()` 逐类型判定（并顺带挡掉 `bool` 被读成 `1`）；
4. `europe_pmc_runtime.py:108` `dict(params)` arg-type ⇒ 参数类型从 `Mapping[str, object]`
   收窄为 `Mapping[str, str | int]`（值与 `search_params` 的产出同型）。

### ⑦ 按压矩阵（四条，先红后绿 + 逐字节复原）

留档 `scratch/goal027-c1-press/press-matrix.log`（**2825 字节 / `CR` 计数 0** / 二进制写盘）。

| 按压 | 改动 | 实测（红） | 复原 raw `sha256` |
| --- | --- | --- | --- |
| P1 | `assert_url_allowed` 开头 `return`（策略整体失效） | **19 failed / 2 passed** | `56c3cd3a…accd35`（= 基线）⇒ 21 passed |
| P2 | **只**删声明白名单分支 | **7 failed / 14 passed**（保留类用例仍绿 ⇒ 两条机制各自独立钉住） | `56c3cd3a…accd35`（= 基线）⇒ 21 passed |
| P3 | 夹具 `_PROVIDERS` 去掉 `"europe_pmc"` | **4 failed**（下界判据 1 + `test_runs_api` 3） | `03e73f90…af05e`（= 基线）⇒ 31 passed |
| P4 | 删 `_read_args` 的 `argument_digest` 比对 | 首轮 **16 passed（按压假绿）** ⇒ 改判据后重压 **1 failed / 15 passed** | `ec380889…b4ff`（= 基线）⇒ 16 passed |

**P4 的假绿是一次真教训（如实登记）**：原判据篡改成的参数对 `literature_search` **本身就非法**
（缺 `query`），删掉 digest 校验后仍被「入参非法」那条分支的同一异常满足 ⇒ 断言被**另一条路径**
满足。**修法 = 改判据侧**：篡改值换成**语义合法**的另一种参数（另一个真 PMID 的检索串），
并**额外断言 `transport.count == 0`**；重压即红（`DID NOT RAISE`）。**未改产品代码、未放宽断言。**

### ⑧ 新增判据的静态门（四道）

```text
ruff check apps services packages adapters tests          ⇒ All checks passed!
ruff check .cursor/hooks .cursor/skills --select F,I      ⇒ All checks passed!
ruff format --check apps packages adapters services tests  ⇒ 1077 files already formatted
mypy（strict，1067 source files）                          ⇒ Success: no issues found
```

规模门：四份新文件 **318 / 266 / 217 / 198 行**，均 < 450；无超 50 行函数。
（首版 `test_europe_pmc_provider_contract.py` **537 行**超门 ⇒ 拆出共享支持件，见「设计要点」第 5 条。）

### ⑨ 全量 m0 首跑抓到的两处（均为本人新文件，已修；如实留档）

**首跑终态**：`FAILED: 2 check(s): python/tests=1, framework/validate_bundle=1`（不是终态行）。

1. **`framework/validate_bundle` 判红 —— 测试数据与全仓「旧版本引用」守卫撞车（我引入的）**：
   URL 策略反证里用了 TEST-NET-1 地址 `192.0.<b>2</b>.<b>10</b>`，而该守卫的正则是
   `(?<![0-9])v?(?:0\.2\.[0-9]+|0\.3\.0)(?![0-9])` ⇒ 地址里的子串 **`0.<b>2</b>.<b>10</b>`** 被读成
   「旧项目版本 `0.<b>2</b>.<b>10</b>`」。判词点名三处（判据文件 + 本 PLAN + `RECHECK-256`）。
   **修法**：把该地址换成 TEST-NET-3（`203.0.113.10`）—— 仍是「文档用保留段」，
   与被测语义完全等价，且不再命中版本正则。复跑 `validate_bundle` ⇒ **验证通过**；
   URL 判据 **21 passed** 未变。**未改任何门禁 / 阈值**。

2. **`python/tests` 的 1 条判红 —— 负载下的超时 flake（与本改动无关，已复跑对照）**：
   `tests/application/experiments/test_m12_reference_e2e.py::TestM12ReferenceNegativeResult::test_negative_result_stays_scientific`
   实测 `assert 'TIMED_OUT' == 'NEGATIVE_RESULT'`。该用例在**全量 m0 满负荷**下跑一个
   真子进程实验（`timeout_seconds=60`），全量运行时被判超时。
   **复跑对照（同一代码、单跑）**：`pytest tests/application/experiments/test_m12_reference_e2e.py -q`
   ⇒ **6 passed in 98.65s**。⇒ 归为**资源阈值型 flake**（既有已知类），
   **未改该用例、未动阈值**；终态由重跑全量 m0 给出。

### ⑩ as-is 本机 m0 到 23/23（记录写入之后；终态行实测）

第三次全量运行（前两次的红点是 §⑨ 的两处，均已处置）与前两次的**产品代码逐字节相同**；
唯一差异是 §⑨-1 的测试地址与记录措辞。

```text
uv run --frozen --no-sync python -B   .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
⇒ PASS: profile=m0; 23 deterministic checks      ← 终态行（条数仍是 23）
⇒ PASS [ 行数 = 24、FAIL [ 行数 = 0、EXIT=0
⇒ 4866 passed, 21 skipped（python/tests 段 in 684.74s）
⇒ 日志 scratch/goal027-c1c-m0.log（独占运行、canonical DSN pin、不接管道）
⇒ 跑完复验进程卫生：零 python 残留
```

用例数 **4866**（基线 GOAL-026 收口为 4807）⇒ **只增不减**，与「新增判据 ⇒ m0 条数仍 23」一致。

### ⑪ CI 台账到终态（推送 `83f5150`）

M0 **[36606591243](https://github.com/Eswink/research-system-new/actions/runs/36606591243)** 八 job 全 `success`；
CodeQL **[36606590109](https://github.com/Eswink/research-system-new/actions/runs/36606590109)** 3/3 `success`；
两者 `run_attempt=1`（一次成功、无 flake）。原始 JSON 实查 `jobs=8 ok=8 bad=[]` / `jobs=3 ok=3 bad=[]`，
`head_sha=83f51501…` 与推送 sha 一致。轮询日志 `scratch/goal027-c1-ci-poll.log`（44 轮）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | IN_PROGRESS | cycle 1 派生：EC-01 = 真实文献能力扩容（Europe PMC）。建档勘察已定：复用既有能力名 ⇒ policy 三处零改动；URL 策略须由本 provider 在触网前自判（实测既有面只覆盖 LLM 端点与探针）。 |
| 2026-09-29 | DONE | **cycle 1 收口**：AC-1…AC-6 全部 PASS。**按压四条**（P1 策略整体 / P2 白名单单点 / P3 夹具 pin 面 / P4 参数防篡改）全部先红后绿且逐字节复原（P4 首轮**假绿** ⇒ 改判据侧复压，未改产品）；**RECHECK-20260929-256 = `PASS_WITH_WARNINGS`**；**MEM-20260929-174** 落档；GOAL-027 回写（EC-01 → PASS + 迭代日志 + 状态历史 + child_plans + memory_entries）。如实登记的残余：`W-1` 出口执法只覆盖本 provider / `W-2` `digest` 是声明值 / `W-4` Europe PMC 只做检索与按 id 取记录 / `W-5` `execute` 语句级绑定 / `W-6` 按压面有限。 |
| 2026-09-29 | IN_PROGRESS | WP-1…WP-6 落地：适配器三文件 + pin 契约 + 登记 + 三份新判据 + `__init__` 导出 + 文档同源更新。**四条首版判红全部修复**（未用 `noqa` / `type: ignore` 掩盖）。**杀伤半径按预测命中并处置**：`_PROVIDERS` 单行追加 ⇒ `tests/api/` 580 passed。定向套件全绿（见「证据」⑤）。WP-7 记录面（RECHECK / MEM / GOAL 回写 / ALL_PLAN）进行中。 |

## 影响报告

- **Domain/API/schema**：新增 1 个 tool pack 契约（`toolpack_europe_pmc.yaml`）+ 1 个 provider 条目
  （`europe_pmc`）；**不改** Domain 类型、**不改** capabilities 词表、**不改** `_CAPABILITY_SCOPE`、
  **不改** policy.yaml。**不改** OpenAPI（无路由 / DTO 变化）。
- **安全/凭据**：新增源**无需凭据** ⇒ `credentials: []` 且 provider 不声明 `credential_ref`、
  不解析任何凭据（无 token passthrough 通道）；URL 策略**收紧**（触网前校验 host +
  声明域名白名单 + 保留类判据复用唯一入口）；默认门仍离线
  （`tests/egress_guard.py` 未放宽，判据 `judged 0 connection attempt(s)`）。
  **不宣称**项目安全（`R-M1` 未收口）。
- **兼容性/迁移**：纯**追加**（新 provider + 新判据 + 单行夹具 pin 源扩表）；
  既有 `ncbi_eutils` 条目、`ncbi.py` / `parsing.py`、全部既有判据**逐字节未改**。
  无数据迁移、无 schema 版本变化。
- **上游版本影响**：零新依赖（`httpx` + 标准库是现有栈）；Europe PMC 为公开 REST API，
  pin 记在 `resolved_revision`（`2026-09-29-europepmc-rest-6.9`）与 `digest`（**声明值**）。
- **可靠性口径**：本 provider 的错误分类沿用既有 transient/permanent 语义；
  **不宣称** exactly-once（**明确否认**；口径固定为 at-least-once + idempotency + deduplication）。
- **剩余差距 / 下一项任务**：本 EC 的**未覆盖范围**——Europe PMC 只做 `search` +
  按 id 取记录两能力，**不做**全文抓取 / 引文网络；`network_domains` 的运行时执法
  **只覆盖本 provider**（仓内没有全局出口网关，其它 provider 仍未受此判据约束）。
  cycle 2 = **EC-02**（MCP 真实接入 + `McpToolProvider` 空参数真缺陷修复）。
