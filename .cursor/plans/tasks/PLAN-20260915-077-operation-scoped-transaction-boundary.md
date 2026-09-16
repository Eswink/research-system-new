---
id: PLAN-20260915-077
slug: operation-scoped-transaction-boundary
title: 操作级事务边界：with conn 从语句边界升级为持锁的块边界（共享连接的跨线程提交/回滚爆炸半径归零）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 14 = RECHECK-20260915-076 后继（多语句事务语义）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-077-operation-scoped-transaction-boundary.md
memory_entries:
  - MEM-20260915-052-the-transaction-was-the-connection-not-the-operation
---

# PLAN-20260915-077 — 操作级事务边界（GOAL-003 cycle 14）

## 目标

`adapters/sqlite/db.py` 的模块 docstring 写着"SQLite 提供单进程 ACID 与进程重启级持久化"，
`adapters/sqlite/workflow_ops.py` 的 `_persist_new_lease` 写着"Insert a fresh lease row, mark
the task LEASED, publish TASK_LEASED"（一次操作三条写语句），`OutboxWriter.publish` 的
docstring 写着"事务内写 outbox（调用方持有写锁/事务）"。控制面各处也**已经**用
`with self._conn:` 把一次操作包起来——看起来事务边界是有的。

探针 2/3 实测的结果与这个印象**相反**：

- **`with conn:` 不持锁**（探针 2 A：块内第一个写之后，另一个线程的语句 0.000s 就执行完）。
  也就是说"操作的原子边界"只覆盖 `__exit__` 那一瞬间，块内的语句别的线程可以随便穿插。
- **别的线程可以提交你半个操作**（探针 2 B：线程 A 还在块里，线程 B 自己的
  `with conn:` 退出就把 A 的第一次写**提交**了，第三个连接当场看得见 → 操作不是原子的）。
- **别的线程的失败会回滚掉你已完成的操作**（探针 3：线程 A 的操作整段跑完、无异常，
  线程 B 的块在写之后抛错 → 两个线程都结束后，第三个连接看到**两行全没了**，
  包括 A 那条已经"成功返回"的写）。这是**数据丢失**级的行为，而根因是
  事务边界属于**连接**、不属于**操作**：共享连接上只有一个隐式事务，
  谁的 `commit`/`rollback` 先到，谁就决定了别人写的命运。

本轮把事务边界从"连接的"变成"操作的"：`with conn:` 进入时**取锁**、退出时提交/回滚后
**释放锁**，于是块内语句与块边界同属一个线程独占区间——别的线程既插不进语句，
也无法提交/回滚它。

## 口径

1. **块 = 操作的独占区间**：`__enter__` 取可重入锁、`__exit__` 提交/回滚后释放
   （`try/finally`，提交失败也必须释放）。异常仍**不吞**（与真连接一致）。
2. **不改语义、只改边界**：成功提交、异常回滚、返回值恒 False 都不变；
   `execute`/`cursor`/`commit`/`rollback`/`close` 的既有行为不变。
3. **写入一律在块里**：把仍是"裸 `commit()`"的写路径改成 `with conn:` 块
   （构造期的 schema bootstrap 除外——那是本连接的初始化，不是并发写路径）。
4. **判据要确定性与可移植**：用"块开着时另线程的语句是否阻塞""外部连接在块内/块后
   分别看到几行""回滚是否吃掉别人的写"三条**结构化**对照，不依赖负载与调度。
5. **如实标注取舍**：持锁整块会拉长临界区（块内不能等待别的线程使用同一连接）。
   本仓 `adapters/sqlite/**` 的 74 个 `with` 块体内**没有**任何线程原语或外部 I/O
   （AST 扫描为 0），因此这条取舍在本仓是安全的——但它是**约定**，写进风险。

## 范围

- 修改：`adapters/sqlite/db.py`（`_enter_context` 取锁、`_exit_context` 提交/回滚后释放 +
  类 docstring 的范围段更新）。
- 修改（写路径进事务块）：`adapters/sqlite/tool_pack_store.py`（install/replace/revoke）、
  `adapters/sqlite/schedule_store.py`（save_definition/delete_definition）、
  `adapters/sqlite/eval_report_store.py`（put）。
- 新增：`tests/adapters/sqlite/test_shared_connection_transaction_scope.py`。
- **不改**：Postgres adapter（它本来就用真事务）、任何 Port/Domain/DTO/schema、任何调用方签名。

## 验收条件

- [x] AC-01 **块持锁**（确定性）：块开着时，另线程的 `execute` 在 0.5s 内拿不到结果
      （`TimeoutError`）；块退出后立即完成。
- [x] AC-02 **操作原子性对外可见**：块内第一个写之后、块退出之前，**外部连接**看不到
      任何一行；块退出后一次看到该操作的全部行。
- [x] AC-03 **提交/回滚不再有跨操作爆炸半径**（回归，探针 3 的原样重放）：A 的块无异常、
      B 的块抛错 → A 的写**仍在**、B 的写不在。
- [x] AC-04 **别人的块不再能被中途提交**（回归，探针 2 B 原样重放）：A 在块内时，
      B 的 `with conn:` 必须等待；期间外部连接看不到 A 的行。
- [x] AC-05 **提交失败也要释放锁**：注入 `commit()` 抛错的连接，块退出抛出后锁必须是空的
      （另线程 0.5s 内可执行）。
- [x] AC-06 **写入无裸 commit**（结构门禁）：AST 扫描 `adapters/sqlite/*.py`，除
      `__init__`/schema bootstrap 的白名单外，`.commit()` 调用必须落在 `with` 块内。
- [x] AC-07 **不吞异常 + 可重入**（回归）：块内异常仍然向外抛；同线程嵌套块不死锁。
- [x] AC-08 **门禁与记录**：m0 23 项 + 受影响定向套件 + RECHECK-077 + MEM-052 + GOAL 记账 +
      ALL_PLAN 行；探针 2/3 的**收口前**实测与收口后对照记入复检。

## 实施清单

- [x] WP-A `__enter__`/`__exit__` 改为持锁整块（`try/finally` 释放）
- [x] WP-B 三处裸 `commit()` 写路径改成事务块（tool_pack ×3 / schedule ×2 / eval_report ×1）
- [x] WP-C 新用例：块持锁 / 原子性对外 / 两条探针原样重放 / 提交失败释放锁 / 无裸 commit 门禁
- [x] WP-D 收口前实测（探针 2/3）+ 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
# 收口前（探针 2，共享连接）
A. thread B's statement while A is inside `with conn:` took 0.000s (>=0.5 = blocked)
B. witness sees tasks=1 while A is still INSIDE its block (1 = half-op committed)
# 收口前（探针 3，回滚爆炸半径）
PROBE3 witness rows after both operations: []
        a1 present? False  (A 已完成的操作被 B 的失败回滚掉)
        b1 present? False

# 收口后（同脚本同参数）
probe2 A: 另线程语句被阻塞（≥0.5s，实测 10.016s 直到块退出）
probe3:   PROBE3 witness rows after both operations: ['a1']

$ python -m pytest tests/adapters/sqlite/test_shared_connection_transaction_scope.py -q
8 passed
$ python -m pytest tests/adapters/sqlite -q
122 passed
$ python -m mypy
Success: no issues found in 871 source files
$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks   全量 pytest 3663 passed / 10 skipped
```

## 影响报告

- **Domain/API/schema**：无变化（纯 adapter 内部并发/事务口径）。
- **安全/凭据**：无变化。回滚爆炸半径归零同时**去掉了一类数据丢失路径**。
- **兼容性/迁移风险**：`with conn:` 的语义从"退出时提交/回滚"变成"整块独占 + 退出提交/回滚"，
  调用方代码无需改动；代价是临界区变长（块内不得等待别的线程使用同一连接）。
  仓内 `adapters/sqlite/**` 的块体内无线程原语/外部 I/O（AST 扫描 0 命中），
  但这是**约定**，新增代码必须遵守。
- **可观测性**：无变化。
- **下一项任务**：锁粒度（每线程连接，把长临界区代价拿掉）；「按声明给 adapter 接线」
  仍待 escalation 决策（受控出网）。

## 已知风险

- **临界区变长**：块内做重活会拖住其它线程；本仓块内只有 DB 与 telemetry 调用。
- **块内等待别的线程 = 死锁**：约定"块内不等待使用同一连接的线程"；门禁只覆盖裸 commit，
  覆盖不了这条（如实标注）。
- **跨进程仍是 SQLite 语义**：本轮的块边界只在**进程内**成立；多进程仍靠 busy_timeout/WAL。
- **不是 savepoint**：嵌套块是重入同一事务，内层退出会提交外层（与 stdlib `with conn:` 一致）。
- **构造期 commit 仍在白名单**：schema bootstrap 的 `commit()` 会提交连接上已有的东西，
  这属启动期行为，未纳入本轮。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 先用探针 1 确认共享连接的隐式事务长什么样
  （`isolation_level=''`、DML 开事务、SELECT **不**隐式提交），再用探针 2 证伪"`with conn:`
  就是操作的事务边界"（块不持锁、另线程可中途提交），用探针 3 拿到**数据丢失**级的
  确定性反证（B 的失败回滚掉 A 已完成的操作，外部连接两行全看不到）。
- 2026-09-17 WP-A…C 完成：`__enter__` 取锁、`__exit__` 提交/回滚后 `finally` 释放；
  三处裸 `commit()` 写路径改事务块；新用例 8 条（含两条探针的原样重放 + 提交失败释放锁 +
  AST 无裸 commit 门禁）全绿。
- 2026-09-17 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**，
  **首轮即绿**，全量 pytest **3663 passed / 10 skipped**），ruff/format 干净、
  mypy **871 files clean**，记录落盘（RECHECK-077 + MEM-052 + GOAL cycle 14 记账 + ALL_PLAN）。
- 2026-09-17 交付过程中的两处**如实记录**：① 结构门禁（AST）首轮就抓出 4 处此前
  没注意到的真实写路径裸 `commit()`（`project_store.delete_project`、
  `project_settings_store.delete`、`tool_provider_registry.save_registration/delete_registration`），
  一并改成事务块——门禁起到了设计作用，不是"写完再补门禁"；② 目标 DSN 组合跑
  （`tests/api+contracts`）出现 `password authentication failed for user "research_os"`，
  按 m0 口径钉住 DSN 后 **937 passed / 2 skipped** ⇒ 是 litellm `load_dotenv()` 注入
  操作者 `.env` 的**已知环境行为**，**不是**本轮代码回归（见 MEM-052 的适用边界）。
