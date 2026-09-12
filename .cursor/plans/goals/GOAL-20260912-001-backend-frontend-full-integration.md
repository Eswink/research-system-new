---
id: GOAL-20260912-001
slug: backend-frontend-full-integration
title: 后端补全与前端完整对接（预留接口/fixture 全消，33 路由 live-capable）
status: ACTIVE
created_at: 2026-09-12
updated_at: 2026-09-12
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-12 用户要求设计并启用 goal 循环文件以自动迭代完成后端补全与完整对接；GOAL 格式与 push-to-main-for-CI 授权随该计划批准（循环不得推非 main、不得 force）。"
objective: >
  前端所有 live 页面均消费真实后端能力（无预留接口/fixture 冒充业务数据），
  9 个 GAP 域与项目/深水区语义按已批准 PLAN-041/042 落地，main 的本地门与
  GitHub Actions m0-quality 全绿。
exit_criteria:
  - id: EC-01
    criterion: 项目注册表落地：ProjectDefinition 域 + store + GET/POST/PATCH /projects；
      前端 ProjectContext 替换 6 处 example-project 硬编码；#/portfolio/projects 翻 live
    verify: rg -n "example-project" apps/web/src/api/*.ts 仅剩测试/默认值；live e2e 项目链用例绿
    status: PENDING
  - id: EC-02
    criterion: reports/integrations/全局血缘 经既有应用层（deliverable builder、
      tool_plane、跨 run 投影）HTTP 面 + 对应页面翻 live
    verify: tests/api 新端点套件绿；stub e2e 无 Unstubbed；design-fidelity 基线按批准更新
    status: PENDING
  - id: EC-03
    criterion: prompts/datasets/notebooks/alerts/incidents/schedules/data-health 各建
      最小域（domain 实体 + SQLite/PG store + API + client + 页面 live）
    verify: 每域 API 测试 + live e2e 断言；presentationPolicy 不再把该路由强制 example
    status: PENDING
  - id: EC-04
    criterion: 深水区语义收口：budget_adjust 走 BudgetLedger、成本预测投影、
      pause/resume 真执行（lease+worker 协调）、实验队列、artifact 文件 diff、
      memory capability policy（G16）；未落地项必须在 GAPS 保持诚实标注（不得默认绿）
    verify: tests/api 对应用例 + CONSOLE_PAGE_MAP G 表逐行与代码一致
    status: PENDING
  - id: EC-05
    criterion: example fixture 仅作设计参照：33 路由 live-capable（身份/billing/members
      类除外，保持 M18/M19 诚实锁定）；example-isolation 与 live e2e 全链绿
    verify: pnpm run test:e2e + test:e2e:live；pageSupport 无 gap 级业务页残留（EC-04 授权延期项除外）
    status: PENDING
  - id: EC-06
    criterion: 每 cycle main 推送后 GitHub Actions m0-quality 全 job 成功；
      最终收口 RECHECK=PASS/PASS_WITH_WARNINGS 且密封安全扫描有处置记录
    verify: gh run list --branch main --workflow m0-quality.yml 最新 run conclusion=success；
      docs/audits/PA1_MIMOSA_REVIEW.md 含收口时间戳节
    status: PENDING
budget:
  max_cycles: 8
  per_cycle_minutes: 240
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 5
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
child_plans: []
latest_recheck: null
memory_entries: []
---

# GOAL-20260912-001 — 后端补全与前端完整对接（自迭代循环）

## 目标与退出标准

格式规范与循环 SOP 见 [README.md](README.md)（本文件为首个实例）。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | 项目注册表 + 前端去硬编码 + projects 页 live | rg + live e2e | PENDING |
| EC-02 | reports/integrations/全局血缘 复用既有域 + live | API/e2e/基线 | PENDING |
| EC-03 | 9 GAP 域中 prompts/datasets/notebooks/alerts/incidents/schedules/data-health 最小域 + live | API/e2e/policy | PENDING |
| EC-04 | 深水区语义（budget_adjust/预测/真 pause-resume/队列/Diff/memory policy），未落地保持诚实标注 | API + G 表一致性 | PENDING |
| EC-05 | 33 路由 live-capable（M18/M19 诚实锁定除外）；example 仅设计参照 | stub+live e2e + pageSupport | PENDING |
| EC-06 | 每 cycle GHA 全绿；收口 RECHECK + 安全扫描处置 | gh run + audits | PENDING |

前置输入（cycle 前已完成，不占 cycle 预算）：PLAN-20260912-040（后端组成浮现、
接缝闭合、DELETE/custom/clone/approvals-history/参考协议）已 DONE，
RECHECK-20260912-040 = PASS_WITH_WARNINGS；密封扫描 scan-2026-09-12 已处置
（PLAN-040 文件零命中）。

## 循环入口协议

按 README 的 7 步判定执行；当前续点：**cycle 1 未开始 → 执行 ①（派生
PLAN-20260912-041）**。工作树实况：main HEAD 含 040 全部收口 commit；041/042
文件不存在（cycle 1 创建）。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 的主题顺序默认取 EC 表首个 PENDING（EC-01→EC-02→EC-03→EC-04→EC-05），
  除非迭代日志「下一轮输入」给出更强约束（如上一 cycle 的部分交付）。
- 子 PLAN 必须独立可验收、独立 RECHECK；GOAL 只在 EC 层面记账。
- ⑤ push 前：`git pull --ff-only origin main`（并发历史则先 rebase 解决，不 force）。
- EC-04 允许部分延期：任一子项若触发 escalation，记 BLOCKED 并继续其余 EC；
  全部可选项收口后再统一判定 EC-04。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修）：observability OTLP
teardown race、m12 容器 e2e/pg_crash_restart 混合顺序失败（DSN 固化配方）、
m0 全量单跑截断（分组复跑）。工作流文件 `.github/workflows/m0-quality.yml`
属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。

## 终止与收口

- ACHIEVED：EC-01~06 全 PASS（含证据）→ 跑一次整体独立复检（RECHECK-*，
  result=PASS*）→ 沉淀 MEM-* → 本文件 status=ACHIEVED。
- BLOCKED：命中 escalation/fix_policy 上限/no-progress 停止 → 记录阻塞事实、
  所需人工决策、可恢复点；等待人工后转 ACTIVE 或 PAUSED。
- ABORTED：用户撤回目标/授权 → 冻结迭代日志并归档说明。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| (0) | PLAN-20260912-040（cycle 前完成） | 6d844e3, 2022b02, d5abf18, af5df14, b86c693, 54a6360 | m0 分组全绿；stub 30/30；live 10/10 | 本批未 push（收口时按 SOP ⑤ 补推或并入 cycle 1） | — | EC-01~06 | cycle 1 = PLAN-041（EC-01/EC-02 起步） |

## 状态历史

- 2026-09-12 创建（ACTIVE）：GOAL 格式定稿（README），PLAN-040 作为前置输入；
  授权含 push-to-main-for-CI；等待「执行 GOAL-001 下一 cycle」指令进入 cycle 1。
