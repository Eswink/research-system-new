---
id: PLAN-20260922-139
slug: goal-011-closeout-recheck
title: GOAL-011 收口复检：独立复检脚本（当前树 + 干净 checkout 同结论）+ 撤回记录 + m0 23/23 + 一并收口 133…137（EC-06）
status: DONE
created_at: 2026-09-23
updated_at: 2026-09-23
parent_goal: GOAL-20260922-011
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-23 用户 goal 模式指令：**「随后做 EC-06 收口复检并一并收口 PLAN-133/134/135/136/137」**。
    承 GOAL-011 建档授权（push-to-main-for-CI、只推 main、不 force）与凭据/出网纪律。
    **本 PLAN 不发起任何真实调用**：复检脚本**只读**（记录/文档/索引/被跟踪文件），凭据面**只输出
    命中数与相对路径、永不打印值**；不改门禁/断言强度、不新增依赖、不改 pin、不改 Domain /
    Canonical State；不改任何测试断言使其通过——**本轮撞到的三条夹具判据冲突以「撤回载体改动 +
    登记决定请求」处置**，不靠改断言。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260923-139-goal-011-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260923-106-run-chain-evidence-key-and-source-cap.md
  - .cursor/memory/entries/MEM-20260923-107-fixture-failure-shape-is-a-contract.md
  - .cursor/memory/entries/MEM-20260923-108-frozen-refs-on-both-failure-paths.md
---

# PLAN-20260922-139 — GOAL-011 收口复检（EC-06）

## 目标

按 EC-06 的判定细则做**收口复检**，并把 cycle 9 的后果一次结清：① 独立复检脚本在**当前树**与
**干净 checkout** 上给出**同一结论**；② 全量 m0 与治理 `validate.py` 绿；③ **撤回** cycle 9 的载体
改动（CI 判红的溯源结论）并**当场修**顺带抓到的真缺口；④ 一并收口 PLAN-133/134/135/136/137
（各自的复检记录），PLAN-138 保持 BLOCKED 并记下撤回。

**本 PLAN 的产出是复检结论与事实更正，不是新功能**：除撤回、修复与登记外不改产品行为。

## 验收条件

- 复检脚本在**两棵树**上给出**同一结论**；干净树缺少的本机专有资产（`.env`）**如实记「跳过」**。
- 脚本的**撤回层**能被反证：树上有载体残留 ⇒ 该条红（本轮已在 88→84 的两次运行间实测到红/绿两态）。
- 全量 m0 **23/23**（独占运行、DSN 与凭据按 CI 同形固化）；治理 `validate.py` 绿；bundle 校验绿。
- cycle 9 的判红**逐条溯源**：同一子集在 `6f5b9fb5` 上 **11 passed**（基线），撤回 + 修复后
  **25 passed**（含 2 条架构判据与 5 条接缝判据）。
- 撤回**逐字节**可验证：`git diff 6f5b9fb5 -- <四条路径>` 为空。
- 本轮实测到的真缺口（优雅收敛丢字节 digest）**当场修 + 判据钉住**（先红后绿）。
- 133…137 各自的 `latest_recheck` 指向 PASS/PASS_WITH_WARNINGS 且 `memory_entries` 非空；
  `ALL_PLAN` 投影一致；PLAN-138 保持 BLOCKED 并在正文记下撤回。

## 实施清单

- [x] **WP1** 判红溯源（本机复跑 + `6f5b9fb5` / `02a4f47` 两棵 detached worktree 的 A/B 与成对实验）。
- [x] **WP2** 撤回载体改动（协议、合约、5 份 schema、bundle 注册行）并逐字节核对。
- [x] **WP3** 修复优雅收敛路径的冻结引用（`_with_frozen_refs` / `_digest_or_none`）+ 新判据（先红后绿）。
- [x] **WP4** 复检脚本加**撤回层**与 C10 交付物，两棵树各跑一次（干净树见 RECHECK 的两树表）。
- [x] **WP5** 记录面：RECHECK-133…137 + 本 PLAN 的 RECHECK-139 + `MEM-20260923-106/107/108`。
- [x] **WP6** 目标回写：EC-03 保持未达成、EC-06 置 PASS、GOAL 置 **BLOCKED** 并附**下一轮输入**。

## 证据

| # | 事实 | 怎么得到的 |
| --- | --- | --- |
| E-1 | CI 判红（cycle 9 tip）：`python/tests` 11 failed、`console-frontend` 2 failed | `M0 Quality Gates` run `35765996603` @ `02a4f47` 的逐 job 结论 + 失败清单（本机 `scratch/goal011-c10-ci/` 存日志） |
| E-2 | 基线成对：同一子集在 `6f5b9fb5` 上 11 passed | detached worktree `/c/Users/googl/rs-c8tip` |
| E-3 | 撤回后同子集 + 接缝判据 = 25 passed | `pytest … -q`（`tests/api` 4 文件 + 架构判据 + 接缝判据） |
| E-4 | 真缺口先红后绿 | `git stash push -- services/api/run_execution.py` ⇒ 只有新判据红（其余 9 passed）；`pop` ⇒ 10 passed |
| E-5 | 撤回逐字节干净 | `git diff 6f5b9fb5 -- examples/contracts/task_contracts.yaml examples/protocols/m12_reference_research_v1.yaml .cursor/skills/system-spec-check/scripts/validate_bundle.py schemas/` **为空** |
| E-6 | 容器判据在撤回后仍绿 | `pytest tests/e2e/test_sandbox_experiment_seam_docker.py -q` ⇒ **2 passed**（真实容器） |
| E-7 | 收口 m0 与两棵树复检 | 见 `RECHECK-20260923-139` 的表格（本 PLAN 不复述数字） |

## 影响报告

- **Domain / API / schema**：净零（撤回）；`services/api/run_execution.py` 一处**修复**
  （失败收敛路径补冻结引用；行为面不变：终态、判词、预留释放都不动）。
- **安全 / 凭据**：零出网、零凭据读取；`tests/egress_guard.py` 一行不改。
- **CI / workflow**：不改；两次 push 的 run 记在 GOAL 的 CI 台账。
- **上游版本影响**：无。
- **下一项任务**：GOAL-011 以 **BLOCKED** 收口，等下一次拍板（见 GOAL 的「下一轮输入」五条）。

## 状态历史

- 2026-09-23：derive（WP0，与 cycle 10 执行同批）。
- 2026-09-23（cycle 10 执行）：WP1–WP6 全部落地；GOAL 置 BLOCKED；EC-06 置 PASS。
