---
id: MEM-20260921-100
title: "验收门按字面名匹配，所以交付物要么由合约声明命名、要么回落事实名——「不猜」这一格才是契约不腐坏的关键"
status: ACTIVE
created_at: 2026-09-21
updated_at: 2026-09-21
scope: repository
confidence: 0.9
review_after: 2027-09-21
source_plans:
  - .cursor/plans/tasks/PLAN-20260921-127-real-deliverable-contract.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260921-127-real-deliverable-contract.md
supersedes: []
tags:
  - acceptance-gate
  - deliverable
  - adr-0031
  - openhands
  - goal-010
---

# 交付物键名与验收门的耦合（GOAL-010 EC-01 实测）

## 做了什么

真实 runtime 的交付物恒以**事实名** `session_message` 登记，而示例合约
`console_demo_deliverable` 声明 `ARTIFACT_EXISTS: analysis_report`，验收门
（`packages/domain/acceptance.py`）按**字面名**匹配 ⇒ 真实 runtime 的链**必然**判拒
（GOAL-009 EC-01 的 run 就停在 `FAILED`）。GOAL-010 EC-01 把这条耦合打开：
交付物的**外层键名由 `AgentSessionSpec.task_contract` 的声明决定**（`required_artifacts` ∪
`ARTIFACT_EXISTS` 去重后**恰一个**才用该名），**验收门一字未改**。结果：真实 run 第一次
走到 `SUCCEEDED`（run `f1710564-855c-43f7-9fdd-84966a878cf9`，`failures` 为空）。

## 为什么这样做

- **判拒的机制是「键名」这一处可判事实，不是玄学。** `result_handler.register_session_result`
  把结构化输出的每个键变成 `Artifact(id=f"{task.id}:{name}")`；`task_phase_helpers.artifact_view`
  同时按 `artifact.id` 与 `id.split(":")[-1]` 建索引 ⇒ **键名必须恰为合约声明的名字**，
  差一个字符就 `ARTIFACT_EXISTS=False`。定位这一类问题时先看**键名**，不要先怀疑门。
- **名字的声明权归合约，不归 adapter。** adapter 只把**已有的**声明读出来——`AgentSessionSpec`
  本来就携带 `task_contract`，所以**不需要新的声明面**。若让 adapter 自己造映射，
  它就变成了声明方（那正是 ADR-0031 D2 要拍板的事）。
- **「不猜」这一格是要紧的，不是防御性冗余。** 没有它，合约只要多声明一个 artifact，
  adapter 就会**挑**一个名字去凑门。
- **ADR-0031 的闸门装在「门」上，不装在 adapter 上。** 它的结构判据
  （`tests/tooling/test_toolpack_capability_policy_pending.py` 第 4 条）判的是
  `evaluate_criterion` 的**字面匹配**（`CriterionInputs` 由用例**手工构造**、不经过 adapter）
  ⇒ 取 **D2-A 形态**（门不改、名字由声明侧给出）时该判据**原样保持绿、无需修改任何门禁**。
  它还断言 `session_message` 仍出现在 adapter 源文件里 ⇒ **事实名不能删掉**，只能作为来源
  事实继续登记。ADR 原文写明 D1/D2「**可分别决定**」⇒ D1 未决时整体保持 `Proposed`。

## 怎么做与复现

受控边界（**判据已压过，别删**）：

| 合约声明 | 交付物键名 |
| --- | --- |
| 恰一个 artifact 名 | 该名 |
| 零个 | 事实名 `session_message` |
| **多个互不相同** | 事实名 `session_message`（**不猜**） |

- 实现：`adapters/openhands/runtime_adapter.py` 的 `_declared_deliverable_name` +
  `_deliverable`（载荷带 `fact_name` / `declared_artifact` / `contract_id` 三个来源事实）。
- 判据：`tests/architecture/python/test_real_deliverable_contract_same_source.py`（8 个，
  断言全用**字面量**，不 import adapter 的 helper ⇒ 不与实现循环论证）；
  链级两分支 `tests/e2e/test_ec03_real_runtime_offline_chain.py`；
  live `tests/e2e/test_real_deliverable_contract_live.py`。
- **「门 PASS」怎么判**：`task_phase_helpers.register_and_gate` 在 `evaluate_gate` 返回 `None`
  时**必然**写 `failure_step("… rejected by acceptance gate")` ⇒ run `FAILED`；因此
  「`SUCCEEDED` 且 `failures` 为空」⟺ 门通过。**逐条 criterion 的 reason 文本活在进程内的
  review finding 里，进程结束即消失**——要拿到它必须再跑一次（与「最小必要调用」冲突）。
- 反证（压过即红）：把键名写死回事实名 ⇒ PASS 分支红；把 `len(declared) == 1` 改成 `declared`
  ⇒ 链级 REJECT 分支与判据级边界用例**都**红；把文档里「回落」的措辞改弱 ⇒ 文档同源用例红。

## 适用边界

- **只对「声明恰一个 artifact」的合约成立。** 多产物合约下 adapter **故意**回落事实名、
  门**故意**判拒——那是设计，不是待修的缺陷。
- **交付物内容未被判据把守。** `ARTIFACT_EXISTS` 只判**存在**、不判**内容是否合格**；
  交付物仍是自由文本。真实模型能否**稳定**产出可用交付物，本条目**不**回答（两次
  `SUCCEEDED` 是**两次观测**，按 AGENTS.md §4 只能停在「可重复配置」）。
- **证据链不在本条目射程内。** 该成功 run 的 `EVIDENCE_COVERAGE` 仍由**模型自述**满足
  （数的是交付物自己，`TrustLabel.GENERATED`）——那是 GOAL-010 **EC-02** 的靶子，未解决。
- **不覆盖** `ANTHROPIC` 面的 run 路径（`docs/integration/LLM_ENDPOINTS.md` §12）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260921-127-real-deliverable-contract.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260921-127-real-deliverable-contract.md`（PASS_WITH_WARNINGS）
- 目标：`.cursor/plans/goals/GOAL-20260921-010-real-deliverable-contract.md`（EC-01）
- 决策：`docs/adr/ADR-0031-toolpack-capability-policy.md`（D2 已定向；**D1 仍未决**，整体 Proposed）
- 代码：`adapters/openhands/runtime_adapter.py`、`packages/application/run_orchestration/result_handler.py`、
  `packages/application/run_orchestration/task_phase_helpers.py`、`packages/domain/acceptance.py`
- 前置：`MEM-20260920-094`（live 门与「设计内 FAILED」）
