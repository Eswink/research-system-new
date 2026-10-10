---
id: RECHECK-20261010-392
slug: goal-047-ec05-self-bootstrap-closeout
title: 独立复检：GOAL-20261010-047 EC-05 自举收口（验证器 / 两树 / 归档 / 门链 / 真红修复）
plan_id: PLAN-20261010-391
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
verify_paths:
  - path: 当前工作树（含 cycle 1/2 全部交付与记录）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-047-verdict-current.txt
  - path: 干净 checkout（`git worktree add --detach HEAD`，同一份断言集）
    evidence: .cursor/plans/goals/evidence/GOAL-20261010-047-verdict-clean.txt
---

# RECHECK-20261010-392 — GOAL-20261010-047 EC-05 自举收口 独立复检

复检对象：`PLAN-20261010-391`。独立重跑下列机械面，不引用 PLAN 结论当证据。
**`verify_paths` 声明：2 路**（本树 + `--base-ref` 的干净 checkout，同一份断言集）。

## 检查结果

### 1. 收口面进树与四道门（AC-1，独立重跑）

| 检查 | 读数 |
| --- | --- |
| 两个脚本在树 | `tools/verify_goal047_closeout.py` / `tools/goal047_closeout_assertions.py` |
| `ruff check` / `ruff format --check` | 全绿 |
| `mypy`（strict） | Success: no issues found |
| 规模门 | 文件 ≤ 450 行、函数 ≤ 50 行（全绿） |
| `IN_SCOPE` **纯收紧** | `+2` 行；判据全绿 |
| 射程分区清单（GOAL-043 立）**同步登记** | `+1` 行 + 下界 16→17；判据全绿 |

**判词集覆盖本 GOAL 的 EC（逐条）**：`ec02-*`（注册助手 / **复用既有 Port** / **自有前缀** /
元数据与 phase 面同源 / **三种点名形态** / 幂等 / 驱动先注册后判定 / **只读判定面不得出现写方法**）·
`ec03-*`（准入助手 / **前缀分派** / run 终态 / **既有规则逐字保留** / 前缀提前返回早于状态机）·
`ec04-*`（五条按压各自的用例逐条点名 / **实跑回路成环** / **准入窄性成对** / 按压归档全红且复原一致）。

### 2. 两树复检与归档（AC-2，独立重跑）

**bootstrap 轮**：两份归档 missing（归档由本次调用写出、尚在提交之前）⇒ `TWO-TREE RED`；
两路 `COMPARE identical=True`（差异**只**在归档项）。**终态轮**（`--base-ref HEAD`）：
终局行 **`TWO-TREE PASS`**；两路 **70 判词**、`sha256` 相同 `a2ba7fa00137c70a…`。
归档两份各 **2600 B / 70 行 / `CR=0` / 0 FAIL**（二进制写盘）。

### 3. 本轮真红的修复（独立复核，**这是本次最要紧的一条**）

| # | 检查 | 读数 |
| --- | --- | --- |
| 3.1 | CI 在 `f4e8f34` 上的红 | `quality-ubuntu-latest` / `quality-windows-latest` **failure**；失败面逐字两条既有断言集判负（`goal044` / `goal046` 的「审批面只读」）|
| 3.2 | 成因 | 我把**有副作用**的注册实现放进了序 12/14 的**只读判定面** `program_waiting.py` |
| 3.3 | 修法 | 按 `phase_pause.py` 之于 `phase_runner.py` 的**同一手法**把注册单列成 `program_gate_registration.py` |
| 3.4 | 修后实测 | `program_waiting.py` 的 `register(` 与 `replace(` **各 0**；驱动**先注册后判定** |
| 3.5 | 既有资产复原 | 两个既有断言集**判负清零**（`tests/tooling` + `tests/architecture` **1715 passed**）|
| 3.6 | **判据的对错归属** | **判据是对的、实现是错的** —— GOAL-043 立的那条判据**第三次兑现价值** |

### 4. 门链与记录面（AC-3，独立重跑）

`validate.py` 通过；`test_mainline_program_is_intact.py` 绿（本 GOAL 的 id 已在程序表**序 15**）；
`tests/tooling` + `tests/architecture` **1715 passed**（8 个收口验证器全 0 判负）；
两个验证器全 0 FAIL（`goal046` **76** / `goal047` **70**）。
**as-is m0**：`PASS: profile=m0; 23 deterministic checks`（`PASS [` 24 / `FAILED [` 0 /
**5576 passed, 21 skipped**；在全部记录写完之后、独占、仓库 `.venv`、不接管道）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tools/goal046_closeout_assertions.py` | `_gate_precedes_conclusion_face` 由**定义行**改判**求值顺序** | **等价**（同一关系：闸门先于结论面；两种调用形态都认 ⇒ 搬迁不改结论；真挪到后面仍判红） | `+33 / -3` | 3 行 = 原 `_first_call_line` 的两行取行号 + 返回值行（**判的关系一字未改**） |
| `tools/goal047_closeout_assertions.py` | EC-02 判词指向新注册模块 + 新增「只读判定面」一条 | **纯收紧**（只加一条，且原判据改判更精确的落点） | `+25 / -5` | 5 行 = 落点常量与判词体的改写 |
| `packages/application/run_orchestration/program_waiting.py` | **恢复只读**（删掉误放进来的注册实现） | — | `+8 / -63` | 63 行 = **本轮刚加又撤掉的**注册实现（净效果 = 该文件回到只读面 + 判词接上注册结果）|
| `packages/application/run_orchestration/program_retry.py` | +`claimed_but_missing`（搬迁，行为等价） | **等价**（逐行搬运） | `+14 / -1` | 1 行 = `__all__` 改写 |
| `packages/application/run_orchestration/program_runner.py` | 闸门求值抽出 + 搬迁后的调用点 | **等价**（顺序仍是先注册后判定、闸门先于结论面） | `+35 / -20` | 20 行 = 被搬走的两段（`_claimed_but_missing` 与内联的闸门求值）|
| `services/api/approvals.py` | 前缀常量 import 改走新模块 | — | `+1 / -1` | 1 行 = import 行（常量值一字未改，仍是**单一来源**）|

**收窄受判面？** 无。**本轮没有放宽任何断言**；两条既有断言集的红是**修实现**（不是修判据）。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-5 逐条独立成立：收口面进树且过四道门、
两树 `TWO-TREE PASS`、归档与最终一轮同结论、治理与宪章判据绿、as-is m0 23/23、
CI 台账逐提交（含本次真红的逐字归因与修复）。

### Warnings

- **W-1（本轮 CI 真红是**实现面**缺陷，不是判据问题）**：注册实现曾落进只读判定面 ⇒
  两条既有断言集判负。**处置是修实现**（单列模块），**判据一字未改**。
  **不得**把它读成「判据过严」或「搬迁的必然代价」。
- **W-2（`program-gate:` 是**有界准入例外**；承 cycle 1 的 `W-1`）**：`decide` 的准入多了
  一个分支（前缀 + run 终态）；两侧由既有 `test_decide_requires_waiting_state` 与新配对用例钉住。
- **W-3（催办 / 升级 / 超时 / 通知不在本 GOAL；`Y-1` / `Y-3`）**：本轮让闸门**可被满足**；
  **不**做「没人拍板怎么办」。
- **W-4（条件式 / 多点闸门不在本 GOAL；`Y-2`，承 `X-2`）**：仍按**单序号**声明。
- **W-5（D 组审批通道本身不在本 GOAL；触达即 BLOCKED；承 `X-3`）**：闸门用的是**既有**审批面。
- **W-6（`has_waiting_context` 面不适用本前缀；承 cycle 1 的 `W-5`）**：程序闸门不产出 run
  状态迁移，故不受 503「上下文丢失」影响 —— **设计差异**，如实登记。
- **W-7（承继残余原样保持）**：GOAL-046 的 `X-1`（「接回」这一半由本 GOAL 推进，「催办 /
  升级 / 超时」仍保留）/ `X-2` / `X-3`；GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
  GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
