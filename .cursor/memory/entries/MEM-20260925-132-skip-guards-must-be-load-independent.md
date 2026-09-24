---
id: MEM-20260925-132
title: "跳过守卫必须与收集面无关：子目录 conftest 里的 skip 在定向跑里等于不存在"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-164-local-gate-protocol-and-decision-briefing.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-165-local-gate-protocol-and-decision-briefing.md
supersedes: []
tags: [test-isolation, pytest, conftest, postgres, skip-guard, fail-closed]
---

## 做了什么

`postgres` / `distributed` 标记的**跳过**守卫原先只写在 `tests/postgres/conftest.py` 与
`tests/distributed/conftest.py` 的 `pytest_collection_modifyitems` 里。pytest 只在**真的收集到
该目录**时才加载它的 conftest ⇒ 一条 `postgres` 标记用例只要不在那些目录里（例如
`tests/api/test_worker_plane_composition.py`），**定向跑**时那道守卫根本不存在：

- 不跳过、也不快失败，而是**挂死**（PG 客户端在不可达 DSN 上等到超时）；
- 同一个文件只要**顺带**收集 `tests/postgres`，就变成 `16 passed, 93 skipped in 4.22s`。

修法（**判据一字不动**，只改守卫的**加载面**）：

- `tests/postgres_guard.py`：共享模块——`postgres_dsn()`（DSN 解析）、`postgres_available()`、
  `apply_reachability_skips(items)`（不可达 ⇒ 给标记用例加 skip，理由里带启动命令）、
  `RESEARCHOS_REQUIRE_POSTGRES=1` ⇒ **fail-closed**（`pytest.exit(..., returncode=1)` 并点名
  不可达，而不是静默跳过）。
- `tests/conftest.py`：既有 `pytest_collection_modifyitems` 的**第一步**就调用它 ⇒ 加载无关。
- 两个子目录 conftest 只保留各自的夹具（`_pg_schema_ready` / `clean_worker_plane` 等），
  删掉重复的收集钩子。
- 4 个模块原先 `from tests.postgres.conftest import _postgres_dsn`（借 conftest 的内部名）
  ⇒ 改为 `from tests.postgres_guard import postgres_dsn`。
- 新判据 `tests/architecture/python/test_postgres_skip_is_load_independent.py`：不可达 DSN
  （`postgresql://research_os@127.0.0.1:1/research_os`）下**定向跑**必须 exit 0 且出现
  `skipped`；同一命令加 `RESEARCHOS_REQUIRE_POSTGRES=1` 必须**非零退出**且判词含
  `not reachable` / `fail-closed`。

## 为什么这样做

- **挂死比失败更坏**：「跳过没生效」的下一步是「等到超时」，而超时会把本地判决变成
  「这轮到底红没红？」——本地判定确定性的直接漏洞。
- **守卫按目录生效是 pytest 的语义，不是配置错误**：所以修法必须是「让守卫与收集面无关」，
  而不是「让每个定向跑都记得带上 `tests/postgres`」——后者要求人记住，等于没有守卫。
- **fail-closed 不能省**：`RESEARCHOS_REQUIRE_POSTGRES=1` 是 CI / 本地「必须真跑 PG」的口径；
  若它在不可达时也只是 skip，那「跳过」与「通过」在判词上就分不开了。

## 怎么做与复现

- 复现（修前）：`RESEARCHOS_POSTGRES_DSN=postgresql://research_os@127.0.0.1:1/research_os
  pytest tests/api/test_worker_plane_composition.py -q` ⇒ 120s 内无输出、被杀（exit 143）。
- 复现（修后）：同一条命令 ⇒ 快速 `skipped`、exit 0。
- 判据：`pytest tests/architecture/python/test_postgres_skip_is_load_independent.py -q` ⇒
  `2 passed`。
- 回归面：`tests/postgres` + `tests/distributed` + 4 个 `postgres` 标记的 API 用例 ⇒ `143 passed`。
- 若将来新增「按标记跳过」的守卫，**必须**放在根 `tests/conftest.py`（或更早的 hook）里，
  并让判据用**子进程**跑一次「不收集该目录」的定向命令。

## 适用边界

- 本守卫只判**可达性**（能不能连上）；`RESEARCHOS_REQUIRE_POSTGRES` 与 DSN 的取值来自环境，
  因此 CI 需要 PG 的 job 必须显式带上该变量才有 fail-closed 保护。
- 跳过理由里带的是**启动命令**（compose 服务名），不是「省略了 PG 也能跑」的许可。
- 不改变任何被测语义：跳过面收紧 / fail-closed 都是**门禁面**行为，产品代码未动。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-164-local-gate-protocol-and-decision-briefing.md`（WP4）
- `.cursor/plans/rechecks/RECHECK-20260925-165-local-gate-protocol-and-decision-briefing.md`
- `docs/evaluation/CROSS_SUITE_ISOLATION_AUDIT.md` 第 4 节（R-4 的 A/B 成对复现）
- `docs/architecture/LOCAL_GATE_PROTOCOL.md`（支持 / 不支持的跑法）
