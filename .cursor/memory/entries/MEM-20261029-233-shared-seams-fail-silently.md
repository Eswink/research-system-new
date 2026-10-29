---
id: MEM-20261029-233
title: "共用缝上的四个静默失效：能力面漏声明、面板相跨相输入、task.contract 不存在、已渲染字符串被再渲染"
status: ACTIVE
created_at: 2026-10-29
updated_at: 2026-10-29
scope: repository
confidence: 0.95
review_after: 2027-04-29
source_plans:
  - .cursor/plans/tasks/PLAN-20261029-100-goal-100-submission-ready-and-citation-binding.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261029-100-goal-100-submission-ready-and-citation-binding.md
supersedes: []
---

# 共用缝上的四个静默失效

## 做了什么

序 68（GOAL-100）加两个相（`editorial` 投稿决策 / `revision` 逐条应答）与两条共用缝
（提示词多一段「评审点表」、`retmax` 配置面）时，**判据全绿而真实 run 是坏的** 发生了五次。
四次都在共用缝上，形态各不同 —— 记下来是因为它们与本仓既有记忆里的几类假绿**不同**：
这次不是「判据只覆盖一半」，而是**判据根本看不见那个面**。

## 四个静默失效（本轮实测）

1. **能力面漏声明 ⇒ 会话工具面漏 provider**。`capability_execution: run_chain` 只把
   **本相 `tool_requirements` 里**的 provider 从会话工具面排除；新相只声明三条能力，另三条
   能力对应的 provider（`europe_pmc` / `ncbi_eutils` / `openhands_workspace`）就排不掉，
   留在会话工具面又没绑定 ⇒ 真实 run 建会话时 `ToolDefinition 'europe_pmc' is not
   registered`。**`compile_protocol` 零 ERROR**：它只检声明内部自洽，不检「排不掉的东西
   能不能解析」。识别手法 = 新相一律**把冻结集覆盖到的能力全声明**（与 `manuscript` 相
   同一手法），并用 `session_tool_face(plan, phase)` 读一次它必须是空元组。

2. **评审面板相不能当跨相 `inputs` 的产出方**。`cross_phase_inputs.producer_task_id` 按
   `{run_id}:{phase}:` 前缀解析，命中两条就点名 `ambiguous`。`review` 相是 panel
   （`scientific_reviewer` + `novelty_reviewer` 两个 `ResearchTask`）⇒ `review:review_decision`
   **恒** ambiguous。编译期只检「该产物在产出方的 `outputs` 里」，不检「产出方有几个任务」。
   识别手法 = 跨相 `inputs` 的产出方必须是**单任务相**；面板的结论经**提示词那一段**
   （`PRIOR REVIEW` / `REVIEW POINTS`）送。

3. **`ResearchTask` 只有 `contract_id`，没有 `contract`**。写成 `task.contract` 时
   `getattr(..., None)` 拿到 `None`，于是「要不要做这件事」的判断**静默返回 False** ——
   点表从未进提示词，而模型照常回一条 `P1`，直到汇编器点名 19 条漏答。识别手法 = 判断
   「这一相要不要某个面」时**按在场字段写**（`task.contract_id`），并在判据里跑一次
   「该相真的拿到了那个面」。

4. **已渲染的字符串被当视图对象再渲染一次**。`session_prompts.*_prompt` 返回**文本**，
   `compose_prompt` 又把它交回同一个 `prompt_with_*` ⇒ `tuple("<文本>")` 按**字符**迭代 ⇒
   提示词里是 `-  (): ` 空行（本轮 19 行）。这是本仓**第三次**踩同一条缝（`_section_of`
   的 docstring 已记过 GOAL-091 的实测），而每次都是**新加的那一段**没有 `str` 短路。
   识别手法 = 新写一个 `prompt_with_<slot>` 时，第一行就是 `if isinstance(x, str): return x`。

**第五个不在共用缝上但同属「读面假绿」**：`ArtifactStore.put` **不等于**读面可见 ——
`GET /runs/{id}/artifacts` 走 claim→relation 投影，只 `put` 不 `register` 的制品读不到。
识别手法 = 新产品件一律成对写 `_put_*` 与 `_register_*`（照抄 `manuscript` 的 `_register`）。

## 为什么这样做

这五条的共性是**「判据绿」与「产品能用」不同源**：单元判据直接喂对象/字符串，绕过了产品
路径上真正的那条缝。**唯一可靠的识别手法是走一次产品入口**（
`TestClient(create_app(deps))` → `POST /projects/{id}/runs`）：五个里**只有**第 4、5 条
会被单测抓到（且只有当我构造的输入与产品路径同形时）。

## 怎么做与复现

- 新相：能力面覆盖冻结集 → 读一次 `session_tool_face` 必须是空；
- 跨相 `inputs`：产出方必须是单任务相（面板结论走提示词）；
- 判「要不要」：读在场字段（`contract_id`），不读不存在的属性；
- 新提示词段：`str` 短路 + 一条「喂已渲染字符串」的用例；
- 新产品件：`put` 与 `register` 成对，并在**读面**（不是 store）判它在场。

## 适用边界

适用于「共用渲染/装配缝 + 新加一格」的改动。**不**声称这五类已普查全仓（本轮只修了自己
射程内的）；也**不**声称产品入口判据能替代单元判据 —— 两者各自看见不同的面，缺一都会漏。

## 来源

- GOAL：`.cursor/plans/goals/GOAL-20261029-100-submission-ready-and-citation-binding.md`
- 子 PLAN：`.cursor/plans/tasks/PLAN-20261029-100-goal-100-submission-ready-and-citation-binding.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261029-100-goal-100-submission-ready-and-citation-binding.md`
- 判据：`tests/application/test_citation_numbers_reach_the_prompt.py`、
  `tests/application/test_editorial_decision.py`、`tests/application/test_author_response.py`、
  `tests/api/test_retmax_is_configurable.py`、
  `tests/e2e/test_direction_to_manuscript_product_path.py`
