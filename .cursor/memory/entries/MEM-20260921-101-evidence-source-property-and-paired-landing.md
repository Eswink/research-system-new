---
id: MEM-20260921-101
title: "证据覆盖的判别性质必须落在编排边界、按集合成员判定；且「收紧口径」与「接上真实来源」必须同一提交成对落地"
status: ACTIVE
created_at: 2026-09-21
updated_at: 2026-09-21
scope: repository
confidence: 0.9
review_after: 2027-09-21
source_plans:
  - .cursor/plans/tasks/PLAN-20260921-128-evidence-chain-truthfulness.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260921-128-evidence-chain-truthfulness.md
supersedes: []
tags:
  - evidence
  - acceptance-gate
  - run-orchestration
  - goal-010
---

# 证据来源的判别性质与成对落地（GOAL-010 EC-02 实测）

## 做了什么

`EVIDENCE_COVERAGE` 原本数的是 `len(evidence)`，而 evidence 全部派生自**同一次会话输出**
（`trust_label=GENERATED`）⇒ **交付物就是它自己的「来源」**，`≥ 1` 恒成立。EC-02 把它改成
**「一条 source 计入覆盖，当且仅当它的对象不是本任务自己产出的 artifact」**，并给 run 链接上
**契约声明的输入制品**（组合根以真文件字节种入、内容寻址、digest 可重算、`USER_PROVIDED`）。

## 为什么这样做

- **判别性质落点**：验收门（`packages/domain/acceptance.py`）只吃一个整数
  （`minimum_sources` vs `evidence_source_count`），「什么算来源」的判据**不在**门里、
  也不在 Domain。要在**编排**层（喂数的那一侧）动手，否则会在门里造出一个与 Domain 无关、
  又必须随生产者变化而改的语义；落在编排层还意味着**不触 Canonical State 边界**。
- **判定形态选集合成员，不选 id 名前缀**：自述来源恒为 `{task_id}:{name}`、工具结果是
  `tool-result:…`、声明输入由组合根以独立 id 种入。前缀启发式会随生产者变化失效；
  `artifact_id ∉ self_artifact_ids` 对新增生产者稳健，且**构造性地**排除了模型自述
  ——自述必然是它自己的产物，这不是约定，是必然。
- **成对落地是硬约束，不是风格**：只收紧不接来源 = 把所有 min-1 合约（含刚达成的
  `SUCCEEDED`）打回 `REJECT`；只接来源不收紧 = 判据没变。两者必须在**同一提交**里落地，
  否则是拿一个 EC 换另一个 EC。

## 怎么做与复现

- **声明面**：用**既有**的 `ProtocolPhase.inputs`（此前有 schema、无消费者）声明该 phase 要读的
  输入制品；编译器把它透传进 `CompiledPhase.inputs`。
- **供应面**：组合根把声明名解析到**真实对象**（内容寻址、`created_by=composition-root`、
  `mark(VERIFIED)`）；解析不到**不得**伪填充，按 fail-closed 处理。
- **登记面**：`register_declared_input_sources` 造 `SourceRecord(trust_label=USER_PROVIDED)` +
  一条 `Evidence`（`artifact_id` = **输入制品** id），并挂 `SUPPORTS` relation。
- **计数面**：`ResultRegistration.evidence_source_count` = `artifact_id ∉ self_artifact_ids`。
- **成对的取证（先红后绿，三次压制）**：去协议声明 ⇒ 红；去种入 ⇒ 红；撤收紧 ⇒ 红；
  每次复原后 `git diff` 只剩意图内改动。
- **共享声明会同时作用于所有组合根**：给一份**共享**协议加 `inputs:`，等于给**每一个**跑它的
  装配点加了「必须有那份输入」的义务。本 cycle 因此漏掉 **PG 组合根**
  （`build_postgres_assembly`），全量 m0 里 `test_m13_pg_run_e2e` 的 run 直接 `FAILED`
  （`manifest_digest: null`，死在执行前）。**修法是结构判据，不是补丁**：判据**从文件本身推出**
  「控制面组合根」集合（`services/api/` 顶层里既造 `ArtifactStore(` 又接 `artifacts=` 的模块），
  要求每个都种入并断言集合恰为已知的两者 ⇒ 新增根会**变红**，逼加它的人当场决定。
  同理，`seed_declared_inputs` 只有 `put`+`mark` **合起来**可重入（`put` 把行重置为 `STAGED`，
  `mark` 才做 `STAGED → VERIFIED`），所以它能在持久库上重复调用。
- **改 DTO 要看所有消费者**：同一轮 m0 还抓出前端单测夹具没跟上 `EvidenceDto` 的三个新字段
  （`typescript/typecheck` 红）。**定向套件全绿不等于没有回归**——两条都是全量 m0 抓出来的。

## 适用边界

- **只证明 grounding，不证明「读过」**：声明输入证明的是「交付物与它被供应的输入之间有
  **可核验的 grounding 关系**」（digest 可重算、可指认），**不**证明任务**真的读了**它——
  后者只有工具观测（`register_tool_evidence`）能证。**不得**把前者写成后者。
- **读面缺字段会让判据根本无法满足**：加字段之前 `SourceRecord` 在 `services/` 里**零命中**，
  即 EC 的判据用语「其 `origin`/`trust_label` 可取」当时**无路可走**；本次给 `EvidenceDto`
  补了 `source_origin` / `source_trust_label` / `source_access_time`（取不到为 `null`，不伪填充）。
- **读面只经 claim relations 走**：`GET /runs/{id}/evidence` 的投影只经 claim relations，
  所以声明输入的 evidence 必须 `attach_relation(SUPPORTS)` 才可读，且要并进**同一** Claim 的
  relations 才不破坏「`claim.evidence_relations` == 已挂 relations」这条不变量。
  此处 `SUPPORTS` 的语义是 **grounding**，不是「输入证明了结论」——属**语义借用**。
- **缺省退路偏松**：`ResultRegistration` 若**不传** `self_artifact_ids`（缺省空集），计数会退化成
  旧口径。生产两条路径都传了，但第三方构造时漏传会得到一个偏松的数——登记为已知薄弱面。
- **`minimum_sources: 10`（`domain_discovery`）至今没有 run 路径行使过**（既未满足也未违反）
  ⇒ 它既不是达成的证据，也不是失败的证据，是**未覆盖面**。
- **拒绝发生的位置**：实测落在**登记期** fail-closed，而不是 preflight 拒绝；实质相同
  （不伪填充、不进 RUNNING、run 落 `FAILED`），差别是**诊断更晚也更钝**。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260921-128-evidence-chain-truthfulness.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260921-128-evidence-chain-truthfulness.md`（PASS_WITH_WARNINGS）
- 目标：`.cursor/plans/goals/GOAL-20260921-010-real-deliverable-contract.md`（EC-02）
- 代码：`packages/application/run_orchestration/result_handler.py`、
  `packages/application/run_orchestration/task_phase_helpers.py`、
  `services/api/demo.py`、`services/api/composition.py`、`services/api/pg_composition.py`、
  `services/api/routers/inspection.py`
- 判据：`tests/architecture/python/test_declared_input_sources.py`、
  `tests/application/evidence/test_provenance.py`、`tests/e2e/test_evidence_chain_source_live.py`
- 前置：`MEM-20260921-100`（交付物键名与验收门；EC-01）
