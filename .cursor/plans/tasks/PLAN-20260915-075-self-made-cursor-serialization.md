---
id: PLAN-20260915-075
slug: self-made-cursor-serialization
title: 自建游标收口：兑现「这条连接上的语句串行、读原子」这句承诺（conn.cursor 路径）
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 12 = RECHECK-20260915-074 后继②（`conn.cursor()` 自建游标路径收口）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE，从 cycle 11 续跑）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-075-self-made-cursor-serialization.md
memory_entries:
  - MEM-20260915-050-a-promise-with-two-entry-points
---

# PLAN-20260915-075 — 自建游标收口（GOAL-003 cycle 12）

## 目标

`adapters/sqlite/db.py` 的并发口径在两个 cycle 里被修过（cycle 8 语句级串行、cycle 9
锁内取尽），但**只覆盖 `conn.execute()` 这一个入口**：

```text
SerializedConnection.execute/executemany/executescript  → 取锁（+ 读语句锁内取尽）
SerializedConnection.cursor()                           → 只把"创建游标"这一步收进锁，
                                                          返回的仍是裸 sqlite3.Cursor
```

裸游标的 `execute()` **不取锁**、`fetch*()` **不物化**，于是：

- 同一连接上并发使用自建游标，会退回 cycle 8 的崩溃类（`InterfaceError`）；
- 读的结果也不再在 execute 时刻定死（实测见下）。

模块 docstring 本来就如实写着这个缺口（"`conn.cursor()` 自建游标的路径也不经物化"）
——本轮把缺口补上，让那句承诺对**两个入口**都成立。

## 口径

1. **收口而不是禁止**：`conn.cursor()` 继续返回游标语义的对象，但语句在锁内执行、
   读语句的行在锁内取尽（`SerializedCursor`），与 `conn.execute()` 同一套口径。
2. **不改契约面**：`execute()` 仍返回 `MaterializedRows`（cycle 9 的结构判据不变）；
   `executemany/executescript/commit/rollback/close` 行为不变。
3. **判据必须可移植**：负载型复现是**记录**不是门禁（MEM-048）。
   本轮的确定性判据：① 持锁时另一线程的语句**阻塞**（锁真的被取）；
   ② 读结果在 execute 时刻定死（取行不因后来的提交而变）；
   ③ 取行不再依赖连接（关门之后仍可取）。
4. **反证要挑与平台无关的那条**：实测发现"裸游标会不会读到提交后的新行"**取决于
   查询计划**（带主键 + 排序：新行进来；无主键 + 排序：sorter 定死结果集，不进来），
   因此**不**把它写成判据；改写与计划无关的一条——裸游标取行要碰连接
   （关门即 `ProgrammingError`），锁内取尽后只读本地列表。
5. **零生产调用方也要修**：当前仓内没有 `conn.cursor()` 调用方（只有 docstring 提到），
   所以这是**潜伏缺口**——正因为它是潜伏的，修它的价值在于"承诺与实现一致"，
   而不是"修一个正在冒烟的缺陷"。本轮如实这样记账。

## 范围

- 修改：`adapters/sqlite/db.py`（新增 `SerializedCursor`；`cursor()` 返回它；
  更新两处"范围注记"docstring）。
- 新增：`tests/adapters/sqlite/test_serialized_cursor_path.py`（结构 / 锁 / 冻结 /
  跨连接存活 / 裸游标反证 / 往返 / 游标面 / 负载回归）。
- **不改**：任何 store、composition、Port 契约；不改 `MaterializedRows` 的语义。

## 验收条件

- [x] AC-01 **结构**：`conn.cursor()` 返回 `SerializedCursor`（不是 `sqlite3.Cursor`），
      读语句的结果在 execute 内物化成 `MaterializedRows`；`conn.execute()` 的返回类型
      不变（cycle 9 的结构判据继续成立）。
- [x] AC-02 **锁真的被取**（确定性）：另一线程持锁时，通过自建游标执行语句会阻塞，
      释放后立即完成。
- [x] AC-03 **读在 execute 时刻定死**（确定性）：execute 之后、取行之前的写入+提交
      不进入本次结果；取行不依赖连接（关门后仍可取）；**反证**：裸游标同一动作
      关门即 `ProgrammingError`。
- [x] AC-04 **游标面与往返**：自建游标的 `execute/executemany/executescript/
      fetchone/fetchmany/fetchall/迭代/close/description/rowcount/lastrowid/arraysize/
      connection` 可用；写入（单条 + 批量）提交后读得回来。
- [x] AC-05 **负载回归**：12 线程 × 8 轮"写后立读"经自建游标不再出现异常或读不上
      （回归，不是反证）。
- [x] AC-06 **门禁与记录**：m0 23 项 + 受影响定向套件 + RECHECK-075 + MEM + GOAL 记账 +
      ALL_PLAN 行；实测数字（收口前/后）记入复检。

## 实施清单

- [x] WP-A `SerializedCursor`（锁内执行 + 锁内取尽 + 游标面）
- [x] WP-B `cursor()` 接线与两处 docstring 更新
- [x] WP-C 确定性用例 + 裸游标反证 + 负载回归
- [x] WP-D 收口前/后实测（记录）+ 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
$ python -m pytest tests/adapters/sqlite/test_serialized_cursor_path.py -q
9 passed
$ python -m pytest tests/adapters/sqlite -q
107 passed
$ python -m pytest tests/adapters/sqlite tests/api tests/integration -q
525 passed
$ python -m mypy
Success: no issues found in 868 source files
$ PYTHONPATH=. python scratch/goal3-cycle12-probe6-cursor-load-before-after.py
收口前：problems 15/96、18/96、14/96（异常 10/11/8 + 读不上 5/7/6）
收口后：problems 0/96、0/96、0/96
$ sh scratch/run-m0-cycle12.sh
PASS: profile=m0; 23 deterministic checks
```

m0 首轮红于 `python/typecheck`：`cursor()` 在类型上放宽成 Any，用例里
`return cursor.fetchall()` 触发 `no-any-return` ⇒ 用例显式 `cast` 收回类型
（**未放宽 mypy 配置**）。第二轮红于 `framework/validate`：PLAN 标题以反引号开头
导致 frontmatter 无法解析（YAML 特殊字符）⇒ 改写标题；另两条是同一张记录尚未落盘
产生的投影不一致（`## 影响报告` 缺失、ALL_PLAN 状态未同步），补齐后复跑通过。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 时先确认缺口真实（仓内无 `conn.cursor()`
  调用方 ⇒ 潜伏缺口；docstring 已如实登记），再用 4 个探针把"该写什么判据"问清楚——
  探针 3/4 证明裸游标"读到提交后新行"的行为取决于查询计划（不可移植），
  探针 5 找到与计划无关的对比（裸游标取行要碰连接），探针 6 拿到收口前/后的负载数字。
- 2026-09-17 WP-A…C 完成：`SerializedCursor` + `cursor()` 接线 + 两处 docstring 更新；
  九条用例（结构 / 锁 / 冻结 / 跨连接存活 / 裸游标反证 / 形态差异 / 往返 / 游标面 /
  负载回归）全绿。
- 2026-09-17 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**），
  ruff/format 干净、mypy **868 files clean**，记录落盘（RECHECK-075 PASS_WITH_WARNINGS +
  MEM-050 + GOAL cycle 12 记账 + ALL_PLAN）。

## 影响报告

- **Domain/API/schema**：无变化（纯 adapter 内部口径）。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：`conn.cursor()` 的返回类型从 `sqlite3.Cursor` 变成
  `SerializedCursor`（只覆盖仓内用到的游标面）。仓内**无调用方**，故无迁移动作；
  但第三方代码若把它当完整游标用（`setinputsizes` 等），需要按需补齐（见告警 W-2）。
- **可观测性**：无变化。
- **下一项任务**：多语句事务语义（`with conn:` 的事务边界）或锁粒度（每线程连接）；
  按声明给 provider adapter 接线仍待 escalation 决策。

## 已知风险

- **负载数字不可移植**：14~18/96 是本机负载下的观测，只作记录（MEM-048）。
- **游标面不完整**：`setinputsizes`/`setoutputsize`/`cursor.row_factory` 未实现。
- **潜伏缺口的收益是防御性的**：仓内无调用方，修的是"承诺与实现不一致"。
- **仍不做多语句事务**：自建游标与连接级方法都是"单条语句"粒度。
