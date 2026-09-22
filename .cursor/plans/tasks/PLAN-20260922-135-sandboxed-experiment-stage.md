---
id: PLAN-20260922-135
slug: sandboxed-experiment-stage
title: 沙箱实验阶段：把「实验协议的执行阶段」接进既有 Docker 执行后端（GOAL-011 EC-03）
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
    GOAL-20260922-011 cycle 6 = EC-03（真实实验执行链：真实 LLM 驱动一条实验协议跑到终态，
    实验产物 + 证据 + 预算归账可读，执行体 = 既有 Docker 后端）。授权来源：2026-09-22 用户
    goal 模式指令 frontmatter `authorization.ref`——(1) live-gated 真实调用（端点 `ANTHROPIC` +
    `agnes-2.5-flash`，凭据仅在本机 gitignored `.env`，键名 `LLM_MAIN_KEY`）；(2) **允许真实检索出网**——
    仅 NCBI E-utilities（`eutils.ncbi.nlm.nih.gov`），只在该 provider 的 `network_domains` 声明范围内，
    次数取最小必要；(3) 本机 Docker 用于既有实验执行后端（**不新增执行后端、不新增依赖**）；(4) 凭据纪律
    不放松（值不得进任何 tracked 文件/DB/记录/日志/回显；`RESEARCHOS_AGENT_RUNTIME` 只作单条命令内联前缀，
    不得写进 `.env`）；(5) 默认 runtime 保持 Fake、默认 CI 离线；**不得为了跑通而放宽出站判据**
    （`tests/egress_guard.py` 是结构判据），live/docker 类用例必须挂 `requires_live_llm` /
    `requires_docker`（同一放行面）；(6) push-to-main-for-CI（只推 main、不 force、不重写历史）。
    **本 PLAN 明文不做**：改 validator/门禁/快照/测试断言使其通过；skip/删除测试、降低断言强度；
    `git add -A`；伪造或夸大验证证据；**放宽验收门（AcceptanceCriteria）凑成功**；为跑通而放宽出站判据；
    新增依赖或改上游 pin；把真实 runtime 设为默认；把凭据写进 CI；把 `sort_analysis_v1` 的
    M7 参考语义改写掉（那会让 10+ 条已判绿用例的语义消失）。
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260922-135 — 沙箱实验阶段（GOAL-011 EC-03）

## 目标

EC-03 要的是**真实实验执行链**：真实 LLM 驱动一条实验协议跑到**终态**，且
**实验产物 + 证据 + 预算归账**三项从读面取到，执行体 = **既有 Docker 后端**（不新增后端/依赖）。

起点实测（本 PLAN 的 derive 证据，全部只读）：

- **运行编排里「实验阶段」这道缝今天存在，但没有任何装配接线**：
  `PhaseRunnerDeps.experiment_task`（`phase_runner.py:61-64`）默认 `None`，唯一驱动方是
  `tests/integration/test_ig1_phase_runner.py`（Fake 执行后端）。`docs/roadmap/M12_COMPLETION_RECORD.md`
  §12 第 4 条逐字写着同类缺口「预留在 run_orchestration 边界；对账已实现，**接入需 composition root**」。
- **派发判据是字面量**：`phase_runner.py:414` `tctx.contract.id == "experiment_execution"`。
  ⇒ 任何**别的**实验合约（例如 `m12_experiment_execution`）即使语义相同也不会被派发。
- **两份被点名的协议各自不可用**（这是本 PLAN 的**载体定案**依据，逐条可复核）：
  - `m12_reference_research_v1`：**7 个 phase 里 5 个没有 `task_contract`**
    （design / analysis / peer_review / deliverable / final_audit）⇒
    `service._contract_for`（`service.py:389-395`）对空 refs 抛
    `ValueError("phase declares no task contract")` ⇒ **会话解析期就死**；
    其 discovery phase 的 `EVIDENCE_COVERAGE: minimum_sources: 10` 也**没有诚实的 run 路径**
    （该 phase 零声明输入；一次工具调用 1 条来源 ⇒ 至少 11 次真实出网 × `parallel_agents` 的
    2 个会话 = 22 次），且 GOAL cycle 1 迭代日志**已登记**它就是「**已声明但不可执行**」。
  - `sort_analysis_v1`：全 phase 有合约（**测试夹具** `tests/api/run_fixtures.py:54-95` /
    `tests/e2e/scenario_catalog.py:_execution_contract` 注入），⇒ **可被编排器驱动到终态**。
    代价是它的执行阶段今天是**会话**语义（`workspace.read` / `workspace.write.code` / `code.execute`），
    而「执行体 = 既有 Docker 后端」要的是**实验**语义。
- **既有 Docker 后端是 M9 已 E2E 验证的那一个**：`adapters/execution/docker_backend.py` 的
  `DockerExecutionBackend`（M12 DoD #5 逐字「DockerExecutionBackend 6 容器 E2E + ReproducibilityAudit PASS」；
  本机镜像 `research-os-sandbox:m9-test` 实测在册）。**不新增后端、不新增依赖。**

⇒ 本 PLAN 把「实验阶段」做成**声明化**的一等事实，并把**既有** Docker 执行后端接进运行编排：
契约**声明**「我这件工作不是一次会话，而是由沙箱实验后端跑一次实验」⇒ 运行链在**执行阶段**
把它交给实验执行缝（既有 `execute_experiment_task`）⇒ 实验真的在 Docker 里跑 ⇒ 产物/证据/预算
落 canonical ⇒ 三个读面可读。

## 验收条件

- **AC-1 声明化派发**：`TaskContract.experiment`（**可选**，缺省 `None`）声明「本任务由沙箱实验后端执行」；
  缺省 ⇒ **逐字保持会话语义**（既有 run 一行不改）。声明了而装配**没接线** ⇒ **点名拒绝**
  （fail-closed，**不**静默回退到会话）。`experiment_execution`（目录合约）声明同一份 spec ⇒
  既有派发行为**逐字保持**（今天按 id 派发的那条路径语义不变）。
- **AC-2 执行体是既有 Docker 后端**：装配面把 `DockerExecutionBackend` 接进实验缝；
  实验容器真的起、镜像 digest 进执行事实；**不新增执行后端、不新增依赖**。
- **AC-3 三项读面齐备 + 终态如实**：一次真实 LLM 驱动的 run 到**终态**；
  `GET /runs/{id}/experiments`（实验产物 + metrics）· `GET /runs/{id}/evidence`（证据）·
  预算归账读面可读。**只有 `SUCCEEDED` 是成功**；`FAILED` 如实登记、**不得**写成成功。
- **AC-4 门禁与出站判据不放松**：`sort_analysis_v1.yaml` **一行不改**；既有合约的
  `acceptance_criteria` 一行不改（`EVIDENCE_COVERAGE` 仍由声明输入满足）；`tests/egress_guard.py`
  一行不改；默认门离线；live/docker 用例挂 `requires_live_llm` / `requires_docker`。
- **AC-5 规模门禁**：50 行函数 / 450 行文件两道门绿。**贴线文件零增长**：
  `services/api/composition.py`（450）、`phase_runner.py`（450）、`service.py`（450）
  本 PLAN 只做**净减**或零行改动（派发分支换成对 helper 的一次调用 ⇒ 净减）。

## 计划开始前的定案（写死，执行中不得回退）

- **D-1 载体 = `sort_analysis_v1`**（两份点名协议里唯一可被编排器驱动到终态的）。
  `m12_reference_research_v1` **不做载体**：5 个 phase 缺合约 ⇒ 会话解析期 `ValueError`；
  补齐合约属**新写 5 份合约**，且其 discovery phase 的 `min 10` 覆盖门无诚实路径（见上）。
  **本 PLAN 不修改这两份协议文件的任何字节**。
- **D-2 声明落在「合约」而不是「协议」**：`sort_analysis_v1.yaml` 的 M7 参考语义被 10+ 条
  已判绿用例（`tests/e2e/scenario*.py` 全套）按会话语义驱动 ⇒ **改协议 = 那批用例的语义消失**。
  声明放合约层 ⇒ 协议零改动，M7 套件零影响。
- **D-3 声明由 run-ready/live 装配发出**（`tests/e2e/live_run_support.py` + `tests/api/run_fixtures.py`
  的 run-ready 装配）——这与 GOAL-009/010/011 **全部真实 run** 走过的同一条路径
  （测试/运维**显式声明**的执行上下文；生产组合根不接这一环的做法由 W-C 同源登记）。
- **D-4 派发判据 = `contract.experiment is not None`**（不是 id 比较）。`experiment_execution`
  目录合约补同一份声明 ⇒ 既有 id 派发路径的行为**逐字保持**。
- **D-5 实验脚本**：`examples/experiments/sort_analysis_baseline.py`——纯标准库、确定性、
  在容器内产出 `analysis_report.json`（对齐合约 `ARTIFACT_EXISTS(analysis_report)`）。
  镜像用**既有** `research-os-sandbox:m9-test`。

## 实施清单

- [ ] **WP1** 声明面：`ExperimentExecutionSpec`（Domain）+ `TaskContract.experiment` +
  `schemas/task-contract.schema.json` + `adapters/contracts/tasks_loaders.py` +
  `adapters/sqlite/serialization.py` 往返 + `examples/contracts/task_contracts.yaml`
  给 `experiment_execution` 补声明（既有行为逐字保持）。
- [ ] **WP2** 派发：`phase_runner` 换成 `contract.experiment is not None` → helper
  （净减行）；helper `dispatch_experiment` 落在 `experiment_task.py`（声明了但没接线 ⇒ 点名拒绝）。
- [ ] **WP3** 装配：`services/api/experiment_support.py`（`ExperimentTaskDeps` + governed executor +
  `DockerExecutionBackend` + request/provenance builder + 计划预注册）；run-ready/live 装配接线。
- [ ] **WP4** 实验脚本 `examples/experiments/sort_analysis_baseline.py`。
- [ ] **WP5** 判据：离线（默认门：编排器 + Fake 执行后端走真缝 ⇒ 终态 + 三项读面）+ 按压
  （摘声明 ⇒ 不派发 ⇒ 红）；live/docker（真实 LLM + 真实 Docker + 三个读面 + 终态如实）。
- [ ] **WP6** 文档同源 + GOAL 回写（EC-03 状态、迭代日志、child_plans、CI 台账）。

## 证据

| # | 事实 | 取数方式 |
| --- | --- | --- |
| E-1 | `experiment_task` 缝存在、默认 `None`、零装配接线 | `phase_runner.py:61-64`；`rg -n "experiment_task\|ExperimentTaskDeps" services/` ⇒ 零命中；驱动方只有 `tests/integration/test_ig1_phase_runner.py` |
| E-2 | 派发判据是字面量 id | `phase_runner.py:414` |
| E-3 | `m12_reference_research_v1` 不可执行 | 5 个 phase 无 `task_contract`（`rg -n "task_contract:" examples/protocols/m12_reference_research_v1.yaml` 只 2 条）+ `service.py:389-395` 对空 refs 抛 `ValueError` |
| E-4 | `sort_analysis_v1` 的合约来自夹具 | `examples/contracts/task_contracts.yaml` 里**没有** `sort_analysis_execution`；`tests/api/run_fixtures.py:54-95` 注入 |
| E-5 | Docker 后端是既有的、已 E2E 验证的 | `docs/roadmap/M12_COMPLETION_RECORD.md` DoD #5；本机 `docker images` 有 `research-os-sandbox:m9-test` |
| E-6 | 三个读面已存在 | `routers/experiments.py:98`（`/runs/{id}/experiments`）· `routers/inspection.py`（`/runs/{id}/evidence`）· `routers/budget_forecast.py:65`（`/runs/{id}/cost-forecast`） |
| E-7 | 贴线文件行数 | `wc -l` composition.py / phase_runner.py / service.py 三个 450 |

## 影响报告

- **Domain**：`TaskContract` 加**可选**字段 `experiment`（缺省 `None`）⇒ 属性签名加性变化；
  不触及 Canonical State 边界（合约是**目录配置**，随 manifest 冻结的是它的取值；
  本次只有新声明的合约其冻结取值变化）。
- **API / schema**：`schemas/task-contract.schema.json` 加可选属性；OpenAPI 快照**不涉及**
  （合约不走 HTTP DTO）。
- **兼容性 / 迁移**：零迁移。存量合约不带声明 ⇒ 取值 `None` ⇒ 行为逐字不变；
  协议文件、既有 `acceptance_criteria`、出站判据、默认门**一行不改**。
- **安全 / 凭据**：无新增凭据面；实验容器沿用既有边界（network none / 非 privileged /
  capability 全 drop / 只 bind-mount 工作区）。不出网。
- **上游版本影响**：无（不新增依赖、不改 pin）。
- **下一项任务**：EC-04（用户视角端到端 + `partial` 页诚实核对）。

## 状态历史

- 2026-09-22：derive（WP0）。只读勘察 F 面；定案 D-1…D-5；未改产品代码、未发起任何真实调用。
