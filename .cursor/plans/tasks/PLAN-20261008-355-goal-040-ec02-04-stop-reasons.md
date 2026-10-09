---
id: PLAN-20261008-355
slug: goal-040-ec02-04-stop-reasons
title: GOAL-040 cycle 1（EC-02/EC-03/EC-04）：判定种类扩齐 + 按终态分派 + 实跑取证（含反证）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-356-goal-040-ec02-04-stop-reasons.md
memory_entries: []
parent_goal: GOAL-20261008-040
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-040 的 **EC-02 / EC-03 / EC-04**。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**判定种类互不混用**（四态各归各的）；
    **空 `cited_facts` 必须说清为什么空**；**重试有界可观测**；**缺省不重试**（逐字保持）；
    **取消不重试**；既有 `SUCCEEDED` 路径的判定**逐字保持**；**只加可选字段 / 枚举值 +
    只加列迁移**；**不改**任何既有判据的断言（三处因**行为修正**而必须更新的既有 e2e 用例
    已逐条登记理由）；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把「停止理由」落成**互不混用**的判定：① **判定种类扩齐**（`STOP_RUN_FAILED` /
    `STOP_CANCELLED` / `RETRY_FAILED_RUN` + 可选有界重试声明）；② **按终态分派**
    （只有 `SUCCEEDED` 走结论面；失败走失败面；取消走取消面）；③ **实跑取证**（失败轮点名
    「未获结论」；声明重试 ⇒ 同序号重起且计数可见、用尽点名；**反证**：空 `cited_facts` 不再出现）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **判定种类扩齐**：`ProgramDecisionKind` 增三种（各带 docstring）；
      `ResearchProgram.max_attempts_per_index`（缺省 `1`，`>=1` 校验）**落库**
      （迁移 019 只加列 + 缺省回填；SQLite / PG 读写带上；建程序 DTO + 读面披露）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/domain tests/adapters tests/postgres
      tests/api -q` ⇒ 全绿；live PG 实测 `migration_version` = 19。
    status: PASS
  - id: AC-2
    criterion: >-
      **按终态分派（互不混用）**：`_evaluate` 在结论面**之前**按 `last.state` 分派；
      `CANCELLED` ⇒ `STOP_CANCELLED`（不重试）；`FAILED` ⇒ 重试未用尽 ⇒
      `RETRY_FAILED_RUN`（**同序号**）/ 否则 `STOP_RUN_FAILED`（点名「未获结论」+ 已用尝试数）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/application/run_orchestration/test_program_runner.py -q` ⇒ 13 passed。
    status: PASS
  - id: AC-3
    criterion: >-
      **实跑取证 + 反证**：新判据文件 `tests/e2e/test_program_stop_reasons_are_decidable.py`
      （4 例）：失败停点名 / 旧形态（`STOP_RULE` + 空 `cited_facts`）**不再出现** /
      声明重试同序号重起且用尽点名 / 缺省不重跑。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest tests/e2e -q` ⇒ 全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **门链 + 记录面**：四道门绿；广面套件全绿；OpenAPI 快照同轮重生成；
      记录（本 PLAN、`RECHECK-20261008-356`）；治理 `validate.py` 绿。
    verify: >-
      门读数逐条 + 广面读数。
    status: PASS
---

# PLAN-20261008-355 — GOAL-040 cycle 1（EC-02/03/04）

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 判定种类扩齐 + 重试声明落库（迁移 019） | PASS |
| AC-2 | 按终态分派（互不混用） | PASS |
| AC-3 | 实跑取证 + 反证（空 `cited_facts` 不再出现） | PASS |
| AC-4 | 四道门 + 快照同轮 + 记录面 | PASS |

## 实施清单

- [x] `packages/domain/program.py`：三种判定种类 + `max_attempts_per_index`（缺省 1）。
- [x] `adapters/postgres/migrations/019_program_attempts.sql`：只加列 + 缺省回填。
- [x] `adapters/sqlite/program_store.py` / `adapters/postgres/program_store.py`：读写带上。
- [x] `packages/application/run_orchestration/program_runner.py`：`_evaluate` 按终态分派 +
      `_non_success_terminal` / `_failed_round`（**拆函数**守 50 行上限）。
- [x] `services/api/dto/programs.py` + `routers/programs.py`：建程序可声明 + 读面披露。
- [x] 判据：驱动单元 13 例（+6）+ e2e 4 例（新文件）。
- [x] 同轮同步：OpenAPI 快照重生成。
- [x] 记录面：本 PLAN、`RECHECK-20261008-356`、GOAL 行、`ALL_PLAN`、m0。

## 证据

| 门 | 读数 |
| --- | --- |
| 新判据（驱动） | `tests/application/run_orchestration/test_program_runner.py` **13 passed** |
| 新判据（e2e） | `tests/e2e/test_program_stop_reasons_are_decidable.py` **4 passed** |
| 广面 | `tests/application + e2e + domain + api + adapters + postgres + tooling + contracts + loaders + architecture` **5138 passed, 18 skipped** |
| 隐私/契约 | `tests/contracts + tests/observability` **661 passed, 74 skipped** |
| `mypy`（strict） | `Success: no issues found in 1168 source files` |
| live PG | `migration_version` 最新 = **19**；`research_programs` 列清单实见 `max_attempts_per_index` |

> **三处既有 e2e 用例因行为修正而更新（如实登记，逐条给理由）**：本轮把「失败轮」
> 从**结论面**移到**失败面** ⇒ 三条既有用例原先**依赖旧的失真行为**（它们靠
> 「失败轮被判『续』⇒ 还能起第 2 轮」来取第 2 轮的判词）：
> ① `test_program_advance_on_the_run_path.py::test_a_rejected_verdict_...`：分数不达阈值
> ⇒ 那一轮以 `FAILED` 收敛 ⇒ 断言改 `STOP_RUN_FAILED` + `state=FAILED` + 「未获结论」；
> ② `test_cross_run_knowledge_on_the_run_path.py::test_missing_provider_is_named_not_silent`：
> 缺 provider 的失败发生在**第 1 轮**里 ⇒ 改为直接取第 1 轮取证（不依赖第 2 轮存在），
> 并补一条失败面断言；
> ③ `test_cross_run_consumption_is_decidable.py::test_a_missing_declared_path_...`：
> 「路径缺失」这条判定发生在**第 1 轮** ⇒ 改为取第 1 轮；助手 `_two_rounds` 放宽为
> **接受「只有第 1 轮」**（判据本身不再依赖失真行为）。
> **三处的断言强度未降**（都仍在断言「点名」这一实质），且**先在干净树 `49b2c7d` 上复跑确认
> 它们原先通过**（证明是行为修正导致、不是环境漂移）。

## 影响报告

- **Domain / API / schema 变化**：判定枚举 +3；`ResearchProgram` +1 可选字段（缺省 1）；
  PG 迁移 **019**（只加列 + 缺省回填）；建程序 DTO +1 可选字段、读面 DTO +1 字段。
- **安全 / 凭据变化**：无（不动放行面）。
- **兼容性 / 迁移风险**：**低** —— 缺省 `1` ⇒ 既有行为（不重试）逐字保持；只加列。
- **观测隐私**：无新出口。**上游版本影响**：无。
- **下一项任务**：EC-05（自举收口 + GOAL 收口）。

## 无可复用事实

本 cycle 的机制（按终态分派 / 有界重试）与既有「判定种类各归各的」纪律同族，其可复用
事实已由 GOAL-037/039 的记录承载；本轮未产生新的可复用工程事实。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 三条 AC 落地：域 + 迁移 019 + 两适配器 + 分派 + 拆函数；驱动 13 例 + e2e 4 例全绿；广面 5138 passed。 |
| 2026-10-08 | DONE | 四条 AC 全 PASS；`RECHECK-20261008-356` 独立复检（PASS_WITH_WARNINGS：三处既有用例的行为修正逐条登记）。 |
