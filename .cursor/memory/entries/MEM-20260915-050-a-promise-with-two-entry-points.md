---
id: MEM-20260915-050
title: 一句承诺有两个入口时，只修一个入口等于没修——顺带：不可移植的差异不要写成判据
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-075-self-made-cursor-serialization.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-075-self-made-cursor-serialization.md
supersedes: []
tags:
  - sqlite
  - concurrency
  - shared-connection
  - portable-gates
  - latent-gap
---

# 一句承诺有两个入口时，只修一个入口等于没修

## 做了什么

`adapters/sqlite/db.py` 的并发口径在 cycle 8（语句级串行）与 cycle 9（锁内取尽）
被修过两次，但**只覆盖 `conn.execute()` 这一个入口**：`conn.cursor()` 返回的仍是
裸 `sqlite3.Cursor`——它的语句执行不取锁、取行不物化。模块 docstring 一直如实写着
这个缺口（"`conn.cursor()` 自建游标的路径也不经物化"），本轮把它补上：

```text
新增  SerializedCursor（锁内执行 + 锁内取尽 + 仓内实际用到的游标面）
接线  SerializedConnection.cursor() 返回它
```

实测（win32 / SQLite 3.50.4，12 线程 × 8 轮"写后立读"，三次运行）：

```text
收口前（裸游标）：problems 15/96、18/96、14/96（异常 10/11/8 + 读不上 5/7/6）
收口后（收口形态）：0/96、0/96、0/96
```

## 为什么这样做

1. **承诺的作用域就是它的入口集合**。类名/文档说"这条连接上的语句是串行的、读是原子的"，
   但实现只保护了 `execute` 系列——调用方随手写 `conn.cursor()` 就掉出保证之外。
   修完两个入口，这句承诺才与实现对齐（这与 [[MEM-20260915-047]] 同族：
   声明了却不成立的东西等于谎言）。
2. **潜伏缺口也要修**。仓内当前**没有** `conn.cursor()` 调用方——它不是正在冒烟的
   缺陷，而是"后来者一用就中"的陷阱。修它的收益是防御性的，记账时如实写成
   "承诺与实现不一致"的修复，而不是缺陷修复。
3. **不可移植的差异不要写成判据**（[[MEM-20260915-048]] 的延续）。本来打算用
   "裸游标会把提交后的新行读进来"当反证，实测发现它**取决于查询计划**：
   带主键 + 排序时新行进来，无主键 + 排序时 sorter 在首次 step 就定死结果集、新行不进来。
   同一条流程换个表形态结论就反转 ⇒ 该行为不能当判据。改用与计划无关的一条：
   裸游标取行**要碰连接**（关门即 `ProgrammingError`），锁内取尽后只读本地列表。
4. **实现前提要先验证**：CPython 3.12 的 `Connection.execute/executemany/executescript`
   在 C 层直接建游标，**不经过** Python 层的 `cursor()` 覆盖（探针 1）——所以覆写
   `cursor()` 不会反过来改变 `execute()` 的行为，两个入口互不干扰。这条不验证就动
   实现，很容易写出"改 A 影响了 B"的意外。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_serialized_cursor_path.py -q   # 9 passed
python -m pytest tests/adapters/sqlite -q                                  # 107 passed
PYTHONPATH=. python scratch/goal3-cycle12-probe6-cursor-load-before-after.py
# 收口前 problems 14~18/96 → 收口后 0/96（本机负载下的观测，仅作记录）
```

判据取"与负载、与查询计划都无关"的四条：① `cursor()` 返回收口对象且读语句物化；
② 持锁时另一线程的语句阻塞（锁真的被取）；③ 读结果在 execute 时刻定死、取行不依赖
连接；④ 裸游标的反证（关门后取行抛错）。

## 适用边界（踩过的坑）

- **`SerializedCursor` 不是完整游标兼容层**：只覆盖仓内实际用到的面；
  `setinputsizes`/`setoutputsize`/`cursor.row_factory` 等未实现，将来要用就按需补。
- **`lastrowid` 只由单条 `execute` 更新**（`executemany` 不更新）——真游标也是这个语义，
  写断言时别想当然（本轮先写错、实测后修正）。
- **负载型数字永远只是记录**：14~18/96 换台机器就变，不作为门禁。
- **仍未覆盖多语句事务**：自建游标与连接级方法都是"单条语句"粒度（既有范围注记不变）。
- 相关：[[MEM-20260915-045]]（共享连接不是并发安全）、
  [[MEM-20260915-046]]（语句级串行不等于读原子）。

## 来源

- PLAN-20260915-075 / RECHECK-20260915-075（GOAL-20260915-003 cycle 12）。
- 探针：`scratch/goal3-cycle12-probe{1,3,4,5,6}-*.py`（探针 2 为同族的内存库版本）。
