---
id: GOAL-20260915-002
slug: gap-registry-completion
title: 诚实缺口注册表收口：G9/G12/G8/G7/G15/G2 六项从「诚实禁用」转为「有真实消费者」
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」——GOAL-20260912-001 收口（ACHIEVED）后，本 GOAL 承接其长程迭代余量：候选缺口表（G9 全局血缘 / G12 跨 run 时序预测 / G8 workspace 文件树 / G7 ops 余项 / G15 tool-provider 写面 / G2 项目删除）由 GOAL-001「终止与收口 · cycle 12 长程排期」立项。push-to-main-for-CI 授权沿用 GOAL-001 的批准口径（只推 main、不 force、不推旁支触发 CI）。"
objective: >
  把前端的六个诚实缺口（pageSupport 中已如实标注的 partial/gap 项）逐个变成
  有真实后端消费者与真实页面的能力：G9 全局跨 run 血缘、G12 跨 run 时序成本预测、
  G8 workspace 文件树与文件级快照 Diff、G7 ops 写面（告警规则/incident 处置/
  用户级 schedule/聚合报表）、G15 tool-provider 管理写面、G2 项目删除/归档；
  每一项要么交付并翻 live，要么产出 Accepted ADR 并在 pageSupport / CONSOLE_PAGE_MAP
  同步收敛（不留死端点、不用 fixture 冒充业务数据）。
exit_criteria:
  - id: EC-01
    criterion: >-
      G9 全局跨 run 血缘：项目作用域血缘投影（run/dataset/prompt 节点与边）落地并翻 live
    verify: >-
      OpenAPI 快照含项目级 lineage 路径；library/lineage 的 pageSupport reason 收敛；live e2e 用例绿
    status: PENDING
  - id: EC-02
    criterion: >-
      G12 跨 run 时序成本预测：由 cost/daily 序列给出跨 run 预测（口径与计量完备状态如实标注）
    verify: >-
      OpenAPI 快照含预测路径；insights/cost-analytics 与 govern/budget 的 reason 收敛；API + live e2e 用例绿
    status: PENDING
  - id: EC-03
    criterion: >-
      G8 workspace 文件树 + 文件级快照 Diff：只读文件树 API 与文件级 diff 接入页面；
      若判定不可行则产出 Accepted ADR 并同步收敛页面标注，且不留死端点
    verify: >-
      OpenAPI 快照路径 + live e2e 绿，或 ADR 文件（Accepted）+ pageSupport 文案一致
    status: PENDING
  - id: EC-04
    criterion: >-
      G7 ops 写面：告警规则 CRUD 与 incident 处置（declare/assign/close）落地，页面去掉对应 disabledOperations
    verify: >-
      OpenAPI 快照写方法存在；ops/alerts 与 ops/incidents 的 disabledOperations 相应项消失；API + live e2e 绿
    status: PENDING
  - id: EC-05
    criterion: >-
      G15 tool-provider 管理写面：注册/更新/健康复核（当前只读投影 → 有真实写面与消费者）
    verify: >-
      OpenAPI 快照写方法存在；ops/integrations 的 disabledOperations 相应项消失；API + live e2e 绿
    status: PENDING
  - id: EC-06
    criterion: >-
      G2 项目删除/归档 + 治理收口：项目归档/删除语义落地（被引用返回 409，不静默级联）；
      每个 cycle 本地 m0 与 main 的 CI 全绿；收口 RECHECK + 安全扫描处置
    verify: >-
      OpenAPI 快照含 DELETE/PATCH 项目路径 + 409 用例；每 cycle CI run 六 job 结论；
      收口 RECHECK = PASS 或 PASS_WITH_WARNINGS
    status: PENDING
budget:
  max_cycles: 10
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
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

# GOAL-20260915-002 — 诚实缺口注册表收口（自迭代循环）

## 目标与退出标准

格式规范与循环 SOP 见 [README.md](README.md)。本 GOAL 是 GOAL-20260912-001
（ACHIEVED，2026-09-15）的长程承接：GOAL-001 把 33 条规范路由全部变成「live-capable 且
**诚实标注缺失面**」；本 GOAL 的目标是把其中**仍然缺失的六个能力**做成真实能力，
而不是把标注改小。

| EC | 标准（摘要） | 验证 | 状态 |
| --- | --- | --- | --- |
| EC-01 | G9 全局跨 run 血缘（项目作用域节点/边） | OpenAPI + pageSupport + live e2e | PENDING |
| EC-02 | G12 跨 run 时序成本预测 | OpenAPI + API/live e2e + 计量口径 | PENDING |
| EC-03 | G8 workspace 文件树 + 文件级 diff（或 Accepted ADR 收敛） | OpenAPI/ADR + live e2e | PENDING |
| EC-04 | G7 ops 写面（告警规则 CRUD + incident 处置） | OpenAPI 写方法 + pageSupport 收敛 | PENDING |
| EC-05 | G15 tool-provider 管理写面 | OpenAPI 写方法 + pageSupport 收敛 | PENDING |
| EC-06 | G2 项目归档/删除 + 每 cycle 门禁/CI 全绿 + 收口复检 | DELETE/PATCH + 409 用例 + CI run + RECHECK | PENDING |

**不变量（沿用 GOAL-001 与 AGENTS.md）**：不伪装实现（不注册没人消费的 scheduler/规则、
不让 fixture 冒充业务数据）；默认 deny 的安全姿态不变；观测隐私（不记录完整 Prompt）
不变；每一项写面必须走既有 policy/preflight 门链。**规模标注**：G8 为 L（控制面当前
没有 workspace 快照枚举面）、G7/G9/G12/G15 为 M、G2 为 S。

## 循环入口协议

按 README 的 7 步判定执行；当前续点：**cycle 0（尚未开始）**。首个动作 = ① derive：
按 EC 表顺序取 EC-01（G9 全局血缘），子 PLAN 编号续全局序列（下一号 = PLAN-20260915-054）。
driver=session-goal，owner=root-agent。

## 驱动

驱动无关（README「驱动适配」）：默认会话驱动；需要无人值守时挂定时自动化，指令模板见
README（仅当 status=ACTIVE 时推进）。进入 cycle 时在迭代日志声明 driver/owner；
同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 的主题顺序默认取 EC 表首个 PENDING；若上一 cycle 部分交付，则以其「下一轮输入」为准。
- 子 PLAN 必须独立可验收、独立 RECHECK；GOAL 只在 EC 层面记账。
- ③ 本地验证：m0 全量（23 项）+ 受影响定向套件 + web 门（lint/typecheck/unit/build/stub e2e/live e2e）
  + 设计基线（页面改动时按既有流程强制重生成并目检）。
- ⑤ push 前 `git pull --ff-only origin main`（并发历史先 rebase，不 force）。
- 每个 EC 允许拆到多个 cycle；部分交付记 `PARTIAL`，不得预置 PASS。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修）：observability OTLP teardown race、
m0 全量单跑在负载下的 timing 用例（隔离复跑对照）、DSN 注入（需固化配方）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）。
`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。

## 终止与收口

- **ACHIEVED** 前置：六个 EC 全 PASS（或经 Accepted ADR 收敛）+ 独立 RECHECK
  PASS/PASS_WITH_WARNINGS + 本文件收口（`latest_recheck` 指向该 RECHECK）。
- **BLOCKED**：预算触顶（`max_cycles` 或 `no_progress_stop_cycles`）、命中 escalation_triggers、
  或同一失败签名超过 `fix_policy` 上限；恢复条件必须写清（哪些 EC 未达成、需要谁决定什么）。
- **收口动作**：更新 EC 状态表、迭代日志、child_plans、memory_entries；把长程剩余项
  写入「终止与收口」供后继 GOAL 承接（不在本文件内隐藏缺口）。

## 迭代日志

| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| （尚无 cycle） | — | — | — | — | — | EC-01~06 全部 PENDING | cycle 1 = ① derive EC-01（G9 全局血缘） |

## 状态历史

- 2026-09-15 创建（ACTIVE）：GOAL-20260912-001 收口（ACHIEVED，RECHECK-20260915-053）后，
  按用户「循环迭代 10-20 次」的授权承接长程迭代；范围 = GOAL-001「终止与收口 · cycle 12
  长程排期」的候选缺口表（G9/G12/G8/G7/G15/G2），六项各立一个 EC。
