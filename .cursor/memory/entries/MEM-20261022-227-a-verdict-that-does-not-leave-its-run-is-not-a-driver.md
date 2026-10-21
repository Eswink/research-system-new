---
id: MEM-20261022-227
title: "判词不出本 run，就不是驱动源：跨 run 搬运评审结论时，三态必须各说各话"
status: ACTIVE
created_at: 2026-10-22
updated_at: 2026-10-22
scope: repository
confidence: 0.9
review_after: 2027-04-22
source_plans:
  - .cursor/plans/tasks/PLAN-20261022-093-goal-093-the-review-verdict-drives-the-next-round.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261022-093-goal-093-the-review-verdict-drives-the-next-round.md
supersedes: []
tags: [review, cross-run, prompt-slot, three-states, carry, goal-093, ladder]
---

## 做了什么

把**上一轮落库的评审结论**做成**下一轮会话提示词的第五个并列槽位**：

- `packages/application/run_orchestration/review_outcome.py`：读取层。入口是 `run_id` →
  `RunStore.get_run` 取 `program_id` → `for_program` 取**序号最大的前序 run** →
  `ReviewFindingStore.for_run` 取判词 → `view_of` 聚合成 `ReviewOutcomeView`
  （`advisory` / `votes` / `voters` / `dissent` / `ineligible` / `targets` / `reason`）；
- `retrieval_prompt.py`：第五段标题
  `PRIOR REVIEW (how the last round was judged; revise against it)` + 渲染器 +
  `compose_prompt` 的第五个关键字参数（段序：方向 → 前序知识 → 检索 → **上一轮评审** →
  被评对象）；
- `services/api/review_outcome_support.py`：组合根闭包（与另三个 builder 同形同层）；
- 链上每一环：`AgentSessionSpec.review_outcome_prompt` → `SessionSpecContext.review_outcome`
  → `session_prompts.review_outcome_prompt` → `session_builder` 的 `compose_prompt` 调用
  → `phase_runner` 的求值点 → `runner_wiring` → 两个组合根。

## 为什么这样做

**判词停在读面上，评审就只是一次性的闸门，不是驱动源。** GOAL-084…087/091 把判词做成了
可归因、可聚合、平票也可读 —— 但 `dissent` / `advisory` 在产品三根里除聚合器自身与读面
自身**零消费者**，四个提示词槽位**没有一个**携带判词。于是「上一轮被判成什么」在下一轮
的会话里**根本不可见**，修订无从谈起。补上这条通道，评审才第一次成为**下一轮的输入**。

## 怎么做与复现

1. **先让通道跑通，再写判据。** 这一步救回一个**只在真 run 上出现**的缺陷：接上闭包后
   `POST /projects/{id}/runs` 直接 **404**。根因是 `runs.get_run(run_id)` 对**本 run**
   抛 `KeyError` —— run 行由调用方在编排返回**之后**才写入，所以「第一轮开工那一刻」必然
   查不到自己。**判成失败会让每个程序的第一轮必然失败**，因此新增第三态 `NO_RUN_ROW`。
   （隔离手法：在同一装配上分别只接 `review_outcome` / 只换 runtime ⇒ 前者 404、后者 200。）
2. **三态各说各话**：`NO_PRIOR_RUN`（没有前序 run）/ `NO_ATTRIBUTABLE`（有前序但读不到
   可归因判词）/ `NO_RUN_ROW`（本 run 行未落库）。合并任意两态 ⇒ 读者分不清「第一轮」与
   「读不到」，而这两件事的处置完全不同。
3. **分歧优先于多数票**：面板有分歧时逐条列出**每一位未采纳者**的 verdict + 执行目标 +
   它自己写的正文；只报多数票会把上一轮刚做出来的「分歧可读」压回一个数字。
4. **归因面必须进提示词**：只看票数时，「两个模型分歧」与「一个模型自言自语」不可区分
   ⇒ `targets` 逐条列出（与 `PanelVerdict.targets` 同源）。
5. 复跑：
   ```bash
   uv run --frozen --no-sync python -B -m pytest \
     tests/application/run_orchestration/test_review_outcome_in_prompt.py \
     tests/application/run_orchestration/test_review_outcome_across_runs.py -q
   uv run --frozen --no-sync python -B tools/verify_goal093_closeout.py --root . --verdict-only
   ```

## 适用边界

- **只搬运，不生成指令**。「该改什么」是**下一轮模型**的事；在模块里生成指令会造出一段
  **没有作者的判词**（与 AGENTS.md §8「记忆不是自由写入的摘要」同一纪律）。
- **不判「模型据此真的改了」**。那是 live 判据 + 人评；与 GOAL-082 EC-04 的未决取舍同源
  （模型对内容采纳不可判，子串判据会假绿）。
- **只取序号最大的那个前序 run**：上一轮没有判词时**不**往前找更早的轮次 —— 那会让
  「上一轮」这个说法失真，故宁可点名「读不到」。
- **这一段进提示词，不进判定面**：`aggregate_panel` 的票数与 advisory 语义**一行未动**，
  `Decision` 仍由验收门给出（advisory 不夺真相权）。
- 不得据此宣称项目安全（`R-M1` 未收口）。

## 来源

- `PLAN-20261022-093` / `RECHECK-20261022-093`
- `packages/application/run_orchestration/review_outcome.py` /
  `services/api/review_outcome_support.py`
- `tests/application/run_orchestration/test_review_outcome_{in_prompt,across_runs}.py`（13 例）
- `.cursor/plans/goals/evidence/GOAL-20261022-093-next-round-charter.md`（读取器自举的产物）
- 同族：[[MEM-20261020-225]]（提示词段在交接层被静默丢弃）—— 本条是同一个问题的下一步：
  **段落得先是「存在的」，然后才谈「送得对」**；[[MEM-20261021-226]]（下一轮的输入要么是
  文件读出来的，要么就不存在）。
