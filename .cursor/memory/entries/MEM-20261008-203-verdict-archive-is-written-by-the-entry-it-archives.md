---
id: MEM-20261008-203
title: "判词归档由被归档的那个入口写出：首轮必然红，别为让首轮变绿删掉存在性断言"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-329-goal-035-ec04-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-330-goal-035-ec04-self-bootstrap-closeout.md
supersedes: []
tags: [two-tree-recheck, verdict-archive, bootstrap-timing, closeout, goal-035]
---

## 做了什么

收口复检的**判词归档**（`.cursor/plans/goals/evidence/<goal>-verdict-{current,clean}.txt`）是
由 `tools/two_tree_recheck.py` 在跑完两棵树后用 `--verdict-current / --verdict-clean`
**写出来**的；而收口验证器（`tools/verify_goal035_closeout.py` 一族）里有一条断言是
「归档在树且非空、`CR=0`」。两条事实合起来 ⇒ **首轮两树复检必然红**：跑之前归档还不存在。

## 为什么这样做

这不是缺陷，是**自举时序**：断言面与产出面是同一套东西。实测形态是固定的：

| 轮次 | `--base-ref` | 读数 |
| --- | --- | --- |
| 首轮 | 归档**尚未生成**的提交 | 两路判词逐字节相同，红项**仅**两份归档缺失 |
| 次轮 | **含归档**的提交 | `TWO-TREE PASS`，两路 `sha256` 相同 |

**危险的动作**是「首轮红了 ⇒ 把归档存在性断言删掉（或放宽成警告）」—— 那会把
「归档从来没写出来」和「归档写出来了」变成同一个结论，正是这类断言存在的理由。
正确处置：**保留断言**，在复检记录里把两轮读数**如实登记**（首轮 = bootstrap 时序，
次轮 = 通过），并把「首轮为什么红」写进记录（否则后来者把首轮红误读成失败）。

## 怎么做与复现

```bash
# 首轮：归档落点由入口写出（此轮判词里含「归档缺失」两条红，属预期）
uv run --frozen --no-sync python -B tools/two_tree_recheck.py \
  --script tools/verify_goal035_closeout.py --root . --script-mode shared \
  --base-ref HEAD --verdict-current .cursor/plans/goals/evidence/GOAL-…-verdict-current.txt \
  --verdict-clean .cursor/plans/goals/evidence/GOAL-…-verdict-clean.txt -- --verdict-only
# 次轮：把首轮产出的归档提交，再跑一次同一命令（--base-ref 指向含归档的提交）⇒ TWO-TREE PASS
```

配套两条纪律：**不读归档内容做一致性断言**（输入即输出 ⇒ 永不收敛；一致性由入口自己的
`COMPARE` 回答），**判词行不含任何树的绝对路径**（两树入口会拒绝，属正确拒绝）。

## 适用边界

- 适用于任何「被归档的对象 = 归档它的工具」的自举场景（收口验证器、判词归档、清单生成器）。
- **不**适用于断言面与产出面分离的场景 —— 那里首轮红就是真红，别用本条做借口。
- 记录里必须**同时**写首轮与次轮读数；只写「TWO-TREE PASS」会掩盖首轮红的真实原因。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-329-goal-035-ec04-self-bootstrap-closeout.md`
- `.cursor/plans/rechecks/RECHECK-20261008-330-goal-035-ec04-self-bootstrap-closeout.md`
- 先例：`RECHECK-20261008-318`（GOAL-033）、`RECHECK-20261008-322`（GOAL-034）同款两轮登记
