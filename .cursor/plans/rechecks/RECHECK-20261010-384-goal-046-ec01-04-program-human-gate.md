---
id: RECHECK-20261010-384
slug: goal-046-ec01-04-program-human-gate
title: 独立复检：GOAL-20261010-046 cycle 1（程序级人工闸门 —— 可声明 / 两库落库 / 判定点名）
plan_id: PLAN-20261010-383
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-384 — GOAL-20261010-046 cycle 1 独立复检

复检对象：`PLAN-20261010-383`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | **域实体无闸门位**（修前） | `dataclasses.fields(ResearchProgram)` 字段表 = `id` / `project_id` / `protocol_id` / `max_runs` / `continue_rule` / `max_attempts_per_index` / `created_at` / `updated_at` ⇒ **无**任何闸门位 |
| 1.2 | **程序面三文件零命中**（修前） | `rg -c "human_gated\|human_gate" packages/domain/program.py packages/application/run_orchestration/program_{runner,waiting}.py` ⇒ 全 **0** |
| 1.3 | **序 12 只做「认得状态」** | `program_waiting.py::AWAITING_HUMAN` 与 `ProgramDecisionKind.WAIT_FOR_APPROVAL` 在树（**状态**面）；声明面当时为零 |
| 1.4 | **phase 面可复用** | `human_gates.pending_human_gates` 语义 = 「声明的 `HUMAN_GATE` − 已裁决（`status` 非「待决」）」；`phase_pause.pause_for_human_gate` 含「注册 + 发事件 + 落 `WAITING_FOR_APPROVAL`」三步 |
| 1.5 | **两库无承载列** | `adapters/{sqlite,postgres}/program_store.py` 的列清单无闸门列 ⇒ **需要迁移 020** |

### 2. 声明与落库（AC-2，独立重跑）

- 域声明**可选**（`human_gate_at_index: int | None = None`）⇒ 缺省 `None`；
  越界（`> max_runs` / `0` / 负）⇒ `ValueError` 且**点名** `human_gate_at_index must be within`；
- **迁移 020 只加列**（`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，同文件无 `DROP COLUMN`）；
- SQLite 与 PG 的**写入与读取**都带该列（`_encode_program` / `_decode_program` / `_PROGRAM_SELECT` / `INSERT`）；
- 建程序 DTO 与路由透传（`ProgramCreateDto` / `ProgramDetailDto` / `create_program` / `_detail_dto`）。

**如实登记（**本 check 的边界**）**：本 cycle 落地时，上述 SQLite / PG **行为面用例**
（声明值往返 / 缺省读回 `None`）**尚未写出**（复检时实测 `rg -l human_gate_at_index tests/`
只有判定面那一个文件）；**同一 cycle 的 `verify` 行点名了它们** ⇒ 属**证据链缺口**，
由修复轮 `PLAN-20261010-387` 补齐（SQLite 5 / PG 3 / 域 10 例）并在
`RECHECK-20261010-388` 独立复检。**本条不因此把 cycle 1 记为失败** —— 缺口是
**证据**层面的，实现面经判定面用例与三向按压已可证；**也不**把它写成「已验证」。

### 3. 判定与推进（AC-3，独立重跑）

| 形态 | 判定 | 判词点名 |
| --- | --- | --- |
| 声明闸门在该轮、仍有**待决**审批 | `WAIT_FOR_APPROVAL` | `human_gate_at_index=<N>` + 待审批 id |
| 声明闸门、**缺审批面** | `WAIT_FOR_APPROVAL` | 「本装配未提供审批面」（**不**当成无闸门） |
| 声明闸门、审批面**查询抛错** | `WAIT_FOR_APPROVAL` | 「审批面查询失败（<异常类名>）」 |
| 声明闸门、该 run **无审批记录** | `WAIT_FOR_APPROVAL` | 「尚无审批记录」 |
| 声明闸门、**已裁决** | 落结论面（不拦） | —（与 phase 面同语义） |
| **未声明** | 落结论面**逐字** | 被引事实只有判词 |

**只读**：判定面只调 `list_for_run`，无 `register` / `replace`；**闸门求值先于结论面**
（AST 按被调名取行号，不靠文本巧合）。

### 4. 三向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `G-1` | 闸门被绕过（判定面恒不拦） | **RED** |
| `G-2` | 轮前也拦（不在该轮就误拦） | **RED** |
| `G-3` | 已裁决也拦（语义与 phase 面不一致） | **RED** |

复原用**二进制读写**，raw `sha256` **逐字节相同**；归档
`.cursor/plans/goals/evidence/GOAL-20261010-046-press-two-way.txt`（295 B / `CR=0`）。

### 5. 规模门逼出的搬迁撞红既有判据（独立确认）

为守 `program_runner.py` 的 **450 行硬上限**，失败重试面的计数口径被搬到新模块
`program_retry.py`（行为等价）⇒ `tools/goal041_closeout_assertions.py` 的两条断言
**按位置**写死而**假红**，**被 GOAL-043 立的「零判负」判据当场捕获** ⇒ 改成
**判关系不判位置**。登记为**搬迁的既有代价**（不是产品缺陷）。沉淀 `MEM-20261010-215`。

### 6. 门链与记录面

四道门全绿（`ruff check` / `ruff format --check` / `mypy` strict / 规模门：`program_runner.py`
**430 行**、函数全 ≤ 50）；广面 `tests/{application,adapters,domain,api,tooling}`
**3894 passed, 8 skipped**。

### 7. 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | 追加 1 例（既有 9 例一字未动） | — | `+28 / -0` | **0** |
| `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | 追加 7 例（序 12 的 7 例一字未动） | — | `+122 / -0` | **0** |
| `tools/goal041_closeout_assertions.py` | 两条按位置写死 ⇒ 判关系 | **等价**（同一关系） | `+44 / -4` | 仅那 4 行按位置写死的表达式 |

**注**：另三个测试文件（SQLite / PG / e2e）的用例在**修复轮**追加，读数见
`RECHECK-20261010-388` 的申报表。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：程序**自己**能声明闸门，
声明落 canonical（两库同契约 + 迁移只加列），该轮跑完后的推进被拦下并**点名**声明值与
待审批，缺面 / 查错 / 查不到三种形态**各自点名**，三向反证打满。

### Warnings

- **W-1（本 cycle 的证据链缺口，交修复轮）**：`verify` 行点名的两库往返用例与 HTTP 面实跑臂
  当时**未写出** ⇒ 由 `PLAN-20261010-387` 补齐（见 `RECHECK-20261010-388`）。本处如实登记。
- **W-2（闸门的处置不在本 GOAL；承 `V-1` ⇒ `X-1`）**：本轮让闸门**可声明 / 可判定 / 可点名**；
  **不**做催办 / 升级 / 超时取消。
- **W-3（条件式 / 多点闸门不在本 GOAL ⇒ `X-2`）**：本轮按**单序号**声明；
  条件式（「分数低于 X 才停」）与多个闸门点**不在**。
- **W-4（D 组审批通道本身不在本 GOAL；触达即 BLOCKED ⇒ `X-3`）**：闸门用的审批面是**既有**实例；
  不放开任何 destructive 能力的放行。
- **W-5（承继残余原样保持）**：GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
  GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-1` / `O-3` / `O-4` / `O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
