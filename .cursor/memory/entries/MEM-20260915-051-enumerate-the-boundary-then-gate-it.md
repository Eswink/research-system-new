---
id: MEM-20260915-051
title: 把边界枚举出来再门禁：隐含的"范围之外"迟早会藏进一个没人看过的入口
status: ACTIVE
created_at: 2026-09-17
updated_at: 2026-09-17
scope: repository
confidence: 0.9
review_after: 2027-09-17
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-076-connection-boundary-enumeration.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-076-connection-boundary-enumeration.md
supersedes: []
tags:
  - sqlite
  - concurrency
  - boundary
  - gated-invariants
  - context-manager
---

# 把边界枚举出来再门禁

## 做了什么

`SerializedConnection` 的承诺是"同一连接的多线程使用串行化（语句 + 事务边界）"。
cycle 8/9/12 补了 `execute` 系列、锁内取尽、自建游标，但"还有哪些入口没收口"一直是
**隐含**的。本轮做两件事：

```text
收口       __enter__/__exit__（with conn: 成功提交、异常回滚，都在锁内）
           isolation_level / autocommit 的**赋值**（__setattr__ + LOCKED_ATTRIBUTES）
           —— 读取刻意不收口（只读标志位，不触碰连接状态）
枚举门禁   tests/adapters/sqlite/test_serialized_connection_surface.py
           逐条登记"不收口"的 25 个公共名与理由；用例断言"未收口集合 == 那张表"
```

实测（win32 / CPython 3.12 / SQLite 3.50.4）：

```text
覆写 commit/rollback ≠ 锁住事务边界：
  with conn: 的提交/回滚在 C 层直接做，**不经过** Python 层覆写
  isolation_level / autocommit 的 setter 同理

确定性对照（持锁时另线程是否阻塞）：
  with 退出        收口前 False → 收口后 True
  属性赋值         收口前 False → 收口后 True
```

## 为什么这样做

1. **"范围之外"必须是可读的名单，不是感觉**。只要边界靠记忆维持，下一个入口
   （`with conn:`、属性 setter、CPython 新加的方法）就会悄悄落在锁外——而且**没人会发现**。
   把它写成字面量集合 + 用例，边界就从"我以为"变成"机器检查的"。
2. **门禁要能对着"未来"报警**：断言"未收口集合 == 名单"意味着 CPython 一旦新增公共
   方法，用例立刻红，逼一次决定（收口，或写清为什么不收）。这比"我现在检查过一遍"强得多。
3. **有些名字必须**不收口**，写下来才不会被后人当成疏漏**：`interrupt` 的用途就是被
   别的线程调用来中止正在跑的语句——把它塞进同一把锁会正好废掉这个能力。
   这类"故意"只有写在名单里才不会被"顺手修好"。
4. **判据要确定性**：本轮的收口前/后对照用"持锁时是否阻塞"，与负载和查询计划都无关
   （[[MEM-20260915-048]]），可以直接当判据；不像负载型数字只能当记录。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_serialized_connection_surface.py -q   # 7 passed
PYTHONPATH=. python scratch/goal3-cycle13-probe2-boundary-before-after.py
# 收口前 False/False → 收口后 True/True（持锁时是否阻塞）
```

改连接边界时的检查清单：① 新入口要么收口、要么进 `NOT_GUARDED` 并写清理由；
② `LOCKED_ATTRIBUTES` 只能是 `NOT_GUARDED` 的子集（两处边界不能各说各话）；
③ 事务边界动作要在锁内、只读属性不进锁；④ 门禁用例保持"集合相等"，别改成"包含"。

## 适用边界（踩过的坑）

- **是"枚举 + 门禁"，不是"全部收口"**：`backup`/`iterdump`/`serialize`/`create_function`/
  `load_extension` 等仍不收口（本仓不用，且与语句级锁不是一回事）。
- **仍不把多条语句变成原子事务**：`with conn:` 只保证事务**边界**动作在锁内，
  不保证"一个请求里的多条语句"在并发下互不穿插（这是独立的一项）。
- **`NOT_GUARDED` 的理由会过期**：名单里的"本仓不用"要随实际使用变化重审。
- **只读属性不进锁是有意的**：给读也加锁会把"读标志位"变成潜在阻塞点，得不偿失。
- 相关：[[MEM-20260915-050]]（承诺有两个入口时只修一个等于没修）、
  [[MEM-20260915-045]]（共享连接不是并发安全）。

## 来源

- PLAN-20260915-076 / RECHECK-20260915-076（GOAL-20260915-003 cycle 13）。
- 探针：`scratch/goal3-cycle13-probe{1,2}-*.py`。
