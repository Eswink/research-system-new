# Goal Records — 自迭代目标循环（GOAL-*）

本目录存放 **GOAL 记录**：位于 `PLAN-*` 之上的一层编排文件。一个 GOAL 承载一个
用户批准的终极目标，以「cycle」为单位反复迭代：每个 cycle 派生一个标准子
PLAN → 执行 → 本地验证 → commit → push → 检查 GitHub Actions → 纠错 → 回写
GOAL → 决定下一 cycle 或终止。GOAL 只做编排与记账；工程事实、验收与复检仍由
PLAN/RECHECK/MEM 体系承载（单一流程权威，见 `.cursor/rules/20-plan-memory-recheck.mdc`）。

- 命名：`GOAL-YYYYMMDD-NNN-<kebab-topic>.md`（NNN 为 GOAL 独立计数序列，从 001 起）。
- 生命周期：`DRAFT → ACTIVE →（循环）→ ACHIEVED | BLOCKED | ABORTED`；`PAUSED`
  为人工挂起。状态变化只追加，不静默改写。
- 结构合规由 `governance-check` 的 `check_goals()` 强制（必含章节见下）。

## Frontmatter 契约

```yaml
---
id: GOAL-YYYYMMDD-NNN
slug: <kebab-topic>
title: <一句话目标标题>
status: ACTIVE
created_at: YYYY-MM-DD
updated_at: YYYY-MM-DD
owners: [root-agent]
authorization:
  source: user-request
  ref: "<用户批准目标与循环授权的原文要点；push-to-main 授权必须在此显式记录>"
objective: <终极验收目标（一句话）>
exit_criteria:            # 每条必须机器可检：命令 + 期望值
  - id: EC-01
    criterion: <可判定标准>
    verify: <命令或可核查证据>
    status: PENDING        # PENDING | PASS | BLOCKED
budget:
  max_cycles: <int>              # 硬上限，触顶即 BLOCKED
  per_cycle_minutes: <int>       # 单 cycle 本地工作量上限（软约束）
  no_progress_stop_cycles: <int> # 连续 N 个 cycle 未推进任何 EC → 停止
fix_policy:
  same_signature_retries: <int>  # 同一失败签名自动修复上限
  cycle_fix_retries: <int>       # 单 cycle CI 修复总上限
  forbidden:                     # 永不允许（触犯即 BLOCKED）
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:             # 任一命中 → status=BLOCKED，留人工决策
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更
  - 同一失败签名超过 fix_policy 上限
child_plans: []                  # 本 GOAL 派生的 PLAN-* 路径（全局 NNN 续号）
latest_recheck: null             # ACHIEVED 时必须指向 PASS/PASS_WITH_WARNINGS 的 RECHECK
memory_entries: []               # 收口时沉淀的工程记忆
---
```

## 必含章节（check_goals 强制）

1. `## 目标与退出标准` — EC 表：编号 / 标准 / 验证命令 / 证据来源 / 状态。
2. `## 循环入口协议` — 幂等恢复规则（见下）。
3. `## 单 cycle SOP` — ①~⑦ 步骤（见下）。
4. `## CI 失败分类与纠错` — 失败分类 → 处置映射表。
5. `## 终止与收口` — ACHIEVED/BLOCKED/ABORTED 的判定与动作。
6. `## 迭代日志` — 每 cycle 一行（见格式）。
7. `## 状态历史`。

## 循环入口协议（幂等重入）

驱动方（会话或定时自动化）进入时，按迭代日志最后一行 + 工作树/远端实况判定续点：

1. 最后一 cycle 无记录 → 开 cycle 1：执行 ①。
2. 有子 PLAN 但仍在 IN_PROGRESS → 继续该 PLAN 的执行（②）。
3. 本地验证已过、有未推送 commit → 执行 ④⑤（push + CI）。
4. CI 在跑或未记录结论 → 执行 ⑤（等待/判定），禁止猜测绿。
5. CI 有失败且修复次数未达上限 → 执行 ⑥（纠错）。
6. 最后一 cycle 的 commit+CI 全绿且 EC 未满足 → 执行 ①（生成下一子 PLAN）。
7. 判定条件按「终止与收口」：ACHIEVED / BLOCKED / 超预算。

任何一步完成后立即回写本文件（状态历史/迭代日志），保证任意时刻崩溃后重入可续。

## 单 cycle SOP

- **① derive**：从剩余 EC + 上一轮「剩余差距」圈定一个可独立验收的最小主题；
  用 Plan Mode 流程写子 PLAN（`.cursor/plans/tasks/PLAN-…`，frontmatter 增加
  `parent_goal: GOAL-…` 并投影 ALL_PLAN）。GOAL 迭代日志登记子 PLAN 路径。
- **② 执行**：子 PLAN 按自身 WP 提交纪律推进（每 WP 独立 commit，显式路径）。
- **③ 本地验证**：m0 按组（python 6 / typescript 9 / framework 8，DSN 固化配方）
  + 受影响定向套件 + web 门（tsc/eslint/unit/build/stub/live e2e）。本地不绿不得 push。
- **④ commit**：子 PLAN 收口（RECHECK 完成后 DONE），GOAL 记录 commit 列表。
- **⑤ push + CI**：`git push origin main`（仅限 main；授权见 frontmatter）→
  `gh run list --branch main --workflow m0-quality.yml --limit 1` → 轮询至完成；
  失败时 `gh run view --log-failed <run-id>` 取证据。记录 run URL + 结论。
- **⑥ 纠错**：按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
  超过 fix_policy 上限或命中 escalation_triggers → status=BLOCKED。
- **⑦ 记录 + 下一轮**：更新 EC 状态、迭代日志、child_plans、状态历史；
  未达终态 → 回到 ①（cycle+1）；触顶预算 → BLOCKED。

## CI 失败分类与纠错

| 类别 | 识别 | 处置 |
| --- | --- | --- |
| lint/format/typecheck | job 报 ruff/eslint/tsc/mypy | 直接修复 → fix commit → 重推 |
| 产品测试失败 | pytest/playwright 断言 | 读失败输出定位缺陷（产品或测试各半）；修产品优先，禁改断言迁就 |
| flake/env | 已知签名（observability OTLP 端口、teardown race、DSN 注入、compose 环境） | 按 `docs`/记忆中的既有配方重跑；配方不覆盖 → 归类下一行 |
| 基础设施 | runner 挂/网络/依赖源不可达 | 等窗口重跑 1 次；仍败 → BLOCKED（infra 非代码缺陷） |
| 治理/安全门禁 | Mimosa/validator 命中新增项 | 按各处置文档修或登记误报；不得绕过；不得宣称安全 |

## 迭代日志格式

```
| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
```

`CI run/结论` 必须含 run 链接与真实终态；本机无法验证时记 `PENDING` 并停止推进
（不伪造 PASS）。`ACHIEVED` 前置：所有 EC=PASS 且有证据 + 独立 RECHECK
PASS/PASS_WITH_WARNINGS + 本文件收口。
