---
id: MEM-20260930-177
title: "`RunOutcome.handoff_digests` 装的其实是 task id（`tuple(sorted(handoffs))` 排的是字典键）—— 零消费者让错名活了很久；EVIDENCE_COVERAGE 只数本任务可见的来源 ⇒ 评审 phase 必须自带声明输入，且不得声明 minimum_retrieved_sources"
status: ACTIVE
created_at: 2026-09-30
updated_at: 2026-09-30
scope: repository
confidence: 0.90
review_after: 2027-03-30
source_plans:
  - .cursor/plans/tasks/PLAN-20260930-261-goal-027-ec04-multi-role-research-subiteration.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260930-262-goal-027-ec04-multi-role-research-subiteration.md
supersedes: []
tags: [run-outcome, handoff-bundle, naming-defect, evidence-coverage, review-phase, goal-027, ec-04]
---

## 做了什么

把一次 run 做成**多 role 科研子迭代**（3 个会话 phase × 3 个不同 role + 1 个合约声明的
沙箱实验 phase），并在过程中修掉一处**真缺陷**。四条**实测**得到的事实：

- **字段名可以撒谎很久**：`RunOutcome.handoff_digests` 在 `phase_runner` 里填的是
  `tuple(sorted(handoffs))` —— `handoffs` 是 `dict[task_id, HandoffBundle]`，
  `sorted(dict)` 排的是**键** ⇒ 该字段装的是**任务 id**（实测三条 UUID
  `21c79561-54a7-4399-81bf-f03715fa3193` 型）。`rg handoff_digests` 全仓**零消费者**
  （只有定义与本次新判据）⇒ 错名从未被暴露，直到 EC-04 要求「HandoffBundle 的 digest 序列」
  可取证。修法：新增纯函数 `outcomes.handoff_digests(handoffs)`（取 `bundle.digest`、
  确定性排序、缺属性跳过不伪造）+ 两处调用点替换；函数落 `outcomes.py` 让
  `phase_runner.py` 保持 **449 ≤ 450** 行。
- **`EVIDENCE_COVERAGE` 只数「本任务可见的非自产来源」**（`registration.evidence_source_count`）：
  上游 phase 的产物是**另一个任务**的自产面，不进本任务计数 ⇒ **评审 phase 若想「有东西可判」，
  必须自己声明输入**（`inputs: [input-brief:...]`）。不给声明输入，评审的判据恒判
  `0 < 1 sources`（本条实测：`acceptance gate rejected: EVIDENCE_COVERAGE: 0 < 1 sources`）。
- **`minimum_retrieved_sources` 是「本任务自己系统取得的来源」**：只有做了检索的 phase
  （侦察）能声明它；让评审 phase 声明它 = 要求评审者为自己**没做**的事背书
  ⇒ 本 EC **不这么写**，并把这条边界写进契约注释（这是**如实边界**而非遗漏）。
- **会话工具列表 = 冻结集 − 本 phase 的 run-chain provider**：某 phase 若**不**在
  `required_capabilities` 里覆盖某个 provider，它就会落进**该 phase**的会话工具列表；
  生产装配今天没有 provider→SDK 映射 ⇒ 会话创建**点名失败**
  （`ToolDefinition 'europe_pmc' is not registered`，实测）。⇒ 每个 phase 的声明面要
  把冻结集**全覆盖**（本协议用 `workspace.read` / `evidence.read` / `literature.*` 做到）。

## 为什么这样做

- **命名不是文档，是接口**：`handoff_digests` 的错名之所以无害，纯粹因为它没有消费者；
  本 EC 一旦要取证就立刻现形。⇒ 新增字段时，「谁读它」应当先于「它叫什么」确定；
  反之，**给未被读取的字段改名/修正语义是低风险窗口**（本条即在此窗口内完成，
  零消费者 ⇒ 零迁移、零破坏面）。
- **判据要按**本任务**的可见面写**：评审「真判定」的机制不是「读到上游的东西」，
  而是「**自己声明的依据**在场/缺席 ⇒ 判过/判负」。把这两件事混起来会写出
  「评审其实什么也没判，只是复述上游计数」的假判据。
- **两段执行体缝由装配方补**（运行链检索 / 合约声明的沙箱实验）：产品组合根今天不自己接
  （`F-10` 同族缺口）⇒ 判据用 `with_capabilities` / `with_contract_declared_experiment`
  补上，**不改产品代码**（装配方补执行体是本仓认下的处置）。

## 怎么做与复现

1. 跑本 EC 判据（需 Linux 可用 Docker daemon；非 Linux 下如实 skip）：
   `uv run --frozen --no-sync python -B -m pytest tests/e2e/test_multi_role_research_offline.py -q`
   ⇒ 6 passed。
2. 看修复：`packages/application/run_orchestration/outcomes.py::handoff_digests`；
   按压配方 = 把它改回 `tuple(sorted(handoffs))`（P-I，判据转红）、
   或摘掉评审 phase 的 `inputs` 声明（P-K，判据转红）。
3. 读面分工：会话任务在 `GET /runs/{id}/tasks`（**实验任务不在其中**），
   实验任务在 `GET /runs/{id}/experiments`。

## 适用边界

- 本 EC 的实跑用 run-ready 夹具（`preflight_override` + 装配方补的执行体缝）
  ⇒ 证明的是**链路与判据**，不是「真实控制面」。
- 生产装配缺 provider→SDK 映射（既有缺口）⇒ 本协议在默认装配下会话 phase 会点名失败；
  判据用测试侧 `map_tools=True` 补上（与 `sort_analysis_v1` 既有判据同一手法）。
- 本 EC 未重测策略 `DENY` 面（`FakePolicyEvaluator` 默认 ALLOW）。
- **不得**据此宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 来源

- `PLAN-20260930-261`（GOAL-027 EC-04）与 `RECHECK-20260930-262`（§3 / §4 / §7）；
- 判据与支持件：`tests/e2e/test_multi_role_research_offline.py`、
  `tests/e2e/literature_chain_support.py`（`OutcomeRecorder`）；
- 协议与契约：`examples/protocols/multi_role_research_v1.yaml`、
  `examples/contracts/task_contracts.yaml`（`multi_role_scouting` / `multi_role_review`）；
- 相关代码：`packages/application/run_orchestration/phase_runner.py`（`handoffs` 累积）、
  `packages/application/run_orchestration/outcomes.py`（`handoff_digests`）、
  `packages/domain/acceptance.py::_evaluate_evidence_coverage`、
  `packages/application/run_orchestration/result_handler.py`（`register_session_result`）；
- 同族记忆：[[evidence-read-face-claim-relation]]（读面经 claim relation 投影）、
  [[retrieved-source-and-coverage-nature]]（覆盖两维）、
  [[run-chain-declaration-is-the-only-deterministic-retrieval-door]]（EC-03 的链面前置）。
