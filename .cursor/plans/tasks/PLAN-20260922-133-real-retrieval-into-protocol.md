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

**（待 WP1 填写）**

## 实施清单

- [ ] **WP1 定案**（只读，**不发任何真实调用**）：在「定案」节写死三件事——
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
