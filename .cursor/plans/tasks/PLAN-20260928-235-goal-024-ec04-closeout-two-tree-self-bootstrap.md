---
id: PLAN-20260928-235
slug: goal-024-ec04-closeout-two-tree-self-bootstrap
title: GOAL-024 cycle 5（EC-04）：自举收口 —— 收口验证器进树并入必备清单 + 两树复检逐行与 sha256 一致 + 终态台账
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-024
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-024 的 **EC-04**（复用 GOAL-022 / 023 的机器）。授权沿用该 GOAL 的
    `authorization.ref`：范围为「**新增金丝雀判据与夹具**（`tests/**`）+ **文档同源更新** +
    **复用 GOAL-022/023 的收口机器**（`tools/two_tree_recheck.py` /
    `tools/closeout_recheck_assertions.py` / 同形的新验证器）」；push-to-main-for-CI 口径
    （**只推 main、不 force**）。
    **本 PLAN 专属边界**：新增验证器只**读**树（不写树、不新增依赖、不出网）；把新验证器加入
    `IN_SCOPE` 是**纯收紧**（该判据的下界断言是单调的 `required ⊆ IN_SCOPE`）；**不得**修改任何
    既有判据的断言、阈值或放行面；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口验证器进树且只写自己特有的断言**：`tools/verify_goal024_closeout.py` 复用
      `tools/closeout_recheck_assertions.py` 的公共面（标准断言集一行都不重写），
      只写 GOAL-024 特有断言（受判出口恰好六条 / 读面上下界与分区 / 七源矩阵 / 条款锚点 /
      未覆盖面 / 被点名判据存在性 / 残余与未覆盖登记在位）。
    status: PASS
  - id: AC-2
    criterion: >-
      **验证器并入必备清单（纯收紧）**：`tests/tooling/test_tooling_scripts_meet_product_gates.py`
      的 `IN_SCOPE` 增加该脚本 ⇒ 它自身必须过四道门（`ruff format --check` / `ruff check` /
      规模 / `mypy`）；既有 `IN_SCOPE` 条目一个不少（下界单调）。
    status: PASS
  - id: AC-3
    criterion: >-
      **两树一致**：用 `tools/two_tree_recheck.py`（`--script-mode shared`）在**当前树**与
      **干净 checkout** 上跑同一验证器 ⇒ 逐行判词**完全相同**（含 `sha256`），
      且 `verify_paths ≥ 2` 路声明在位。
    status: PASS
  - id: AC-4
    criterion: >-
      **终态**：EC-01…EC-03 全 PASS、EC-04 记 PASS；`latest_recheck` 为仓库相对路径且可解析；
      `child_plans` / `memory_entries` 对齐；残余（承继 12 条 + 本轮新增）+ 未覆盖范围五条
      逐条在位；as-is 本机 m0 = `PASS: profile=m0; 23 deterministic checks`（记录之后）；
      治理 `validate.py` 绿；CI 台账到终态。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-236-goal-024-ec04-closeout-two-tree.md
memory_entries: []
---

# PLAN-20260928-235 — GOAL-024 cycle 5（EC-04）：自举收口

**动因**：EC-01…EC-03 各自有判据与复检，但「这一轮到底交付了什么、哪些面没验证」还只散在
迭代日志里。EC-04 要把它们收成**可复跑的收口断言集**（进树），并用 GOAL-022/023 的两树机器
证明「当前树与干净 checkout 结论相同」——**记录面本身也是受判面**。

## 验收条件

见 frontmatter `AC-1`…`AC-4`。

## 实施清单

- [x] WP1：`tools/verify_goal024_closeout.py`（431 行；最长函数 44 行）—— 标准断言集 +
      本轮特有断言；`--root` / `--verdict-only` 与两树入口同协议；判词不含任何树的绝对路径。
- [x] WP2：`IN_SCOPE` 增加该脚本（**纯收紧**），并让该判据实跑四道门。
- [x] WP3：两树复检（当前树 + 干净 checkout）逐行 + `sha256` 比对。
- [x] WP4：记录（本 PLAN / RECHECK / GOAL 收口）+ as-is m0 + push + CI 台账终态。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 收口验证器判词 | **36 PASS / 0 FAIL**（自跑；另有 2 条在记录补齐前如实判红，补齐后转绿） |
| 规模 | 431 行（≤450）；最长函数 44 行（≤50） |
| 四道门 | `ruff format --check` / `ruff check` = `All checks passed!`；`mypy` = `Success` |
| 必备清单 | `IN_SCOPE` 4 条（原 3 条 + 本轮验证器）；该判据 8 例全绿 |
| 两树 | 见 RECHECK-236 与 GOAL 收口判词（逐行判词 + `sha256`） |

**无可复用事实**（本 PLAN 不沉淀工程记忆：收口机器与协议都是 GOAL-022/023 已沉淀形态的直接复用）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档（GOAL-024 cycle 5，EC-04）。 |
| 2026-09-28 | DONE | 验证器进树并入必备清单；两树一致；终态记录与台账补齐。 |

## 影响报告

- **Domain/API/schema**：无（`tools/**` + `tests/**` + 记录）。
- **安全/凭据**：无凭据改动；验证器只读树。
- **兼容性/迁移风险**：无（`IN_SCOPE` 是单调收紧）。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-024 收口（ACHIEVED）；后续 GOAL 另行建档。
