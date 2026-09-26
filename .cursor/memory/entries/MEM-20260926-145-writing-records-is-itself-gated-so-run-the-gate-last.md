---
id: MEM-20260926-145
title: "「写记录」这一步本身会被判据扫到；全量门压在记录之前 ⇒ 记录永远没被门覆盖过（CI 会替你发现）"
status: ACTIVE
created_at: 2026-09-26
updated_at: 2026-09-26
scope: repository
confidence: 0.9
review_after: 2027-03-26
source_plans:
  - .cursor/plans/tasks/PLAN-20260926-194-goal-019-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260926-195-goal-019-closeout-recheck.md
supersedes: []
tags: [gate-ordering, goal-closeout, record-face, wording-gate, multi-tree-recheck, attribution, goal-019, ec-05]
---

## 做了什么

GOAL-019 收口的**多面复检**发现：cycle 2 的**记录提交** `75155b2` 把一个**真红**带进了 main，
而它的**本地全量 m0 是绿的**——因为 m0 跑在**记录写入之前**。

| 面 | 提交 | 定向判据 | M0 |
| --- | --- | --- | --- |
| 交付 tip | `957fe05`（4 文档 + 判据） | **1359 passed / exit=0** | **八 job 全 success** |
| 记录 tip | `75155b2`（+6 个 `.cursor/**` 文件） | **exit=1**：`test_reproducibility_wording.py::…test_no_affirmative_fully_reproducible_claim` | **failure**（`quality-ubuntu-latest` + `quality-windows-latest`） |
| 终态（修后） | — | exit=0 | 见 RECHECK-195 |

`git diff --name-only 957fe05..75155b2` = **恰好 6 个记录文件**（零产品/文档代码）⇒ 归因无歧义。

## 为什么这样做

1. **记录的用词在判据的扫描面内。** `tests/architecture/python/test_reproducibility_wording.py`
   的 `_SCAN_ROOTS` **包含 `.cursor/plans`** ⇒ 记录里"列举被禁词表"这种写法会被当成**宣示**。
   那条判据的豁免是「**加引号**的提及」或「同一行含**否定标记**」——本仓既有记录正是这么写的
   （`「完全可复现」`、`不得…简称为「完全可复现」`）；新记录写成了裸词表 ⇒ 判红。
2. **「先跑全量门、后写记录」= 记录从未被门覆盖。** 本地 m0 的证书只证明**它跑的那一刻**
   那棵树；之后每一次记录写入都是**未受门的新增面**。这不是"运气不好"——是这个顺序的**必然**。
   ⇒ 收口/回写的正确顺序是 **写记录 → 跑记录面判据 → 全量门**；若必须最后补一行（例如把 m0
   终态行回填进记录），那一行要用**定向判据 + 治理 + DOCS-CHECK** 再盖一次。
3. **多面（按提交切面）比"同提交两棵树"更快定位归因。** 「同提交两棵树同结论」证明的是
   **可复现**；但当红已经出现时，真正要回答的是「**哪个提交引入的**」。
   把「交付 tip / 记录 tip / 终态」三面摆在一起 + 一份 `A..B` 的文件清单，
   归因从"推理"变成"读表"。**两种比较都要做**：前者证明判据稳定，后者证明归因唯一。
4. **干净 worktree 里跑 pytest 必须沿用同一条调用口径。** 直接调 `.venv/Scripts/python.exe`
   ⇒ `lint-imports` 不在 PATH ⇒ **14 条已知假红**（`test_dependency_boundaries.py` 一族的
   `RuntimeError: lint-imports executable is unavailable`）。同一提交在两种口径下
   `1359 passed` vs `1345 passed / 14 failed`——假红会让"两棵树都红"掩盖掉真红。
   **判据：跨树比较前先把调用口径统一（本仓用 `uv run --frozen --no-sync`）。**

## 怎么做与复现

```bash
# 1) 记录 tip 与交付 tip 的差集（归因唯一性）
git diff --name-only <交付 tip>..<记录 tip>
# 2) 多面复检（交付 tip / 记录 tip / 终态各跑一遍同一组判据）
uv run --frozen --no-sync python -B scratch/goal019-ec05-multitree.py
# 3) 干净树同提交可复现（两个独立 checkout，同一提交）
for T in D:/rs-goal019-deliv D:/rs-goal019-mirror; do (cd $T && uv run --frozen --no-sync python -B -m pytest tests/architecture/python tests/tooling -q --tb=no); done
# 4) 记录面判据（写记录之后必须再跑一次）
uv run --frozen --no-sync python -B -m pytest tests/architecture/python tests/tooling -q
```

## 适用边界

- **只对"判据会扫记录"的那一类成立**：本仓已知 `.cursor/plans` 在
  `test_reproducibility_wording.py` 的扫描面内；是否还有别的判据扫记录面**未逐一核实**
  ⇒ 稳妥做法是收口后跑**整个 `tests/architecture/python` + `tests/tooling`**，而不是只跑治理。
- **多面复检比较的是"每个提交面自身的结论"**，不是"同一棵树上的 A/B"；
  它不能替代"同提交两树同结论"（两者互补）。
- **干净 worktree 是只读用法**：脚本只写主树的 `scratch/`；在干净树里按压后必须
  校验 sha256 还原（本轮实测 `0cb60c3ee79ff14f` 前后一致）。
- **CI 的 `quality-*` job 覆盖整份 pytest**，因此记录面的红**一定**会在 CI 上出现——
  不能靠"CI 绿"来推断记录面没事，只能靠"记录写完之后又跑过一遍"。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260926-194-goal-019-closeout-recheck.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260926-195-goal-019-closeout-recheck.md`
- 脚本与日志：`scratch/goal019-ec05-multitree.py` / `scratch/goal019-ec05-{deliv,records,main}.out` /
  `scratch/goal019-c3-ci-poll.log`
- 相关记忆：`MEM-20260925-141`（判据自身恒真）、`MEM-20260926-142`（按压要落在判据自己的块内）、
  `MEM-20260926-144`（同源文档要有逐字声明句 / 按压要报实际判红的集合）、
  `MEM-20260925-139`（收口需要两棵树与两条终态行）
