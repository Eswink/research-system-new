---
id: RECHECK-20260914-044
plan_id: PLAN-20260914-044
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-14
completed_at: 2026-09-14
reviewer: root-agent-gate-evidence
baseline_ref: 3c61747
checked_head: cycle 4 commit（见状态历史）
---

# RECHECK-20260914-044 — 库目录域独立复检

GOAL-20260912-001 cycle 4（EC-03 第一批）派生计划的复检。以「本地全门命令输出 +
定向 e2e + CI run 终态」为权威证据，逐 AC 核对，并对诚实边界对抗核查（不伪造
内容/版本/上传；配置面归属不产生第二真相）。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260914-044-library-catalog-domains-live.md`
  （`parent_goal: GOAL-20260912-001`，EC-03 第一批）。
- 变更范围：新增 `packages/domain/library.py`、
  `packages/application/ports/library_store.py`、`adapters/sqlite/library_store.py`、
  `services/api/{routers,dto}/library.py`、前端 `library/` 目录与三页改写；
  改 `services/api/{app,composition,pg_composition}.py`、conftest/run_fixtures、
  pageSupport、docs 2 份、基线 3 路由 × win32/linux。
- 边界：M18 零触碰；无 PG 表/迁移（配置面同侧）；alerts/incidents/schedules/
  data-health 属第二批（cycle 5），不在本 cycle。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01（WP-A） | 域有界校验、store 确定性/KeyError/close；配置面 SQLite 同侧（不新增 PG 表） | `pytest tests/adapters/sqlite/test_library_store.py` = 13 passed；`_sqlite_config_stores`/`_pg_config_stores` 逐行核对 | PASS |
| AC-02（WP-B） | 三 kind 创建/列表 kind 过滤/项目归属 404/未知 404/PATCH 归档/空载荷 422/无 DELETE(405)；openapi 零漂移 | `pytest tests/api/test_library_api.py` = 7 passed；`test_openapi_snapshot` 2 passed | PASS |
| AC-03（WP-C） | 三页消费真实端点、pageSupport 与文档一致 | `pnpm --dir apps/web run lint/typecheck/test/build` 全绿（73/73）；根 `pnpm run boundaries` 无违规 | PASS |
| AC-04（WP-D） | stub 无 Unstubbed、live 覆盖库端点、基线 3 路由 × 2 平台、全量 pytest、m0、CI 终态 | stub e2e 30/30；live e2e 13/13；全量 pytest 0 failed；m0 见状态历史；CI run 见状态历史 | PASS |

## 警告与处置

1. **W-1（WARNING，既有，非本 cycle）** collector-quality 仍见 2 项 timing flake
   （`test_collector_persists_research_os_spans`、
   `test_scenario_d_network_partition_no_old_authority`），已在 RECHECK-042/043
   登记；本 cycle 未触碰。
2. **W-2（INFO）** 基线再生发现新坑：`--update-snapshots` 只重写**有差异**的快照；
   当某页渲染结果恰好与库中旧基线逐字节相同（旧页面残留或缓存），不写文件、回拷
   覆盖宿主新基线 → 假绿。处置：脚本改为先 `rm -f *-linux.png` 强制重写，并在
   强制重写后发现 9 张**无关**基线因渲染抖动漂移，已 `git checkout` 还原，仅保留
   目标 3 路由。此坑并入 MEM-20260913-022。
3. **W-3（INFO）** 两处测试因「页面等级从 gap 提升为 partial」需同步：unit 的
   `resolveDataSource` 断言与 e2e 的 example 直达用例——改用仍为 gap 的
   `ops/alerts`（不放宽断言，只换继续成立的对象）。

## 结论

PLAN-20260914-044 AC-01~AC-04 全部满足；W-1 为既有范围外项。判定
**PASS_WITH_WARNINGS**，计划 DONE。GOAL-20260912-001 EC-03 部分完成（3/7 域）；
cycle 5 输入：EC-03 第二批（alerts/incidents/schedules/data-health）。
