---
id: RECHECK-20261010-370
slug: goal-043-ec01-04-closeout-assets
title: 独立复检：GOAL-20261010-043 cycle 1（复检资产跑自己的断言 —— 加载面 / 崩溃面 / 机器判据）
plan_id: PLAN-20261010-369
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-370 — GOAL-20261010-043 cycle 1 独立复检

复检对象：`PLAN-20261010-369`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | 声明 / 实载逐条对拍（**修正前**形态：`038`/`039`/`040` 均实载 037 的那份） | 已在本次修复前实测；P-1 按压**复现**该形态 ⇒ 判据红 |
| 1.2 | 自有断言从未运行 | `verify_goal040_closeout.py --verdict-only` 判词里其自有断言名命中 **0**（修正前） |
| 1.3 | 断言集本身是绿的 | 直接调 `goal037/038/039` 的 `assertion_verdicts`：**34 / 21 / 21** 条、FAIL **0** |
| 1.4 | 崩溃实测 | 直接调 `goal040_closeout_assertions.assertion_verdicts` ⇒ **`ValueError: substring not found`** |
| 1.5 | 崩溃根因 | `tools/goal040_closeout_assertions.py` 用文本 `runner.index("_non_success_terminal(program, existing, last)")`；真实源码是 `_non_success_terminal(program, existing, last, programs)`（GOAL-041 正当加的形参） |

### 2. 加载面修正（AC-2，独立重跑）

| 验证器 | 修正后判词数 | FAIL |
| --- | --- | --- |
| `verify_goal038_closeout.py` | **60 PASS** | **0** |
| `verify_goal039_closeout.py` | **60 PASS** | **0** |
| `verify_goal040_closeout.py` | **59 PASS** | **0** |

**自有断言真的在跑**：`grep -c` 其自有断言名（`ec02-three-new-kinds` /
`ec03-dispatch-by-terminal-state` / `ec04-judge-asserts-the-old-shape-is-gone`）⇒ **3**（修正前 **0**）。

**判词数变化如实登记**：`verify_goal040` 的判词数 **73 → 59**（**变少**）—— 因为它改为加载
自己的 **20** 条（037 的是 **34** 条）。**换加载面必然改变条数**；组合覆盖不丢失
（037 的 34 条仍由 **037 自己的验证器**运行）。**建档时的 EC-02 子句「判词数只增不减」经实测
不成立且不该成立**，已当场改为「**跑自己的**断言」（见 GOAL 的 EC-02 正文修正段）。

### 3. 崩溃面修正（AC-3，独立重跑）

- 直接调 `goal040_closeout_assertions.assertion_verdicts` ⇒ **跑完不崩**；
- 受判面**等价性**逐条比对：原判据问「`_non_success_terminal` 的调用是否先于 `_verdicts` 调用」；
  新判据（`_dispatch_precedes_conclusion_face`）用 **AST** 按**被调名**取行号后比较
  ⇒ 仍是同一件事；且**两者任一缺失即判负**（与原文本写法同强度）；
- **反证**：把结构判据改回文本匹配（`P-2`）⇒ `test_every_named_assertion_set_is_executable_on_this_tree` **判红**。

### 4. 机器判据（AC-4，独立重跑）

新增 `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` ⇒ **7 passed**：

- `test_every_verifier_declares_the_assertion_set_it_actually_loads`（声明==实载；两种世代形态）；
- `test_every_named_assertion_set_is_executable_on_this_tree`（**可执行**：崩了就是资产坏了）；
- `test_the_verifiers_list_partitions_every_verifier_explicitly`（射程**逐条分类**：
  `031…042` 在射程 / `015`·`023…030` 登记为旧一代、理由非空、**分区不得重叠**、清单不得陈旧）；
- 四条两向反例（合成「声明 A 实载 B」/「断言集抛异常」/ 正控制 / 注释不得被骗）。

**两向反证（真形态）**：

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `P-1` | 把 `verify_goal038` 的实载改回 `goal037`（**历史缺陷原形**） | **RED**（声明==实载那条） |
| `P-2` | 把 `goal040` 的结构判据改回**文本匹配**（崩溃原形） | **RED**（可执行性那条） |

复原后 raw `sha256` **逐字节相同**；归档
`.cursor/plans/goals/evidence/GOAL-20261010-043-press-two-way.txt`（110 B / `CR=0`）。

### 5. 门链与记录面（AC-5 前置）

四道门（对本轮改动文件）**全绿**；`tests/tooling` **1422 passed**；
`ruff check tools tests` 仍有 **74** 条历史遗留（`tools/` 未入射程的旧脚本 —— 与
`MEM-20260928` 登记的「73 条」同源，本轮**未触碰**、**未新增**）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat`（相对 `59c0e31`） | 删除行读数（逐条） |
| --- | --- | --- | --- | --- |
| `tools/goal040_closeout_assertions.py` | 文本 index ⇒ **AST 结构判据** + 两个 AST 助手 | **等价**（同一关系；两者缺一仍判负） | `+38 / -2` | 删的**仅**那两行文本锚点（`runner.index("_non_success_terminal(program, existing, last)")` 与 `< runner.index("_verdicts(findings, last.id.value)")`） |
| `tools/verify_goal038_closeout.py` | 加载面 + 注释 | **等价**（不改判据） | `+3 / -1` | 删的**仅** `path = … / "goal037_closeout_assertions.py"` 这一行 |
| `tools/verify_goal039_closeout.py` | 同上 | **等价** | `+3 / -1` | 同上（仅那一行） |
| `tools/verify_goal040_closeout.py` | 同上 | **等价** | `+3 / -1` | 同上（仅那一行） |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | **新增** | — | 新增文件 | — |

**谓词逐条比对（不是「强度未降」的口头断言）**：
① `tools/verify_goal0{38,39,40}` 三处**只改「加载谁」**，判据体**一字未动** ⇒ 谓词**逐字相同**；
② `goal040_closeout_assertions.py` 那条：原谓词 = 「`_non_success_terminal` 的**文本调用**出现在
`_verdicts(findings, last.id.value)` 的**文本**之前」；新谓词 = 「`_non_success_terminal` 的
**AST 调用行号** < `_verdicts` 的 **AST 调用行号**」，且**任一缺失即返回 False**（= 判负）
⇒ 受判面**等价**（同一个关系，同一条「两者都要在场」的约束）。**无收窄**。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：三处加载面修正后**各自跑通且自有断言
真的在判词里**，崩溃面改为 **AST 结构判据**后**不再随签名演进失效**，形态由**新判据**钉住
（含射程分区与四条两向反例），两向反证打满。

### Warnings

- **W-1（判词数变少是**正确**的收窄，如实申报）**：`verify_goal040` **73 → 59**。
  这不是缺陷也不是「强度不变」——它是**换加载面**的必然结果（20 条 vs 34 条）。
  判据要的是「**跑自己的**断言」；组合覆盖由各自验证器分别承担。
- **W-2（`U-1`：不重跑历史收口复检）**：本轮让**今天**的加载面与可执行性正确并钉住形态；
  **不**重建 GOAL-038/039/040 当时的树状态去重跑它们的收口复检（且历史结论**不重写**）
  ⇒ 「**当时**那几轮复检里其自有断言**确实没跑**」这一事实**如实登记**，但不据此改写历史结论。
- **W-3（`U-2`：文本锚点未普查）**：本判据只钉「加载对 / 跑得动」；它**不**禁止断言集内部的
  文本锚点 ⇒ 其它历史断言集的同类脆弱性**未普查**。
- **W-4（`U-3`：`tools/` 射程外旧脚本仍无机器门）**；**W-5（承继残余原样保持）**：
  GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
