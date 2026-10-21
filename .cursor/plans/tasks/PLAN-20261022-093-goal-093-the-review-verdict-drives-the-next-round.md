---
id: PLAN-20261022-093
slug: goal-093-the-review-verdict-drives-the-next-round
title: GOAL-093 EC-01…05 —— 上一轮评审的判词驱动下一轮的会话（第五个提示词槽位 + 跨 run 搬运）
status: DONE
created_at: 2026-10-22
updated_at: 2026-10-22
parent_goal: GOAL-20261022-093
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261022-093-goal-093-the-review-verdict-drives-the-next-round.md
memory_entries:
  - MEM-20261022-227
---

# PLAN-20261022-093 — GOAL-093 全五个 EC

## 验收条件

- [x] **EC-01**：`ReviewOutcomeView` 从前序 run 的落库判词读出面板结论 + 逐条分歧；渲染成提示词**第五段**；一负一过 ⇒ `advisory` 为 `None`、`dissent` 两位都在、`targets` 含两个执行目标；段序在检索之后、被评对象之前。
- [x] **EC-02**：五段全缺 ⇒ `compose_prompt("PURPOSE") == "PURPOSE"`；程序第一轮的每次会话 spec 上 `review_outcome_prompt is None`（经产品路径实跑）；反证臂：前序有分歧判词 ⇒ 同一装配下那一段在场且含双方 verdict。
- [x] **EC-03**：三态严格区分 —— 无前序 ⇒ `NO_PRIOR_RUN`；有前序但读不到可归因判词 ⇒ 点名 `NO_ATTRIBUTABLE` + 该轮 id；本 run 行未落库 ⇒ `NO_RUN_ROW`（**不是**失败）。未归因判词逐条点名且不进票；不属于任何程序 ⇒ 点名拒绝。
- [x] **EC-04**：真程序两轮，第二轮经**产品闭包**读到的前序恰是第一轮（经 `program_id` 反查），第一轮的分歧判词逐条可读；两个组合根都接上该闭包。
- [x] **EC-05**：记录 → `git add` 全部受判文件 → 记录面判据 → **最后**跑 m0 写见证 → 提交推送 → CI 到终态；阶梯「复检」行同轮升级；程序表序 61 + 扩表核算；读取器自举物证（产物 + 5/5 残余处置）。

## 五、EC 落点

| EC | 落点 | 判据 |
| --- | --- | --- |
| EC-01 | `packages/application/run_orchestration/review_outcome.py`（读取 + 视图）、`retrieval_prompt.py`（`REVIEW_OUTCOME_SECTION_TITLE` + 渲染器 + `compose_prompt` 第五参数） | `tests/application/run_orchestration/test_review_outcome_in_prompt.py` |
| EC-02 | 同上（空视图 ⇒ 逐字返回 purpose）+ `phase_runner.py` 的求值点 | 同左（3 条） |
| EC-03 | 同上（`NO_PRIOR_RUN` / `NO_ATTRIBUTABLE` / `NO_RUN_ROW`） | 同左（4 条） |
| EC-04 | `services/api/review_outcome_support.py` + `composition.py` / `pg_composition.py` 接线、`dependencies.py` / `phase_runner.py` / `runner_wiring.py` 的传参 | 同左（端到端 1 条）+ 组合根 grep |
| EC-05 | GOAL / PLAN / RECHECK / MEM / 宪章（序 61 + 阶梯「复检」+ 扩表核算 + 进展记录）+ 见证 | `tools/verify_goal093_closeout.py` + 见证 `terminal_line` |

## 实施清单

- [x] **WP-1**：读取层 `review_outcome.py`（`build_review_outcome` / `view_of` / `with_review_outcome`）。
- [x] **WP-2**：渲染层（标题常量 + `render_review_outcome_prompt` + `prompt_with_review_outcome` + `compose_prompt` 第五参数；段序 = 检索之后、被评对象之前）。
- [x] **WP-3**：装配链（`AgentSessionSpec.review_outcome_prompt` → `SessionSpecContext.review_outcome` → `session_prompts.review_outcome_prompt` → `session_builder` 的 `compose_prompt` 调用）。
- [x] **WP-4**：组合根接线（`OrchestrationDependencies.review_outcome` + `PhaseRunnerDeps.review_outcome` + `runner_wiring` 转交 + 两个组合根各一行）。
- [x] **WP-5**：13 条判据（5 条纯视图 + 2 条渲染/段序 + 1 条零回归 + 3 条产品路径 + 2 条读取入口）。
- [x] **WP-6**：宪章（扩表 60→70 / 序 61 / 阶梯「复检」行升级 / 战役级核算）。
- [x] **WP-7**：读取器自举（产物落 `evidence/`，5 条残余逐条处置）。
- [x] **WP-8**：记录面（GOAL / PLAN / RECHECK / MEM / 进展记录 / 归档）+ 见证 + CI 台账。

## 证据

| 证据 | 读数 |
| --- | --- |
| `tools/next_round_charter.py` 对 GOAL-092 | `exit 0`；残余 **5 条**（`W-1`…`W-5` 连续）；阶梯命中「迭代」；CI 台账 17 行（8 success / 7 无 run / 2 判红）；`sha256:419d954215f2e22f56e3e58ce50a2ed87a45f4b053aeaeaf8544f564e5a2f259` |
| 宪章三条判据 | `test_mainline_program_is_intact` / `test_mainline_research_ladder_advances` / `test_mainline_archive_is_continuous` ⇒ **20 passed** |
| 新判据 | `tests/application/run_orchestration/test_review_outcome_in_prompt.py` ⇒ **13 passed**（0 skipped） |
| 受影响套件 | `tests/application/run_orchestration/` + 聚合/方向/渲染器 ⇒ **325 passed** |
| 全量 e2e | `tests/e2e` ⇒ **369 passed / 19 skipped**（skip = 既有 Docker/live 门） |
| 规模门 | `tests/tooling/test_python_source_limits.py` ⇒ **1316 passed**（`composition.py` 恰 450 行） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-22 | **IN_PROGRESS** | 建档：WP-1…WP-7 已完成（通道落地 + 13 条判据 + 宪章扩表 + 读取器自举）。 |

| 2026-10-22 | **DONE** | 五个 EC 全达成；收口验证器 **68/68 PASS**；新判据 **13 passed**；受影响套件 **325 passed**；全量 e2e **369 passed / 19 skipped**；全 `tests/application` **1266 passed / 1 skipped**。 |

## 影响报告

| 面 | 变化 | 风险 / 迁移 |
| --- | --- | --- |
| Domain | **无**（`TrustLabel` / `Decision` / `aggregate_panel` 一行未动） | 无 |
| API / schema | **无**（不新增路由、不改 DTO） | 无 |
| 提示词装配 | 新增第五个并列槽位 `review_outcome_prompt`（缺省 `None` ⇒ 逐字不变） | 既有四段的顺序与内容不变；零回归由 `test_all_segments_absent_returns_the_purpose_verbatim` 与真 run 第一轮的 spec 断言钉住 |
| 组合根 | `services/api/composition.py` 接一行（并合并三处重复注释以守 450 行门）；`pg_composition.py` 接一行 | 无 |
| 安全 / 凭据 | **无**（只读 canonical、零出网、不读时钟） | 无 |
| 上游版本 | **无**（零新增依赖） | 无 |
| 宪章 | `max_goals` 60→70（**用户授权**）、程序表序 61、阶梯「复检」行升级、进展记录 + 修订记录各加一行（各移出一行到 archive） | 归档连续性由既有判据钉住 |