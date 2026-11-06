---
id: RECHECK-20261107-107
slug: four-targets
title: GOAL-107 复检 —— 四靶并行（前端补全 / 引用分布 / 外部评审面板 / 脚本执行权威）
status: VERIFYING
result: null
created_at: 2026-11-07
updated_at: 2026-11-07
plan_id: PLAN-20261107-107
parent_goal: GOAL-20261107-107
owners:
  - root-agent
verify_paths:
  - apps/web/src/features/reports/ManuscriptPanel.tsx
  - apps/web/src/features/projects/ProgramsSection.tsx
  - apps/web/src/api/types.ts
  - packages/application/deliverable/citation_distribution.py
  - packages/application/deliverable/manuscript_panel.py
  - packages/application/experiments/script_authority.py
  - packages/application/experiments/governed.py
  - docs/architecture/MANUSCRIPT_QUALITY.md
  - tools/verify_goal107_closeout.py
  - tools/goal107_closeout_assertions.py
---

# RECHECK-20261107-107

## 复检范围

GOAL-20261107-107 的十四条 EC 逐条取证。**两路以上**（`verify_paths` 列出的每个文件都是
一条独立的取证路径；产品面与判据面各取一次）。

四靶的分工与各自的**射程边界**（本轮把边界写在前面，收口时逐条核对有没有越界）：

| 靶子 | EC | 本轮**交付**什么 | 本轮**不**宣称什么 |
| --- | --- | --- | --- |
| C 前端补全 | EC-01…03 | 后端已就绪的能力在页面上可用（改稿并排 diff、程序页三件） | 不宣称「前端功能完备」——只补这三处 |
| B 引用分布 | EC-04…05 | 一条命令算分布 + 一个明确的语料门 | **不宣称「引用充分性已判」**：三个阈值仍 `None`（n=1 < 3） |
| A 外部评审面板 | EC-06…08 | 带归因的第三方判词落既有读面，advisory | **不宣称「叙述质量已判」**：`NOT_JUDGED` 五项逐字不动，面板是另一个判者，不是确定性判据 |
| D 脚本执行权威 | EC-09…11 | `SHIPPED`/`AUTHORED` 闭集 + 既有策略约束真的生效 | **不宣称「生成级已启用」**：`AUTHORED` 出厂默认关闭，启用另需一次决定 |

## 检查结果

（收口时逐条填写：每条 EC 的取证命令、读数、以及它是否真的判红过。）

## 反证臂汇总（**判据咬得住**的证据）

（收口时填写：每条新增判据的两向按压留证 —— 去掉修复判红、过度修复也判红。）

## 结论

（收口时填写。`result` 取 `PASS` / `PASS_WITH_WARNINGS` / `FAIL`；`status` 取 `COMPLETED`。）
