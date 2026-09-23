---
id: MEM-20260923-122
title: "Windows 会剥掉尾随的点：`...` 这类链接 target 在本地判绿、在 Linux/CI 判红（平台相关假绿）"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-24
scope: repository
confidence: 0.95
review_after: 2027-03-24
source_plans:
  - .cursor/plans/tasks/PLAN-20260923-153-frontend-criteria-disclosure-judge.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-154-frontend-criteria-disclosure.md
supersedes: []
---

## 做了什么

GOAL-20260923-013 cycle 4 的 CI 首轮判红 `quality-ubuntu-latest`，判词是一条
`Markdown 本地链接不存在: .cursor/plans/rechecks/RECHECK-2026…md -> ...`——
那份记录里我写了链接形状的字面量（方括号紧接圆括号），它的 target 恰好是 `...`。

**为什么本地 m0 看不见这条红**：`validate_bundle.py` 的链接判据把 target 交给
`(doc.parent / target).resolve()` 再 `exists()`。Win32 **剥掉路径末尾的点**，
`...` 归一化成「本目录」⇒ `exists()` 为真 ⇒ 本地判绿；Linux 上 `...` 是普通名字
⇒ 判红。**这不是判据的问题**，判据在 Linux 上是对的。

## 为什么这样做

这类「本地绿 / CI 红」最容易读成「CI 环境问题」而重跑，从而把一条**真缺陷**蒙过去。
知道它的机制后可以一眼认出：**凡是判词里出现「尾点是点」的路径，先去查 `...` 写法**。

## 怎么做与复现

- 复现口径（机器可判）：扫**已跟踪**的 `.md`，抽取链接 target，报**basename 会被 Win32
  归一化**的那些（`name != name.rstrip(". ")`）；`.` / `..` 解析到真实目录，属合法、跳过。
  本仓实测：`...` 一处（本轮已修），另一个 `../` 是合法 target。
- 该扫描已落进 `scratch/verify_goal013_c4.py` 的 H1 判组（`scratch/` 不进仓库）。
- **写记录时的写法纪律**：要示范「链接形状」就把方括号与圆括号**分开**写
  （`` `[...]` 紧跟 `(...)` ``），**不要**把它们连成一个 Markdown 链接形状的字面量
  —— 那本身就是这条判据要抓的东西。
- 边界：**Windows 本地 m0 无法覆盖这一类**（判据本身在 Linux 上才生效）⇒ 这类红
  必须靠 CI 兜，别把它归因成 flake。

## 适用边界

- 只对「靠文件系统 `exists()` 解析路径」的判据成立（Markdown 链接、docs 引用等）；
  纯字符串判据不受影响。
- 同理适用于以**尾随点 / 尾随空格**结尾的 target（`foo.md.`、`dir.`），Windows 一律归一化。

## 来源

- CI run `35909318756` 的 `quality-ubuntu-latest` job（`validate_bundle` 判红那条），
  日志在 `scratch/goal013-c4-ci-ubuntu.log`（本机留存，`scratch/` 不进仓库）。
- 修好后的本机复扫与判组 H1：`scratch/verify_goal013_c4.py`。
- 相关记录：`RECHECK-20260923-154` 第五节（CI 首轮的第三条红）与第六节（H1 口径）。
