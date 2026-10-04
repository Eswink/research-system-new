---
id: PLAN-20261005-281
slug: goal-029-ec04-05-two-tree-archives-and-self-bootstrap-closeout
title: GOAL-029 cycle 4+5（EC-04 / EC-05）：两树判词归档留档 + 自举收口（验证器进树 + TWO-TREE PASS + m0）
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-282-goal-029-ec05-self-bootstrap-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20261005-186-two-tree-verdict-write-is-input-output.md
parent_goal: GOAL-20261004-029
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261004-029 的 **EC-04 与 EC-05**。授权沿用该 GOAL 的 `authorization.ref`：
    「新增判据 / 夹具（落 `tests/**`）」+「收口验证器进树」+ push-to-main-for-CI 口径
    （**只推 `main`**、不 force、不重写历史、不推旁支；push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面（对
    `IN_SCOPE` 的改动是**纯收紧**：只追加两个本轮新增脚本）；**不改** `PRODUCT_ROOTS` /
    m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
    deduplication）。
objective: >-
    收 GOAL-028 发现的两个缺口：**①** 两树复检只留 log（且是 PowerShell 重定向的 CRLF），
    **判词文件本身没有独立归档** ⇒ 「两树逐行相同」缺可独立复核的物证（EC-04）；
    **②** 收口验证器进树 + 两树同结论 + m0 + 治理 + 台账（EC-05）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **两份判词归档在树**（二进制写盘）：`sha256` 相同、行尾为 **LF**（逐字节扫 `\\r`）、
      判词纯度（只有判词行前缀）、路径无关（无盘符）；落点**不被 `.gitignore` 覆盖**。
    status: PASS
  - id: AC-2
    criterion: >-
      **两向反证**：文本模式写一份 ⇒ 判红（`sha256` 不同 + 含 CR）；二进制复原 ⇒ 绿。
      另固定两条「为什么必须读 raw bytes」的实测事实（文本模式写 CRLF + `.gitattributes`
      的 `eol=lf` 会静默归一化 ⇒ `git diff` 不足以充当逐字节证据）。
    status: PASS
  - id: AC-3
    criterion: >-
      **收口验证器进树**（`tools/verify_goal029_closeout.py`，≤450 行）**复用**
      `closeout_recheck_assertions.py` 的 `standard_verdicts`，只写本轮特有断言；
      与它复用的只读工具集（`tools/closeout_recheck_tools.py`）**双双进 `IN_SCOPE`**（纯收紧）；
      四道门（ruff / format / mypy / 规模）全绿。
    status: PASS
  - id: AC-4
    criterion: >-
      **两树同结论**：`--script tools/verify_goal029_closeout.py --script-mode shared`
      ⇒ 两树各 **54 判词**、`sha256` 相同、`COMPARE identical=True`、**`TWO-TREE PASS`**、
      两树 exit=0；两路判词**二进制写盘**到 EC-04 的归档落点。
    status: PASS
  - id: AC-5
    criterion: >-
      **as-is m0 23/23**，且**跑在记录写入之后**（独占、仓库 `.venv`、canonical DSN pin、
      不接管道、零进程残留）。
    status: PASS
  - id: AC-6
    criterion: >-
      **治理与台账**：`validate.py` 绿；CI 台账**逐提交**（`cancelled` 如实登记 + 原因；
      空集合 = 未取证）；承继残余逐条在位 + 本轮新增；未覆盖范围逐条明写。
    status: PASS
implementation:
  - id: WP-A
    title: EC-04 判据 + 两份归档落档
    files:
      - tests/tooling/test_two_tree_verdicts_are_archived.py
      - .cursor/plans/goals/evidence/GOAL-20261004-029-verdict-current.txt
      - .cursor/plans/goals/evidence/GOAL-20261004-029-verdict-clean.txt
  - id: WP-B
    title: EC-05 收口验证器 + 只读工具集 + IN_SCOPE 纯收紧
    files:
      - tools/verify_goal029_closeout.py
      - tools/closeout_recheck_tools.py
      - tests/tooling/test_tooling_scripts_meet_product_gates.py
---

## 背景

EC-04 收 GOAL-028 登记的缺口：两树复检的**判词文件本身没有独立归档**（只有 PowerShell 重定向的
CRLF log，且落在树外）⇒ 「两树逐行相同」缺可独立复核的物证。EC-05 是自举收口。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-6）。

## 实施清单

- [x] **WP-A**：`tests/tooling/test_two_tree_verdicts_are_archived.py`（13 passed）；
      两份归档落 `\.cursor/plans/goals/evidence/`（`sha256` 相同、CR=0、判词纯度、路径无关）。
- [x] **WP-A 反证**：文本模式写一份 ⇒ 2 failed；二进制复原 ⇒ 绿。
- [x] **WP-B**：`tools/verify_goal029_closeout.py`（419 行）+ `tools/closeout_recheck_tools.py`（118 行）；
      `IN_SCOPE` 追加两条（纯收紧）；四道门 8 passed。
- [x] **WP-B 自举**：两树首跑 RED（干净树是**已推送** HEAD 的 checkout，不含未提交验证器）
      ⇒ 提交推送后复跑 ⇒ **TWO-TREE PASS**。
- [x] **记录**：本 PLAN 收口（`DONE`）+ `RECHECK-20261005-282` + `ALL_PLAN` 投影 +
      GOAL 迭代日志与状态历史 + `ACHIEVED`。

## 证据

- **commit**：`e1f2b4b`（EC-04 归档 + 判据）+ `c8e0cd5`（EC-05 验证器 + 工具集 + IN_SCOPE）+
  `dcd8387`（去掉循环依赖 + 重新生成归档）+ 本条回写提交。
- **归档物证**：两份各 **2593 字节**、**54 行**、**CR count 0**、`sha256` **相同**
  （`db4faa07d42532d0dd4793a9d42b8392784ecfb761af07562e7915eb12b9a503`）。
- **两树复检**：`TREE current` 与 `TREE clean` 各 **54 判词**、同一 `sha256`、
  `COMPARE identical=True`、**`TWO-TREE PASS`**（两树 exit=0）。
- **验证器本树**：`--verdict-only` ⇒ **54 PASS / 0 FAIL**。
- **判据例数**：EC-04 判据 **13 passed**；四道门 **8 passed**。
- **本轮实测并修掉的三处自身缺陷**（详见 RECHECK 的 W-NN）：验证器自身的 mypy 两处 + 一处
  `AnnAssign` 读取缺口（判据假红）+ **一处循环依赖**（验证器读两树入口写回的文件 ⇒ 输入即输出）。
- **CI**：见 GOAL「CI 台账」（本 PLAN 三个提交逐行）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 4+5 derive）并执行 WP-A/WP-B。 |
| 2026-10-05 | DONE | WP-A/WP-B 收口；两树 **TWO-TREE PASS**（54 判词、sha256 相同）；`RECHECK-20261005-282` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：新增判据一份 + 两份归档 + 两个 `tools/` 脚本 + `IN_SCOPE` 两行（纯收紧）。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：无。
- **兼容性 / 迁移风险**：无（纯新增；`IN_SCOPE` 只增不删）。
- **上游版本影响**：无（未动依赖）。
