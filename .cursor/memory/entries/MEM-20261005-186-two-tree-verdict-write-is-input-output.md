---
id: MEM-20261005-186
title: "两树入口的判词落点是「输入即输出」：验证器不得读它自己会被写回的文件（否则永不收敛）"
status: ACTIVE
created_at: 2026-10-05
updated_at: 2026-10-05
scope: repository
confidence: 0.95
review_after: 2027-04-05
source_plans:
  - .cursor/plans/tasks/PLAN-20261005-281-goal-029-ec04-05-two-tree-archives-and-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261005-282-goal-029-ec05-self-bootstrap-closeout.md
supersedes: []
tags: [two-tree, verdict-archive, circular-dependency, goal-029, plan-281, false-red]
---

## 做了什么

GOAL-029 EC-05 的收口验证器起初**读**两树入口写回的判词归档
（`.cursor/plans/goals/evidence/GOAL-*-verdict-{current,clean}.txt`）来做
`ec04-archives-have-the-same-sha256` 断言 —— 即「验证器读的是它自己这一趟会被覆盖的文件」。

实测后果：两树复检首跑 **current 判红 / clean 判绿**，两棵树读到的是**不同的历史残留**；
而且**永不收敛**：这一次写回的内容成为下一次的输入。

## 为什么这样做

`tools/two_tree_recheck.py` 的 `dump_verdicts` 在**跑完两棵树之后**才把判词写到
`--verdict-current/--verdict-clean` 指定的路径。若断言脚本（作为 `--script` 传入）
同时读那两个路径，就构成 **输入 = 输出** 的闭环：

- 两棵树**先后**执行同一个脚本，第一次执行时归档还是上一轮的内容 ⇒ 两棵树看到的**不同**；
- 无论怎么重跑，写回与读取互相污染 ⇒ 该断言永远不可能稳定通过。

## 怎么做与复现

- **判词归档的形态与一致性由专属判据承担**，不放进尝试验证器：
  `tests/tooling/test_two_tree_verdicts_are_archived.py`（跑在门禁里、在两树写入之后）。
- **验证器只判 GOAL 自己的交付物**（源码结构、判据在位、记录面），不判「这次运行的产物」。
- 复现：把归档断言放回验证器并跑
  `tools/two_tree_recheck.py --script tools/verify_goal029_closeout.py --script-mode shared`
  ⇒ 两棵树判词不同（`DIFF ec04-archives-have-the-same-sha256`）；移除后 ⇒ `TWO-TREE PASS`，
  两树各 54 判词、`sha256` 相同（实测 `db4faa07d42532d0…`）。

## 适用边界

本仓任何**被两树入口驱动**的复检脚本都适用：脚本是**消费者**，两树入口是**生产者**，
脚本不得消费本次运行的产物。**不**适用于跑在门禁里、在两树写入之后才执行的判据
（那类读归档是正确用法）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261005-281-goal-029-ec04-05-two-tree-archives-and-self-bootstrap-closeout.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261005-282-goal-029-ec05-self-bootstrap-closeout.md`
- 事实：`tools/two_tree_recheck.py::dump_verdicts`（写盘发生在两棵树都跑完之后）
