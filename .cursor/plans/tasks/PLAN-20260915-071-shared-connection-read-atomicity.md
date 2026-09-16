---
id: PLAN-20260915-071
slug: shared-connection-read-atomicity
title: 共享 SQLite 连接的读原子性（execute 与取行之间不得被打断）
status: DONE
created_at: 2026-09-16
updated_at: 2026-09-16
parent_goal: GOAL-20260915-003
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-003 cycle 9 = cycle 8 明确移交的另一半（RECHECK-070 W-1：语句级串行治崩溃、不治'写后立读'）。授权来源：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-071-shared-connection-read-atomicity.md
memory_entries:
  - MEM-20260915-046-statement-serialization-is-not-read-atomicity
---

# PLAN-20260915-071 — 共享 SQLite 连接的读原子性（GOAL-003 cycle 9）

## 目标

cycle 8 把语句收进一把锁之后，还剩一类**静默错误**：同一条共享连接上，
`execute()` 拿到的游标在 `.fetchone()` 之前会被**另一个线程的语句/提交**打断，
读到的结果可能与库里的真相不符：

```text
修复前（12 线程 × 8 轮"写后立读"，共享连接，同一脚本同参数）：
    probe 8 次运行：miss 10 / 14 / 13 / 16 / 20 / 6 / 15 / 11（每轮 96 次读）
    miss 的分布：in_transaction=False、**紧接着的 list_definitions() 看得见那行**、
                 独立连接 100% 看得见 ⇒ 不是快照旧，是**这次 fetch 本身被打断**
    另一种更响的形态：`zip(_COLUMNS, row, strict=True)` 抛
                     `ValueError: zip() argument 2 is shorter than argument 1`
                     （fetch 拿回的行**列数不对**）
    live 控制面残留：12 线程 24 个 POST /ops/schedules ⇒ 1×404 unknown schedule
                     （POST 的响应要回读刚写的定义：`registry.create()` 之后
                       `_dto_of()` → `registry.get(name)`，读不到就 404）
```

## 口径

1. **锁的粒度错了位**：cycle 8 锁的是**一条语句**，而调用方要的是**一次读**
   （execute + 取行）。两者之间是一个窗口，别的线程可以在这个窗口里执行语句或提交。
2. **2×2 对照实验定因**（12 线程 × 8 轮，每格 3 轮 × 96 次读）：

   | 写守护 | 读守护 | miss（3 轮） |
   | --- | --- | --- |
   | 否 | 否 | 10 / 14 / 13 |
   | 是 | 否 | 1 / 4 / 0 |
   | 否 | **是** | **0 / 0 / 0** |
   | 是 | 是 | 0 / 0 / 0 |

   ⇒ **只护读就够**；护写只是减轻（读侧的窗口仍在）。
3. **修法在唯一咽喉处**：`SerializedConnection._statement` 在锁内 execute，
   若该语句**返回行**（`cursor.description is not None`）就**在锁内取尽**
   （`fetchall()`）并返回一个只读视图 `MaterializedRows`。
   store、路由、composition 一行不动。
4. **不夸大**：这**不是**"多语句事务原子"。跨语句的操作仍不原子；
   `conn.cursor()` 自建游标的路径也不覆盖（本仓无调用点）。见告警。
5. **不引入 rollback 语义**：本仓控制面**没有**任何 `rollback()` 调用点
   （已全仓 grep 确认），所以"别人的 rollback 吃掉我未提交的写"这一类不存在；
   本轮也不新增事务 API。

## 范围

- 修改：`adapters/sqlite/db.py`（`MaterializedRows` + `_statement` 锁内取尽 + `_forward` 拆分）。
- 新增：`tests/adapters/sqlite/test_shared_connection_read_atomicity.py`
  （写后立读钉子 + 语句级串行版反证 + 游标面对账 + 行形状对账）。
- **不改**：任何 store、任何路由、`connect()` 的对外契约（仍返回 `sqlite3.Connection`）。

## 验收条件

- [x] AC-01：共享连接上"写后立读"0 miss（12 线程 × 8 轮，连跑 ≥3 轮；修复前 10~20/96）。
- [x] AC-02：**反证**——同一负载打在"语句级串行、不取尽行"的连接上仍会 miss（>0），
      证明用例测的是这件事，而不是别的东西。
- [x] AC-03：游标面对账——`fetchone` / `fetchall` / `fetchmany` / 迭代 / `rowcount` /
      `description` / `close` 在物化视图与真游标上行为一致（仓库实际用到的面全覆盖）。
- [x] AC-04：行形状对账——并发下 `list_definitions()` 的逐行解码不再出现"行列数不对"。
- [x] AC-05：live 控制面 12 线程 24 个 `POST /ops/schedules` ⇒ **0×500 且 0×404**。
      **注记（收口时如实收窄）**：live **反证未复现**——把控制面切回语句级串行
      （启动标记确认补丁生效）后 216 个并发 POST 仍全 201 ⇒ live 只能作**补充观察**，
      本轮判据由 AC-01/AC-02 的单元级证据承担（见 RECHECK-071 W-1）。
- [x] AC-06：全量门禁（m0）+ 记录（RECHECK-071 + MEM-046 + GOAL 记账 + ALL_PLAN）。

## 实施清单

- [x] WP-A `MaterializedRows` + `_statement` 锁内取尽
- [x] WP-B 回归用例（钉子 + 反证 + 游标面/行形状对账）
- [x] WP-C live 对照实测（同脚本同参数，修复前 1×404 → 修复后 0×404）
- [x] WP-D 全量门禁 + 记录 + 收口提交 → CI

## 证据

```text
# 定因：2×2 对照（12 线程 × 8 轮，每格 3 轮 × 96 次读）——未修复时
(写F, 读F) 基线 : misses=[10, 14, 13]
(写T, 读F) 只护写: misses=[1, 4, 0]
(写F, 读T) 只护读: misses=[0, 0, 0]      ← 决定性的一侧是读
(写T, 读T) 全护  : misses=[0, 0, 0]
修复后同矩阵：四格全 [0, 0, 0]

$ python -m pytest tests/adapters/sqlite/test_shared_connection_read_atomicity.py -q
4 passed（连跑 6 次一致；含"语句级串行仍会读错"的反证）
$ python -m pytest tests/adapters/sqlite tests/api -q
476 passed in 51.70s
$ ruff check / format --check：干净；mypy：clean

# live 控制面（真实 SQLite + uvicorn）
12 线程 24 个 POST /ops/schedules  ⇒ 24×201 / 0×404 / 0×500
再加 12 线程 × 12 轮（144 个）      ⇒ 144×201
（反证：把控制面切回语句级串行后 216 个 POST 仍全 201 ⇒ live 压不出这个缺陷，见 RECHECK-071 W-1）
```

## 状态历史

- 2026-09-16 创建（IN_PROGRESS）：缺陷来自 cycle 8 收口时如实登记的 W-1。
  derive 阶段先把"到底是什么坏了"钉死，再动手：三次诊断脚本（scratch，不入库）
  依次排除了"读快照旧"（miss 时 `in_transaction=False`，同一连接上紧接着的
  `list_definitions()` 看得见）、排除了"写入丢了"（独立连接 100% 看得见），
  最后用 2×2 对照把因定在**读侧窗口**上。
- 2026-09-16 WP-A/B/C 完成：`MaterializedRows` + `_statement` 锁内取尽；
  回归用例四条（钉子/反证/游标面对账/行形状对账）连跑稳定；live 对照采集完成，
  并**如实标注** live 反证未复现（AC-05 收窄为补充观察）。
- 2026-09-16 DONE：全量门禁通过（m0 **PASS: profile=m0; 23 deterministic checks**，
  定向 **476 passed**，ruff/format/mypy 干净），记录落盘（RECHECK-071 PASS_WITH_WARNINGS +
  MEM-046 + GOAL cycle 9 记账 + ALL_PLAN），复检基线 `4bc2f89`。

## 影响报告

- **Domain/API/schema**：无变化（纯适配层）。
- **安全/凭据**：无。
- **兼容性/迁移风险**：`execute()` 的返回对象仍是"游标形状"，但**不再是 `sqlite3.Cursor`
  实例**（物化视图；`executemany`/`executescript` 仍返回真游标，因为它们不返回行）。
  仓库内没有 `isinstance(cursor, sqlite3.Cursor)`、也没有把游标存起来跨线程复用的调用点
  （已 grep 确认）。裸 `sqlite3.connect()` 的连接不受影响。
- **可观测性**：无新增遥测；"读回来的行对不上"这类现象不再出现本身即是信号。
- **下一项任务**：provider 凭据绑定（`ToolProviderSpec.endpoint_env` 已解析但从未被消费），
  或 `conn.cursor()` 自建游标路径的收口。

## 已知风险

- **仍不是多语句事务原子**：跨语句的操作（读-改-写）不在本轮范围；本仓控制面
  目前没有这种操作，若将来出现需要显式事务 API（`BEGIN IMMEDIATE` 作用域）。
- **锁内取尽的代价**：返回行很多的 SELECT 会在锁内取完，锁持有时间随之变长
  （cycle 8 的 W-2 已登记锁粒度问题）。本仓控制面的读都是小结果集；
  若将来出现大结果集扫描，应改为每线程连接而不是把锁调大。
- **`conn.cursor()` 未覆盖**：直接拿游标的调用方绕开物化（本仓无调用点）。
- **live 判据强度**：live 路径的语句密度压不出这一类缺陷（HTTP 开销稀释窗口），
  未来回归**必须**依赖单元级反证，不能拿 live "全绿"当结论。
