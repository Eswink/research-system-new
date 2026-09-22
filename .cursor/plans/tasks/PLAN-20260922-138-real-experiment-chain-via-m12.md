---
id: PLAN-20260922-138
slug: real-experiment-chain-via-m12
title: 真实实验执行链：把 m12 参考协议补成可跑通的载体并跑一次真实 run（GOAL-011 EC-03）
status: IN_PROGRESS
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260922-011
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-23 用户 goal 模式拍板：**EC-03 取 (B)**——「为 m12_reference_research_v1 补齐 5 份
    phase 合约并接受约 22 次真实检索出网」。授权原文要点：(1) **(B) 拍板本身**：不为 EC-03 改冻结门
    / 放宽 `classify_risk` / 让 `freeze_manifest` 接受 WARN（(A) 一系全部不取）；
    (2) **真实检索出网**（承 GOAL-011 建档授权）：限 `ncbi_eutils` 的 `network_domains`，
    次数取最小必要；本次为满足 discovery phase **既有**的 `minimum_sources: 10`（**不改该判据**），
    装配方声明**分页检索计划**（`fixed_arguments` 只放量：`retstart`/`retmax`），
    ⇒ 预计每会话 ~10 次、2 个会话共 ~20 次真实出网；(3) **live-gated 真实 LLM**（最小必要，
    单条命令内联前缀 `set -a; . ./.env; set +a` + `RESEARCHOS_AGENT_RUNTIME=openhands`）；
    (4) 凭据纪律不放松（值不落 tracked/DB/记录/日志/回显）；(5) 只推 main、不 force、
    push 前 `git pull --ff-only`。
    **本 PLAN 明文不做**：改任何判据/门禁/快照/验收门使其通过；skip/删除测试、降低断言强度；
    `git add -A`；伪造或夸大验证证据；新增依赖或改上游 pin；把 `RESEARCHOS_AGENT_RUNTIME` 写进 `.env`。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-138 — 真实实验执行链（GOAL-011 EC-03，取 (B)）

## 目标

EC-03：**真实 LLM 驱动一条实验协议（`sort_analysis_v1` 或 `m12_reference_research_v1`）跑到终态**，
且**实验产物 + 证据 + 预算归账**三者在读面上可读；执行体 = **既有** Docker 后端
（`research-os-sandbox:m9-test`，本机镜像已存在）。

`sort_analysis_v1` 一系命中「改门禁才能过」⇒ **本轮不取**。取 **(B)：把
`m12_reference_research_v1` 补成可跑通的载体**。

## 起点事实（derive，只读实测）

- **F-1 m12 的 7 个 phase 里 5 个没有 `task_contract`**（`design` / `analysis` / `peer_review` /
  `deliverable` / `final_audit`）⇒ 运行期 `service._contract_for` 抛
  `ValueError("phase declares no task contract")`。**执行前**就死。
- **F-2 编译器只对「引用了不存在的合约」判红**（`requirements.task_contract_refs`：
  `TASK_CONTRACT_MISSING`），**不**要求每个 phase 都有合约 ⇒ 缺合约的协议能**编译过**、跑不过。
- **F-3 两条 phase 的合约已经就位且带实验声明**：`domain_discovery`（discovery）与
  `m12_experiment_execution`（execution，**pin 了** `script`/`image`/`command`
  ⇒ 装配方**不得**覆盖）⇒ EC-03 要的「既有 Docker 后端」这条路**已经通**。
- **F-4 discovery 的 `EVIDENCE_COVERAGE: minimum_sources: 10` 是**唯一**的硬骨头**：
  `evidence_source_count` 按**任务**计（`result_handler.ResultRegistration`），
  来源 = 非自产 evidence；而运行链**每执行一次声明的调用就登记 1 条**
  （`execute_run_chain_capabilities` 逐条 `evidences.append`，`_operation_key` 只做记账键、
  **不**去重跳过）⇒ **声明 N 次调用 = N 条来源**。
  **结论：10 条来源可由「装配方声明 10 次检索调用」诚实满足**（cycle 6 记的「1 次调用 1 条来源」
  正是指这个乘法关系）。`parallel_agents` 下 discovery 有 **2 个会话** ⇒ 约 **20 次**真实出网。
- **F-5 `QUALITY_GATE` 不阻断运行**：编译只把它记进 `plan.gates`；运行期消费者只有
  `human_gates.py`（只认 `HUMAN_GATE`），`preflight/policy_check.py` 也只对 `HUMAN_GATE`
  设条件 ⇒ m12 的 3 个 `QUALITY_GATE` phase **不会**成为新的死点。
- **F-6 角色与 Agent 全在**：`domain_researcher` / `literature_scout` / `experiment_engineer` /
  `scientific_reviewer` / `research_writer` 都在 `examples/config/roles.yaml`，
  `agents.yaml` 里各有实例（`domain_a` / `scout_a` / `scout_b` / `engineer` / `reviewer_a` /
  `reviewer_b` / `writer`）。
- **F-7 镜像在**：`docker images research-os-sandbox` ⇒ `m9-test` / `m9-sandbox-v1` / `latest` 三枚
  （各 177MB），daemon `29.2.1` 可用。
- **F-8 输出 schema 目录是 `schemas/`**（`*_v1.schema.json`，如既有
  `domain_discovery_output_v1.schema.json` / `experiment_run_output_v1.schema.json` /
  `real_research_deliverable_v1.schema.json`）；合约文件是 `examples/contracts/task_contracts.yaml`。

## 验收条件

- **AC-1 协议可执行**：m12 的 **7 个 phase 全部有可解析的 `task_contract`**；离线编译
  ⇒ **零** `TASK_CONTRACT_MISSING`；运行期不再有 `phase declares no task contract`。
- **AC-2 来源路径诚实且**不改判据**：**discovery 的 `minimum_sources: 10` **一字不改**；
  由**装配方**声明**分页**检索计划（`fixed_arguments` 只放量）使每个 discovery 会话登记
  **≥10 条非自产来源**；离线（MockTransport）实测该 phase 的 gate **判过**、且**零真实出网**。
- **AC-3 实验链真跑**：一次 **真实 LLM** run 跑到终态；`execution` phase 由**既有** Docker 后端执行，
  实验产物（`metrics` 等）+ 证据 + 预算归账在**读面**可读。
- **AC-4 终态如实**：只有 `SUCCEEDED` 记成功；若停在别的终态，**逐字记录**停在哪一条判据/阶段，
  并把 EC-03 如实登记（不粉饰、不改判据凑绿）。
- **AC-5 规模与门禁**：50 行函数 / 450 行文件两道门绿；本机 m0 **23/23**；治理 validate 绿。
- **AC-6 live 记账**：真实出网**逐次**计数（provider 域内）+ 真实 LLM 会话数；跑后环境与 `.env`
  **不留**开关与凭据。

## 计划开始前的定案（写死）

- **D-1 取 (B)，不取 (A)**：任何「放宽 `classify_risk` / 让 `freeze_manifest` 接受 WARN /
  把 `code.execute` 从合约里删掉」的修法都不做——那是改门禁凑成功。
- **D-2 5 份新合约按「phase 的真实意图」写判据**，不写「必然能过」的空判据：
  `design` / `analysis` / `peer_review` / `final_audit` 各自声明**本 phase 的输出物**为
  `ARTIFACT_EXISTS`（名字取自协议里该 phase 的 `outputs:`），`deliverable` 照
  `real_research_deliverable` 的先例**只声明一个产物**（GOAL-010 的命名契约要求唯一）。
  不为「保证成功」而新增任何**新编的**判据类型。
- **D-3 来源数由装配方声明，不由协议伪造**：检索的**内容**（query）来自**声明的输入**；
  分页量（`retstart` / `retmax`）放 `fixed_arguments`（装配方决定的量）。
  协议新增的 `inputs:` 是**诚实的**研究简报声明，不是为凑数的占位。
- **D-4 离线先证、再真实跑**：先在**离线**装配（Fake runtime + MockTransport）上把
  「7 phase 全过 + experiment 真在容器里跑完」证出来，**再**开真实 LLM/真实检索；
  离线阶段**零出网**（`tests/egress_guard.py` 会把关）。
- **D-5 成本上限**：真实检索 ≈ 每 discovery 会话 10 次 × 2 会话；**不**为「多跑几次更稳」重复；
  真实 run 最多 **1 次**（失败就记失败并定位，不做第 2 次重跑除非定位到本 cycle 自伤）。

## 实施清单

- [ ] **WP1** 5 份 phase 合约 + 需要的输出 schema（`schemas/`）+ 相关注册面。
- [ ] **WP2** 协议声明面：discovery 的 `capability_execution: run_chain` + `inputs:` 简报声明；
      组合根/受控装配的种入对齐（按既有结构判据枚举的根逐个对齐）。
- [ ] **WP3** 离线全链证明：Fake runtime + MockTransport + **真实 Docker** 实验 ⇒
      7 phase 全过、实验产物落地、gate 判过 10 条来源、**零出网**。
- [ ] **WP4** 真实 run（最小必要）：live 前缀单条命令；读面取「实验产物 / 证据 / 预算归账」；
      终态如实记录；真实出网逐次计数。
- [ ] **WP5** 记录 + GOAL 回写（EC-03 状态 / 迭代日志 / 台账）。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | 起点事实 F-1…F-8 | 本 PLAN「起点事实」逐条（读代码/配置/镜像） |

## 影响报告

- **Domain / API / schema**：新增合约与 schema（加性）；协议加声明（可能触及既有判据，按按压处置）。
- **CI / workflow**：不改。
- **兼容性 / 迁移**：m12 此前不可执行 ⇒ 无行为回归面；新增 `inputs:` 会影响**跑它的组合根**。
- **安全 / 凭据**：真实检索限 `ncbi_eutils` 声明域内；无新凭据面；不打印凭据值。
- **上游版本影响**：无。
- **下一项任务**：EC-06 收口复检（并把 133/134/135/136/137/138 一并收口）。

## 状态历史

- 2026-09-23：derive（WP0）。拍板 (B)；只读勘察得到 F-1…F-8；未改任何文件、未发起任何出站。
