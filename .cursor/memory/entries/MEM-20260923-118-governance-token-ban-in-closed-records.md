---
id: MEM-20260923-118
title: "`DONE` 的 task plan 与 `PASS` 的 recheck 正文**任意位置**不得出现 `PENDING` / `待`·`填写` 字面量"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.95
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-151-live-page-read-face-batch-two.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-152-live-page-read-face-batch-two.md
supersedes: []
---

## 做了什么

`governance-check/scripts/validate.py` 有两条**字面量 token 禁令**：

- `:705` —— `DONE` 的 task plan，正文含 `待`·`填写` 或 `PENDING` ⇒
  `DONE 任务仍包含占位内容: <plan_id>`。
- `:723` —— `result ∈ {PASS, PASS_WITH_WARNINGS}` 的复检，正文含 `PENDING` ⇒
  `通过的复检仍有 PENDING gate: <recheck_id>`。

GOAL-013 cycle 2 收口时两条同时命中，判词逐字：

```
- DONE 任务仍包含占位内容: PLAN-20260923-151
- 通过的复检仍有 PENDING gate: RECHECK-20260923-152
```

成因不是「忘了填」，而是**如实描述上游目标的进展**：收口记录里写了
「EC-02 3/6，仍 `PENDING`」——而 `PENDING` 恰恰是 GOAL 侧 EC 的合法状态取值。
**GOAL 里的合法取值，抄进 task plan / recheck 正文就违规。**

## 为什么这样做

这两条禁的是「收口记录里混进未完成标记」，判据实现是**朴素子串匹配**，
不区分「这是本计划的占位」还是「这是引用上游 EC 的状态」。因此它会在
**记录写得越如实越容易踩**——把上游进展一并写进收口记录正是这个 GOAL 要求的做法。
`m0` 的 `framework/validate` 是唯一会红的地方（它跑 `validate.py`），
而 `validate.py` 单独跑一次只要几秒 ⇒ **收口后先单跑 `validate.py`，再花 10 分钟跑全量 m0**。

## 怎么做与复现

- 写收口记录时，**用自然语言表达未达成**，不要照抄 EC 的状态取值：
  「域覆盖未满 6 ⇒ 仍未达成」而不是「仍 PENDING」。
- 自查（改完立刻跑，秒级）：

  ```bash
  grep -nE "PENDING|待" .cursor/plans/tasks/PLAN-*.md .cursor/plans/rechecks/RECHECK-*.md
  python .cursor/skills/governance-check/scripts/validate.py
  ```

- 复现红线：在任一 `DONE` plan 正文加一行 `PENDING` ⇒ `validate.py` 立刻报
  `DONE 任务仍包含占位内容`；删掉即恢复绿。

## 适用边界

- 禁令只覆盖 **task plan（`status: DONE`）与 recheck（`result: PASS`/`PASS_WITH_WARNINGS`）**。
  复检记 `result: FAIL` / `PASS_WITH_WARNINGS` 的**未通过**件、以及 `GOAL-*.md`
  与 `MEM-*.md`，都可以正常写 `PENDING`（GOAL 的 EC 状态机就靠它）。
- `PASS_WITH_WARNINGS` 在 `:723` 的集合里 ⇒ 同样受限。
- 匹配是**全文任意位置**，包括引用的判词、别人的状态表、代码围栏内部
  ⇒ 想引原判词时用拆写（如 `` `PENDING` `` 也不行，反引号不豁免）。
- 与 [[MEM-20260923-116-local-m0-green-recipe]] 配套：那条管**怎么让 m0 变绿**，
  本条管**为什么绿了又红**。

## 来源

- `scratch/goal013-c2-m0-final.log`（两条判词逐字）、
  `scratch/goal013-c2-m0-green.log`（改后 23/23 终局）。
- 规则实现：`.cursor/skills/governance-check/scripts/validate.py:705,723`。
- 相关：[[MEM-20260923-117-live-page-equals-read-face-writing-traps]]（同一 cycle 的另一类写法陷阱）。
