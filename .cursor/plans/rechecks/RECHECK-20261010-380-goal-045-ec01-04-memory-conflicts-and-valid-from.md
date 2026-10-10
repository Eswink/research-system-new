---
id: RECHECK-20261010-380
slug: goal-045-ec01-04-memory-conflicts-and-valid-from
title: 独立复检：GOAL-20261010-045 cycle 1（冲突与生效起点 —— 可声明 / 三适配器落库 / 读面点名）
plan_id: PLAN-20261010-379
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-380 — GOAL-20261010-045 cycle 1 独立复检

复检对象：`PLAN-20261010-379`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | **提案无该两字段**（修正前） | `dataclasses.fields(MemoryWriteProposal)` 不含 `contradictions` / `valid_from` |
| 1.2 | **记录有该两字段** | `MemoryRecord` 字段表含二者 ⇒ **有类型、零写者** |
| 1.3 | **声明路径不存在** | `MemoryWriteProposal(..., contradictions=["x"])` ⇒ **`TypeError: unexpected keyword argument`** |
| 1.4 | SQLite 漏字段（修正前） | `commit` 构记录时逐字段给了 `scope` / `review_after` / `expires_at` / `supersedes`，**无**该二字段 |
| 1.5 | PG 硬编码（修正前） | `None,  # valid_from` 与 `_json([]),  # contradictions (empty at commit)` |
| 1.6 | **无新迁移** | 两列已在表上：SQLite `_MEMORY_COLS` 含二者；`migrations/004_memory_state.sql` 含二者 |
| 1.7 | 消费面 | 修正前全仓（排除 tests）只命中域定义与两适配器读写 ⇒ **零按冲突判定** |

### 2. 声明与落库（AC-2，独立重跑）

- 提案可**声明**（`contradictions` / `valid_from`，缺省 `[]` / `None`）；
- **三个适配器**的 `commit` 都带上：SQLite（`+4/-0`）、PG（`+4/-2`，替换两处硬编码）、
  **Fake**（`+5/-0`）；**往返一致**（提交回执 / 重新读出 / 查询三处逐字相同）；
- 缺省路径在**三处**都逐字保持（`[]` / `None`）；
- 非法冲突项（空串）⇒ **点名**（`ValueError: proposal contradictions must be non-empty strings`）。

**独立重跑**：`tests/adapters + tests/domain` **1027 passed, 3 skipped**；
其中域 **4 passed**、SQLite **13 passed**、读面 **18 passed**。

### 3. 读面与点名（AC-3，独立重跑）

| 形态 | 读面 `contradictions` | 读面 `valid_from` | 理由 |
| --- | --- | --- | --- |
| 声明冲突 | `["memory:earlier-claim"]` | — | **点名**该标识 + 「未自动消解」 |
| 声明生效起点 | `[]` | ISO 串 | 不含冲突文字（`[]` ⇒ 不追加） |
| 未声明 | `[]` | `None` | **不得**出现「冲突」字样（**不**凭空） |

**`[]` 与 `None` 语义互不混用**（逐条断言）：`[]` = 已判定**无**冲突；
`valid_from=None` = **不适用/未声明**（**不猜**成某个时点）。

### 4. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `C-1` | SQLite `commit` 不带两字段（**复现静默丢弃**） | **RED** |
| `C-2` | 读面点名句变空（点名面失效） | **RED** |
| `C-3` | 未声明也报冲突（**凭空**） | **RED** |

复原用**二进制读写**，raw `sha256` **逐字节相同**；归档
`.cursor/plans/goals/evidence/GOAL-20261010-045-press-two-way.txt`（295 B / `CR=0`）。

### 5. 本轮实测到的**第三个适配器**（同类缺陷，独立确认）

Fake 的 `commit` **同样**只带 `supersedes` —— 修 PG/SQLite 后读面判据仍在 Fake 路径上红
（3 例里 2 例）。**它的源码注释此前已写着**这条纪律（「少带字段会让判据在 Fake 路径上假绿
（实测过）」）⇒ **同一条纪律第二次生效**。已修 ⇒ 三适配器同契约。沉淀 `MEM-20261010-214`。

### 6. 门链与记录面

四道门全绿（`ruff check` / `ruff format --check`（1060 files）/ `mypy` strict（441 files））；
`tests/postgres` + 规模门 **1201 passed, 101 skipped**。

### 7. 改既有判据的申报（承 `MEM-20261009-210`）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/sqlite/test_memory_scope_and_validity.py` | **追加** 2 例（既有 11 例一字未动） | — | `+41 / -0` | **0** |
| `tests/adapters/canonical/test_memory_read_dispositions.py` | **追加** 3 例（既有 15 例一字未动） | — | `+51 / -0` | **0** |
| `tests/domain/test_memory_declaration_fields.py` | **新增**文件（**注意**：初版误用 `test_memory_scope_and_validity.py` 这个名字 ⇒ 与 `tests/adapters/sqlite/` 同名 ⇒ pytest **`import file mismatch`** ⇒ 已改名） | — | 新增 | — |
| `adapters/postgres/memory_store.py` | **替换**两个硬编码 | 硬编码 ⇒ 提案值 | `+4 / -2` | 仅那 2 行 |
| `adapters/canonical/memory_read.py` | 读面 +2 键 + 点名助手 | — | `+20 / -1` | 仅被扩展的 1 行 |

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：「有类型、零写者」的两个字段
现在**可声明 / 可落库（三适配器同契约）/ 可点名**，缺省逐字不变，`[]` 与 `None` 语义不混用，
三向反证打满。

### Warnings

- **W-1（冲突的自动处置不在本 GOAL）**：本轮让冲突**可声明 / 可落库 / 可点名**；
  **不**自动挑一方 / 删除 / 降权（`W-1`）。
- **W-2（冲突检测算法不在本 GOAL）**：「谁和谁冲突」是**声明**；本条**不**推断（`W-2`）。
- **W-3（`supersedes` 的判定面不动）**：它已在落库面（序 7），「被取代后是否影响判定」
  **不在**（`W-3`）。
- **W-4（承继残余原样保持）**：GOAL-044 的 `V-1`…`V-3`；GOAL-043 的 `U-1`…`U-3`；
  GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；GOAL-040 的 `R-1`…`R-3`；
  GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；GOAL-037 的 `O-1`…`O-5`；
  `R26-*` 终态；未覆盖范围逐条保持。**不得**据此宣称项目安全（`R-M1`）；
  **不得**宣称投递语义为那四个字（**明确否认**）。
