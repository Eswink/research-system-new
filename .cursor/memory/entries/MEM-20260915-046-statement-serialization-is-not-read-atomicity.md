---
id: MEM-20260915-046
title: 语句级串行不等于读原子；共享连接的取行窗口会让"写后立读"读错
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-071-shared-connection-read-atomicity.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-071-shared-connection-read-atomicity.md
supersedes: []
tags:
  - sqlite
  - concurrency
  - read-atomicity
  - shared-connection
  - stale-read
---

# 语句级串行不等于读原子：取行窗口会被别的线程打断

## 做了什么

给共享 SQLite 连接加锁（语句级串行，[[MEM-20260915-045]]）之后，还剩一类**静默错误**：
`execute()` 拿到的游标在取行之前被另一个线程的语句/提交打断，于是"写一条、立刻读同一条"
读不到刚提交的行，甚至取回**列数不对**的行。实测（12 线程 × 8 轮"写后立读"）：

```text
语句级串行：每 96 次往返 miss 10 / 14 / 13 / 16 / 20 / 6 / 15 / 11
           另一种形态：_decode 的 zip(..., strict=True) 抛
                       ValueError: zip() argument 2 is shorter than argument 1
读在锁内取尽：0 / 0 / 0
```

修法（`adapters/sqlite/db.py`）：`SerializedConnection._statement` 在锁内执行，
**返回行的语句**（`cursor.description is not None`）就在锁内 `fetchall()`，交回只读视图
`MaterializedRows`（`fetchone` / `fetchmany` / `fetchall` / 迭代 / `rowcount` /
`description` / `close`）。store、路由、composition 一行未动。

## 为什么这样做

1. **锁的粒度要与调用方的"一次读"对齐**：调用方要的是 `execute + 取行`，
   只锁 `execute` 就留下了一个窗口。2×2 对照（写守护 × 读守护）定因：
   只护读 ⇒ 0/96；只护写 ⇒ 1~4/96；都不护 ⇒ 10~14/96 ⇒ **决定性的一侧是读**。
2. **不是快照问题**：miss 发生时 `in_transaction=False`，且**紧接着**在同一连接上跑
   `list_definitions()` 看得见那行、独立连接 100% 看得见 ⇒ 数据早就落库了，
   坏的是这一次取行。
3. **咽喉处修**：`_statement` 是全仓唯一的语句入口，物化在那里做，覆盖所有 store。
4. **不夸大**：物化只保证**单条语句**的读自洽，跨语句的读-改-写仍不原子。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_shared_connection_read_atomicity.py -q
# 四条：写后立读 0 处对不上（3 轮 × 96）/ 反证（语句级串行形态仍会读错）/
#       游标面七项与真游标逐项相等 / 并发解码不再出现短行
python -m pytest tests/adapters/sqlite tests/api -q      # 476 passed
```

**live 压不出这一类**：把控制面切回语句级串行（`SerializedConnection.execute` 打补丁 +
启动标记确认生效）后，216 个并发 `POST /ops/schedules` 仍全 201 ⇒ HTTP 路径的语句密度
稀释了微秒级窗口。**判定修复要用单元级反证，不要拿 live "全绿"当证明**；
反过来，live 上偶发的 `404 unknown schedule` 只能说"与这一类一致"，不能据此定论。

## 适用边界（踩过的坑）

- **仍不是多语句事务原子**：读-改-写跨语句时，别的线程仍可能夹在中间（控制面目前无此类操作）。
- **`conn.cursor()` 不走物化**：自建游标的调用方绕开这条路径（本仓无调用点）。
- **锁内取尽有代价**：返回行多的 SELECT 会在锁内取完 ⇒ 锁持有时间变长（锁粒度告警仍在）。
- **返回对象不再是 `sqlite3.Cursor` 实例**：跨 `Connection.execute` 的声明类型用 `cast`；
  依赖 `isinstance(cursor, sqlite3.Cursor)` 的调用方会受影响（本仓没有）。

## 来源

- PLAN-20260915-071 / RECHECK-20260915-071（GOAL-20260915-003 cycle 9；
  缺陷由 cycle 8 的 RECHECK-070 W-1 如实移交）。
- 相关：[[MEM-20260915-045]]（加锁只治崩溃）、
  [[MEM-20260915-042]]（有界等待：同一族"把语义边界写清楚"的做法）。
