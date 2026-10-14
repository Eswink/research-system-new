---
id: MEM-20261014-220
title: "「谁执行这件工作」是一条契约声明，不是合约 id 的字面量：加第三条执行体时，派发分支、装配关键字、以及『两个声明同时在场』都要有一处点名拒绝"
status: ACTIVE
created_at: 2026-10-14
updated_at: 2026-10-14
scope: repository
confidence: 0.9
review_after: 2027-04-14
source_plans:
  - .cursor/plans/tasks/PLAN-20261014-466-goal-077-ec02-03-report-on-the-product-path.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261014-467-goal-077-ec02-03-report-on-the-product-path.md
supersedes: []
tags: [run-orchestration, task-contract, dispatch, seam, size-gate, research-report]
---

## 做了什么

把**报告汇编**接成 run 编排的**第三条执行体**（前两条：会话 = 缺省、沙箱实验 =
`TaskContract.experiment`）。做法与实验那条**同形同层**：

1. **域声明**：`TaskContract.report: ReportAssemblySpec | None`（新类型，**刻意没有输入字段**
   —— 报告的输入是本 run 已落库的事实，装配方无从在契约里写死）；
2. **互斥**：`experiment` 与 `report` 同时在场 ⇒ `__post_init__` **点名拒绝**
   （「which body executes this work would be undecidable」）；
3. **派发**：`task_dispatch.dispatch_task_execution` 按**声明**分流，
   缺装配 ⇒ `dispatch_report` **点名拒绝**（fail-closed，**不**静默回退到会话）；
4. **装配面**：`OrchestrationDependencies.report_task` + `services/api/report_support.py`
   （与 `experiment_support.py` 同形）。

## 为什么这样做

**为什么是「声明」而不是「按合约 id 分派」**：写死一个合约名会漏掉语义相同的别的合约，
而且「声明了报告」与「真的汇编了」会分叉（run 显示成功而报告根本没被汇编）——
这条纪律在 GOAL-011 EC-03（实验那一条）就已立起，本处只是第三条实例。

**为什么新类型而不是复用 `ExperimentExecutionSpec`**：那个类型的字段名（`script` /
`image` / `command`）说的是**沙箱实验**；拿它声明「汇编一份报告」是语义错配，
读者会以为跑了容器。**空声明 `{}` 本身**才是完整信息。

**为什么互斥要落在域而不是派发点**：派发点的顺序会**看起来像**优先级，而两个声明
同时在场时**没有任何**可辩护的优先序（挑错方向 ⇒ run 成功而工作没做）。域构造期
拒绝是最早的可能点。

## 怎么做与复现

```bash
# 主干 + 两条反证（摘检索接线 / 摘汇编器缝 ⇒ 各自点名，终态相反）
uv run --frozen --no-sync python -B -m pytest \
  tests/e2e/test_research_report_arc_offline.py -q      # 7 passed

# 互斥（构造期点名拒绝）
uv run --frozen --no-sync python -B -c "
from packages.domain.tasks import TaskContract, ReportAssemblySpec, ExperimentExecutionSpec
from packages.domain.enums import AcceptanceCriterionType
from packages.domain.tasks import AcceptanceCriterion
TaskContract(id='x', version='1', purpose='p',
  acceptance_criteria=[AcceptanceCriterion(type=AcceptanceCriterionType.ARTIFACT_EXISTS)],
  report=ReportAssemblySpec(), experiment=ExperimentExecutionSpec())"
# ⇒ ValueError: ... 'which body executes this work' would be undecidable
```

实测读数（同一次实跑）：plan 格的覆盖判词 `EVIDENCE_COVERAGE: 3 >= 1 sources; 2 >= 1 retrieved`
（两维都在）；报告制品 `{run_id}:research_report.md` 内联 `text/markdown`；
`4` 条 HandoffBundle digest（立题 / 实验 / 评审 / 报告）。

## 适用边界（本次踩到的四处）

- **规模门是硬的**：加第三条执行体让 `phase_runner.py`（459 行）与 `service.py`（453 行）
  双双越界 ⇒ 按既有先例拆出 `task_dispatch.py`（派发点）与 `runner_wiring.py`（装配）。
  初版的 `report_task.py` 532 行也被拆出读面 `report_facts.py`。**先数行数再动手**。
- **run 行在编排返回后才落库**：报告在 run **内**执行 ⇒ 去 `RunStore` 读只会读到「未知 run」。
  正解是把**在场的那份事实**（`RunContext.run`）随 `SessionSpecContext` 交下去
  （与 `run_id_argument` 同层：声明的是**取值的来源**，不是值）。
- **两处各读一份来源必然漂移**：报告的指标必须读**与 HTTP 读面同一份字节**
  （`experiment_result.json` 的 `metrics`），且值按 JSON **逐字**（`300.0` 不归一成 `300`）。
- **报告在 run 内汇编 ⇒ 抬头不得写「终态」**：写「**汇编时状态**」。把「汇编时的读数」
  写成「终态」是夸大。
- 本记忆**不**作任何安全结论（`R-M1` 未收口）；投递语义**不是**「恰好一次」。

## 来源

- `PLAN-20261014-466` / `RECHECK-20261014-467`；
- 判据：`tests/e2e/test_research_report_arc_offline.py`（7 例）+
  `tests/architecture/python/test_run_chain_capability_exposure.py` /
  `test_session_tool_bindings_exposure.py` / `test_declared_input_sources.py`（清单扩面）。
