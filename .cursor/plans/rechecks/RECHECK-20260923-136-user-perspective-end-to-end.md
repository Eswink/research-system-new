---
id: RECHECK-20260923-136
plan_id: PLAN-20260922-136
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-23
completed_at: 2026-09-23
reviewer: independent-closeout-script + root-agent-goal-011-ec06
baseline_ref: 6f5b9fb5
checked_head: 收口提交（RECHECK-133…139 + EC-06 置 PASS + GOAL 置 BLOCKED 同一次提交落地）
---

# RECHECK-20260923-136 — 用户视角端到端 + `partial` 页诚实标注（GOAL-011 EC-04）

## 检查范围

**不采信 PLAN-136 的结论文本**：读面快照（`scratch/goal011-c4-*/`，**不进仓库**）在 cycle 7 已落地，
本复检只重新核对**树上还在的**那一部分：判据（用户视角用例 + `partial` 页口径）与**未被本 GOAL 改动**
这一事实。

## 检查结果

| # | 该 PLAN 的主张 | 复检怎么验的 | 结论 |
| --- | --- | --- | --- |
| 1 | 五步（建项目 → 选协议 → 跑 run → 看制品/证据/预算/血缘）以**既有 API 面**走通 | A 层：`tests/api/test_projects_api.py::test_runs_started_at_a_path_project_belong_to_the_fixture_project` 按名在位（「新建项目的 run 归属该项目」这条链的判据）；本 cycle 实跑 `tests/api` 全绿 | ✅ |
| 2 | 记录落 `scratch/`（不进仓库、不上传） | `scratch/` 在 `.gitignore` 内（E 层间接判：凭据面扫描只看仓根与 `secrets/`，`scratch/` 不在被跟踪集合里）；`git status` 无 scratch 条目 | ✅ |
| 3 | `partial` 页诚实标注逐条核对（措辞问题改措辞、行为问题登记 W） | 该 PLAN 的 W 列表在案且**未被本 cycle 改动**；判据侧对应面（`partial` 口径）在 cycle 7 实跑通过 | ✅（承前） |
| 4 | 出站与凭据纪律不变 | E 层：`ALLOWED_KINDS` 仍只有 `localhost`；本 cycle 全部实跑 `blocked 0`；无 live 调用 | ✅ |
| 5 | 本 PLAN 的文件**未被 cycle 9/10 触及** | `git diff 6f5b9fb5 -- <EC-04 判据路径>` 为空（无本次改动） | ✅ |

## 结论

**PASS_WITH_WARNINGS**：EC-04 的验收在 cycle 7 已按「读面快照 + 既有 API 面」完成，本 GOAL 收口时
**承前**（未改动其判据与记录）；本轮只补充了「cycle 9/10 未触碰它」这一事实。

**W 列表（承自 PLAN-136，本次复检未消除）**

- **W-7**：EC-04 的记录形态是**读面快照**（定案 D-1 的选择），不是浏览器截图 ⇒ 前端渲染面
  （页面真的把读面值画出来）**不在** EC-04 的判据内；它由 console 的 live e2e 套件**另测**
  （CI `console-frontend` 作业）。两者不可互相替代，如实并列。
- **W-8**：本轮 cycle 9 的 tip 上 `console-frontend` 作业曾判红 2 条（**夹具语义**所致，
  见 `RECHECK-20260923-139` 的撤回记录）⇒ 「用户视角」这条链的**夹具协议是共享的**，
  改参考协议的失败形态会同时打到它与 API 判据（`MEM-20260923-107`）。
