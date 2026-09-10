---
id: PLAN-20260910-037
slug: frontend-backend-api-integration
title: 前端预留接口与后端对接及缺失 API 补充开发
status: IN_PROGRESS
created_at: 2026-09-10
updated_at: 2026-09-10
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-10 用户要求按前端页面预留接口对接后端，缺少的 API 由后端补充开发；Plan Mode 计划（①+②全量、③保持诚实 gap 标注、后端测试+live e2e 双绿验收）已获批准"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260910-037 — 前端预留接口 ↔ 后端对接与补充开发

## 背景与范围

`apps/web` 双轨架构（live/example）下，`src/api` 已预留 60+ 接口，
`navigation/pageSupport.ts` 是前端缺口登记表。与 `services/api`（FastAPI 控制面）
对照后分三类：

- **① 前端预留、后端路由已存在**（约 15 个 client 函数无 UI 调用方）→ 前端接线。
- **② 后端契约缺失但 Domain/Store 已有支撑**（8 项）→ 后端补充开发 + 前端接线。
- **③ 治理上推迟/无 Domain 支撑**：多项目、账户/billing/身份（M18/M19 DEFERRED）、
  tool-packs install/approve/revoke、prompts/datasets/notebooks/reports/alerts/
  incidents/schedules/data-health、budget_adjust/replace_agent（恒 501）、forecast、
  run-diff、DELETE 语义。**本计划不做**，相关页面维持现有诚实 gap 标注与禁用按钮。

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
  探测不可达 = UNKNOWN 第三态（不得伪装 True/False），超时预算 ≤2s/provider 并行；
  `GET /cost/daily` 五状态语义按日聚合、定价版本盖章；不做预测。
  证据：provider_health 升为 Mapping[str, EndpointHealth]（checks.py 三态：
  UNKNOWN→TOOL_HEALTH_UNPROVEN WARN 不阻断、OPEN_CIRCUIT/DISABLED→不可用、
  NATIVE→HEALTHY 结构性豁免有文档）；tests/application/test_provider_preflight_health.py
  8 passed；daily.py 纯函数（混合定价天不求和 PARTIALLY_METERED、UNKNOWN≠0、
  窗口、truncated）6 passed + API 3 passed；前端 DailyCostPanel（真实日序列，
  无数据日不插值）；openapi 再生 + contract 路径断言过；
  ruff/mypy/tsc/eslint/unit 70/70/stub-e2e 11/11 全绿。
  注：探测超时预算由 adapter 自有（Port 无 timeout 参数；控制面当前未注册外部
  provider 实例，非 NATIVE 探测收敛 UNKNOWN，符合三态设计）。
- [x] AC-05（WP-E）：`GET/POST /projects/{pid}/experiments` + cancel；ExperimentStore
  支撑；SQLite 无 store → 503；schedule 保持禁用。
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
- [ ] AC-06（WP-F）：Memory REST 四端点按 CONTROL_PLANE_API.md §Memory；提案走
  MemoryWriteProposal → schema → provenance → policy → curator gate（AGENTS.md §8）；
  provenance 拒绝与 commit 恰一赢用例过；audit Memory tab 接真实数据。
- [ ] AC-07（WP-G）：`GET /notifications` + read 投影自 outbox 事件；已读持久化；
  无事件显示真实空态，绝不虚构。
- [ ] AC-08（WP-H）：run_orchestration 在策略审批门注册 ApprovalRecord 并置
  WAITING_FOR_APPROVAL；新带审批门 reference protocol；decide 链恢复 run/失败分支
  与 restart 恢复用例过；approvalsEmpty gap 解除。
- [ ] AC-09（WP-Z）：openapi 快照再生 + `src/api/types.ts` 同步；stub-api/apiHarness
  注册全部新路由；live-api-workflow 扩展主链；m0 profile 全绿；pageSupport/GAPS 与
  docs/api/CONTROL_PLANE_API.md 同步更新；RECHECK PASS。

## 工作包

- WP-A 前端接线（零后端改动）：A1 endpoints 详情/编辑/测试；A2 models 详情/编辑/
  compatibility；A3 createAgent + saveProjectSettings；A4 draftApi.list/
  listRevisions/getRevision + protocols/validate + 单步 preflight；A5 pause/resume。
- WP-B 草稿修订 compile/preflight/dry-run（后端 + 前端解锁）。
- WP-C Artifact 浏览/预览/下载（控制面新只读端点 + workspace UI）。
- WP-D provider health 真实探测 + 成本日序列。
- WP-E 实验列表 + 创建/排队。
- WP-F Memory REST。
- WP-G 通知投影。
- WP-H 审批注册点。
- WP-Z 横切收口：openapi 再生、types 同步、e2e 桩注册、全量质量门、文档、recheck。

顺序：A → B → C/D → E/F → G → H → Z。

## 风险

- 并发 agent 同树编辑：逐 WP 小步提交，禁 `git add -A`。
- provider 探测延迟：超时预算 + UNKNOWN 降级。
- WP-H 触碰编排状态机：先加契约测试再改实现，限 `run_state` 迁移白名。
- 兼容：`ProtocolSourceDto` 仅加可选字段，旧 `protocol_path` 语义不变。

## 进度记录

- 2026-09-10 计划获用户批准，状态 IN_PROGRESS。
