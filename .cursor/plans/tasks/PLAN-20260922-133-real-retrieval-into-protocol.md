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
- **不给模型注册一个真实可调用的检索工具**（要动 `register_tools` 生产装配 + ToolDefinition + 依赖模型行为）。
  记为**后继增强入口**，不在 EC-01 的验收路径上。
- **不重构贴线文件**（`composition.py` 零余量 / `phase_runner.py` 7 行）。若最终必须重构，
  按 AC-5 先记入 GOAL 的「需人工拍板」第 4 项再决定。

**WP3 必须先做的两个探针（离线，先探后写）**：
- **P-1 会话健康探针**：声明 `literature.search` 会让 `ncbi_eutils` 进入 `frozen_tool_set`
  ⇒ 真实会话会拿到 `Tool(name="ncbi_eutils")`。今天 `real_research_task_v1` 的冻结集已含
  `m12_artifact`（`artifact.read` 的 provider，`kind: NATIVE`）且真实 run 能到 `SUCCEEDED`。
  **探针**：离线装配下确认多一个未注册名字**是否**让会话装配/初始化失败。
  **若失败** ⇒ 就在既有 `register_tools` 生产 hook 上注册一个**真实的**检索工具（复用它而不是新造），
  这反而是把 D-5 的缺口补上；**若不失败** ⇒ 不动 `register_tools`，把事实写进记录。
- **P-2 投影探针**：按 D-9 验证「只 `register_evidence` 不 `attach_relation`」确实**读不到**，
  再验证补上 relation 后**读得到** ⇒ 反证的口径以此为准。

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

## 实施清单

- [x] **WP1 定案**（只读，**不发任何真实调用**）：在「定案」节写死三件事——
      (1) **协议路径 (a) 还是 (b)**（见 D-12/D-13 的取舍）；
      (2) **接线架构**（能力如何到达 phase、provider/policy 如何进入 run 链、hook 形态与
      `phase_runner` 的**净增行数**预算）；
      (3) **反证的精确形态**（移除什么 ⇒ 哪条判据红 ⇒ 复原复绿）。
      产出：本文件「定案」节 + GOAL 迭代日志。
- [ ] **WP2 工具观测的持久化与读面**（离线可验）：新增工具观测的存储与**读面**
      （端点 / DTO），使 AC-3 成立。**新模块承载**；贴线文件净零/净负。
      反证：读面**不空转**（无观测时必须能判出「无」）。
- [ ] **WP3 接线**：能力从协议到达 phase；`NcbiEutilsProvider` 在生产装配里被实例化并注册；
      执行经既有 `execute_tool_call`（策略判定在内）；结果经既有 `register_tool_evidence`
      准入并**挂 claim relation**（D-9）⇒ 使 AC-1 与 AC-2 在**离线**（Fake provider）下先成立。
- [ ] **WP4 真实协议 + live 判据**：按 WP1 的 (a)/(b) 落地协议与合约（**纯加性**）；
      写 live 判据（挂 `requires_live_llm` 或同一放行面），跑**最小必要**次数的真实检索，
      取回 run 终态 + 工具观测 + 证据链外部标识；**按压**反证（移除能力 ⇒ 无观测）并复原。
- [ ] **WP5 收口**：定向套件 + m0 全量 23/23 + 治理 `validate.py` 绿 + 快照类门禁
      （OpenAPI / 设计基线）+ 独立 RECHECK（含 W 列表）+ GOAL 回写（EC-01 置 PASS、
      迭代日志、`child_plans`、`latest_recheck`、`memory_entries`）。

## 影响报告

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

- 2026-09-22：derive（cycle 1）。建档 GOAL-011 后派生本 PLAN（EC-01，主干）。
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
