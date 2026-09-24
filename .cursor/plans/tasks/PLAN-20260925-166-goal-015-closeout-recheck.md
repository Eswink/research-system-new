---
id: PLAN-20260925-166
slug: goal-015-closeout-recheck
title: GOAL-015 收口复检：独立复检脚本两树同结论 + m0 可支持终态行 + 残余逐条登记（EC-04）
status: DONE
created_at: 2026-09-25
updated_at: 2026-09-25
parent_goal: GOAL-20260925-015
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260925-015 的 **2026-09-25 用户授权（goal 模式）**：授权**修测试隔离与本地判定
    确定性**，且**不改判据强度、不放宽门禁**。**明确禁止**：为消灭本地红而放宽任何判据 / 门禁 /
    放行面（含 `tests/egress_guard.py` 的目的地判定、`framework/validate_bundle` 的检查项、
    m0 任一 check 的阈值）；改 `tests/application/test_m2_audit.py` 的镜像一致性判据；
    skip / xfail / 删除测试 / 调整收集顺序掩盖顺序失败；豁免 fake-IP（`198.18.0.0/15`）或任何
    目的地址类别。**若根因判定为门禁自身 scoping 有误 ⇒ 不在本循环改门禁**，改产出决策简报
    条目（EC-03）。push-to-main-for-CI（只推 main、不 force、不重写历史、不推旁支）；
    默认 runtime 保持 Fake、默认 CI 离线；**本 PLAN 零真实出网调用**。
    **本 PLAN 是收口轮，零功能改动**：只增一个**只读**复检脚本（标准库、不 import 仓库代码、
    零出网）+ 记录。**不碰任何判据 / 门禁 / 阈值 / 策略面 / 依赖 pin / 运行时默认值**。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260925-167-goal-015-closeout-recheck.md
memory_entries: []
---

# PLAN-20260925-166 — GOAL-015 收口复检（EC-04）

## 目标

把 GOAL-015 的四个 EC 收成一份**可独立复核**的终态：**同一份只读脚本**在**当前树**与
**干净 checkout** 两处给出**同判据同结论**；m0 给出**可支持的终态行**（as-is 与代管后
分开写清）；13 条人工面与全部承继残余**逐条登记**；CI 台账**到终态**。

## 验收条件

- **AC-1｜独立复检脚本**：`tools/verify_goal015_closeout.py`（只读、标准库、**不 import 仓库
  代码**、零出网）在**主树**与**干净 worktree** 两处跑出**同结论**；差异只允许「收口记录尚未
  落盘」这类**时序项**，落盘后归零。
- **AC-2｜判据面逐字节未改**：脚本内置 `git diff --quiet 414f2e5 HEAD -- <判据文件>` 检查
  （`tests/egress_guard.py` / `tests/application/test_m2_audit.py` /
  `tests/tooling/test_python_source_limits.py` / `validate_bundle.py` / `validate.py`）**全绿**。
- **AC-3｜没有用 skip/xfail 掩盖**：四条新判据里无 `mark.skip` / `xfail`；共享守卫的
  skip **按设计**存在，脚本改判其是否具备 **fail-closed** 出口（`RESEARCHOS_REQUIRE_POSTGRES`
  + `pytest.exit`）。
- **AC-4｜m0 可支持终态行**：as-is 与代管后**分别**给出（`FAILED: 1 check(s):
  framework/validate_bundle=1` / `PASS: profile=m0; 23 deterministic checks` + 逐字节复核），
  **不得**把代管后写成 as-is。
- **AC-5｜残余逐条登记**：13 条人工面 + 承继残余（`R-F1`/`R-F2`/`R-F3`/`R-M1`/`R-D1`/`R-B1`/
  `R-N1`）+ 本 GOAL 的 `W` 列表**原样保留**；简报条目与人工面**双向对齐**仍由判据强制。
- **AC-6｜收口记录**：GOAL-015 `status: ACHIEVED`；EC-01…EC-04 全 `PASS`；
  `latest_recheck` = **仓库相对路径**；CI 台账**无未记账 run**。

## 实施清单

- [x] **WP1 — 只读复检脚本**：`tools/verify_goal015_closeout.py`（六组判据：产物在册 /
  判据面逐字节 / 无 skip 掩盖 + fail-closed / GOAL 记录自洽 / 简报六要素与对齐表 / CI 台账）。
- [x] **WP2 — 两树成对复检**：主树 + `git worktree add --detach HEAD` 的干净 checkout，
  两端各一条命令与逐字输出。
- [x] **WP3 — m0 终态行**：`scratch/goal015-c3-m0-asis.log`（as-is）与
  `scratch/goal015-c3-m0-quarantined.log`（代管后，含逐字节复核）。
- [x] **WP4 — 残余登记 + GOAL 收口**：迭代日志 cycle 3 行、状态历史、CI 台账尾巴、
  `status: ACHIEVED`、`child_plans` / `latest_recheck` 对齐。

## 证据（本地）

- **两树成对**：主树 `checked=121 failures=0`；干净 worktree 同判据同结论（收口提交前
  差一条「产物尚未落盘」的**时序项**，落盘后归零——见本 PLAN 的收口回写）。
- **m0**：as-is = `FAILED: 1 check(s): framework/validate_bundle=1`（`R-3`，仓库外文件）；
  代管后 = `PASS: profile=m0; 23 deterministic checks` + `size` / `mtime_ns` / `sha256` 全等。
- **治理**：`validate.py` = `Cursor 治理验证通过`；`DOCS-CHECK PASS: 6 deterministic checks`。

## 残余（本 PLAN 不处置）

- 本 PLAN **无可复用事实**（收口轮零功能改动：只增一个只读复检脚本 + 记录）；GOAL-015 的
  可复用事实已在 cycle 1 / cycle 2 落进 `MEM-20260925-130` … `-133`，本轮不新增记忆条目。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-25 | IN_PROGRESS | WP1–WP3 实施（复检脚本 + 两树 + m0 两种终态） |
| 2026-09-25 | DONE | WP4 收口记录落盘；GOAL-015 = `ACHIEVED` |

## 影响报告

- **Domain / API / schema**：无变化。
- **安全 / 凭据**：无（脚本只读工作树 + `git diff`，零出网、零凭据）。
- **兼容性 / 迁移风险**：无——除一个只读脚本外**零代码改动**；未触碰产品代码、判据、门禁。
- **上游版本影响**：无。
- **下一项任务**：GOAL-015 已 `ACHIEVED`；后续待拍板项见
  `docs/roadmap/OPEN_DECISIONS_BRIEFING.md`（12 条），其中 `D-10`（门禁 scoping）与本 GOAL 的
  `R-3` 同源。
