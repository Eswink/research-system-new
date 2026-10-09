---
id: RECHECK-20261009-364
slug: goal-041-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261009-041 EC-05 自举收口（验证器 / 两树 / 归档 / 门链）
plan_id: PLAN-20261009-363
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-09
completed_at: 2026-10-09
owners:
  - root-agent
---

# RECHECK-20261009-364 — GOAL-20261009-041 EC-05 自举收口 独立复检

复检对象：`PLAN-20261009-363`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref b47bcd0` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal041_closeout.py`（105 行）/ `tools/goal041_closeout_assertions.py`（214 行） |
| `ruff format --check` | 2 files already formatted |
| `ruff check` | All checks passed |
| `mypy`（strict） | Success: no issues found in 2 source files |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` 纯收紧 | `+2` 行（只增不删）；判据 `test_tooling_scripts_meet_product_gates.py` **8 passed** |

**自指判词**：`self-loads-its-own-assertions` —— 本解析器读**自身源码**里
`_load_assertions` 之后的片段，确认加载的是 `goal041_closeout_assertions.py`
（不是上一轮那份）。**为什么需要**：GOAL-038/039/040 实测到「声明自己的断言集却加载
`goal037_closeout_assertions.py` ⇒ **自有断言从未运行**」的同族缺陷（GOAL-040 收口的
73 条判词里，其自有的 20 条**一条都没出现**）；本条把该形态做成机器可检事实。

### 2. 两树复检与归档（AC-2，独立重跑）

```
TREE current=D:\research-system  exit=0 verdicts=63 sha256=53b77cf68abe18c5...
TREE clean=D:\rs-goal041-clean   exit=0 verdicts=63 sha256=53b77cf68abe18c5...
COMPARE identical=True
TWO-TREE PASS
```

- 判词归档：两份各 **2323 B / 63 行 / `CR=0` / 0 FAIL**（**二进制写盘**；`git diff` 不足以
  充当逐字节证据，故本复检直接对 raw bytes 取 `sha256`）；
- **三轮时序如实登记**：`7c9b35c` ⇒ DIFF 第 42 行（`IN_SCOPE` 未进干净树）+
  归档 missing；`dfcdb56` ⇒ 只剩归档 missing；`b47bcd0` ⇒ **PASS**。
  这是 bootstrap 时序（干净 checkout 逐提交推进），不是判据缺口。

### 3. 收口验证器读数（本树独立重跑）

**63 PASS / 0 FAIL**。其中本轮特有断言 30 条（新种类 / 计数口径 / 分派顺序 /
单调 tie-breaker / 实跑判据 / 归档形态 / 射程）+ 标准断言集 + 记录面。

### 4. 记录面与治理（AC-3，独立重跑）

`validate.py` 通过（Rules / Skills / 子代理 / ALL_PLAN / Task Plan / Recheck / Memory
交叉引用一致 / GOAL 结构合规 / 版本单一源 / 无凭据材料）；
`test_mainline_program_is_intact.py` **8 passed**；grep 复核：本 GOAL 的 id 已在程序表**序 9**、
本 PLAN 与 `RECHECK-20261009-362/364` 均在树、`latest_recheck` 指向本文件。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`（两路 63 判词 / `sha256` 相同）、归档定格、治理与宪章判据绿、
CI 台账逐提交。

### Warnings

- **W-1（两树三轮时序）**：前两轮红是 bootstrap 时序（干净树逐提交推进）—— 如实登记，
  **不得**读成「判据曾被放宽」。
- **W-2（GOAL-038/039/040 的同族缺陷未修）**：三处验证器**今天仍加载 037 的那份断言集**
  （GOAL-041 起已自查，但这三处**不在本 GOAL 的修复面内**）。登记为后续输入
  （`MEM-20261009-210` 的「来源」表已引述）。
- **W-3（决策时点的修法在驱动侧）**：存储层的自然键与静默冲突处理**未变** ⇒
  **直接调用 store 的第三方**仍可撞车并静默丢事实（承 `MEM-20261009-211` 的适用边界）。
- **W-4（承继残余原样保持）**：GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
