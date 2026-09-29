---
id: RECHECK-20260929-246
slug: goal-026-ec01-idempotency-and-dedup
title: GOAL-026 EC-01 复检：生产 SQLite 幂等 store 上的写面语义 + 域级行计数 + 跨会话（含重放来源的第二条路径）
plan_id: PLAN-20260929-245
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-29
completed_at: 2026-09-29
owners:
  - root-agent
---

# RECHECK-20260929-246 — GOAL-026 EC-01 复检

**复检口径**：不采信判据自己的叙述；本文件给出**可复核观察面**（命令 / 判词行 / raw `sha256`）。
关键结论用**第二条路径**复核（独立探针直读持久化行）。**未实跑的不记通过**。

## 检查结果

### 1. AC-1 生产 store 上的写面语义（实测）

- 交付：`tests/api/test_idempotency_sqlite_semantics.py`（**4 例**），全部打在
  **生产实现** `SqliteIdempotencyStore`（文件库）上——装配为
  `make_app_deps(db_path=<tmp>/control.db)` 后**替换** `deps.idempotency` 为
  `SqliteIdempotencyStore(db_path=<tmp>/idempotency.db)`；`IdempotencyMiddleware` 零改动。
- **重放三件套逐字符相等**：`assert _triple(replay) == _triple(first)`，其中
  `_triple = (status_code, json_body, ETag)`；实测首次 `201` 且 `ETag` 非空
  （`_assert_etag_is_real` 是**受判面非空**的守卫：若路由不再发 `ETag`，三件套比较会退化成
  两 `None` 相等 ⇒ 该守卫先红）。
- **同键异载荷** ⇒ `422` 且 `title == "Idempotency-Key Reused"`，并且**资源列表仍为 1 条**
  （冲突不得被当成重放）。
- **无键** ⇒ `422` 且 `title == "Idempotency-Key Required"`，并且**资源列表为空**（未落库）。
- 实跑：`uv run --frozen --no-sync python -B -m pytest tests/api/test_idempotency_sqlite_semantics.py -q`
  ⇒ **4 passed**。

### 2. AC-2 域级去重按 canonical 行计数（实测，含两向控制）

- 交付：`tests/e2e/test_idempotency_canonical_dedup.py`（**2 例**）。SQL **字面量直送**
  `execute`（不经过任何变量 / 拼接）。
- **恰为一行**：同 key 重放后 `tasks == 1` 且 `idempotency_records == 1`。
- **两向控制**：换一个 key ⇒ `tasks == 2` 且 `idempotency_records == 2`
  ⇒ 证明上面的计数判据**不是空转**（承 MEM-156 / MEM-159）。
- 实跑：`uv run … -m pytest tests/e2e/test_idempotency_canonical_dedup.py -q` ⇒ **2 passed**。

### 3. AC-3 跨会话重放（实测）

- 同一文件、**新的 store 实例 + 新的应用 + 新的客户端**（第一个 `TestClient` 已关闭）
  ⇒ 三件套再次相等，且 canonical 端点列表仍为 **1**。
- **注意边界**：这是**同进程内的顺序会话** + 文件库（等价于「重启后同节点重放」），
  **不是**跨进程 / 跨副本。

### 4. AC-4 按压 + 逐字节复原 + 四道门（实测）

**按压矩阵**（留档 `scratch/goal026-ec01-press-matrix.log`，**二进制写盘**，`CR` 计数 0，
`sha256 = c6df1097787195dd`）：

| 按压 | 位置 | 期望 | 实测红（原样） | 复原 |
| --- | --- | --- | --- | --- |
| **P1** 去重键 → 随机值 | `tests/e2e/test_idempotency_canonical_dedup.py::test_same_idempotency_key_leaves_exactly_one_business_fact` | 判红 | `assert 2 == 1`（`2 = _count_tasks(...)`）⇒ `1 failed, 1 passed` | `sha256` 回到 `fd0e1128…4f89`（`MATCHES_BASELINE True`）⇒ `2 passed` |
| **P2** 重放请求键 → 异键 | `tests/api/test_idempotency_sqlite_semantics.py::test_replay_on_production_store_returns_identical_triple` | 判红 | `At index 1 diff: {'id': '0afe552e-…'} != {'id': '68c79bf0-…'}`（**新资源出现** ⇒ 重放身份是**键绑定**的）⇒ `1 failed, 3 passed` | `sha256` 回到 `34c7bef2…147a`（`MATCHES_BASELINE True`）⇒ `6 passed` |

- **两向**：两次按压中**未受判的用例保持绿**（P1 时「异键应产生第二行」的控制例绿；
  P2 时冲突 / 无键 / 跨会话三例绿）⇒ 「不该红时不红」。
- **复原是逐字节的**：两文件的 raw `sha256` 均回到按压前的值（二进制读盘计算）。
- **四道门**：`ruff format --check` = `2 files already formatted`；`ruff check` =
  `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；
  规模门（`tests/tooling/test_python_source_limits.py` 对新增文件参数化）= **8 passed**。
- **既有判据逐字节未改**：`git status --porcelain -- tests/` 只有两个**新增**（`??`）文件；
  受影响套件合跑（既有 4 个文件 + 新 2 个）= **35 passed**。
- **无 skip / xfail**：两个新文件不含 `skip` / `xfail`。

### 5. 第二条路径：重放由**持久化行**提供（独立探针）

判据自身的断言不能自证「重放来自 store」。独立探针（留档
`scratch/goal026-ec01-recheck-provenance.log`，二进制写盘，`CR` 计数 0）做了**对抗性**动作：
首次 `POST`（`201`，`ETag = sha256:be7edda2…`）后，**直接改写持久化行**
（`status_code=299` / 正文 `{"tampered_by_recheck": true}` / `ETag = W/"recheck-tampered"`），
再重放 ⇒ **重放原样返回被篡改的三件套**（`299` + 篡改正文 + 篡改 `ETag`），
且 canonical 端点仍为 **1**。

**读法**：这证明「重放的同一结果」**不是路由被重新执行的幂等假象**，而是**读持久化行**；
它同时说明该 store 是**唯一的重放来源**（可被写坏 ⇒ 可被取证）。

## 结论

**EC-01 = PASS_WITH_WARNINGS**（`PLAN-20260929-245` 的 AC-1…AC-4 全部成立且有实跑证据）。
九项义务里的「**idempotency key**」与「**deduplication**」两半在**单节点、顺序会话**
的射程内**成立**；本 GOAL 的 `R26-6`（节点本地 store / check-then-act）**原样保留**。

**如实登记的警告（`W-1`…`W-6`）**：

- `W-1` 射程是**单节点**：HTTP 幂等 store 在 PG 模式下仍是 SQLite
  （`services/api/pg_composition.py:307-315`）⇒ **跨副本重放**未取证，**不得**读成跨副本保证；
- `W-2` **并发同键**未取证：`get → call_next → put` 是 check-then-act、无 in-flight 标记
  （`services/api/middleware.py:72-95`）；本判据不覆盖该窗口（改语义属**明令禁止**面）；
- `W-3` 两次按压都是**判据源码级**（改判据自己的键来源），**未**在产品侧
  （中间件）施加按压——产品语义本轮**不允许**被改；
- `W-4` 跨会话是**同进程顺序会话 + 文件库**，**不是**跨进程 / 跨副本；
- `W-5` 三件套里的 `ETag` 相等**依赖路由发 `ETag`**；`_assert_etag_is_real` 只在
  重放 / 跨会话两条用例上守住了「非空」，冲突 / 无键两例未断言 `ETag` 形态；
- `W-6` 域级计数只证**行数**，**未**断言是哪条分支去重（`deduped` 记录）；
- `R-M1` 未收口（Mimosa 钩子 `scanner_enobufs` 未得完整结论）⇒ **不得**据此宣称项目安全。

**未覆盖范围（承 GOAL-026，逐条不在本 PLAN 射程）**：读面未认证 / 多租户未做 /
BOLA·BFLA 未做 / 部署面未验证 / `R-M1` 未收口。
