---
id: RECHECK-20260915-076
plan_id: PLAN-20260915-076
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-17
completed_at: 2026-09-17
reviewer: root-agent-goal-003-cycle13
baseline_ref: ca03254
checked_head: ca03254+worktree
---

# RECHECK-20260915-076 — 连接边界枚举化（GOAL-003 cycle 13）

## 检查范围

PLAN-20260915-076 声称的交付面：`adapters/sqlite/db.py` 的 `__enter__`/`__exit__` 收口、
`isolation_level`/`autocommit` 赋值收口（`__setattr__` + `LOCKED_ATTRIBUTES`）、类 docstring
的"边界是枚举出来的"段，以及 `tests/adapters/sqlite/test_serialized_connection_surface.py`
的七条用例（枚举门禁 / 名单一致性 / 语义 / 两条确定性锁判据 / 只读对照 / 混合负载回归）。

另有交付过程中的**门禁驱动改动**：`db.py` 触到 450 行硬上限后，取行面
（`MaterializedRows` / `SerializedCursor`）被**原样搬移**到新增的 `adapters/sqlite/cursor.py`，
`db.py` 用 `X as X` 显式再导出（详见下表的"文件规模硬上限"一行）。

**未覆盖**（见告警）：多语句**原子事务**语义（一个请求内多条语句一个事务）仍没做。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 事务边界是缺口（实测，不是推断） | 探针 1：覆写了 `commit`/`rollback` 的子类上跑 `with conn:`，Python 层的覆写**一次都没被调用**（记录为空）⇒ CPython 3.12 的上下文管理器在 C 层直接提交/回滚；`isolation_level` setter 同理 | PASS |
| 收口前/后的**确定性**对照 | 探针 2（持锁时另线程是否阻塞）：`with` 退出 **False → True**；`isolation_level` 赋值 **False → True**。与负载、与查询计划无关，可直接当判据 | PASS |
| 事务边词语义（AC-02） | `test_context_manager_commits_on_success_and_rolls_back_on_error`：成功退出后 1 行；异常退出后仍是 1 行（第二次插入被回滚）且异常**未被吞**（`pytest.raises` 收到 `RuntimeError`） | PASS |
| 事务边界在锁内（AC-03） | `test_context_manager_exit_takes_the_connection_lock` 与 `test_transaction_boundary_attribute_assignment_takes_the_lock`：持锁时 0.5s 内拿不到结果（`TimeoutError`），释放后完成；赋值后 `isolation_level == "IMMEDIATE"` 生效 | PASS |
| 读取刻意不收口（AC-03 对照） | `test_reads_of_transaction_flags_do_not_need_the_lock`：持锁时读 `isolation_level` **立即**返回（只读标志位，不进锁也就不阻塞） | PASS |
| 枚举门禁（AC-01） | `test_unguarded_surface_matches_the_documented_list`：未收口集合 == `NOT_GUARDED` 的 25 个名字（逐条带理由）；同时断言名单里**没有过期名字**（某版本已无该属性时也红）。`test_locked_attributes_are_a_subset_of_the_documented_surface`：`LOCKED_ATTRIBUTES ⊆ NOT_GUARDED ⊆ sqlite3.Connection 公共面` | PASS |
| 回归（AC-04） | `test_a_statement_execution_and_a_context_exit_do_not_interleave`：12 线程 × 8 轮混合 `with conn:` 与直接执行语句，`problems == []`，总数 96 行（回归用途，判据是上面三条确定性用例） | PASS |
| 文件规模硬上限（**门禁抓到的真实问题**） | m0 第 1 轮红于 `test_python_source_size_limits[adapters\sqlite\db.py]`：`assert 475 <= 450`。阈值**未被放宽**（那属于 fix_policy 禁止的"改门禁使其通过"），而是把取行面原样搬到 `adapters/sqlite/cursor.py`：`db.py` **475 → 331 行**、新模块 170 行 | PASS（修法：抽取） |
| 再导出的类型面 | m0 第 2 轮红于 `python/typecheck`：`no_implicit_reexport` 下普通 `import` 不算再导出（`Module "adapters.sqlite.db" does not explicitly export attribute ...`）。改用 `X as X` 显式再导出后 mypy 全绿；3 个既有用例（`test_serialized_cursor_path` / `test_shared_connection_read_atomicity` / `test_serialized_connection_surface`）的 import 路径**未改**且全过 | PASS |
| 行为等价性 | 搬移是**逐字**的（两类的 docstring、语义、`__slots__` 未动）；`tests/adapters/sqlite` 与 `tests/tooling/test_python_source_limits.py` 合跑 **994 passed**；m0 第 3 轮 **PASS: profile=m0; 23 deterministic checks**（全量 pytest **3654 passed / 10 skipped**） | PASS |
| 门禁与记录（AC-05） | m0 **PASS: profile=m0; 23 deterministic checks**；`tests/adapters/sqlite` **114 passed**；`tests/adapters/sqlite+tests/api+tests/integration` **532 passed**；mypy **870 files clean**；ruff/format 干净；RECHECK-076 + MEM-051 + GOAL 记账 + ALL_PLAN | PASS |

## 告警

- **W-1（不是"全部收口"）**：`NOT_GUARDED` 里仍有 25 个公共名不收口（`backup`/`iterdump`/
  `serialize`/`deserialize`/`blobopen`/`create_*`/`set_*`/`load_extension`/`setconfig`/
  `setlimit`/`getconfig`/`getlimit`/`row_factory`/`text_factory`/`total_changes`/
  `in_transaction`，其中 `autocommit`/`isolation_level` 的**赋值**已收口）。它们要么只读、
  要么是进程级配置、要么与语句级锁不是一回事——逐条理由在用例里。
- **W-2（`interrupt` 故意不收口）**：它是"从另一个线程中止正在跑的语句"的机制，
  放进同一把锁等于废掉它。这条**必须**留在名单里，后人别把它当成漏网之鱼"顺手修好"。
- **W-3（仍不做多语句原子事务）**：`with conn:` 只保证事务**边界**动作在锁内；
  一个请求里的多条语句在并发下仍可能被别的线程的语句穿插（既有范围注记不变）。
  要做需要显式的"请求级事务"设计，属独立一项。
- **W-4（名单会过期）**：`NOT_GUARDED` 的理由含"本仓不用"这类判断，随实际使用变化需要重审；
  门禁只保证"集合没变"，保证不了"理由仍然成立"。
- **W-5（`__setattr__` 拦截的代价）**：每次属性赋值多一次名字判断与 `getattr(self, "_lock", None)`；
  代价极小，但这是"用魔法换边界"的取舍，已写进 `__setattr__` 的 docstring。
- **W-6（再导出是"类型面"的约定，不是运行时的）**：`adapters/sqlite/db.py` 里的
  `X as X` 只对 mypy 生效；真正的约束来自"3 个用例按旧路径 import 且全过"。
  若后人把 `cursor.py` 里的类改名，mypy 会红、用例也会红——这条有双保险，不靠约定。

## 结论

本轮把两件事做完：① 事务边界的两个入口（`with conn:`、`isolation_level`/`autocommit` 赋值）
收进同一把锁——**实测**证明覆写 `commit` 并不覆盖它们（C 层直接提交/回滚），
收口前/后用"持锁时是否阻塞"给出确定性对照；② 把"还有哪些入口没收口"从隐含变成
**枚举 + 门禁**：25 个不收口的公共名逐条带理由，用例断言集合相等，CPython 新增公共方法
即红。结果仍为 **PASS_WITH_WARNINGS**：W-1/W-2 是这次枚举本身的边界与例外，
W-3 如实标注"多语句原子事务仍未做"。

另记：交付过程中 m0 两轮红**都不是本轮逻辑的问题**，而是门禁按设计起了作用——
第 1 轮 450 行硬上限（改法是抽取而非放宽阈值），第 2 轮 `no_implicit_reexport`
（改法是 `X as X`）。两条都写进了 PLAN-076 的状态历史，没有静默改门禁或改配置。
