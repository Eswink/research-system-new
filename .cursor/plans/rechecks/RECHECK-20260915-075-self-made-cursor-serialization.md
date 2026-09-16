---
id: RECHECK-20260915-075
plan_id: PLAN-20260915-075
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle12
baseline_ref: f329444
checked_head: f329444+worktree
---

# RECHECK-20260915-075 — 自建游标收口（GOAL-003 cycle 12）

## 检查范围

PLAN-20260915-075 声称的交付面：`adapters/sqlite/db.py` 的 `SerializedCursor`
（锁内执行 + 锁内取尽 + 游标面）与 `cursor()` 接线、两处"范围注记"docstring 的更新、
以及 `tests/adapters/sqlite/test_serialized_cursor_path.py` 的九条用例。

**未覆盖**（见告警）：`MaterializedRows` 与 `SerializedCursor` 的面**不完整**
（例如 `setinputsizes`/`setoutputsize`、`cursor.row_factory`）；本轮只覆盖仓内实际
用到的面，未引入完整游标兼容层。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 结构（AC-01） | `test_self_made_cursor_is_a_serialized_cursor_that_materializes`：`conn.cursor()` 返回 `SerializedCursor` 且**不是** `sqlite3.Cursor`；`execute()` 返回自身且其 `_view` 是 `MaterializedRows`；`conn.execute()` 的返回类型未变（cycle 9 的结构判据 `type(...).__name__ == "MaterializedRows"` 继续通过） | PASS |
| 锁真的被取（AC-02，确定性） | `test_self_made_cursor_statement_waits_for_the_connection_lock`：主线程持 `conn._lock`，另一线程 `cursor.execute(...)` 在 0.5s 内**拿不到结果**（`TimeoutError`），释放后立刻返回 `[(1,), (2,)]` —— 不依赖负载，任何机器成立 | PASS |
| 读在 execute 时刻定死（AC-03） | `test_self_made_cursor_freezes_rows_at_execute_time`：表形态刻意取"带主键 + 按列排序"（实测中裸游标会把新行读进来的那种形态），execute 之后同连接写入 + 提交，`fetchall()` 仍是两行 | PASS |
| 取行不依赖连接（AC-03） | `test_self_made_cursor_rows_survive_the_connection`：execute 后**关掉连接**，`fetchall()` 仍返回物化结果（只读本地列表） | PASS |
| 反证与计划无关（AC-03） | `test_a_raw_cursor_fetch_depends_on_the_going_connection`：裸游标同一动作在关门后抛 `ProgrammingError`；`test_a_raw_cursor_stops_being_materialized_or_locked`：裸游标连 `_view` 属性都没有。两条都不依赖查询计划或负载 | PASS |
| 游标面与往返（AC-04） | `test_self_made_cursor_round_trips_writes_and_reads`：`execute`/`executemany` 写入 + 提交后可读回，`rowcount` 如实，`lastrowid` 只由单条 `execute` 更新（与真游标一致，实测确认后修正了断言）；`test_self_made_cursor_covers_the_cursor_surface_the_repo_uses`：`fetchone`/`fetchmany`（含 `arraysize`）/迭代/`description`/`connection`/`close` 后 `ProgrammingError` | PASS |
| 负载回归（AC-05） | `test_self_made_cursor_keeps_writes_serialized_under_load`：12 线程 × 8 轮经自建游标"写后立读"，`problems == []`，总数 96 行 —— 回归用途，**不当反证**（见 W-1） | PASS |
| 收口前/后实测（记录） | `scratch/goal3-cycle12-probe6-cursor-load-before-after.py`（裸游标形态 = 子类覆写 `cursor()` 返回裸游标）：三次运行 **problems 15/96、18/96、14/96（异常 10/11/8 + 读不上 5/7/6）→ 收口后 0/96、0/96、0/96** | PASS |
| 门禁与记录（AC-06） | m0 **PASS: profile=m0; 23 deterministic checks**；`tests/adapters/sqlite` **107 passed**；`tests/adapters/sqlite+tests/api+tests/integration` **525 passed**；ruff/format 干净；mypy clean；RECHECK-075 + MEM-050 + GOAL 记账 + ALL_PLAN | PASS |

## 探针（决定判据怎么写）与"什么没写成判据"

derive 阶段先用四个探针把问题问清楚，避免把不可移植的行为写成门禁
（MEM-048 的教训）——**这些都是实测，不是推断**（win32 / SQLite 3.50.4）：

```text
探针 3/4：裸游标 execute 读语句 → 同连接写入 + 提交 → 再取行
    带主键 + 按列排序   ：三行都在（新行进来了）
    带主键、不排序      ：三行都在
    无主键 + 按列排序   ：只有两行（sorter 在首次 step 就定死结果集）
    无主键、不排序      ：三行都在
⇒ "裸游标会不会读到提交之后的新行"取决于**查询计划** ⇒ **不写成判据**

探针 5：与计划无关的对比
    裸游标：关门后取行 → ProgrammingError: Cannot operate on a closed database.
    锁内取尽：关门后取行 → 正常返回（本地列表）
⇒ 这条才是可移植的反证

探针 1：CPython 3.12 的 `Connection.execute/executemany/executescript` **不经过**
        Python 层的 `cursor()` 覆盖（C 层直接建游标）⇒ 覆写 `cursor()` 不会反过来
        改变 `execute()` 的行为，两个入口互不干扰（这是实现选择的前提）
```

## 告警

- **W-1（负载数字只是记录）**：收口前 14~18/96 的问题率是**本机负载下的观测**，
  换台机器、换个核数就可能不同——所以它是记录，不是判据（MEM-048）。
  判据是与负载无关的四条：结构、锁、冻结、跨连接存活，加一条与计划无关的反证。
- **W-2（游标面不完整）**：`SerializedCursor` 覆盖仓内实际用到的面；
  `setinputsizes`/`setoutputsize`/`cursor.row_factory` 等未实现。若将来有调用方需要，
  应按需补齐——**不要**把它当成"完整兼容层"。
- **W-3（潜伏缺口，不是冒烟缺陷）**：仓内当前**没有** `conn.cursor()` 调用方，
  所以本轮修的是一个"承诺与实现不一致"的缺口（docstring 早就如实写着它）。
  收益是防御性的：任何后来者用自建游标都不会掉出并发保证之外。
- **W-4（未覆盖多语句事务语义）**：本轮仍不把"一个请求里的多条语句"变成原子事务
  （既有范围注记不变）；自建游标同样是"单条语句"粒度。
- **W-5（`executescript` 走同一把锁）**：自建游标的 `executescript` 与连接级
  `executescript` 行为一致（锁内转发），但**没有**像读语句那样物化（脚本无结果集）——
  与连接级实现一致，不是新的不一致。

## 结论

`SerializedConnection` 的并发承诺此前只对一个入口成立（`conn.execute()`），
`conn.cursor()` 返回的裸游标不受锁也不物化——模块 docstring 如实登记了这个缺口。
本轮把自建游标收进同一把锁与同一套"锁内取尽"口径（`SerializedCursor`），
并用**与负载、与查询计划都无关**的判据把它钉住；裸游标侧留了一条可移植的反证。
结果为 **PASS_WITH_WARNINGS**：W-1 说明为什么负载数字只是记录，W-2/W-4/W-5 是本轮
刻意划定的边界，W-3 说明这是一个潜伏缺口的防御性修复而不是缺陷修复。
