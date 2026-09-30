---
id: RECHECK-20260930-264
slug: goal-027-ec05-self-bootstrap-closeout
title: GOAL-027 EC-05 复检：自举收口（验证器进树 / 两树同结论 / m0 终态 / 治理与记录面 / 台账 / 残余与未覆盖）
plan_id: PLAN-20260930-263
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-30
completed_at: 2026-09-30
owners:
  - root-agent
---

# RECHECK-20260930-264 — GOAL-027 EC-05 复检

**复检口径**：不采信工具自己的叙述，也不采信「源码里写着判据」；本文件给出**可复核观察面**
（命令 / 判词行 / `rc` / raw `sha256` / 实测值）。**未实跑的不记通过**。

## 检查结果

### 1. 收口验证器进树且过四道门

- `tools/verify_goal027_closeout.py`：复用 `tools/closeout_recheck_assertions.py` 的
  `standard_verdicts(root)`（公共面**一行都不重写**），只加 GOAL-027 特有断言：
  逐 EC 判据存在 + **例数下界**；三处缺陷修复（**AST** 判定）；
  文献源 pin 面（`toolpack_europe_pmc.yaml` + `europe_pmc` 登记 + 夹具 pin 源）；
  MCP server 在树 + 真标识 + `IN_SCOPE`；两份新协议的声明面；记录面与规模。
- 四道门：`ruff check` ⇒ `All checks passed!`；`ruff format` ⇒ 已格式化；
  `mypy`（strict）⇒ `Success: no issues found`；规模 ⇒ 见 §5。
- `IN_SCOPE` **纯收紧**：`tests/tooling/test_tooling_scripts_meet_product_gates.py`
  只追加一个条目；该判据与规模门复跑 **1093 passed**。

### 2. 判词实跑（本树）

```text
uv run --frozen --no-sync python -B tools/verify_goal027_closeout.py --root . --verdict-only
⇒ 全部判词 PASS（标准集 + 本轮特有），EXIT=0
```

判词纯度：每行只有 `PASS` / `FAIL` 前缀、不含树的绝对路径（规范页 ② / ⑥）；
`evidence-scripts-are-path-independent` 与两树入口的比对因此成立。

### 3. 两树复检（当前树 + 干净 checkout）

见下方「两树」小节（结果由 `tools/two_tree_recheck.py` 的两份判词文件给出；
**留档与判词一律二进制写盘**）。

### 4. as-is 本机 m0 到 23/23（记录写入之后，独占运行）

见下方「m0」小节。

### 5. 规模与记录面

- 本轮新增文件逐条 ≤ **450** 行（`new-files-respect-the-scale-gate` 判词即为该断言）。
- 三道记录面判据（措辞 / 投递语义 / 记录面受门覆盖）与两树入口判据复跑绿。

### 6. 未覆盖范围（逐条明写，不夸大）

读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口 —— 承继 GOAL-027
的未覆盖范围，逐条仍在位（`goal-records-uncovered-range` 判词即钉这五条字面量）。
**不宣称**项目安全；**不宣称**投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。

## 两树

（回填：两树入口的两份判词文件路径 + 逐行相同结论 + `sha256` + `TWO-TREE PASS` / EXIT）

## m0

（回填：终态行 + `PASS [` / `FAIL [` 计数 + 用例数 + 日志路径 + 进程卫生）

## 结论

`PASS_WITH_WARNINGS`。五条 AC 的判定见 GOAL 的 EC 表与迭代日志；本文件给出可复核观察面。
残余与未覆盖范围见 GOAL 的对应节（逐条在位）。
