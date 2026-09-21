---
id: PLAN-20260921-127
slug: real-deliverable-contract
title: 真实交付物契约：让真实会话的产出满足合约声明的 artifact 名（GOAL-010 EC-01）
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
    GOAL-20260921-010 cycle 1 = EC-01（真实交付物契约，主干）。授权来源：2026-09-21 用户
    goal 模式指令 frontmatter `authorization.ref`——(1) live-gated 真实调用授权（**次数取最小必要**）；
    (5) push-to-main-for-CI（只推 main、不 force、不重写历史）。**本 PLAN 明文不做**：
    改验收门（`packages/domain/acceptance.py` 保持**字面判定**）、改 `validator`/门禁/快照、
    skip 或降低任何断言强度、新增依赖、改上游 pin、把真实 runtime 设为默认、把凭据写进 CI。
    **D2（事实名 → 合约名的声明权）的定向由用户在 GOAL-010 EC-01 里给出**——用户给出二选一
    (i)/(ii) 并要求「受控、声明化、可审计」，本 PLAN 取 **(ii) 的声明化形态**（见「影响报告」D2 节）；
    该定向**不等同于**采纳 ADR-0031 整体（D1 仍未决，`Status: Proposed` 保持不变）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260921-127 — 真实交付物契约（GOAL-010 EC-01）

## 目标

把「**真实会话的产出如何满足合约声明的 artifact 名**」落地成**有终态的契约**，使**一次真实 run
在真实执行体下验收门 PASS 且终态恰为 `SUCCEEDED`**（GOAL-009 EC-01 那次是 `FAILED`），
并且这个成功**经得起反证**：把声明对齐摘掉 ⇒ **回到 REJECT**。

**不做的事**：不改验收门的判定语义（`packages/domain/acceptance.py` **保持字面匹配**）、
不为了让门通过而改合约、不用 Fake 结构化输出充充当本 PLAN 的证据。

## 验收条件

- **AC-1 判据（same-source）**：存在一条**结构判据**把「交付物键名由**合约声明**决定」钉住，
  且它**被压过**（改坏声明 ⇒ RED；复原 ⇒ GREEN，`git diff` 只剩意图内改动）。
- **AC-2 受控边界**：合约声明**恰好一个** artifact 名 ⇒ 交付物用该名；声明**零个**或**多个
  互不相同**的名字 ⇒ **不猜**（保持事实名）——该边界**有判据**，不是注释里的承诺。
- **AC-3 可审计**：交付物 payload 带**来源事实**（合约 id / 声明名 / 事实名 / 会话与对话 id），
  读者能从读面判断「这个名字是**谁**声明的」，而不是只能看到结果。
- **AC-4 验收门**（ADR-0031 的结构判据）**不被修改且仍绿**：
  `tests/tooling/test_toolpack_capability_policy_pending.py` 原样通过——
  特别是 `test_the_acceptance_gate_still_matches_artifact_names_literally`。
- **AC-5 反证成对**：离线同路径链上，**声明对齐 ⇒ 门 PASS**、**声明不对齐 ⇒ 门 REJECT**
  两条分支**同时**有用例覆盖；GOAL-009 记的那条「判拒是链在正常工作」的证据**不丢失**。
- **AC-6 真实 run**：**一次** live run（最小必要次数）在真实执行体下验收门 **PASS**、
  canonical 终态**恰为 `SUCCEEDED`**；逐条 criterion 的 reason 落记录。
- **AC-7 本地门禁**：规模门禁自查（**50 行函数 / 450 行文件**）→ 定向套件 → `make validate-all`
  （m0 全量 23/23）→ 治理 `validate.py` 绿。**默认门一律离线**。
- **AC-8 记录**：RECHECK（独立复检）落盘；GOAL-010 的 EC-01 状态、迭代日志、`child_plans`
  回写；W 列表（含**本 PLAN 反证覆盖到哪、没覆盖到哪**）如实登记。

## 实施清单

- [ ] WP1 **D2 定向与记录一致性**：在 ADR-0031 的 D2 节记录「取自用户 GOAL-010 EC-01 定向」
      （日期 + 授权指认 + 所选形态 + 仍余 D1），并修正 Consequences 里那条**已不再成立**的
      「必被判拒」，使记录不与事实矛盾；**`Status: Proposed` 保持不变**（D1 未决）。
      同一步核对 ADR 结构判据**未被修改且仍绿**（AC-4）。
- [ ] WP2 **adapter 声明化命名**：`adapters/openhands/runtime_adapter.py` 的 `_deliverable`
      改为**按 `spec.task_contract` 的声明**命名交付物（声明源与受控边界见「影响报告」）；
      payload 带来源事实（AC-3）；docstring 与「D2」相关的措辞同步（**不得**留下与行为矛盾的句子）。
- [ ] WP3 **同源判据**：钉住「声明 ⇒ 键名」的绑定与零/多声明的**不猜**边界（AC-1/AC-2），
      并**被压过**（先红后绿）。
- [ ] WP4 **离线链双分支**：`tests/e2e/test_ec03_real_runtime_offline_chain.py` 的交付物裁决
      断言改为**同时**覆盖「声明对齐 ⇒ PASS」与「声明不对齐 ⇒ REJECT」（AC-5）；
      **不在**该用例里放过 REJECT 分支的证据。受影响文档（`docs/integration/LIVE_MODEL_RUNBOOK.md`
      §6 样本段 / `docs/integration/OPENHANDS_ADAPTER.md` / `docs/architecture/AGENT_RUNTIME.md`）
      同步为**事实口径**。
- [ ] WP5 **真实 run**（最小必要次数）：单条命令内联前缀开门跑 live 判据 ⇒ 门 **PASS**、
      终态**恰为 `SUCCEEDED`**（AC-6）；样本（run id / UTC 时间 / 返回 model 名 / 逐条 criterion
      reason）落 RECHECK 与 runbook，**不含凭据值**。失败**也如实落终态**，**不**写成成功。
- [ ] WP6 **本地门禁 + 复检 + 收口**：定向套件 → `make validate-all` 23/23 → 治理绿 →
      独立 RECHECK → GOAL 回写（AC-7/AC-8）。

## 证据

### WP1 — D2 定向（进行中）

待本轮执行后回填：ADR 改动范围、结构判据实跑输出、以及「未修改门禁」的核对方式。

### WP2 — adapter 声明化（进行中）

待本轮执行后回填：改动函数、**函数行数**（50 行门禁）、以及 payload 的来源事实字段。

### WP3–WP6

待本轮执行后回填。

## 影响报告

### D2（事实名 → 合约名的声明权）——本 PLAN 取「声明化 + 门不改」

**用户定向**：GOAL-010 EC-01 给出二选一并要求「受控、声明化、可审计」。
本 PLAN 取 **(ii) 的声明化形态**：交付物键名**不**由 adapter 发明，而由**已在
`AgentSessionSpec.task_contract` 里的合约声明**决定——即 ADR-0031 的 **D2-A**
（「维持字面判定，映射由合约/计划侧声明」；ADR 原文列为**不改 Canonical 语义**的选项）。

**为什么不是 (i)（让模型按结构化 schema 产出）**：真实模型的终端产出是**自由文本**，
让它**恰好**给出合约声明的键名是**概率性**的；判据将无法区分「这一次对了」与「契约被满足」。
(i) 不是不可行，但它把判据的稳定性押在外部模型的服从性上，与「判据必须可重算」冲突。
**代价如实登记**：本 PLAN 因而**没有**验证「模型能否自主产出合约名」这条路径。

**为什么不是 D2-B（验收门支持别名）**：那是 **Canonical 判定语义变更**
（`acceptance.py` 的「artifact 存在」变成「某个别名存在」），属 escalation，**本循环明文不做**。

**「改本 ADR 的状态」这条前置怎么处理**：ADR-0031 的 Consequences 写着「改动它必须先改本 ADR
的状态」，而它的结构判据 `tests/tooling/test_toolpack_capability_policy_pending.py` 钉住
「不得出现 `Status: Accepted`」。**本 PLAN 不改该判据，也不改 ADR 的整体状态。**
依据是 ADR 自己写明的「**可分别决定**」：D1（`tool_pack.*` 能力策略）**仍未决**，
因此该 ADR **整体**仍是 `Proposed`；D2 这一半的定向来自用户，在 D2 节内**如实记录**即可，
ADR 整体状态与结构判据都不需要动——**该判据在 (ii) 形态下原样保持绿**（已核对：
它判的是 `evaluate_criterion` 的**字面匹配**，不是 adapter 的键名；见 WP1 的实跑取证）。

### 受控边界（AC-2 的可判形态）

| 合约声明 | 交付物键名 | 理由 |
| --- | --- | --- |
| **恰一个** artifact 名（`ARTIFACT_EXISTS` / `required_artifacts`） | 该名 | 声明方给出了唯一的可满足目标 |
| **零个** | 事实名 `session_message` | 没有声明就不发明 |
| **多个互不相同** | 事实名 `session_message` | 一条会话消息**不能**诚实地同时充当多个产物 |

「多个」这一格是本 PLAN **最要紧的诚实点**：没有它，只要合约多声明一个 artifact，
adapter 就会**猜**一个名字，把自己变成事实上的声明方。

### 受影响的既有面（必须逐条处理，不得放过）

- **`tests/e2e/test_ec03_real_runtime_offline_chain.py`**：其 `_assert_deliverable_adjudicated`
  **断言链在验收门判拒**。本 PLAN 改动后该断言的前提不再成立 ⇒ **改写成双分支**
  （声明对齐 ⇒ PASS；声明不对齐 ⇒ REJECT）。**这是「产品行为按设计改变、用例前提随之失效」，
  不是「改断言迁就实现」**——判据总数**只增不减**，且 GOAL-009 的 REJECT 证据被**保留**为
  反证分支。**该处置必须在 RECHECK 里被独立核对**。
- **`tests/tooling/test_toolpack_capability_policy_pending.py`**：**不得修改**，且必须仍绿（AC-4）。
  它断言 `session_message` **仍出现在 adapter 源文件里** ⇒ 本 PLAN 必须**保留**该事实名
  （作为**来源事实**继续登记），而不是把它删掉。
- **文档同源面**：`docs/integration/LIVE_MODEL_RUNBOOK.md`（§6 样本段的制品 id 后缀口径）、
  `docs/integration/OPENHANDS_ADAPTER.md`（交付物键名说明）、
  `docs/architecture/AGENT_RUNTIME.md`（「因此 acceptance gate 拒绝」那句）。
  三处都在描述**现状**，改动后必须同步，否则记录与事实矛盾。
- **ADR-0031** 的 D2 节与 Consequences（见上）。

### 失败如何落终态

- 若真实模型/端点导致 run **不能**到达 `SUCCEEDED`，如实归类（端点面 / 协议面 / 装配面）、
  按 fix_policy 纠错；**不得**把 `FAILED` 写成成功、**不得**降低判据。
- 若「声明化」被论证为**不能**受控（例如合约声明与真实产出在语义上无法对齐），
  记 `BLOCKED`（能力边界）并写明为什么。

### 规模与快照类门禁（先自查再跑）

- **50 行函数 / 450 行文件**：`_deliverable` 的改造必须拆函数，不得让单函数越线
  （GOAL-009 cycle 4 的同一条门禁曾抓出 58 行用例函数）。
- **OpenAPI / 设计基线**：本 PLAN **不**改 DTO / 路由 / 前端读面 ⇒ 预期**不触**快照类门禁；
  若实际触到，按既有配方（`UPDATE_OUTLINES` / `verify_linux_outlines`）处置并如实登记。

## 状态历史

- 2026-09-21 derive：由 GOAL-20260921-010 的 EC-01 派生（`parent_goal` 投影 ALL_PLAN）。
  派生时已核对：判拒的机制是**结构化输出键名**（`result_handler.py` 的 `Artifact(id=f"{task.id}:{name}")`
  + `task_phase_helpers.artifact_view` 的裸名索引 + `acceptance.py` 的字面匹配），
  `AgentSessionSpec` **已携带** `task_contract` ⇒ 声明化命名**不需要**新的声明面。
