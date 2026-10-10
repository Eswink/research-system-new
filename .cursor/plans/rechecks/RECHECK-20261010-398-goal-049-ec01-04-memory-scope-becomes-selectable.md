---
id: RECHECK-20261010-398
slug: goal-049-ec01-04-memory-scope-becomes-selectable
title: 独立复检：GOAL-20261010-049 cycle 1（记忆范围可选 —— 查询面 / 消费面 / 四向反证）
plan_id: PLAN-20261010-397
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-10
completed_at: 2026-10-10
owners:
  - root-agent
---

# RECHECK-20261010-398 — GOAL-20261010-049 cycle 1 独立复检

复检对象：`PLAN-20261010-397`。独立重跑下列机械面，不引用 PLAN 结论当证据。

## 检查结果

### 1. 勘察读数复核（AC-1，独立重跑）

| # | 检查 | 读数 |
| --- | --- | --- |
| 1.1 | `scope` 在域声明面**在场**（修前） | `rg -n "scope: str" packages/domain/memory.py` ⇒ `MemoryRecord` 与 `MemoryWriteProposal` **各一行**（缺省 `"project"`）|
| 1.2 | **查询面只有一维**（修前） | 三适配器签名**逐字相同**：`query(self, tier: MemoryTier \| None = None)` |
| 1.3 | **反证：传了会崩**（修前） | `store.query(scope="project")` ⇒ `TypeError: unexpected keyword argument 'scope'` |
| 1.4 | 调用点逐条（修前） | 全仓 `query(` **三处**：HTTP 读面 ×2（不传）、`memory_read.py:150`（只传 tier）|
| 1.5 | 读面**已披露**（修前） | 载荷逐条含 `"scope": str(record.scope)` ⇒ **看得见**、「按它选」不存在 |
| 1.6 | 两库列**已在**（修前） | `scope` 列在 SQLite schema 与 PG 表上（序 13 落的）⇒ **无迁移** |
| 1.7 | 计数摘要形态**现成** | `dispositions`（不解析数组就知道有没有被跳过）⇒ `filtered_out` 照此 |

### 2. 查询面与消费面（AC-2/AC-3，独立重跑）

**实跑（`FakeMemoryStore` + `memory_read`）**：

| 输入 | 读数 |
| --- | --- |
| 不传 `scope`（3 条记录） | `memory_count=3`；载荷键 = `dispositions / memories / memory_count / now / tier`（**无** `scope` / `filtered_out`）|
| `scope="project"`（project 2 条、team 1 条） | `memory_count=2`；`scope="project"`；**`filtered_out=1`** |
| `scope="nope"` | **`InvalidInputError: memory_read scope 'nope' is not a known scope (known: ['project', 'team'])`** |
| `tier="SESSION"` + `scope="team"` | `memory_count=1` ⇒ **两维并存**（不是互相顶替）|

**三适配器同契约**：SQLite（+1 例）/ PG（+1 例）/ Fake（读面 4 例全走它）**各**验证了
「按范围筛 + 缺省不筛 + 两维并存」。**HTTP 面**：缺省响应**无**那两键；带 `?scope=` ⇒
`scope` 与 `filtered_out` 都在；DTO 用**两个显式形态**（继承复用）。

### 3. 两向反证（AC-4，独立重跑）

| 按压 | 复现什么 | 结果 |
| --- | --- | --- |
| `K-1` | 传了范围却不生效（返回全部） | **RED**（1 例）|
| `K-2` | 没传范围却筛掉了（缺省被改动） | **RED**（3 例）|
| `K-3` | 未知范围静默返回空集（不点名） | **RED**（1 例）|
| `K-4` | 筛掉的条数不点名（静默丢） | **RED**（1 例）|

四条**全部**判红且**二进制复原**后 raw `sha256` 逐字节相同；归档
`.cursor/plans/goals/evidence/GOAL-20261010-049-press-two-way.txt`（431 B / `CR=0`）。

### 4. 门链与下游同步

四道门全绿（`ruff check` / `ruff format --check`（1191 files）/ `mypy` strict（**1181** files）/
规模门）；定向套件 **4937 passed, 18 skipped**。**OpenAPI 快照同轮重生成**（`+59 / -1`）且
`tests/contracts/test_openapi_snapshot.py` **一字未改**、**8 passed**（承 `MEM-20261010-216`）。
**无迁移**（`scope` 列早已在表上）。

### 5. 改既有判据的申报（承 `MEM-20261009-210`，逐条自证）

| 文件 | 改动 | 谓词比对 | `numstat` | 删除行 |
| --- | --- | --- | --- | --- |
| `tests/adapters/canonical/test_memory_read_dispositions.py` | **追加** 4 例 + `_record` 助手加 `scope` 形参 | **谓词一字未改**（唯一 `-` 是 `scope="project"` **参数化**为 `scope=scope`，**缺省值 `"project"` 未变**）| `+41 / -1` | 那 1 行 = 助手参数化 |
| `tests/adapters/sqlite/test_memory_scope_and_validity.py` | **追加** 1 例（既有 13 例一字未动） | — | `+21 / -0` | **0** |
| `tests/api/test_memory_api.py` | **追加** 1 例（既有 9 例一字未动） | — | `+52 / -0` | **0** |
| `tests/postgres/test_memory_scope_pg.py` | **追加** 1 例（既有 2 例一字未动） | — | `+30 / -0` | **0** |
| `packages/application/ports/memory_store.py` | `query` **+1 可选参** | 既有调用 `query(tier)` 语义不变 | `+3 / -1` | 1 行 = 签名行改写 |
| `adapters/sqlite/memory_store.py` | 分支改写（两维可并存） | **缺省（都 None）⇒ 全表**，与修前一致 | `+22 / -8` | 8 行 = 旧的两分支体 |
| `adapters/postgres/memory_store.py` | 同上 | 同上 | `+17 / -8` | 8 行 = 同上 |
| `adapters/fakes/memory_store.py` | 同上 | 同上（**第三个适配器**） | `+13 / -4` | 4 行 = 同上 |
| `adapters/canonical/memory_read.py` | 读面条件性 +2 键 + 点名助手 | **缺省载荷逐字相同**（判据钉住） | `+35 / -2` | 2 行 = 调用点与 return 改写 |
| `services/api/dto/memory.py` | 新增 `MemoryFilteredListViewDto`（继承） | **既有 `MemoryListViewDto` 逐字保留** | `+19 / -0` | **0** |
| `services/api/routers/memory.py` | 按 `scope` 选 DTO 形态 | 缺省路径返回**同一** DTO | `+26 / -5` | 5 行 = 旧 return 改写 |

**收窄受判面？** 无。**未**放宽任何既有断言。

## 结论

**result: PASS_WITH_WARNINGS**。AC-1…AC-4 逐条独立成立：`scope` 从「看得见」变成
**「可选择的」**（查询面按它筛、消费面点名筛掉多少、未知范围点名），缺省路径逐字不变，
四条反证打满。

### Warnings

- **W-1（范围**不是**权限；承 `AA-1`）**：`scope` 是**声明的范围**，**不是** ACL。
  本轮**只**做「选择面」：**不**做读面认证 / 多租户 / RBAC / BOLA·BFLA（M18 deferred）。
  **不得**据本条宣称任何隔离保证。
- **W-2（语义检索不在本轮；承 `AA-2` / `Q-3`）**：按**声明值**精确匹配筛，
  **不**做 embedding / 相似度 / 模糊匹配。
- **W-3（范围治理面不在本轮；承 `AA-3`）**：自动过期 / 清理 / 容量 / 跨范围迁移**不在**。
- **W-4（`filtered_out` 的口径**，如实登记）**：它是「同一 `tier` 维下、不含该范围的条数」
  （`len(query(tier)) - kept`）—— 即**该次调用的过滤量**，**不是**全库里范围的历史统计。
  口径写在 `_filtered_out` 的 docstring 里。
- **W-5（本轮实测到两处真缺陷，均已修且登记在 PLAN 正文）**：
  `K-2` 反证臂最初**假绿**（判据数据单一 tier ⇒ 区分不了两件事）；
  `response_model_exclude_none` **递归**抹掉别的读面上有意义的 `null`。
  **都不是**判据放宽，而是**判据/实现选得不巧**被当场抓住。
- **W-6（承继残余原样保持）**：GOAL-048 的 `Z-1`…`Z-3`；GOAL-047 的 `Y-1`…`Y-3`；
  GOAL-046 的 `X-1`…`X-3`；GOAL-045 的 `W-1`…`W-3`；GOAL-044 的 `V-1`…`V-3`；
  GOAL-043 的 `U-1`…`U-3`；GOAL-042 的 `T-1`…`T-3`；GOAL-041 的 `S-1`…`S-3`；
  GOAL-040 的 `R-1`…`R-3`；GOAL-039 的 `Q-1`…`Q-3`；GOAL-038 的 `P-1`…`P-3`；
  GOAL-037 的 `O-2`…`O-5`；`R26-*` 终态；未覆盖范围逐条保持。
  **不得**据此宣称项目安全（`R-M1`）；**不得**宣称投递语义为那四个字（**明确否认**）。
