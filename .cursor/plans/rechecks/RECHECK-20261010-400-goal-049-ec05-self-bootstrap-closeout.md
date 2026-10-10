---
id: RECHECK-20261010-400
slug: goal-049-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-049 EC-05 自举收口（验证器 / 两树 / 归档 / 门链 / 判据自纠两处）
plan_id: PLAN-20261010-399
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（含 cycle 1/2 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-049-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-049-verdict-clean.txt
---

# RECHECK-20261010-400 — GOAL-20261010-049 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-399`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal049_closeout.py` / `tools/goal049_closeout_assertions.py` |
| `ruff check` / `ruff format --check` | 全绿（两个脚本各过一遍） |
| `mypy`（strict） | Success: no issues found |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` **纯收紧** | `+2` 行；判据全绿 |
| 射程分区清单（GOAL-043 立）**同步登记** | `+1` 行 + 下界 18→19；判据全绿 |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（Port 有 scope 维 / **三适配器各一条** /
**三适配器同签名**）· `ec03-*`（读面收 scope / **点名未知范围与 `filtered_out`** /
**缺省不出现那两键** / **两个显式 DTO 形态** / **不得调用递归开关** / 快照含新入参）·
`ec04-*`（存储侧筛 / **第二 tier 守卫** / 缺省载荷 / 未知范围 / 两维并存 / HTTP 面 /
**四按压全红与复原一致**）。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**；两路 **69 判词**、`sha256` 相同 `b089a27770c7236b…`。
归档两份各 **2562 B / 69 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. 判据自纠（独立复核，**本次最要紧的两条**）

| # | 检查 | 读数 |
| --- | --- | --- |
| 3.1 | **下界条目的路径写错** | `CASE_FLOORS` 里 PG 测试写成 `tests/adapters/postgres/...`（实际 `tests/postgres/...`）⇒ `_text` 返空、计数读 **0** ⇒ 判负**当场报出** |
| 3.2 | 若没有下界判据会怎样 | 该条**不会错**，但错的**路径**会让它**静默失效**（下界形同虚设）—— 这正是「受判面非空」要防的形态 |
| 3.3 | **文本包含把解释性注释当违规** | `ec03-the-recursive-switch-is-not-used` 初版 `not in router` ⇒ 路由里「解释为什么**不**用它」的注释被判违规 ⇒ **假红** |
| 3.4 | 修法 | `_calls_named`（**AST 数关键字实参**）—— 注释/字符串里的提及不算调用；承 `MEM-20261010-215` |
| 3.5 | 归属 | **判据的问题**（不是产品缺陷、不是放宽）；两处均由**本轮验证器自己的首跑**报出 |
| 3.6 | 修后现状 | 验证器 **69 判词 / 0 FAIL**；19 个收口验证器全 0 判负 |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 17**）；
`tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` + `test_two_tree_verdicts_are_archived.py`
**22 passed**。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / **5592 passed, 21 skipped**；在全部记录写完之后、独占、
仓库 `.venv`、不接管道）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **+2 行** | **纯收紧**（只加） | **0** |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 射程清单 **+1 行** + 下界 18→19 | **纯收紧** | **0** |

**收窄受判面？** 无。**未**放宽任何既有断言。**本轮未改动任何既有判据的谓词**
（唯一的两处改动在**本轮新增的**断言集内部）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档与最终一轮同结论、治理与宪章判据绿、as-is m0 23/23、
CI 台账逐提交。

### Warnings

- **W-1（范围**不是**权限；承 cycle 1 的 `W-1` ⇒ `AA-1`）**：`scope` 是**声明的范围**。
  **不**做读面认证 / 多租户 / RBAC / BOLA·BFLA（M18 deferred）。**不得**据本条宣称任何隔离保证。
- **W-2（语义检索不在本轮；承 `AA-2` / `Q-3`）**：按**声明值**精确匹配，**不**做 embedding /
  相似度 / 模糊匹配。
- **W-3（范围治理面不在本轮；承 `AA-3`）**：自动过期 / 清理 / 容量 / 跨范围迁移**不在**。
- **W-4（`filtered_out` 的口径**，承 cycle 1 的 `W-4`）**：它是「同一 `tier` 维下、不含该范围的
  条数」（该次调用的过滤量），**不是**全库范围的历史统计。
- **W-5（判据自纠两处，已修；承 `MEM-20261010-215`）**：见上文第 3 节 —— 均属**判据**问题
  （下界路径写错 / 文本包含把注释当违规），**不**是产品缺陷、**不**是放宽。**登记为既有代价**。
- **W-6（承继残余原样保持）**：GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
  GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
  GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-2`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
