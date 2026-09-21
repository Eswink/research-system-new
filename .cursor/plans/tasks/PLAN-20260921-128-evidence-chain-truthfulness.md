---
id: PLAN-20260921-128
slug: evidence-chain-truthfulness
title: 证据链真实性：让 `EVIDENCE_COVERAGE` 由真实可查来源满足，而不是由模型自述（GOAL-010 EC-02）
status: DONE
created_at: 2026-09-21
updated_at: 2026-09-21
parent_goal: GOAL-20260921-010
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    GOAL-20260921-010 cycle 2 = EC-02（证据链真实性）。授权来源：2026-09-21 用户 goal 模式指令
    frontmatter `authorization.ref`——(1) live-gated 真实调用授权（**次数取最小必要**）；
    (5) push-to-main-for-CI（只推 main、不 force、不重写历史）。**本 PLAN 明文不做**：
    改验收门的判定语义使其变松、改 validator/门禁/快照、skip 或降低任何断言强度、
    新增依赖、改上游 pin、把真实 runtime 设为默认、把凭据写进 CI。
    **触到 Domain / Canonical State 边界（例如给验收标准加新字段）即 BLOCKED**，按
    GOAL frontmatter 的 escalation_triggers 处置。**不引入新依赖、不新造 URL 判据**
    （复用既有 `endpoint_policy`）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260921-128-evidence-chain-truthfulness.md
memory_entries:
  - .cursor/memory/entries/MEM-20260921-101-evidence-source-property-and-paired-landing.md
---

# PLAN-20260921-128 — 证据链真实性（GOAL-010 EC-02）

## 目标

把 `EVIDENCE_COVERAGE` 从「**模型说了一句话就算有来源**」变成「**必须由真实可查的来源满足**」。
现状（cycle 2 derive 实测）：`ResultRegistration.evidence_source_count = len(self.evidence)`，
而 evidence **全部**派生自同一次会话输出（`result_handler.register_session_result` 由
`structured_output` 造 artifact → `_evidence_from_artifact`），`SourceRecord` 的
`trust_label` 是 `GENERATED`，`origin` 是 `evidence.source_ref`（= 该 artifact 自己）。
⇒ **交付物自己就是它自己的「来源」**，`EVIDENCE_COVERAGE ≥ 1` **恒成立**。

**判据（EC-02 原文）**：`EVIDENCE_COVERAGE ≥ 1` 由**真实可查的来源**（检索 / 制品 / 外部源）
满足，**不得由模型自述充当**；来源记录**可读**；**反证：去掉来源 ⇒ 判拒**。

## 验收条件

- **AC-1 判别性质被明确记录**：「什么样的来源算真实可查」必须是一个**写下来的、可判的**
  性质（不是「看起来像」），且**把被排除的那一类点名**（模型自述）。记录里必须写明该性质
  为什么**不可能**被模型自述满足。
- **AC-2 真跑证据**：**一次真实 run** 的 `EVIDENCE_COVERAGE` 由**真实可查的来源**满足，
  且该来源记录**经既有读面可取**（`GET /runs/{id}/evidence`），其 `origin` **不是**交付物自身。
- **AC-3 反证成对**：**去掉**那个真实来源 ⇒ `EVIDENCE_COVERAGE` **判拒**（同一路径、同一判据）；
  复原 ⇒ 复绿。只有绿没有红 ⇒ 判据没在看。
- **AC-4 不靠放宽**：验收门 `packages/domain/acceptance.py` 的比较语义**不被改松**；
  若最终改了 `evidence_source_count` 的口径，那是**收紧**（模型自述**不再**能单独满足覆盖），
  且必须**压过**（把收紧撤掉 ⇒ 判据红）。
- **AC-5 爆破面如实登记**：任何收紧都会改变**既有**声明 `EVIDENCE_COVERAGE` 的合约的结论
  （已知：`domain_discovery` min 10、`console_demo_deliverable` min 1，外加测试夹具）。
  **逐个点名**哪些路径会因此改判、以及它们**各自**如何满足新口径——**不得**用「反正 CI 绿了」
  代替这份清单。
- **AC-6 本地门禁**：规模门禁自查（**50 行函数 / 450 行文件**）→ 定向套件 →
  `make validate-all`（m0 全量 23/23）→ 治理 `validate.py` 绿。**默认门一律离线**。
- **AC-7 记录**：独立 RECHECK（含 W 列表）+ GOAL 回写（EC-02 状态、迭代日志、`child_plans`）；
  **失败如实落终态**（`FAILED` 不得写成成功）。

## 实施清单

- [x] WP1 **证据面审计 + 判别性质定案**（本 PLAN 的承重墙，**先做，不做完不进 WP2**）。
      产出：证据创建点的**全清单**（谁在什么条件下造 `SourceRecord` / `Evidence`）、
      各自的 `origin` 与 `trust_label`、**真实 run 路径今天有没有任何真实来源**、
      以及收紧后的**爆破面清单**（AC-5）。定案必须写明**候选与取舍**，见「影响报告」。
      **已定案**（E-1…E-10 + 来源类取舍 + 逐个点名的爆破面 + 成对落地的硬约束）：
      判别性质 = 「来源的对象**不是**本任务自己产出的 artifact」；主来源类 = 契约声明的输入制品；
      工具结果只接链；manifest / 协议 / 端点事实 / **惰性工具的 `"inert"` 观测**列为被拒来源类。
- [x] WP2 **把真实来源接进 run 链**（机制由 WP1 定案）。约束：**不得**为了让判据绿而
      在测试侧伪造来源；来源必须由**产品路径**在**真跑**中产生。
      **已完成**（WP2a…WP2e 全部落地，成对）：声明面用既有无消费者的 `ProtocolPhase.inputs`
      （`CompiledPhase.inputs` + 编译器透传）；供应面 `services/api/demo.py` 的 `DECLARED_INPUTS`
      + `seed_declared_inputs()` 把**仓库真文件字节**内容寻址地种入 store 并 `mark(VERIFIED)`；
      登记面 `register_declared_input_sources` 造 `SourceRecord(USER_PROVIDED)` + `Evidence`
      （`artifact_id` = **输入制品** id）并挂 `SUPPORTS` relation；计数面
      `evidence_source_count` 改为 `artifact_id ∉ self_artifact_ids`。**id 命名空间先核对过**：
      自述 `{task_id}:{name}` / 工具 `tool-result:…` / 输入 `input-corpus:…` 三者不相交。
- [x] WP3 **判据 + 反证**：同源判据钉住判别性质与被排除的那一类；**被压过**（撤掉收紧 ⇒ 红）。
      **已完成**：`tests/architecture/python/test_declared_input_sources.py`（3 用例：协议声明 ==
      `DECLARED_INPUTS`、字节 digest 可重算、`created_by == "composition-root"`）+
      `tests/application/evidence/test_provenance.py`（自述计 0 / 声明输入计 1 `USER_PROVIDED` /
      输入缺失 ⇒ `InvalidInputError`）。**三次压制全部先红后绿**（见「WP2–WP5 证据」）。
- [x] WP4 **真实 run**（最小必要次数）：来源记录可读 + `origin` 不是交付物自身（AC-2）；
      去掉来源 ⇒ 判拒（AC-3）。样本落 RECHECK，**不含凭据值**。
      **已完成**：`tests/e2e/test_evidence_chain_source_live.py` ⇒ run
      `a2a1bfbf-fea1-44a5-bfd0-ac3396d5d054` **`SUCCEEDED`**、`failures` 为空；读面 4 条来源
      （2 `GENERATED` 自述 + **2 `USER_PROVIDED` 声明输入**），被引用对象
      `created_by=composition-root`；样本 `scratch/ec02-live/ec02-live-source.json`。
      **如实登记：live 调用 4 次**（3 次是判据/读面胶水缺陷，非端点缺陷；仍超出「最小必要」）。
- [x] WP5 **本地门禁 + 复检 + 收口**：定向 → m0 23/23 → 治理绿 → RECHECK → GOAL 回写。
      **已完成**：定向套件绿；全量 m0（CI 同形配置）绿；治理 `validate.py` 绿；
      `RECHECK-20260921-128` = **PASS_WITH_WARNINGS**；GOAL-010 已回写（EC-02 / 迭代日志 /
      `child_plans` / `latest_recheck` / 状态历史），沉淀 `MEM-20260921-101`。

## 证据

### WP1 — 证据面审计与定案（**已完成**）

derive 时已核对（**只读代码，未发起任何调用**）：

| # | 事实 | 核对方式 | 结论 |
| --- | --- | --- | --- |
| E-1 | 真实 run 的 evidence **全部**派生自会话自身输出 | 读 `result_handler.register_session_result` → `_artifact_for_output` → `_evidence_from_artifact` → `_register_into_ledger` | `origin = evidence.source_ref = artifact.storage_uri or artifact.id`；`trust_label = TrustLabel.GENERATED` ⇒ **交付物是它自己的来源** |
| E-2 | 覆盖计数就是 evidence 条数 | `result_handler.ResultRegistration.evidence_source_count = len(self.evidence)`；`task_phase_helpers.evaluate_gate` 把它直接喂给 `EvaluationInputs.evidence_source_count` | `EVIDENCE_COVERAGE ≥ 1` 在**任何**产出交付物的 run 上**恒成立** |
| E-3 | **run 链里没有任何工具结果** | `grep -rn "ToolResultRecord" packages services adapters` ⇒ 只出现在 `evidence/tool_evidence.py`、`experiments/usage_collection.py`、`ports/tool_provider.py`；`packages/application/run_orchestration/` **零命中** | run 编排**不产生** `ToolResultRecord` ⇒ 今天**不可能**有工具来源的证据 |
| E-4 | 工具证据准入路径**存在但未接线** | `register_tool_evidence` 的调用点只有 `tests/application/evidence/test_tool_result_not_evidence.py`（**无生产调用方**） | 它要求 `ToolResultRecord.status == SUCCEEDED` + 内容已 spill 且 `Digest.of_bytes(content) == output_digest`（**可重算**）⇒ 是合格的「真实可查来源」胚子，但**没接进 run** |
| E-5 | 声明 `EVIDENCE_COVERAGE` 的合约只有两条 | `grep -rn "EVIDENCE_COVERAGE" examples/contracts/*.yaml` | `domain_discovery`（min **10**）、`console_demo_deliverable`（min **1**）；另有测试夹具（`run_fixtures`、`scenario_catalog`）⇒ 爆破面**有限但非空** |

**E-3/E-4 合起来是本 cycle 的核心困难**：真实 run 里**没有**真实来源可接——
`register_tool_evidence` 是唯一合格的胚子，却在 run 链之外。因此 WP2 不是「改一行」，
而是**在 run 链里开出第一个非模型来源**；WP1 必须先把「哪一个」定下来。

#### WP1 执行补充：判据落在哪一层（**读码实测**）

| # | 事实 | 核对方式 | 结论 |
| --- | --- | --- | --- |
| E-6 | 验收门**只吃一个整数** | `packages/domain/acceptance.py:144-155`：`_evaluate_evidence_coverage` 读 `criterion.minimum_sources` 与 `inputs.evidence_source_count`，`count >= minimum` 即判过 | 「什么算来源」的判据**不在** Domain、不在门里，而在**编排**（喂进来的那个数）⇒ 收紧**不需要**改 Domain / 改 gate，**不触发** escalation 里的 Canonical State 边界 |
| E-7 | 工具平面**确实产出可核验的 spill 制品**，但生产调用方只在适配器 | `spill_large_result` 的调用方：`adapters/mcp/provider.py`、`adapters/research_tools/ncbi.py` | 工具来源**有真实产出方**（MCP / NCBI 检索），只是 run 链没接 |
| E-8 | 输入制品槽位**存在**但通用路径不填 | `RunManifest.input_artifact_digests`（`packages/domain/manifest.py:66`，默认空）；全仓**唯一**填充点：`packages/application/m12_reference/恢复生命周期v1.py:82` | 契约声明的输入制品是**已存在的 Domain 槽位**，缺的是「供应 + 登记为来源」这条链 |
| E-9 | 两条 min-1 合约声明的能力**正是读取/检索** | `examples/contracts/task_contracts.yaml`：`console_demo_deliverable` 要 `artifact.read`；`domain_discovery` 要 `literature.search` + `literature.read`，产物是 `source_set` | 合约**自己的声明**指向「来源来自工具/输入」，不是我们新造的口径 ⇒ 本 PLAN 的方向与既有设计同源 |
| E-10 | live 判据里的工具是**惰性**的 | `tests/e2e/live_run_support.py:25-70`：`InertExecutor` 恒返回 `Observation.from_text("inert")` | **把惰性工具的结果登记为来源是不可接受的**：它虽非模型自述，但内容恒为 `"inert"`，等于用「非模型」的形式换掉「真实」的实质——**明文列为被拒来源类** |

#### 定案（AC-1 / AC-2 / AC-5 的答案）

**判别性质（AC-1）**：一条 source 计入 `EVIDENCE_COVERAGE`，**当且仅当它的对象不是本任务
自己产出的 artifact**（即 `origin` 不落在本任务会话产出的那批 artifact id 上）。这条性质
**可判、在编排边界可算、不需要 Domain 字段**（E-6），并且**模型自述不可能满足它**——
因为模型的自述**必然**是它自己的产出。

**合用的来源类（substantive，按优先级）**：

1. **契约声明的输入制品**（E-8 的槽位）：run 冻结时其 digest 已知、内容寻址、**可独立重算**；
   Fake 与真实路径都能有；不依赖模型是否调用工具 ⇒ **本 cycle 的主来源类**。
2. **工具结果**（E-4/E-7）：`register_tool_evidence` 登记工具平面真实 spill 的产物，
   语义最强（是「读过」的直接观测）；**本 cycle 只接链、不依赖它满足 min**。

**被拒的来源类（登记为反例，防以后有人拿它凑数）**：manifest / 协议定义 / 端点探测事实 /
运行指纹——它们与任务的 claim **没有 grounding 关系**，登记它们只把计数抬上去而不让 claim
更真；**尤其**是 live 判据里那条**惰性**工具（E-10），内容恒为 `"inert"`。

**爆破面（AC-5，逐个点名 + 各自如何满足新口径）**：

| 声明 | 值 | 谁在跑它 | 收紧后是否改判 | 如何满足新口径 |
| --- | --- | --- | --- | --- |
| `domain_discovery` | min **10** | **没有任何 run 路径**——`minimum_sources: 10` 在全仓只出现在 `tests/domain/test_tasks_acceptance.py:223`（手搭 `CriterionInputs`，**不经 run**）与 catalog 文件 | **不改判** | 如实登记：**它的 min 10 在 run 面上从未被行使过**（既没被满足过，也没被违反过）⇒ 本 cycle **不**为它造来源；要真被行使需检索类工具结果（来源类 2 的真实接线），**登记为残余** |
| `console_demo_deliverable` | min **1** | 绑 `examples/protocols/console_demo_research_v1.yaml`；**三条**路径使用：console demo、`tests/e2e/test_ec03_real_runtime_offline_chain.py`、EC-01 的 live 判据 | **会改判** | 该协议两个 phase 的 task 都声明 `artifact.read`（E-9）⇒ 给 run 供应**契约声明的输入制品**并登记为来源 |
| `sort_analysis_review` | min **1** | 夹具两处：`tests/api/run_fixtures.py:85`、`tests/e2e/scenario_catalog.py:148` | **会改判** | 同口径：夹具侧供应输入制品（**不是**为了判据绿而伪造来源——制品内容与 digest 由夹具真实构造并通过 `ArtifactStore` 落盘） |

**硬约束（写死，WP2 必须遵守）**：**收紧与给来源必须在同一提交里成对落地**。
只收紧 = 把 console demo / EC-03 离线链 / **EC-01 刚达成的 `SUCCEEDED`** 一起打回 `REJECT`
——那是拿 EC-01 换 EC-02，本 GOAL 明文不许（「不得用 Fake 结构化输出伪造成功路径」的反面：
也不得为了让本 EC 成立而毁掉已成立的 EC）。

**这条来源口径的诚实边界（AC-8 要写进判据）**：来源类 1 证明的是「**交付物与它被供应的
输入之间有可核验的 grounding 关系**」（digest 可重算、可指认），它**不**证明任务**真的读了**
那份输入——「真的读过」只有来源类 2（工具观测）能证。**不得**把前者写成后者。

**未定项（如实登记，不自行拍板）**：`domain_discovery` 的 min 10 要真被行使，
需要为检索类任务接上真实检索来源（`literature.search` 的生产工具 + 其结果的 spill 与登记）；
这是**新的检索能力接线**，不在本 PLAN 的 AC 内，登记为**残余**交后续 cycle。

### WP2–WP5

**WP2 设计（WP1 定案后的落地方案；下一续点从这里执行）**

先记三条**读码实测**的现状（决定了为什么 WP2 必须跨层，而不是改一行）：

| # | 事实 | 结论 |
| --- | --- | --- |
| E-11 | `ProtocolPhase.inputs`（`packages/domain/protocols.py:144`）**字段存在、无消费者**；`examples/protocols/` 下**没有任何**协议写 `inputs:` | 「输入制品」的**声明槽位本来就有**，缺的是**消费它的链**——这与 E-9（合约声明 `artifact.read`）同源 |
| E-12 | `packages/domain/manifest.py:8-11` 的**既有纪律**：`input_artifact_digests` 等字段「当前无法从 compile/preflight 上下文获取，**保持 None/空（不做伪填充）**」 | 供应面**不得**用「填个常量凑数」的方式打开；必须真有对象（内容寻址、digest 可重算），否则就按既有口径留空并让 preflight 判拒 |
| E-13 | `PreflightContext` 已有「组合根声明的事实」通道（`execution_substrate`、`runtime_fingerprints` 都从这里冻结进 manifest，见 `manifest.py:13-20`） | 供应的**接入点已存在**，不需要新造通道 |

**WP2a 声明面**：协议 phase 用**既有** `ProtocolPhase.inputs` 声明该 phase 要读的输入制品名
（示例协议 `console_demo_research_v1.yaml` 的两个 phase + `sort_analysis` 夹具）。
**WP2b 供应面**：preflight 把声明的输入名解析到**真实对象**——对象须已内容寻址地存在于 `ArtifactStore`
（由组合根 / 夹具**真实构造并落盘**，不是常量），digest 冻进 `RunManifest.input_artifact_digests`。
**解析不到真实对象时不得伪填充**（E-12）：按 preflight 既有口径判「输入 Artifact 不完整」并拒绝进 RUNNING
（AGENTS §3 的既有检查项，不新造判据）。
**WP2c 登记面**：run 链在注册任务结果时，把**本任务声明的输入**登记为 `SourceRecord`
（`origin` = 输入制品 id，`content_digest` = 该对象 digest，与 `artifact.storage_uri or artifact.id` 的自述来源**可区分**）
+ 一条 `Evidence`（`artifact_id` = **输入制品** id，**不是**本任务产出的 artifact）。
**WP2d 计数面（判别性质落地）**：`ResultRegistration.evidence_source_count` 改为**只数非自身来源**
（`origin` 不落在本任务会话产出的那批 artifact id 上）。**门与 Domain 不动**（E-6）。
**WP2e 成对落地（硬约束）**：`console_demo_deliverable` 与 `sort_analysis_review` 两条 min-1 路径
必须**在同一提交**里拿到 ≥1 条真实来源（见「爆破面」表的「如何满足新口径」列）。

**WP2 的验收边界**：WP2 只负责「接上 + 收紧成对落地」；
**AC-2/AC-3 的真跑与反证归 WP4**（真实 run 的读面 + 去掉来源 ⇒ 判拒）。

**WP2 起手前必须先确认的一条**：`ArtifactStore` 的既有实现里，**输入制品的 id 约定**是什么
（自述来源用 `{task_id}:{name}`）——输入制品**不得**与任务产出共用同一 id 命名空间，
否则「非自身」的判别会在 id 层面失效（这正是 W-4 那类「换个名字冒充来源」的入口）。

## 影响报告

### 本 PLAN 的承重墙是 WP1，不是 WP2

**为什么先审后改**：EC-01 的机制可以在**一处可判事实**（结构化输出的键名）上打开，
所以那个 cycle 是「定位 → 改 → 压过」。EC-02 **不是**：E-3/E-4 说明真实 run 链里
**根本不存在**非模型来源，因此「让覆盖由真实来源满足」等于**新开一条链**。
先动代码会得到两种坏的结局之一——要么接进来的「来源」其实还是模型自述换个名字
（判据绿而事实没变），要么为了让判据绿而在测试侧造来源（**明文禁止**）。
所以 WP1 的产出（判别性质 + 爆破面清单）**先于**任何实现。

### 候选（WP1 必须在其中定案并写明取舍）

| 候选 | 做法 | 收益 | 代价 / 风险 |
| --- | --- | --- | --- |
| **A. 接工具结果**（`register_tool_evidence` 进 run 链） | run 编排把会话中真实的工具结果 spill 成 artifact 并登记为来源 | 来源是**工具观测**、digest **可重算**，语义最正 | 需要 `ToolResultRecord` 的**产出方**——而 live 判据里工具是**惰性**的（`register_inert_tools`），真跑**产不出**结果 ⇒ 需要改测试装配，**逼近「为判据改环境」的红线** |
| **B. 接真实输入制品** | 给 phase 供应**真实存在的输入 artifact**（内容寻址、digest 已知），把「本任务读过它」登记为来源 | 来源在 run **之外**产生、**可独立核验**；Fake 与真实路径都能有 | 需要**输入供应**这条新链；且来源**先于 run 存在**，「支撑」的强度弱于工具观测 |
| **C. 接 workspace 制品** | 会话结束前后把 workspace 里**真实存在**的文件登记为来源 | 文件系统事实、digest **可重算** | live 判据里工具惰性 ⇒ 会话**写不出**文件；要靠预置，同样逼近红线 |
| **D. 仅收紧口径、不接来源** | 让覆盖**不能**由 GENERATED 满足，接受既有路径开始判拒 | 最小改动 | **AC-2 达不成**（真实 run 将**没有**来源）且会**打断** console demo（`EVIDENCE_COVERAGE: 1`）⇒ 单用 **不可行**，只能作为 A/B/C 的**配套**（那才是 AC-4 的收紧） |

**倾向（WP1 已定案，见「WP1 — 证据面审计与定案」末节，不是预判）**：**来源类 1（契约声明的
输入制品）为主来源、来源类 2（工具结果）只接链**；C 否决（依赖预置文件，且 Fake / live 装配下
会话写不出文件）；D **只作配套的收紧**、不与给来源拆开落地。
无论选哪个，**判别性质**都要能回答「为什么模型自述**不可能**满足它」（AC-1）。

### 与 EC-01 的关系：**不要**顺手把 EC-01 的机制当来源

交付物 artifact 是**合约声明命名**的会话输出（EC-01 的成果）——它**仍然是模型自述**。
把它的名字换成合约名**不**使它成为来源。本 PLAN **不得**用「名字对了」冒充「来源真实了」；
这正是 `RECHECK-20260921-127` 的 **W-4** 点名未解决的缺口。

### 爆破面（AC-5 的起点，WP1 必须补全）

- `console_demo_deliverable`（`EVIDENCE_COVERAGE: 1`）：console demo（Fake 路径）、
  EC-03 离线链、EC-01 的 live 判据**都**绑它 ⇒ 收紧后**必须**各自能给出真实来源，否则
  它们会从 PASS 变 REJECT。**这是本 PLAN 最大的风险面**。
- `domain_discovery`（min **10**）：需要 10 个真实来源——今天**没有**任何路径能给出。
  若某个用例用它，收紧后必红。**WP1 要点名它是否在被跑路径上。**
- 测试夹具（`tests/api/run_fixtures.py`、`tests/e2e/scenario_catalog.py`）里的
  `EVIDENCE_COVERAGE` 声明：**逐个点名**。

### 失败如何落终态

- 真实 run **不能**由真实来源满足覆盖 ⇒ 如实归类（来源面 / 装配面）并按 fix_policy 纠错；
  **不得**把 `FAILED` 写成成功、**不得**降低判据、**不得**在测试侧伪造来源。
- 若定案**需要**给验收标准加字段 / 改 Domain / 动 Canonical State 边界 ⇒ **BLOCKED**
  （GOAL frontmatter 的 escalation_triggers），留人工拍板。

## 状态历史

- 2026-09-21 derive：由 GOAL-20260921-010 的 EC-02 派生（`parent_goal` 投影 ALL_PLAN）。
  派生时**只读代码、未发起任何调用**，得到 E-1…E-5；其中 **E-3/E-4**（run 链无工具结果、
  工具证据准入未接线）决定了本 cycle 的形状：**先审后改**，且承重墙是 WP1。

- 2026-09-21 WP1 定案（`8d3afd4` 推送并已入 CI 台账）：判别性质 = 「来源的对象**不是**本任务
  自己产出的 artifact」；落在**编排**（E-6：门只吃整数 ⇒ 不碰 Domain、不碰 gate）；
  主来源类 = **契约声明的输入制品**；被拒来源类点名四类（含**惰性工具的 `"inert"` 观测**）。
  爆破面实测比预估小（`minimum_sources: 10` 无 run 路径行使），并写死硬约束
  **「收紧与给来源必须同一提交成对落地」**。

- 2026-09-21 WP2–WP5 完成，**本 PLAN 收口 DONE**（`RECHECK-20260921-128` =
  **PASS_WITH_WARNINGS**）。**成对落地**：来源面（协议声明 → 组合根种入 → 登记为
  `USER_PROVIDED` 来源 → 挂 relation）与计数收紧（`artifact_id ∉ self_artifact_ids`）
  **同一提交**。**真跑**：run `a2a1bfbf-fea1-44a5-bfd0-ac3396d5d054` **`SUCCEEDED`**，
  读面 4 条来源（2 自述 + 2 声明输入），被引用对象 `created_by=composition-root`、
  digest 可重算。**反证三次被压过**（去声明 / 去种入 / 撤收紧，各自先红后绿）。
  **如实登记**：live 调用 **4** 次（超「最小必要」，3 次是判据/读面胶水缺陷）；
  `sort_analysis_review` 合约**新增**一条 `ARTIFACT_EXISTS`（收紧，但属判据面改动，
  独立复核应重点压它）；`domain_discovery` min 10 **仍未在 run 面上被行使**（残余）；
  `inputs` 只表达**外部供应**的输入、不表达 phase 间引用。

### WP2–WP5 证据（判据与压制）

**新增/改动的判据**（**没有任何一条被放宽**；`packages/domain/acceptance.py` 与
`examples/contracts/task_contracts.yaml` 的 `minimum_sources` 数值**零改动**）：

| 判据 | 钉住什么 |
| --- | --- |
| `tests/architecture/python/test_declared_input_sources.py`（**新**，3 用例） | 协议 YAML 的 `inputs:` 声明 == `DECLARED_INPUTS` 表；输入制品字节 digest **可重算**；`created_by == "composition-root"`；`services/api/composition.py` **确实**调用 `seed_declared_inputs(` |
| `tests/application/evidence/test_provenance.py`（重写） | 模型自述计 **0**；声明输入计 **1** 且 `trust_label=USER_PROVIDED`；声明输入**不在 store 里** ⇒ `InvalidInputError`（fail-closed） |
| `tests/e2e/test_evidence_chain_source_live.py`（**新**） | EC-02 的 live 判断：读面里存在 `source_origin == "input-corpus:console_demo_v1"` 且 `source_trust_label == "USER_PROVIDED"`、被引用对象 `created_by == "composition-root"` |
| `tests/e2e/test_vertical_slice_happy_path.py`（改） | 制品总数 = 产出 4 + 种入 `len(DECLARED_INPUTS)`；**按 id 分开**并各自断言 `created_by` |

**三次压制（全部先红后绿，复原后 `git diff` 只剩意图内改动）**：

| # | 压制 | 红在哪 |
| --- | --- | --- |
| ① | 去掉**协议声明**（`sort_analysis_v1.yaml` 的 `inputs:`） | 同源判据 1 用例 + vertical slice **6 用例**（review 覆盖归零 ⇒ 判拒） |
| ② | 去掉**种入**（`M7Harness` 的 `seed_run_inputs`） | vertical slice **6 用例**（`declared input artifact … is not in the artifact store`） |
| ③ | 撤掉**收紧**（`evidence_source_count` 改回 `len(self.evidence)`） | `test_provenance.py` **3 用例**（`1 != 0`） |

**AC-2/AC-3 的真跑与反证**归 WP4：live 判据 PASS（非 skip），run 终态**恰为 `SUCCEEDED`**；
「去掉来源 ⇒ 判拒」由压制 ①② 在同一路径上取证（remove ⇒ `EVIDENCE_COVERAGE` 判 `False` ⇒
`rejected by acceptance gate`），复原后复绿。

**证据诚实边界（AC-8）见 `RECHECK-20260921-128` 的 W-1…W-8**，其中 W-1（合约新增
`ARTIFACT_EXISTS`）与 W-2（live 调用超最小必要）是两处**须人工复核**的登记项。
