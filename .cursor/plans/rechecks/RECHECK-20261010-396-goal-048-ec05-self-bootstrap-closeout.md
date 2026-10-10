---
id: RECHECK-20261010-396
slug: goal-048-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-048 EC-05 自举收口（验证器 / 两树 / 归档 / 门链 / 判据自纠）
plan_id: PLAN-20261010-395
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（含 cycle 1/2 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-048-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-048-verdict-clean.txt
---

# RECHECK-20261010-396 — GOAL-20261010-048 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-395`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal048_closeout.py` / `tools/goal048_closeout_assertions.py` |
| `ruff check` / `ruff format --check` | 全绿 |
| `mypy`（strict） | Success: no issues found |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` **纯收紧** | `+2` 行；判据全绿 |
| 射程分区清单（GOAL-043 立）**同步登记** | `+1` 行 + 下界 17→18；判据全绿 |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（域可选条件 / **三种坏声明点名** / **互斥** /
两库列 / **迁移只加列** / DTO 与路由 / **快照含新字段**）·
`ec03-*`（触发助手 / **按落库判词** / **只读** / **单一来源** / 点名条件与依据 /
**判词只读一次供两处共用** / **闸门先于结论面**）·
`ec04-*`（命中 / 不命中 / 点名依据 / 条件也走同一注册面 / 未声明零调用 / HTTP 面**成对** /
坏声明 / **四按压全红与复原一致**）。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**；两路 **75 判词**、`sha256` 相同 `e6ead21f2ba7a89e…`。
归档两份各 **2831 B / 75 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. 判据自纠（独立复核，**本次最要紧的两条**）

| # | 检查 | 读数 |
| --- | --- | --- |
| 3.1 | 文本计数把**定义行**算成调用 | `ec03-the-verdicts-are-read-once-for-both-faces` 初版 `count("_verdicts(")` ⇒ `def _verdicts(` 也命中 ⇒ **假红**（实测）|
| 3.2 | 修法 | 改用 **AST 调用计数**（`_count_calls`）—— 数的是**调用**，不是文本出现 |
| 3.3 | 结论面坐标取错（承 cycle 1） | `goal040` / `goal046` 各一条拿 `_verdicts` 的**读取行**当坐标 ⇒ 判词「读一次共用」后**正当**前移 ⇒ **假红**；已改判**分派点**（`_after_hit`）|
| 3.4 | 归属 | **判据的问题**（不是产品缺陷、不是放宽）；GOAL-043 立的「零判负」判据把 3.3 **当场报出**，3.1 由本轮验证器**首跑**报出 |
| 3.5 | 两条既有资产现状 | `goal040` **59 PASS** / `goal046` **0 FAIL**；`tests/{tooling,architecture}` 全绿 |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 16**）；
8 个收口验证器全 0 判负。**as-is m0**：`PASS: profile=m0; 23 deterministic checks`
（`PASS [` 24 / `FAILED [` 0 / **5585 passed, 21 skipped**；在全部记录写完之后、独占、
仓库 `.venv`、不接管道）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tools/goal040_closeout_assertions.py` | 结论面坐标 `_verdicts` → `_after_hit` | **等价**（判的仍是「失败面分派先于结论面」；真挪到后面**仍会判红**） | 仅坐标改动（见 `numstat`）|
| `tools/goal046_closeout_assertions.py` | 同上（闸门 vs 结论面） | **等价**（同一件事；两种调用形态都认） | 仅坐标改动（见 `numstat`）|
| `tests/tooling/test_tooling_scripts_meet_product_gates.py` | `IN_SCOPE` **+2 行** | **纯收紧**（只加） | **0** |
| `tests/tooling/test_closeout_verifiers_run_their_own_assertions.py` | 射程清单 **+1 行** + 下界 17→18 | **纯收紧** | **0** |

**收窄受判面？** 无。**未**放宽任何既有断言（两条按关系改判，真挪位**仍判红**）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档与最终一轮同结论、治理与宪章判据绿、as-is m0 23/23、
CI 台账逐提交（含本 GOAL 的 `cancelled` 逐字归因与 `covered_by`）。

### Warnings

- **W-1（条件式的表达力有界；承 cycle 1 的 `W-1` ⇒ `Z-2`）**：条件限「落库判词取值命中
  声明的集合」。**不**支持跨轮聚合 / 数值阈值 / 自然语言。**不得**读成「条件可以是任意表达式」。
- **W-2（多点闸门仍不在；承 `X-2` 的另一半 ⇒ `Z-1`）**：本轮做**条件式**；
  「一个程序里声明**多个**闸门点」**不在**；两条声明**互斥**是**设计选择**。
- **W-3（催办 / 升级 / 超时取消仍不在；承 `X-1` 其余部分与 `Y-1` ⇒ `Z-3`）**。
- **W-4（D 组审批通道本身不在本 GOAL；触达即 BLOCKED）**：闸门用的是**既有**审批面。
- **W-5（判据自纠两处，已修；承 `MEM-20261010-215`）**：见上文第 3 节 —— 均属**判据**问题
  （文本计数 / 坐标取错），**不**是产品缺陷、**不**是放宽。**登记为既有代价**。
- **W-6（承继残余原样保持）**：GOAL-047 的 `Y-1` / `Y-3`；GOAL-046 的 `X-1` / `X-2` / `X-3`；
  GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；
  GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
