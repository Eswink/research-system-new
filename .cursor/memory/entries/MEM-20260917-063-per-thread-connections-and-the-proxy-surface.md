---
id: MEM-20260917-063
title: "锁粒度换到每线程连接：`__getattr__` 代理面、`:memory:` 归属连接、装配边界的 cast"
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260917-088-per-thread-sqlite-connection.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260917-088-per-thread-sqlite-connection.md
supersedes: []
tags:
  - sqlite
  - concurrency
  - connection-pool
  - duck-typing
  - memory-database
  - test-fixtures
---

# 锁粒度：从"一条连接 + 一把锁"到"每线程一条"

## 做了什么

控制面把**一个** `SerializedConnection` 注入 ~30 个 store，而同步端点跑在 threadpool、
五个守护线程也在写；`SerializedConnection` 的锁只保证"共用一条连接时不并发使用"。
本轮换成 `adapters/sqlite/pool.py::ThreadLocalConnection`：store 拿到的仍是**同一个句柄**，
但语句/游标/事务边界/pragma 全部转发到**本线程自己**的连接（文件库；懒创建，WAL +
`busy_timeout` 同 `db.connect`）。

```text
_open_sqlite(db_path) -> ThreadLocalConnection
    current()            本线程的真实连接（懒创建、登记在案）
    __getattr__          execute/executescript/cursor/commit/rollback/pragma… 全转发
    row_factory         属性代理（写回本线程连接）
    __enter__/__exit__  with conn: = 本线程事务块（sqlite3 语义）
    close() / close_all() / connection_count()
```

## 为什么这样做

1. **"不跨线程用同一条连接"是 SQLite 层面的正确姿势**：`check_same_thread=False` 只是关掉
   检查；锁粒度再细也仍是"多人共用一把事务状态"。每线程一条把这个问题从"纪律"变成"结构"。
2. **store 不该为连接布局改代码**：代理面让 ~30 个 store 一行不动，也让"哪条线程用哪条连接"
   成为纯粹的 adapters 层决定。
3. **跨线程写交给 WAL**：SQLite 自身有写锁 + `busy_timeout`，不需要应用层再串一遍。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_thread_local_connection.py -q      # 池单测 5 条
python -m pytest tests/api/test_ops_schedules_concurrency_api.py -q             # 内存/文件两路径负载
python -m pytest tests/api -q                                                   # 代理面整库兼容（~420 例）
```

## 适用边界（踩过的坑）

- **`:memory:` 属于连接**：每线程一条会各自看到**空库**（不是共享，而是"另一个数据库"）。
  池对这种路径共用一条 —— 这是 SQLite 语义，不是妥协；也意味着**测试夹具默认路径不覆盖
  每线程连接**，要覆盖必须给文件库夹具（本轮就这么做）。
- **`__getattr__` 递归**：转发必须放过下划线名（`current()` 里访问 `self._shared` 时若属性
  缺失会递归进 `__getattr__`）。实现里 `if name.startswith("_"): raise AttributeError(name)`。
- **鸭子类型没有静态检查**：池不是 `sqlite3.Connection` 子类 ⇒ mypy 在装配边界报错，用显式
  `cast` + 注释收口；"连接上不存在的名字"只有运行期才炸，所以**整库套件是覆盖面**（夹具
  统一走池，等于免费拿到 ~30 个 store 的兼容回归）。
- **安全扫描器会把转发方法误报成 SQL 注入**：写成 `def execute(self, sql, ...)` 的转发会被
  Mimosa 拦（"用户输入拼进 SQL"）。用 `__getattr__` 委托既避开误报，也少写 N 个将来会漏的
  转发方法。
- **锁语义变了要写进文档**：`with conn:` 从"全局锁住的块"变成"本线程事务块"；
  `SerializedConnection` 的既有用例（含"A 在块内时 B 进不来"）**原样保留**——它们测的是那个
  类本身，仍服务于"必须共用一条连接"的场景。
- 相关：[[MEM-20260915-047]]（声明要有消费者）、[[MEM-20260917-062]]（事实从事件链接回）。

## 来源

- PLAN-20260917-088 / RECHECK-20260917-088（GOAL-20260917-004 cycle 5 = EC-05 第①半）。
