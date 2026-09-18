---
id: RECHECK-20260918-104
plan_id: PLAN-20260918-104
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-cycle5
baseline_ref: 0e14ce5
checked_head: WORKTREE
---

# RECHECK-20260918-104 — 批量读显式上限 + Fake 弱同判逐条点名（GOAL-006 cycle 5 = EC-05）

## 检查范围

EC-05 的两条要求逐条对表：

| EC 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| ① 批量读有**显式上限**、超限行为可判定 | port 常量 `MAX_DISPATCH_OWNERSHIP_BATCH` + `validate_dispatch_batch()`；三实现入口调用 | `tests/contracts/test_dispatch_ownership_contract.py::test_a_batch_over_the_limit_is_rejected`（按 `_FACTORIES` 参数化 ⇒ Fake/SQLite/PG 各跑一次） |
| ① 上限值写在**契约**（port docstring + `PORTS.md` / `CONTROL_PLANE_API.md`） | port 方法 docstring + `PORTS.md` + `CONTROL_PLANE_API.md` 三处同名同值 | `tests/contracts/test_dispatch_ownership_weak_equivalence.py::test_the_cap_value_lives_in_one_place_and_the_docs_name_it` |
| ① 超限**不静默截断**、且发生在读库之前 | 三实现把校验放在入口最早处（PG 在 `try` 之外） | SQLite：语句探针 `test_sqlite_an_over_limit_batch_sends_no_statement`；PG：`test_pg_an_over_limit_batch_is_rejected_as_a_caller_bug`（分类 + 已关闭引擎反证） |
| ① 谁负责分块（调用方），分块的诚实边界 | `services/api/run_dispatch_view.py::dispatch_ownership_read_many` 按上限切块并合并；docstring 写明"整批可能跨多个快照（块内仍是一个快照）" | `tests/api/test_run_dispatch_view_api.py` 四条单元级用例（块大小、覆盖、重复 id、半份答案不给） |
| ② Fake 的弱同判要么对齐、要么写成**显式边界** | 选择"显式边界"：Fake 无租约时钟 / 无 worker 注册表 / 无 `RETRY_SCHEDULED` 写路径 ⇒ 三轴不可同判 | port 模块 docstring 末节"弱同判边界"清单 |
| ② 同判用例只断言可同判部分，**不一致处逐条点名** | 8 条可同判轴 + 3 条不可同判轴逐条点名（每条带判据文件与用例名） | `test_dispatch_ownership_weak_equivalence.py` 七条机器判据（引用可解析、三实现参数化、双向一一对应、不可同判轴不许声称三实现） |

## 检查结果

### 上限（EC-05 ①）

- 值：`MAX_DISPATCH_OWNERSHIP_BATCH = 500`（`packages/application/ports/workflow_engine.py`），
  语义写在 port 常量注释与方法 docstring；`PORTS.md` / `CONTROL_PLANE_API.md` 各有一行
  同时点名常量与值。
- 判定口径：按**入参长度**（重复 id 不豁免）；超限 ⇒ `InvalidInputError`
  （`retryable=False`、`FailureCategory.VALIDATION_FAILURE`），**恰好等于上限合法**。
- 三实现共用 port 的**同一句**判据（`validate_dispatch_batch`），不是三份复制品。
- 分块在**调用方**（服务层）：块大小 == 上限，合并后覆盖所有请求 id；重复 id 先归一
  （不占额度）；任一块 `PortError` ⇒ 整批空 dict（不交半份答案，避免"没读的部分"被当成
  `NONE`）。
- **诚实边界**：页大于上限时整批可能跨多个快照。这是把"一次读 = 一条语句 = 一个快照"
  从"整页"缩到"块内"的**有意代价**，写在服务层 docstring + `PORTS.md` +
  `CONTROL_PLANE_API.md` 三处。

### 弱同判边界（EC-05 ②）

- 可同判轴（8 条，三实现同跑）：无派发方 / 未知 run / 持有者点名 / 完成后归还 / 按 run 隔离 /
  批量 == 逐 run / 空入参 / 超限拒绝。
- 不可同判轴（3 条，逐条点名真实现判据）：租约过期（SQLite 注入时钟 + PG parity）、
  LOST worker（同上）、重排计数与 `BOTH`（契约套件里的持久化实现用例 +
  `test_retry_schedule_contract.py` 的 Fake 边界用例）。
- 机器判据不只看"文本写了什么"，还看"文本有没有撒谎"：可同判轴引用的用例必须真的按
  `_FACTORIES` 参数化（含 Fake），且与套件里**所有**三实现用例双向一一对应；不可同判轴的
  引用不许是三实现参数化。`_FACTORIES` 本身必须来自注册表且注册表确实含 `FakeWorkflowEngine`。

## 反证与实测

| # | 扰动 | 预期 | 实测 |
| --- | --- | --- | --- |
| P1 | Fake 去掉 `validate_dispatch_batch` | 契约用例红 | `test_a_batch_over_the_limit_is_rejected[FakeWorkflowEngine]` `DID NOT RAISE InvalidInputError`（1 failed / 2 passed） |
| P2 | SQLite 把上限校验挪到取数**之后** | 语句探针红 | `assert 1 == 0`（"超限调用不许读库"）1 failed / 1 passed |
| P3 | PG 把上限校验挪进 `try`（`_ensure_open` 之后） | 分类断言红 | `TransientPortError: postgres transient failure: InvalidInputError(...)` —— 正是"调用方 bug 被误分类成瞬时失败" |
| P4 | 契约里把批量读用例改成 `_PERSISTENT_FACTORIES` | 判据红 | 2 failed（同判轴不在三实现上跑 + 双向对应缺一条） |
| P5 | 把某条 `[不同判]` 轴改成 `[同判]` | 判据红 | 3 failed（清单条数 / 三实现参数化 / 双向对应） |
| P6 | 把点名的用例名写错一个字母 | 判据红 | 3 failed（引用不可解析 + 双向对应） |
| P7 | 把 `PORTS.md` 里的值从 500 改成 400 | 判据红 | 1 failed（"必须写出上限的值 500"） |

P1–P7 全部**先红后复原**，复原后复跑：`tests/contracts` 5 个文件 + `tests/adapters/sqlite`
2 个文件 + `tests/api/test_run_dispatch_view_api.py` + `tests/postgres/test_dispatch_ownership_pg.py`
+ 体积门禁共 **1003 passed**（含 PG 容器实测）。

### 返工（记录诚实）

- 第一版把轴清单写在 `dispatch_ownership_many` 的**方法 docstring** 里 ⇒ 触发体积门禁
  （函数 63 行 > 50）；改为 port **模块 docstring** 末节，方法 docstring 只留指针与契约要点。
- 同时 `adapters/postgres/workflow_engine.py` 因新增说明超出 450 行硬上限（454），压缩说明为
  +1 行（顺带修正该 docstring 里"两条 SQL"的陈旧说法——EC-01 之后是一次调用**一条语句**）。
- 轴清单最初用 `path::test_name` 紧邻写法 ⇒ 两行超 100 列（ruff E501）；改成"文件 + 用例名"
  分开点名，判据改用 `可同判轴的判据文件：` 默认行 + 每条用例名解析（判别力由 P4–P6 反证）。
- 第一版判据要求每条轴都写全路径 ⇒ 清单冗长；改成默认文件行，未降低强度（P6 仍能红）。

## 告警（W）

- **W-1**（结构，非缺陷）：上限值 500 的"合理量级"没有独立依据——今天的列表路径未分页，
  真实页大小远小于 500，所以这个数只保证"放大可判定"，不证明"500 条一定安全"。
- **W-2**：分块后的**跨块快照**边界没有并发写反证用例（单块快照有 SQLite/PG 两条注入写反证）。
  今天的判据只到"块大小 + 合并结果覆盖"。
- **W-3**：`dispatch_ownership_read_many` 的分块用例是**单元级**（替身 spy），不经 HTTP：
  HTTP 侧只验证了"页在上限内一次读"。真跨块（501+ 行）的端到端路径没有实测。
- **W-4**：`adapters/postgres/workflow_engine.py` 恰好 450 行（硬上限），**零余量**；下一轮若再改
  该文件必须先让出行数或拆分。
- **W-5**：不可同判轴的"不可同判"由代码结构（Fake 无时钟/无注册表/无写路径）判定，不由
  行为差分实测——本轮没有构造"Fake 与 PG 在同一场景给出不同答案"的运行时反例。

## 结论

EC-05 的两条要求**均已交付并可复核**：上限是契约事实（值、判定口径、失败分类、分块责任都在
契约层），三实现同判且超限在读库之前可判定拒绝；Fake 的弱同判写成显式边界，可同判轴与
不可同判轴逐条点名，并由机器判据钉住"点名与实际断言一致"。七条扰动反证先红后复原。
结论：**PASS_WITH_WARNINGS**（W-1…W-5 见上；W-4 是下一轮改 PG 引擎前必须处理的结构约束）。

## 门禁

- 规模门禁（`tests/tooling/test_python_source_limits.py`）：940 passed（含 50 行函数 / 450 行文件）。
- 定向：`tests/contracts`（dispatch 三文件 + retry）· `tests/adapters/sqlite`（dispatch 两文件）
  · `tests/api/test_run_dispatch_view_api.py` · `tests/postgres/test_dispatch_ownership_pg.py`
  ⇒ 1003 passed（含 PG 容器实测）。
- `make validate-all`（m0 全量 23 项）：见 PLAN-20260918-104「证据」与 GOAL-006 迭代日志。
- ruff check / ruff format --check：变更文件全部通过；mypy：随 m0 `python/typecheck`。
