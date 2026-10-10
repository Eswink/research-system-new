---
id: RECHECK-20261010-402
slug: goal-050-ec01-04-superseded-memory-is-no-longer-used
title: 独立复检：GOAL-20261010-050 cycle 1（被取代不再照用 —— 两向披露 / 第四态 / 消费端分派）
plan_id: PLAN-20261010-401
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
---

# RECHECK-20261010-402 — GOAL-20261010-050 cycle 1 独立复检

复检对象：`PLAN-20261010-401`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | `supersedes` 域声明**在场**（修前） | `MemoryRecord` 与 `MemoryWriteProposal` **各一行** |
| 1.2 | **有写者** | `lifecycle.supersede_memory`：新记录 commit（`supersedes=[old_id]`）+ **旧记录 `deactivate`**；inactive 记录不可被 supersede |
| 1.3 | gate **引用完整性** | `supersedes target {old_id!r} does not exist` |
| 1.4 | 读面**零命中**（修前） | `rg -n supersedes adapters/canonical/memory_read.py` ⇒ 0 |
| 1.5 | `disposition_of` **只吃时效**（修前） | 签名 `(state: ValidityState \| None) -> str` ⇒ 看不见 `active` |
| 1.6 | **实跑**（修前） | `deactivate` 之后该条仍 `disposition="USE"`，理由「未声明时效或未到 ⇒ 照用」；载荷无那两个键 |
| 1.7 | 消费端按 `disposition` 分派 | `memory_gate_verdict` 三态（只有 `SKIP` 跳过整步）|

### 2. 读面披露与第四态（AC-2/AC-3，独立重跑）

**实跑矩阵**（`FakeMemoryStore` + `memory_read`）：

| 形态 | `disposition` | 理由 | `supersedes` | `superseded_by` |
| --- | --- | --- | --- | --- |
| 被取代（`m-old`） | **`SUPERSEDED`** | 被 `m-new` 取代 ⇒ 已不是当前版本（不照用） | `[]` | `["m-new"]` |
| 取代者（`m-new`） | `USE` | 照用（理由逐字） | `["m-old"]` | `[]` |
| 无关系（`m-a`） | `USE` | **逐字与改动前相同** | `[]` | `[]` |
| 既过期又被取代 | **`SUPERSEDED`** | **两因都点名**（`取代` + `已过`） | — | — |

**计数摘要**：四态**分开报**（`SUPERSEDED` **不并进** `SKIP` 那一格）。

**消费端**（`memory_gate_verdict`）：被取代 ⇒ `skip=True`（与已过期**同处置**）；
两者并存 ⇒ 判词**分别点名**（`expired … | superseded …`）；**只有**被取代 ⇒ **只报那一因**
（不得凭空说过期）。未知处置仍 **fail closed**（新增已知态**不是**放宽那条）。

### 3. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `L-1` | 被取代仍报 `USE`（处置面没接上） | **RED**（3 例）|
| `L-2` | 未取代却报为已取代（凭空） | **RED**（7 例）|
| `L-3` | 两个方向只给一个（反向链接被抹掉） | **RED**（1 例）|
| `L-4` | 把「已取代」与「已过期」混用（共用一句理由）| **RED**（2 例）|

四条**全部**判红且**二进制复原**后 raw `sha256` 逐字节相同；归档
`.cursor/plans/goals/evidence/GOAL-20261010-050-press-two-way.txt`（471 B / `CR=0`）。

### 4. 门链与既有资产（独立重跑）

四道门全绿（`ruff check` / `ruff format --check`（1191 files）/ `mypy` strict（**1181** files）/
规模门）。**本轮实测到一处既有判据假红并修好**（见下第 5 节）。19 个收口验证器全 0 判负。
**OpenAPI 快照无需重生成**（本轮未动 DTO / 路由 —— §⑤ 的申报）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | 删除行 |
| --- | --- | --- | --- |
| `tests/adapters/canonical/test_memory_read_dispositions.py` | 既有**计数判据**的期望枚举 **+1 成员**；追加 5 例；`_record` 助手 +1 可选形参 | **谓词形态一字未改**（仍是 `==` **精确相等**；原有三个键**仍逐个被要求** ⇒ **未收窄受判面**）| 见 `numstat`（助手参数化 1 行）|
| `tests/application/run_orchestration/test_memory_validity_gate.py` | **追加** 3 例 + `_row` 助手**加一个字典键** | 既有三键**逐字保留** | **0** |
| `tools/goal045_closeout_assertions.py` | `ec03-the-reason-carries-the-note` 由**调用式逐字**改判**关系** | **等价**（判的仍是「`reason` = 时效理由 **加** 冲突点名」；两种调用签名都通过，**摘掉冲突点名仍判红** —— 已两向实测）| 1 行 = 原文本比对式 |

**两向实测**（该条判据自身）：真实形态 `True` / 历史形态 `True` / 摘掉冲突点名 `False` /
不拼加 `False`。

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：「被取代」从**写进去但看不见**
变成**可判定的不适用理由**（读面两向披露 + 第四态 + 消费端真的分派），
无取代关系时处置与理由逐字不变，四条反证打满。

### Warnings

- **W-1（链式取代不在本轮；承 `BB-1`）**：只报**直接**链接；A→B→C 的传递闭包**不做**。
- **W-2（冲突的处置仍不在；承 `BB-2` / `W-1`）**：本条只做 `supersedes`（**已取代**）；
  `contradictions`（**冲突**）的处置仍是另一件事。
- **W-3（自动取代 / 推荐取代不在本轮；承 `BB-3`）**：谁取代谁是**声明**，**不**推断。
- **W-4（HTTP 读面未动，如实登记）**：本轮改的是**编排消费面**的读面（`memory.read`）；
  HTTP 读面（`MemoryRecordDto`）**未**披露那两向链接 —— **未覆盖**（若后续要做，
  必须**同轮**同步 OpenAPI 快照）。
- **W-5（本轮实测到的既有判据假红，已按关系修正）**：`goal045` 的
  `ec03-the-reason-carries-the-note` 把调用式**逐字写死** ⇒ 本轮正当给 `_reason` 加
  `superseded_by=` 关键字实参后**假红**（被 GOAL-043 立的「零判负」判据当场报出）。
  已改为**判关系**并**两向实测**（承 `MEM-20261010-215`）。**判据对、写法过严** ——
  登记为**搬迁/签名演进的既有代价**。
- **W-6（承继残余原样保持）**：GOAL-049 的 `AA-1`…`AA-3`；GOAL-048 的 `Z-1`…`Z-3`；
  GOAL-047 的 `Y-1`…`Y-3`；GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-1`…`W-3`；
  GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；
  GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；
  GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
