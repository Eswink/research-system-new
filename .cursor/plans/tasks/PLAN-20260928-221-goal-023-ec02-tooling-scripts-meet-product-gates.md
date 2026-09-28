---
id: PLAN-20260928-221
slug: goal-023-ec02-tooling-scripts-meet-product-gates
title: GOAL-023 cycle 2（EC-02）：tools/ 受判面以新增判据收口 —— 有界射程 + 四道门 + 修入口自身的规模与复杂度
status: DONE
created_at: 2026-09-28
updated_at: 2026-09-28
parent_goal: GOAL-20260928-023
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260928-023 的 **EC-02**（`tools/` 受判面收口，收 GOAL-022 EC-01 的 `W-1`：
    入口无格式 / 类型 / 规模门）。授权沿用该 GOAL 的 `authorization.ref`：范围严格限定为
    「复检资产归档化 + **`tools/` 受判面以新增判据形式收口** + 受判射程边界机械化」
    + **修被新判据证明的缺陷** + **文档同源更新**；**不改安全策略、不放宽任何判据**；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**、默认门**一律离线**。
    **本 PLAN 专属边界（形式硬约束）**：**必须是「新增判据」** ——
    **不得**改 `PRODUCT_ROOTS`、**不得**改任何既有 check、**不得**改 `.github/workflows/**`
    的作业结构、**不得**改 m0 条数（终态行必须仍是 `23`）；
    **不得**把历史遗留 `tools/` 脚本纳入射程然后为使其变绿而改历史资产；
    **不得**新增依赖；**不得**修 `main` 时改既有行为判据的断言迁就。
exit_criteria:
  - id: AC-1
    criterion: >-
      新判据对**被点名脚本集**执行与产品同款的四道检查：`ruff format --check`、
      `ruff check`（含 `max-complexity = 10`、行宽 100）、规模（函数 ≤ 50 行、文件 ≤ 450 行）、
      `mypy`（既有 `strict` 配置；**实测可稳定机械执行** ⇒ 无豁免）
    status: PASS
  - id: AC-2
    criterion: >-
      射程**有界**：判据源码里**固化的必备清单**（≥ 入口与断言集）**加**规范页点名的文件；
      **不**扫整个 `tools/`；历史遗留以**清单 + 理由**逐条登记，且**清单增删必须显式**
      （未分类脚本 ⇒ 判红）
    status: PASS
  - id: AC-3
    criterion: >-
      **首个受判对象是红的**（实测复核）：入口 `main` = 53 行 > 50 + `ruff check` 报
      `complex-structure 14 > 10` ⇒ 先**修入口**；`tests/tooling/test_two_tree_recheck_entry.py`
      的 **11 例断言一字未改且保持全绿** ⇒ 判据拿到「真红 → 绿」，不是空真
    status: PASS
  - id: AC-4
    criterion: >-
      **反证三向**（去格式化 / 重新引入复杂度 / 把某函数撑过 50 行）**各自**只让对应的那一道门
      判红；逐字节复原（raw `sha256`）⇒ 绿；另有一条 hermetic 判据自身按压证明四道门都会检测
    status: PASS
  - id: AC-5
    criterion: >-
      新判据自身落在 `tests/**` ⇒ 自洽通过既有 50/450 门与格式门；m0 条数仍 `23`；
      as-is 本机 m0 到 23/23 且运行**在记录写入之后**（承 MEM-145）
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260928-222-goal-023-ec02-tooling-scripts-meet-product-gates.md
memory_entries:
  - .cursor/memory/entries/MEM-20260928-158-bounded-scope-must-be-partitioned-explicitly.md
---

# PLAN-20260928-221 — GOAL-023 cycle 2（EC-02）：`tools/` 受判面以新增判据收口

**主题**：`tools/` **不在** `PRODUCT_ROOTS` ⇒ 落在 `tools/` 的脚本**不被** ruff / mypy / 规模门
覆盖（GOAL-022 EC-01 的 `W-1` / `W-4`）。本轮**不改** `PRODUCT_ROOTS`（那属另行授权）、
**不改**任何既有 check、**不改** m0 条数，而是**新增判据**对一个**有界射程**执行同款四道门。

**第一个受判对象就是红的**：入口自身的 `main` = **53 行** > 50，`ruff check` 报
`complex-structure: main is too complex (14 > 10)` ⇒ 本 PLAN 的**第一步是修入口**。
这使判据拿到「**真红 → 绿**」，而不是 MEM-156 警告的「受判集合为空 ⇒ 判据尚未生效」的空真。

## 验收条件

| # | 条件 | 状态 |
| --- | --- | --- |
| AC-1 | 四道门（format / lint / 规模 / mypy）对被测脚本集机械执行 | **PASS** |
| AC-2 | 射程有界：判据源码必备清单 ∪ 规范页点名；历史遗留清单 + 理由；增删显式 | **PASS** |
| AC-3 | 首个受判对象真红（53 行 / 复杂度 14）→ 修入口 → 绿；11 例未改且全绿 | **PASS** |
| AC-4 | 反证三向各自只红对应门 + 逐字节复原；hermetic 四门检测 | **PASS** |
| AC-5 | 新判据自洽过规模 / 格式门；m0 仍 23；as-is m0 在记录之后 | **PASS** |

## 实施清单

- [x] WP1（`44bfb31`）：修入口 —— 从 `main`（53 行 / 复杂度 14）拆出
      `resolve_worktree_dir` / `prepare_clean_tree` / `run_assertions` / `dump_verdicts` / `report`；
      `main` → **21 行**，`report` **19 行**，全文件**无**超 50 行函数。
- [x] WP2（`507b250`）：新判据 `tests/tooling/test_tooling_scripts_meet_product_gates.py`（8 例）。
- [x] WP3（`341038c`）：规范页同源更新（`tools/` 仍不在 `PRODUCT_ROOTS`，但被点名脚本有了
      有界射程的机器门）。
- [x] WP4：反证三向 + 逐字节复原；记录 + m0 + push + CI 台账。

## 证据

**首个受判对象的真红 → 绿（AC-3；用 `--stdin-filename` 对**修复前**的提交内容复测 ⇒ 可复跑、零写盘）**

| 观察 | 修复前（`HEAD` 的入口） | 修复后（当前树） |
| --- | --- | --- |
| `ruff check` | **1 条错误**：`complex-structure: main is too complex (14 > 10)` | `All checks passed!` |
| 超 50 行函数（AST，口径 `end_lineno - lineno + 1`） | **`[('main', 53)]`** | **`[]`** |
| 文件行数 | 301 | 329 |
| 关键函数 | `main` = 53 | `main` = **21**、`report` = **19** |
| 既有行为判据 | —— | `tests/tooling/test_two_tree_recheck_entry.py` **11 passed**（断言**一字未改**） |

**判据自查与自洽门（AC-1 / AC-5）**

| 观察 | 结果 |
| --- | --- |
| 新判据 | `tests/tooling/test_tooling_scripts_meet_product_gates.py`，**8 例** |
| `ruff check` / `ruff format --check` | 新判据**全绿**；被按压的四道门对被测脚本集**全绿** |
| `mypy` | 被测脚本集 `Success: no issues found in 2 source files` |
| 规模自查 | 新判据自身与两个被测脚本均**无**超 50 行函数、均 < 450 行 |
| 射程实测 | `IN_SCOPE` **2** 条 + 规范页点名 **2** 条（同一集合）；历史遗留登记 **37** 条（含理由）|
| 清单完整性 | `tools/` 下 **39** 个 `.py` 全部被**显式分类**（= 2 在射程内 + 37 登记在案）|
| m0 条数 | 新判据落在 `tests/**` ⇒ 仍在 `python/tests` 收集面内 ⇒ **仍 23** |

**反证三向 + 逐字节复原（AC-4；按压 / 复原一律用 Edit 工具）**

| # | 按压（对入口 `tools/two_tree_recheck.py`） | 判据结果 | 复原（raw `sha256`） |
| --- | --- | --- | --- |
| A | **去格式化**：`print("TWO-TREE RED")` → 单引号 | **`1 failed, 7 passed`** —— 只有 `…_are_formatted` 红（lint 仍绿 ⇒ 隔离干净） | 回到 `1e867ea51ac575a0363d8a48236acc8013d94d9a4e00597604dbc7d2373c8dd2` |
| B | **重新引入复杂度**：`report()` 里临时加 9 段 if/elif | **`1 failed, 7 passed`** —— 只有 `…_pass_ruff_check` 红（`complex-structure 14 > 10`） | 同上 `1e867ea5…` |
| C | **把某函数撑过 50 行**：`report()` 里临时加 32 行注释 | **`1 failed, 7 passed`** —— 只有 `…_respect_the_size_limits` 红（`report` = 52 > 50），`ruff check` 仍绿 | 同上 `1e867ea5…` |
| D | **判据自身按压（hermetic）**：`tmp_path` 造人造坏脚本 | 四道门**各自**报出问题：`ruff format --check 不通过` / `unused-import: os imported but unused` / `mypy 不通过` / `有超过 50 行的函数：['broken']` | 不写仓库（`tmp_path`） |

三种按压**各自只让一道门判红**，与 hermetic 的四门检测互补 ⇒ 门不是空转的。

**as-is 本机 m0（记录写入之后、独占、仓库 `.venv`、DSN 固化）**

| 观察 | 结果 |
| --- | --- |
| 终态行 | `PASS: profile=m0; 23 deterministic checks`（退出码 `0`） |
| `PASS [` 行数 | **24**（`release-assets-immutable` 在计数之外） |
| `FAILED` / `ERROR` | **零** |
| 日志与时刻 | `scratch/goal023-c2-m0.log`，文件时刻**晚于**本 PLAN 与 `RECHECK-222` 的写入时刻 ⇒ 门在记录之后 |
| 治理 | `validate.py` = `Cursor 治理验证通过` |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-28 | IN_PROGRESS | 建档；先复测首个受判对象的真红（入口 `main` 53 行 / 复杂度 14），再动刀。 |
| 2026-09-28 | DONE | 五条验收全部成立且有实跑证据；`RECHECK-20260928-222` = `PASS_WITH_WARNINGS`。 |

## 影响报告

- **Domain / API / schema**：**零改动**。
- **安全 / 凭据**：**零改动**；未新增任何 token 字面量。
- **兼容性 / 迁移风险**：**无**。入口重构**不改变**任何对外行为（11 例行为判据一字未改且全绿）；
  新判据只读仓库事实。
- **上游版本影响**：**零依赖改动**；判据调用的 `ruff` / `mypy` 是**既有**开发依赖。
- **未覆盖范围（原样保留）**：读面未认证 / 多租户与 RBAC 未做 / BOLA·BFLA 未做 /
  部署面未验证 / `R-M1` 未收口（**不得**宣称项目安全）；**历史遗留 `tools/` 脚本仍不受
  任何判据覆盖**（收口需另行授权）。
- **下一项任务**：GOAL-023 EC-03（受判射程边界机械化；**新增**判据，不改既有那条判据）。
