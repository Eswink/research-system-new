---
id: MEM-20260913-022
title: design-fidelity linux 基线必须在容器内叠加工作树再生（clone 只见已提交内容）
status: ACTIVE
created_at: 2026-09-13
updated_at: 2026-09-13
scope: repository
confidence: 0.9
review_after: 2026-12-13
source_plans:
  - .cursor/plans/tasks/PLAN-20260913-043-reports-integrations-lineage-live.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260913-043-reports-integrations-lineage-live.md
supersedes: []
tags:
  - playwright
  - design-fidelity
  - baseline
  - ci
---

# MEM-20260913-022 — linux design-fidelity 基线再生需叠加工作树

## 做了什么

页面改动后 update design-fidelity 基线（win32 本地 + linux 容器）。首次沿用
cycle 1 的 `scratch/gen_linux_baselines.sh`（容器内 `git clone /work /tmp/ws`），
脚本报 `1 passed`、33 张 linux 全部写出，但 `git status` 显示 linux 基线**无变化**。

## 为什么这样做

根因：`git clone /work /tmp/ws` 只携带**已提交**内容；本 cycle 的页面改动尚在
工作树（未提交），clone 里仍是旧页面，playwright 渲染旧页并再生成**与库中逐字节
相同**的 linux 基线 → diff 为空（看似成功，实则假绿）。若就此提交，CI 的
console-frontend（ubuntu）会因 linux 基线是旧页面而失败。

处置：新脚本 `scratch/gen_linux_baselines_worktree.sh` 先 `git status --porcelain`
列出改动路径，逐条从 `/work` 复制进 clone（tracked 改动 + untracked 新文件），
再 `playwright test design-fidelity --update-snapshots`。实测 overlay 32 路径后，
仅目标 2 路由 × 2 平台共 4 张基线变化，符合预期。

## 怎么做与复现

- 复现（错误姿势）：改动页面后跑 `docker run ... bash /run.sh`（clone 版），
  `git status` 无 diff → 假绿。
- 正确姿势：
  `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*" docker run --rm -v D:/research-system:/work -v D:/research-system/scratch/gen_linux_baselines_worktree.sh:/run.sh mcr.microsoft.com/playwright:v1.56.1-noble bash /run.sh`
  → 输出 `overlaid N changed paths` + 33 张写回；`git status` 显示预期基线变化。
- 校验：改动页面后 linux 基线**必须**出现 diff，否则先查 clone 是否漏了工作树。

## 适用边界

适用于 postcss/浏览器渲染基线的容器内再生（design-fidelity、任何
`--update-snapshots` 且源在工作树未提交的场景）。已提交后再跑 clone 版亦可，
但多 commit 批次习惯先做基线再提交，故默认用叠加版。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20260913-043-reports-integrations-lineage-live.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20260913-043-reports-integrations-lineage-live.md`
- 脚本：`scratch/gen_linux_baselines_worktree.sh`（对照 cycle 1 的 `scratch/gen_linux_baselines.sh`）
