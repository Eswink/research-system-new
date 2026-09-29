---
id: PLAN-20260929-251
slug: goal-026-ec04-compensation-and-transactional-outbox
title: GOAL-026 cycle 4（EC-04）：发件箱失败注入原子性 / 去重与投递边界 / 补偿可复核 / exactly-once 机械否认
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-026
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-026 的 **EC-04**（§7 义务「compensation for non-idempotent actions」与
    「transactional outbox」的对抗性自检，外加 ④ exactly-once 的**机械否认**）。
    授权沿用该 GOAL 的 `authorization.ref`：「**新增判据**（一律落 `tests/**`；落在既有
    `python/tests` 收集面内 ⇒ m0 条数仍 `23`）」+「**测试侧夹具 / 探针**」+
    「修**被新判据证明为真缺陷**的问题（**只允许收紧**）」+「文档同源更新」；
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；push 前
    `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**判据文件，**不修改**任何既有判据 / 夹具 / 门禁 / 阈值 /
    放行面（点名：`tests/adapters/sqlite/test_event_publisher.py`、
    `tests/adapters/sqlite/test_workflow_engine.py::TestOutbox`、
    `tests/postgres/test_outbox_pg.py`、`tests/application/run_orchestration/**`、
    `tests/architecture/python/test_reproducibility_wording.py`、`tests/egress_guard.py`）；
    **产品侧只动**被新判据证明为**不实**的**注释**（零行为变更，见 AC-5）——**不实现**任何新补偿、
    **不新增**事件消费者、**不改**发布器的自提交语义；**不改** `PRODUCT_ROOTS` / m0 条数 /
    作业结构；**零**新依赖；**全离线**；测试数据一律**合成值**；**不得**宣称项目安全
    （`R-M1` 未收口）；**不得**宣称 exactly-once（口径只能是 at-least-once + idempotency +
    deduplication）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **发件箱失败注入原子性**：在同一提交块内注入故障（SQLite **授权回调**拒写
      `outbox_events`，不拼 SQL 文本）⇒ 租约行与任务状态**一起回滚**（`(0, 0, 1)` +
      状态仍 `QUEUED`），且回滚后仍能重新 claim；**正控制**（无故障）⇒ 三件同时可见
      （`(1, 1, 1)` + `LEASED`）；故障真的触发过（`denied == 1`）。
    status: PASS
  - id: AC-2
    criterion: >-
      **两条写路径的原子性实测不同**：发布器 `publish` 自提交后，**同一调用块内的后续失败
      不会把它带走**（两个连接都看得见那一行）⇒ 按**实测**钉住（不按注释钉），
      并在记录里登记「引擎路径 all-or-nothing / 发布器路径自提交」这一不对称。
    status: PASS
  - id: AC-3
    criterion: >-
      **去重面 + 投递边界**：同一 `event_id` 重复发布 ⇒ 只留一行且保留**首次** envelope
      （防篡改）；`pending()` / `published` / `mark_published()` 逐条对账（标记一条恰好减少一条、
      总表不减、重复标记幂等、空集 no-op），受判面**下界** `≥ 2`；
      并**如实登记**仓内无应用级事件消费者（消费端去重未取证）。
    status: PASS
  - id: AC-4
    criterion: >-
      **补偿可复核 + 不可重复施加 + 缺失面登记**：`compensate_failed_resume` 把 `RUNNING`
      放回 `PAUSED` 并发**恰好一条**事件（payload 键集合与值可核对）；再补一次 ⇒
      `InvalidTransitionError` 且事件不增；`COMPENSATE` / `COMPENSATING` 在产品代码里
      **只出现在域定义文件**（扫描面下界 `≥400` 个 `.py`）、`compensation_actions`
      **产品零命中**且仍登记在文档 ⇒ 非幂等副作用的补偿**不实现**、只登记。
    status: PASS
  - id: AC-5
    criterion: >-
      **注释与实测不符 ⇒ 就地更正（仅注释、零行为变更）**：
      `adapters/sqlite/event_publisher.py` 旧注释称自提交的事件会与「同一调用块内的后续失败」
      一起回滚 —— 实测为**假**（见 AC-2）⇒ 改为写明实测语义与代价（要与业务写同生共死请用
      `OutboxWriter`），PA-1 F7 的耐久性理由与自提交行为**均不动**。
    status: PASS
  - id: AC-6
    criterion: >-
      **exactly-once 的机械否认**：在**有界且显式声明**的受判面上逐条分类
      `exactly[ _-]once`（`DENIAL` / `EXEMPT`（理由非空）/ `AFFIRMATIVE`），
      **0 条肯定式**、受判面下界（文件 `≥2500`、条数 `≥16`）；豁免表有上限且必须全部被用到；
      否定词窗**有界**（±6 行 + 段落截断）；否认词表有**正控制**；规则文本面（`goals/**`）
      单列且「引用即须写出禁令」；CJK lemma 在产品 + 文档面零命中且检测器在别处有正控制；
      可靠性文档里口径串在位。
    status: PASS
  - id: AC-7
    criterion: >-
      **按压两向 + 逐字节复原 + 四道门**：① 事件写进另一个事务（`persist_new_lease` 提前
      `conn.commit()`）⇒ 判红（`1 failed, 4 passed`）；② 关掉去重（`INSERT OR IGNORE` →
      `INSERT OR REPLACE`）⇒ 判红（`1 failed, 7 passed`）；两次复原后 raw `sha256` 均回到基线；
      留档二进制写盘（`CR` 计数 0）；`ruff format --check` / `ruff check` / `mypy` /
      规模门（1070 passed）全绿；定向套件 `2211 passed, 1 skipped`；既有判据逐字节未改；
      新判据**无 skip / xfail**。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-252-goal-026-ec04-compensation-and-transactional-outbox.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-171-outbox-has-two-write-paths-with-different-atomicity.md
---

# GOAL-026 cycle 4（EC-04）：补偿与事务性发件箱

## 目标

把 §7 的两项义务 —— 「**compensation for non-idempotent actions**」与
「**transactional outbox**」—— 从「**代码里有**」推进到「**有判据证明它真的成立**」，
并把「**不宣称 exactly-once**」这条口径做成**机械判据**（不是散文承诺）。
建档/探查发现的既有覆盖缺口（**实测**，不是推测）：

1. 既有两条发件箱原子性判据（`test_events_are_written_transactionally`、
   `test_outbox_atomic_with_task_transition`）**都走全绿路径** —— 没有人证明
   「失败时事件不在」；
2. 发布器的**自提交**语义与它自己的注释**相反**（见 AC-2 / AC-5）；
3. 「同 `event_id` 只留一条」只被断言行数，**没有**绑定「保留首次 envelope（防篡改）」；
   `pending()` / `mark_published()` 的**投递边界**没有任何对账判据；
4. 仓内**唯一可调用**的补偿（`compensate_failed_resume`）**没有直接判据**
   （既有资产只测 `publish_compensation_failure` 的 payload 形状）；
5. `exactly[ _-]once` 在仓内出现 20 次（实质面），**没有**任何机械判据过一遍。

## 验收条件

- [x] **AC-1 失败注入原子性**（授权回调拒写 outbox ⇒ 业务写一起回滚 + 正控制）。
- [x] **AC-2 两条写路径原子性不同**（实测钉住，2026-09-29 测得）。
- [x] **AC-3 去重面 + 投递边界**（保留首次 + 逐条对账 + 下界 + 无消费者登记）。
- [x] **AC-4 补偿可复核 + 不可重复施加 + 缺失面登记**。
- [x] **AC-5 注释与实测不符 ⇒ 仅注释就地更正**（零行为变更）。
- [x] **AC-6 exactly-once 的机械否认**（有界面 + 有界窗 + 豁免上限 + 正控制）。
- [x] **AC-7 按压两向 + 逐字节复原 + 四道门**。

## 实施清单

- [x] **WP-1**：新增 `tests/adapters/sqlite/test_outbox_atomicity.py`（5 例：AC-1 / AC-2 / AC-3）。
- [x] **WP-2**：新增 `tests/application/run_orchestration/test_compensation_boundary.py`（3 例：AC-4）。
- [x] **WP-3**：新增 `tests/architecture/python/test_delivery_semantics_wording.py`（6 例：AC-6）。
- [x] **WP-4**：事前探针 `scratch/goal026_ec04_probe.py`（Q1 / Q2：**先量再写判据**）。
- [x] **WP-5**：产品侧**仅注释**更正 `adapters/sqlite/event_publisher.py`（AC-5；零行为变更）。
- [x] **WP-6**：按压 A（提前提交）/ B（去重不再忽略）⇒ 判红；raw `sha256` 逐字节复原 ⇒ 复绿；
      留档 `scratch/goal026-ec04-press-matrix.log`（二进制写盘）。
- [x] **WP-7**：四道门 + 定向套件 + 规模自查；写 `RECHECK-20260929-252` + `MEM-20260929-171`；
      回写 GOAL-026 的 EC-04 状态与迭代日志；投影 `ALL_PLAN`。

## 证据

- **实跑**：`uv run --frozen --no-sync python -B -m pytest
  tests/adapters/sqlite/test_outbox_atomicity.py
  tests/application/run_orchestration/test_compensation_boundary.py
  tests/architecture/python/test_delivery_semantics_wording.py -q` ⇒ **14 passed**
  （加既有 `test_event_publisher.py` 三条 ⇒ **17 passed**）；
  定向套件（sqlite + application + architecture/python + 规模门）⇒ **2211 passed, 1 skipped**。
- **失败注入实测**：`fault=on ⇒ DatabaseError('not authorized') denied=1`、
  `counts = (0, 0, 1) status = ['QUEUED']`；`fault=off ⇒ (1, 1, 1) status = ['LEASED']`。
- **两条路径不对称（实测）**：自提交的事件在同一调用块后续失败后**仍可见**
  （同连接与第二连接都是 `(1, 0, 0)`）⇒ 产品注释就地更正（**仅注释**）。
- **exactly-once 分类实测**：扫描 **2605** 文件 / **20** 条出现 ⇒ `DENIAL 14 + EXEMPT 6 +
  AFFIRMATIVE 0`；豁免 6/8 全被用到；CJK 正控制 **12** 文件、产品 + 文档 **0** 命中；
  规则文本面 **27** 文件。
- **按压矩阵**（`scratch/goal026-ec04-press-matrix.log`，二进制写盘 / `CR` 计数 0 / 4088 字节）：
  **A** 提前提交 ⇒ `AssertionError: 事件写失败后不得留下租约行或事件行`（`1 failed, 4 passed`），
  复原回 `e5a21a8c…` ⇒ `5 passed`；**B** `INSERT OR REPLACE` ⇒
  `AssertionError: 已存在的事件不得被后来的内容顶掉`（`1 failed, 7 passed`），
  复原回 `82b98d90…` ⇒ `5 passed`。
- **四道门**：`ruff format --check` = `4 files already formatted`；`ruff check` =
  `All checks passed!`；`mypy` = `Success: no issues found in 4 source files`；
  规模门 = **1070 passed**。
- **首轮被抓到的本人错误**（如实记录，非产品缺陷）：2 处超长行 + 1 处需重排；
  判据首版的否定词窗只看上一行、词表缺「否认 / 不做 / BLOCKED」⇒ 13 条记录面出现被误判
  `AFFIRMATIVE`（**判据自己红**）⇒ 改为 ±6 行按段落截断 + 补词表 ⇒ 归零；**未**放宽硬断言。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | DONE | 三个新判据文件（14 例）落地；AC-1…AC-7 全部 PASS；`RECHECK-20260929-252` = `PASS_WITH_WARNINGS`（`W-1`…`W-7`）；沉淀 `MEM-20260929-171`。**产品净改动 = 一处注释更正**（零行为变更）。 |

## 影响报告

- **改动**：新增三个判据文件（14 例）；产品侧**仅注释**（`adapters/sqlite/event_publisher.py`
  的 PA-1 F7 说明段按实测改写，自提交行为**未动**）；记录面（PLAN / RECHECK / MEM / GOAL /
  ALL_PLAN / INDEX）。
- **lint / typecheck / test**：四道门全绿；定向套件 `2211 passed, 1 skipped`。
- **Domain / API / schema 变化**：**无**（未新增事件类型 / 字段 / 路由 / 表）。
- **安全 / 凭据变化**：**无**（合成值；零真实内容 / token）。
- **兼容性 / 迁移风险**：**无行为变更**。但**注释更正后与既有判据文件的 docstring 不一致**
  （见 `W-1`：本 GOAL 不改既有判据 ⇒ 只登记）。
- **上游版本影响**：**无**（零新依赖）。
- **未覆盖范围与残余**：无应用级事件消费者 ⇒ 消费端去重未取证（`R26-5`）；PG 侧仍只在全绿路径
  （`W-6`）；故障注入只压 claim 路径（`W-3`）；非幂等副作用的补偿未实现（`R26-4`）；
  exactly-once 面**只证到有界面**（**不宣称**全仓无肯定式，`W-4`）；`auth.py:22` 的肯定式短语
  未取证（`W-5`）；`R-M1` 未收口。
- **下一项任务**：GOAL-026 EC-05（自举收口：两树复检 + as-is m0 23/23 + 治理绿 + CI 台账到终态）。
