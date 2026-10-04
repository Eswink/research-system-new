---
id: MEM-20261005-187
title: "判据的受判面可能被写窄：「声明了⇒有实现」若写成 declared∩implemented，缺实现者永远报不出来"
status: ACTIVE
created_at: 2026-10-05
updated_at: 2026-10-05
scope: repository
confidence: 0.95
review_after: 2027-04-05
source_plans:
  - .cursor/plans/tasks/PLAN-20261005-277-goal-029-ec01-session-tool-called-end-to-end.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261005-278-goal-029-ec01-session-tool-called-end-to-end.md
supersedes: []
tags: [verdict-scope, masking, completion-audit, goal-029, false-green]
---

## 做了什么

GOAL-029 EC-02 的主判据要证「声明了承接 ⇒ 一定有实现注册」。首版把受判面写成：

```python
mine = declared & implemented          # ← 缺陷在这里
missing = [c for c in mine if not has_implementation(c)]
assert missing == []
```

`declared & implemented` **天然排除了缺实现的那些** ⇒ 「声明了但没实现」**在构造上
不可能被报出来**（`missing` 恒为空）。判据、门禁、m0 **全绿**，GOAL 一度记为 ACHIEVED。

完成核对时读判据源码才发现。修成「受判面 = provider 声明的**每一条**，每条要么有实现、
要么在登记表里逐条点名理由」后，它**立刻报出三条真实缺口**：
`claim.read`（已补真实现）、`experiment.read` / `experiment_plan.read`（已从声明面移除）。
同时暴露出更早报出的「承接面 17/46」**含两条假计数** ⇒ 修正为 **15/46**。

## 为什么这样做

这是 `MEM-20260922-160`（不得靠并集掩蔽）的**镜像形态**：那条防的是「用并集把不在射程里的
东西盖住」，本条是「用**交集**把本该受判的东西排出去」。共同点是
**受判面本身被写窄**，于是断言在缩小的集合上恒真。

关键教训：**判据绿 ≠ 判据覆盖了对的东西**。五个 EC 全绿、两树 PASS、m0 23/23、
治理通过 —— 这些**都不能**证明某一条判据的受判面没被写窄；只有回头**读它的受判面**
才抓得到。所以「完成核对」必须核对**判据的覆盖范围**，而不只是核对「判据是否通过」。

## 怎么做与复现

- **写「A ⇒ B」型判据时，受判面取 A（声明的全集），不要取 `A ∩ B`**；
  例外项（实现由别处承担 / 判定不该有实现）走**显式登记表**并逐条点名理由，
  另断言登记表不得含幽灵条目（不在声明面里的登记项判红）。
- **完成核对必做**：逐条读自己新增判据的**受判面表达式**，问「什么情况下这条断言会
  因为集合变小而恒真」。
- 复现：把 `claim_read` 从 `adapters/canonical/read_provider.py` 的 `_TOOL_CAPABILITIES`
  删掉 ⇒ `uv run --frozen --no-sync python -B -m pytest
  tests/architecture/python/test_capability_coverage_is_implemented.py -q -p no:randomly`
  ⇒ **2 failed**（主判据 + 下界断言）；复原 ⇒ 8 passed。

## 适用边界

本仓所有**排他性/完备性**结构判据都适用（「声明了⇒有实现」「实现了⇒有声明」
「每个都有主」「唯一入口」）。**不**适用于纯行为判据（跑一遍看结果，没有受判面集合）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261005-277-goal-029-ec01-session-tool-called-end-to-end.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261005-278-goal-029-ec01-session-tool-called-end-to-end.md`
- 事实：`tests/architecture/python/test_capability_coverage_is_implemented.py` 的
  `test_every_declared_capability_has_an_implementation`（修正前后两版都在 git 历史里）
