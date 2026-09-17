---
id: PLAN-20260917-087
slug: failed-run-semantic-digest
title: 失败 run 与冻结事件的语义 digest：收敛分支与成功路径同判据，"从事件重放 run 行"补得回来
status: DONE
created_at: 2026-09-17
updated_at: 2026-09-17
parent_goal: GOAL-20260917-004
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260917-004 cycle 4 = EC-04（承接 GOAL-003「终止与收口 · BLOCKED 记录（2026-09-18）」后继入口第 5 项，基线告警 RECHECK-083 W-1+W-2）。授权来源：2026-09-17 用户 goal 模式指令（新建承接 GOAL-004 并自动化循环推进）。push-to-main-for-CI 授权沿用 GOAL-001 批准口径（只推 main、不 force、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260917-087-failed-run-semantic-digest.md
memory_entries:
  - MEM-20260917-062
---

# PLAN-20260917-087 — 失败 run 的冻结语义 digest（GOAL-004 cycle 4 = EC-04）

## 目标

今天**冻结的语义事实在失败收敛路径上被丢掉**：

- `RunManifest.semantic_digest()`（排除 `frozen_at`，供 resume 漂移校验）只在成功路径经
  `RunOutcome` 过 HTTP 边界（`services/api/run_execution.py:159`）；
- 执行期 `ValueError` 收敛 `FAILED` 的那一支只从 `manifest.frozen` 事件里捞回
  `digest` / `pricing_version` / `pricing_digest`（`run_execution.py:65-82`），
  **`manifest_semantic_digest` 不落行**；
- 而事件 payload 里压根没有这项（`packages/application/run_orchestration/eventing.py:57-64`），
  所以"从事件链重放 run 行"也补不回来。

后果是真实的：语义 digest 缺失 ⇒ `assert_semantics_frozen` 直接拒绝
（`packages/application/run_orchestration/convergence.py:29`，"frozen manifest lacks a
semantic digest"），也就是**一条 FAILED 的 run 连"重建 + 漂移校验"这条正路都走不进去**，
尽管它的 manifest 在失败之前就已经冻结、事件也已经落 outbox。

本轮把这份事实补齐到"与成功路径同一判据"：

1. `manifest.frozen` payload 增 `semantic_digest`（与 `digest` 同一时刻、同一 producer）；
2. 失败收敛分支读回四项引用，并用**成功路径同一个** `ResearchRun.with_manifest(...)`
   落行（不是手写字段赋值——判据一致要能一眼看出来）；
3. 读面 `RunDetailDto.manifest_semantic_digest` 如实暴露（None = 该 run 没有冻结语义
   或事件早于本轮）。

## 口径

1. **同判据 = 同一个 producer + 同一个域方法**：语义 digest 只由 `RunManifest.semantic_digest()`
   产生；落行只走 `with_manifest`。收敛分支不再自己拼字段。
2. **不猜、不回填**：payload 缺 `semantic_digest`（本轮之前的旧事件）⇒ 读回 None；
   没有冻结事件的 FAILED run（preflight 拒绝、未 pin）⇒ 四项引用全 None，与基线一致。
3. **读面诚实**：`manifest_semantic_digest` 非空只表示"这条 run 冻结过一次 manifest 且
   事件里有这项"，不保证重建成功（目录/契约漂移仍由 `assert_semantics_frozen` 拒绝）。
4. **判据只增强**：既有成功路径用例、失败收敛用例（`manifest_digest` 非空/为空两种）
   逐字不变；新增字段是可选字段，旧行读回 None。

## 验收条件

- [x] AC-01 **事件带语义 digest**：`frozen_payload(...)` 含 `semantic_digest`，取值等于
  同一 manifest 的 `RunManifest.semantic_digest()`；`EVENT_MODEL.md` 写明 payload 键。
- [x] AC-02 **失败收敛同判据**：执行期 `ValueError` 收敛的 run 行
  `manifest_semantic_digest` 非空、`!= manifest_digest`（排除冻结时刻）、非空字符串形如
  `sha256:`；落行走 `with_manifest`（成功路径同一方法）。同协议的成功 run 与失败 run
  在同一夹具里对同一判据都成立。
- [x] AC-03 **重放一致**：只凭事件链（`FrozenManifestRefs.from_payload`）重建出的四项冻结
  引用与 API 读面/ canonical 行完全相等；`GET /runs/{id}` 的 `manifest_semantic_digest`
  与事件 payload 相等。
- [x] AC-04 **诚实边界**：preflight 拒绝（无冻结事件）的 FAILED run 语义 digest 仍为 None；
   payload 缺键 ⇒ 读回 None（不猜测、不回填）。
- [x] AC-05 **反证 + 门禁与记录**：去掉事件 payload 键 / 去掉收敛分支语义 digest ⇒ 新用例
  失败（实跑记录）；定向套件 + m0 23 项 + OpenAPI/前端类型/夹具同源 + RECHECK-087 + MEM +
  GOAL-004/ALL_PLAN 记账。

## 实施清单

- [x] WP-A **事件**：`eventing.frozen_payload` 增 `semantic_digest` + `EVENT_MODEL.md`
  payload 键说明（+ 事件侧用例：payload 与 manifest 同源）。
- [x] WP-B **收敛与读面**：`FrozenManifestRefs`（值对象 + `from_payload` 单一映射）替换
  三元组；`run_from_execution` 的 `except ValueError:` 走 `with_manifest`；
  `RunDetailDto.manifest_semantic_digest` + `_detail_dto` + `docs/api/openapi.m13.json`
  重生成 + `apps/web/src/api/types.ts` / `apiFixtures.ts` + `CONTROL_PLANE_API.md`。
- [x] WP-C **用例与收口**：`tests/api/test_failed_run_semantic_digest_api.py`（失败行判据 /
  事件相等 / 重放一致 / 漂移守卫消费）+ 反证实跑 + 定向 + m0 → commit（每 WP 独立）→
  push → CI 六 job → RECHECK-087 + MEM + GOAL-004 回写。

## 证据

- 提交：`1831841`（WP-A 事件 payload + EVENT_MODEL）、`028abf3`（WP-B 收敛路径 + DTO/OpenAPI/
  web 类型与夹具 + CONTROL_PLANE_API）、`65d1ebd`（WP-C API 用例 7 条）、记录提交见 GOAL 迭代日志。
- 定向：`tests/api` **418 passed**；新增 API 用例 **7 passed**、新增应用用例 **3 passed**；
  `tests/domain tests/application tests/contracts tests/postgres tests/e2e` 复跑
  **1629 passed / 4 skipped**（197.19s）；web 门全绿（lint 0 error / typecheck / unit 76 /
  build / stub e2e 83 / live e2e 36）。
- 反证：去掉事件 payload 键 ⇒ **7 failed / 3 passed**；去掉收敛分支的语义 digest 参数 ⇒
  **3 failed / 4 passed**（失败文本 `frozen manifest lacks a semantic digest`）。
- m0：**PASS: profile=m0; 23 deterministic checks**（全量 pytest **3835 passed / 10 skipped**，
  477.88s）。两次红项均已定位并修复：首跑唯一红 = `framework/validate` 的"MEM-062 引用的
  RECHECK-087 尚未写入"（记录顺序）；复跑红 = `python/typecheck` 的类型收窄问题
  （把 `if self.digest is None:` 改写成属性谓词会丢 `str | None` 收窄）——恢复显式判空并
  删掉未被消费的 `frozen` 属性后复跑全绿，未改门禁、未加 ignore。
- 记录：RECHECK-20260917-087（PASS_WITH_WARNINGS，W-1…W-4）+ MEM-20260917-062。

## 状态历史

- 2026-09-17 建档（GOAL-20260917-004 cycle 4 = EC-04）；`status: IN_PROGRESS`。
- 2026-09-17 收口：WP-A/WP-B/WP-C 完成；反证双跑（去掉事件 payload 键 ⇒ 7 红；去掉收敛
  分支的语义 digest 参数 ⇒ 3 红，失败文本正是改动前的 `lacks a semantic digest`）；
  定向 + web 门全绿；m0 23/23（首跑唯一红项 = MEM 先于 RECHECK 写入的记录顺序问题）；
  RECHECK-087 **PASS_WITH_WARNINGS**；`status: DONE`。

## 影响报告

- **Domain**：无新实体/字段；`ResearchRun.with_manifest` 复用既有方法（行为不变）。
- **API/schema**：`RunDetailDto` 新增可空 `manifest_semantic_digest`（向后兼容）；
  `docs/api/openapi.m13.json` 重生成。
- **事件/契约**：`manifest.frozen` payload 增可选键 `semantic_digest`（schema_version 仍为
  "1"：新增可选键、旧读者忽略；旧事件读回 None）。
- **持久化**：run 行 `manifest_semantic_digest` 本就在 store 往返之内（SQLite/PG），本轮只是
  让失败收敛路径也写它；无迁移。
- **安全/凭据**：无新面（digest 是内容摘要，不含凭据）。
- **兼容性/迁移风险**：旧 run/旧事件读回 None（与今天一致）；不做回填。
- **上游版本影响**：无新依赖。
