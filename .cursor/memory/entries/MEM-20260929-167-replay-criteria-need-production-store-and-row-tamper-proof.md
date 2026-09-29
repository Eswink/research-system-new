---
id: MEM-20260929-167
title: "重放类判据必须打在**生产存储实现**上，并用「篡改持久化行」证明重放来源：否则『重放返回同一结果』可能只是路由被重新执行的幂等假象"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-245-goal-026-ec01-idempotency-and-dedup.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-246-goal-026-ec01-idempotency-and-dedup.md
supersedes: []
tags: [idempotency, replay, provenance, positive-control, sqlite-store, goal-026, ec-01]
---

## 做了什么

GOAL-026 EC-01 把 §7 义务「idempotency key + deduplication」的两个缺口补成判据：

1. `tests/api/test_idempotency_sqlite_semantics.py` —— 把「重放三件套（状态码 + 正文 + `ETag`）
   逐字符相等 / 同键异载荷 422 / 无键 422」打在**生产实现** `SqliteIdempotencyStore`（文件库）上，
   并覆盖**跨会话**（新 store 实例 + 新应用 + 新客户端、同一文件）；
2. `tests/e2e/test_idempotency_canonical_dedup.py` —— 域级去重按 **canonical 行计数**取证：
   同键 ⇒ `tasks` / `idempotency_records` **恰为 1**；**异键 ⇒ 2**（两向控制）。

## 为什么这样做（为什么值得记）

- **既有判据的缺口是「注入的存储」而不是「语义」**：`tests/api/test_idempotency_ifmatch.py`
  注入的是 `InMemoryIdempotencyStore` ⇒ **生产 store 的 replay / conflict / ETag 语义从未被证**。
  换成生产实现**一行装配**（`deps.idempotency = SqliteIdempotencyStore(db_path=…)`）即可覆盖，
  成本极低而覆盖面差别很大。
- **「重放返回同一结果」有两个可能来源**：① 读**持久化行**（真正的幂等重放）；
  ② 路由被**重新执行**且恰好幂等（假象）。断言相等**区分不了这两者**。
  用**篡改持久化行**（改状态码 + 正文 + `ETag`）再重放 ⇒ 观察重放是否原样跟随被篡改的值：
  跟随 ⇒ 来源是 store 行；不跟随 ⇒ 是重新执行。这是一条**对抗性正控制**，
  比「两次响应相等」强得多（后者在两条路径下都成立）。
- **计数类判据必须带两向控制**：只断言「同键 ⇒ 1 行」时，若去重把**所有**提交都吞掉，
  判据仍绿。加一条「**异键 ⇒ 2 行**」才让它可证伪（承 MEM-156 / MEM-159）。

## 怎么做与复现

1. **把判据打在生产实现上**：`deps = make_app_deps(db_path=<tmp>/control.db)` 之后
   `deps.idempotency = SqliteIdempotencyStore(db_path=<tmp>/idempotency.db)`；两个 `TestClient`
   （前一个关闭）即覆盖「重启后重放」。
2. **来源正控制**：首次请求后直读 `idempotency_responses` 行，`UPDATE` 成
   「异常状态码 + 篡改正文 + 篡改 `ETag`」，再重放 ⇒ 断言重放**原样等于被篡改的值**。
3. **计数两向**：同键 ⇒ `tasks == 1` 且 `idempotency_records == 1`；**异键 ⇒ == 2**。
4. **命令**：`uv run --frozen --no-sync python -B -m pytest
   tests/api/test_idempotency_sqlite_semantics.py tests/e2e/test_idempotency_canonical_dedup.py -q`
   （本轮 **6 passed**；受影响套件合跑 **35 passed**）。SQL 用**字面量直送** `execute`，
   不经过任何变量或拼接。

## 适用边界

- 射程是**单节点、顺序会话**：HTTP 幂等 store 在 PG 模式下仍是 SQLite
  （`services/api/pg_composition.py:307-315`）⇒ **跨副本重放**未取证；
- **并发同键**未取证：`get → call_next → put` 是 check-then-act、无 in-flight 标记
  （`services/api/middleware.py:72-95`）；改该语义属**明令禁止**面，只登记；
- 计数只证**行数**，不证**是哪条分支**去重；
- `ETag` 相等依赖路由发 `ETag` ⇒ 判据需带「非空」守卫，否则退化成两 `None` 相等的空真；
- 本轮两次按压都是**判据源码级**（产品中间件不允许改），**未**在产品侧按压。

## 来源

- `PLAN-20260929-245`（GOAL-026 EC-01）与 `RECHECK-20260929-246`；
- 实跑留档：`scratch/goal026-ec01-press-matrix.log`、
  `scratch/goal026-ec01-recheck-provenance.log`（均二进制写盘 / `CR` 计数 0）；
- 相关判据：`tests/api/test_idempotency_sqlite_semantics.py`、
  `tests/e2e/test_idempotency_canonical_dedup.py`。
