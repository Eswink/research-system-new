---
id: MEM-20260919-085
title: "GOAL 的 EC 表（frontmatter）会与迭代日志/状态历史漂移：回写时必须把 EC 表行与日志行当同一笔改动"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-113-goal-007-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-113-goal-007-closeout-recheck.md
supersedes: []
tags:
  - goal-record
  - closeout
  - record-drift
  - verification-script
---

# GOAL 记录漂移（GOAL-20260919-007 / cycle 7 收口复检）

## 做了什么

收口复检脚本（三层判据的 C 层）逐行回读 GOAL frontmatter 的 EC 表，抓出 **EC-04 / EC-05
的 `status` 仍是「未完成」枚举、`evidence` 仍是空串** —— 而迭代日志行、状态历史、两条
RECHECK 都写着 PASS。也就是说：**同一个 GOAL 文件里，机器可读的那一半与叙述的那一半
互相矛盾**，而且矛盾已经存在了两个 cycle。

## 为什么这样做（可复用结论）

1. **漂移不是一次意外，是反复出现的失败模式**：GOAL-006 收口时出现过**同一类**问题
   （EC-03 / EC-04 的 `status` 在 cycle 3 / cycle 4 回写时漏改）。两个 GOAL、同一形态 ⇒
   回写 SOP 本身有洞：cycle 回写容易只改「迭代日志 + 状态历史」，忘了 frontmatter 的
   EC 表行（它在文件顶部，离你正在编辑的日志行很远）。
2. **动作**：把「EC 表行」与「迭代日志行」当作**同一笔改动**——回写时先改 EC 表（status +
   evidence），再写日志行，最后用只读脚本回读一遍（脚本比人眼可靠）。
3. **只读脚本是最便宜的护栏**：`scratch/verify_goal0NN_closeout.py` 的 C 层直接断言
   「每条 EC 的 `status` 必须是 PASS」，一次运行就把两处漂移都抓出来。收口时写它、平时
   也可以随时跑。
4. 修正是**记录面更正**，不改任何门禁/断言；但必须写明「漏改了两个 cycle」，否则读者会
   以为 EC-04 / EC-05 是收口才通过的。

## 怎么做与复现

- 回读：`uv run --frozen --no-sync python -B scratch/verify_goal007_closeout.py` ⇒
  80 checks / 0 failures（修 EC 表 + 补 RECHECK-113 之后）；修之前会在 C 层报
  `GOAL EC-04 状态不是 PASS: PENDING`。
- 定位漂移源头：`git log -L <EC-04 的 status 行>:.cursor/plans/goals/GOAL-….md` 显示该行
  **自建档后没被改过**，即可确认是哪几个 cycle 漏改。

## 适用边界

- 本记录只覆盖 GOAL 的 EC 表；GOAL 正文的其他数字（如「当前续点」）也可能漂——同一脚本
  的 C 层顺带断言了 `latest_recheck` / child_plans / ALL_PLAN 投影，但**正文措辞**仍需人工。
- 治理 validator（`.cursor/skills/governance-check/scripts/validate.py`）**不检查** EC 表的
  status 值 ⇒ 这类漂移不会被它拦下（它查的是结构合规与交叉引用存在性）。

## 来源

- `.cursor/plans/goals/GOAL-20260919-007-configurable-runtime-and-egress-gate.md`（EC 表修正）
- `.cursor/plans/rechecks/RECHECK-20260919-113-goal-007-closeout-recheck.md` W-9
- 先例：GOAL-20260918-006 收口时的同类更正（`RECHECK-20260918-106`）
