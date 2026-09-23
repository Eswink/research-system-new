---
id: MEM-20260923-110
title: "冻结集含两件 provider 时会话构造是独立失败面：SDK 工具名由类名派生 ⇒ 惰性替身必须按名分名，且该死法可用 mock 端点离线复现（零模型调用）"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-142-live-experiment-chain-to-terminal.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-143-live-experiment-chain-to-terminal.md
supersedes: []
---

# MEM-20260923-110 — 两件 provider 的冻结集 ⇒ 会话构造独立失败面

## 做了什么

在 GOAL-012 EC-02 的第一次真实取样里，`sort_analysis_v1` 的 run **冻结成功、实验真的在容器里跑了**，
却死在 review 阶段的会话：`task … failed: Duplicate tool names found: {'inert'}`。
根因是测试侧惰性工具替身把冻结集里的**两件** provider（`openhands_workspace` +
`m12_artifact`）都注册成**同一个类**，而 OpenHands SDK 的 `ToolDefinition.name` 是
**类名派生**的（`InertTool` ⇒ `inert`）⇒ 两件同名 ⇒ agent 初始化直接抛错（`Loaded 2 tools
from spec` 之后立刻失败，**零模型调用**）。

修法：`tests/e2e/live_run_support.inert_tool_class_for(registry_name)` 按注册名生成**独有类名**
的惰性工具类（模块全局只造一次、显式 `__qualname__`/`__module__`，避免 SDK 的
`<locals>` / "Duplicate class definition" 两种毒化），`register_inert_tools` 逐名分名注册。

## 为什么这样做

- **不是产品缺陷**：真实 provider→SDK 工具的映射属 EC-05（未接线），测试侧惰性替身只是让
  冻结集里的名字在 SDK 注册表里可解析。但它必须**每名一件**，否则「两件 provider 的协议」
  这条在测试装配里根本不可执行。
- **它只在 ≥2 件 provider 时出现**：`real_research_task_v1`（1 件 provider）的真 run 一路绿，
  所以这个死法长期没暴露；`sort_analysis_v1` 的每个阶段都是两件。
- **可离线复现**：mock 端点 + `map_tools=True` 的既有装配（`test_ec03_real_runtime_offline_chain.py`）
  逐字复现了 live 的死法（`1 failed`，mock 端点零请求），无需真实调用即可钉住。

## 怎么做与复现

1. 判据：`tests/e2e/test_ec03_real_runtime_offline_chain.py::test_a_two_provider_frozen_set_starts_a_session`
   （离线；判**可观测后果**：mock 端点收到补全请求 + 失败面里没有名字冲突）。
2. 按压（先红）：把 `register_inert_tools` 临时改回共用一个类 ⇒ 该用例逐字红
   （`scratch/goal012-c2-press-duplicate.txt`：`Duplicate tool names found: {'inert'}` + `requests == []`）。
3. 相关判据：`tests/e2e/test_ec02_experiment_chain_offline.py`（离线全链，`requires_docker`）与
   `tests/e2e/test_ec02_experiment_live.py`（真实一次 run，`requires_live_llm`）。

## 适用边界

- 只覆盖**测试侧惰性映射**；真实映射（EC-05）若实现为「一个类服务多件 provider」，同样会撞
  名字冲突——届时要按 provider 声明工具名，而不是复用类名。
- 判据不依赖惰性替身的实现细节（看 mock 请求与失败文案），所以替身换实现时判据仍有效。
- 另一条相邻事实（同一 cycle）：**合约声明了 `experiment` 的阶段不跑会话**（走
  `dispatch_experiment`）⇒ 「会话交付物」只会卡在**没有**实验声明的那些阶段上。

## 来源

- GOAL-20260923-012 EC-02；PLAN-20260923-142；RECHECK-20260923-143。
- 实测：`scratch/goal012-c2-live2/**/ec02-live-experiment-chain.json`（失败形态）与
  `scratch/goal012-c2-live-sample.json`（修好之后的那一次 `SUCCEEDED` 样张）。
