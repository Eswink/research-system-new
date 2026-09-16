---
id: RECHECK-20260915-071
plan_id: PLAN-20260915-071
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-16
completed_at: 2026-09-16
reviewer: root-agent-goal-003-cycle9
baseline_ref: 4bc2f89
checked_head: 4bc2f89+worktree
---

# RECHECK-20260915-071 — 共享 SQLite 连接的读原子性（GOAL-003 cycle 9）

## 检查范围

PLAN-20260915-071 声称的交付面：`adapters/sqlite/db.py` 的 `MaterializedRows`
（只读游标视图）与 `_statement` 的"锁内取尽"、`tests/adapters/sqlite/test_shared_connection_read_atomicity.py`
（钉子 + 反证 + 游标面对账 + 行形状对账），以及控制面 live 对照观察。

**未覆盖**（见告警）：多语句事务原子（读-改-写）、`conn.cursor()` 自建游标路径。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 共享连接上"写后立读"不再读错（AC-01） | `test_write_then_read_on_a_shared_connection_sees_the_row`：12 线程 × 8 轮 × 3 轮 = **288 次往返，0 处对不上真相**（修复前同一脚本：10 / 14 / 13 / 16 / 20 / 6 / 15 / 11 每 96 次） | PASS |
| **反证**：用例真的在测这件事（AC-02） | `test_statement_level_serialization_still_misses_the_row`：把执行面换成 cycle 8 的"语句级串行"（`_StatementOnly`），同一负载 3 次尝试中至少一次复现；实测两种形态——**读不到刚写的行**、以及更响的 **`zip() argument 2 is shorter than argument 1`**（取回的行列数不对） | PASS |
| 游标面对账（AC-03） | `test_materialized_view_matches_a_real_cursor`：同一 SQL、同一数据下，`fetchone` / 迭代 / `fetchall`（耗尽后） / `fetchmany(2)` / `description` / 空结果 `rowcount` / UPDATE 后 `rowcount` 七项与真游标**逐项相等** | PASS |
| 行形状对账（AC-04） | `test_concurrent_reads_never_decode_a_short_row`：8 个写线程 + 4 个读线程并发，`list_definitions()` 20 × 4 次解码**零异常**，最终 48 行齐全 | PASS |
| live 对照（AC-05） | 控制面（uvicorn + 真实 SQLite）：12 线程 24 个 `POST /ops/schedules` ⇒ **24×201 / 0×404 / 0×500**；再加 144 个并发 POST ⇒ **144×201** | 观察（见 W-1） |
| 定向套件（AC-06） | `tests/adapters/sqlite tests/api` **476 passed**（含新增 4 条）；`tests/adapters/sqlite` 单跑稳定 | PASS |
| 全量门禁 + 记录（AC-06） | m0 **PASS: profile=m0; 23 deterministic checks**；ruff check/format 干净；mypy clean；RECHECK-071（本文）+ MEM-20260915-046 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（live 反证未复现，AC-05 只能当观察）**：把控制面切到"语句级串行"（`SerializedConnection.execute`
  打补丁，启动标记 `statement-only patch applied: True` 确认生效）后，**216 个并发 POST 全部 201**——
  live 负载压不出这个缺陷（HTTP 路径的语句密度低于单元负载，窗口约微秒级）。
  因此：**本轮的决定性证据是单元级反证**，live 对照是补充观察；
  cycle 8 的 live 1×404 只能说到"与这一类一致"，**不能**说"已证明同源"。
- **W-2（仍不是多语句事务原子）**：物化只保证**单条语句**的读自洽。跨语句的
  读-改-写（本仓控制面目前没有）仍可能被别的线程夹在中间；若将来出现，需要显式事务 API。
- **W-3（未覆盖的入口）**：`conn.cursor()` 自建游标不走物化（本仓无调用点，已 grep 确认）；
  裸 `sqlite3.connect(...)` 的连接同样不受影响。
- **W-4（锁内取尽的代价）**：返回行多的 SELECT 会在锁内取完，锁持有时间随之变长
  （cycle 8 的锁粒度告警仍在）。控制面读都是小结果集；若将来出现大结果集，应改为每线程连接。
- **W-5（类型边界）**：`MaterializedRows` **不是** `sqlite3.Cursor` 实例，返回处用 `cast`
  穿过 `Connection.execute` 的声明类型。仓库内没有 `isinstance(cursor, sqlite3.Cursor)`、
  没有跨线程复用游标的调用点（已 grep 确认），风险落在"未来新增调用点"上。

## 结论

cycle 8 如实移交的读侧缺陷在本轮被治住，且治在**唯一咽喉处**：`SerializedConnection._statement`
在锁内 `execute` 并对返回行的语句**取尽**，调用方拿到的行不再依赖连接状态。
证据结构是完整的：**分类实验定因**（2×2 对照：只护读即归零，只护写不归零）→
**修复后 0/288** → **反证可复现**（语句级串行的形态两种坏结果都出现过）。
结果为 **PASS_WITH_WARNINGS**：W-1 是 live 复现率不足（如实标注证据强度），
W-2/W-3/W-4/W-5 是范围与代价边界。
