---
id: PLAN-20261008-327
slug: goal-035-ec03-review-score-linkage-on-the-run-path
title: GOAL-035 cycle 3（EC-03）：评审结论进入判据面 —— REVIEW_SCORE 三态可判 + 反证（不回落默认分）
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-328-goal-035-ec03-review-score-linkage.md
memory_entries:
  - no-score-is-not-a-low-score
parent_goal: GOAL-20261008-035
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-035 的 **EC-03**（覆盖充分 + 评审联动）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不改**既有受判面（`sort_analysis_review`
    等既有契约与它们的夹具一字不动）；**不建第二套**判据（复用既有
    `_evaluate_review_score` 与既有 fail-closed 判词）；**不得**把「缺分数」改成默认通过
    或默认分数（那是把「没有评审结论」伪装成「结论很差」）；**不得**声称分数一定正确
    （口径是「结论能进判据面且三态可判」）；**不得**宣称安全（`R-M1`）；
    **不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 EC-03 从「`REVIEW_SCORE` 判据存在但产品路径从不喂分」推进到「**评审结论真的进判据面**」：
    ① **来源被点名** —— 合约在 `REVIEW_SCORE` 判据里用 `metric` 写明分数的**结构化输出
    路径**（如 `review_decision.score`），产品路径按该路径取数；② **三态可判** —— 分数 ≥
    阈值判过、< 阈值判负并**点名那个分数**、缺来源维持既有 fail-closed
    `review score unknown`；③ **判据**：出厂合约实跑三态各自成立且判词经**既有读面**
    （GOAL-035 EC-01 的 `GET /runs/{id}/reviews`）可读；④ **反证**：把来源摘掉 ⇒ 回落
    fail-closed 并点名；按压（回落默认分）⇒ 判据判红。
exit_criteria:
  - id: AC-1
    criterion: >-
      **来源被点名 + 复用既有判据**：`declared_review_score(contract, structured_output)`
      按合约**自己声明的** `metric` 路径取数（缺路径 / 路径缺失 / 值不是数 ⇒ `None`）；
      判定仍由既有域函数 `_evaluate_review_score` 做（**不建第二套**）；**绝不**回落默认分。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/e2e/test_review_score_linkage_on_the_run_path.py -q` ⇒ 3 passed。
    status: PASS
  - id: AC-2
    criterion: >-
      **三态（判过 / 判负点名分数 / 缺来源 fail-closed）**：判词逐字为
      `review score 0.95 GTE 0.8` / `review score 0.5 GTE 0.8` / `review score unknown`；
      前两者终态 `SUCCEEDED` / `FAILED`；第三种**不得**出现分数与算子（回落默认分会让它出现）。
    verify: >-
      同文件三例分别覆盖三态。
    status: PASS
  - id: AC-3
    criterion: >-
      **声明面**：新增出厂合约 `review_scored_deliverable`（`REVIEW_SCORE` +
      `metric: review_decision.score` + `GTE` + `0.8`）与协议 `review_scored_research_v1.yaml`
      （1 phase、1 交付物）；**既有契约与夹具一字不动**（新增而非改动 ⇒ 既有受判面不变）。
    verify: >-
      `tests/loaders` + `tests/contracts` + `tests/api` + `tests/domain` + `tests/application`
      ⇒ **2372 passed, 77 skipped**。
    status: PASS
  - id: AC-4
    criterion: >-
      **反证 + 按压**：判据内建反证（缺来源臂断言无分数、无算子）；按压「回落默认分」
      ⇒ 缺来源臂判红（`assert 'SUCCEEDED' == 'FAILED'`：本该 fail-closed 的 run 会假绿）。
    verify: >-
      实测按压：**1 failed, 2 passed** ⇒ `RESTORED`（重跑 3 passed）。
    status: PASS
---

# PLAN-20261008-327 — GOAL-035 cycle 3（EC-03）：评审结论进判据面

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 来源被点名（声明路径取数）+ 复用既有判据 + 不回落 | PASS |
| AC-2 | 三态判词逐字（判过 / 判负点名分数 / 缺来源 fail-closed） | PASS |
| AC-3 | 新增合约与协议，既有受判面一字不动 | PASS |
| AC-4 | 判据内建反证 + 按压判红且复原 | PASS |

## 实施清单

- [x] `packages/application/run_orchestration/evaluation_gate.py`：`declared_review_score`
      （按声明的 `metric` 点分路径取数；缺 ⇒ `None`）+ 在 `evaluate_task_gate` 里应用
      （显式传入的分数优先，那是装配方更近的事实）。
- [x] `examples/contracts/task_contracts.yaml`：新增 `review_scored_deliverable`。
- [x] `examples/protocols/review_scored_research_v1.yaml`：新增单 phase 协议。
- [x] `tests/e2e/test_review_score_linkage_on_the_run_path.py`（3 例，判词经 EC-01 的读面读）。

## 证据

### 勘察读数（实测）

| # | 事实 | 读数 |
| --- | --- | --- |
| 1 | `review_score=` 的赋值点 | 全仓 `rg`：**只有 tests**（`tests/evals`、`tests/domain`）⇒ 产品路径**从不赋值** |
| 2 | `REVIEW_SCORE` 的出厂用法 | `rg -n "REVIEW_SCORE" examples/` ⇒ **零命中**（schema 里有该枚举值，但没有合约声明它） |
| 3 | 判定面已存在 | `_evaluate_review_score(score, operator, threshold)` 判词 `review score {score} {op} {threshold}`；缺分 ⇒ `review score unknown`（fail-closed） |
| 4 | 异构评审的角色面 | `ReviewPanelRole` 有类型、preflight 的 `role_checks` 在用（WRITER 角色）；**分数聚合不在 run 路径**（如实边界） |
| 5 | 既有契约不可加判据 | `sort_analysis_review` 的结构化输出在多条既有判据/夹具里被复用 ⇒ 加判据会让它们「缺分数」连环判负（**新增而非改动**） |
| 6 | 分数路径可用 schema 既有字段声明 | `acceptanceCriterion.metric` 已存在（字符串）⇒ **零 schema 改动** |

### 判据（新，3 例）—— 三态逐字

```
tests/e2e/test_review_score_linkage_on_the_run_path.py ... [100%]  3 passed
```

| 臂 | 输入（受控执行体声明） | 读面判词 | 终态 |
| --- | --- | --- | --- |
| ① 判过 | `score: 0.95` | `REVIEW_SCORE: review score 0.95 GTE 0.8` | `SUCCEEDED` |
| ② 判负 | `score: 0.5` | `REVIEW_SCORE: review score 0.5 GTE 0.8` | `FAILED` |
| ③ 缺来源 | 无 `score` 键 | `REVIEW_SCORE: review score unknown`（**无分数、无算子**） | `FAILED` |

### 按压（AC-4）

| # | 按压 | 读数 |
| --- | --- | --- |
| P-1 | `declared_review_score` 末尾回落 `Decimal("1")` | **1 failed, 2 passed**（③ 臂 `assert 'SUCCEEDED' == 'FAILED'`：本该 fail-closed 的 run 假绿）⇒ `RESTORED`（3 passed） |

### 门（本 PLAN 触及面）

| 门 | 读数 |
| --- | --- |
| `tests/loaders` + `tests/contracts` + `tests/domain` + `tests/application` + `tests/api` | 2372 passed, 77 skipped |
| `tests/e2e` + `tests/tooling` | 1636 passed, 13 skipped |
| **as-is m0**（冻结树，**全部记录写入之后**） | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5358 passed, 20 skipped**；收集数 +4 逐文件分解 = 新判据 3 例 + 源文件参数化 +1（`test_python_source_limits` 1150→1151，基线 `26cfa63` 同法收集）；`skipped` 20 未升；日志 `scratch/m0-goal035-cycle3.log`） |

## 影响报告

- **Domain / API / schema 变化**：**零**（复用既有 `_evaluate_review_score`；`metric` 是 schema
  既有字段；无新读面、无新 DTO ⇒ OpenAPI 快照与 web 类型**无需改**）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：**零改动面** —— 新契约与新协议是新增；既有合约、既有夹具、既有
  协议一字不动（这正是「另立一份」的理由）。未声明 `REVIEW_SCORE` 的合约行为**逐字不变**
  （`review_score` 仍为 `None` ⇒ 该判据仍 fail-closed，但那些合约并不声明它）。
- **观测隐私**：无新出口。
- **上游版本影响**：无。
- **下一项任务**：EC-04（自举收口：验证器进树 + 两树复检 + 判词归档 + as-is m0 + 治理 + CI 台账）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | 勘察定稿：`REVIEW_SCORE` 判据存在但产品路径从不喂分（`review_score=` 只在 tests）、出厂合约零声明。设计：来源 = 合约声明的结构化输出路径（`metric`，schema 既有字段）；**新增**合约与协议以不动既有受判面。 |
| 2026-10-08 | DONE | 四条 AC 全 PASS：三态判词逐字（判过 / 判负点名分数 / 缺来源 fail-closed 且无分数无算子）、声明面新增、按压「回落默认分」判红且复原。**零 domain/API/schema 改动**。`RECHECK-20261008-328` 独立复检。 |
