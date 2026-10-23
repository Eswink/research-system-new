---
id: PLAN-20261023-095
slug: goal-095-the-ledger-judge-reads-both-directions
title: GOAL-095 全五个 EC —— 台账判据补上反方向 + 证据域的存量矛盾聚合
status: DONE
created_at: 2026-10-23
updated_at: 2026-10-23
parent_goal: GOAL-20261023-095
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261023-095-goal-095-the-ledger-judge-reads-both-directions.md
memory_entries:
  - MEM-20261023-229
---

# PLAN-20261023-095 — GOAL-095 全五个 EC

## 验收条件

- [x] **EC-01**：反方向判据在树，且**既有 8 条判据逐字未动**。新建 `tests/tooling/goal_commit_chain.py`（谓词）与 `tests/tooling/test_goal_commit_chain_reaches_the_ledger.py`（用例）；`test_goal_ledger_covers_every_commit.py` 只加 import 与一条**挂钩**判据（import 本文件的两个谓词与两个常量，**不另造受判面**）。合计 **14 passed**。
- [x] **EC-02**：两向按压在真实树上成立。① 删 GOAL-094 台账里的 `80e844b1` ⇒ 判红并点名它；② 把 GOAL-094 移出受判面 ⇒ 同一条残缺台账变绿；③ 两次均按 raw `sha256` 逐字节复原。
- [x] **EC-03**：GOAL-094 的 `e8a1500c` / `ca4565d7` / `2c913d1f` / `f8c61422` 一提交一行补进台账（真实 run id）+ 进 cycle 行 ⇒ 正反向同时绿；**判据未因它而改**。
- [x] **EC-04**：`packages/application/memory/conflict_sweep.py`（跨记录聚合，确定性）+ `memory.read` 的可选键 `sweep_conflicts`（缺省载荷逐字不变）+ 9 条判据 + **实测成本曲线**。
- [x] **EC-05**：记录面齐备（GOAL / PLAN / RECHECK / ALL_PLAN / 宪章序 63 + 阶梯「证据」行 + 两表各一行）；m0 见证覆盖提交后的树。

## 一、EC 落点

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `tests/tooling/goal_commit_chain.py`（`chain_for` / `unledgered` / `phantom` / `floor_commit` / `untagged_code_commits` / `goal_number`） | `tests/tooling/test_goal_commit_chain_reaches_the_ledger.py`（5 条）+ 正向文件里的挂钩判据 |
| EC-02 | 同上 + 本 PLAN 第五节按压记录 | 按压脚本与 `sha256sum -c`（基线 `scratch/goal095-press-baseline.sha256`） |
| EC-03 | `.cursor/plans/goals/GOAL-20261022-094-…md`（台账 +4 行、cycle 4 `commits` 格扩展 + 一条说明） | 正反向判据 14 passed |
| EC-04 | `packages/application/memory/conflict_sweep.py`、`adapters/canonical/memory_read.py`（两行钩子） | `tests/application/memory/test_conflict_sweep.py`（9 条） |
| EC-05 | `GOAL-20261023-095` / `PLAN-20261023-095` / `RECHECK-20261023-095` / `ALL_PLAN.md` / `MAINLINE.md` | `validate.py` + 三个 mainline 判据 |

## 实施清单

- [x] **WP-1**：`goal_commit_chain.py` —— 提交链取用（**只认主题行**）、台账比对（HEAD 结构例外）、张冠李戴、无法归属的代码提交、最老链基。
- [x] **WP-2**：`test_goal_commit_chain_reaches_the_ledger.py` —— 核心 / 区间 / 两向反证 / 归因（主题行 + 编号）/ 空链点名。
- [x] **WP-3**：正向文件只加 import 与挂钩判据（按**限定名**比较，`is` 会因 pytest 双重加载判否）。
- [x] **WP-4**：GOAL-094 补 4 行台账（真实 run id 取自 GitHub API）+ cycle 4 `commits` 格扩展。
- [x] **WP-5**：`conflict_sweep.py`（`conflicts_among` / `conflict_summary` / `conflict_rows` / `conflict_sweep`）。
- [x] **WP-6**：`memory_read` 的 `sweep_conflicts` 可选键（**缺省载荷逐字不变**；钩子压到 2 行 + 1 条注释以守 450 行硬顶）。
- [x] **WP-7**：`test_conflict_sweep.py` —— 正向 / 排序稳定 / 三条边界 / 误报防线 / 只读 + 摘要 / 缺省载荷不变 / 无 IO 构造判据 / 成本形态。
- [x] **WP-8**：记录面（本 PLAN + GOAL + RECHECK + ALL_PLAN + 宪章）。

## 证据

| 证据 | 读数 |
| --- | --- |
| 台账判据（正反向） | `pytest tests/tooling/test_goal_ledger_covers_every_commit.py tests/tooling/test_goal_commit_chain_reaches_the_ledger.py -q` ⇒ **14 passed** |
| 按压①（删 `80e844b1`） | 判红：`GOAL-20261022-094（序 62）：1 个提交不在台账（链 10 个，台账 9 个）：80e844b1 feat(goal094): cross-goal ledger judge + the model-written report` |
| 按压②（移出受判面） | 同一条残缺台账：`in scope: [('GOAL-20261022-094', ['80e844b1'])]` / `excluded: []` ⇒ **变绿** |
| 逐字节复原 | `sha256sum -c scratch/goal095-press-baseline.sha256` 四文件全 `OK`（GOAL-094 `a9d5298a…` / 正向 `ad9cc0c1…` / 反向 `c96781da…` / 谓词 `c9ee898b…`） |
| GOAL-094 台账 | 补后 **10 行 = 10 个提交**（`80e844b1` / `38edc9ac` / `b07c3398` / `b911e4a0` / `b11ab450` / `068e16c4` / `f8c61422` / `2c913d1f` / `ca4565d7` / `e8a1500c`） |
| 存量矛盾聚合 | `pytest tests/application/memory/test_conflict_sweep.py -q` ⇒ **9 passed** |
| 零回归 | `pytest tests/adapters/ tests/application/memory/ tests/api/test_memory_api.py tests/api/test_memory_unknown_query_params_are_named.py -q` ⇒ **848 passed / 3 skipped** |
| 成本曲线 | n=50/100/200/400/800 ⇒ 0.0394 / 0.1707 / 0.6409 / 5.1567 / 20.7839 秒（翻倍 ⇒ 约 4 倍） |
| 类型 / 风格 | `mypy` ⇒ **1319 source files, no issues**；`ruff check` + `ruff format --check` 全过 |
| 规模门 | `memory_read.py` **447** 行（≤ 450）、`memory_read` 函数 **50** 行（≤ 50）；新增文件均在限内 |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-23 | **DONE** | 五个 EC 全部达成；判据面本地全绿（台账 14 例 + 聚合 9 例 + 零回归 848 例）；两向按压各判红/绿并按 raw `sha256` 逐字节复原。 |

## 影响报告

- **Domain / API / schema**：**无变化**。没有新增端点、没有改 DTO、没有改 `TrustLabel` ⇒
  OpenAPI 快照与 `types.ts` **无需更新**（`memory.read` 是内部工具面，不在 HTTP 契约上）。
- **新增可选面（一处）**：`memory.read` 的调用参数 `sweep_conflicts`（传了才附 `conflicts` 键）。
  缺省路径的载荷键集与取值**逐字不变**（判据钉住）。
- **安全 / 凭据**：零新增出网路径、零新增凭据（聚合是纯文本确定性判定，不调模型）。
  `tools/credential_audit.py` 四面 `offenders=0`。
- **兼容性 / 迁移风险**：无迁移（不碰 canonical schema）；存量扫描**不改**任何记录（只读）。
- **上游版本影响**：无依赖变更。
- **与 AGENTS.md 的关系**：投递语义仍是 at-least-once + 幂等 + 去重（**不是**「恰好一次」）；
  本 GOAL **不**宣称项目安全（`R-M1` 未收口）。
