---
id: PLAN-20261001-273
slug: goal-028-ec05-self-bootstrap-closeout
title: GOAL-028 cycle 5（EC-05）：自举收口 — 收口验证器进树 + 两树复检 + IN_SCOPE 纯收紧 + 残余与未覆盖逐条
status: DONE
created_at: 2026-10-01
updated_at: 2026-10-01
latest_recheck: .cursor/plans/rechecks/RECHECK-20261001-274-goal-028-ec05-self-bootstrap-closeout.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-172-closeout-tools-reuse-standard-face-and-behavioural-floor.md
parent_goal: GOAL-20261001-028
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261001-028 的 **EC-05**（自举收口）。授权沿用该 GOAL 的 `authorization.ref`：
    「新增判据 / 夹具 / 探针（落 `tests/**`）」+「**新增真实现的 MCP server 或对既有自建 server
    扩展**（落 `tools/` 或既有结构，**必须**加进 `IN_SCOPE`）」（收口验证器同一条口径）+
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：新增件一律落**新文件**；**不修改**任何既有判据 / 门禁 / 阈值 /
    放行面（点名：`tools/two_tree_recheck.py`、`tools/closeout_recheck_assertions.py`、
    `tests/tooling/test_two_tree_recheck_entry.py`、
    `tests/tooling/test_closeout_assertions_are_in_tree.py`、`tests/egress_guard.py`、
    三道记录面判据、`tests/application/preflight/**`、规模门）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
    （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
    **一处对既有文件的受控改动（纯收紧、逐条留档）**：
    `tests/tooling/test_tooling_scripts_meet_product_gates.py` 的 `IN_SCOPE` ——
    **只追加** `tools/verify_goal028_closeout.py` 一个条目（EC-05 的 verify 明文要求），
    不删任何既有条目、不改任何断言。
exit_criteria:
  - id: AC-1
    criterion: >-
      **收口验证器进树且过四道门**：`tools/verify_goal028_closeout.py` 复用
      `tools/closeout_recheck_assertions.py` 的公共判词（`standard_verdicts`），
      只写本轮特有断言；**显式加入** `IN_SCOPE`（纯收紧）；`ruff check` /
      `ruff format --check` / `mypy`（strict）/ 规模（≤ 450 行）全绿；在**本树**跑出
      **零 FAIL**（逐条判词可读）。
    status: PENDING
  - id: AC-2
    criterion: >-
      **两树复检同结论**：`tools/two_tree_recheck.py --script tools/verify_goal028_closeout.py
      --script-mode shared` 跑**当前树 + 干净 checkout** ⇒ 判词**逐行相同** + 两份判词文件
      `sha256` 相同 + `TWO-TREE PASS` / `EXIT=0`；留档与判词**一律二进制写盘**。
    status: PENDING
  - id: AC-3
    criterion: >-
      **as-is 本机 m0 到 23/23**：终态行 `PASS: profile=m0; 23 deterministic checks`；
      **运行发生在记录写入之后**（承 MEM-145）；独占运行、canonical DSN pin、
      不接管道、零进程残留。
    status: PENDING
  - id: AC-4
    criterion: >-
      **治理与记录面**：`validate.py` 绿（含 `DOCS-CHECK`）；记录面判据绿；
      `latest_recheck` 是仓库相对路径且指向通过取值的复检；`child_plans` /
      `memory_entries` 与 EC 表、迭代日志互相对齐。
    status: PENDING
  - id: AC-5
    criterion: >-
      **台账到终态 + 残余与未覆盖逐条**：CI 台账**逐提交**（每个推送的提交都要有 run 行
      或结构化覆盖声明，由 `tools/audit_goal028_ledger.py` 机器复核）；
      Residuals 与未覆盖五条逐条在位；凡本机不可判定的一律 PENDING + 理由。
    status: PENDING
---

## 验收条件

承 GOAL-20261001-028 的 EC-05，五条 AC 见 frontmatter（AC-1…AC-5）。

## 实施清单

- [x] **WP-A 验证器**：`tools/verify_goal028_closeout.py`（416 行；复用
      `standard_verdicts`，只写本轮特有断言：主干交付物 AST 判定 / 判据专用协议在树 /
      `IN_SCOPE` / 逐 EC 例数下界 / 记录面残余与未覆盖 / 新增文件规模 / 文档同源）。
- [x] **WP-B `IN_SCOPE` 纯收紧**：追加本验证器一条。
- [x] **WP-C 两树复检**：提交推送后跑 ⇒ **`TWO-TREE PASS` / `EXIT=0`**，两树各 46 判词、
      `sha256` 相同（`e43cb3b0d718a078885ce46d2e93263a7b759b3ee9030962664569c35c74f2e1`）；
      留档 `scratch/goal028-c5b-twotree.log`。
- [x] **WP-D 记录 + 门 + 提交**：本回写提交 + `RECHECK-20261001-274`；m0 见 GOAL 迭代日志 cycle 5 行。

## 证据

**验证器在树跑出的判词**：**46 PASS / 0 FAIL**（标准集 + 本轮特有断言；`--verdict-only`）。

**两树复检**：`TREE current` / `TREE clean` 各 **46** 判词、`sha256` **相同**、
`COMPARE identical=True`、**`TWO-TREE PASS`**、`EXIT=0`。

**首版三处判红 + 一处规模门（全在验证器自身，已修）**：
① 例数下界按 `pytest` **收集**数写（参数化让收集数更大）⇒ 与 `def test_` **声明**数
不是一个量 ⇒ 改按声明数（docstring 写明区别）；
② `IN_SCOPE` 尚未含本文件（自举时序）⇒ 追加；
③ 子计划/复检路径写的是旧 `RECHECK-20261001-270` ⇒ 改指 `RECHECK-20261001-272`；
④ `deliverable_verdicts` >50 行 ⇒ 拆成 `_binding_face_verdicts` + `_retrieval_and_ledger_verdicts`。

**两树首跑 RED = 正确行为**：干净树是**已推送** HEAD 的 checkout，还不含未提交的验证器
⇒ 两条判词判红（`new-scripts-in-scope` / `new-files-within-size`，都点名文件不存在）。
提交推送后**复跑 ⇒ PASS**（同时是两树入口有效性的正控制）。

## 影响报告

- **Domain/schema 变化**：无。
- **API 变化**：无。
- **安全/凭据变化**：无（验证器只读树内文本）。
- **兼容性/迁移风险**：无；新增件全为新文件，唯一既有文件改动是 `IN_SCOPE` 的**纯追加**。
- **上游版本影响**：无依赖改动。
- **下一项任务**：GOAL-028 收口（EC-01…05 全 PASS + 两树 + m0 + 治理 + 台账）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-01 | IN_PROGRESS | cycle 5 派生：EC-05（自举收口）。 |
