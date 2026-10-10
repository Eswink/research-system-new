---
id: RECHECK-20261010-404
slug: goal-050-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-050 EC-05 自举收口（验证器 / 两树 / 归档 / 门链 / 判据自纠）
plan_id: PLAN-20261010-403
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（含 cycle 1/2 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-050-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-050-verdict-clean.txt
---

# RECHECK-20261010-404 — GOAL-20261010-050 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-403`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal050_closeout.py` / `tools/goal050_closeout_assertions.py` |
| `ruff check` / `ruff format --check` | 全绿 |
| `mypy`（strict） | Success: no issues found |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` **纯收紧** | `+2` 行；判据全绿 |
| 射程分区清单（GOAL-043 立）**同步登记** | `+1` 行 + 下界 19→20；判据全绿 |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（两向都在 / 反向链接**一次扫描** /
四态分开计数）· `ec03-*`（四态常量 + `disposition_of` 收可选维 + 消费端**两因分开点名** +
未知态仍 fail closed + 两因皆有时都点名）· `ec04-*`（七条用例逐条点名 + 四按压全红与复原一致）。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**；两路 **64 判词**、`sha256` 相同 `01ab4af0c1a45fe6…`。
归档两份各 **2369 B / 64 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. 判据自纠（独立复核）

| # | 检查 | 读数 |
| --- | --- | --- |
| 3.1 | **判据内嵌源码字面折行** | `ec03-the-consumer-splits-the-two-reasons` 初版把 `f"{len(superseded)} superseded memory record(s) "` 逐字写进判据 ⇒ 源码那行**被 ruff 折成两行** ⇒ **假红**（实测，由本验证器首跑报出）|
| 3.2 | 修法 | 改判**关系**（三组解包 + 两个理由各自成句 + 走 `parts.append` 拼接）；承 `MEM-20261010-215` |
| 3.3 | 与本 GOAL 主缺陷同族 | cycle 1 也修了 `goal045` 的**调用式逐字比对**（加关键字实参即假红）—— **同一类「按写法写死」**在本 GOAL 出现两次 |
| 3.4 | 归属 | **判据**的问题（不是产品缺陷、不是放宽）；登记为既有代价 |
| 3.5 | 修后现状 | 验证器 **64 判词 / 0 FAIL**；20 个收口验证器全 0 判负 |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 18**）；
定向套件 `tests/{application,api,e2e,domain,adapters,postgres,contracts,tooling}`
**4945 passed, 18 skipped**。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / passed/skipped 读数**待全量 m0 实测回填**；在全部记录写完之后、
独占、仓库 `.venv`、不接管道）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **+2 行** | **纯收紧**（只加） | **0** |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 射程清单 **+1 行** + 下界 19→20 | **纯收紧** | **0** |
| `tools/goal045_closeout_assertions.py`（cycle 1） | 由**调用式逐字**改判**关系** | **等价**（两向实测：真实/历史形态 `True`，摘掉冲突点名 `False`）| 1 行 = 原文本比对式 |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档与最终一轮同结论、治理与宪章判据绿、定向套件 4945 例绿、
CI 台账逐提交。

### Warnings

- **W-1（链式取代不在本轮；承 `BB-1`）**：只报**直接**链接；传递闭包**不做**。
- **W-2（冲突的处置仍不在；承 `BB-2`）**：本条只做 `supersedes`；`contradictions` 的处置
  仍是另一件事。
- **W-3（自动取代 / 推荐取代不在本轮；承 `BB-3`）**：谁取代谁是**声明**，**不**推断。
- **W-4（HTTP 读面未披露那两向链接，如实登记）**：本轮改的是**编排消费面**的读面
  （`memory.read`）；HTTP 读面（`MemoryRecordDto`）**未**披露 —— **未覆盖**。
  若后续要做，必须**同轮**同步 OpenAPI 快照（承 `MEM-20261010-216`）。
- **W-5（判据自纠一处 + cycle 1 一处同族，均已修）**：见第 3 节 —— **判据按写法写死**
  在本 GOAL 出现**两次**（收口断言集内嵌折行 / `goal045` 调用式逐字），都不是产品缺陷。
- **W-6（承继残余原样保持）**：GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；
  GOAL-047 的 `Y-1`…`Y-3`；GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-1`…`W-3`；
  GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
  GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
  GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
