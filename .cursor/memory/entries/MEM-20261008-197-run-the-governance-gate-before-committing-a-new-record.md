---
id: MEM-20261008-197
title: "新 PLAN/RECHECK 落地后**立刻**跑治理：先提交后校验会在 CI 红一次（`framework/validate` 缺章节 + 未入 ALL_PLAN）"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-317-goal-033-ec04-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-318-goal-033-ec04-self-bootstrap-closeout.md
supersedes: []
tags: [governance-gate, record-face, ordering-discipline, ci-red, goal-033, plan-317]
---

## 做了什么

GOAL-033 cycle 4 我在本地把验证器跑绿、把两树跑到 `TWO-TREE PASS`，然后**直接提交并推送**
了新建的 `PLAN-20261008-317`。CI 随即判红 —— 不是产品问题，是**记录面结构**：

```
Cursor 治理验证失败:
- 任务计划缺少章节 ## 验收条件: PLAN-20261008-317
- 任务计划未加入 ALL_PLAN: PLAN-20261008-317
```

`framework/validate`（治理 `validate.py`）在 m0 里；它读 `.cursor/plans/**` 的结构契约
（必含章节、ALL_PLAN 投影、DONE 勾选一致性）。我在**写文件之后、提交之前**没有跑它。

## 为什么这样做

**纪律**（与 `MEM-20260928-155`「门必须在记录写入之后跑」同族，但侧重**更早**的一步）：

```text
新 PLAN / RECHECK / MEM 文件落地
  → 立刻跑治理 validate.py（结构面：章节 / ALL_PLAN / 索引 / 勾选投影）
  → 再跑记录面判据（话术 / 凭据 / 结构签名）
  → 再跑全量门
```

三条都要跑，缺任何一步都会被 CI 抓到，而 CI 的反馈循环比本地慢一个数量级。
**提交前跑治理的成本是秒级**；不跑的成本是一次红 + 一次修复提交。

**具体易漏项**（本轮实测）：
- 新 PLAN 的**必含章节**（`## 验收条件` / `## 实施清单` / `## 证据` / `## 状态历史` / `## 影响报告`）；
- 新 PLAN 必须**同轮**进 `ALL_PLAN`，且**状态投影**与 frontmatter 一致
  （改 `status: IN_PROGRESS → DONE` 时要同步把行改成 `| [x] | ... | DONE |`）。

## 怎么做与复现

```bash
# 新增/修改任何 .cursor/plans/** 或 .cursor/memory/** 之后，**提交前**：
uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py
# 期望：Cursor 治理验证通过
```

## 适用边界

- 适用于任何对 `.cursor/plans/**`、`.cursor/memory/**`、`.cursor/rules/**` 的增改。
- 治理绿**不等于**其他门绿：它只覆盖记录面结构契约（章节 / 投影 / 链接 / 凭据扫描），
  产品门与记录面**内容**判据（话术 / 结构签名）仍要各自跑。
- 反过来也成立：**内容**判据绿不代表治理绿（本轮就是内容全绿而治理红）。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-317-goal-033-ec04-self-bootstrap-closeout.md`
- `.cursor/plans/rechecks/RECHECK-20261008-318-goal-033-ec04-self-bootstrap-closeout.md`（W-1）
- CI：`4e59e1f` 的 `quality-ubuntu-latest` 的 `FAILED [framework/validate]`
