---
id: MEM-20260927-153
title: "复检条款写明的每一路都要各自留档：只跑当前树而宣称「两树同结论」会被判负——补跑配方（worktree + --root + 共用解释器 + 判词 sha256）"
status: ACTIVE
created_at: 2026-09-27
updated_at: 2026-09-27
scope: repository
confidence: 0.95
review_after: 2027-03-27
source_plans:
  - .cursor/plans/tasks/PLAN-20260927-209-goal-021-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260927-210-goal-021-closeout-recheck.md
supersedes: []
tags: [closeout-recheck, two-tree, verdict-parity, process-defect, goal-021, ec-05]
---

## 做了什么

GOAL-021 的 EC-05 条款①要求复检脚本对「**当前树 + 干净 checkout**」跑出**同结论**（判词列逐行相同）。
首轮**只跑了当前树**，且**未**在 RECHECK 的「未复核的面」里登记该跳过，却随 EC-05 一起记 PASS
⇒ 被完成核验判为**未达成**（「未实跑不得记 PASS」）。**本轮补跑**并留档：

- **当前树**：28 行判词全 PASS；
- **干净 checkout**（`git worktree add --detach ../goal021-clean-tree HEAD`）：28 行判词全 PASS；
- `diff` **IDENTICAL**；两个判词文件 `sha256` **相同**
  （`5bb9bc08398eac789f9a07814b71b0586f7b1b34252a3c3cbb797efe119487f3`）；
- 按压后**两树均干净** ⇒ 逐字节复原在两树都成立。

## 为什么这样做

- **「跑了一路、结论看起来一样」不能替代第二路**。条款把两路**并列写明**时，
  每一路都是**独立的证据面**：第一路证明「当前树成立」，第二路证明「**提交后的树**也成立」
  （排除「结论依赖工作树里的未提交产物 / 本地残留」这类可能）。
- **跳过本身要登记**。即使当时判断「没必要跑」，也必须写进「未复核的面」——
  **静默跳过 + 记 PASS** 是本次被判负的直接原因。
- **两树必须共用解释器**：干净 checkout 没有自己的 `.venv`，现场建会超时，
  而且**比的是两套环境**（承 GOAL-020 的既有教训）⇒ 用**主树**的
  `.venv/.../python`（等价 `uv run --frozen --no-sync`）。
- **判词要比「行」而不是比「整份输出」**：整份输出含耗时 / 路径 ⇒ 天然不同。
  做法：脚本加 `--verdict-only`（只打印 `PASS/FAIL\t<标签>`）⇒ `diff` 可直接用，
  `sha256` 可直接比对。**注意**：跑 pytest 的那一面仍会有耗时差异，
  因此**判词行里不得含耗时**（本轮 `record()` 在 verdict-only 模式下不打印 detail）。

## 怎么做与复现

```bash
# 1) 干净 checkout（同 tip、独立目录）
git worktree add --detach ../goal021-clean-tree HEAD

# 2) 两路判词（脚本需支持 --root 与 --verdict-only）
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec05-closeout-recheck.py \
  --verdict-only > scratch/goal021-c5-verdict-current.txt
PYTHONPATH=. uv run --frozen --no-sync python -B scratch/goal021-ec05-closeout-recheck.py \
  --root ../goal021-clean-tree --verdict-only > scratch/goal021-c5-verdict-clean.txt

# 3) 逐行比对 + 字节比对
diff scratch/goal021-c5-verdict-current.txt scratch/goal021-c5-verdict-clean.txt
sha256sum scratch/goal021-c5-verdict-current.txt scratch/goal021-c5-verdict-clean.txt

# 4) 收尾（干净 checkout 不留痕）
git worktree remove --force ../goal021-clean-tree
```

## 适用边界

- 适用于**任何**写明「两树 / 两环境 / 两入口同结论」的条款；只写「跑复检」而无对照要求的，
  单路即可（但**范围要在记录里写清**）。
- WORKTREE 方式**不改主树**；若用 `git clone` 或拷贝目录，注意 `.venv` / `node_modules`
  是否被带过去 ⇒ 可能引入**第三套环境**，反而污染对照。
- 「判词相同」证明的是**该脚本的断言**在两树一致；它**不**证明两树的**行为**处处相同
  （那要各自实跑行为套件）。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260927-209-goal-021-closeout-recheck.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260927-210-goal-021-closeout-recheck.md`（`W-0`）
- 留档：`scratch/goal021-c5-verdict-current.txt` / `-clean.txt`
- 相关：[[MEM-20260927-152]]（同为收口复检自身形态的教训）、
  `MEM-20260925-139`（既有「收口需要两棵树与两条终态行」条目）
