---
id: RECHECK-20261011-408
slug: goal-051-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261011-051 EC-05 自举收口（验证器 / 两树 / 归档 / 门链 / 恒假判据自纠）
plan_id: PLAN-20261011-407
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（含 cycle 1/2 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-051-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261011-051-verdict-clean.txt
---

# RECHECK-20261011-408 — GOAL-20261011-051 EC-05 自举收口 独立复检

复检对象：`PLAN-20261011-407`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal051_closeout.py` / `tools/goal051_closeout_assertions.py` |
| `ruff check` / `ruff format --check` | 全绿 |
| `mypy`（strict） | Success: no issues found |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` **纯收紧** | `+2` 行；判据全绿 |
| 射程分区清单（GOAL-043 立）**同步登记** | `+1` 行 + 下界 20→21；判据全绿 |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（第五态常量 / 可选维 / **优先级固定且写明** /
点名冲突 id 与「未自动消解」/ 计数第五格）· `ec03-*`（单独成组 / 「未消解」点名 /
**未知态仍 fail closed** / 两因分开）· `ec04-*`（六条用例逐条点名 + 四按压全红与复原一致）。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**；两路 **66 判词**、`sha256` 相同 `b528f7396ab1cbf5…`。
归档两份各 **2466 B / 66 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. 恒假判据自纠（独立复核，**本次最要紧的一条**）

| # | 检查 | 读数 |
| --- | --- | --- |
| 3.1 | **空判据（恒假）** | `ec02-the-disposition-takes-the-conflicted-dimension` 初版把 `"disposition_of("`（**带括号**）拿去查**裸函数名集合** ⇒ 条件**恒假**（真值在场却判负；实测）|
| 3.2 | 同类前科（同轮） | `goal045` 的 `_reason_appends_the_conflict_note` 初版给 `ast.parse` 传**片段** ⇒ 永远 `SyntaxError` ⇒ 同样恒假 |
| 3.3 | 修法 | 两条均改为**判关系**：前者查**裸名** + `conflicted` 维；后者解析**整个模块**并**两向实测**（真实/历史形态 `True`；摘掉点名/只有点名 `False`）|
| 3.4 | **为什么这档比假红更坏** | 假红立刻被注意；**恒假会静默掩盖真回归**（若哪天 `conflicted` 维被摘掉，那条判据**永远不响**）—— 由本验证器**自己的首跑**报出 |
| 3.5 | 修后现状 | 验证器 **66 判词 / 0 FAIL**；21 个收口验证器全 0 判负 |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 19**）；
定向套件 `tests/{application,api,e2e,domain,adapters,postgres,contracts,tooling}`
**4953 passed, 18 skipped**。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / **5609 passed, 21 skipped**；在全部记录写完之后、
独占、仓库 `.venv`、不接管道）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **+2 行** | **纯收紧**（只加） | **0** |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 射程清单 **+1 行** + 下界 20→21 | **纯收紧** | **0** |
| `tools/goal045_closeout_assertions.py`（cycle 1） | 由**按行文本**改判 **AST 字典值** | **等价**（同一关系：`reason` = 时效理由 **加** 冲突点名；两向实测）| 仅原比对式 |
| `tools/goal050_closeout_assertions.py`（cycle 1，两条） | 由**整行签名** / **解包变量名**改判**关系** | **等价**（同一件事；签名加维与解包加组都不再假红）| 仅原比对式 |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档与最终一轮同结论、治理与宪章判据绿、定向套件 4953 例绿、
CI 台账逐提交。

### Warnings

- **W-1（冲突的消解不在本轮；承 `CC-1`）**：本轮让「有未消解冲突」**可判定**；
  **不**做「谁对谁错」（那是**人的判断**）。
- **W-2（冲突检测不在本轮；承 `CC-2`）**：「谁和谁冲突」是**声明**，**不**推断。
- **W-3（冲突的时效性不在本轮；承 `CC-3`）**：很久以前声明的冲突是否仍算数**不在**。
- **W-4（HTTP 读面未披露处置/冲突；承序 18 的 `W-4`）**：本轮改的是**编排消费面**的读面；
  HTTP 读面（`MemoryRecordDto`）**未**披露 —— **未覆盖**。若做 ⇒ 必须**同轮**同步 OpenAPI 快照。
- **W-5（判据恒假两处，均已修；本档比假红更坏）**：本 GOAL 实测到**两处空判据**
  （收口断言集查带括号的名字对裸名集合 / `goal045` 给 `ast.parse` 传片段）——
  它们**永远不响**，会静默掩盖真回归。两处均由**验证器首跑**报出并改为判关系 / 解析整模块。
- **W-6（承继残余原样保持）**：GOAL-050 的 `BB-1` / `BB-3`；GOAL-049 的 `AA-1`…`AA-3`；
  GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；GOAL-046 的 `X-1`…`X-3`；
  GOAL-045 的 `W-2` / `W-3`；GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；
  GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
