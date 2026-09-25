---
id: MEM-20260925-139
title: "收口复检要交两样东西：两棵树同一个结论 + 两个不可互换的 m0 终态行"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-178-goal-016-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-179-goal-016-closeout-recheck.md
supersedes: []
tags: [closeout, gate, m0, worktree, goal-016, ec-06]
---

## 做了什么

GOAL-016 的 **EC-06（收口复检）**：写了一个**不复用 GOAL 叙述**的独立复检脚本
`scratch/goal016-ec06-closeout-recheck.py`（六个 EC 各自「结构断言 + 判据文件子进程实跑」
两路同时成立才算 PASS），在**当前树**与**干净 `git worktree` checkout** 上跑出**同一个结论**；
并取到 **两个** m0 终态行（as-is 22/23 = `R-3`；代管后 23/23）。

## 为什么这样做

- **收口结论不能只由「本轮的证人」作出**：同一批记录既写过程又下结论，就没有独立面。
  复检脚本的价值在于**换一个执行者**重导一遍结论。
- **「当前树绿」不等于「提交的树绿」**：工作树里可能有未提交的改动、并发写者的文件、
  被 gitignore 的残留。⇒ 必须在**检出出来的那棵树**上再跑一次，否则结论覆盖的不是
  仓库里那个对象。**本仓的 `pythonpath = ["."]`** 让这件事有意义：pytest 用 rootdir 入
  `sys.path` ⇒ 在 checkout 里跑就是**跑那棵树自己的代码**（若项目是 editable 安装指向
  工作树，这个验证就会变成假的）。
- **两棵树必须能同跑**：所以复检脚本要接受 `--root`，且**不依赖**被测树的任何未提交内容；
  脚本自身放 `scratch/`（gitignored）⇒ 干净 checkout 里没有它也不影响（从工作树调用、
  用 `--root` 指向 checkout）。
- **m0 有两个身份不同的终态行**：as-is（仓库外 gitignored 文件触发红）与代管后（临时移出
  该文件）。**两者不可互换**，行数也能区分：`PASS [` 计数里**不含**
  `release-assets-immutable` ⇒ as-is 22/23 对应 23 行、代管 23/23 对应 24 行。
  含糊写一个「23/23」就等于把 as-is 的红藏起来。
- **判据要能红**：复检脚本在**终态表未落盘**时必须报错（实测报出 13 条缺失）。
  写「有表才逐条查」会得到一个**恒真**断言——表被整段删掉反而全绿。

## 怎么做与复现

- **写脚本**：每个 EC 两条腿——① 本脚本自己**重新读树**断言结构事实（模板单一来源 /
  策略面相对基线 diff 为空 / lockfile 解析版本 / ADR 的 `Status` 与非 ASCII 双向清单 /
  受保护文档的标记词 / 记录与终态表在位）；② 该 EC 的判据文件用
  `<tree>/.venv/Scripts/python.exe -B -m pytest -q <literal paths>` 子进程跑，
  `cwd = <tree>`。两腿都过才 PASS。
- **两树**：`git worktree add <tmp> <sha>` ⇒ 跑
  `<worktree>/.venv/...` 不存在时用**主仓的**解释器（`pythonpath` 仍指向被测树）。
  比对两份输出：逐 EC 结论逐字一致。
- **as-is m0**：直接 `run_all_checks.py --profile m0 --keep-going`（**不要**代管），
  如实记下 `FAILED: n check(s)` 与红项名。
- **代管 m0**：`tools/quarantine_and_run_m0.py --path <gitignored file> --log <log>`，
  记下终态行 + 逐字节复核三元组（size / mtime_ns / sha256）。
- **记录时序**：m0 必须在**冻结树**上跑；跑完之后的补写只能是**记录面**，
  并在记录里写明这一时序（否则终态行的树身份就不清）。

## 适用边界

- **两行不可互换、不可合并**：任何地方只写「23/23」而不说哪棵树 / 哪种跑法，
  都是把 as-is 的红藏起来。
- **`scratch/` 不入库**：复检脚本与日志都不进 git（这是既有约定）；
  所以**可复核性靠记录里的命令 + 输出片段**，而不是靠脚本本身在仓库里。
- **复检脚本会随被测面漂移**：它硬编码了文件路径与期望值（如非 ASCII 路径数 30、
  `vite` 版本）。这些值变了脚本要跟着改；**改脚本去迁就现实**必须和「改判据」一样当作
  实质改动来审。
- **`Path.walk(followlinks=…)` 在本仓的解释器上不可用**，用 `os.walk(path, followlinks=False)`
  ——`node_modules` 里的悬空 pnpm 链接会让 `Path.rglob` 直接炸。
- 结论绑定**被测树的那个 SHA**；两棵树不同 SHA 时先确认差异是否影响判据。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-178-goal-016-closeout-recheck.md`（WP1–WP6）
- `.cursor/plans/goals/GOAL-20260925-016-decisions-landed-and-threat-model.md`（EC-06 + 13 项 `D-NN` 终态表）
- `scratch/goal016-ec06-closeout-recheck.py`（复检脚本，不入库）
- `scratch/goal016-c6-recheck-worktree.txt`、`scratch/goal016-c6-m0-as-is.log`、
  `scratch/goal016-c6-m0-quarantined.log`（输出留档，不入库）
- `docs/architecture/LOCAL_GATE_PROTOCOL.md`（m0 跑法与代管口径）
