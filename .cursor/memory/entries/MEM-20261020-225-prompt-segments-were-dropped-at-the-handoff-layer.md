---
id: MEM-20261020-225
title: "提示词四段在真实会话里全被静默丢弃：判据测的是渲染器，缺陷在「谁把什么交给谁」"
status: ACTIVE
created_at: 2026-10-20
updated_at: 2026-10-20
scope: repository
confidence: 0.95
review_after: 2027-04-20
source_plans:
  - .cursor/plans/tasks/PLAN-20261020-091-goal-091-two-models-judge-the-same-artifact.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261020-091-goal-091-two-models-judge-the-same-artifact.md
supersedes: []
tags: [prompt-assembly, dead-seam, review, two-models, envelope, goal-091]
---

## 做了什么

让「两个不同的评审模型对同一件产物各判一次」从**结构不可达**变成**可判定**，并在真跑上
取得有效分歧读数（`main/glm-5.3` 0.45 判负 / `main/kimi-k2.6` 0.82 判过）。

## 三条可复用的形态

### 1. 判据测了纯函数，缺陷在传递层

`compose_prompt` 的**纯函数**判据全绿（渲染器逐条正确、`== purpose` 零回归也成立），但真实
会话收到的提示词里**四段全不见**。根因：
`task_executor._run_session` 把 `session_prompts.*_prompt(spec_context)` 的返回（**已渲染的
`str`**）放进 `AgentSessionSpec`，`SessionBuilder` 又把它交给 `compose_prompt`，而后者按
**视图对象**调 `render_*_prompt(view)` —— 对字符串取 `getattr(view, "entries", ())` 得空
⇒ 返回空串 ⇒ 那一段**静默丢弃**。

**教训**：当「渲染器」与「装配器」是两层时，判据必须跑**装配→发送的整条缝**，不能只测
渲染器和拼接函数。取证手法：在 `LocalConversation.send_message` 处打点，看**实际发出的
字符串**；在 `build_session` 处再打一次点看**入参** —— 两处一对比，缺口落在哪一层立刻分明。
（同族见 [[declared-but-never-constructed-is-a-dead-seam]]：那条问「有没有构造点」，这条问
「构造出来的东西有没有原样送到终点」。）

### 2. 信封形态：模型写的字在多一层里面

真实会话交付物是**信封**（`{declared_artifact: {content: "<模型正文>", …}}`），而
`REVIEW_SCORE` 只按**顶层**点分路径取值 ⇒ 恒 `None` ⇒ 恒判负。后果不是「评审太严」，而是
**两个模型无论判什么都只得到一个「不知道」** —— 「不同模型判出不同结论」在数据面上不可达。

**教训**：凡是「读模型自己写的数」的判据，取值面必须与**落库形态**一致（信封 / 直形态
两种都得认）。修法是复用既有解包口径（`declared_object`），不要写第二份解析。

### 3. 合约措辞也是一种判据

合约写「artifact is included **before** this task text」，而实际拼法是**追加在 purpose
之后** ⇒ 模型按指令往前找、找不到，如实报告「段不存在」。**模型没做错，是措辞在骗它**。

**教训**：提示词里的方位词（before / below / attached）是**可被检验的断言**。改拼法要同轮
改措辞；否则模型会把「指令与事实不符」如实报成「内容缺失」，而那条读数会把你引向错误的
根因。

## 为什么这样做

**判据测对了函数，却测错了对象。** `render_retrieval_prompt` / `compose_prompt` 的纯函数
判据全绿，`== purpose` 的零回归也成立 —— 但真实会话里那几段**一个字都没到模型眼前**。
缺陷不在函数里，在**两次交接**：装配层把「已渲染的字符串」放进 spec，发送层又把它当成
「视图对象」交给渲染器。任一侧单独看都合理，拼起来就是**静默丢内容**（空串且不报错）。

**为什么先钉缺口而不是先修**：若直接写「加了第四段就通过」，读者无从判断那一段是否真的
到达模型。本轮的做法是**在 `send_message` 处打点看实际发出的字符串**，用读数把缺口钉死，
再修。这也是本仓反复出现的形态：**判据要与它声称覆盖的那一层对齐**。

**为什么合约措辞也算判据**：模型是**按字面**执行的 —— 它说「你说在任务文本之前，我读了
整条消息，没有」，这句话**既真实又无用**（因为拼法是把段追加在后）。定位时若只看「模型说
没有」，会去查装配；实际要查的是**措辞与拼法是否一致**。

## 怎么做与复现

1. **取证三处打点**（缺一不可，否则分不清缺口在哪一层）：
   - 装配器处：`with_review_material` 是否挂上了视图；
   - `SessionBuilder.build_session` 的 `compose_prompt` **入参**：是 `str` 还是视图；
   - `LocalConversation.send_message` 的**实际字符串**：那一段在不在。
   ```bash
   # 真实 SDK 的 send_message 在 LocalConversation 上（不在 Conversation 上）
   from openhands.sdk.conversation.impl.local_conversation import LocalConversation
   ```
2. **修法**：`_section_of(value, render)` —— `str` 原样用、视图才渲染。
   **零回归两侧都要钉**：空串 / `None` ⇒ `compose_prompt(...) == purpose`（逐字）。
3. **信封形态**：`REVIEW_SCORE` 的取值面在**路径每一段**上解信封，复用既有
   `declared_object`（不写第二份解析）；解不出 ⇒ 仍 `review score unknown`。
4. **措辞与拼法同轮改**：`before this task text` → `below this task text`。
5. 复跑：
   ```bash
   uv run --frozen --no-sync python -B -m pytest      tests/application/run_orchestration/test_review_material_in_prompt.py      tests/e2e/test_two_models_judge_the_same_artifact.py -q
   set -a; . ./.env; set +a
   RESEARCHOS_AGENT_RUNTIME=openhands RESEARCHOS_LIVE_E2E=1      uv run --frozen --no-sync python -B -m pytest      tests/e2e/test_two_models_judge_the_same_artifact_live.py -q -rs
   ```

## 适用边界

- 本修法覆盖**会话提示词**的四段（方向 / 前序 / 检索 / 被评对象）；fork / resume 路径
  走的是 `AgentSessionSpec` 的同一组字段 ⇒ 同样受益，但本轮**没有**单独为 resume 取证。
- `REVIEW_SCORE` 的分数仍是**评审者自述**：本轮只让它读得到，**没有**判它与判词是否一致。
- 分歧的**质量**无人判：只证明「两位判出了不同结论」，不证明谁更对。
- 中转站瞬时失败会打掉一位评审者（该位 `UNKNOWN`，读面如实点名，不冒充判负）。

## 来源

- GOAL：[GOAL-20261020-091](../../plans/goals/GOAL-20261020-091-two-models-judge-the-same-artifact.md)
- 子 PLAN：[PLAN-20261020-091](../../plans/tasks/PLAN-20261020-091-goal-091-two-models-judge-the-same-artifact.md)
- 复检：[RECHECK-20261020-091](../../plans/rechecks/RECHECK-20261020-091-goal-091-two-models-judge-the-same-artifact.md)
- 判据：`tests/application/run_orchestration/test_review_material_in_prompt.py`
  （含 `test_a_rendered_section_string_survives_the_composer`）、
  `tests/application/run_orchestration/test_review_score_reads_the_envelope.py`、
  `tests/e2e/test_two_models_judge_the_same_artifact.py`、
  `tests/e2e/test_two_models_judge_the_same_artifact_live.py`
- 真跑读数：`scratch/goal091-ec04-dual-review.json`（gitignored；正文已抄入 RECHECK）


- 分数仍是「评审者自述」，没判它是否与判词一致（低分却写 ACCEPT 不可判）；
- 分歧的**质量**无人判（只判「判出了不同结论」，不判谁更对）；
- 中转站瞬时失败会打掉一位评审者 ⇒ 该位 `UNKNOWN`（读面如实点名，不冒充判负）。
