---
id: RECHECK-20261011-406
slug: goal-051-ec01-04-a-conflicting-memory-is-no-longer-used
title: 独立复检：GOAL-20261011-051 cycle 1（有冲突不再照用 —— 第五态 / 消费端分派 / 两向反证）
plan_id: PLAN-20261011-405
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-11
completed_at: 2026-10-11
owners:
  - root-agent
---

# RECHECK-20261011-406 — GOAL-20261011-051 cycle 1 独立复检

复检对象：`PLAN-20261011-405`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | `contradictions` 域声明**在场**（修前） | `MemoryRecord` 与 `MemoryWriteProposal` **各一行**；域层**已校验**非空字符串 |
| 1.2 | **三适配器都带**（修前） | SQLite 列 `contradictions TEXT NOT NULL` + `commit` + `_to_json`；PG；Fake ⇒ **无新迁移** |
| 1.3 | 读面**已披露**（序 13） | 逐条 `"contradictions": list(...)` + `_conflict_note` **点名** |
| 1.4 | **处置面为零**（修前） | `rg -n "CONFLICT\|resolve_conflict\|has_conflict" packages/ adapters/` ⇒ 命中的**全是别的东西**（成本面 `CURRENCY_CONFLICT` / SQL `ON CONFLICT`）|
| 1.5 | **实跑**（修前） | 有冲突与无冲突的记录 ⇒ 处置**都是** `USE`（冲突只在 `reason` 后缀）|
| 1.6 | **实跑**（修前） | `_split_by_disposition` ⇒ `expired=0 superseded=0 due=0`（**不落任何一组**）；计数摘要**无该格** |

### 2. 处置面与消费端（AC-2/AC-3，独立重跑）

**实跑矩阵**（`FakeMemoryStore` + `memory_read`）：

| 形态 | `disposition` | 理由要点 | 计数格 |
| --- | --- | --- | --- |
| 无冲突、未声明时效 | `USE` | **逐字与改动前相同** | `USE` |
| 声明冲突 | **`CONFLICTED`** | 点名声明的冲突 id + 「未自动消解」 | `CONFLICTED` |
| 待复核 | `ANNOTATE` | 点名 `review_after` | `ANNOTATE` |
| 已过期 + 有冲突 | `SKIP` | **两因都点名**（已过 + 冲突未消解） | `SKIP` |
| 已取代 + 有冲突 | `SUPERSEDED` | 以**取代**为先（已被替代 ⇒ 冲突已无实际意义） | `SUPERSEDED` |

**五态常量两两不等**（`len({...}) == 5`）。

**消费端**（`memory_gate_verdict`）：

| 输入 | 判定 | 判词 |
| --- | --- | --- |
| 仅 `CONFLICTED` | **`ANNOTATE`**（**不跳过**） | 「…carry unresolved contradictions (still used, flagged for a human): m-c（…）」|
| `ANNOTATE` + `CONFLICTED` | `ANNOTATE` | **两因分开点名**（`due for review … | unresolved contradictions …`）|
| 仅 `CONFLICTED`（断言只报那一因）| `ANNOTATE` | **不**出现 `due for review` / `expired` / `superseded` |

**未知处置仍 fail closed**：`expected USE / ANNOTATE / SKIP / SUPERSEDED / CONFLICTED`
（新增已知态**不是**放宽那条 —— 未知值仍点名）。

### 3. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `M-1` | 有冲突仍报 `USE`（处置面没接上） | **RED**（2 例）|
| `M-2` | 无冲突却报为有冲突（凭空） | **RED**（7 例）|
| `M-3` | 与「已过期」混用（过期时吞掉冲突那一路）| **RED**（1 例）|
| `M-4` | 点名缺失（消费端把两因并成一句）| **RED**（2 例）|

四条**全部**判红且**二进制复原**后 raw `sha256` 逐字节相同；归档
`.cursor/plans/goals/evidence/GOAL-20261011-051-press-two-way.txt`（453 B / `CR=0`）。

### 4. 门链与下游同步

四道门全绿（`ruff check` / `ruff format --check`（1191 files）/ `mypy` strict（**1181** files）/
规模门）；读面判据 **32 passed**（原 27 + 5）/ 消费端判据 **18 passed**（原 15 + 3）。
**OpenAPI 快照无需重生成**（本轮未动 DTO / 路由 —— 决策④的申报）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/canonical/test_memory_read_dispositions.py` | 既有**计数判据**的期望枚举 **+1 成员**；追加 5 例；`_record` 助手 +1 可选形参（带 `noqa: PLR0913`） | **谓词形态一字未改**（仍是 `==` **精确相等**；原有四个键**仍逐个被要求** ⇒ **未收窄受判面**）| 见提交 | 见提交（助手**参数化**行与 import 排序） |
| `tests/application/run_orchestration/test_memory_validity_gate.py` | **追加** 3 例 + `_row` 助手**加一个字典键** | 既有四键**逐字保留** | 见提交 | **0** |
| `adapters/canonical/memory_read.py` | 第五态 + `disposition_of` 加可选维 + 理由分支重排（**删掉一处已不可达的旧分支**） | **缺省（两缺省参数皆 `False`）逐字等价**；过期分支**多**点名冲突（**只增不减**）| 见提交 | 那 1 处不可达分支（被新分支覆盖） |
| `packages/application/run_orchestration/phase_capability_triggers.py` | `_split_by_disposition` **三组 → 四组** | `ANNOTATE` / `SKIP` / `USE` 三路**逐字保留**；**新增**第四组 | 见提交 | **0**（原三路一行未改） |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：「带着未消解的冲突」从
**只是一句理由文字**变成**可判定的第五态**（读面处置 + 判词点名 + 计数分格），
且**消费端真的按它分派**（执行但带标注 —— 冲突不等于不可用），
四条反证打满，无冲突路径逐字不变。

### Warnings

- **W-1（冲突的消解不在本轮；承 `CC-1`）**：本轮让「有未消解冲突」**可判定**；
  **不**做「谁对谁错」（那是**人的判断**）。
- **W-2（冲突检测不在本轮；承 `CC-2` / 序 13 的 `W-2`）**：「谁和谁冲突」是**声明**，**不**推断。
- **W-3（冲突的时效性不在本轮；承 `CC-3`）**：一条**很久以前**声明的冲突是否仍算数
  （复核 / 过期）**不在**。
- **W-4（HTTP 读面未披露处置/冲突，如实登记；承序 18 的 `W-4`）**：本轮改的是**编排消费面**
  的读面（`memory.read`）；HTTP 读面（`MemoryRecordDto`）**未**披露 —— **未覆盖**。
  若后续要做，必须**同轮**同步 OpenAPI 快照（承 `MEM-20261010-216`）。
- **W-5（`_conflict_note` 与 `_reason` 的分工，本轮明确）**：冲突**成为处置理由**时由
  `_reason` **自己点名**（不再叠加，避免同一句出现两遍）；**其余分支**（已取代 / 待复核 / 照用）
  仍由 `_extra_conflict_note` 补上 —— 「处置理由」与「读者可见信息」分离，**两者都不省、
  也都不重复**。
- **W-6（承继残余原样保持）**：GOAL-050 的 `BB-1` / `BB-3`；GOAL-049 的 `AA-1`…`AA-3`；
  GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；GOAL-046 的 `X-1`…`X-3`；
  GOAL-045 的 `W-2` / `W-3`；GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；
  GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
