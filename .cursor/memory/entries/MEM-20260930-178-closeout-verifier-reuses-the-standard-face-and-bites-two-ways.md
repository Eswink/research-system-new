---
id: MEM-20260930-178
title: "收口验证器必须复用 std 断言集（只写本轮特有断言）并用 AST 判缺陷修复；两树入口要求判词纯度与路径无关 —— 这三条一起让收口结论「可复跑」而不是「可信的叙述」"
status: ACTIVE
created_at: 2026-09-30
updated_at: 2026-09-30
scope: repository
confidence: 0.90
review_after: 2027-03-30
source_plans:
  - .cursor/plans/tasks/PLAN-20260930-263-goal-027-ec05-self-bootstrap-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260930-264-goal-027-ec05-self-bootstrap-closeout.md
supersedes: []
tags: [closeout, two-tree, verdict-purity, ast-assertions, goal-027, ec-05]
---

## 做了什么

用**本 GOAL 自己的机器**把五个 EC 收口（EC-05）。四条**实测**得到的装置事实：

- **收口验证器 = 标准断言集 + 本轮特有断言**：`tools/closeout_recheck_assertions.py::standard_verdicts(root)`
  覆盖受保护判据 / 规模门上限（AST 读 `450` / `50`）/ 产品根（两个载体都不得含 `tools`）/
  m0 条数（由**门运行器自己算**）/ 两树入口（无单树模式 + 两条反证用例）/ 规范页（条款小节 +
  六条口径 + INDEX 登记）/ 记录自洽（已收口的 GOAL / PLAN 的 `latest_recheck` 逐条可解析）。
  本轮验证器**一行都不重写**它们，只加 GOAL-027 特有面（逐 EC 判据 + 例数下界 / 三处缺陷修复 /
  文献源 pin 面 / MCP server 与 `IN_SCOPE` / 协议声明面 / 记录与规模）。
- **缺陷修复用 AST 判**：`_defines(text, name)`（`ast.FunctionDef`）与
  `_references_attr(text, attr)`（`ast.Attribute`）—— 「文本里出现过 `argument_digest`」
  与「真的取用了它」是两件事；文本巧合会在重构时给出假绿。
- **判词纯度与路径无关是硬要求**（规范页 ② / ⑥）：判词行只有 `PASS` / `FAIL` 前缀、
  不含任何树的绝对路径；出现别的行**拒绝服务**而不是静默过滤（静默过滤会把真差异一起丢掉）。
- **m0 条数的判据来自门运行器**：`checks_for("m0", root)` 现算 23 项，而不是「文档里写着 23」。

## 为什么这样做

- **「可复跑」比「可信」更强**：收口结论若只写在 RECHECK 里，它是一段叙述；写成进树验证器后，
  任何人 clone 仓库 `--root . --verdict-only` 就能复现同一组判词。⇒ 验证器必须**进树 + 进 `IN_SCOPE`**
  （否则它自己不受四道门约束，「受判脚本」与「判定脚本」会分叉）。
- **两树排除的是「结论依赖未提交产物」**：干净 checkout 上跑同一组断言 ⇒ 判词逐行相同
  才说明结论不依赖工作树里的残留。判词里嵌路径会让两棵树的输出天然不同 ⇒ **拒绝**而非改写
  （改写会掩盖真差异）。
- **ISO 时序**：EC-05 的判词就是收口复检产出的 ⇒ 「GOAL 的 EC-05 在跑之前仍是待判定」是
  **时序**而不是放宽；判据写成 `≥4` 个 EC 标 PASS 并把这个理由写进 docstring。

## 怎么做与复现

1. 本树：`uv run --frozen --no-sync python -B tools/verify_goal027_closeout.py --root . --verdict-only`
   ⇒ 全 `PASS`、`EXIT=0`。
2. 两树：`uv run --frozen --no-sync python -B tools/two_tree_recheck.py
   --script tools/verify_goal027_closeout.py --script-mode shared --root .` ⇒ `TWO-TREE PASS`；
   两份判词文件**二进制写盘**（`write_bytes`，规范页 ③）。
3. 四道门（验证器自己也要过）：`ruff check` / `ruff format --check` / `mypy`（strict）/
   规模（≤ 450 行）；`IN_SCOPE` 含它。

## 适用边界

- 标准断言集的覆盖面是**仓库装置面**（判据 / 门 / 记录自洽）；它**不**判定产品行为正确性
  —— 那是各 EC 的判据面。
- 判词纯度是**形式**要求：它保证两树可比，但**不**保证断言本身够强（断言强度由各 EC 的判据承担）。
- 本 GOAL 收口**不**消解读面未认证 / 多租户 / BOLA·BFLA / 部署面 / `R-M1` 这些未覆盖范围。
- **不得**据此宣称项目安全（`R-M1` 未收口）；**不得**宣称投递语义为「恰好一次」
  （**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 来源

- `PLAN-20260930-263`（GOAL-027 EC-05）与 `RECHECK-20260930-264`；
- 装置：`tools/closeout_recheck_assertions.py`、`tools/two_tree_recheck.py`、
  `tools/verify_goal027_closeout.py`、`docs/architecture/RECHECK_SCRIPT_CONVENTIONS.md`；
- 判据：`tests/tooling/test_two_tree_recheck_entry.py`、
  `tests/tooling/test_closeout_assertions_are_in_tree.py`、
  `tests/tooling/test_tooling_scripts_meet_product_gates.py`；
- 同族记忆：[[goal-closeout-procedure]]（收口步骤）、[[two-tree-recheck-mechanization]]
  （三个环境坑与进程卫生）、[[local-gate-protocol-and-flake-classes]]（m0 独占与 DSN pin）、
  [[record-face-is-gated-run-the-gate-last]]（记录面受门覆盖：门必须最后跑）。
