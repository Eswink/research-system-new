---
id: RECHECK-20261010-374
slug: goal-043-third-instance
title: 独立复检：GOAL-20261010-043 收口后补正（第三处文本锚点失配 + 该类机器化）
plan_id: PLAN-20261010-373
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-374 — GOAL-20261010-043 收口后补正 独立复检

复检对象：`PLAN-20261010-373`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 第三处失配的实测（AC-1，独立重跑）

**普查口径**：对**全部 13 个**收口验证器逐个跑 `--verdict-only` 并数判负。修正前读数：
**只有 `goal031` 有 1 条判负**（其余 12 个 0 条）—— 即「13 个里 1 处仍未发现」，
这与 `U-2`（「同类脆弱性未普查」）的登记一致。

**具体那条**：`ec03-run-completed-carries-the-skip-facts`，其谓词是
`'"skipped"' in runner`（**文本**要求在 `phase_runner.py` 里出现字面量）。
**行为逐字保持**：载荷改由 `run_completion_payload.py` 产出，那里仍写 `payload["skipped"]`
（`rg '"skipped"'` 在该构造点命中）。⇒ **字面量搬了家**，判据**盯错位置**。

### 2. 结构判据修正（AC-2，独立重跑）

`_run_completed_carries_the_skip_facts(root, runner)`：接受两种形态 ——
① 字面量在原模块；② 载荷由**被 runner 调用的构造点**产出（顺导入找一个模块，在其中找该键）。
**任一缺 ⇒ 判负**（受判面**等价**）。修正后 `verify_goal031` ⇒ **80 判词 / 0 判负**。

**全量复取证**：13 个收口验证器 **全部可执行且 0 判负**。

### 3. 该类机器化（AC-3，独立重跑）

新增 `test_every_named_assertion_set_reports_no_negative_on_this_tree`
（**断言集在本树上不得有判负**）⇒ `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py`
**8 passed**。

**两向反证**：`P-3`（把 goal031 改回纯文本谓词 ⇒ **复现第三处失配**）⇒
`test_every_named_assertion_set_reports_no_negative_on_this_tree` **判红**；
二进制复原后 raw `sha256` **逐字节相同**；归档更新为三行
（`P-1`/`P-2`/`P-3`，165 B / `CR=0`）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-3 逐条独立成立：第三处失配**实测在位且已修**
（结构判据、受判面等价），该**类**由新判据机器化（含忠实复现的按压红）。

### Warnings

- **W-1（`U-2` 只部分闭合）**：三处实例（加载面 / 调用签名 / 字面量搬家）全修，且
  「断言集在本树有判负」已**可被机器发现**；但**文本锚点本身未被禁止** ——
  断言集内部仍可能用文本锚点，本判据只在它们**当前失配**时报红。
- **W-2（`U-1` 仍登记）**：**不重跑** GOAL-038/039/040/031 当时的收口复检（且历史结论**不重写**）；
  「**当时**那几轮里其自有断言/该判据的状态」如实保留在各自的 `W` 里。
- **W-3（`U-3` 仍登记）**：`tools/` 射程外旧脚本仍无机器门。
- **W-4（承继残余原样保持）**：GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
