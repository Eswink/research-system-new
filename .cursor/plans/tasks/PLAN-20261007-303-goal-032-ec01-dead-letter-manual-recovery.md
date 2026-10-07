---
id: PLAN-20261007-303
slug: goal-032-ec01-dead-letter-manual-recovery
title: GOAL-032 cycle 1（EC-01）：死信人工恢复路径 —— ADR-0033 + 状态机出边 + Port/三实现 + 幂等与点名拒绝 + 两向反证 + 实跑
status: DONE
created_at: 2026-10-07
updated_at: 2026-10-07
latest_recheck: .cursor/plans/rechecks/RECHECK-20261007-304-goal-032-ec01-dead-letter-manual-recovery.md
memory_entries:
  - manual-recovery-keeps-the-terminal-read-and-the-budget
parent_goal: GOAL-20261007-032
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261007-032 的 **EC-01**（`R26-1` 死信人工恢复路径）。授权原文见该 GOAL 的
    `authorization.ref`（用户 2026-10-06 下放全部权限 + 2026-10-07 goal 模式指令 +
    push-to-main-for-CI 口径）。**本 PLAN 专属边界**：① 改 `DEAD_LETTER` 的终态语义
    **必须留 ADR**（已落 `docs/adr/ADR-0033-dead-letter-manual-recovery.md`，
    `Status: Accepted`）——这是「可以有界改产品语义」的授权面，**不是**放宽判据；
    ② 同步集**仅限** GOAL-032 fix_policy 点名的四条（`RUN_STATE_MACHINE.md` 迁移表与
    Terminal 注 / `test_workflow_dead_letter_surface.py` 的重新定基 /
    `test_state_machines.py` 的 `ENQUEUE` 参数行【**逐字未动**，见下】/
    `test_task_state_drivers.py` 的 `_DRIVEN_BY`）；**其余既有判据一字未改**；
    ③ 零 allow 变更、零 pin 夹具改动、零新依赖、零真实凭据、默认门仍离线；
    ④ **不得**宣称项目安全（`R-M1`）；**不得**宣称投递语义为「恰好一次」（**明确否认**）。
objective: >-
    把 AGENTS.md §7 的 `dead-letter / manual recovery` 从「只有半边成立」（可枚举、
    可处置的终态成立；人工恢复动作无产品路径）推进到**两半都成立且有判据**：先按
    `ADR-0030` 的候选与机制观察选定做法并**新增 ADR**（改终态语义不得静默），再让
    `DEAD_LETTER` 可被**人工显式恢复**（重新入队），幂等（重复恢复零第二次副作用）、
    不可恢复输入**点名拒绝**、两向反证（摘掉出边 ⇒ 判红；点名拒绝改静默 ⇒ 判红）、
    实跑（真实失败路径进死信 → 人工恢复 → 重建续跑跑到终态）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **ADR 依据**：`docs/adr/ADR-0033-dead-letter-manual-recovery.md` 在树、
      `Status: Accepted`，写明候选（对照 ADR-0030 的 A–E 与机制观察）与**为什么不是别的
      选项**；`docs/INDEX.md` 登记；ADR 不改 `ADR-0030` 的 `Status: Proposed`。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_pending_validation_failure_registration.py -q` ⇒ 绿（ADR-0030
      仍是 Proposed、同源指针未断）；`rg -n "ADR-0033" docs/INDEX.md docs/adr/` ⇒ 命中。
    status: PASS
  - id: AC-2
    criterion: >-
      **恢复路径（域 + Port + 三实现）**：`(DEAD_LETTER, Transition.REQUEUE) → QUEUED`
      是唯一出边；Port 新增 `requeue(task_id) -> str`；SQLite / PostgreSQL / Fake 三实现
      同判据（成功 `restored`；不存在 / 非死信 ⇒ `InvalidInputError` 且消息点名）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/contracts/test_dead_letter_manual_recovery_contract.py -q`（含 PG：需
      `RESEARCHOS_POSTGRES_DSN`）⇒ 绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **幂等 + 点名拒绝 + 终态语义**：第二次恢复被**点名拒绝**且**零新副作用**
      （事件计数取样在第二次**之前**）；恢复**前**自动路径（`acquire_lease`）仍点名拒绝
      死信；`DEAD_LETTER` 仍在 `terminal()`；恢复**不重置**尝试预算（`fence_seq` 不回退，
      下一次交付推进代次）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py -q` ⇒ 绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **实跑（真实失败 → 死信 → 人工恢复 → 终态）**：执行契约 `max_attempts=1` 经真编排
      收敛 `FAILED` 且任务落 `DEAD_LETTER`；恢复前自动入口点名拒绝；`requeue` 后回
      `QUEUED`；重建续跑跑到 `SUCCEEDED`；尝试代次前进；事件链含恢复事件。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_dead_letter_recovery_full_loop.py -q` ⇒ 绿。
    status: PASS
  - id: AC-5
    criterion: >-
      **两向反证 + 逐字节复原**：① 摘掉恢复出边 ⇒ 恢复类判据判红；② 点名拒绝改静默 ⇒
      点名拒绝判据判红；两臂复原后 raw `sha256` 回到基线。
    verify: >-
      `uv run --frozen --no-sync python -B scratch/goal032-cycle1-press.py` ⇒
      `P1_RED` / `P2_RED` 各自有失败、`FINAL_MATCHES_BASELINE True`；
      留档 `scratch/goal032-cycle1/press-matrix.log`（二进制写盘、CR=0）。
    status: PASS
  - id: AC-6
    criterion: >-
      **同步集自证（四条，仅限点名面）**：① `RUN_STATE_MACHINE.md` 迁移表 + 终态注；
      ② `test_workflow_dead_letter_surface.py` 的「无出边」判据**按新事实重新定基**
      （受判面**扩大**：从「所有事件非法」到「恰有 REQUEUE 合法、其余仍非法」）；
      ③ `test_state_machines.py` 的 `DEAD_LETTER + ENQUEUE` 参数行**逐字未动**
      （新事件名 `REQUEUE` 不在该行）；④ `test_task_state_drivers.py` 的 `_DRIVEN_BY`
      增列人工入口。其余既有判据**零改动**（`git diff --numstat` 逐条出示）。
    verify: >-
      `git diff --numstat` 对 `tests/` 的读数；`uv run --frozen --no-sync python -B -m
      pytest tests/domain/test_state_machines.py -q` ⇒ 绿。
    status: PASS
  - id: AC-7
    criterion: >-
      **门与留档**：受影响套件全绿（`tests/adapters/sqlite` / `tests/domain` /
      `tests/contracts` / `tests/e2e` / `tests/application` / `tests/architecture`）；
      `ruff check` / `ruff format --check` / `mypy` 全绿；规模门（450 行 / 50 行函数）
      绿——PG 引擎触顶后按本仓拆分先例抽出 `workflow_requeue.py`（逐行搬运）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/tooling/test_python_source_limits.py
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 绿；
      `ruff check adapters packages tests services` + `ruff format --check` + `mypy` 读数。
    status: PASS
---

# PLAN-20261007-303 — GOAL-032 cycle 1（EC-01）：死信人工恢复路径

本 PLAN 承载 `R26-1` 的实现、判据、反证与实跑。工程事实以本文件与
`RECHECK-20261007-304` 为准；GOAL 只做编排记账。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-7）。

## 实施清单

| # | 项 | 交付 |
| --- | --- | --- |
| WP-1 | ADR 依据 | `docs/adr/ADR-0033-dead-letter-manual-recovery.md`（Accepted）+ `docs/INDEX.md` 登记 |
| WP-2 | 域 | `packages/domain/task_state.py`：`Transition.REQUEUE` + `(DEAD_LETTER, REQUEUE) → QUEUED`；模块 docstring 写明「终态 = 对**自动路径**」 |
| WP-3 | Port | `packages/application/ports/workflow_engine.py::requeue`（契约四条写进 docstring） |
| WP-4 | SQLite | 新增 `adapters/sqlite/requeue.py`（`requeue_task`，与 `cancel_run.py` 同形）+ `workflow_engine.py::requeue` 包装 |
| WP-5 | PostgreSQL | 新增 `adapters/postgres/workflow_ops.py::requeue_impl` + `adapters/postgres/workflow_requeue.py`（mixin，守 450 行）+ `workflow_engine.py` 继承与接线 |
| WP-6 | Fake | `adapters/fakes/workflow_engine.py::requeue` + `mark_dead_letter`（测试起态；Fake 无死信到达路径这条边界显式） |
| WP-7 | 判据 | 引擎面 8 例（含参数化）+ 契约面 7 例 + e2e 1 例 |
| WP-8 | 反证 | `scratch/goal032-cycle1-press.py`（行尾自适应、二进制复原）+ 留档 |
| WP-9 | 同步集 | `RUN_STATE_MACHINE.md` / 既有「无出边」判据重新定基 / `_DRIVEN_BY` |
| WP-10 | 声明面 | `WORKFLOW_RELIABILITY.md` §10（半边 → 两半）、`PORTS.md` 的 WorkflowEngine 职责 |

## 证据

- **ADR**：`docs/adr/ADR-0033-dead-letter-manual-recovery.md`（`Status: Accepted`）。
- **判据读数**：引擎面 `8 passed`（`tests/adapters/sqlite/test_workflow_dead_letter_manual_recovery.py`）；
  契约面 `7 passed, 3 skipped` 无 DSN / `12 passed` 含 PG（`RESEARCHOS_POSTGRES_DSN` 指向
  `localhost:15432`）；e2e `1 passed`；受判面合跑 `1150 passed, 72 skipped`（domain + sqlite +
  contracts）；`1255 passed, 14 skipped`（e2e + application + architecture）。
- **反证**：`P1_RED 3 failed, 5 passed`（摘掉出边）/ `P2_RED 5 failed, 10 passed, 3 skipped`
  （点名拒绝改静默）/ `FINAL_MATCHES_BASELINE True`；留档 `scratch/goal032-cycle1/press-matrix.log`
  （249 字节、CR=0）。
- **门**：`ruff check` = `All checks passed!`；`ruff format --check` = `1124 files already formatted`；
  `mypy` = `Success: no issues found in 1107 source files`；规模门 `1125 passed`。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-07 | IN_PROGRESS | cycle 1 开工：ADR-0033 先落，再实现与判据。 |
| 2026-10-07 | DONE | 七条 AC 全 PASS（`RECHECK-20261007-304` = PASS_WITH_WARNINGS）。 |

## 影响报告

- **Domain/API/schema**：`ResearchTaskState` 新增 `Transition.REQUEUE` 与**一条**出边；
  `WorkflowEngine` Port 新增 `requeue`（**无 HTTP 面**——本轮不新增路由，故 OpenAPI 快照与
  web 类型零改动）；`RecordType` 词表**零扩张**（复用 `task.retry_scheduled`）。
- **安全/凭据**：零影响（无凭据、无策略、无网络）。
- **兼容性/迁移**：无数据迁移。既有 `DEAD_LETTER` 行第一次被恢复时走新路径；
  `terminal()` 的消费点逐条未改（守卫语义不变）。
- **上游版本**：零影响（无依赖变更）。
- **下一项任务**：cycle 2 = EC-02（`R26-5` 取证追认）。
