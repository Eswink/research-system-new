---
id: PLAN-20260922-134
slug: retrieved-evidence-nature
title: 证据链的「系统取得」性质：TrustLabel 加 RETRIEVED + 覆盖判据按来源性质判（GOAL-011 EC-02）
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
    GOAL-20260922-011 cycle 5 = EC-02（证据链从「声明输入」升级为「系统取得」）。授权来源：2026-09-22
    用户 goal 模式指令 frontmatter `authorization.ref`——(1) live-gated 真实调用（端点 `ANTHROPIC` +
    `agnes-2.5-flash`，凭据仅在本机 gitignored `.env`，键名 `LLM_MAIN_KEY`）；(2) **允许真实检索出网**——
    仅 NCBI E-utilities（`eutils.ncbi.nlm.nih.gov`），只在该 provider 的 `network_domains` 声明范围内，
    次数取最小必要；(3) 凭据纪律不放松（值不得进任何 tracked 文件/DB/记录/日志/回显；
    `RESEARCHOS_AGENT_RUNTIME` 只作单条命令内联前缀，不得写进 `.env`）；(4) 默认 runtime 保持 Fake、
    默认 CI 离线，**不得为了跑检索而放宽出站判据**（`tests/egress_guard.py` 是结构判据），检索/live 类
    用例必须挂 `requires_live_llm`（或同一放行面）才可出网；(5) push-to-main-for-CI（只推 main、
    不 force、不重写历史）。**本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；
    skip/删除测试、降低断言强度；`git add -A`；伪造或夸大验证证据；放宽验收门（AcceptanceCriteria）
    凑成功；**为跑通而放宽出站判据**；新增依赖或改上游 pin；把真实 runtime 设为默认；把凭据写进 CI。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-134 — 证据链的「系统取得」性质（GOAL-011 EC-02）

## 目标

EC-01 已经把**检索来源**接进运行链（真实 esearch/efetch、PMID 逐字进证据链），但读面与验收门
**还看不出这条来源的来路**：`SourceRecord.trust_label` 今天只被赋 `USER_PROVIDED`（声明输入）
与 `GENERATED`（会话自述/实验产出），**没有「系统取得」这一档**；`EVIDENCE_COVERAGE` 也只吃一个
整数（非自产来源数）⇒ 覆盖今天由**声明输入**满足，与「系统真的去取了」无关。

本 PLAN 让**来源性质**成为一等事实：读面可区分 `USER_PROVIDED` 与 `RETRIEVED`，
覆盖判据**由检索来源满足**，并且**去掉检索来源 ⇒ 覆盖判拒**（成对反证）。

## 验收条件

- **AC-1 读面可区分且口径诚实**：同一次真实 run 的 `GET /runs/{id}/evidence` 上，
  声明输入来源报 `USER_PROVIDED`、检索来源报 `RETRIEVED`，**不混称**；
  模型自述（会话产出）**不**得报成外部取得。
- **AC-2 覆盖由检索来源满足（性质判据，不是计数）**：`EVIDENCE_COVERAGE` 的满足集合
  **含检索来源**；该来源**可追溯到外部标识**（PMID/DOI/URL）且 **digest 可独立重算**。
  **不得**用「计数 ≥ 1」代替来源性质；**不得**用模型自述充当外部来源。
- **AC-3 反证成对（EC-02 本体）**：从绿出发，**去掉检索来源** ⇒ 同一 run 的
  `EVIDENCE_COVERAGE` **判拒**（run 收敛 `FAILED`，诊断点名覆盖判词）；复原 ⇒ 复绿。
  只绿不红 ⇒ 判据没在看。
- **AC-4 出网纪律**：真实检索**只**打到 `eutils.ncbi.nlm.nih.gov`；**次数取最小必要**；
  **默认门一律离线**、`tests/egress_guard.py` **一行不改**；live 用例挂 `requires_live_llm`；
  live 只用**单条命令的内联前缀** `RESEARCHOS_AGENT_RUNTIME=openhands` 开，**跑后不留开关**。
- **AC-5 规模门禁**：**50 行函数 / 450 行文件**两道门仍绿；`services/api/composition.py`（450 行，
  零余量）与 `phase_runner.py` / `service.py`（各 450 行）**本 PLAN 一律不改**。

## 计划开始前的定案（写死，执行中不得回退）

### D-1 载体 = `TrustLabel` 新增 `RETRIEVED` 成员

- EC-02 逐字要求读面区分 `USER_PROVIDED` 与 `RETRIEVED`，而 `EvidenceDto.source_trust_label`
  **就是**那条读面（GOAL-010 EC-02 加的），它的值直接取 `SourceRecord.trust_label`。
  另造「派生性质字段」只有两条路：在编排里用启发式推（本仓明文拒绝前缀启发式——
  `result_handler.evidence_source_count` 的注释写死「判别是**集合判定**，不是 id 前缀启发式」），
  或在 `SourceRecord` 上加第二个 nature 字段（**更大**的 Domain 改动）。两条都更差。
- **边界论证（结论：不触及 Canonical State 边界，不构成 escalation）**：`TrustLabel` 是
  **分类枚举**，不是状态机。本次改动是**加一个成员**：不改既有成员语义、不改 Evidence/Claim
  生命周期、不改任何状态转移、无 CHECK 约束（`trust_label TEXT NOT NULL`，SQLite 与 PG 同形）
  ⇒ **不需要迁移**，既有行含义不变。escalation 里那条指的是「把验收门结果改成可改写已终态的行」
  这类**边界**动作，本改动不属该类；且 EC-02 是 GOAL frontmatter（优先级最高）逐字写出的要求
  ⇒ 属**被授权**的改动。今天 `TRUSTED_INTERNAL` / `VERIFIED_SOURCE` 已是「生产路径零赋值」的成员，
  新增一个同类成员不引入新的语义类别。

### D-2 覆盖判据 = 新增**可选**参数 `minimum_retrieved_sources`（并存于既有计数）

- 把 `evidence_source_count` 收窄成「只数检索来源」会**回退** GOAL-010 EC-02 已判绿的语义
  （声明输入是第一类非自身来源），并把没有检索的协议（`console_demo_*`、`real_research_task_v1`）
  一并打红 ⇒ 那是**回归**，不是收紧。
- 新增**性质维度**：`AcceptanceCriterion.minimum_retrieved_sources`（缺省 `None` ⇒ 行为**逐字不变**）。
  只有显式声明的合约多受一条**更严**的要求 ⇒ 「不得用计数 ≥ 1 代替来源性质」被逐字满足：
  判的是**性质分类下的计数**。

### D-3 盖章点唯一：`ToolEvidenceInput.trust_label`，由调用方按 **provider 声明性质**给值

- provider 声明了 `network_domains`（外部网络域）⇒ `RETRIEVED`（内容取自系统之外）；
  否则缺省 `GENERATED`（**不**自称「系统取得」）。`register_tool_evidence` 仍是工具证据的
  **唯一**准入入口，盖章规则写在它的输入对象上，不在读面/门里再推一次。

### D-4 判据（成对、必按压）

1. 机制：RETRIEVED 盖章 ⇒ 读面报 `RETRIEVED`；`minimum_retrieved_sources=1` 且检索来源为 0 ⇒
   `EVIDENCE_COVERAGE` 判 `False`（原因点名性质），为 1 ⇒ 判 `True`。
2. 「模型自述不算外部来源」：只有自述证据的注册结果 ⇒ 覆盖判拒（即便证据条数 ≥ 1）。
3. e2e（生产装配、离线）：`SUCCEEDED` + 同一 run 上 `USER_PROVIDED` 与 `RETRIEVED` 并存 +
   满足覆盖的来源含检索来源 + `source_ref` 含外部标识 + digest 由 artifact 内容独立重算。
4. **反证（EC-02 本体）**：去掉检索接线 ⇒ 覆盖判拒、run `FAILED`；复原 ⇒ `SUCCEEDED`。
5. live（最小必要）：真实 LLM + 真实检索，同上口径。

## 工作计划

- **WP0** derive：本 PLAN + `ALL_PLAN` 投影（同一提交）。
- **WP1** Domain 面：`TrustLabel.RETRIEVED`；`AcceptanceCriterion.minimum_retrieved_sources`；
  `CriterionInputs.retrieved_source_count` + 求值器；schema / loader / SQLite 往返三处同步。
- **WP2** 编排面：`ToolEvidenceInput.trust_label` 盖章；运行链按 provider 声明给值；
  「检索来源数」由 **ledger 的 SourceRecord** 判定（性质判据的唯一来源）并喂进门。
- **WP3** 合约 + 判据：`real_research_deliverable` 声明 `minimum_retrieved_sources: 1`；
  机制判据 + e2e 主干 + 成对反证；按压（先红后绿再复原）。
- **WP4** live 判据（`requires_live_llm`，最小必要次数）+ 样张落 `scratch/`。
- **WP5** 本地门（规模门禁 / 快照类门禁 / `make validate-all` m0 全量 23/23 / 定向套件 / web 门）。
- **WP6** 回写（GOAL EC-02 / 迭代日志 / child_plans / 状态历史）+ 提交推送 + CI 到终态。

## 决策记录

（执行中追加，只追加不覆盖。）

- **D-5 新合约 `real_retrieval_deliverable`，不动共用契约**（执行中定案，实测理由）：
  `examples/contracts/task_contracts.yaml` 的 `real_research_deliverable` 被**没有检索**的
  `real_research_task_v1`（GOAL-010 的协议）共用；给它加 `minimum_retrieved_sources: 1`
  会把那份协议的 run 一并判拒 ⇒ 那是**回归**而不是收紧。因此新增一份只给检索协议用的合约，
  两份的差别**只有这一条性质维度**。实测：`real_research_task_v1` 的既有判据
  （`tests/api/test_real_protocol_identity.py`、`tests/e2e/test_real_protocol_run_live.py`）
  **零改动**且仍绿。
- **D-6 门被拒时落「逐条判词」**（`gate_rejection_reason`）：EC-02 的反证要求从 canonical
  读面能看出「是**覆盖判据**判的、判词里的数是多少」，而此前 `evaluate_gate` 把被拒结局换成
  `None`、调用方只写一句 "rejected by acceptance gate"——判词被丢掉（GOAL-010 收口登记的
  **W-9「诊断更钝」**同源）。改动是**加词**，既有子串断言不受影响：全仓
  `grep -rn "rejected by acceptance gate" --include=*.py` 只命中**两处生产代码**，
  无测试断言该消息的精确串。
- **D-7 两维分工（写死）**：`evidence_source_count`（非自产来源总数）**语义零改动**；
  性质维度**新增且可选**，只在合约显式声明时参与。两维都过才判过 ⇒「总数够」与
  「有检索来源」**互相不能顶替**（双向反证都做成了判据）。

## 证据（derive 阶段实测；**只读代码/配置，未发起任何真实调用**）

| # | 事实 | 位置（实测） |
| --- | --- | --- |
| E-1 | `TrustLabel` 恰 5 个成员，**无 `RETRIEVED`**；生产路径只赋两种：声明输入 ⇒ `USER_PROVIDED`、会话/实验自产 ⇒ `GENERATED` | `packages/domain/enums.py:244-249`；`packages/application/run_orchestration/result_handler.py:162,235` |
| E-2 | 工具证据的**唯一**准入入口给 `SourceRecord` 盖章 `GENERATED`（含检索证据） | `packages/application/evidence/tool_evidence.py:76`；调用方只有 `packages/application/run_orchestration/phase_capabilities.py:203` |
| E-3 | 覆盖判据**只吃一个整数**：`count >= minimum` ⇒ 过；缺 `minimum_sources` 或缺 count ⇒ fail-closed 判 `False` | `packages/domain/acceptance.py:144-155` |
| E-4 | 这个整数 = **非自产**证据数（`artifact_id not in self_artifact_ids`），声明输入与检索来源都算 ⇒ 覆盖今天由**声明输入**满足 | `packages/application/run_orchestration/result_handler.py:60-68` |
| E-5 | 读面**已经**有 `source_trust_label`（值直取 `SourceRecord.trust_label`）⇒ 加成员即被读面看见，**无需新 DTO 字段** | `services/api/dto/inspection.py:29-35`；`services/api/routers/inspection.py:49-68` |
| E-6 | 新枚举成员**不需要迁移**：`trust_label` 两存储面都是 `TEXT NOT NULL`，**无 CHECK 约束** | `adapters/postgres/migrations/002_domain_state.sql:17`；`adapters/sqlite/evidence_rows.py:37` |
| E-7 | 判据**不在任何 API DTO 里**（`services/` 对 `acceptance_criteria` / `minimum_sources` 零命中）⇒ 加一个可选参数不触发 OpenAPI 快照 | `grep -rn "acceptance_criteria\|minimum_sources" --include=*.py services` ⇒ 0 条 |
| E-8 | 契约 schema 对 criterion 是 `additionalProperties: false` ⇒ 新参数**必须**同时进 schema，否则示例合约加载即失败 | `schemas/task-contract.schema.json:57-84`；`adapters/contracts/tasks_loaders.py:19-32`；`adapters/sqlite/serialization.py:100-112` |
| E-9 | 「什么算来源」的既有定案：收紧放**编排**、判别用**集合判定**、**拒绝** id 前缀启发式 | `packages/application/run_orchestration/result_handler.py:23-30`（模块 docstring）；`.cursor/plans/tasks/PLAN-20260921-128-…md` 的 E-6 |
| E-10 | 规模余量：本 PLAN 触碰的 10 个文件均 **≤ 371 行**（最大 `packages/domain/enums.py`）；贴线的 `composition.py` / `phase_runner.py` / `service.py` **本 PLAN 不改** | `wc -l` 实测 |

## 实施清单

- [x] **WP0 derive**：本 PLAN 建档 + `ALL_PLAN` 投影（同一提交）。
- [x] **WP1 Domain 面**（离线可验）：`TrustLabel.RETRIEVED`；
      `AcceptanceCriterion.minimum_retrieved_sources`（可选，缺省 `None` ⇒ 行为逐字不变）；
      `CriterionInputs.retrieved_source_count` + `_evaluate_evidence_coverage`（性质+计数双判，
      缺一即判拒并点名）；`schemas/task-contract.schema.json` / `adapters/contracts/tasks_loaders.py` /
      `adapters/sqlite/serialization.py` 三处同步（**不改** `minimum_sources` 的任何既有数值与语义）。
- [x] **WP2 编排面**（离线可验）：`ToolEvidenceInput.trust_label`（盖章点唯一）；
      运行链按 provider 的 `network_domains` 声明给 `RETRIEVED`；
      「检索来源数」由 **ledger 的 SourceRecord** 判定（`evidence.source_ref → get_source`），
      经 `EvaluationInputs.retrieved_source_count` 喂进门。
- [x] **WP3 合约 + 判据**：新合约 `real_retrieval_deliverable` 声明
      `minimum_retrieved_sources: 1`（D-5），检索协议改绑它；机制判据（domain 5 条 +
      application 4 条）、e2e 主干加 EC-02 两段（性质可区分 / 检索来源满足覆盖）、
      成对反证改成「零工具观测 **且** 覆盖判拒 ⇒ run `FAILED`」。
- [x] **WP4 live 判据**（`requires_live_llm`，最小必要次数）：**PASS（非 skip）**，
      复原后同命令**再跑一次仍 PASS**；样张 `scratch/goal011-c5-live-facts.json`
      （run `a93e6b36-619b-4e65-b2af-9865d0c87c7e`：`SUCCEEDED`、三种性质并存、
      PMID 逐字可追溯、四条证据 digest 全部重算一致）。
- [x] **WP5 本地门**：规模门禁（50/450，**抓出并修好两条**：e2e 文件 470 行 ⇒ 移出检索判据对；
      live 判据函数 63 行 ⇒ 拆两个辅助函数）+ 快照类门禁（无 OpenAPI/设计基线变化：DTO 零改动）
      + `make validate-all`（m0 全量 **23/23 项全跑**，唯一红项＝**本机既有签名** `python/tests`
      的 fake-IP 出站判红，pytest 自身 4370 passed / 17 skipped / **0 failed**）+ 定向套件
      （`tests/{api,loaders,contracts,architecture,integration}` 1215 passed；`tests/e2e`+`tests/tooling`
      1104 passed）+ 治理 `validate.py` 与 DOCS-CHECK 绿。**默认门全程离线**，`egress_guard` 一行未改。
- [x] **WP6 回写与收口**：GOAL 的 EC-02 置 PASS（含 `status_note`）/ 迭代日志第 5 行 /
      `child_plans` 加本 PLAN / 状态历史 / CI 台账；提交推送 + CI 到终态（见 GOAL 台账）。
      **子 PLAN 自身的 RECHECK 与 DONE 收口留到 EC-06**（登记在 GOAL 的下一轮输入里）。

## 影响报告

**改动文件**（本 cycle，提交按 WP 分组、全部显式路径）：

| 面 | 文件 | 改动 |
| --- | --- | --- |
| Domain | `packages/domain/enums.py` | `TrustLabel` 加 `RETRIEVED`（分类枚举加成员；**无迁移**：`trust_label` 两存储面均 `TEXT NOT NULL`、无 CHECK 约束） |
| Domain | `packages/domain/tasks.py` | `AcceptanceCriterion.minimum_retrieved_sources`（可选；缺省 `None` ⇒ 行为逐字不变；负数点名拒绝） |
| Domain | `packages/domain/acceptance.py` | `CriterionInputs.retrieved_source_count`；覆盖判据改成**计数 + 性质**双维（缺维度 fail-closed 并点名） |
| Application | `packages/application/evidence/tool_evidence.py` | `ToolEvidenceInput.trust_label`＝来源性质的**唯一**盖章点 |
| Application | `packages/application/run_orchestration/phase_capabilities.py` | `_trust_label_for`：provider 声明了 `network_domains` ⇒ `RETRIEVED`，否则 `GENERATED` |
| Application | `packages/application/run_orchestration/result_handler.py` | `count_retrieved_sources`（按 canonical 的 SourceRecord 判性质，与读面**同源**） |
| Application | `packages/application/run_orchestration/evaluation_gate.py` | `EvaluationInputs.retrieved_source_count` 透传 |
| Application | `packages/application/run_orchestration/task_phase_helpers.py` | 喂性质数；`evaluate_gate` 总是返回求值结果；被拒时失败消息带**逐条判词**（D-6） |
| 契约/协议 | `examples/contracts/task_contracts.yaml`、`examples/protocols/real_retrieval_research_v1.yaml` | 新合约 `real_retrieval_deliverable`；检索协议改绑它（D-5） |
| Schema | `schemas/task-contract.schema.json` | `acceptanceCriterion` 加 `minimum_retrieved_sources`（该 schema 是 `additionalProperties: false`，必须同步） |
| 适配器 | `adapters/contracts/tasks_loaders.py`、`adapters/sqlite/serialization.py` | 新字段的加载与解码（编码走既有 `canonical_json_bytes`，自动带上） |
| 判据 | `tests/domain/test_tasks_acceptance.py`、`tests/application/run_orchestration/test_run_chain_capabilities.py`、`tests/e2e/test_ec03_real_runtime_offline_chain.py`、`tests/e2e/test_run_chain_retrieval_live.py` | 机制 / e2e / 反证 / live 四层 |
| 文档 | `docs/architecture/TASK_HANDOFF.md`、`docs/architecture/DOMAIN_MODEL.md`、`docs/architecture/CAPABILITY_SECURITY.md` | 结构化参数、覆盖的两维、`RETRIEVED` 的语义与边界 |

**Domain / API / schema 变化**：Domain 加一个枚举成员与一个**可选**判据参数（均**加性**）；
schema 加一项；**API 面零变化**（`services/` 对 `acceptance_criteria` / `minimum_sources`
零命中 ⇒ 无 DTO/路由/OpenAPI 快照改动，实测 E-7）。

**安全 / 凭据变化**：无新凭据面、无新出网口；检索仍只在 provider 声明的 `network_domains`
内（URL 策略在触网前判，未改）；live 只用环境变量，值不入库 / 记录 / 回显。

**兼容性 / 迁移风险**：**无 DB 迁移**；缺省语义不变 ⇒ 既有协议、既有合约、既有 run 记录的
含义都不变；`real_research_deliverable` 与 `real_research_task_v1.yaml` 逐字未动。

**上游版本影响**：无依赖新增或 pin 变更。

## 状态历史

- 2026-09-22：derive 建档（`status: IN_PROGRESS`）。定案 D-1…D-4 见上；WP1…WP6 未开始。
- 2026-09-22（cycle 5 执行）：WP1…WP4 完成（见实施清单），追加 D-5/D-6/D-7。
  **按压三次全先红后绿**：① 摘掉合约的性质维度 ⇒ 反证用例红（run 回到 `SUCCEEDED`）；
  ② 盖章规则强制成 `GENERATED` ⇒ 主干红，判词逐字
  `EVIDENCE_COVERAGE: 0 < 1 retrieved sources (3 >= 1 sources)`（3 条来源在场、0 条检索来源）；
  ③ **live 同一条命令**摘掉协议里的两条检索能力 ⇒ live 判据红，判词
  `EVIDENCE_COVERAGE: 0 < 1 retrieved sources (1 >= 1 sources)`（1 条声明输入在场）⇒
  复原 ⇒ PASS。live 调用记账：**4 次真实运行**（live 判据 2 次 + 样张 1 次 + 按压 1 次），
  其中 3 次各含**恰 2 次**真实检索出网（`eutils.ncbi.nlm.nih.gov`），1 次（按压）只到 LLM。

