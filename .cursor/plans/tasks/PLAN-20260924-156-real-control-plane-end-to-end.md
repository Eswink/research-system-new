---
id: PLAN-20260924-156
slug: real-control-plane-end-to-end
title: 真实控制面端到端：产品组合根 + 真适配器跑到 SUCCEEDED，实验半被验收门阻断（GOAL-014 EC-02）
status: BLOCKED
created_at: 2026-09-24
updated_at: 2026-09-24
parent_goal: GOAL-20260924-014
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260924-014 建档授权（2026-09-24 用户 goal 模式指令）的 **EC-02**：
    「**真实控制面端到端**：**不带任何 `preflight_override`** 跑一次真实 run
    （真实 LLM + 真实检索 + 真实实验）到终态 `SUCCEEDED`，三项读面齐备」。
    授权面承 EC-01（`evidence.read` 的 allow + 镜像同步，**已由 cycle 1 落地**），
    另有：live-gated 真实调用（端点 `agnes-anthropic` / `main`，凭据仅在本机
    gitignored `.env`，键名 `LLM_MAIN_KEY`）；真实检索出网仅 NCBI E-utilities
    （`eutils.ncbi.nlm.nih.gov`，在该 provider 声明的 `network_domains` 内，次数取最小必要）；
    本机 Docker 用于既有实验执行后端；凭据纪律不放松（值不得进任何 tracked 文件 / DB /
    记录 / 日志 / 回显；`RESEARCHOS_AGENT_RUNTIME` 只作单条命令内联前缀，不得写进 `.env`）；
    默认 runtime 保持 Fake、默认 CI 离线；push-to-main-for-CI（只推 main、不 force）。
    **本 PLAN 明文不做**：改 validator / 门禁 / 快照 / 测试断言使其通过；skip/删除测试或
    降低断言强度；`git add -A`；伪造或夸大验证证据；**放宽验收门（AcceptanceCriteria）凑成功**；
    为跑通而放宽出站判据；**在授权范围外放宽任何策略面**；改 `test_m2_audit.py` 的镜像一致性判据。
    **本 PLAN 的结论是一条如实阻断**：EC-02 的判据本体（带真实实验到 `SUCCEEDED`）在今天
    的产品路径上**不可达**，阻断点落在用户已登记的拍板项上（见「阻断」节与 GOAL 的 `F-10`/
    `F-11`）。**未实跑不得记 PASS** ⇒ 本 PLAN 置 `BLOCKED`，**不**为凑绿新造判据更弱的合约。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260924-158-real-control-plane-end-to-end.md
memory_entries:
  - .cursor/memory/entries/MEM-20260924-125-seam-empty-is-not-assembly-missing.md
---

# PLAN-20260924-156 — 真实控制面端到端（GOAL-014 EC-02）

## 目标

让 `real_retrieval_research_v1` 经**产品组合根 + 既有 API**（`preflight_override = None`）
跑到终态，并如实判定 EC-02 的**实验半**能否在今天的产品路径上达成。

## 计划开始前的定案（写死）

- **D-1｜「真实控制面」的判据是结构性的**：`execution_inputs()` 的第二分岔
  （`deps.preflight_override is None ⇒ _live_preflight`）。判据**必须**走产品入口，
  **不得**手工拼 `PreflightContext`。
- **D-2｜只注入执行体，绝不注入判词**（本 PLAN 的纪律边界）：允许把 provider **实例**
  （`ApiDeps.tool_providers`）与运行链能力步装配（`CapabilityDeps`）交给装配方；
  **不得**注入 `provider_health` / `endpoint_health` / `policy_evaluator` /
  任何 `PreflightContext` 字段——那些是判词。这一条把「补装配」与「换控制面」分开。
- **D-3｜工具证据的单一来源**：`NcbiEutilsProvider` 必须用**运行链同一个** artifact store
  （产品根里 `deps.artifacts` 与编排侧是同一实例），`spill_threshold_bytes=1`（既有口径）。
- **D-4｜协议来源**：走**既有出厂协议**（`real_retrieval_research_v1.yaml`），
  **不**新造出厂声明、**不**改任何契约断言。

## 验收条件

- [x] **AC-1**：判据在册且离线**零出网**：`tests/e2e/test_real_control_plane_retrieval_live.py`
      （`requires_live_llm` + live 门 skip；离线实跑 `1 skipped`、`judged 0`）。
- [x] **AC-2**：控制面确为产品自己的：`override is None`、求值器为
      `NativePolicyEvaluator`、policy 版本取自 `examples/config/policy.yaml`（`0.4.0`）、
      `ncbi_eutils` 健康=**HEALTHY**（真适配器真探测）、adapter 为 `NcbiEutilsProvider`。
- [x] **AC-3**：真实 run 到终态 **`SUCCEEDED`**、manifest 冻结、无失败事件；
      证据面 ≥1 条 `source_trust_label = RETRIEVED`（真 PMID，`tool_refs` 非空）；
      预算面有归账条目。
- [x] **AC-4**：成对反证（两条，均**免费**——止于冻结前）：撤 `evidence.read` 的 allow ⇒
      产品路径 `sort_analysis_v1` **FAILED**、零 task / 零实验 / 零证据；撤 `literature.*`
      的 allow ⇒ `real_retrieval_research_v1` 同样冻结前终止。按压后**逐字节还原**
      （`git diff --stat` 为空）。
- [ ] **AC-5（判据本体，未达成）**：带**真实实验**跑到 `SUCCEEDED` + 实验读面齐备。
      **阻断**（三条实测，见下）⇒ 本 AC 置未达成，PLAN 置 `BLOCKED`。
- [x] **AC-6**：阻断机制**逐条可复跑**并落 `scratch/`（控制面矩阵、验收门探针、两条按压）。

## 实施清单

- [x] **WP1｜控制面矩阵测量**：产品组合根（无 override）跑三条协议的 preflight + 冻结判定，
      对照「注册真适配器 / 不注册」两种装配（`scratch/goal014_c2_probe.py`）。
- [x] **WP2｜live 判据**：新增 `tests/e2e/live_control_plane_support.py`（装配支持，只给执行体）
      + `tests/e2e/test_real_control_plane_retrieval_live.py`（判据本体）。
- [x] **WP3｜真实 run**：一次真实 run（1 phase、1 次真实 LLM 会话、2 次真实 NCBI 调用）⇒
      样张逐字落 `scratch/`。
- [x] **WP4｜成对反证**：两条按压 + 逐字节还原。
- [x] **WP5｜验收门探针**：把「实验跑成功时产品路径能给出的事实」直接喂给既有求值器
      （`scratch/goal014_c2_acceptance_probe.py`）。
- [x] **WP6｜RECHECK + 登记**：RECHECK-158、本 PLAN 置 `BLOCKED`、GOAL 回写（`F-10`/`F-11`）。

## 证据

- **控制面矩阵**（`scratch/goal014-c2-real-control-plane-probe.txt`）：产品组合根、
  `preflight_override = None`。`sort_analysis_v1` ⇒ `WARN` + **可冻结**（走 GOAL-012 的
  显式策略通道，4 条留痕）；`real_retrieval_research_v1` / `m12_reference_research_v1`
  **不注册适配器** ⇒ `WARN`（`TOOL_HEALTH_UNPROVEN` ×2）+ **拒冻**（该警示无接受通道）；
  **注册真适配器** ⇒ 两条都 **`PASS` + 可冻结**。
- **真实 run 样张**（`scratch/goal014-c2-real-plane-sample.json`）：`state = SUCCEEDED`、
  `manifest_digest = sha256:6e0804dc…`、`failures = []`、`plane = {override: null,
  evaluator: NativePolicyEvaluator, policy_version: 0.4.0, provider_health:
  {ncbi_eutils: HEALTHY}, adapter: NcbiEutilsProvider}`、证据面 4 条（其中 **2 条
  `RETRIEVED`**：`tool:literature_search:…` / `tool:literature_read:…42778281+42778201+42777851`，
  `tool_refs = [ncbi_eutils, literature_*]`）、预算面 1 条（`AGENT_TURNS` / `quantity 1` /
  `cost_status UNKNOWN`）、`experiments = []`。
- **按压**：`scratch/goal014-c2-press-allow-withdrawn.txt`（撤 `evidence.read` ⇒
  `FAILED` / `manifest_digest: null` / `POLICY_DENIED, TOOL_RISK_ELEVATED` / `tasks: []` /
  `experiments: []` / `evidence: []`）、`scratch/goal014-c2-press-literature-withdrawn.txt`
  （撤 `literature.*` ⇒ 同形，`POLICY_DENIED`）。两处还原后 `git diff --stat` **为空**。
- **验收门探针**（`scratch/goal014-c2-acceptance-probe.txt`）：实验**跑成功**、制品齐备
  （`metrics` 在场 ⇒ `ARTIFACT_EXISTS` **OK**）时，两份声明了 `experiment` 的出厂合约
  （`experiment_execution` / `m12_experiment_execution`）仍判 **`passed=False`**：
  `TEST_PASSES → "no test results provided"`、`POLICY_COMPLIANT → "policy decision unknown"`。

## 阻断（EC-02 的判据本体为什么不可达）

- **M-1｜执行体缝出厂组合根不接**：`ApiDeps.tool_providers` 生产为空（既有注释写死
  「生产未注册时空 dict」）、`OrchestrationDependencies.capabilities` 与 `.experiment_task`
  缺省 `None` ⇒ 产品路径**自己**执行不了检索与实验（本 PLAN 由装配方补上，见 D-2）。
- **M-2｜没有出厂的「检索 + 已 pin 实验」配对声明**：`real_retrieval_research_v1` 只有检索
  （无实验阶段）；`m12_reference_research_v1` 的检索**不是** `run_chain`（是会话工具，
  而生产装配的 provider→SDK 工具映射是空操作）。配对需要**新增出厂声明**。
- **M-3｜验收门缺 `tests` / `policy_decision` 两维（决定性）**：见上「验收门探针」。
  这一条**正是** GOAL-011 登记的下一轮拍板项 ①②③（`SCHEMA_VALID` / `TEST_PASSES` /
  `POLICY_COMPLIANT` 接线）⇒ 触及「不进入循环 / 需人工拍板」。

## 状态历史

- 2026-09-24：derive + 执行（GOAL-014 cycle 2）。开工先把「产品组合根 + 无 override」的
  控制面矩阵测出来（WP1）：真实控制面对检索类协议在**注册真适配器后**即 `PASS` + 可冻结，
  这一半是**可达的**；随后落 live 判据（WP2/WP3）实跑得 `SUCCEEDED`。实验半按 WP5 探针
  判为**不可达**（M-3），另两条缝（M-1/M-2）如实登记。**未改任何门禁 / 合约 / 策略面**；
  真实调用 1 次会话 + 2 次检索，全部按最小必要。

## 影响报告

- **改动面**：判据面（新增 2 个文件：装配支持 + live 判据），**零产品代码改动**、
  **零策略面改动**（按压已逐字节还原）、零合约/快照改动。
- **Domain/API/schema 变化**：无。
- **安全/凭据变化**：无。凭据值未进入任何 tracked 文件 / 记录 / 日志；真实出网仅
  端点探测 + NCBI E-utilities（在 provider 声明的 `network_domains` 内）。
- **兼容性/迁移风险**：新增判据挂 `requires_live_llm`（默认门 skip），不影响默认门离线性质。
- **上游版本影响**：无（不新增依赖、不改 pin）。
- **下一项任务**：EC-02 待用户拍板（`F-11` 的三个接线项 + `F-10` 的组合根接线）；
  本循环转 EC-03（策略面双向差集审计，**完全在授权内、离线**）。
