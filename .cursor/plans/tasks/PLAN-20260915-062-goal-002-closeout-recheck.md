---
id: PLAN-20260915-062
slug: goal-002-closeout-recheck
title: GOAL-20260915-002 收口复检：EC-01~06 证据面与当前树一致性（cycle 8）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 8（收口轮）：用户 2026-09-15 会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；按 GOAL 的「终止与收口」条款，六个 EC 全 PASS 后执行 ACHIEVED 前置复检。push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-062-goal-002-closeout.md
memory_entries:
  - MEM-20260915-030-goal-closeout-verification-recipe
---

# PLAN-20260915-062 — GOAL-002 收口复检（cycle 8）

## 目标

对 GOAL-20260915-002 的六个退出标准做一次**不依赖历史结论文本**的独立复检：只读当前
工作树的 OpenAPI 快照、前端能力清单、源码诚实边界标记、设计基线与 live 清单，
重新判定 EC-01~06，并给出 ACHIEVED 的判定依据。本计划**不新增产品能力**，
改动仅限记录面（GOAL/ALL_PLAN/记忆/复检），因此范围小、风险低。

## 诚实边界

- 复检**不重演历史 cycle 的实现过程**，只核验"当前树是否仍然支持这些结论"：
  端点仍在、页面仍声明收敛、守卫与诚实边界标记仍生效、live 清单仍登记、基线仍存在。
- 历史 RECHECK 的 WARN 项（RECHECK-052~061 的 W-1..W-N，含门禁容差盲区、
  worker SIGTERM 打不断阻塞读、capabilities 非授权边界、pin 只校验形态、
  替身守不住 Idempotency-Key、草稿引用计数上限等）**不因收口而复检通过**，
  在 RECHECK-062 中以"结转清单"原样保留。
- CI 证据**逐 run 从 GitHub API 重读 job 结论**（`actions/runs/<id>/jobs`），
  不采信迭代日志里的文字；本 cycle 的收口提交单独跑 run 并登记。

## 范围

- 复检脚本（scratch，gitignored）：`scratch/verify_goal002_closeout.py`——EC-01~06 的
  证据面断言 + 设计基线/路由清单核对。
- CI 复核：cycle 1~7 的 run 逐 job 结论（GitHub API 现读）。
- 记录：RECHECK-062、GOAL 收口（status=ACHIEVED、latest_recheck、memory_entries、
  迭代日志第 8 行、状态历史收口段）、ALL_PLAN。

## 验收条件

- [x] AC-01：`python scratch/verify_goal002_closeout.py` 的 **59 条**证据面断言全过
  （EC-01~06 的 OpenAPI 路径与读写方法、pageSupport 收敛文案、诚实边界标记、
  live 清单登记、33 路由与双平台基线存在）。
- [x] AC-02：CI 逐 cycle 复核——cycle 1~7 的 run 经 GitHub API 逐 job 读取，
  **每个 run 都是六个 job 全 success**（含本轮 cycle 7 的 35018256116）。
- [x] AC-03：本地 m0 在收口 head 上 23/23 PASS；治理 validate 绿。
- [x] AC-04：RECHECK-062 = PASS_WITH_WARNINGS（结转清单原样保留），
  GOAL 判定 ACHIEVED 并收口（latest_recheck 指向 RECHECK-062）。

## 实施清单

- [x] WP-A 复检脚本 + EC-01~06 证据面断言（59 条）
- [x] WP-B CI 逐 cycle 逐 job 复核（GitHub API 现读，8 个 run）
- [x] WP-C 结转告警清单整理（RECHECK-052~061）
- [x] WP-D RECHECK-062 + GOAL 收口（ACHIEVED）+ ALL_PLAN 记账

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `python scratch/verify_goal002_closeout.py` → `PASS: EC-01..EC-06 证据面与当前树一致`（**59 条断言**：EC-01 5 / EC-02 7 / EC-03 6 / EC-04 12 / EC-05 12 / EC-06 12 / 路由与基线 5） | PASS |
| WP-B | GitHub API 逐 run 读 job 结论：cycle 1 `34960364156`、cycle 2 `34969935719`、cycle 3 `34978272057`、cycle 4 `34984686466`、cycle 5 `35002027768`、cycle 6 `35011288950` + 记录提交 `35013114804`、cycle 7 `35018256116` —— **8 个 run × 6 job 全 success** | PASS |
| WP-C | 结转清单：RECHECK-052/053/054/055/056/057/058/059/060/061 的 WARN 项逐条保留（含 RECHECK-054 W-1 与 RECHECK-061 W-2） | PASS |
| WP-D | RECHECK-20260915-062 = PASS_WITH_WARNINGS；GOAL-20260915-002 status=ACHIEVED（latest_recheck → RECHECK-062） | PASS |

## 已知风险

- 复检是"当前树一致性"核验，不重演历史实现；若历史 RECHECK 的**判定本身**有偏差，
  本轮只可能通过"当前树不支持该结论"发现它（已按此口径写进 RECHECK 的检查范围）。
- 结转告警中的"设计门禁容差盲区"（W-1）在本轮仍成立且**已被三次量化**
  （1.02%/0.93% → 0.79%/0.66% → 0.48%/0.47%），它是流程约束（页面改动必须主动重生成
  基线并目检），不是可用门禁替代的东西。
- 收口提交只改 `.cursor/**` 记录面，但**仍会触发 CI**（cycle 1 已证明记录提交也会跑六 job），
  因此本 cycle 也必须等本轮 run 六 job 全绿才算收口成立。

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 8（ACHIEVED 前置复检）。
- 2026-09-16 WP-A/WP-B 完成：59 条证据面断言全过；8 个 CI run 逐 job 复核全绿。
- 2026-09-16 WP-C/WP-D 完成：结转清单整理；RECHECK-062 = PASS_WITH_WARNINGS，
  GOAL 记 ACHIEVED。

## 影响报告

- 改动：仅记录面（`GOAL-20260915-002`、`ALL_PLAN.md`、`RECHECK-20260915-062`、
  本计划、GOAL 迭代日志第 8 行与收口状态历史）；产品代码、API、schema、凭据、
  依赖**均无改动**。
- lint/typecheck/test：本地 m0 = `profile=m0; 23 deterministic checks`；治理 validate 绿；
  复检脚本 59/59。
- Domain/API/schema 变化：无。
- 安全/凭据变化：无（无新凭据面、无新依赖）。安全面结论沿用 cycle 7 的 Mimosa 密封扫描
  对账（36 findings / 3 high，本轮改动文件命中 0 条；`scanner_enobufs` 期间不主张项目整体安全）。
- 兼容性/迁移风险：无。
- 上游版本影响：无。
- 下一项任务：无（本 GOAL 收口）。长程剩余项见 GOAL「终止与收口」段：门口禁容差盲区、
  worker SIGTERM、capabilities 非授权边界、pin 形态校验、ToolPack install/approve 面、
  M18 租户/RBAC，均由后继 GOAL 承接。
