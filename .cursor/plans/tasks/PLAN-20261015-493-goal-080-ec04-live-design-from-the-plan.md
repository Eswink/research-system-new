---
id: PLAN-20261015-493
slug: goal-080-ec04-live-design-from-the-plan
title: GOAL-080 cycle 4 — 真实模型写出的设计驱动实验（EC-04）
status: DONE
created_at: 2026-10-15
updated_at: 2026-10-16
parent_goal: GOAL-20261015-080
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261015-494-goal-080-ec04-live-design-from-the-plan.md
memory_entries: []
---

# PLAN-20261015-493 — GOAL-080 cycle 4

## 验收条件

- [x] live 判据在树且默认门如实 skip（`requires_live_llm` + 显式开关）
- [x] live 判据断言：计划制品里有**设计块** + 读面上的臂**就是**计划里那些
- [x] **判据补强**：每个臂声明的参数**逐键**落在该臂实验的落库指标里（防「参数没进容器」假绿）
- [x] 真实 run 上设计由模型写出并驱动实验（多臂、参数各自生效）
- [x] 读数归档进树（阻塞点取证 + 达成读数，均 `CR=0`）
- [x] 记录面（PLAN + RECHECK）与 GOAL 回写

## 目标（本 cycle 的可独立验收主题）

**EC-04**：真实中转站上跑通一次 —— 真实模型写出的**计划产物**驱动该 run 的实验臂与参数。

## ★ 本 cycle 的**真缺陷**（四轮真实 run 逐次暴露，全在产品代码里）

1. **SDK 循环控制动词被当成能力拒掉**：`think` / `finish` 双双落 `default_effect: DENY`
   ⇒ 模型**无法思考、无法收尾**（自陈「even `think` is being denied」）。它们不是能力
   （SDK 逐字：*required* for the agent to work；`readOnlyHint=True`，经 `include_default_tools`
   默认注入）⇒ 逐字白名单 `LOOP_CONTROL_VERBS`，**只在 agent loop** 豁免，R-03 直达通道照旧全门禁。
2. **`finish` 动作的 message 从不变成 MESSAGE**：SDK 逐字称它 *Final message to send to the
   user* ⇒ 答复正文在动作里 ⇒ 交付物只剩提示词（`message_count = 1`）。
3. **正文取自 Python repr + 交付物被遥测上限截断**：`str(content)` 是 repr 而非文本；
   交付物从映射事件取正文而映射层套了 500 上限 ⇒ 计划被切在设计块中间。

## 实施清单

1. **WP-A**（判据）：live 判据 + 参数生效断言（两层名字映射：参数名 vs 脚本回报名）。
2. **WP-B**（产品）：三处缺陷的修复（循环控制豁免 / finish 投影 / 正文与交付物）。
3. **WP-C**（记录 + 门）：本文件 + RECHECK + GOAL 回写；真实 run 读数归档；m0。

## 影响报告

- **产品代码**：`policy_enforcing_agent`（新增逐字豁免集）/ `event_mapping`（finish 投影 +
  正文提取 + 不截断的 `final_answer_text`）/ `runtime_adapter`（交付物改用前者）/
  `experiment_support`（`docker_experiment_assembly` 透传 `design_source`）。
- **合约**：`research_report_plan` 的 `purpose` 改写为**任务指令**（它**就是**模型读到的任务书）。
- **判据面**：只增（新判据 + 既有判据**加强**：参数生效）；**无放宽**。
- **无 schema 迁移、无依赖变化、无新增 allow、无凭据变化。**

## 残余与未覆盖

- live 实跑**只跑一次 run**（本轮为取证共跑四次：三次暴露缺陷、一次达成）；
- 「模型的**设计质量**」无人判（`W-2`）；臂数 > 2 与择优不在射程（`W-4`）。

## 证据

| 面 | 读数 | 命令 |
| --- | --- | --- |
| live 实跑 | **1 passed in 75.57s**（run `748a56a6-…`，`SUCCEEDED`、`failures: []`） | `RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1 … -m pytest tests/e2e/test_experiment_design_from_the_plan_live.py -q` |
| 设计由模型写出 | `{"experiment_design": {"arms": {"deduped": {"seed":42,"n_items":120,"duplicate_pairs":0}, "raw": {"seed":42,"n_items":120,"duplicate_pairs":12}}}}` | 计划制品正文（4240 字符） |
| 参数逐键生效 | `duplicates_expected` **0 vs 12**、`comparison_reduction_ratio` **0.0 vs 595.0** | 读面 `GET /runs/{id}/experiments` |
| 归档 | `evidence/GOAL-20261015-080-ec04-{blocker,design-evidence}.txt`（`CR=0`） | — |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-15 | IN_PROGRESS | cycle 4 建档（live 判据 + 计划制品取证）。 |
| 2026-10-15 | BLOCKED→IN_PROGRESS | 前三次真实 run 暴露三处产品缺陷（详见修复记录）；依授权拍板「交付物取会话末条消息」并逐一修复。 |
| 2026-10-16 | DONE | 末次真实 run **1 passed**：模型自写设计块、两臂各跑一次、参数逐键生效。RECHECK-494 = PASS。 |
