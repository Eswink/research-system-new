---
id: RECHECK-20261010-394
slug: goal-048-ec01-04-a-declared-gate-can-be-a-condition
title: 独立复检：GOAL-20261010-048 cycle 1（条件式程序闸门 —— 声明面 / 求值点名 / 两向反证）
plan_id: PLAN-20261010-393
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-394 — GOAL-20261010-048 cycle 1 独立复检

复检对象：`PLAN-20261010-393`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | 声明位是**单序号**（修前） | `rg -n "human_gate_at_index: int \| None" packages/domain/program.py` ⇒ **一行**，类型逐字 `int \| None` |
| 1.2 | 越界声明已点名（修前） | `must be within 1..max_runs when declared`（序 14 的判据靶子）|
| 1.3 | **循环面已有**声明式停止判据 | `round_loop.py`：`stop_when: str = CONVERGED_NO_NEW_IDS` + **未知判据点名** |
| 1.4 | **程序面对条件声明零命中**（修前） | `rg -n "gate_condition\|stop_when\|gate_if\|on_verdict" packages/domain packages/application` ⇒ 命中的每一条都在 `round_loop*.py` |
| 1.5 | 结论面的取值分派手法 | `continue_rule.verdict_in` + `program_runner` 的命中判定 ⇒ 同族手法**现成** |
| 1.6 | 闸门等待起点已落库 | 实跑读回决策的 `decided_at` ⇒ 条件判定有据可依 |

### 2. 声明面（AC-2，独立重跑）

- 域：`human_gate_on_verdicts: tuple[str, ...] | None`（缺省 `None`）；公开属性
  `condition_gate_hit` 供读面 / 判定面区分**是哪条声明**；
- **三种坏声明各自点名**（逐条实测）：空集合 ⇒ `at least one verdict`；
  空串 ⇒ `must not be empty strings`；**与序号并存** ⇒ `mutually exclusive`；
- SQLite：`human_gate_on_verdicts_json TEXT` 列 + `_encode/_decode_gate_conditions`
  （`None` ⇒ 存 `NULL`，**不**存 `[]`）+ INSERT 与**两处** SELECT 都带上；
- PG：`_PROGRAM_SELECT` + `INSERT` + `_decode_program`；**迁移 021 只加列**
  （`ADD COLUMN IF NOT EXISTS ... JSONB`，同文件无 `DROP COLUMN`）；
- 建程序 DTO / 路由 / 读面透传（`ProgramCreateDto` / `ProgramDetailDto` / 两处构造点）。

### 3. 求值与推进（AC-3，独立重跑）

**实跑（经既有 HTTP 面）**：

| 声明 | 落库判词 | 推进结果 | 被引事实 |
| --- | --- | --- | --- |
| `["REJECT"]` | `PASS` | **`CONTINUE`** + 起第 2 轮 | `['verdict PASS']`（**没有**闸门字样）|
| `["PASS"]` | `PASS` | **`WAIT_FOR_APPROVAL`** + 不起新轮 | `human_gate_on_verdicts=['PASS']` + `verdict PASS` + `approval_id=...` |

**单一来源**：触发判定只在 `declared_gate_trigger`（**只读**）；`declared_gate_pending`
（判定面）与 `register_declared_gate`（注册面）**都**调它 ⇒ 两处不可能对「是否触发」有分歧。
**落库判词只读一次**：`program_runner` 把 `_verdicts(...)` 的结果同时交给条件闸门与结论面
⇒ 两处看到的是**同一批**事实。

### 4. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `J-1` | 条件成立仍放行（去掉拦住） | **RED**（11 例）|
| `J-2` | 条件不成立也拦（无条件触发） | **RED**（2 例）|
| `J-3` | 非法条件被静默当成「无条件」（不点名） | **RED**（1 例）|
| `J-4` | 未声明条件也产生副作用（注册面被调用） | **RED**（3 例）|

四条**全部**判红且**二进制复原**后 raw `sha256` 逐字节相同；归档
`.cursor/plans/goals/evidence/GOAL-20261010-048-press-two-way.txt`（455 B / `CR=0`）。

### 5. 门链与下游同步

四道门全绿（`ruff check` / `ruff format --check`（1190 files）/ `mypy` strict（**1180** files）/
规模门 —— 域 `__post_init__` 加校验后触**复杂度门**（11 > 10）⇒ 抽出模块级
`_validate_gate_declarations` 后过）。**OpenAPI 快照同轮重生成**（`+28 / -0`）且
`tests/contracts/test_openapi_snapshot.py` **一字未改**、**8 passed**（承 `MEM-20261010-216`）。

### 6. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | **追加** 1 例（既有 10 例一字未动） | — | **0** |
| `tests/application/run_orchestration/test_program_waiting_on_the_run_path.py` | **追加** 5 例（既有 20 例一字未动） | — | **0** |
| `tests/e2e/test_program_advance_on_the_run_path.py` | **追加** 2 例（既有 11 例一字未动） | — | **0** |
| `tests/e2e/program_advance_support.py` | `create_program` +1 可选形参 | 缺省**不发键** ⇒ 请求体与旧形态**逐键相同** | 见 `numstat`（同一字典改写成变量） |
| `packages/domain/program.py` | `__post_init__` 抽助手 | **等价**（同一批校验搬出函数，消息逐字保留） | 见 `numstat` |
| `packages/application/run_orchestration/program_waiting.py` | 判定面接条件 | **序号声明的判词逐字保持**（同一点名句仍在，判据钉住） | 见 `numstat` |
| `tools/goal040_closeout_assertions.py` | 结论面坐标由 `_verdicts`（**读取行**）改为 `_after_hit`（**分派点**） | **等价**（判的仍是「失败面分派先于结论面」；读取行会被「读一次共用」正当挪动 ⇒ 那是**位置**不是**关系**） | `+12 / -2` |
| `tools/goal046_closeout_assertions.py` | 同上（闸门 vs 结论面） | **等价**（同一件事：闸门先于结论面；两种调用形态都认） | `+6 / -2` |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：程序能声明**条件式**闸门
（可机检 + 缺省逐字不变 + 坏声明点名 + 与序号声明互斥），求值按**落库判词**且**先于**结论面、
**点名**声明的条件与**命中依据**，命中后走上条已成立的闸门语义（注册 + 等人 + 可接回），
四条反证打满。

### Warnings

- **W-0（本轮实测到的**既有判据假红**，已按关系修正）**：把落库判词改成「读一次供两处共用」（条件闸门与结论面看到同一批事实）之后，`goal040` / `goal046` 各有一条断言**假红** —— 它们拿 `_verdicts` 的**读取行**当「结论面」的坐标，而读取行被**正当**前移了。**判据判的应是「谁先决定」，不是「某条读取语句在哪一行」**（承 `MEM-20261010-215`）；两条已改判**分派点**（`_after_hit`），断言仍是**同一件事**，且把闸门 / 失败面真挪到后面**仍会判红**。**登记为搬迁的既有代价**（不是产品缺陷、不是判据放宽）。

- **W-1（条件的表达力有界，如实登记）**：条件限**「落库判词取值命中声明的集合」**这一形态
  （与 `verdict_in` 同族）。**不**支持跨轮聚合 / 数值阈值 / 自然语言 —— 那些要引入表达式
  求值或语义比对，属**未覆盖**（`Z-2`）。**不得**把本条读成「条件可以是任意表达式」。
- **W-2（多点闸门仍不在；承 `X-2` 的另一半 ⇒ `Z-1`）**：本轮做**条件式**；
  「一个程序里声明**多个**闸门点」**不在**。与序号声明的**互斥**是**设计选择**（决策②），
  不是能力上限 —— 但两条声明确实**不能并存**。
- **W-3（催办 / 升级 / 超时取消仍不在；承 `X-1` 其余部分与 `Y-1` ⇒ `Z-3`）**：
  本轮让条件闸门**可被满足**；**不**做「没人拍板怎么办」。
- **W-4（D 组审批通道本身不在本 GOAL；触达即 BLOCKED）**：闸门用的审批面是**既有**实例。
- **W-5（承继残余原样保持）**：GOAL-047 的 `Y-1` / `Y-3`；GOAL-046 的 `X-1` / `X-2` / `X-3`；
  GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；
  GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
