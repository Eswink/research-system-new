---
id: MEM-20260915-048
title: 不可移植的反证不是门禁：竞态类反证要判结构，不判复现率
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.9
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-071-shared-connection-read-atomicity.md
  - .cursor/plans/tasks/PLAN-20260915-072-provider-endpoint-binding.md
  - .cursor/plans/tasks/PLAN-20260915-073-goal-003-budget-closeout.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-071-shared-connection-read-atomicity.md
  - .cursor/plans/rechecks/RECHECK-20260915-073-goal-003-budget-closeout.md
supersedes: []
tags:
  - testing
  - concurrency
  - ci
  - counterexample
---

# 不可移植的反证不是门禁：竞态类反证要判结构，不判复现率

## 做了什么

cycle 9 给共享 SQLite 连接做"读原子性"时，反证写成**负载型**：同一批并发往返打在
"语句级串行"的连接上**应当**读错。本地（8+ 核 Windows）每次都能压出 10~20/96，
CI 的 `quality-ubuntu-latest`（2 vCPU）**288 次往返一次都没复现** ⇒ `python/tests` 判红
（run 35115260874）。cycle 10 把反证改成**结构判据**：

```text
产品路径：connect() 的读结果在锁内取尽（type(cursor).__name__ == "MaterializedRows"）
退回形态：返回裸 sqlite3.Cursor（取行在锁外 ⇒ 结构上不存在原子性）
```

确定性、任何机器成立；改回去就红。负载型复现器（数字 + 脚本）降级为**记录**。

## 为什么这样做

1. **竞态的"复现率"是环境属性，不是代码属性**：并行度一变（核数、调度、GIL 切换）
   复现率可能从 10% 掉到 0，门禁就会随机红——那是对 CI 撒谎，不是对代码把关。
2. **"确定性交错"也不保证**：试过拿住游标 + 让另一线程写+提交后再取行（单线程可编排的
   时间窗交错），**不触发**——这类竞态要两个线程**同时**在 sqlite3 的 C 调用里（GIL 已释放），
   顺序交错不等于并发。
3. **判结构就能判"性质还在不在"**：被保护的性质是"读结果在锁内取尽"，
   它可以在不引入负载的前提下断言；症状级证据留给记录（并且如实标注平台依赖）。
4. **诚实记账**：红项要按失败分类表定性（本轮 = 反证不可移植，不是代码缺陷、
   也不是门禁过严），并把"更正后在哪次 run 上验证"写清楚（cycle 10 的
   run 35119573827：六个 job 全 success）。

## 怎么做与复现

```bash
python -m pytest tests/adapters/sqlite/test_shared_connection_read_atomicity.py -q
# 结构反证 + 负载型钉子（只断言"无坏结果"，不断言"一定坏"）
sh scratch/run-m0-cycle12.sh        # 本地 m0 23/23 才是收口前置
```

**写反证时的检查清单**：① 被保护的性质能否**不依赖负载**断言？② 症状级复现器在
目标机器上有多少余量（核数、超时）？③ 若某天反证不再复现，记录里要能查到
"当时的复现条件"，而不是删掉它。④ 别把"门禁换判据"说成"放宽断言"——
要说清被保护的性质有没有变。

## 适用边界（踩过的坑）

- **不是所有反证都能结构化**：只能结构化的性质才适用；纯数值/统计类的仍要靠阈值 + 余量。
- **结构判据不覆盖"未来形态"**：它钉的是当前实现的形态；换实现（例如改成每线程连接）
  时判据要一起改，别机械保留。
- **live/低并发环境同理**：cycle 9 的 live 对照（216 个并发 POST 全 201）也压不出这一类，
  已如实写成"补充观察"——**live 全绿不等于竞态已治**。

## 来源

- PLAN-20260915-071 / RECHECK-20260915-071（更正段）、PLAN-20260915-072、
  RECHECK-20260915-073（GOAL-003 收口；CI run 35115260874 红 → 35119573827 绿）。
- 相关：[[MEM-20260915-046]]（语句级串行不等于读原子）、
  [[MEM-20260915-045]]（加锁只治崩溃）。
