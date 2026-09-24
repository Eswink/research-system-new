---
id: MEM-20260924-128
title: "运行链 phase 的 required_capabilities 必须覆盖**全计划**的冻结工具集，否则别的相位会把 provider 漏进会话工具表"
status: ACTIVE
created_at: 2026-09-24
updated_at: 2026-09-24
scope: repository
confidence: 0.95
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260924-160-acceptance-gate-input-face-wiring.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260924-162-acceptance-gate-input-face.md
supersedes: []
---

## 做了什么

新增一份出厂协议（`examples/protocols/real_experiment_research_v1.yaml`：`analysis` 相位走
运行链检索、`execution` 相位走沙箱实验）后，**离线链路真的走产品运行链**时 run 判红：

```
ToolDefinition 'openhands_workspace' is not registered
```

根因不在实验相位，也不在工具注册表，而在**两张表的粒度不同**：

- `frozen_tool_set` 是**计划级**的（`flatten_tool_providers(plan)`——一个 plan 只用一份冻结集，
  AGENTS.md §5 要求 AgentSession 的有效工具集冻结）；
- 运行链能力步的声明面 `capability_execution: run_chain` 是**相位级**的
  （`run_chain_tool_ids(plan, phase)`）。

于是 `execution` 相位声明的 provider（`openhands_workspace`）进了**计划级**冻结集，
却不在 `analysis` 相位的运行链声明里 ⇒ 落到 `analysis` 的**会话工具表**里，而产品路径上
provider id（`m12_artifact` / `openhands_workspace`）与 SDK 已注册 tool 名之间**没有映射**
（见 `MEM` 中「provider id → SDK tool mapping」一条）⇒ 会话创建点名失败。

修法是**声明面**的：把该 provider 提供的能力加进**其它相位**的 `required_capabilities`
（本处 `analysis` 补 `workspace.read`），让每个相位声明的运行链能力集合**覆盖全计划**的
provider 集合——**不是**给 provider 注册 SDK 工具名、也不是改冻结语义。出厂原型里已有先例：
`real_retrieval_research_v1` 的 `analysis` 声明了 `artifact.read` 却从不链式执行它，
存在的意义就是「别把它暴露成会话工具」。

## 为什么这样做

「计划级冻结 + 相位级声明」的组合下，**任何**新增相位/新增 provider 都可能踩到这条：
症状出现在运行期会话创建，离真正的声明缺口（另一个相位）很远，很容易被误诊成工具注册缺陷
（本 cycle 初判就是「缺 provider→tool 映射」，实为声明面没覆盖）。

## 怎么做与复现

- 新增带 `capability_execution: run_chain` 的协议/相位时：先列出**全计划**的 provider 集合
  （`flatten_tool_providers(plan)`），再看每个相位的 `required_capabilities` 是否**并集**
  覆盖它；不覆盖就补声明，补的注释写清「只为不进会话工具表」。
- 症状定位：`ToolDefinition '<provider_id>' is not registered` 出现在**会话创建**、
  且点名的是一个**别的相位**的 provider ⇒ 先查声明面，别先查注册表。
- 复现：`tests/e2e/test_real_experiment_research_offline.py`（离线链路判据）在缺声明时判红、
  补声明后复绿；架构侧的暴露面判据是
  `tests/architecture/python/test_run_chain_capability_exposure.py`。

## 适用边界

- 只对「计划级冻结集 + 相位级运行链声明」这套现行语义成立（`packages/application/run_orchestration`）。
- 补声明**不**等于放行：它只影响**会话工具表**的构成，不改变 policy 面的 allow/deny。
  别用它去绕开策略面（那会变成放宽权限，属 GOAL 明文禁止）。

## 来源

- `.cursor/plans/tasks/PLAN-20260924-160-acceptance-gate-input-face-wiring.md`（WP5 证据段）
- `.cursor/plans/rechecks/RECHECK-20260924-162-acceptance-gate-input-face.md`（第二节）
- `examples/protocols/real_experiment_research_v1.yaml`（相位声明与注释）
- `tests/e2e/test_real_experiment_research_offline.py`（判据）
