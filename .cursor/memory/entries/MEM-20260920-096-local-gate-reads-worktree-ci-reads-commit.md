---
id: MEM-20260920-096
title: "本地门读的是工作树、CI 读的是提交：改写未进暂存区 ⇒ 本地绿而 CI 红（GOAL-009 cycle 1 的 framework/validate 红就是这么来的）"
status: ACTIVE
created_at: 2026-09-20
updated_at: 2026-09-20
scope: repository
confidence: 0.9
review_after: 2027-09-20
source_plans:
  - .cursor/plans/tasks/PLAN-20260920-121-first-live-sampling-run.md
  - .cursor/plans/tasks/PLAN-20260920-122-anthropic-surface-boundary-decision.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260920-121-first-live-sampling-run.md
  - .cursor/plans/rechecks/RECHECK-20260920-122-anthropic-surface-boundary-decision.md
supersedes: []
tags:
  - governance
  - validator
  - staging
  - local-gate
  - ci
  - goal-009
---

# 本地门读工作树、CI 读提交（GOAL-009 cycle 1）

## 做了什么

记录一次**真实的 CI 红**及其根因，因为它属于「本地门怎么骗过你」这一类，会重复发生：
GOAL-009 cycle 1 的推送 `e16e458` 让 CI 的 `quality-ubuntu-latest` / `quality-windows-latest`
两个 job 红，红项是 `framework/validate`（治理 validator），报
`MEM-20260920-094` 缺 `## 做了什么` / `## 为什么这样做` / `## 怎么做与复现` / `## 适用边界` / `## 来源`。

**CI 是对的。** 那个条目在本地**已经修好**了，但**那次改写没有进暂存区**：
提交进去的仍是旧形态（`## 事实一/二/三`），而本地 validator **绿**是因为它读了
**未提交**的工作树文件。修法是以独立提交补上改写（`86e77d8`），
**不是**放宽 validator。

## 为什么这样做

- 这条红**看起来**像「validator 抽风 / 环境差异」，实际上是一个**暂存遗漏**。
  如果不把根因写下来，下次同族红的第一反应会是去查环境或去查 validator 版本。
- 它与 [[MEM-20260920-093]]（干净 checkout 封印）是**互补**的两面：
  那条说的是「本地工作树**干净**时仍要验干净 clone」，这条说的是
  「本地工作树的改动**可能根本没提交**」。两者都会让「本地绿」失去意义。
- GOAL-008 收口时也栽在同一个形状上（**frontmatter 的 EC 状态**与正文状态表不一致，
  表改了 frontmatter 没改，validator 钉住）——**同一类漏改，两次都由 validator 抓到**，
  这正是不把 validator 只放在本地的理由。

## 怎么做与复现

**判据（推 CI 之前自查）**：对**本轮所有记录类改动**（`.cursor/**` 的 PLAN / RECHECK /
MEM / GOAL / ALL_PLAN）确认「工作树 == 暂存区 == 提交」三者一致：

```bash
# 1) 还有没有未暂存的记录改动？（有 ⇒ 你正在重演本条）
git status --short .cursor

# 2) 关键：让 validator 读**提交进去的那份**，而不是工作树
git stash push -- .cursor          # 或先 commit
uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py
git stash pop
```

**为什么要用 `git stash` 而不是只跑一次 validator**：validator 在**工作树**上跑，
所以「本地绿」**不能**推出「提交绿」。要判提交，就得让 validator 面对提交的那份内容。

**红项识别**：`framework/validate: exit 1` + `工程记忆缺少章节 …` / `GOAL 仍有未通过退出标准`
这类文案 ⇒ 先查**暂存**，再查内容。

## 适用边界

- **适用于**：本地绿而 CI 红的**记录/治理类**门禁（validator、DOCS-CHECK、bundle 校验）；
  以及任何「本地检查通过了但 CI 说没有」的困惑。
- **不适用于**：产品代码的 lint/typecheck/test——那些跑的就是工作树里的**源码**，
  与暂存状态无关（`git add` 与否不改变 pytest 读到什么）。
- **不要**把这条读成「validator 太严」：两次抓到都是**真缺陷**，
  处置始终是**修记录**，不是调门禁。相关：[[MEM-20260920-093]]。

## 来源

- 红：CI run `35517481162`（`e16e458`）的 `framework/validate` 输出
  （`quality-ubuntu-latest` 与 `quality-windows-latest` 同一条）
- 修：提交 `86e77d8`（把 MEM-094 的改写真正提交进去）
- 复检：`.cursor/plans/rechecks/RECHECK-20260920-122-anthropic-surface-boundary-decision.md` 的 **W-6**
- 目标：`.cursor/plans/goals/GOAL-20260920-009-live-sample-and-anthropic-surface-closure.md`
