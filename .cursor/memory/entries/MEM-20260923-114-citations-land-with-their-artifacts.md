---
id: MEM-20260923-114
title: "引用了另一个文件的记录必须与那个文件同一次提交落地——本地先落产物后落引用方，会把治理红藏到 CI 上"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.93
review_after: 2027-03-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-147-experiments-read-face-in-browser.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-148-experiments-read-face-in-browser.md
supersedes: []
---

## 做了什么（一次真实的 CI 判红）

GOAL-012 cycle 5 把功能面（夹具 + live spec + suite 登记 + `PLAN-147` + `MEM-20260923-113`）
提交为 `d5baf05` 并推送，CI 上 `quality-windows-latest` 与 `quality-ubuntu-latest` 两个 job 判红，
**根因同一条**：

```
Cursor 治理验证失败:
- 工程记忆来源不存在: MEM-20260923-113: .cursor/plans/rechecks/RECHECK-20260923-148-…md
```

即：`MEM-113` 的 `source_rechecks` 指向 `RECHECK-148`，而那份复检**落在下一个提交**里
（本地因为文件已在工作树里，`validate.py` 一直绿）。

## 为什么这样做

治理校验（`.cursor/skills/governance-check/scripts/validate.py`）会检查
`memory_entries` / `latest_recheck` / `child_plans` / `ALL_PLAN` 的**交叉引用可解析**——
判的是「**这一棵树**里引用得通」，而 CI 只看**被推送的那个提交**。所以「产物先落盘、引用方后写」
在本地看不出来，一到 CI 就是红。同类引用面还有：`PLAN.latest_recheck` → 复检文件、
`GOAL.child_plans` → PLAN 文件、`ALL_PLAN` 行 → PLAN 文件。

## 怎么做与复现

- **纪律**：任何带 `memory_entries` / `latest_recheck` / `child_plans` 的记录，
  **必须与它引用的文件放进同一次提交**；若要拆两次提交，就**不要**在第一次里写引用
  （先写文件、后写引用行）。
- **复核**：`uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`
  绿**只对当前工作树成立**；要判 CI 会不会红，得用
  `git stash`/干净 worktree 或直接在**提交后的树**上再跑一遍（本 cycle 的补救就是后者：
  回写提交把 `RECHECK-148` 落盘后同一判据转绿）。
- 分类：这属于**提交切分错误**，不是产品缺陷，也不是判据缺陷 ⇒ 处置是**让引用与产物同源**，
  **不放宽**判据。

## 适用边界

- 只对「文件间引用」的治理判据成立；对行为判据（跑起来才知真假）不适用。
- 与 [[MEM-20260923-112]]（amend 之后必须复测）是同一类错误的两个面：**记录与它的证据必须同时同地成立**。

## 来源

- GOAL-20260923-012 cycle 5；PLAN-20260923-147；RECHECK-20260923-148。
- 实测：CI run 35847860197 的两个 job 日志（逐字判词见上）；回写提交后同判据转绿。
