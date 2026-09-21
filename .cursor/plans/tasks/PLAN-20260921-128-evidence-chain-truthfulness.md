---
id: PLAN-20260921-128
slug: evidence-chain-truthfulness
title: 证据链真实性：让 `EVIDENCE_COVERAGE` 由真实可查来源满足，而不是由模型自述（GOAL-010 EC-02）
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: []
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

- [ ] WP1 **证据面审计 + 判别性质定案**（本 PLAN 的承重墙，**先做，不做完不进 WP2**）。
      产出：证据创建点的**全清单**（谁在什么条件下造 `SourceRecord` / `Evidence`）、
      各自的 `origin` 与 `trust_label`、**真实 run 路径今天有没有任何真实来源**、
      以及收紧后的**爆破面清单**（AC-5）。定案必须写明**候选与取舍**，见「影响报告」。
- [ ] WP2 **把真实来源接进 run 链**（机制由 WP1 定案）。约束：**不得**为了让判据绿而
      在测试侧伪造来源；来源必须由**产品路径**在**真跑**中产生。
- [ ] WP3 **判据 + 反证**：同源判据钉住判别性质与被排除的那一类；**被压过**（撤掉收紧 ⇒ 红）。
- [ ] WP4 **真实 run**（最小必要次数）：来源记录可读 + `origin` 不是交付物自身（AC-2）；
      去掉来源 ⇒ 判拒（AC-3）。样本落 RECHECK，**不含凭据值**。
- [ ] WP5 **本地门禁 + 复检 + 收口**：定向 → m0 23/23 → 治理绿 → RECHECK → GOAL 回写。

## 证据

### WP1 — 证据面审计（进行中）

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

### WP2–WP5

待执行后回填。

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

**倾向（待 WP1 用证据定案，不在本 PLAN 里预判）**：**B 或 A**；C 依赖预置、D 单用不可行。
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
