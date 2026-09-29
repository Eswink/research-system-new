---
id: PLAN-20260929-245
slug: goal-026-ec01-idempotency-and-dedup
title: GOAL-026 cycle 1（EC-01）：幂等与去重 —— 生产 SQLite store 上的重放/冲突/拒 + 域级计数 + 跨会话
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
    承 GOAL-20260929-026 的 **EC-01**（§7 义务「idempotency key + deduplication」的对抗性自检）。
    授权沿用该 GOAL 的 `authorization.ref`：范围 = 「**新增判据**（一律落 `tests/**`；落在既有
    `python/tests` 收集面内 ⇒ m0 条数仍 `23`）」+「**测试侧夹具 / 探针**」+「修**被新判据证明为真缺陷**
    的问题（**只允许收紧**）」+「文档同源更新」；push-to-main-for-CI 口径（**只推 main**、不 force、
    不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**判据文件，**不修改**任何既有判据 / 夹具 / 门禁 / 阈值 / 放行面
    （点名：`tests/api/test_idempotency_ifmatch.py`、`tests/api/test_api_restart_recovery.py`、
    `tests/e2e/test_idempotency.py`、`tests/contracts/test_m13_r1_store_contracts.py`、
    `tests/tooling/test_console_stub_idempotency_parity.py`、`services/api/middleware.py`、
    `services/api/idempotency.py`、`adapters/sqlite/idempotency_store.py`、
    `tests/tooling/test_tooling_scripts_meet_product_gates.py`、`tests/egress_guard.py`）；
    **改 `IdempotencyMiddleware` / `Idempotency-Key` 语义** = 立即 BLOCKED
    （承 GOAL-019 判词：该面**只加判据**）；**不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构；
    **零**新依赖；**全离线**（无真实出网）；测试数据一律**合成值**；
    **不得**宣称项目安全（`R-M1` 未收口）；**不得**宣称 exactly-once。
exit_criteria:
  - id: AC-1
    criterion: >-
      **生产 store 上的写面语义（承 EC-01 ①②③）**：在**生产实现** `SqliteIdempotencyStore`
      （文件库，非 `InMemoryIdempotencyStore`）上，经 HTTP 中间件实测：① **重放**返回**同一结果**
      —— 状态码 + 正文 + `ETag` **三件套逐字符相等**；② **同键不同载荷 ⇒ 422
      `Idempotency-Key Reused`**；③ **无键 ⇒ 422 `Idempotency-Key Required`**。
    status: PASS
  - id: AC-2
    criterion: >-
      **域级去重按存储行计数（承 EC-01 ④）**：同一 `idempotency_key` 在 canonical 层**不产生第二条
      业务事实** —— `tasks` 与 `idempotency_records` 行数重放前后不变且恰为 **1**；
      **两向控制**：异键 ⇒ 行数 **2**（承 MEM-156 / MEM-159）。
    status: PASS
  - id: AC-3
    criterion: >-
      **跨会话重放（承 EC-01 ⑤）**：同一 store 文件、**新的 store 实例 + 新的应用 + 新的客户端**
      ⇒ 重放结论与首次**一致**（三件套再次相等），且**仍不**新增业务事实。
    status: PASS
  - id: AC-4
    criterion: >-
      **按压 + 逐字节复原 + 四道门（承 MEM-152 / MEM-159）**：① 两次按压（去重键 → 随机值 /
      重放键 → 异键）各自**判红**，复原 ⇒ 复绿；② 按压 / 复原走 raw `sha256` + **二进制读写**；
      ③ 四道门全绿；④ 既有幂等判据**逐字节未改**且合跑全绿；新判据**无 skip / xfail**。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-246-goal-026-ec01-idempotency-and-dedup.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-167-replay-criteria-need-production-store-and-row-tamper-proof.md
---

# GOAL-026 cycle 1（EC-01）：幂等与去重

## 目标

把 §7 义务「**idempotency key + deduplication**」从「**代码里有**」推进到
「**有判据证明它真的成立**」：在**生产实现**（`SqliteIdempotencyStore` + HTTP 中间件）
与 **canonical 层**（`tasks` / `idempotency_records` 行数）两个面上取证，
并补上既有判据的**三处缺口**：

1. 既有 HTTP 幂等判据（`tests/api/test_idempotency_ifmatch.py`）注入的是
   `InMemoryIdempotencyStore` ⇒ **生产 store 的 replay / conflict / 拒绝语义无人证**；
2. 跨会话重放判据（`tests/api/test_api_restart_recovery.py:152-169`）只断言 id 与列表长度
   ⇒ **状态码 / 正文 / `ETag` 三件套跨会话相等无人证**；
3. canonical 去重只有「不新增」的断言 ⇒ **「恰为一行」与「异键应产生第二行」两向无人证**。

**本 PLAN 只新增判据文件；`IdempotencyMiddleware` / `Idempotency-Key` 语义零改动**
（承 GOAL-019 判词：该面只加判据）。

## 验收条件

- [x] **AC-1 生产 store 上的写面语义**：重放三件套（状态码 + 正文 + `ETag`）逐字符相等；
      同键异载荷 ⇒ 422 `Idempotency-Key Reused`；无键 ⇒ 422 `Idempotency-Key Required`
      —— 三条**全部**打在 `SqliteIdempotencyStore`（文件库）上。
- [x] **AC-2 域级去重按行计数**：同键重放前后 `tasks` / `idempotency_records` 行数不变且 **恰为 1**；
      **异键** ⇒ 行数 **2**（两向控制）。
- [x] **AC-3 跨会话重放**：新 store 实例 + 新应用 + 新客户端（同一文件）⇒ 三件套再次相等
      且 canonical 端点列表仍为 1。
- [x] **AC-4 按压 / 复原 / 四道门**：按压 ⇒ 判红；复原 ⇒ 复绿；raw `sha256` 逐字节复原；
      四道门绿；既有判据逐字节未改；无 skip / xfail。

## 实施清单

- [x] **WP-1**：写 `.cursor/plans/tasks/PLAN-20260929-245-*.md` + `ALL_PLAN` 投影行（同一提交）。
- [x] **WP-2**：新增 `tests/api/test_idempotency_sqlite_semantics.py`（**4 例**，AC-1 + AC-3）。
- [x] **WP-3**：新增 `tests/e2e/test_idempotency_canonical_dedup.py`（**2 例**，AC-2）。
- [x] **WP-4**：按压 P1 / P2 ⇒ 判红取证；逐字节复原（raw `sha256`）⇒ 复绿；留档二进制写盘。
- [x] **WP-5**：四道门 + 定向套件 + 规模自查；写 `RECHECK-20260929-246` + `MEM-20260929-167`；
      回写 GOAL-026 的 EC-01 状态与迭代日志。

## 证据

- **AC-1 / AC-3 实跑**：`uv run --frozen --no-sync python -B -m pytest
  tests/api/test_idempotency_sqlite_semantics.py -q` ⇒ **4 passed**（生产 store 装配 =
  `make_app_deps(db_path=<tmp>/control.db)` 后把 `deps.idempotency` 换成
  `SqliteIdempotencyStore(db_path=<tmp>/idempotency.db)`）；首次 `201` 且 `ETag` 非空。
- **AC-2 实跑**：`… -m pytest tests/e2e/test_idempotency_canonical_dedup.py -q` ⇒ **2 passed**
  （同键 `tasks == 1` / `idempotency_records == 1`；异键 `== 2`）。SQL 字面量直送 `execute`。
- **按压矩阵**（`scratch/goal026-ec01-press-matrix.log`，二进制写盘 / `CR` 计数 0 /
  `sha256 = c6df1097787195dd…`）：**P1** 去重键 → 随机值 ⇒
  `assert 2 == 1 (2 = _count_tasks(...))`（`1 failed, 1 passed`）；**P2** 重放键 → 异键 ⇒
  `At index 1 diff: {'id': '0afe552e-…'} != {'id': '68c79bf0-…'}`（`1 failed, 3 passed`）。
  复原后 raw `sha256`：`fd0e1128…4f89` / `34c7bef2…147a`（两者 `MATCHES_BASELINE True`）⇒ **6 passed**。
- **第二条路径（重放来源）**：篡改持久化行（`299` + 篡改正文 + 篡改 `ETag`）后重放 ⇒
  **原样跟随**，canonical 端点仍为 1 ⇒ 重放来源是**持久化行**，不是路由被重新执行的假象
  （`scratch/goal026-ec01-recheck-provenance.log`，二进制写盘 / `CR` 计数 0）。
- **四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；
  `mypy` = `Success: no issues found in 2 source files`；规模门参数化 = **8 passed**。
- **既有判据未改**：`git status --porcelain -- tests/` 只有两个 `??` 新增文件；
  受影响套件合跑（既有 4 + 新 2）= **35 passed**，`egress guard: blocked 0`。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | IN_PROGRESS | 建档：承 GOAL-026 EC-01，四 AC 全部未开始；实施清单 WP-1…WP-5。 |
| 2026-09-29 | DONE | 四 AC 全部 PASS（实跑见「证据」）；`RECHECK-20260929-246` = `PASS_WITH_WARNINGS`（`W-1`…`W-6`）；沉淀 `MEM-20260929-167`。**零产品代码改动**（两个新增判据文件 + 记录面）。 |

## 影响报告

- **改动**：新增 `tests/api/test_idempotency_sqlite_semantics.py`（4 例）与
  `tests/e2e/test_idempotency_canonical_dedup.py`（2 例）；记录面（PLAN / RECHECK / MEM / GOAL / ALL_PLAN）。
- **lint / typecheck / test**：四道门全绿（见「证据」）；受影响套件 **35 passed**。
- **Domain / API / schema 变化**：**无**（无产品代码改动；OpenAPI 快照与 web 类型零漂移）。
- **安全 / 凭据变化**：**无**（测试数据全为合成值；未引入任何真实内容 / token）。
- **兼容性 / 迁移风险**：**无**；`IdempotencyMiddleware` / `Idempotency-Key` 语义**零改动**。
- **上游版本影响**：**无**（零新依赖）。
- **未覆盖范围与残余**：见 `RECHECK-246` 的 `W-1`…`W-6`（单节点射程 / 并发同键未取证 /
  按压为判据级 / 跨会话非跨进程 / `ETag` 守卫范围 / 计数不证分支）与 `R-M1` 未收口。
- **下一项任务**：GOAL-026 EC-02（租约 / 心跳 / 重试分类 / 退避）。
