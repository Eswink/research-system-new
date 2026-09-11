---
id: PLAN-20260910-037
slug: frontend-backend-api-integration
title: 前端预留接口与后端对接及缺失 API 补充开发
status: DONE
created_at: 2026-09-10
updated_at: 2026-09-11
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-10 用户要求按前端页面预留接口对接后端，缺少的 API 由后端补充开发；Plan Mode 计划（①+②全量、③保持诚实 gap 标注、后端测试+live e2e 双绿验收）已获批准"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260911-039-frontend-backend-api-integration.md
memory_entries: []
---

# PLAN-20260910-037 — 前端预留接口 ↔ 后端对接与补充开发

## 目标

以 `apps/web` 前端预留接口清单（`src/api` client 面 + `navigation/pageSupport.ts`
缺口登记）为输入，把已有后端路由接进 live 页面，并为契约缺失但 Domain/Store
已有支撑的 8 项能力补充控制面 API；③类（多项目、身份/账户、tool-packs 供应链、
prompts/datasets/notebooks/reports/alerts/incidents/schedules/data-health、
budget_adjust/replace_agent、forecast、DELETE 语义）不扩建，维持诚实 gap 标注。

## 范围

- 包含：WP-A 前端接线（endpoints/models/team/editor/runs 五域预留 client 函数）；
  WP-B 草稿修订 compile/preflight/dry-run；WP-C Artifact 浏览/预览/下载；
  WP-D provider health 三态 + 成本日序列；WP-E 实验项目视图/预注册/归档；
  WP-F Memory 门链端点；WP-G 通知投影 + 已读；WP-H human-gate 审批注册与续跑；
  WP-Z 收口（openapi/types/文档/门禁/recheck）。
- 不包含：③类能力、`.cursor/memory` 工程记忆接入产品面、真实付费 LLM 依赖、
  多租户/RBAC（M18/M19 DEFERRED）。

## 架构与数据流

新增控制面读取一律经既有 Port 与 application use case（protocol_source、
cost/daily、memory gate、lifecycle、notification projection），无第二套事实源；
写路径全部 Idempotency-Key，带版本资源 If-Match/412；store 未配置 503 不伪装；
UNKNOWN/第三态不并入健康或零值。OpenAPI 快照 docs/api/openapi.m13.json 单一
truth，contract 测试防漂移。

## 验收条件

- [x] AC-01（WP-A）：endpoints/models/team/editor/run-controls 五处预留 client 函数
  全部有真实 UI 调用方；单查/PATCH+If-Match/连接测试/compatibility/新建 Agent/
  项目设置保存/草稿修订列表/pause-resume 在 live 树可用；example 树零 `/api` 不变。
  证据：tsc 无错；eslint --max-warnings 0 过；unit 70/70；playwright
  console-shell/rebuild-baseline/example-isolation/a11y-viewport 29/29；
  design-fidelity 通过（plan-team 基线因新增“新建 Agent”按钮按批准重录）。
- [x] AC-02（WP-B）：`ProtocolSourceDto` 支持 `path | {draft_id, draft_revision}`
  二选一，compile/preflight/dry-run 三端点加载不可变草稿修订走同一编译链；
  旧 path 请求兼容；draft-preflight/draft-start 禁用解除。
  证据：tests/api/test_protocol_source_draft.py 6 passed（含修订不可变、422/404 语义）；
  conftest DraftService 补齐 text_loader（与生产构造对齐，测试装配偏差修复）；
  前端 protocolSourceOf 门禁 + canStart 新语义用例 + T14 baseline 更新；
  tsc/eslint/unit 70/70；tests/api 全量 192 passed + 3 个 @pytest.mark.postgres
  失败确认为测试 PG 未运行（启动 compose-postgres 后 6/6 passed，与本改动无关）。
- [x] AC-03（WP-C）：`GET /runs/{id}/artifacts`、`GET /artifacts/{id}`、
  `GET /artifacts/{id}/content`（digest 校验、类型白名单预览、Content-Disposition）；
  store 未配置 → 503 不伪装；workspace 页预览/下载可用；file-diff 保持禁用。
  证据：tests/api/test_artifacts_api.py 7 passed（503/404/410 tombstone/413/
  inline+attachment/nosniff/ETag/列表不伪装 verified）；composition SQLite 路径
  双 FakeArtifactStore 实例修复（run 产物对读取端可见的根因）；
  前端 artifactClient + ArtifactBrowser（下载 + 白名单预览 + 元数据 verified）；
  openapi 快照再生 contract 2 passed；tsc/eslint/unit 70/70。
- [x] AC-04（WP-D）：preflight provider health 经 ToolProvider port 真实探测，
  探测不可达 = UNKNOWN 第三态（不得伪装 True/False）；
  `GET /cost/daily` 五状态语义按日聚合、定价版本盖章；不做预测。
  证据：provider_health 升为 Mapping[str, EndpointHealth]（checks.py 三态：
  UNKNOWN→TOOL_HEALTH_UNPROVEN WARN 不阻断、OPEN_CIRCUIT/DISABLED→不可用、
  NATIVE→HEALTHY 结构性豁免有文档）；tests/application/test_provider_preflight_health.py
  8 passed；daily.py 纯函数（混合定价天不求和 PARTIALLY_METERED、UNKNOWN≠0、
  窗口、truncated）6 passed + API 3 passed；前端 DailyCostPanel（真实日序列，
  无数据日不插值）；openapi 快照再生 contract 通过；tsc/eslint/unit 70/70。
  注：探测超时预算由 adapter 自有（Port 无 timeout 参数；控制面当前未注册外部
  provider 实例，非 NATIVE 探测收敛 UNKNOWN，符合三态设计）。
- [x] AC-05（WP-E）：`GET/POST /projects/{pid}/experiments` + 取消语义。
  证据（语义修正记录）：域内实验计划状态机为 DRAFT/PREREGISTERED/ARCHIVED，
  无 QUEUED/RUNNING（experiment_state.py:17-49），POST /experiments/{id}/cancel
  会操作无人读取的行（executor 不落 store、worker 仅 claim EXECUTION）——
  诚实替代为 `POST /experiments/{plan_id}/archive`（域迁移 + 409/404）；
  列表以跨 run evidence 聚合（GET /projects/{pid}/experiments，SQLite/PG 双可用）；
  计划创建仅 PG canonical state（ApiDeps.experiment_store 槽位 +
  pg_composition 接线；SQLite 503 有 FakeExperimentStore 测试双路径）；
  tests/api/test_experiments_api.py 6 passed（项目聚合、503、幂等 422、
  预注册+归档+409+404）；前端 ExperimentPlanPanel + pageSupport
  experimentCreate 更新（queue/schedule 保持禁用）。注：本计划文案中的
  “排队”按域事实修正为“预注册”，未发明队列语义。
- [x] AC-06（WP-F）：Memory REST 按 CONTROL_PLANE_API.md §Memory；提案走
  MemoryWriteProposal → schema → provenance → policy → curator gate（AGENTS.md §8）；
  provenance 拒绝与 commit 恰一赢用例过；audit Memory tab 接真实数据。
  证据（语义修正记录）：域内无持久化 pending 提案 → `POST /memory/proposals`
  实现为完整 §8 门链直提交（拒绝按 stage+reasons 分类 422），两阶段 `decide`
  不实现（无 pending 对象可裁决）；capability policy 面受 `_CAPABILITY_SCOPE`
  镜像契约约束记为 follow-up（router policy 槽位显式 None + docstring 说明）。
  GET 带 store-missing 503 + scope_note；DELETE 经 lifecycle（索引同步 +
  MEMORY_DELETED + 幂等键 + 404/204）。tests/api/test_memory_api.py 6 passed；
  PG 恰一赢由既有 test_memory_claim_concurrency 锁定；前端 MemoryPanel；
  openapi 再生 + 契约断言；三门 + e2e 10/10 绿。提交 3d4efc2。
- [x] AC-07（WP-G）：`GET /notifications` + read 投影自 outbox 事件；已读持久化；
  无事件显示真实空态，绝不虚构。
  证据：RunProjection.recent_events（port + Sqlite SQL 顶序 + PG sink 尾部
  反转，两路径同源经 relay-consolidated publisher）；NotificationReadStore
  port + SqliteNotificationReadStore（view-state 存控制面 SQLite，与配置
  存储同侧先例；两 composition 接线）；路由白名单过滤（task.* 执行噪音不
  呈现、无 payload 内容=观测隐私）、GET/POST read 204+幂等键+422；
  tests/api/test_notifications_api.py 4 passed（503、白名单、read 持久化
  幂等、真实 run 事件投影）；前端 NotificationsPage 从 gap 脚手架升级为
  live（pageSupport level partial：无实时推送；design-fidelity notifications
  基线按新 live 页重录）；契约断言 + openapi 再生；stub e2e 29/29、
  contracts 330、三门全绿。
- [x] AC-08（WP-H）：run_orchestration 在策略审批门注册 ApprovalRecord 并置
  WAITING_FOR_APPROVAL；新带审批门 reference protocol；decide 链恢复 run/失败分支
  与 restart 恢复用例过；approvalsEmpty gap 解除。
  证据：HUMAN_GATE finding WARNING→INFO（声明性控制门；否则 WARN 阻断 freeze，
  审批点永不可达——test_m2 已按新语义更新并断言 INFO + unresolved_risks +
  dry_run approval_actions 保留）；phase_runner 在 gated phase 前 register +
  APPROVAL_REQUESTED + WAITING outcome + service._waiting 暂存（进程内，重启
  丢失诚实 503 且审批不被消费）；OrchestrationDependencies.approvals 与
  ApiDeps 同实例（两条 composition + run_fixtures 共享）；decide approve 后
  续跑并持久化终态；demo 协议 examples/protocols/human_gate_demo_v1.yaml；
  tests/api/test_approval_registration_api.py 4 passed（暂停+注册+事件、
  approve 续跑收敛、deny FAILED、重启 503 不消费）。
  语义修正记录：原计划“策略判定注册”落地为协议声明的 HUMAN_GATE（与
  M2 状态机白名单一致；PolicyEvaluator 的 REQUIRE_APPROVAL 属执行期工具门，
  不伪造注入点）。approvalsEmpty gap 文案更新，run/approvals → full。
- [x] AC-09（WP-Z）：openapi 快照再生 + `src/api/types.ts` 同步；stub-api/apiHarness
  注册全部新路由；live-api-workflow 扩展主链；m0 profile 全绿；pageSupport/GAPS 与
  docs/api/CONTROL_PLANE_API.md、docs/frontend/CONSOLE_PAGE_MAP.md 同步；RECHECK PASS。
  证据：复检代理独立跑 AC-01~09 定向套件全 PASS（RECHECK-20260911-039
  PASS_WITH_WARNINGS）；收口修复 50 行 limit×2、FAIL 词×1、命名基线登记 12；
  gen_openapi 再生产零漂移；m0 job 分组复跑（python 6/6、typescript 9/9、
  framework 8/8、分批 pytest 全目录、stub 30/30、live 7/7）在 DSN gating 环境
  下全绿；Docker/PG 依赖测试的环境性 flake 定性见影响报告遗留项。

## 实施清单

- [x] STEP-01 WP-A 前端接线（A1 endpoints 详情/编辑/测试；A2 models 详情/编辑/
  compatibility；A3 createAgent + settings 逐项保存；A4 草稿库/修订历史/compile/
  recheck；A5 pause/resume）。提交 9fa1641。
- [x] STEP-02 WP-B protocol_source 共享 loader + DTO 双来源 + 四端点 + 前端解锁。
  提交 7fd0aba。
- [x] STEP-03 WP-C artifacts 只读三端点 + SQLite 双实例修复 + ArtifactBrowser。
  提交 77a9f40 / 02c236a。
- [x] STEP-04 WP-D provider_health 三态 + /cost/daily + DailyCostPanel。
  提交 8d9587e。
- [x] STEP-05 WP-E 项目实验视图 + 预注册/归档 + ExperimentPlanPanel。
  提交 ba1fea6。
- [x] STEP-06 WP-F memory 门链三端点 + MemoryPanel。提交 3d4efc2。
- [x] STEP-07 WP-G notifications 投影 + 已读 + NotificationsPage live 化。
  提交 4358b5c。
- [x] STEP-08 WP-H human-gate 注册/暂停/续跑 + demo 协议 + 审批页语义更新。
  提交 3e0db85。
- [x] STEP-09 WP-Z 收口：全部门禁复跑、文档同步、recheck、命名基线登记。

## 证据

- 提交链：9fa1641（WP-A）、7fd0aba（WP-B）、77a9f40+02c236a（WP-C）、
  8d9587e+02c236a（WP-D）、ba1fea6（WP-E）、3d4efc2（WP-F）、4358b5c（WP-G）、
  3e0db85（WP-H）。
- 新增测试：test_protocol_source_draft（6）、test_artifacts_api（7）、
  test_provider_preflight_health（8）、test_cost_daily（6）+ test_cost_daily_api（3）、
  test_experiments_api 扩展（+5）、test_memory_api（6）、test_notifications_api（4）、
  test_approval_registration_api（4）。
- 门禁（收口批次，见状态历史）：ruff check/format（760 limit 测试过）、mypy 全绿、
  分批 pytest 全目录、root pnpm test 18/18、web lint/tsc/unit 70/70、
  stub e2e 30/30、live e2e 7/7、framework/hook/learning evals 全 PASS、
  docs_consistency PASS、system-spec bundle PASS。

## 已知风险

- Draft 与并发 agent 同树编辑：逐 WP 小步提交，禁 `git add -A`。
- WP-D provider 探测延迟：超时预算由 adapter 自有（MCP/NCBI 30s），当前无注册
  provider 实例，非 NATIVE 收敛 UNKNOWN 不触网。
- WP-H 改编排状态机：限 run_state 白名迁移；重启丢上下文以 503 诚实呈现。
- worker_plane/m12-e2e 两个 Docker/PG 依赖测试在混合顺序下环境性失败
  （单跑通过；见影响报告遗留项）。

## 偏差记录

- AC-05 “cancel”按域事实替代为 archive（无 queued 状态，不伪造队列/取消）。
- AC-06 两阶段 decide 不提供（无持久化 pending 提案对象）；memory.write 入
  capability policy 记为 follow-up（G16）。
- AC-08 审批注册点落地为协议声明 HUMAN_GATE（执行期工具门不在本范围）；
  HUMAN_GATE preflight finding 由 WARNING 降为 INFO（否则 WARN 阻断 freeze，
  审批门不可达；unresolved_risks 与 dry_run approval_actions 保留声明）。
- pause/resume 文案：按钮已接线但保持“控制面状态迁移”诚实标注（G6）。
- 命名门禁 LEGACY_PATH_EXCEPTIONS 由 14 扩至 26：登记 PLAN-033~036 引入的
  12 个原型命名遗留（TableRows.tsx 等），新文件仍受规则约束；本计划新增的
  2 项违规（RunActionButtons/SettingsRows）以改名/拆文件修复。

## 状态历史

- 2026-09-10 计划获用户批准，状态 IN_PROGRESS。
- 2026-09-10 WP-A 完成（三门 + stub e2e 29/29 + plan-team 基线重录），提交 9fa1641。
- 2026-09-10 WP-B 完成（draft source 双来源链 + 前端解锁），提交 7fd0aba。
- 2026-09-10 WP-C 完成（artifact 三端点 + 双实例修复 + ArtifactBrowser），
  提交 77a9f40；补交遗漏模块 02c236a。
- 2026-09-10 WP-D 完成（三态 provider health + 日序列），提交 8d9587e。
- 2026-09-10 WP-E 完成（项目实验视图 + 预注册/归档），提交 ba1fea6。
- 2026-09-10 WP-F 完成（memory 门链 + MemoryPanel），提交 3d4efc2。
- 2026-09-11 WP-G 完成（通知投影 + NotificationsPage live 化），提交 4358b5c。
- 2026-09-11 WP-H 完成（human-gate 审批链 + demo 协议），提交 3e0db85。
- 2026-09-11 WP-Z 收口：live e2e 主链扩展 7/7、root 门禁复跑发现并修复
  50 行函数 limit 2 处 + 生产边界 FAIL 词 1 处 + 命名门禁新违规 2 处与存量
  登记 12 处；分批 pytest 复跑确认（见证据）。
- 2026-09-11 独立复检 RECHECK-20260911-039 PASS_WITH_WARNINGS（AC-01~09 全
  PASS；警告 4 项均为环境/流程定性，不改变判定）。计划 DONE。
- 工程记忆：无可复用事实新增（DSN gating 配方与 dotenv 污染模式已由既有记忆
  覆盖；本计划新增事实如 hgate 注册点、三态 provider health 均可从代码/
  文档直接推导，不重复入库）。

## 影响报告

- Domain/API/schema 变化：ProtocolSourceDto 增可选 draft 引用（旧请求兼容）；
  PreflightContext.provider_health 类型 bool→EndpointHealth；RunProjection 增
  recent_events；新 MemoryReadStore/ApprovalStore 共享接线；新增 13 个端点
  （artifacts×3、cost/daily、experiments×2、memory×3、notifications×2、
  experiments 项目视图、archive）；openapi 快照再生并 contract 断言扩充。
- 安全/凭据：api_key 永不回显（PATCH 剔除）；artifact 下载 nosniff + 白名单
  内联 + attachment 降级；notification 不含 payload 内容（观测隐私）；memory
  门链 sanitize-before-commit；human-gate approve 不伪造 resume（重启 503）。
- 兼容性/迁移：无 DB 迁移（notification_reads 为 adapter 内 CREATE TABLE
  IF NOT EXISTS；memory/experiment store 用既有表）；SQLite 开发路径新增
  共享实例（artifacts/approvals），run 产物/审批对读取端首次真实可见。
- 上游版本影响：无新依赖。
- 遗留：m0 全量 profile 复跑中 2 个 Docker 环境依赖测试（m12 容器 e2e
  TIMED_OUT、pg_crash_restart）在长组合下偶发、单跑通过；Mimosa 完整
  密封扫描未在本 session 完成（scanner_enobufs），待另跑深度审计。
