---
id: MEM-20261008-202
title: "「没有分数」不等于「分数很低」：缺来源必须维持 fail-closed，回落默认分是把两件相反的事混成一件"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.92
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-327-goal-035-ec03-review-score-linkage-on-the-run-path.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-328-goal-035-ec03-review-score-linkage.md
supersedes: []
tags: [acceptance-criteria, review-score, fail-closed, judge-linkage, goal-035]
---

## 做了什么

`REVIEW_SCORE` 判据（域实现、判词、fail-closed 分支）**早就存在**，但产品路径从不喂分：
全仓 `review_score=` 只出现在 tests，出厂合约 `examples/` 里 `REVIEW_SCORE` **零声明** ⇒
任何合约声明它都会一律判负（`review score unknown`）。

本轮让分数**有来源且来源被点名**：合约在判据里用 `metric` 写明结构化输出的字段路径
（如 `review_decision.score`），产品路径按这条**声明**的路径取数；判定仍走既有域函数。

## 为什么这样做

**「没有评审结论」与「评审结论很差」是两件相反的事。** 缺来源时回落一个默认分（哪怕 0.0）
会把前者伪装成后者；回落 1.0 则更糟（把没评审的当成满分）。因此缺来源**必须**维持既有
fail-closed 判词，而判据要**同时**断言两件事实：判词是 `review score unknown`，**且**判词里
没有分数、没有算子（回落默认分会让这两样出现）。

同理：分数来源必须是**声明**的（`metric` 路径），不是按名字猜的（`score` / `confidence` /
`rating` 都有人这么叫）；猜错的后果是读到**别人的数**进判据 —— 那是另一种伪装。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_review_score_linkage_on_the_run_path.py -q   # 3 passed
# ① score 0.95 ⇒ PASS，判词 `review score 0.95 GTE 0.8`
# ② score 0.5  ⇒ FAILED，判词 `review score 0.5 GTE 0.8`（点名分数）
# ③ 无 score   ⇒ FAILED，判词 `review score unknown`（无分数无算子）
```

按压：把取数函数末尾改成回落 `Decimal("1")` ⇒ **缺来源臂判红**（本该 fail-closed 的 run 假绿）。

**「不改既有受判面」的具体做法**：不要给既有契约加判据（那会让它的既有夹具变成「缺分数」
而连环判负），**新增**一份合约 + 一份协议 —— 实测既有 `examples/contracts` 只增 27 行、
0 删除，全量定向套件 2372 passed。

## 适用边界

- 适用于任何「外部/模型给一个数，判据拿它裁决」的场景（评审分、质量分、覆盖率、置信度）。
- **不**适用于「没有值就该按最坏情况处理」的场合 —— 那时请显式声明默认值与理由，
  而不是让取数函数静默回落。
- 分数**正确性**不在本条的声明范围内：本条只保证「有来源、三态可判、缺来源不伪装」。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-327-goal-035-ec03-review-score-linkage-on-the-run-path.md`
- `.cursor/plans/rechecks/RECHECK-20261008-328-goal-035-ec03-review-score-linkage.md`
