---
id: MEM-20260915-052
title: 事务边界属于连接时，别人的 commit/rollback 决定你的写（可能整条操作丢失）
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.93
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-077-operation-scoped-transaction-boundary.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-077-operation-scoped-transaction-boundary.md
supersedes: []
tags:
  - sqlite
  - concurrency
  - transaction
  - shared-connection
  - data-loss
---

# 事务边界属于连接时，别人的 commit/rollback 决定你的写

## 做了什么

共享 SQLite 连接上**只有一个隐式事务**（`isolation_level=''`：DML 打开、SELECT 不隐式提交），
所以"事务边界"实际上属于**连接**而不是**操作**：任何线程的 `commit()`/`rollback()`
都在替整条连接上的所有未提交写签字。控制面看起来是有事务边界的——各处都写着
`with self._conn:`——但实测它不是：

```text
探针 2（块开着时，另线程在做什么）
  A. 块内第一个写之后，另一个线程的语句 0.000s 就执行完      ⇒ 块**不持锁**
  B. 另线程自己的 `with conn:` 退出后，第三个连接在 A 仍在块内时看到了 A 那行
     ⇒ 半个操作被**提交**了

探针 3（回滚的爆炸半径）
  A 的操作整段跑完（写 a1、无异常）+ B 的块写 b1 后抛错
  ⇒ 两线程都结束后，外部连接 SELECT 返回 []   —— a1 也没了（**数据丢失**）
```

收口：`with conn:` 从"语句边界"升级为"**操作边界**"——`__enter__` 取可重入锁、
`__exit__` 提交/回滚后 `finally` 释放。块内语句与块边界同属一个线程独占区间，
别的线程既插不进语句，也提交/回滚不了它。同口径重放：探针 3 `[] → ['a1']`，
探针 2 A 由 0.000s 变成被阻塞。

## 为什么这样做

1. **"看起来有事务"比"没有事务"更危险**：`with self._conn:` 的写法让 review 与自测都
   以为操作是原子的，而真实语义只是"退出那一刻提交"。半个操作被提交/被回滚这类
   失效**不会在小规模测试里出现**——它需要"块中途另一个线程恰好也在写"。
2. **回滚的爆炸半径是数据丢失级**：别人的失败能抹掉你**已经成功返回**的写。
   这不是"隔离级别不够"，而是"边界挂错了对象"。
3. **两种写法并存本身就是信号**：`with self._conn:`（块内提交）与裸 `self._conn.commit()`
   （提交连接上待提交的一切）在同一个仓里混用，说明"边界在哪"没有共识。
   裸 commit 在共享连接上等于"替别人的半个操作签字"。
4. **判据要确定性与可移植**：用"块开着时另线程的语句是否阻塞""外部连接在块内/块后
   各看到几行""回滚是否吃掉别人的写"三条**结构化**对照，不用负载型复现器
   （[[MEM-20260915-048]]）。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_shared_connection_transaction_scope.py -q  # 8 passed
PYTHONPATH=. python scratch/goal3-cycle14-probe3-rollback-blast-radius.py   # 收口后 ['a1']
PYTHONPATH=. python scratch/goal3-cycle14-probe2-block-boundary.py           # 收口后 A 项被阻塞
```

改共享连接边界时的检查清单：① 边界要持有**锁**，不是只持有提交动作（入口取、出口释放，
释放放 `finally`——提交失败也必须还锁，否则整条连接永久卡死）；② 写路径**不许裸 commit**，
用 AST 门禁把"非 `with` 块内的 `.commit()`"钉成字面量白名单（只留构造期 schema bootstrap）；
③ 覆盖 `commit`/`rollback` 时要覆盖**类属性**本身，改 `_commit_txn` 不会影响已经绑定的
`commit = _commit_txn`（子类化时的真实坑）；④ 判据用外部连接做证人，别用"共享连接自己看得见"
（同一连接永远看得见自己未提交的写）。

## 适用边界（踩过的坑）

- **临界区变长**：块现在独占整条连接。块内做重活（特别是 IO）会拖住其它线程；
  本仓块体内只有 DB 与 telemetry（AST 扫描：线程原语/外部 IO 0 命中），但这是**约定**。
- **块内等待使用同一连接的线程 = 死锁**：这条**没有门禁**（AST 判不出"是否等待"），
  只能靠 review 与 docstring。
- **不是 savepoint**：嵌套块重入同一事务，内层退出会提交外层（与 stdlib 一致）。
- **只在进程内**：跨进程仍是 SQLite 语义（WAL + `busy_timeout`）。
- **构造期 commit 仍在**：8 处 `__init__`/schema bootstrap 的 `commit()` 留在白名单里。
- **目标 DSN 类失败要先怀疑环境**：`tests/api+contracts` 组合跑出的
  `password authentication failed for user "research_os"` 是 litellm `load_dotenv()`
  注入操作者 `.env` 的已知行为，按 m0 口径把 DSN 钉住即 937 passed——**不是**代码回归。
- 相关：[[MEM-20260915-051]]（把边界枚举出来再门禁）、[[MEM-20260915-050]]（承诺有两个入口）、
  [[MEM-20260915-045]]（共享连接不是并发安全）、[[MEM-20260915-046]]（语句串行不等于读原子）。

## 来源

- PLAN-20260915-077 / RECHECK-20260915-077（GOAL-20260915-003 cycle 14）。
- 探针：`scratch/goal3-cycle14-probe{1,2,3}-*.py`。
