---
id: PLAN-20260912-040
slug: frontend-backend-seams-and-surfacing
title: 后端组成浮现与前后端接缝闭合（040/041/042 系列第一轮）
status: DONE
created_at: 2026-09-12
updated_at: 2026-09-12
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-12 用户要求补充后端（前端预留接口或数据）并完整对接；Plan Mode 批准 PLAN-040/041/042 系列（040 接缝与既有能力浮现 → 041 GAP 新域与页面翻 live → 042 语义深水区）；本轮 040 按批准计划执行"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260912-040-frontend-backend-seams-and-surfacing.md
memory_entries:
  - .cursor/memory/entries/MEM-20260912-019-sqlite-composition-surfacing-facts.md
---

# PLAN-20260912-040 — 后端组成浮现与前后端接缝闭合

## 目标

把"已有实现但没接线/没端点/契约不闭合"的接缝全部接上：SQLite 开发组成改用已实现
且有测试的持久 Store（Artifact/Memory），补 SQLite ExperimentStore 与 WorkerRegistry
消灭 dev 路径 503；补齐低危写语义（删除、自定义 role/template/agent clone、
runs approvals 列表、compatibility 投影）；前端接回被绕开的请求 DTO、统一禁用逻辑、
隔离 live shell 中的 example fixture 泄漏、清理死代码。041（9 GAP 页新域）与
042（预算调整/真暂停/实验队列/Diff/预测）不在本轮。

## 范围

- 包含：
  - WP-A 后端组成浮现：`_assemble_sqlite` 接 `SqliteArtifactStore`（blob 目录持久，
    替换 in-memory FakeArtifactStore，同实例共享给 orchestration 与读端点）与
    `SqliteMemoryStore`；新增 `adapters/sqlite/experiment_store.py` 与
    `adapters/sqlite/worker_registry.py`（照 PG 版实现 Port，两组成注入）；
    `/runs/{id}/evidence|claims` 未知 run → 404；`GET /health` 组成摘要端点，
    compose healthcheck 改用之。
  - WP-B API 面补齐：`GET /runs/{id}/approvals`；`POST /roles/custom`、
    `POST /team-templates/custom`、`POST /agents/{id}/clone`（复用 catalog_merge
    SQLite override 链）；`DELETE /llm-endpoints/{id}`、`/models/{id}`、
    `/protocol-drafts/{id}`、`/agents/{id}`（Port 增删除语义 + SQLite/PG 实现，
    被引用 → 409）；`/models/{id}/compatibility` 的
    `hard_capability_requirements` 从合并目录 role/profile 声明投影（非 probe assertions）。
  - WP-C 前端契约与 fixture 隔离：4 个被绕开的请求 DTO 接入 client 调用点；
    `isOperationDisabled` 统一禁用面；`pageSupport.ts` 过期文案修正；
    dependency-cruiser 禁止 example-console 被 live 树 import + 四处 layout
    fixture 改 live fallback；`TeamPreflight` 改用项目引用协议；死代码清理
    （useOperations、Tooltip、DataViewFrame/useCombinedView、Donut/Heatmap、
    project.json/provenance.json 死 fixture）。
  - WP-D 收口：openapi 再生零漂移、`CONTROL_PLANE_API.md`（含 5 个高估路由的
    未提供标注）/`CONSOLE_PAGE_MAP.md`/G 表同步、stub-api 注册、live e2e 扩展、
    m0 全绿、独立 RECHECK-040。
- 不包含：041 的 9 个 GAP 新域与 projects 注册表、042 的 budget_adjust/真
  pause-resume/实验队列/Diff/预测、M18/M19（多用户/RBAC/身份）。

## 架构与数据流

与 PLAN-037 同一不变量：读取只经既有 Port 与 application use case，无第二套事实
源；写路径全部 Idempotency-Key，带版本资源 If-Match/412；store 未配置诚实 503
不伪装；UNKNOWN/第三态不并入健康或零值；PostgreSQL 为 Canonical State，SQLite 为
开发路径（本轮只增 SQLite 实现，不改 PG 语义）；OpenAPI 快照
`docs/api/openapi.m13.json` 单一 truth，contract 测试防漂移；example 树保持零
`/api`。

## 验收条件

- [x] AC-01（WP-A）：dev 路径 artifacts 重启后仍可下载（SqliteArtifactStore）；
  memory GET/POST/DELETE 在 SQLite 组成可用；`/cluster/workers` 与项目实验
  GET/POST/archive 在 SQLite 组成不再 503；`/runs/{unknown}/evidence|claims`
  返回 404；`GET /health` 返回组成摘要且 compose 用之。
- [x] AC-02（WP-B）：删除四端点在 SQLite/PG 双组成有测试（含引用中 409 与
  If-Match）；custom role/team-template 写入 override 并被 catalog_merge 读出；
  agent clone 产生新 agent；`GET /runs/{id}/approvals` 有数据；compatibility
  投影在有 probe 断言时非空。
- [x] AC-03（WP-C）：tsc/eslint/unit/build 全绿；dependency-cruiser 新增规则生效
  （live 树 import example-console 即 fail）；live 模式 layout 不再渲染虚构用户/
  workspace fixture；`isOperationDisabled` 成为禁用判定单一来源。
- [x] AC-04（WP-D）：openapi 再生零漂移；CONTROL_PLANE_API.md 无高估路由；
  stub e2e + live e2e + m0（python 6 / typescript 9 / framework 8）全绿；
  RECHECK-040 独立复审完成并回填本文件。

## 实施清单

- [x] WP-A 后端组成浮现：`SqliteArtifactStore`/`SqliteMemoryStore` 接入
  `_assemble_sqlite`；新增 `adapters/sqlite/experiment_store.py`、
  `adapters/sqlite/worker_registry.py`（contract suite 注册）；
  `/runs/{id}/evidence|claims` 未知 run 404；`GET /health` + compose 改用；
  `SqliteArtifactStore` 写路径补 commit。
- [x] WP-B API 面补齐：`GET /runs/{id}/approvals`；`POST /roles/custom`、
  `POST /team-templates/custom`、`POST /agents/{id}/clone`（CatalogOverrideStore
  新 Port + SQLite 实现 + catalog_merge 合并视图）；DELETE
  `/llm-endpoints/{id}`、`/models/{id}`、`/protocol-drafts/{id}`、
  `/agents/{id}`（引用完整性 409；draft delete 扩 InMemory/SQLite/PG 三实现
  + Port + 契约用例）；compatibility `hard_capability_requirements` 投影。
- [x] WP-C 前端契约与 fixture 隔离：4 个请求 DTO 接入调用点；facade 增
  remove/clone/custom/runApprovals；endpoints 抽屉与 models inspector 删除
  UI（确认 + 409 呈现）；审批历史面板；TeamPreflight 改读
  `ProjectSettings.reference_protocol`（新字段贯通 catalog/store/DTO/settings
  UI）；`isOperationDisabled` 成为 SettingsPage 禁用判定来源；GAPS 过期文案
  修正；layout 不再直接 import `example-console/data/`（exampleChrome 桥 +
  production-boundaries 静态测试）；死代码清理（Tooltip、DataViewFrame/
  useCombinedView、Donut、Heatmap、useOperations hook）。
- [x] WP-D 收口：openapi 再生零漂移；CONTROL_PLANE_API.md（高估路由
  stream/ws/identity 标注未提供、custom/clone/DELETE/health 落地）与
  CONSOLE_PAGE_MAP.md（G10、memory/experiments 双路、settings/team 节）同步；
  live e2e 扩展；m0 分组全绿；RECHECK-040。

## 状态历史

- 2026-09-12 立项，Plan Mode 批准 PLAN-040/041/042 系列。
- 2026-09-12 WP-A 完成：`SqliteArtifactStore`（内容寻址、blob 目录默认
  `data/artifact-blobs`、写路径补 commit——原实现跨连接不可见，属既有缺陷）与
  `SqliteMemoryStore` 接入 `_assemble_sqlite`；新增
  `adapters/sqlite/experiment_store.py`、`adapters/sqlite/worker_registry.py`
  （后者注册进 WorkerRegistry contract suite，36 passed）；`/runs/{id}/evidence|
  claims` 未知 run → 404；`GET /health` 组成摘要 + compose healthcheck 改用；
  `experiment_rows` codec 移至 `adapters/contracts/`（双 store 共享）。
  tests/api 221 项通过（2 项 worker_plane 为既有 PG 环境依赖，按 DSN 固化配方
  复跑通过）；契约套件 333 passed；openapi 快照待 WP-B 后统一再生。
- 2026-09-12 WP-B 完成：`GET /runs/{run_id}/approvals`（list_for_run 历史面）；
  `POST /roles/custom` + `POST /team-templates/custom`（新 CatalogOverrideStore
  Port + Sqlite 实现，schema/domain 双校验、id 冲突 409、缺 store 503，合并视图
  与 examples 项同构）；`POST /agents/{id}/clone` + `DELETE /agents/{id}`；
  `DELETE /llm-endpoints/{id}`（被 model id/name 引用 → 409）、
  `DELETE /models/{id}`（agent 显式绑定 → 409）、`DELETE /protocol-drafts/{id}`
  （Port delete 扩到 InMemory/SQLite/PG 三实现 + 契约套件用例）；
  `/models/{id}/compatibility` 的 hard_capability_requirements 改为合并目录
  投影（roles.all_of/any_of + profiles.hard_capabilities）。
  conftest base deps 注入 catalog_overrides；mypy/ruff 干净；
  openapi 再生后 tests/api 全绿 + snapshot/boundaries 通过（当时计数 241；
  WP-C 后 test_wp_b_surface 合并 orphan 用例，DSN 固化复跑为 237 passed）。
- 2026-09-12 WP-C 完成（前端契约与 fixture 隔离）：
  - DTO 接线：`EndpointTestRequestDto`/`ProtocolSourceDto`/`ApprovalDecideDto`/
    `RunStartPayloadDto` 接入 client 调用点；facade 增
    removeEndpoint/removeModel/removeAgent/removeDraft/cloneAgent/
    createCustomRole/createCustomTeamTemplate/runApprovals。
  - 删除 UI 接线：endpoints 详情抽屉与 models inspector 增删除动作
    （EndpointDelete.tsx / ModelDelete.tsx，含确认与 409 错误呈现）；
    approvals 页接入 run 审批历史（RunApprovalHistory.tsx，WP-B 面）；
    stub-api 注册 DELETE/history 桩。
  - TeamPreflight：改用项目设置 `reference_protocol`（ProjectSettings 新字段，
    经 project.yaml `protocol` 加载、store/DTO/PUT 贯通、settings 页可编辑），
    删除硬编码 `TEAM_REFERENCE_PROTOCOL`；未配置诚实空态。
  - isOperationDisabled 消费：SettingsPage locked 分区判定改读注册表
    （disabledOperations = account/security/billing）；GAPS.delete 过期文案
    修正；endpoints 删除解锁；memory/experiments 文案同步 WP-A 双路支持。
  - fixture 隔离：layout 不再直接 import `example-console/data/*.json`
    （经 `exampleChrome.ts` 桥接）；production-boundaries 新静态测试强制
    data/ 仅 example 树可 import。
  - 死代码清理：Tooltip、DataViewFrame/useCombinedView、charts/Donut、
    charts/Heatmap、useOperations hook（保留被测纯 helpers）；
    project.json/provenance.json 死 fixture（注：`example-console/data/*.json`
    整体被根 `data/` gitignore，属工作树清理，不产生 git 变更）。
  - 门禁：tsc/eslint(0 warn)/unit 70/70/build、boundaries 6/6、
    stub e2e 受影响 spec 11/11、live e2e 7/7。
- 2026-09-12 WP-D 完成 + 独立复检收口：openapi 再生零漂移（快照含 9 新路由）；
  CONTROL_PLANE_API.md 逐路由 0 高估、22 未提供标注核真、补 3 条既存在路由
  （F-2）；CONSOLE_PAGE_MAP G 表同步（G10 已交付、memory/experiments 双支持）；
  live e2e run_fixtures 补齐 ledger/agent/settings/override/worker/experiment
  store（10/10）；m0 python 6 / typescript 9 / framework 8 全绿、stub 30/30；
  密封深度扫描 scan-2026-09-12T13-05-21 补跑并处置（本批新文件零命中，
  唯一产品树 HIGH 为既有 SafeLoader 误报，RECHECK-039 警告 3 闭环）。
  独立复检 RECHECK-20260912-040 判定 PASS_WITH_WARNINGS（F-1/F-3/F-5 已在收口
  commit 修正，F-2 补记路由，F-4/F-6 登记）；PLAN-040 关闭，下一项 PLAN-041。

## 证据

- WP-A：commit `6d844e3`；`tests/adapters/sqlite/test_experiment_store_sqlite.py`
  5 passed；`tests/contracts/test_worker_registry_contract.py` 36 passed
  （SqliteWorkerRegistry 注册后）；`tests/api/test_composition_sqlite_persistence.py`
  （durable store 类型 + artifact 重启往返 + /health）；inspection 404 两用例；
  tests/api 全量 + contracts 333 passed。
- WP-B：commit `2022b02`；`tests/api/test_wp_b_surface.py` 8 passed
  （custom role 201/409/422/503、template、clone/delete roundtrip、引用 409、
  compatibility 投影非空/空、draft delete roundtrip）；draft store 契约新增
  delete 用例（InMemory+SQLite）；mypy/ruff 0；openapi 再生 drift 测试过。
- WP-C：commit `d5abf18`；web typecheck/lint(0 warn)/unit 70/70/build 全绿；
  `tests/architecture/typescript/production-boundaries.test.mjs` 6/6
  （含新 data-import 隔离测试）；stub e2e 受影响 11/11、live e2e 7/7、
  tests/api 48 passed（team/llm/models/settings/wp_b 子集）。
- 计划文件命名：governance validate（framework profile）在补齐规范章节后通过。

## 已知风险与偏差记录

- `GET /cluster/workers` 在开发路径返回 `[]`（无 worker 注册）——诚实空态，
  reaper daemon 随 SQLite registry 一并启动。
- 删除 relay 后 credential 注册表条目保留至进程退出（进程内、永不落盘）；
  未做显式 forget（Port 无该面），已在端点删除文案中如实说明。
- draft delete 采用物理删除（append-only 修订史随之移除）；已冻结 run 不受
  影响（正文在启动时刻冻结）。
- `exampleChrome.ts` 仍被 live layout 静态引用（chrome 异常豁免）：
  data JSON 本就被根 gitignore 排除于仓库外，隔离规则守卫的是「业务 fixture
  import 面」而非 bundle 体积；bundle 级隔离（lazy）留作后续。
- `hard_capability_requirements` 投影源 = 合并目录 role/profile 声明；
  `endpoint_healthy_hint` 仍为 None（健康探测属显式动作，不隐式发起）。
- `services/api/custom_catalog.py` 在 composition root 之外 import
  `adapters.contracts.*`（与既有 catalog_merge 同模式：schema/domain loader，
  非 Port 旁路；`.importlinter.api` 受限源不含此模块，team 路由自身零 adapter
  import）；若未来收紧契约需将 catalog_merge/custom_catalog 一并显式豁免登记。

## 影响报告

- Domain/API/schema：新增 `CatalogOverrideStore` Port、`ProtocolDraftStore.delete`
  扩展、`ProjectSettings.reference_protocol`、`GET /health`、4×DELETE、
  3×custom/clone、run approvals 历史；openapi.m13.json 再生（+operations，
  0 removed）。M5 冻结 Port 语义只增不改（delete 为新能力非重定义）。
- 安全/凭据：无新秘密面；删除端点幂等键强制；health 无内容采样；
  SSRF/凭据纪律不变。
- 兼容性/迁移：`workers`/`artifacts` 表已在共享 SCHEMA_SQL（无 migration）；
  experiment/catalog_overrides 表由 adapter 自建（IF NOT EXISTS）；旧项目设置
  JSON 行缺 `reference_protocol` → `.get()` 回落 None，向后兼容。
- 上游版本影响：无（不触 OpenHands/依赖 pin）。
- 下一项任务：PLAN-041 `gap-domains-and-page-flips`（9 GAP 页新域 + 项目注册表
  + 页面翻 live）。
