---
id: PLAN-20260915-076
slug: connection-boundary-enumeration
title: 连接边界枚举化：事务边界的两个入口收口 + 未收口名单变成可门禁的字面量
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 13 = RECHECK-20260915-075 后继（多语句事务语义/事务边界入口；本轮先做「边界枚举 + 事务边界收口」这条可独立验收的部分）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」+ 2026-09-17 用户拍板恢复条件②（显式变更 budget.max_cycles 10→20 并置回 ACTIVE）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-076-connection-boundary-enumeration.md
memory_entries:
  - MEM-20260915-051-enumerate-the-boundary-then-gate-it
---

# PLAN-20260915-076 — 连接边界枚举化（GOAL-003 cycle 13）

## 目标

`SerializedConnection` 的承诺是"同一连接的多线程使用串行化（语句 + 事务边界）"。
cycle 8/9/12 补上了 `execute` 系列、锁内取尽、自建游标，但"**还有哪些入口没收口**"
一直是隐含的：没人能一眼说出边界在哪，也没人会发现新出现的入口留在锁外。

本轮做两件事：

1. **事务边界收口**（实测确认是缺口）：`with conn:`（`__enter__`/`__exit__`）与
   `isolation_level` / `autocommit` 的**赋值**。探针 1 实测：CPython 3.12 的上下文管理器
   与属性 setter 在 C 层直接提交/回滚/发语句，**不经过** Python 层覆写的
   `commit`/`rollback`——覆写了 `commit` 不等于锁住了事务边界。
2. **边界枚举化**（把隐含变成可门禁的）：公共名逐条登记"收口 / 刻意不收口 + 理由"，
   并用例把"未收口集合"钉成一个**字面量集合**——CPython 换版本带来新公共方法时用例会红，
   逼一次"要不要收口"的决定（而不是让它悄悄留在锁外）。

## 口径

1. **收口事务边界**：`__enter__`/`__exit__` 语义与真连接一致（成功提交、异常回滚、
   不吞异常），提交/回滚在锁内；`isolation_level`/`autocommit` 的**赋值**在锁内，
   **读取**不进锁（只读标志位，不触碰连接状态）。
2. **如实列出"不收口"的名单与理由**：例如 `interrupt` **故意**不收口——它的用途就是
   被别的线程调用来中止正在跑的语句，放进同一把锁会正好废掉这个能力；`backup`/
   `iterdump`/`serialize`/`load_extension` 等本仓不用且与语句级锁不是一回事，逐条写理由。
3. **判据要确定性与可移植**：用"持锁时另线程是否阻塞"做**确定性**对照
   （收口前 `with` 退出不阻塞、收口后阻塞），不依赖负载或查询计划。
4. **不改既有语义**：`execute`/`cursor`/`commit`/`rollback`/`close` 行为不变；
   仍不把多条语句变成原子事务。
5. **不夸大**：本轮收口的是**事务边界入口**；"多语句原子事务"（一个请求内多条语句
   一个事务）仍是未做的独立项，如实留在下一轮输入里。

## 范围

- 修改：`adapters/sqlite/db.py`（`__enter__`/`__exit__`、`__setattr__` + `LOCKED_ATTRIBUTES`、
  类 docstring 的"边界是枚举出来的"段；另因触到 450 行硬上限，取行面被拆出，见下条）。
- 新增：`adapters/sqlite/cursor.py`（`MaterializedRows` / `SerializedCursor` **原样搬移** +
  模块 docstring；由 `db.py` 用 `X as X` 显式再导出，既有 `from adapters.sqlite.db import ...`
  调用点——含 3 个用例——路径与名字都不变。`db.py` **475 → 331 行**、新模块 170 行。
  这是硬上限挡住的**机械拆分**，不是为做新功能而拆。）
- 新增：`tests/adapters/sqlite/test_serialized_connection_surface.py`（枚举门禁 + 事务边界
  语义 + 确定性锁判据 + 混合负载回归）。
- **不改**：任何 store/composition/Port；不引入依赖；`MaterializedRows`/`SerializedCursor`
  的行为**不变**（只换了模块位置）。

## 验收条件

- [x] AC-01 **枚举门禁**：公共名中"未收口集合"恰好等于文档化的 `NOT_GUARDED` 表
      （逐条带理由）；`NOT_GUARDED` 里没有过期名字；`LOCKED_ATTRIBUTES ⊆ NOT_GUARDED`。
- [x] AC-02 **事务边词语义**：`with conn:` 成功提交、异常回滚、不吞异常（与真连接一致）。
- [x] AC-03 **事务边界在锁内**（确定性）：持锁时 `__exit__` 与 `isolation_level` 赋值都会
      阻塞，释放后完成；**对照**：读取 `isolation_level` 不阻塞（读取刻意不收口）。
- [x] AC-04 **回归**：12 线程混合使用 `with conn:` 与直接执行语句不出现异常/坏读。
- [x] AC-05 **门禁与记录**：m0 23 项 + 受影响定向套件 + RECHECK-076 + MEM-051 + GOAL 记账 +
      ALL_PLAN 行；收口前/后的**确定性**对照（探针 2）记入复检。

## 实施清单

- [x] WP-A `__enter__`/`__exit__` 收口（锁内提交/回滚）
- [x] WP-B `isolation_level`/`autocommit` 赋值收口（`__setattr__` + `LOCKED_ATTRIBUTES`）
- [x] WP-C 枚举门禁 + 事务边界语义 + 确定性锁判据用例
- [x] WP-D 收口前/后确定性对照 + 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
$ python -m pytest tests/adapters/sqlite/test_serialized_connection_surface.py -q
7 passed
$ python -m pytest tests/adapters/sqlite -q
114 passed
$ python -m pytest tests/adapters/sqlite tests/api tests/integration -q
532 passed
$ python -m mypy
Success: no issues found in 870 source files
$ PYTHONPATH=. python scratch/goal3-cycle13-probe2-boundary-before-after.py
收口前：with 退出被锁挡住？ False   isolation_level 赋值被锁挡住？ False
收口后：with 退出被锁挡住？ True    isolation_level 赋值被锁挡住？ True
$ sh scratch/run-m0-cycle12.sh   # 第 3 轮（第 1 轮红于文件规模硬上限，第 2 轮红于再导出）
PASS: profile=m0; 23 deterministic checks   全量 pytest 3654 passed / 10 skipped
$ python -m pytest tests/adapters/sqlite tests/tooling/test_python_source_limits.py -q
994 passed
```

## 影响报告

- **Domain/API/schema**：无变化（纯 adapter 内部口径）。
- **安全/凭据**：无变化。
- **兼容性/迁移风险**：`with conn:` 语义与真连接一致（成功提交、异常回滚、不吞异常），
  无调用方需要改动；`isolation_level`/`autocommit` 的**赋值**现在在锁内完成，读取行为不变。
  仓内当前没有这两类调用方，属**潜伏缺口**修复。
- **可观测性**：无变化。
- **下一项任务**：多语句原子事务语义（一个请求内多条语句一个事务）或锁粒度（每线程连接）；
  「按声明给 provider adapter 接线」仍待 escalation 决策。

## 已知风险

- **不是"全部收口"**：25 个公共名仍不收口（逐条理由见用例），其中 `interrupt` 是**故意**的
  ——它就是给别的线程用来中止正在跑的语句的。
- **名单会过期**：名单里的"本仓不用"随使用变化需重审；门禁只保证集合没变，不保证理由仍成立。
- **仍不做多语句原子事务**：`with conn:` 只保证事务**边界**动作在锁内。
- **`__setattr__` 的取舍**：每次属性赋值多一次名字判断，代价极小但确是实现上的"魔法"。

## 状态历史

- 2026-09-17 创建（IN_PROGRESS）：derive 先用探针 1 确认缺口真实——`with conn:` 与属性
  setter 在 C 层直接提交/回滚/发语句，**不经过** Python 层覆写；再用探针 2 拿到
  "持锁时是否阻塞"的**确定性**对照（收口前 False/False，收口后 True/True）。
  范围刻意收窄到"事务边界 + 边界枚举"，不把"多语句原子事务"塞进本轮。
- 2026-09-17 WP-A…C 完成：事务边界两个入口收口（`__enter__`/`__exit__`、
  `isolation_level`/`autocommit` 赋值经 `__setattr__` + `LOCKED_ATTRIBUTES`）；
  枚举门禁把 25 个不收口的公共名连理由一起钉住；七条用例全绿。
- 2026-09-17 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**，
  全量 pytest **3654 passed / 10 skipped**），ruff/format 干净、mypy **870 files clean**，
  记录落盘（RECHECK-076 PASS_WITH_WARNINGS + MEM-051 + GOAL cycle 13 记账 + ALL_PLAN）。
- 2026-09-17 门禁首轮红（**如实记录**）：m0 第 1 轮 `python/tests` 红于
  `tests/tooling/test_python_source_limits.py::test_python_source_size_limits[adapters\sqlite\db.py]`
  ——`assert 475 <= 450`。本轮给 `db.py` 加了 `__enter__`/`__exit__`/`__setattr__` 三段后
  顶穿了 450 行硬上限。**没有**放宽阈值（那属于 GOAL fix_policy 禁止的"改门禁使其通过"），
  而是把取行面（`MaterializedRows` + `SerializedCursor`）机械拆到
  `adapters/sqlite/cursor.py`，`db.py` 显式再导出。第 2 轮红于
  `python/typecheck`：`no_implicit_reexport` 下普通 `import` 不算再导出，
  改用仓内已有的 `X as X` 形式（`services/api/composition.py` 同形）。第 3 轮 **PASS 23/23**。
