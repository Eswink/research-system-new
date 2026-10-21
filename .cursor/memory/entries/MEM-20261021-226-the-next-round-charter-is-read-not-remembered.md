---
id: MEM-20261021-226
title: "迭代的输入要么是文件读出来的，要么就不存在：给「上一轮 → 下一轮」装一个带拒绝臂的读取器"
status: ACTIVE
created_at: 2026-10-21
updated_at: 2026-10-21
scope: repository
confidence: 0.9
review_after: 2027-04-21
source_plans:
  - .cursor/plans/tasks/PLAN-20261021-092-goal-092-the-next-round-charter-is-read-not-remembered.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261021-092-goal-092-the-next-round-charter-is-read-not-remembered.md
supersedes: []
tags: [iteration, charter, deterministic-reader, refusal, weak-convention, goal-092, ladder]
---

## 做了什么

把战役级的「上一轮输出 → 下一轮 charter」从**人的记忆**换成**文件的读数**：

- `tools/charter_parse.py`：纯解析原语（frontmatter / 小节 / 表格数据行 / 残余切分 /
  CI 台账分类），零时钟零出网零模型；
- `tools/next_round_charter.py`：入口。输入**已收口** GOAL + 它的 RECHECK + 宪章 +
  显式的 `--next-goal-id`（编号是判断，不由工具猜），输出三块可提取事实的骨架；
- **六类不合格输入**（未终态 / 缺复检 / 复检不存在 / 复检不属于本 GOAL / 复检不通过 /
  阶梯未收录 / 编号断号）逐条 `REFUSED <code>` + `exit 2` + **不写盘**；
- 判断面（objective / EC 的内容）在骨架里显式留空（`<待填：判断>`）。

## 为什么这样做

**「靠人记得读」这类衔接的失效不在文本里，而在没有读者。** 宪章写了「收口时追加进展记录」，
那条有判据看着（`test_mainline_research_ladder_advances.py`）⇒ 不会漂；但「下一轮的提示词
有没有把上一轮的残余带上」没有任何判据看着 —— 因为**下一轮的提示词不在树里**。
一旦把那一份输入变成**树内制品**，它就能被读、被判、被复核。

**拒绝臂比正例更重要。** 一个只会在正常输入上产出骨架的读取器，与一段手写的 markdown
没有区别；区别在于它**拒绝**：状态不对不产、复检不通过不产、编号断号不产。这些拒绝不是
防御性编程，而是把「这一轮还没有资格进入下一轮」变成可判事实。

## 怎么做与复现

1. **先跑真文件，再写判据**：对着 GOAL-091 跑一次，人眼核对 `W-1…W-7`、阶梯的「复检」行、
   CI 台账的 6 行。这一步立刻暴露一个真实形态：残余节后面还跟着 `R-1…R-3` 一组，
   它们的**续行同样是缩进的** ⇒ 若不显式「非缩进行结束当前条」，最后一条会把残余风险吞进去。
2. **判据自己写一份切分**（不用被测实现的输出当期望）—— 两份独立实现对同一输入给同一读数，
   才叫口径成立；另外单独一条用例把读取器与 `test_mainline_research_ladder_advances.py`
   对**同一份宪章**的阶梯读数逐条比对。
3. **反证在合成树上改事实**：删整条 `W-7`（编号仍连续 ⇒ 产物少一条且自报「共 6 条」）、
   改写某条正文（⇒ 产物跟着改）、`status` 改 `ACTIVE`（⇒ `GOAL_NOT_TERMINAL`）、
   删复检文件（⇒ `RECHECK_MISSING`）、改复检的 `parent_goal`（⇒ `RECHECK_NOT_THIS_GOAL`）、
   改 `result: REVISE`（⇒ `RECHECK_NOT_PASSING`）、删 `W-2` 留断号（⇒ `RESIDUAL_GAP`
   并报出读到的序列）、改宪章阶梯行（⇒ `LADDER_NOT_RECORDED`）、清空残余节（⇒ `RESIDUAL_EMPTY`）。
4. 复跑：
   ```bash
   uv run --frozen --no-sync python -B -m pytest tests/tooling/test_next_round_charter.py -q
   uv run --frozen --no-sync python -B tools/next_round_charter.py --root . \
     --goal .cursor/plans/goals/GOAL-20261021-092-the-next-round-charter-is-read-not-remembered.md \
     --next-goal-id GOAL-20261022-093 --out /tmp/next.md
   ```

## 适用边界

- **只覆盖战役级迭代**：每轮的 GOAL charter 由上一轮的残余派生。产品内「模型据上一轮结论
  提出新问题」这一面**仍无判据**，且仍被 GOAL-082 EC-04 的未决取舍卡住（模型只做不可判的
  内容采纳；解除条件属产品结构改动）。不要把本轮当成那一面的解决。
- **`W-NN` 编号连续性是新加的纪律，不是既有事实**：GOAL-090 只用 `W-6` 一条（前面没有
  `W-1…W-5`）⇒ 读它时读取器会判 `RESIDUAL_GAP`。这是**正确**行为（编号不连续的记录无法
  判断「少了一条」还是「本来就少」），但意味着**历史 GOAL 不能直接喂进读取器**。
- **CI 台账的「全绿」是机械分类**（`success` / 无 run / 判红 / 未识别），不独立取证 CI 本身。
- **它不判下一轮该做什么**：objective / EC 是判断。骨架里留空的那几格被一条判据钉住
  （断言它们**确实**是 `<待填：判断>`），防它偷偷开始做判断。
- 不得据此宣称项目安全（`R-M1` 未收口）。

## 来源

- `PLAN-20261021-092` / `RECHECK-20261021-092`
- `tools/next_round_charter.py` / `tools/charter_parse.py`
- `tests/tooling/test_next_round_charter.py`（19 例）
- `.cursor/plans/goals/evidence/GOAL-20261021-092-next-round-charter.md`（产物）
- 同族：[[MEM-20261020-225]]（判据测对了函数、缺陷在交接层）—— 本条问的是同一个问题的
  下一站：**交接层没有留下可复核的输入**。
