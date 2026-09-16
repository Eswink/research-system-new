---
id: RECHECK-20260915-077
plan_id: PLAN-20260915-077
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle14
baseline_ref: 8b44178
checked_head: 8b44178+worktree
---

# RECHECK-20260915-077 — 操作级事务边界（GOAL-003 cycle 14）

## 检查范围

PLAN-20260915-077 声称的交付面：`adapters/sqlite/db.py` 的 `__enter__`/`__exit__`
（进入取锁、退出提交/回滚后 `finally` 释放）、三处裸 `commit()` 写路径改成事务块
（`tool_pack_store` ×3、`schedule_store` ×2、`eval_report_store` ×1），以及新增的
`tests/adapters/sqlite/test_shared_connection_transaction_scope.py`（8 条用例）。

实现过程中**门禁又逼出四处**（见下表"结构门禁"一行）：`project_store.delete_project`、
`project_settings_store.delete`、`tool_provider_registry.save_registration`、
`tool_provider_registry.delete_registration`——它们同样是"写 + 裸 commit"。

**未覆盖**（见告警）：锁粒度（每线程连接）没做；块内"不得等待使用同一连接的线程"
只是约定，没有门禁。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| `with conn:` 不是操作边界（实测，不是推断） | 探针 2：块内第一个写之后，**另一个线程的语句 0.000s 就执行完**；且它自己的 `with conn:` 退出后，**第三个连接**在 A 仍在块内时就看到了 A 的那一行 ⇒ 半个操作被提交 | PASS（收口前实测） |
| 回滚爆炸半径是数据丢失级 | 探针 3：A 的块整段跑完无异常（写 a1），B 的块在写 b1 后抛错 ⇒ 两线程都结束后，外部连接 `SELECT` 返回 **`[]`**（a1 与 b1 全无） | PASS（收口前实测） |
| 收口后同口径对照 | 探针 3 重放（同一脚本）：外部连接返回 **`['a1']`**（A 的写留下、B 的写回滚）；探针 2 A 项：另线程语句被阻塞（≥0.5s，实测 10.016s 直到块退出） | PASS |
| 块持锁（AC-01） | `test_a_block_holds_the_lock_for_its_whole_body`：块开着时另线程 `execute` 在 0.5s 内拿不到结果（`FutureTimeout`），块退出后 10s 内完成 | PASS |
| 操作原子性对外可见（AC-02） | `test_an_operation_is_all_or_nothing_for_an_outside_witness`：块内第一个写之后、块未退出时外部连接看到 **0** 行；块退出后一次看到 **2** 行 | PASS |
| 回滚爆炸半径归零（AC-03） | `test_a_failing_block_no_longer_rolls_back_another_operations_write`：探针 3 原样重放，断言 `rows == ["a1"]` | PASS |
| 别人的块不能被中途提交（AC-04） | `test_another_thread_cannot_commit_a_block_that_is_in_flight`：A 在块内时 B 的块 0.5s 内进不去（`b_done` 未置位）、外部连接 0 行；A 退出后 B 进块且看到 1 行、外部连接 1 行 | PASS |
| 提交失败也要释放锁（AC-05） | `test_the_block_lock_is_released_even_when_the_exit_commit_fails`：故障注入连接（`commit` 必抛）⇒ 块退出抛 `RuntimeError` 后，另线程 0.5s 内可执行 | PASS |
| 结构门禁（AC-06） | `test_write_paths_commit_only_inside_a_transaction_block`：AST 扫描 `adapters/sqlite/*.py`，不在 `with` 块内的 `.commit()` 集合 == 白名单（8 处构造期 bootstrap + `db.py` 的 `_exit_context`）。**首轮即抓出 5 处**：4 处真实写路径（已改）＋ `db.py` 自身（边界实现，进白名单） | PASS（抓出真实问题） |
| 异常不吞 + 可重入（AC-07） | `test_a_failing_block_still_swallows_nothing`（异常外抛且写被回滚）、`test_nested_blocks_in_one_thread_do_not_deadlock`（嵌套块不死锁、外层退出后锁是空的） | PASS |
| 门禁与记录（AC-08） | m0 **PASS: profile=m0; 23 deterministic checks**（**首轮即绿**，全量 pytest **3663 passed / 10 skipped**）；新用例 **8 passed**；`tests/adapters/sqlite` **122 passed**（114 + 8 新）；`tests/adapters/sqlite+api+contracts`（m0 DSN 口径）**937 passed / 2 skipped**；mypy **871 files clean**；ruff/format 干净；RECHECK-077 + MEM-052 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（临界区变长）**：块现在独占整条连接。块内做重活（或做 IO）会拖住其它线程；
  本仓 `adapters/sqlite/**` 的块体内只有 DB 与 telemetry 调用（AST 扫描：线程原语/外部 IO
  0 命中），但这是**约定**，新增代码若在块内发 HTTP 会显著拉长临界区。
- **W-2（块内等待别的线程 = 死锁）**：约定"块内不得等待使用同一连接的线程"。这条**没有门禁**
  （AST 判不出"是否等待"），只能靠 review 与 docstring 提醒。
- **W-3（不是 savepoint）**：嵌套块重入同一事务，内层退出会提交外层（与 stdlib 的
  `with conn:` 一致，未做 savepoint）。
- **W-4（跨进程仍是 SQLite 语义）**：块边界只在**进程内**成立；多进程仍靠 WAL + `busy_timeout`。
- **W-5（构造期 commit 仍在）**：8 处 `__init__`/schema bootstrap 的 `commit()` 留在白名单里，
  它们会提交连接上已有的东西——属启动期行为，本轮未动。
- **W-6（`_exit_context` 进白名单）**：事务边界的实现自身就在"块外提交"的判据下被扫到，
  白名单里显式登记（它是边界，不是写路径）。
- **W-7（共用连接的相邻项仍未做）**：锁粒度（每线程连接）会把长临界区的代价拿掉，
  但需要先定"每线程连接 + `:memory:` 不可共享"的设计；如实留给下一轮。

## 结论

本轮把事务边界从**连接的**改成**操作的**：`with conn:` 进入即取可重入锁、退出提交/回滚后
`finally` 释放，于是块内语句与块边界同属一个线程独占区间——别的线程既插不进语句，
也无法中途提交/回滚它。**收口前**的两条实测反证（半个操作被别的线程提交；已完成的操作被
别的线程的失败回滚掉，外部连接两行全无）在**收口后**的同口径重放里都反转
（`[]` → `['a1']`；0.000s → 阻塞）。同时把"写入不许裸 commit"做成 AST 门禁，
首轮就抓出 4 处真实写路径（已改）。

结果为 **PASS_WITH_WARNINGS**：W-1/W-2 是"持锁整块"这条取舍的代价与约定，
W-3…W-6 是本轮明确不做的相邻项，W-7 是下一轮输入。**未宣称"并发已经完全正确"**：
锁粒度、跨进程语义、savepoint 都仍是未做项。
