---
id: RECHECK-20261010-376
slug: goal-044-ec01-04-program-wait-reasons
title: 独立复检：GOAL-20261010-044 cycle 1（等待理由可区分 —— 新种类 / 点名面 / 两向反证）
plan_id: PLAN-20261010-375
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-376 — GOAL-20261010-044 cycle 1 独立复检

复检对象：`PLAN-20261010-375`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 混用实测（AC-1，独立重跑）

**修正前**：`_evaluate` 只按 `last.is_terminal` 分派，非终态一律落 `WAIT`，理由串
`第 N 轮尚未终止（state=<s>）⇒ 本轮不推进` —— 对 `RUNNING` 与 `WAITING_FOR_APPROVAL`
**给出同一种类与同形理由**（只有 `state=` 的值不同）。**域里早已可区分**：
`run_state.py` 有这两个非终态常量，且均**不在** `terminal()` 内。

### 2. 两类分派（AC-2 / AC-3，独立重跑）

| 上一轮状态 | 判定种类 | `cited_facts` |
| --- | --- | --- |
| `WAITING_FOR_APPROVAL`（有待决审批） | **`WAIT_FOR_APPROVAL`** | `("state=WAITING_FOR_APPROVAL", "待审批 id=apr-1")` |
| `PAUSED`（有待决审批） | **`WAIT_FOR_APPROVAL`** | 点名该审批 id |
| `RUNNING`（即便有待决审批） | **`WAIT`**（**逐字保持**） | `("state=RUNNING",)`；理由串与修正前**逐字相同** |
| `WAITING_FOR_APPROVAL`（无待决审批） | `WAIT_FOR_APPROVAL` | 点名「查不到」 |
| `WAITING_FOR_APPROVAL`（缺审批面） | `WAIT_FOR_APPROVAL` | 点名「未提供审批面」 |
| `WAITING_FOR_APPROVAL`（审批面抛异常） | `WAIT_FOR_APPROVAL` | 点名异常类型与消息 |

**独立重跑读数**：`test_program_waiting_on_the_run_path.py` **7 passed**；
`test_program_runner.py` **18 passed**（既有面逐字保持）。

### 3. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `W-1` | 把 `AWAITING_HUMAN` 判断压成恒真 ⇒ **复现「混用」** | **RED**（6 例） |
| `W-2` | 把点名句改成「查不到」（待审批在场时也这么说） | **RED**（2 例） |

复原用**二进制读写**，raw `sha256` **逐字节相同**；归档
`.cursor/plans/goals/evidence/GOAL-20261010-044-press-two-way.txt`（110 B / `CR=0`）。

### 4. 按压发现的**死值**（本轮自查，如实登记）

`pending_approval` 早先返回 `(id 串, 点名句)`，而调用方**只用后者** ⇒ 那个 id 串是**死值**：
`W-2` 的第一次按压（只改 id 串）**没有判红** —— 正是这一轮按压暴露了它。**已删**
（签名收成单返回值），`W-2` 改成改**点名句**后**判红**。

### 5. 门链与记录面

四道门全绿（`ruff check` / `ruff format --check` / `mypy` strict）；规模门：
`program_runner.py` **448 行**（≤ 450）、`program_waiting.py` 78 行、两个判据文件 ≤ 450；
广面 `tests/application + domain + tooling/test_python_source_limits` **2464 passed, 1 skipped**。

### 6. 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/domain/test_research_program.py` | 集合 +1 条目 | **形态一字未改**（集合相等）；**纯加法** | `+4 / -0` | **0** |
| `tests/application/run_orchestration/test_program_runner.py` | 7 例**迁出**到新文件（拆分） | 既有 18 例**逐字在** | 拆分后净零 | **0**（搬迁） |
| `packages/application/run_orchestration/program_runner.py` | 分派块**搬到**新模块；签名 +1 参数 | **等价**（`WAIT` 分支逐字） | `+10 / -8` | 仅被搬迁的 5 行 + 2 行签名/传参 |
| `packages/domain/program.py` | 枚举 +1 | — | `+7 / -0` | **0** |
| `services/api/routers/programs.py` | 传 `approvals=deps.approvals` | — | `+4 / -0` | **0** |

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：「等人」与「等机器」**互不混用**且
等待**逐条点名**（四种查不到形态都点名），两向反证打满（含按压发现的死值处置）。

### Warnings

- **W-1（只到「可判定 + 点名」，不做处置）**：本轮**不**做催办 / 升级 / 超时取消（`V-1`）；
  **不**给 SLA（`V-3`）；**不**接通 D 组审批通道本身。
- **W-2（判定面只读审批面）**：`list_for_run` **只读** —— 推进**不**改审批状态
  （这是**故意**的：不得自动批准 / 跳过）；但也就意味着**审批面故障时只能点名**，
  程序只能停在那儿等人（那是「点名」的正确后果，不是缺陷）。
- **W-3（跨程序等待传播未做）**：等待按**程序**划界（`V-2`）。
- **W-4（承继残余原样保持）**：GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
  GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
  GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
