---
id: PLAN-20261008-343
slug: goal-037-ec04-idempotent-advance-and-restart
title: GOAL-037 cycle 4（EC-04）：编排步的幂等与中断（同键重放 / 崩溃窗口 DEDUP / 重启重入）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-344-goal-037-ec04-idempotent-advance-and-restart.md
memory_entries: []
parent_goal: GOAL-20261008-037
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-037 的 **EC-04**（幂等与中断，**约束**而非轴）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：口径只能是 **at-least-once + idempotency +
    deduplication**；**明确否认**「恰好一次」；判据只断言可观测事实（同键重放逐字节相同 /
    崩溃窗口不产生第二个 run / 重启从 canonical 重建），**不**断言不存在重复投递
    （那是 at-least-once 的**含义**）；**不改**任何既有判据的断言；**不得**宣称安全（`R-M1`）。
objective: >-
    把「编排步的可靠性语义」变成**机械可复核的事实**：① **同键重放** —— 同一个
    `Idempotency-Key` 重放推进 ⇒ 响应逐字节相同、run 数 / 决策数都不变；② **不同键 = 新推进**
    —— 幂等**不等于**拒绝新事实；③ **崩溃窗口** —— 上一条 `CONTINUE` 认领的 run 未落库 ⇒
    再推进落 `DEDUP` 且**不产生第二个 run**（点名人工/重试）；④ **重启重入** —— 换应用实例
    （同一 canonical 面）仍能读事实、落决策、不重复副作用；⑤ **口径守卫** —— 记录与判据里
    只用 at-least-once + 幂等 + 去重的表述（**明确否认**「恰好一次」）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **同键重放逐字节相同 + 不重复副作用**：`POST /programs/{id}/advance` 用同一
      `Idempotency-Key` 两次 ⇒ 响应体**完全相同**、程序内 run 数与决策数**都不变**。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_program_idempotency_on_the_run_path.py -q` ⇒ 全绿（5 passed）。
    status: PASS
  - id: AC-2
    criterion: >-
      **不同键按新事实推进 + 崩溃窗口 DEDUP + 重启重入**：(a) 换键 ⇒ 按事实再判一次
      （第 1 轮 `SUCCEEDED` + 判词命中 ⇒ `CONTINUE`）；(b) 预置「决策已落、run 未落库」⇒
      再推进落 `DEDUP`、`started_run_id is None`、run 数不变；(c) 新应用实例（同一 canonical
      面）⇒ 读面 run 数与推进结果都不依赖进程内记忆。
    verify: >-
      同上判据文件的其余用例（3 passed：不同键 / DEDUP / 重启重入）。
    status: PASS
  - id: AC-3
    criterion: >-
      **口径守卫（机械）**：本 PLAN / GOAL / 判据文件里出现 at-least-once + 幂等 + 去重的
      表述，且**明写否认**「恰好一次」；既有 `test_delivery_semantics_wording.py` 的分类
      判据绿（未新增 `AFFIRMATIVE`）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/architecture/python/test_delivery_semantics_wording.py -q` ⇒ 绿（6 passed）。
    status: PASS
  - id: AC-4
    criterion: >-
      **门链 + 记录面**：四道门绿；`RECHECK-20261008-344` 独立复检；治理 `validate.py` 绿；
      记录面判据绿；as-is m0 **23/23**（记录写完之后）。
    verify: >-
      门读数逐条 + `PASS: profile=m0; 23 deterministic checks`。
    status: PASS
---

# PLAN-20261008-343 — GOAL-037 cycle 4（EC-04）幂等与中断

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 同键重放逐字节相同 + 不重复副作用 | PASS |
| AC-2 | 不同键新推进 + 崩溃窗口 DEDUP + 重启重入 | PASS |
| AC-3 | 口径守卫（at-least-once + 幂等 + 去重；**明确否认**「恰好一次」） | PASS |
| AC-4 | 四道门 + 记录面 + 治理 + as-is m0 23/23 | PASS |

## 实施清单

- [x] `tests/e2e/test_program_idempotency_on_the_run_path.py`：五条用例（同键重放 / 新键推进 /
      DEDUP 崩溃窗口 / 重启重入 / 口径守卫）。
- [x] 记录面：本 PLAN、`RECHECK-20261008-344`、GOAL 行、`ALL_PLAN`、m0。

## 证据

### 交付面（WP）

| # | WP | 交付面 |
| --- | --- | --- |
| WP-1 | 判据 | `tests/e2e/test_program_idempotency_on_the_run_path.py`（5 例；全部经既有 HTTP 面） |
| WP-2 | 记录面 | 本 PLAN、`RECHECK-20261008-344`、GOAL 迭代日志 / 状态历史、`ALL_PLAN` |

### 判据要点（逐条可被单变量按压）

| 断言 | 形态 |
| --- | --- |
| 同键重放 | `replay == first`（响应体相等）+ run 数 1 + 决策数 1 |
| 不同键 | 第 2 次落 `CONTINUE` 且 `started_run_id` 与第 1 次不同、run 数 2 |
| 崩溃窗口 | 预置 `CONTINUE`（`cited_run_id` = 幽灵 id）⇒ 落 `DEDUP`、`started_run_id is None`、run 数仍 1 |
| 重启重入 | 新 `TestClient(create_app(deps))` ⇒ 读面 run 数 1，推进落 `CONTINUE`，run 数 2 |
| 口径守卫 | 两个记录文件里 `at-least-once` / 幂等 在场 + 「恰好一次」在场的**否认**形态 |

### 既有机制（本 PLAN 未新增产品面）

| 面 | 承载 |
| --- | --- |
| 同键重放 | 既有 `IdempotencyMiddleware`（mutating 请求的 replay / conflict / record） |
| 崩溃窗口 | GOAL-037 EC-02 的 `_claimed_but_missing` → `DEDUP`（驱动内） |
| 重启重入 | 程序面全读 canonical（`ProgramStore` / `RunStore`），零进程内记忆 |

## 无可复用事实

本 cycle **零产品改动**（既有幂等中间件 / `DEDUP` 判定 / canonical 重建已提供全部机制）；
本轮把它们变成可复核事实的过程没有产生新的可复用工程事实 —— 相关背景已在
`MEM-20261008-209` 与 GOAL-037 的记录里。

## 影响报告

- **Domain / API / schema 变化**：**零**（本 cycle 只新增判据与记录）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无。
- **观测隐私**：无新出口。
- **上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 立项：五条判据已落地（全绿）；记录与门链待收口。 |
| 2026-10-08 | DONE | 四条 AC 全 PASS：同键重放逐字节相同 + 不重复副作用；不同键按新事实推进；崩溃窗口 `DEDUP` 不产生第二个 run；重启重入从 canonical 重建；口径守卫绿（**明确否认**「恰好一次」）。**本 cycle 零产品改动**（机制已在，判据把它变成可复核事实）。`RECHECK-20261008-344` 独立复检。 |
