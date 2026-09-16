---
id: PLAN-20260915-073
slug: goal-003-budget-closeout
title: GOAL-20260915-003 收口复检：十条 cycle 的证据面与预算触顶处置
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 10 收口轮：用户 2026-09-15 会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；按 GOAL 的「终止与收口」条款，`budget.max_cycles: 10` 触顶时执行收口复检并写清恢复条件。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-073-goal-003-budget-closeout.md
memory_entries:
  - MEM-20260915-048-nonportable-counterexamples-are-not-gates
---

# PLAN-20260915-073 — GOAL-003 收口复检（cycle 10 收口轮）

## 目标

`budget.max_cycles: 10` 触顶，按 GOAL 契约执行收口：

1. 对六个 EC 做一次**只读当前证据**的独立复检（不采信历史结论文本）；
2. 汇总每 cycle 的 main CI 结论，并把 **cycle 9 的 ubuntu 红项**定性、处置与验证写清；
3. 完成**安全扫描处置**（Mimosa 密封深度扫描本轮启动，结果如实回填）；
4. 把仍未处理的长程项写成**后继入口**，并写清恢复条件（用户决策点）。

## 范围

- 新增：`RECHECK-20260915-073`（收口复检本体）、本 PLAN、`MEM-20260915-048`。
- 修改：GOAL-20260915-003 的 frontmatter（`status: BLOCKED`、EC-06 → PASS、
  `latest_recheck`）、迭代日志第 10 行（补 CI 结论）、状态历史、终止与收口段。
- **不改**任何产品代码（收口轮不做功能）。

## 验收条件

- [x] AC-01：EC 表逐条给出**可复核证据**（RECHECK/提交/CI run），不写"已完成"了事。
- [x] AC-02：每 cycle CI 结论成表；cycle 9 红项按失败分类表定性 + 处置 + 验证三点齐全。
- [x] AC-03：安全扫描处置写成"能力边界"（静态扫描 ≠ 运行时验证；coverage 口径）。
- [x] AC-04：后继入口按优先级列出，并标注哪些**需要用户拍板**（escalation 级）。
- [x] AC-05：门禁（治理验证 + 文档一致性）+ 记录（PLAN/RECHECK/MEM/ALL_PLAN）+ 提交 → CI。

## 实施清单

- [x] WP-A RECHECK-073（EC 表 + CI 表 + 扫描处置 + 后继入口）
- [x] WP-B GOAL 收口（BLOCKED 记录、EC-06 PASS、latest_recheck 指向）
- [x] WP-C MEM-048（"不可移植的反证不是门禁"）+ ALL_PLAN 登记
- [x] WP-D 治理验证 + 提交推送 + CI 复核

## 证据

```text
GOAL 十条 cycle：EC-01…EC-05 各自的 RECHECK 全 PASS/PASS_WITH_WARNINGS；
EC-06 = 每 cycle m0 23/23 + main CI 六 job（cycle 9 一次红项已定性/更正/验证）。

CI 表（main）：35059391199 / 35064152993 / 35071216707 / 35087267045 / 35093603690 /
35100510412 / 35108305191 / 35111194584 / 35115260874（1 红，ubuntu）/
35119573827（六 job 全 success，含更正后的 ubuntu）。
```

## 状态历史

- 2026-09-16 创建并完成（同一轮）：收口轮不做功能，只做复检与记账。

## 影响报告

- **Domain/API/schema**：无。
- **安全/凭据**：无代码变化；本轮启动 Mimosa 密封深度扫描（只读）。
- **兼容性/迁移风险**：无。
- **下一项任务**：见 RECHECK-073「仍未处理的长程项」——最小且最安全的是
  provider 凭据绑定（`credential_ref` 声明面）。

## 已知风险

- **收口不等于完美**：EC 全 PASS 只覆盖本 GOAL 写下的六条判据；范围注记（各 RECHECK 的
  W 类事实）仍是真实边界，后继入口已列出。
- **预算触顶是契约行为**：不是因为失败，也不是因为 EC 未达成；恢复条件需用户选一条。
