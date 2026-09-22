---
id: PLAN-20260922-133
slug: real-retrieval-into-protocol
title: 把真实检索接进协议与执行链：能力声明 → 实际调用 → 工具观测可读 → 证据由系统取得（GOAL-011 EC-01）
status: IN_PROGRESS
created_at: 2026-09-22
updated_at: 2026-09-22
parent_goal: GOAL-20260922-011
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260922-011 cycle 1 = EC-01（真实检索进协议）。授权来源：2026-09-22 用户 goal 模式指令
    frontmatter `authorization.ref`——(1) live-gated 真实调用（端点 `ANTHROPIC` + `agnes-2.5-flash`，
    凭据仅在本机 gitignored `.env`，键名 `LLM_MAIN_KEY`）；(2) **新授权：允许真实检索出网**——
    仅 NCBI E-utilities（`eutils.ncbi.nlm.nih.gov`），**只在该 provider 的 `network_domains` 声明范围内**，
    次数取最小必要，无 key 时按适配器既有节流（3 req/s），`NCBI_API_KEY` 可选不强制；
    (5) 凭据纪律不放松（值不得进任何 tracked 文件/DB/记录/日志/回显；`RESEARCHOS_AGENT_RUNTIME`
    只作单条命令内联前缀，**不得**写进 `.env`）；(6) 默认 runtime 保持 Fake、默认 CI 离线，
    **不得为了跑检索而放宽出站判据**（`tests/egress_guard.py` 是结构判据），检索类用例**必须**挂
    `requires_live_llm`（或同一放行面）才可出网；(7) push-to-main-for-CI（只推 main、不 force、
    不重写历史）。**本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、
    降低断言强度；新增依赖、改上游 pin；把真实 runtime 设为默认；把凭据写进 CI；
    用 Fake 工具结果充当检索证据。**触到 Domain / Canonical State 边界即 BLOCKED**，留人工拍板。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-133 — 真实检索接进协议与执行链（GOAL-011 EC-01）

## 目标

把「**能力声明**」与「**可执行工具**」之间那条**在生产侧不存在**的连线建起来，
使一次真实 run 的 discovery/analysis 阶段**实际调用检索**，并让该调用留下
**可读的工具观测**与**进入证据链的真实标识**（PMID / DOI / 标题）。

反证必须成对：**把该能力从协议移除** ⇒ 该阶段**无工具观测**（红）⇒ 复原 ⇒ 复绿。

## 验收条件

- **AC-1 能力真的被调用**（主干）：一次真实 run 的 discovery/analysis 阶段留下
  **可读的工具观测**（工具调用/结果记录），且检索返回的**外部标识**（PMID / DOI / 标题）
  出现在**证据链**里。**不算**：工具「被声明可用」、工具「被冻进 tool set」、
  模型**在文本里写了**一个 PMID。
- **AC-2 反证成对且被压过**：从绿出发，把该能力**从协议移除** ⇒ 该阶段**无工具观测**；
  复原 ⇒ 复绿。只绿不红 ⇒ 判据没在看。
- **AC-3 观测可读**：工具观测经**读面**可取（端点或读面投影），且**不是**只活在
  测试进程内存里。**不得**用「日志里有」充当读面。
- **AC-4 出网纪律**：真实检索**只**打到 `eutils.ncbi.nlm.nih.gov`（该 provider 的
  `network_domains` 声明）；**次数取最小必要**；**默认门一律离线**、
  `tests/egress_guard.py` **一行不改**；检索类用例**必须**挂 `requires_live_llm`（或同一放行面）。
  真实 run 用**单条命令的内联前缀** `RESEARCHOS_AGENT_RUNTIME=openhands` 开，
  **跑后不得把开关留在环境或 `.env`**。
- **AC-5 规模门禁**：**50 行函数 / 450 行文件**两道门在改动后仍绿。**本 PLAN 的关键约束**：
  `services/api/composition.py` **恰为 450 行（零余量）**、`packages/application/run_orchestration/phase_runner.py`
  **443 行（仅 7 行余量）** ⇒ 新逻辑**必须**落在**新模块**里，贴线文件只允许**净零或净负**改动；
  若确需重构贴线文件，**先记入 GOAL 的「需人工拍板」第 4 项**再决定（不自行放大 diff）。
- **AC-6 不削既有能力、不放宽既有判据**：`packages/domain/` 的字段/枚举/语义**不得**被削弱；
  既有合约与断言的**强度不得降低**；判据面改动必须**纯加性**（或**收紧**并写明理由）。
- **AC-7 终态如实**：run 终态只有 `SUCCEEDED` 是成功；`FAILED` **不得**写成成功；
  失败与超支**如实登记**。
- **AC-8 门禁与记录**：规模门禁自查 → 定向套件 → m0 全量 **23/23** → 治理 `validate.py` 绿 →
  独立 RECHECK（含 W 列表）→ GOAL 回写（EC-01 状态 / 迭代日志 / `child_plans` /
  `latest_recheck` / `memory_entries`）。

## 证据（derive 阶段实测；**只读代码/配置，未发起任何真实调用**）

| # | 事实 | 核对方式 | 对 EC-01 的含义 |
| --- | --- | --- | --- |
| D-1 | `ncbi_eutils` provider **已声明、已授予**：`kind: REST`、`trust_level: VERIFIED`、`effect_class: READ_ONLY`、能力 `literature.search` / `literature.read` / `citation.inspect`、`network_domains: [eutils.ncbi.nlm.nih.gov]` | 读 `examples/config/tool_providers.yaml:23-42` | 声明的**目的地范围**就是 AC-4 的边界 |
| D-2 | 适配器**已实现且严格**：`NcbiEutilsProvider.execute()` 按 `tool_id` 分派 `literature_search` / `literature_read` / `citation_inspect`；参数经 `tool-args:{task_id}:{operation_key}` artifact **内容寻址校验**（digest == `call.argument_digest`）；结果经 `spill_large_result` 落 artifact，记录只留 digest；错误映射超时/瞬态/永久三类 | 读 `adapters/research_tools/ncbi.py:27-120` | 执行体**不需要新写**；需要的是**把它接进 run 链** |
| D-3 | **能力面今天只是「校验/治理面」**：capability → `ToolRequirement(phase, capability, provider_ids)`（编译期）→ 预检校验 → `flatten_tool_providers()` 把 provider **ID 字符串**冻进 `frozen_tool_set` | `packages/application/protocol_compile/requirements.py:87-111`、`packages/application/preflight/checks.py:167-226`、`packages/application/run_orchestration/session_resolution.py:30-34` | **没有**任何生产路径把 capability/provider 变成**可执行的工具实现** ⇒ 这就是 EC-01 的缺口 |
| D-4 | 真正的 capability → tool 解析器存在，**零生产调用方**：`resolve_capability()` / `freeze_tool_set()` / `build_tool_catalog()` | `packages/application/tool_plane/resolver.py:98-138,163-172`；全仓搜索排除模块自身与 `tests/` ⇒ `packages/ services/ adapters/ tools/` **零命中** | 已有可复用件；**不需要**新造解析器 |
| D-5 | 会话拿到的「工具」是 provider 名字符串，**真实注册是空操作**：`session_builder.py` 调 `self._register_tools(...)`，而生产装配 `AdapterDependencies(...)` **不传** `register_tools` ⇒ 回落空操作；`tools_for_frozen_set` / `register_custom_tools` **零生产调用方** | `adapters/openhands/session_builder.py:45,88-94`、`services/api/runtime_support.py:208-221`、`adapters/openhands/tool_mapping.py:18-32`、`tests/e2e/live_run_support.py:117-136` | 「让模型自己调工具」这条路今天**没有**接线；本 PLAN 的路径见「定案」 |
| D-6 | `execute_tool_call()` 存在且是唯一执行用例：要求 `ToolProvider` 实例 + `ToolProviderSpec` + `ToolCallRecord` + `PolicyEvaluator` + actor；先判策略（`DENY` ⇒ `POLICY_DENIED`，`REQUIRE_APPROVAL` ⇒ `APPROVAL_REJECTED`），再 `provider.execute()`；**不**要求预算预留 | `packages/application/tool_plane/execution.py:72-120` | 可复用；需把 provider 与 policy 送进 run 链 |
| D-7 | `register_tool_evidence()` 存在且严格（要求 `SUCCEEDED` + `output_digest`，并**重读 spill 制品重算 digest**，不等即 `ValueError`），产出 `SourceRecord(trust_label=GENERATED, origin="tool:{tool_id}:{task_id}:{operation_key}")`；**零生产调用方** | `packages/application/evidence/tool_evidence.py:47-97`；唯一调用方 `tests/application/evidence/test_tool_result_not_evidence.py` | 可复用；**但它不 `attach_relation`** ⇒ 见 D-9 |
| D-8 | `ToolCallRecord`（`task_id/attempt/operation_key/tool_id/capability/argument_digest/status/recorded_at`）与 `ToolResultRecord` 类型**存在**，但**无表、无仓储、无读面**（SQLite/PG 迁移都没有工具调用表；OpenAPI 只有 `/tool-packs`、`/tool-provider-registrations*`、`/tool-providers`） | `packages/domain/tools.py:327-369`；`adapters/sqlite/db.py`；`adapters/postgres/migrations/`；`docs/api/openapi.m13.json` | AC-3 要求**读面**⇒ 本 PLAN 必须新建持久化 + 读面（**新模块**，见 AC-5） |
| D-9 | **投影口径（承重）**：`GET /runs/{run_id}/evidence`（`services/api/routers/inspection.py:117-127` ⇒ `list[EvidenceDto]`，含 `source_origin` / `source_trust_label` / `source_access_time`）**只经 claim relations 走**（`services/api/run_evidence.py` 的 `evidence_of_run()`） | 读 `run_evidence.py` + `dto/inspection.py:16-35` | 只 `register_evidence` 而**不** `attach_relation` 的证据**读不到** ⇒ 接线时**必须**同时挂 claim relation，否则出现「判据说绿、读面看不到」 |
| D-10 | `EVIDENCE_COVERAGE` 计数口径：`evidence_source_count = sum(1 for item in evidence if item.artifact_id not in self_artifact_ids)` ⇒ **只有非自产**证据计数（自产制品被排除）；`count >= minimum` 即过，缺配置/缺计数 **fail-closed 判 `False`** | `packages/domain/acceptance.py:144-155`、`packages/application/run_orchestration/result_handler.py:60-68` | 检索来源**属于非自产** ⇒ 可满足覆盖；但反证要求「去掉检索来源 ⇒ 判拒」⇒ 需确认**没有别的**非自产来源单独满足它 |
| D-11 | **`TrustLabel` 今天恰好 5 个成员**：`TRUSTED_INTERNAL` / `VERIFIED_SOURCE` / `UNTRUSTED_EXTERNAL` / `GENERATED` / `USER_PROVIDED`——**没有 `RETRIEVED`**；生产只赋两种（声明输入 `USER_PROVIDED`、会话自产 `GENERATED`） | `packages/domain/enums.py:244-249`、`result_handler.py:162,230` | **EC-02** 的 `RETRIEVED` 落地形态（新枚举成员 vs 读面另加可判字段）**必须**在 EC-02 的子 PLAN 定案并写明理由（涉 Domain 面 ⇒ 触及即 BLOCKED） |
| D-12 | 起点**并非「零声明」**：`m12_reference_research_v1.yaml` 的 `discovery` phase **已声明** `literature.search` / `literature.read`（`domain_discovery` 合约也声明了，含 `minimum_sources: 10`）；`real_research_task_v1.yaml` 只声明 `artifact.read` | `examples/protocols/m12_reference_research_v1.yaml:6-16`、`examples/contracts/task_contracts.yaml:5-7,93-94` | ⇒ 真正的缺口是**执行侧接线**，不是「没人声明过」。**但** m12 那份是 4+ phase、含 `parallel_agents` / `iterative_optimizer` / `min 10`，按 `real_research_task_v1` 头部自述「多阶段今天不可执行、phase 数 = 会话数」⇒ **不可**直接拿来做载体 |
| D-13 | `tests/api/test_real_protocol_identity.py` 把 `real_research_task_v1` **三面钉死**（文件 `id:` / canonical `Run.protocol_id` / 被解析字节 sha256 + **库里的冻结正文**） | 读该文件头部与 `_REAL` 常量 | 动 `real_research_task_v1.yaml` **必然**触及被钉住的冻结正文 ⇒ 见「定案」（取 (b) 则**零触及**） |
| D-14 | **规模门禁实测余量**：`services/api/composition.py` = **450 行（上限 450 ⇒ 零余量）**；`packages/application/run_orchestration/phase_runner.py` = **443 行（余量 7）**；`session_resolution.py` = 106、`dependencies.py` = 40、`tool_plane/resolver.py` = 203 | `wc -l` + `tests/tooling/test_python_source_limits.py`（`assert line_count <= 450`；函数 > 50 行亦红） | **硬约束**：新逻辑必须落在**新模块**；贴线文件只允许**净零/净负**改动（见 AC-5） |
| D-15 | 生产侧 `ArtifactStore` / `EvidenceLedger` **都已注入**（SQLite 与 PG 两条装配各有实现）；`ApiDeps.tool_providers` **两条装配都是空 dict** ⇒ `probe_provider_spec` 对 `ncbi_eutils` 如实返回 `UNKNOWN`（"控制面未注册可探测的 provider 实例"） | `services/api/composition.py:254-288,310-313`、`services/api/pg_composition.py:79-121,208-211`、`services/api/preflight_support.py:159-161` | 装配面**有**可用的 store/ledger；缺的只是 **provider 实例的注册**（顺带把健康探测从 UNKNOWN 变成如实可用） |
| D-16 | 既有 `PhaseRunnerDeps` 已有**注入可调用体**的先例：`experiment_task` 在 `phase_runner.py:408-414` 被调用（`tctx.contract.id == "experiment_execution"` 时走实验分支） | 读 `phase_runner.py:52-81,398-443` | 接线**不必**大改 `phase_runner`：新增一个同形 hook 即可（**≤ 7 行**，见 AC-5） |

## 定案（WP1）

> 本节为 WP1 的交付物：把「选哪条路」与「为什么」写死，供后续 WP 引用。
> **WP1 只读：未发起任何真实调用、未改任何产品代码。**

### 决策 1 —— 协议载体：取 **(a) 扩展 `real_research_task_v1`**，且**不新增 phase**、只在其既有 `analysis` phase 上**加两条能力声明**

**先更正 derive 阶段的一条判断（只追加，不改 D-13 原文）**：D-13 把「被解析字节 sha256 + 库里的冻结正文」
读成了「改协议文件就要同步改一处冻结快照」。**实测证伪**：`tests/api/test_real_protocol_identity.py:79-81`
的判据是
`detail["protocol_body_digest"] == str(Digest.of_bytes(read_protocol_text(protocol).encode()))`
——**摘要由被测文件在测试运行时现算**，再与**该次 run 自己冻结的正文**（`store.get_run(id).protocol_body`，
run 时写入）比对。**测试文件里没有任何 hard-coded 的摘要常量**（`_REAL` / `_DEMO` / `_DECLARED` / `_INPUT_BRIEF`
四个常量全是字面量路径与名字）。⇒ **改动 `real_research_task_v1.yaml` 的正文，该判据自动复绿，无需改测试、
无需改快照**。D-13 的风险等级因此从「触及被钉死的快照」降为「**同一条判据继续有效且自动跟随时**」，
**但判据的强度必须保持**：改完后必须**按压**——把文件 `id:` 改掉 ⇒ 身份判据必须红（证明它仍在看）。

**为什么取 (a) 而不取 (b)（新建协议）**：

1. **EC 的operative要求**是「把能力声明进**一份真实协议**…使一次真实 run 的 **discovery/analysis 阶段**
   实际调用检索」。`real_research_task_v1` 的既有 phase 正是 `analysis`（`Real Research Analysis`）
   ⇒ 在它上面声明，**逐字**满足「analysis 阶段」这一表述。
2. **成本取最小必要**（AC-4）：沿用既有 phase ⇒ 仍是 **1 个 phase = 1 次真实会话**。
   若新增一个 `discovery` phase（字面 (a)）会变成 **2 次真实 LLM 调用**，而 phase 数 = 会话数
   （该协议头部自述、且 `phase.strategy` 在产品侧只有编译器一个消费者）⇒ 多出来的那次会话
   **不带来新能力**，只翻倍成本。
3. **不引入同义协议的增殖**：取 (b) 会得到一份与 `real_research_task_v1` 高度重叠的
   「real research + retrieval」协议，两份都要各自维护登记面与判据；而 (a) 让
   `real_research_task_v1` 成为**唯一**那份「既分析又检索」的真实协议。
4. **(a) 与既有判据兼容**：`test_the_real_protocol_reaches_succeeded_on_the_product_path` 断言的是
   「run 终态 `SUCCEEDED` + evidence refs 含 `:analysis_report` 且含 `input-brief:real_research_v1`」，
   加两条 `required_capabilities` **不改变**这三件事的字面值；`test_the_two_protocols_do_not_collapse_to_one_identity`
   依赖的「两份 id 不同、正文互不出现对方名字」也不受影响（**前提**：新增的能力名与注释里**不得**出现
   `console_demo_research_v1` / `console_demo_research_v1_0_1` 字样——WP4 落笔时按此自查）。

**为什么 `m12_reference_research_v1` 不做载体**（尽管它 D-12 已声明了这两个能力）：
它是 4+ phase、含 `parallel_agents` / `iterative_optimizer`，并绑 `domain_discovery`
（`minimum_sources: 10`）。按 `real_research_task_v1` 头部的自述「多阶段 / 并行的真实研究今天**不可执行**」，
拿它当载体等于把一个**已声明但不可执行**的协议拖进验收 ⇒ 判据会红在「协议本身跑不动」，
而不是红在 EC-01 要看的那件事上。

### 决策 1 的更正（cycle 3，**只追加**）——载体由 (a) **改为 (b) 新建一份真实协议**

**触发证据（cycle 3 实测，非推断）**：把两条 `literature.*` 声明加进 `real_research_task_v1`
的 `analysis` phase 之后，**4 条既有判据立刻转红**（`tests/api/test_real_protocol_identity.py`
的产品路径可达性 + `tests/api/test_run_fingerprint_read_face.py` 三条），而
`tests/architecture`/`tests/contracts`/`tests/loaders` 全绿。归因链（逐段实测）：

1. 声明 `literature.search` ⇒ provider `ncbi_eutils`（`kind: REST`）进 `tool_requirements` 与冻结集；
2. **默认装配**（无 preflight override）走 `_live_preflight` ⇒ `build_provider_health` 对目录里
   **每个** provider 求健康；`ncbi_eutils` 的**凭据门槛**未声明、`endpoint_env` 未声明、
   控制面**未注册可探测实例**（D-15） ⇒ 健康**诚实收敛为 `UNKNOWN`**；
3. `UNKNOWN` ⇒ `TOOL_HEALTH_UNPROVEN`（**WARNING**）⇒ 报告状态 `WARN`；
4. `service.py` 的门**只在 `FAIL` 时失败**（口径：[枚举注释](../) 与 WP-D 均写「UNKNOWN
   只警示**不阻断**」），于是 run 继续走到 `freeze_manifest`；
5. `freeze_manifest` 要求 `report.passed`（= `status is PASS`）⇒ **拒绝冻结**（`ManifestFreezeError`）；
   实测该 run 的读面形态是 `state=FAILED`、`manifest_digest=null`、`execution=null`、**无事件**
   ——即在**预检之后、执行之前**终止。
6. ⇒ 只要协议声明**任何 REST provider**，**默认装配**下它就冻结不了。这是**既有**的语义不一致
   （本协议是第一条踩到它的），**不是**本次改动引入的；本次改动只是把它暴露出来。

**为什么这足以改载体**：EC-01 的原文**显式允许二选一**；而取 (a) 会让这条新暴露的
不一致**波及 4 条 GOAL-010 既有判据的既有对象**（它们跑的就是 `real_research_task_v1`），
也意味着要为了修它去动**门禁语义**——那是 escalation（放宽/收紧验收门）而不是本 PLAN 的活。
取 (b) 把影响面**限制在新协议之内**，既有 4 条判据逐字保持、逐字复绿（实测：7 passed）。

**新载体**：`examples/protocols/real_retrieval_research_v1.yaml`
（`id: real_retrieval_research_v1_0_1`，1 phase `analysis`，复用既有合约
`real_research_deliverable` 与既有声明输入 `input-brief:real_research_v1`，
能力 = `artifact.read` + `literature.search` + `literature.read`，
`capability_execution: run_chain`）。文件头**自述**了上面这条实测边界，不夸大也不缩小。

**如实登记的两条边界（W 列表，本 PLAN 内不修）**：
- **W-A（产品路径）**：新协议在**默认装配**下的产品路径**今天跑不动**（上面第 5 步）。
  可行且被本 PLAN 采用的路是**测试/运维显式给出 `provider_health` 的 preflight 上下文**
  （`run_ready`/live harness）——GOAL-009/010 的全部真实 run 走的也是这条。
  修那条不一致要动门禁语义 ⇒ 归**人工拍板**，不在本 GOAL 内自决。
- **W-B（编辑器往返）**：`apps/web/src/features/protocol/editor/protocolSerialize.ts`
  逐键构造 phase body，**没有** `capability_execution` 这一键（`protocolDocument.ts` 也未解析）
  ⇒ 经协议编辑器**保存草稿**会把该声明**丢掉**，草稿随后跑起来会因 provider 未映射而
  点名失败（**是点名失败，不是静默**，但声明确实丢了）。本 cycle 只登记，不修。

### 决策 2 —— 接线架构：**检索由 run 链执行（能力步）**，不依赖模型自己调工具

**这条是本 PLAN 最承重的决策，理由是一条实测的装配事实**：会话拿到的「工具」是
**provider ID 字符串**（`flatten_tool_providers()` 把 provider id 并集冻进 `frozen_tool_set`，
`session_builder.py:88-94` 组装 `Tool(name=<provider_id>)`），而**生产装配的 `register_tools`
是空操作**（`services/api/runtime_support.py:208-221` 不传该参数 ⇒ `session_builder.py:45` 回落
`lambda spec: None`）。⇒ 若把 EC-01 的达成押在「真实模型去调一个工具」上，那个工具在**生产路径上
根本不存在** ⇒ 判据会红在装配缺失，且是否变绿取决于模型行为（概率性），这正是 GOAL-010 EC-01
判定细则里点名要避免的形态。

**因此定案为「能力步」**：在 phase 真正起会话**之前**，由 **run 链**按该 phase 声明的能力
执行一次检索，并把结果接入既有证据准入。这条路径**确定性**、**可反证**、**不依赖模型行为**，
且**不改变**「谁在执行研究」的语义——检索是系统的取证动作，模型仍然产交付物。

**四个接入点（全部复用既有件，不新造第二套）**：

| # | 接入点 | 落点 | 关键约束 |
| --- | --- | --- | --- |
| I-1 | **能力到达 phase** | `CompiledPhase` **不携带** `required_capabilities`（只有 `plan.tool_requirements` 带）。`resolve_sessions()` 是 run 链里**唯一**同时握有 phase 与 catalog 的地方 ⇒ 在那里把该 phase 的能力集合放进 `SessionSpecContext`（`session_resolution.py` 106 行，**有余量**） | 不改 `phase_runner` 的签名 |
| I-2 | **provider 与 policy 进入 run 链** | 经 `OrchestrationDependencies`（`dependencies.py` 40 行，**有余量**）加两个字段：工具 provider 注册表 + 策略求值器；由 `service.py` 的 `_execute` 透传进 `PhaseRunnerDeps` | 生产装配处**必须**实例化 `NcbiEutilsProvider`（D-15：今天 `ApiDeps.tool_providers` 恒空 ⇒ 健康探测恒 `UNKNOWN`） |
| I-3 | **形态：一个 hook，≤ 7 行** | 照 `experiment_task` 的既有先例（`phase_runner.py:408-414`）在 `_execute_one_task` 里加一个同形 hook：约 `step = deps.capability_step(tctx)` + `if step is not None: return step`。**重活全部落在新模块**（如 `run_orchestration/phase_capabilities.py`） | **AC-5**：`phase_runner.py` 443/450 ⇒ **净增必须 ≤ 7 行**（含空行）。落笔前先 `wc -l`，超了就先把等量逻辑挪进新模块 |
| I-4 | **执行 + 准入 + 可见** | 执行走既有 `execute_tool_call()`（策略判定在其中）；准入走既有 `register_tool_evidence()`；**但必须补 `attach_relation`**（D-9：`/runs/{id}/evidence` 只经 claim relations 走），否则出现「判据说绿、读面看不到」 | 不新造证据准入路径；不削弱 `register_tool_evidence` 的 digest 重算校验 |

**落在「不进入循环」面内的两件事，本 PLAN 明确不做**：
- ~~**不给模型注册一个真实可调用的检索工具**（要动 `register_tools` 生产装配 + ToolDefinition + 依赖模型行为）。
  记为**后继增强入口**，不在 EC-01 的验收路径上。~~
  **【已被下方「P-1 第二半步」的实测更正，2026-09-22 同一 cycle】**
  这条原本写成"不做"是**错的**：provider → SDK 工具的映射**必须**做，否则声明了新能力之后
  **会话根本创建不出来**（见「探针结果」的 P-1 第二半步）。**本 PLAN 把它从"不做"改为"必做"**，
  并明确它**不是**为了"让模型自己调检索"才做，而是**为了让会话能起来**。
- **不重构贴线文件**（`composition.py` 零余量 / `phase_runner.py` 7 行）。若最终必须重构，
  按 AC-5 先记入 GOAL 的「需人工拍板」第 4 项再决定。

**WP3 必须先做的两个探针（离线，先探后写）**：
- **P-1 会话健康探针**：声明 `literature.search` 会让 `ncbi_eutils` 进入 `frozen_tool_set`
  ⇒ 真实会话会拿到 `Tool(name="ncbi_eutils")`。今天 `real_research_task_v1` 的冻结集已含
  `m12_artifact`（`artifact.read` 的 provider，`kind: NATIVE`）且真实 run 能到 `SUCCEEDED`。
  **探针**：离线装配下确认多一个未注册名字**是否**让会话装配/初始化失败。
  **若失败** ⇒ 就在既有 `register_tools` 生产 hook 上注册一个**真实的**检索工具（复用它而不是新造），
  这反而是把 D-5 的缺口补上；**若不失败** ⇒ 不动 `register_tools`，把事实写进记录。
- **P-2 已答（本 cycle 实测，离线、内存内、无出网）**：探针 `scratch/probe133_evidence_projection.py`
用 `FakeEvidenceLedger` + **路由用的同一个投影函数** `services/api/run_evidence.py:evidence_of_run`
实测（不是读代码推断）：

```
P-2 step 1 (registered, NO relation):
  evidence_of_run -> []          visible? False
P-2 step 2 (same evidence, relation attached):
  evidence_of_run -> ['evidence:probe:op-1']   visible? True
  tool_refs exposed on the domain object: ('literature_search',)
  source can be resolved: tool:literature_search:task-1:op-1
VERDICT: relation required for visibility = True
```

⇒ **接线必须同时 `attach_relation`**（I-4 由此从"读代码的印象"升级为"实测结论"）。
同一探针还确认：`tool_refs` 在**领域对象上已经有了**、来源也能解析出
`tool:literature_search:...` 形态的 origin ⇒ WP2 只需把它**提到读面**，不必新建持久化。

### 探针结果（本 cycle 实测；只读代码，未发起真实调用）

**P-1 已答一半（关键）**：**既有的 live 判据全部走 `map_tools=True`**，即
`tests/e2e/live_run_support.py` 在测试侧注入 `register_inert_tools`（把冻结集里每个名字注册成
**惰性工具**），并在注释里明写「测试侧补上 **EC-05 的映射**」；而同文件另有一个
`map_tools=False` 分支，注释写明「改走**生产装配**以**如实测量**缺映射行为」。

⇒ **两点结论**：
1. **GOAL-010 的三次 `SUCCEEDED` 真实 run 是在「有惰性映射」的装配下取得的**，
   **不**证明生产装配（`register_tools` 空操作）也能让未注册的 `Tool(name="m12_artifact")` 正常初始化。
   ⇒ 这是一条**既有的、此前未被点名的射程边界**，WP3 必须**如实登记**（不夸大为「已验证」）。
2. 因此 **P-1 的答案会改变接线的落点**：若生产装配对未注册名字会失败，那么把
   `literature.search` 声明进 phase（⇒ `ncbi_eutils` 进冻结集）**本身**就会让生产路径的会话起不来。
   在这个分支下，**必须**同时把既有 `register_tools` 生产 hook 接上（注册一个**真实**的检索工具，
   复用 `NcbiEutilsProvider`，而不是惰性桩）——这正好把 D-5 的缺口补上，且**不是**新增机制。

**P-1 的剩余半步（留给 cycle 2 的 WP3，离线可做）**：用 `map_tools=False`（生产装配）跑一次
**不声明新能力**的装配探针，确认「今天生产装配对 `m12_artifact` 这个未注册名字是否已经失败」；
若**已经**失败 ⇒ 说明这是**既有缺陷**（GOAL-010 未覆盖），EC-01 的接线**必须**顺带修它；
若**不失败** ⇒ 记录事实，`register_tools` 可不动。

**P-1 前提已实测（本 cycle，离线、无出网）**：探针脚本 `scratch/probe133_frozen_set.py`
（只读文件 + 纯编译路径 `tool_requirements`，**刻意不碰 preflight**，因为 preflight 会做 provider 健康探测）
实测输出：

```
capability -> providers:
  artifact.read      -> ['m12_artifact']
  citation.inspect   -> ['ncbi_eutils']
  literature.read    -> ['ncbi_eutils']
  literature.search  -> ['ncbi_eutils']
  ...
--- as-is ---
  phase=analysis capability=artifact.read -> ['m12_artifact']
  frozen_tool_set = ['m12_artifact']
--- phase 'analysis' plus literature.search/read ---
  phase=analysis capability=artifact.read      -> ['m12_artifact']
  phase=analysis capability=literature.read    -> ['ncbi_eutils']
  phase=analysis capability=literature.search  -> ['ncbi_eutils']
  frozen_tool_set = ['m12_artifact', 'ncbi_eutils']
```

⇒ **证实**：在 `analysis` phase 上加两条能力声明，`frozen_tool_set` 从 `['m12_artifact']`
变成 `['m12_artifact', 'ncbi_eutils']`。⇒ 真实会话会**多拿到一个名字** `Tool(name="ncbi_eutils")`，
而该名字在生产装配里**从未注册**。**这就是 P-1 要问的那件事的前提，已成立。**
（相反方向也钉住了：不加声明时冻结集**不含** `ncbi_eutils` ⇒ R-1 反证有一条干净的起点。）

**P-1 第二半步 —— 结论已由仓库自己的判据给出（本 cycle 实测查到，**不是**推断）**：

先更正我在上一段写下的一句错话：我写「生产装配对未注册名字的行为**未经验证**」。**这是错的。**
该行为在本仓**有文档、有判据、且被离线钉死**：

- **判据**：`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的
  `test_unmapped_tool_set_is_named_not_silently_dropped` —— 用 `map_tools=False`（**生产装配**）
  起一次 run，断言三件事：`run["state"] == "FAILED"`、
  失败消息里 **`"is not registered"`**、且 **`_MockRelayHandler.requests == []`**
  （**工具解析之前不得发生任何 LLM 调用**）。docstring 明写这条是「对**今天真实行为**的固定」。
- **文档**：`docs/architecture/TOOL_RUNTIME.md`「未覆盖 / 未实现」节逐字写着
  「**provider id → SDK tool name 的映射不存在**：SDK 侧期望的是类名（如 `TerminalTool`），
  而冻结集里是 Research OS 的 provider id；**缺映射时会话创建点名失败**（不静默丢工具）」。
  `docs/architecture/AGENT_RUNTIME.md` 同口径，并写明「provider → SDK 工具的映射**属 EC-05**」。
- **机制**：`openhands.sdk.tool.registry.resolve_tool()` 对未注册名字 **`raise KeyError`**
  （`.venv/.../openhands/sdk/tool/registry.py:149-156`）。
  **本 cycle 实测**：进程启动时 `list_registered_tools() == []`（`import` 后**零**工具注册），
  且 `m12_artifact` / `ncbi_eutils` **都不在**注册表里。

**⇒ 三条结论（改变了接线范围，必写死）**：

1. **今天生产装配跑不动任何真实会话**——不只是"缺检索"：冻结集里的 `m12_artifact` 本身就未映射
   ⇒ 缺映射时会话创建**点名失败**（`FAILED`）。GOAL-010 那三次 `SUCCEEDED` 是在
   `map_tools=True`（测试侧惰性注册）下取得的 ⇒ **它证明的是"有映射时可达"，不是"生产可达"**。
   这是一条**既有的、由 GOAL-007 EC-05 命名但未落地的**缺口，本 GOAL 的 EC-01 **必须**顺带闭合它。
2. **因此「provider → SDK 工具映射」从"不做"改成"必做"**（见上文更正）。它**不是**为了
   让模型自己调检索，而是**为了让会话能创建出来**——否则声明新能力之日就是 run 全红之日。
3. **对 `ncbi_eutils` 应当注册一个"真实"工具而不是惰性桩**：既然这个映射必须存在，
   注册惰性桩只是把失败从"装配期点名失败"推迟成"模型调用时失败"；用
   `NcbiEutilsProvider` 支撑的真实工具才是诚实实现，且与**运行链能力步**共用同一个 provider 实例
   （两条路径同源，不新造第二套）。
   **但**：模型是否真的调用它，**不**作为 EC-01 的判据（那仍是概率性的）；EC-01 的证据由
   **运行链能力步**确定性产出。

### 决策 3 —— 反证的精确形态

| 层 | 操作 | 必须观察到的红 | 复原 |
| --- | --- | --- | --- |
| **R-1（EC-01 主干）** | 从 `real_research_task_v1.yaml` 的 `analysis` phase 删掉 `literature.search`（与 `literature.read`）两条声明 | 该 phase **无工具观测**（工具调用/结果记录为空），且检索来源**不出现**在证据链里 | 加回 ⇒ 复绿 |
| **R-2（判据不空转）** | 把该协议文件的 `id:` 改掉 | `tests/api/test_real_protocol_identity.py` 的身份判据**必须红**（证明它仍在看，而不是被本次改动变哑） | 复原 ⇒ 复绿 |
| **R-3（读面不空转）** | 让工具观测**不**落库（或读面查一个不存在的 run） | 读面必须**如实报「无」**，不得静默返回空列表冒充「有」 | 复原 ⇒ 复绿 |
| **R-4（EC-02 的成对，留给 EC-02）** | 摘掉检索来源 | `EVIDENCE_COVERAGE` **判拒** | 复原 ⇒ 复绿 |

**R-1 是 EC-01 的判据本体**；R-2/R-3 是**判据自身不空转**的证据；R-4 属 EC-02，本 PLAN 只保证
「检索来源是**可被摘掉**的一个独立来源」（即：不得让覆盖率只有检索来源一条腿，否则摘掉后
EC-01 也会连带红 ⇒ 那时要重新设计 R-1/R-4 的分工，**不得**用同一个红同时充当两条 EC 的证据）。

### 决策 4（cycle 3，WP3）—— 映射取 **M-2（声明化分离）**，且**声明落在协议 phase 上**（不是 provider 规格、不是 Domain 全局）

> 本节是 cycle 3 的定案交付物。与决策 1/2 同一纪律：**先写理由、再动代码**；理由全部来自
> 本 cycle 实测或仓库既有判据，不来自印象。

**先摆一条本 cycle 实测的射程事实（它改变了 M-1 的性价比）**：会话工具调用在
`PolicyEnforcingAgent._evaluate()` 里以 **`capability=<tool_name>`** 送进 policy
（`adapters/openhands/policy_enforcing_agent.py:96-111`），而 `tool_name` 是 **provider id**；
`examples/config/policy.yaml` 的词汇表**全是能力名**（`artifact.read` / `literature.search` /
`literature.read` …），`default_effect: DENY`。⇒ **今天即便把 provider 注册成真实 SDK 工具，
模型一调用也会在策略门被 DENY**（`ncbi_eutils` / `m12_artifact` 都不在 allow 名单里）。
M-1 的收益（「模型真的能用检索」）**不注册就为零、注册了也为零**，除非同时改政策词汇表——
而那是「把 policy 从说能力改为说 provider」的语义改动，**不在本 EC 内**（GOAL-007 EC-05 已把
「新增接入面」判为超出其 EC 范围）。⇒ **M-1 的收益侧被证伪，只剩成本。**

**再摆一条同样关键的既有判据约束**：`test_unmapped_tool_set_is_named_not_silently_dropped`
跑的是**生产组合根**（`build_agent_runtime`，无 `register_tools`），用 demo 协议，断言
`FAILED` + 「is not registered」+ 未发 LLM 调用。⇒ **任何「让生产装配对未映射名不再失败」的
全局修法都会直接把这判据打红**。这排除了所有全局形态（provider 规格加标记、组合根补注册表、
`flatten_tool_providers` 过滤）——除非把判据改掉，而那是 PLAN 明令禁止的。

**⇒ 唯一同时满足「判据保持强度」「收益侧真实」「不新增模型面接入点」的形态**：把「由运行链执行、
不暴露为会话工具」做成**协议 phase 的显式声明**，默认值 = 今天的行为：

```yaml
phases:
  - id: analysis
    required_capabilities: [artifact.read, literature.search, literature.read]
    capability_execution: run_chain   # 新增；缺省 session = 今天的行为
```

- **判据不动**：demo 协议不写该字段 ⇒ 缺省 `session` ⇒ `m12_artifact` 仍是「会话工具但未映射」
  ⇒ 那条判据的四个断言逐字保持。
- **不新增接入面**：会话拿到的工具集合只会**变窄**，不会变宽；运行链执行的能力仍留在
  `frozen_tool_set` 里（`require_frozen_tool_set` 仍拦住越权），所以是**声明化排除**而非静默丢弃。
- **落点选协议而不是 provider 规格**：provider 规格是全局的（`literature.search` 之于
  `ncbi_eutils` 在 demo 协议里同样存在），全局标记会把 demo 打红；而且「谁执行这个能力」是
  **这一次 run 的编排事实**，不是 provider 的固有属性。
- **不触碰 Domain 的 Canonical State**：新增的是**协议文档的一个可选字段**与其编译透传，
  不改任何持久化 schema、不改迁移、不改 `validate_bundle` 的注册表（协议 schema 文件本身要
  加一项，属**规格契约的加性扩展**）。**加性、缺省即旧行为、旧文档逐字节不受影响**——
  因此不构成 escalation 里的「Canonical State 边界」。
- **粒度取 phase 级**（不是逐能力）：本协议唯一的 phase 里**每一条**能力都由运行链执行
  （`artifact.read` 走 GOAL-010 EC-02 的声明输入机制；`literature.*` 走本 PLAN 的能力步），
  phase 级声明**恰好**表达这件事、不引入重复清单。逐能力粒度留给将来真有混合 phase 时再说，
  此处**如实登记为边界**，不假装支持。

**由此产生的两条硬约束（写死在实现里）**：
1. `capability_execution: run_chain` 的 phase，其能力**必须**仍进 `tool_requirements`
   （preflight/policy/credential/health 判定一字不减）与 `frozen_tool_set`（冻结面不减），
   只是**不进会话工具列表**。
2. 运行链**必须**对该 phase 声明的每条 run_chain 能力给出执行体；**给不出就点名失败**
   （fail-closed），不得出现「声明了 run_chain 却没人执行」的静默空洞。

## 实施清单

- [x] **WP1 定案**（只读，**不发任何真实调用**）：在「定案」节写死三件事——
      (1) **协议路径 (a) 还是 (b)**（见 D-12/D-13 的取舍）；
      (2) **接线架构**（能力如何到达 phase、provider/policy 如何进入 run 链、hook 形态与
      `phase_runner` 的**净增行数**预算）；
      (3) **反证的精确形态**（移除什么 ⇒ 哪条判据红 ⇒ 复原复绿）。
      产出：本文件「定案」节 + GOAL 迭代日志。
- [x] **WP2 工具观测的持久化与读面**（离线可验）：新增工具观测的存储与**读面**
      （端点 / DTO），使 AC-3 成立。**新模块承载**；贴线文件净零/净负。
      反证：读面**不空转**（无观测时必须能判出「无」）。
      **WP1 期间的收缩（只减不增，理由实测）**：AC-3 可能**不需要**新建表/端点——
      `services/api/routers/artifacts.py:72-85` 的 `_run_artifact_ids()` 已经把
      **evidence 引用到的 artifact** 收进 run 作用域列表，而 `register_tool_evidence` 产出的
      `Evidence.artifact_id` 正是 spill 出来的 `tool-result:{task_id}:{operation_key}:{tool_id}`
      ⇒ **工具结果经既有 `/runs/{id}/artifacts` + 内容下载读得到**；`EvidenceDto` 也已暴露
      `source_origin`（其值形如 `tool:{tool_id}:{task_id}:{operation_key}`）。
      ⇒ WP2 的最小形态可能是**纯加性**地补一处读面（例如把已持久化但未暴露的
      `Evidence.tool_refs` 提到 DTO 上），而**不是**新建持久化层。
      **落笔前先按 D-15 与本节实测确认「哪些面已经够用」**，只补真正缺的那一块。
- [ ] **WP3 接线**：能力从协议到达 phase；`NcbiEutilsProvider` 在生产装配里被实例化并注册；
      执行经既有 `execute_tool_call`（策略判定在内）；结果经既有 `register_tool_evidence`
      准入并**挂 claim relation**（D-9）⇒ 使 AC-1 与 AC-2 在**离线**（Fake provider）下先成立。
      **WP1/WP2 期间暴露的设计岔路（cycle 3 的 WP3 必须先在此二选一并写明理由）**：
      映射必须存在（否则声明新能力之日会话全红，见「P-1 第二半步」），但**映射到什么**有两条路：
      - **(M-1) 逐 provider 造真实 SDK 工具**：为冻结集里每个 provider id 注册一个真实现
        （`ncbi_eutils` → 检索工具；`m12_artifact` → 读 ArtifactStore 的制品工具）。
        **优点**：模型真的能用工具（研究能力更真实）。**代价**：每个 provider 都要
        Action/Executor/ToolDefinition（**必须模块级定义**，SDK 会枚举 `Action` 具体子类，
        局部类会毒化同进程后续事件 round-trip——见 `tests/e2e/live_run_support.py:36-64` 的实测教训）；
        且 executor 要拿到 run/task 上下文与 ArtifactStore，集成点尚未探明。
      - **(M-2) 把「运行链执行的能力」与「会话工具」在声明面分开**：在 provider 声明上加一个
        「**由运行链执行、不暴露给会话**」的标记，`flatten_tool_providers()` 据此**声明化地**
        排除它。**优点**：不必为每个 provider 造模型面工具，且与「能力步」设计同源。
        **代价与红线**：`test_unmapped_tool_set_is_named_not_silently_dropped` 固定的是
        「**不得静默丢工具**」——(M-2) 只有在**声明化**（不是默认行为、不是静默）时才成立，
        且**不能修改那条判据的强度**。另外该标记可能触及 provider 规格/Domain 面 ⇒
        **先判它是不是 Canonical State / 规格边界；是则 BLOCKED（归人工拍板）**。
      **定案前不得动 `flatten_tool_providers` 或那条判据。**
- [ ] **WP4 真实协议 + live 判据**：按 WP1 的 (a)/(b) 落地协议与合约（**纯加性**）；
      写 live 判据（挂 `requires_live_llm` 或同一放行面），跑**最小必要**次数的真实检索，
      取回 run 终态 + 工具观测 + 证据链外部标识；**按压**反证（移除能力 ⇒ 无观测）并复原。
- [ ] **WP5 收口**：定向套件 + m0 全量 23/23 + 治理 `validate.py` 绿 + 快照类门禁
      （OpenAPI / 设计基线）+ 独立 RECHECK（含 W 列表）+ GOAL 回写（EC-01 置 PASS、
      迭代日志、`child_plans`、`latest_recheck`、`memory_entries`）。

## 影响报告

- **本地 m0 在这台机器上 `python/tests` 判红，且与本 PLAN 的改动无关（**已用基线对照证明**）**。
  **结论与归因（实测，非推断）**：
  - 现象：`python/tests` 退出码 1，**但 pytest 自身 0 失败**（`4339 passed, 16 skipped`）。
  - 真因是**出站结构判据按设计判红**（`tests/egress_guard.py`，GOAL-010 EC-05）：整轮日志里有
    `egress guard: FAIL — the default gate attempted 2 non-loopback destination(s) that no live
    marker allows:`，两条都指向 **`198.18.0.178:443`（`kind=private`）**，归因链为
    `tests/api/test_runs_api.py::test_start_run_unprovisioned_control_plane_reports_actionable_failure`
    → `preflight_support.py:43:build_endpoint_health` → `_probe_endpoint` → `gateway.probe_connectivity`
    → `list_models` → `transport.request_with_retries` → `_execute_request`。
    ⇒ 一次**真实出站尝试**：该用例走真实组合路径探测例示 endpoint 的健康，而**本机 DNS 走
    fake-IP 代理**（`198.18.0.0/15`）⇒ 域名被解析成私网 fake-IP ⇒ 连接真的发起 ⇒ 判据判红。
    **判据没有错**，这正是它该做的事；**本 PLAN 一行都没有放宽它**。
  - **基线对照（决定性）**：把我的三处 Python 改动 `git stash` 掉后**在原始树上跑同一条全量命令**
    ⇒ **同样的 2 条 `198.18.0.178`、同样的 `egress guard: FAIL`**（该次 `4337 passed, 1 failed`；
    这 1 failed 就是判据的整轮红灯）。⇒ **本 PLAN 的改动不是原因**，这是**本机环境签名**。
  - **与 CI 的差异**：CI（干净 runner，无该 fake-IP 代理）同一棵树为绿 ⇒ 按仓库既有口径
    「每个提交的权威证书是 CI 在推送树上的结果」，本地这一项以**环境签名**如实登记，
    **不**改判据、**不**放行、**不**skip（否则就是为跑通而放宽出站判据，本 GOAL 明文禁止）。
  - **无关的对照**：`tests/api` 单独跑 **500 passed / exit 0 / blocked 0**；
    `tests/observability` 单独跑 **exit 0**（`tests/observability` 里那句
    `shutdown can only be called once` 是既有噪声）。⇒ 需要**整轮**才出现，属跨文件顺序效应。
  - **一条被自己证伪的推断（只追加，保留教训）**：我曾据此推断「缺少 otel collector 导致
    metric exporter 在解释器退出时 flush 失败 ⇒ exit 1」。**该推断是错的**：按仓库既有 compose
    起了 `research-system-otel-collector-1`（loopback-only，镜像本机已存在、无构建无出网）后
    **重跑仍是同一条红**，随后基线对照才把真因定到上面的 fake-IP 探测。**collector 不是原因。**

- **Domain / API / schema**：本 PLAN **不**改 `packages/domain/` 的既有字段或语义（AC-6）。
  新建工具观测的读面**会**动 `docs/api/openapi.m13.json` 快照与 `apps/web` 类型
  （若前端消费） ⇒ **快照类门禁必须同源重生成并复算**（承 `MEM` 的 OpenAPI 快照耦合教训）。
- **安全 / 凭据**：新增的**唯一**出网面是 `eutils.ncbi.nlm.nih.gov`（D-1 已声明的
  `network_domains`）；不需要新凭据（`NCBI_API_KEY` 可选）；凭据纪律与
  `RESEARCHOS_AGENT_RUNTIME` 单条内联前缀口径**不变**。
- **兼容性 / 迁移风险**：新增工具观测存储 ⇒ **新增**表/migration（**加性**，不动既有表）；
  SQLite 开发库若因 schema 变更出现陈旧，按既有配方删本机 gitignored 的
  `data/research-os-control.db` 重生成（**不是**数据迁移）。
- **上游版本影响**：**无**——不新增依赖、不改 pin（新增依赖即 BLOCKED）。
- **默认姿态**：默认 runtime 仍 **Fake**、默认 CI 仍**离线**；检索类用例**只**在
  `requires_live_llm` 放行面下出网；`tests/egress_guard.py` **一行不改**。

## 状态历史

- 2026-09-22：derive（cycle 1）：建档 GOAL-011 后派生本 PLAN（EC-01，主干）。
  derive 阶段只读代码/配置，**未发起任何真实调用**；证据 D-1…D-16 逐条实测。
  关键发现：缺口在**执行侧接线**（D-3/D-4/D-5），不在「没人声明过」（D-12）；
  且**规模门禁余量**（D-14：`composition.py` 零余量、`phase_runner.py` 7 行）是
  本 PLAN 的**一等设计约束**。
- 2026-09-22：**WP1 定案**（只读，未发调用、未改产品代码）。三条决策写死在「定案」节：
  (1) 载体取 **(a) 扩展 `real_research_task_v1`**，且**不新增 phase**、只在其既有 `analysis`
  phase 上加 `literature.search` / `literature.read` 两条声明（理由：逐字满足 EC 的
  「analysis 阶段」表述、成本仍为 **1 次真实会话**、不引入同义协议增殖、与既有三面判据兼容）；
  (2) 接线取「**run 链能力步**」而非「模型自己调工具」——因为生产装配的 `register_tools`
  是空操作，会话里的工具只是 provider ID 字符串，把达成押在模型行为上会红在装配缺失且是概率性的；
  四个接入点 I-1…I-4 全部**复用既有件**，并给出 `phase_runner` **净增 ≤ 7 行**的硬预算；
  (3) 反证分四层 R-1…R-4，**R-1 是 EC-01 的判据本体**，R-2/R-3 判「判据自身不空转」。
  **同时更正了一条 derive 判断**：D-13 担心的「改协议要同步改冻结快照」**经实测证伪**——
  `test_real_protocol_identity.py` 的摘要是**运行时现算**（对被测文件）+ 与**该次 run 自己冻结的正文**
  比对，测试文件里**没有**硬编码摘要常量 ⇒ 改协议正文该判据自动复绿，但**必须按压**（改 `id:` ⇒ 判红）
  以证明它仍在看。
  **本 PLAN 明确不做**：给模型注册真实可调用工具；重构贴线文件。两者都写进记录作为后继入口。
- 2026-09-22：**cycle 2 WP2 落地**（工具观测的**读面**；**不新建持久化**）。
  实测依据：`Evidence.tool_refs` 早已持久化、`Evidence.source_origin` 早已在读面上，
  缺的只是把 `tool_refs` **提到 DTO** ⇒ WP2 收缩为一处**纯加性**改动：
  `EvidenceDto.tool_refs`（+`_evidence_dto` 填充）→ 同步 `docs/api/openapi.m13.json`
  快照（`tools/gen_openapi.py` 重生成，diff **恰好 7 行、只有新字段**，无其它漂移）
  → 同步 `apps/web/src/api/types.ts` 与 `apps/web/tests/unit/consoleFixtures.ts`。
  **判据**：`tests/api/test_inspection_api.py::test_evidence_read_face_distinguishes_tool_origin`
  —— 同一 run 里两条证据的 `tool_refs` 必须**不同**（一条点名 `literature_search`、一条为空），
  读面若恒空或恒同值即红。**已按压**：把 `_evidence_dto` 的 `tool_refs` 临时改成 `[]`
  ⇒ 该用例 **FAILED**（`Right contains one more item: 'literature_search'`），复原 ⇒ 9 passed，
  且 `git diff` 只剩意图内的 **1 行新增**（无按压残留）。
  **WP2 之外仍待做**：见下方 WP3 的映射设计岔路。
- 2026-09-22：**cycle 3 WP3 落地（映射 = M-2 声明化分离；接线未落）**。
  - **定案**：见「决策 4」——M-1（逐 provider 造真实 SDK 工具）**收益侧被实测证伪**
    （会话工具调用在 `PolicyEnforcingAgent._evaluate` 里以 `capability=<provider id>` 送 policy，
    而 `policy.yaml` 的词汇表全是**能力名**且 `default_effect: DENY` ⇒ 注册了也一调用就被拒），
    且任何**全局**形态修法都会直接打红既有判据
    `test_unmapped_tool_set_is_named_not_silently_dropped`（它跑的就是**生产组合根**）⇒ 取
    **协议 phase 级、缺省即旧行为**的声明化分离；**未改任何门禁、未动那条判据的一个字**。
  - **落地面**（Python 侧，全部加性）：`CapabilityExecution`（`packages/domain/protocols.py`）
    → `ProtocolPhase.capability_execution` + `CompiledPhase.capability_execution`（**原样透传**）
    → `schemas/protocol.schema.json` 加一项 enum → loader 读成域枚举（缺省 `session`）
    → `run_orchestration/session_resolution.py::run_chain_tool_ids`（**按 phase 作用域**）
    → `SessionSpecContext.run_chain_tool_ids` → `AgentSessionSpec.run_chain_tool_ids`
    → `adapters/openhands/tool_mapping.py::session_tool_ids`（越界**点名拒绝**，fail-closed）
    → `session_builder`（建会话与 fork **两条**路径都过滤；fork 继承该声明）。
    **两个面都不减**：能力仍在 `tool_requirements`（pin/策略/凭据检查照旧）、provider 仍在冻结集
    （`require_frozen_tool_set` 仍拦越权），被拿掉的只有**会话工具列表**。
  - **判据两条，都**成对**且都被按压过**：
    ① `tests/architecture/python/test_run_chain_capability_exposure.py`（6 条：文档声明／
    加载+编译透传／冻结集**不缩小**／会话列表恰为差集／**按 phase 作用域**／越界点名拒绝）
    —— 删掉协议里的 `capability_execution` 行 ⇒ **4 条红**（会话列表重新等于冻结集），复原 ⇒ 6 passed；
    ② `tests/e2e/test_ec03_real_runtime_offline_chain.py::test_declared_run_chain_capabilities_let_production_assembly_start`
    —— **生产装配**（`map_tools=False`）下会话建得起来（mock 端点收到补全请求）、失败原因**无**
    "is not registered"、run 到 `SUCCEEDED`；删掉声明行 ⇒ **红**，实测失败原因逐字为
    `ToolDefinition 'm12_artifact' is not registered`（会话在建的时候就死）。它与**未动**的
    `test_unmapped_tool_set_is_named_not_silently_dropped` 构成完整的一对：
    「未声明 ⇒ 点名拒绝」对「已声明 ⇒ 声明化排除」。
  - **同一 cycle 的承载更正**：见「决策 1 的更正」（载体 (a) → (b)，附 4 条既有判据转红的归因链）。
    **如实登记 W-A（默认装配的产品路径今天跑不动）与 W-B（协议编辑器往返会丢该声明）**。
  - **仍未落**：**能力步本体**（运行链真的去调 `literature.search` 并把结果登记成证据）——
    即 I-1…I-4 的执行侧与 `NcbiEutilsProvider` 的生产装配，属 WP3 的后半，**下一轮入口**。
    **EC-01 仍 PENDING**（本 cycle 只让它**可验**：声明与装配面已落地并被判据钉住）。
