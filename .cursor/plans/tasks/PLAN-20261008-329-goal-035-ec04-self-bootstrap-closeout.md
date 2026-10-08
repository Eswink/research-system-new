---
id: PLAN-20261008-329
slug: goal-035-ec04-self-bootstrap-closeout
title: GOAL-035 cycle 4（EC-04）：自举收口 —— 验证器进树 + 两树复检 + 判词归档 + as-is m0 + 治理 + 台账
status: DONE
created_at: 2026-10-08
updated_at: 2026-10-08
latest_recheck: .cursor/plans/rechecks/RECHECK-20261008-330-goal-035-ec04-self-bootstrap-closeout.md
memory_entries:
  - verdict-archive-is-written-by-the-entry-it-archives
parent_goal: GOAL-20261008-035
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261008-035 的 **EC-04**（自举收口）。授权原文见该 GOAL 的
    `authorization.ref`。**本 PLAN 专属边界**：**不改**任何既有判据 / 门禁 / 阈值
    （`tools/` 两件新脚本是**新增**；`IN_SCOPE` **纯收紧**，只增不删）；判词行**不含**
    任何树的绝对路径（两树入口会拒绝）；**不读**两树写出的判词做一致性断言
    （输入即输出 ⇒ 永不收敛）；**不得**为让首轮变绿而删掉存在性断言（bootstrap 时序
    如实登记）；**不得**宣称安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
objective: >-
    把 GOAL-035 收口成**可机械复核**的终态：① **验证器进树** ——
    `tools/verify_goal035_closeout.py` 复用 `tools/closeout_recheck_assertions.standard_verdicts`
    （**一行不重写**）+ 本轮断言集 `tools/goal035_closeout_assertions.py`，两者进 `IN_SCOPE`
    （**纯收紧**）；② **两树复检** —— `tools/two_tree_recheck.py --script-mode shared`
    对「当前树 + 干净 checkout」跑同一组断言并逐行比对；**判词归档进树**
    （`.cursor/plans/goals/evidence/`，二进制写盘、`CR=0`）；③ **as-is m0 23/23**
    （在全部记录写入之后，独占、仓库 `.venv`）；④ **治理 + 宪章判据**绿；⑤ **CI 台账
    逐提交**（含本轮真红/取消的如实登记与自我指涉边界封闭）；⑥ 承继残余与未覆盖范围
    逐条明写。
exit_criteria:
  - id: AC-1
    criterion: >-
      **验证器进树且复用标准断言集**：`tools/verify_goal035_closeout.py` 调用
      `standard_verdicts(root)`（公共面一行不重写），本轮特有断言收在
      `tools/goal035_closeout_assertions.py`（三条产品轴 + 判据面 + 归档面 + 射程面）；
      `--verdict-only` 输出只有 `PASS` / `FAIL` 两种前缀且**不含任何树的绝对路径**。
    verify: >-
      `uv run --frozen --no-sync python -B tools/verify_goal035_closeout.py --root .
      --verdict-only` ⇒ 逐行判词；非判词行 0、路径行 0。
    status: PASS
  - id: AC-2
    criterion: >-
      **`IN_SCOPE` 纯收紧**：本轮两个新脚本（验证器 + 断言集）进
      `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的必备清单（只增不删），
      并过**四道门**（`ruff format --check` / `ruff check` / `mypy` / 规模 450·50）。
    verify: >-
      `uv run --frozen --no-sync python -B -m pytest
      tests/tooling/test_tooling_scripts_meet_product_gates.py -q` ⇒ 全绿。
    status: PASS
  - id: AC-3
    criterion: >-
      **两树复检 + 归档进树**：`tools/two_tree_recheck.py --script-mode shared --base-ref
      <含交付面的提交>` ⇒ `TWO-TREE PASS`（两路判词逐行相同、`sha256` 相同）；判词归档
      `.cursor/plans/goals/evidence/GOAL-20261008-035-verdict-{current,clean}.txt`
      **在树**、非空、`CR=0`；**bootstrap 时序如实登记**（归档由被归档的入口写出 ⇒
      首轮必红于「归档不存在」，次轮才全绿）。
    verify: >-
      入口两轮读数（首轮 / 次轮）+ 归档形态读数（字节数 / `CR=0` / 两份 `sha256`）。
    status: PASS
  - id: AC-4
    criterion: >-
      **as-is m0 23/23（在全部记录写入之后）**：`--profile m0 --keep-going`、独占、
      仓库 `.venv`、`uv run --frozen --no-sync python -B`、不接管道；终局行
      `PASS: profile=m0; 23 deterministic checks`；`PASS [` 24 / `FAILED [` 0。
    verify: >-
      m0 日志终局行 + `passed/skipped` 读数（收集数增量逐文件分解）。
    status: PASS
  - id: AC-5
    criterion: >-
      **治理 + 宪章判据**：`.cursor/skills/governance-check/scripts/validate.py` 绿；
      `tests/tooling/test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 在程序表序 3、
      进展记录行指向真实 RECHECK 文件）。
    verify: >-
      两条命令的终局输出。
    status: PASS
  - id: AC-6
    criterion: >-
      **承继残余与未覆盖逐条明写**：GOAL-034 的 `W-1`…`W-4` / `R26-*` 终态 /
      未覆盖范围（读面未认证 / 多租户 / RBAC / BOLA·BFLA / 部署面未验证 / `R-M1` 未收口）
      逐条在位；本轮残余 `N-1`…`N-6` 逐条定格（已收口 / 未覆盖分界）。
    verify: >-
      验证器 `residuals-enumerated` / `uncovered-scope-enumerated` / `r26-*` 判词。
    status: PASS
  - id: AC-7
    criterion: >-
      **CI 台账逐提交**：逐提交登记 run/结论（`cancelled` 如实登记 + 原因 + `covered_by`）；
      空集合 / 空字段 = 未取证；**自我指涉边界**明写并以「末条已取证提交 + 仅记录改动」封闭，
      不得循环引用。
    verify: >-
      GOAL「CI 台账」节的逐提交行 + 边界行的封闭说明。
    status: PASS
---

# PLAN-20261008-329 — GOAL-035 cycle 4（EC-04）自举收口

## 验收条件

见 frontmatter `exit_criteria`。

| AC | 主题 | 状态 |
| --- | --- | --- |
| AC-1 | 验证器进树（复用标准断言集一行未重写；判词纯且与路径无关） | PASS |
| AC-2 | `IN_SCOPE` 纯收紧 + 两脚本过四道门 | PASS |
| AC-3 | 两树复检 `TWO-TREE PASS` + 判词归档进树（`CR=0`；bootstrap 时序如实登记） | PASS |
| AC-4 | as-is m0 23/23（在全部记录写入之后） | PASS |
| AC-5 | 治理 `validate.py` 绿 + MAINLINE 宪章判据绿 | PASS |
| AC-6 | 承继残余与未覆盖范围逐条在位（`N-1`…`N-6` 定格） | PASS |
| AC-7 | CI 台账逐提交（含自我指涉边界封闭） | PASS |

## 实施清单

- [x] `tools/verify_goal035_closeout.py`：入口（标准断言集 + 本轮断言 + 记录面）。
- [x] `tools/goal035_closeout_assertions.py`：本轮特有断言（三条产品轴 + 判据面 + 归档面 + 射程面）。
- [x] `tests/tooling/test_tooling_scripts_meet_product_gates.py`：`IN_SCOPE` **纯收紧** +2 行。
- [x] `.cursor/plans/goals/evidence/GOAL-20261008-035-verdict-{current,clean}.txt`：两树判词归档。
- [x] 记录面：本 PLAN、`RECHECK-20261008-330`、`MEM-20261008-203`、GOAL 收口面（EC 终态 +
      导览表 + 残余 `N-1`…`N-6` + 迭代日志 + 状态历史 + CI 台账）、MAINLINE 进展行、`ALL_PLAN`。

## 证据

### 交付面（WP）

| # | WP | 交付面 |
| --- | --- | --- |
| WP-1 | 验证器进树 | `tools/verify_goal035_closeout.py`（入口：标准断言集 + 本轮断言 + 记录面）、`tools/goal035_closeout_assertions.py`（本轮特有断言） |
| WP-2 | `IN_SCOPE` 纯收紧 | `tests/tooling/test_tooling_scripts_meet_product_gates.py`（+2 行，只增不删） |
| WP-3 | 两树 + 归档 | `tools/two_tree_recheck.py --script-mode shared`（首轮 bootstrap 红 / 次轮 `TWO-TREE PASS`）；`.cursor/plans/goals/evidence/GOAL-20261008-035-verdict-{current,clean}.txt` |
| WP-4 | as-is m0 | `--profile m0 --keep-going`（在全部记录写入之后） |
| WP-5 | 治理 + 宪章 | `validate.py`；`tests/tooling/test_mainline_program_is_intact.py`；MAINLINE 进展记录追加一行 |
| WP-6 | 记录面 | 本 PLAN、`RECHECK-20261008-330`、GOAL 收口（EC-04 + 导览表 + 残余/未覆盖逐条 + 迭代日志 + 状态历史 + CI 台账） |

### 判据（本轮特有断言 → 每条都能被单变量按压判红）

| 轴 | 断言（摘要） | 落点 |
| --- | --- | --- |
| EC-01 | 端口 + SQLite/PG 实现 + 迁移 `016` 在树；`criterion_line` 是**唯一渲染点**；只读路由 `GET /runs/{run_id}/reviews` 在位**且已登记隐私读面清单** | `packages/application/ports/review_finding_store.py`、`adapters/{sqlite,postgres}/review_finding_store.py`、`acceptance_observation.py`、`routers/inspection.py`、`read_face_route_registry.py` |
| EC-02 | run 路径 `_audit_for` 挂到 outcome；随实验落库 `save_audit(outcome.audit)`；读面 `_apply_audit` **重算**校验（`audit_verified`） | `experiments/execute.py`、`types.py`、`experiment_support.py`、`routers/experiments.py` |
| EC-03 | 合约**自己声明**分数路径（`metric: review_decision.score`）；解析器 `declared_review_score` 在路径上被调用；**fail-closed 未变**（`review score unknown` 仍在域里） | `evaluation_gate.py`、`examples/contracts/task_contracts.yaml`、`examples/protocols/review_scored_research_v1.yaml`、`packages/domain/acceptance.py` |
| 判据面 | 三个新判据文件例数**下界**（5 / 3 / 3）；三条轴引用的既有判据仍在树 | `tests/e2e/**`、`tests/contracts/**`、`tests/observability/**`、`tests/domain/**` |
| 归档面 | 两份归档在树、非空、`CR=0`（**不读内容**做断言 —— 输入即输出） | `.cursor/plans/goals/evidence/**` |
| 射程面 | `IN_SCOPE` 含本轮两脚本且**仍钉住**入口与标准断言集 | `tests/tooling/test_tooling_scripts_meet_product_gates.py` |

### 门（实测读数）

| 门 | 读数 |
| --- | --- |
| `ruff check` | `All checks passed!` |
| `ruff format --check` | `2 files already formatted` |
| `mypy`（strict） | `Success: no issues found in 2 source files` |
| 规模（450 行 / 函数 50 行） | `238` / `191` 行（函数均在 50 行内，由判据参数化复核） |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | **8 passed** |
| `tools/verify_goal035_closeout.py --root . --verdict-only` | **70 判词 / 0 FAIL**（本树收口态） |
| 两树复检 | 首轮 bootstrap 红（读数见 `RECHECK-20261008-330` 第 3 节）；次轮 **`TWO-TREE PASS`**（两路 70 判词、`sha256` 相同） |
| as-is m0 | **`PASS: profile=m0; 23 deterministic checks`**（`PASS [` 24 / `FAILED [` 0 / **5358 passed, 20 skipped**；收集数 +0 —— 本轮只新增 `tools/` 下两脚本（不在产品根参数化面）与记录；`skipped` 20 未升） |

> **一次真红并修（如实登记）**：m0 首跑 `framework/validate` 判红 —— 本 PLAN 缺少
> `## 验收条件` / `## 实施清单` / `## 证据` 三个章节（治理校验器的 PLAN 格式契约）。
> **修记录而不是修判据**：补齐三节后**重跑**全量 m0（终局行为上面的读数，取自重跑日志）。

## 影响报告

- **Domain / API / schema 变化**：**零**（本轮只新增 `tools/` 下的机械面与记录）。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无（`IN_SCOPE` 纯收紧；既有判据一字不动）。
- **观测隐私**：无新出口。
- **上游版本影响**：无。
- **下一项任务**：收口后**立即开下一个 GOAL**（MAINLINE 程序表序 4 起）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-08 | IN_PROGRESS | WP-1/WP-2 落地（两脚本进树 + `IN_SCOPE` 纯收紧 + 四道门绿）；WP-3 首轮 bootstrap 红（归档未生成，属预期时序）。 |
| 2026-10-08 | DONE | WP-3…WP-6 全部落地：两树次轮 `TWO-TREE PASS`（首轮 bootstrap 时序如实登记）、归档进树（`CR=0`）、治理 + 宪章判据绿、CI 台账逐提交。**m0 首跑 `framework/validate` 判红**（本 PLAN 缺三个格式章节）⇒ 修记录后重跑为 23/23（如实登记，未改判据）。`RECHECK-20261008-330` 独立复检。 |
