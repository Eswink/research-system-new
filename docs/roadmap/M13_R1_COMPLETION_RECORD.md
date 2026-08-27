# M13-R1 — Research Console Remediation Record

- 日期：2026-08-27
- 性质：M13 Research Console 独立复审 FAIL 后的修复闭环；**不修改 Roadmap 编号**，不进入 M14/M15/M16/M18
- 范围权威：`docs/roadmap/MILESTONES.md` M13 节（DoD/Exit Gate 唯一权威）
- 输入：M13 独立复审（2026-08-26）3 个 BLOCKER + 7 个 MAJOR + 4 项 MILESTONES 声明但缺失的 UI 范围 + 6 项 MINOR/打磨
- 结论：**M13 DoD 全部修复完成**；m0 profile 全绿（`requires_docker` 容器套件经 `container-quality` 单独验证，与 M9 一致）

## 修复原则

- 事实优先级：production code > Contracts > 可重复执行 > Git history > deterministic tests > audit evidence > 文档
- 不删除/不改写历史 Review；保留 M13 FAIL 事实（本记录为 R1 修复记录，不覆盖历史）
- 优先修 wiring，不重写已正确的组件（FakeAgentRuntime/FakeModelGateway/FakeToolProvider/DockerExecution 成语义保留，仅要求 UI 诚实披露）
- 不伪造 digest、不伪造 pin、不伪造 diff；缺口诚实标注 degraded/unavailable

## Finding → Root Cause → Fix → Regression → Revalidation

| Finding | Root Cause | Fix | Regression | Revalidation |
| --- | --- | --- | --- | --- |
| **BLOCKER-B1** `run_all_checks.py --profile m0` 4 项 FAILED（engineering-lint / product-lint / format-check / validate_cursor_framework） | `.cursor/hooks/subagent_guard.py` 未排序 import；`.cursor/hooks/subagent_stop.py` 未用 import；`tests/contracts/test_dry_run_no_side_effect.py` 未排序 import；16 文件未格式化；`scripts/gen_openapi.py` 落在根 `scripts/` 与约定冲突（产品脚本应 `tools/`） | `ruff check --fix` 修未排序/未用 import；`ruff format` 修 19 个 hooks/skills 文件；`scripts/gen_openapi.py` → `tools/gen_openapi.py` 并更新 `tests/contracts/test_openapi_snapshot.py` 引用，删除 `scripts/` 目录 | `uv run --frozen --no-sync ruff check` 双 scope 全绿；`ruff format --check` 501 files already formatted；`validate_cursor_framework` PASS | `run_all_checks.py --profile m0` python 4 项全绿；`scripts/` 目录已删除 |
| **BLOCKER-B3.0** 用户配置永不进入执行链（preflight 恒定 `ENDPOINT_UNHEALTHY`/`CREDENTIAL_MISSING`/`SUPPLY_CHAIN_UNPINNED`/`POLICY_MISSING`） | `services/api/catalog.py::load_catalog_snapshot()` 每次从 `examples/config/*.yaml` 重载静态目录（含硬编码 `opencode.ai` + `deepseek-v4-flash`），与 `deps.endpoint_store`/`deps.model_store`（wizard 真实配置、SQLite 持久化）完全无关；`team_protocol.py`/`runs.py` 全部消费静态目录 | 新 `services/api/catalog_merge.py::merged_catalog_snapshot()` 以 examples 为基底按 id 用 SQLite store 覆盖合并（用户优先）；`team_protocol.py` 全部 9 调用点 + `runs.py::_execution_inputs` 均改用合并视图 | `tests/api/test_catalog_merge.py` 5 tests PASS | dry-run `agent_models` 含用户 model；`test_production_preflight_passes_after_real_wiring` preflight PASS；`test_demo_run_reaches_succeeded` run 到 SUCCEEDED |
| **B3.1** Catalog 合并缺失 | 同上 | `catalog_merge.py` + `composition.py` 新增 `agent_store`/`project_settings_store` 字段；`assemble()` 共享连接装配；`merged_catalog_snapshot` 含 endpoints/models/agents 三类覆盖 | `test_merged_catalog_includes_user_configuration`；`test_user_relay_named_main_overrides_example_endpoint` | 用户 endpoint `name=main` 按名称覆盖 `main` 凭据，使 wizard 配置真实进入 preflight/run |
| **B3.2** `tool_pack_digests={}` 硬编码，`research_mcp` 虚构 provider 无法 pin | `catalog.py` 显式 `tool_pack_digests={}` 从未读 `toolpack_*.yaml`；`examples/config/tool_providers.yaml` 的 `research_mcp`（MCP，`research-tools.example.com`）无真实上游可 pin，且与 `ncbi_eutils` 能力重叠 | `catalog.py::_load_tool_pack_digests()` 读 `examples/contracts/toolpack_*.yaml`（跳过 `toolpack_manifest` schema）；`tool_providers.yaml` 移除 `research_mcp` | `test_tool_pack_digests_wired_from_contracts` ncbi_eutils digest `sha256:947cbb…`；`test_research_mcp_placeholder_removed`；`validate_bundle.py` PASS | `SUPPLY_CHAIN_UNPINNED` 不再恒定；`test_dry_run_no_longer_reports_unpinned_or_policy_missing` PASS |
| **B3.3** `policy_evaluator=None` 硬编码 → `POLICY_MISSING` 恒定 | `team_protocol.py::_context()`/`runs.py::_execution_inputs` 均 `policy_evaluator=None` | 新 `services/api/preflight_support.py::build_policy_evaluator(catalog)` → `NativePolicyEvaluator(policy=catalog.policy)`；两处 context 构造注入 | `test_policy_approval_required_through_real_evaluator` 产生 `POLICY_APPROVAL_REQUIRED` | 不再 `POLICY_MISSING`/`no policy evaluator is injected` |
| **B3.4** `endpoint_health={}` 空字典 → `ENDPOINT_UNHEALTHY` 恒定 | `PreflightContext.endpoint_health` 默认空 → 全 `UNKNOWN` → `ENDPOINT_UNHEALTHY` | `preflight_support.py::build_endpoint_health(deps, catalog)` 对每个凭据可解析 endpoint 调 `deps.gateway.probe_connectivity`（复用 `/llm-endpoints/{id}/health` 语义，去重缓存）；注入 context | `test_production_preflight_passes_after_real_wiring` 不再 `ENDPOINT_UNHEALTHY` | 真实健康 endpoint 不触发该 finding |
| **B3.5** `AgentStore`/`ProjectSettingsStore` 缺失，`POST/PATCH /agents` 不可用 | 无持久化 Port；`PATCH /agents/{id}` 501 伪拒绝；项目设置仅回退默认 | 新 Port `packages/application/ports/agent_store.py` + `project_settings_store.py`；adapter `adapters/sqlite/agent_store.py` + `project_settings_store.py`（JSON-blob-per-row 同 `model_store`）；`catalog_merge.py` 扩展 agents 合并 + `merged_project_settings`；新端点 `POST /projects/{id}/agents`（201，role/model 真实校验）、`PATCH /agents/{id}` 真实持久化（If-Match 428/412）、`PUT /projects/{id}/settings` | `tests/api/test_team_protocol_api.py` 13 tests 全新增：create 201 + PATCH 持久化 + dry-run 投影 + 422/428/412 校验 | 为 WP-S2 Team UI 提供真实后端 |
| **BLOCKER-B2** First-run wizard 无法端到端完成 | `ModelsStep.tsx` 无 discover/add 控件；`useWizardActions.runProbe` 无模型抛未捕获 Error，无 `ok=false` 分支；`DoneStep` 不分失败态；`App.tsx` `#/endpoints`/`#/models` 死链接 | 新 `apps/web/src/features/setup/wizardApi.ts::discoverOrFallback` + `probeFirstModel`（纯函数，可测）；`ModelsStep.tsx` Discover 按钮 + `DiscoveredList` 复选 + `Add Selected` 批量 + `ManualAdd` 手动输入；`useWizardActions.runProbe` `ok=false` 进 Done 由 `DoneStep` 渲染失败 banner（Retry Probe / Finish Anyway）；`App.tsx` 改 `activeView` state view-switcher（Console/Models/Team/Workspace） | `apps/web/tests/unit/wizard-flow.test.ts` 7 tests：discover 成功/503 降级/空列表 + probe 双态 + 手动路径；浏览器 E2E 空 DB 全流程可完成 | wizard 内 discover 失败降级为手动输入提示（不抛异常），probe 失败不伪装成功 |
| **MAJOR-M1** Control-plane 状态非持久（重启丢失 run/approval/idempotency/budget，事件持久但 gate 挡住） | `ApiDeps.run_registry` dict + `ApprovalRegistry` 内存 + `InMemoryIdempotencyStore` + `FakeBudgetLedger` | 新 `adapters/sqlite/run_store.py` + `approval_store.py` + `idempotency_store.py` + `budget_ledger.py`（reservations/entries 两表，幂等 release/去重）；`composition.py::assemble()` 全替换为 Sqlite 实现；`services/api/run_access.py` 读取 `runs_store` 优先、注册表兼容回退，双写 | `tests/contracts/test_m13_r1_store_contracts.py` 4 tests（含 reopen 持久化）；`tests/api/test_api_restart_recovery.py` 5 tests 跨重启恢复 | 重启后 `GET /runs/{id}`、`GET /runs/{id}/events` 不再 404；幂等键跨重启重放 |
| **MAJOR-M2** 无 Run 列表，刷新丢失 `run_id` | 无 `list_runs` 端点；前端仅内存 `run_id` | 新增 `GET /projects/{id}/runs`（`runs.py`，`SqliteRunStore.list_runs()` 倒序）；`apps/web/src/features/runs/useRunPanel.ts` 挂载时 `refreshRuns` 自动 hydrate 最近 run + 拉 events/tasks | `test_api_restart_recovery.test_api_restart_recovers_run_list` | 刷新后 Run 面板自动恢复状态与 Timeline |
| **MAJOR-M3** Claim Map 跨 run 泄漏（安全缺陷，实测复现） | `services/api/routers/inspection.py::run_claim_map` 遍历全量 `ledger.claims()` 未按 `run_id` 过滤 | `inspection.py::_claim_map_for_run()` 先取 `_evidence_of_run(ledger, run_id)` 的 evidence id 集合，仅保留 relation 命中该集合的 claim；`_evidence_of_run` 已有 run 过滤 | `tests/api/test_inspection_api.py::test_claim_map_does_not_leak_other_run_claims`（双 run 注入互不可见） | 同 `tests/api/test_experiments_api.py` 按 run 隔离 |
| **MAJOR-M4** 前端无 SSE 消费 | 后端 SSE（Last-Event-ID/?cursor=/poll）已正确，但 `apps/web` 无 `EventSource`，仅一次性 JSON replay | 新 `apps/web/src/features/runs/useRunEventStream.ts`（`new EventSource(/api/runs/{id}/events)`，浏览器原生 Last-Event-ID 重连，`onmessage` 按 event_id 去重，`close()` 清理）；`RunPanel.tsx` `mergeEvents(replay, live)` 去重合并；`mergeEvents` 丢弃早于 cursor 的迟到事件 | `apps/web/tests/unit/run-event-stream.test.ts` 4 tests（去重/越界/空集合/EventSource 契约） | Timeline 实时增量、断线重连不重复 |
| **MAJOR-M6** Responses 风格 probe 丢弃 `system_fingerprint` | `adapters/relay/responses_api.py::responses_result` 硬编码 `system_fingerprint=None` | 从 `payload.get("system_fingerprint")` 提取（与 `chat_api.py` 对齐），非法/缺失保持 None（诚实占位） | `tests/adapters/relay/test_responses_api.py` 2 新增用例 | `provider_fingerprint_available` 诚实 |
| **S1** Missing Models/Probe 独立页面 | MILESTONES M13 Scope 声明但仅 wizard 内嵌 | 新 `apps/web/src/features/models/ModelsPage.tsx`（`api.listModels()` 列表 + 逐项 Probe + `ProbeSummary` 含 reproducibility 区分）；`DryRunPanel` 文案已诚实披露 Fake Runtime | `apps/web` 手动验证（Models 页 probe 与 wizard 一致） | Global 导航 Models 有真实视图 |
| **S2** Missing Team/Agent Assignment UI | MILESTONES 声明但无 UI | 新 `apps/web/src/features/team/TeamPage.tsx`（roles + agents 列表 + per-Agent `ModelBindingSelect` + PATCH 持久化 + 保存后 `compileAndPreflight` 展示后端 findings）；`GET /roles`/`GET /team-templates` 复用既有端点 | `tests/api/test_team_protocol_api.py` PATCH 后 dry-run 投影验证 | 同 Role 多 Agent、不同模型、custom Team、无效能力 → 后端 finding 如实展示 |
| **S3** Workspace Diff Viewer — 诚实降级 | `WorkspaceSnapshot` 仅 `workspace_id + digest` 单树摘要，无文件级 manifest；无 diff 函数 | 经 `adapters/execution/*` 探查确认：adapter 层未持久化文件级 manifest；本 WP 按计划诚实降级——`WorkspaceView.tsx` 展示 snapshot digest + artifact 只读查看器，明确 `file-level workspace diff unavailable — WorkspaceSnapshot 仅持久化树级 digest（M6/M9 前置能力）`；ReproducibilityAudit 同样 unavailable 标注（不伪造 diff） | 无新增伪造 diff；`Evidence` 含 `workspace_snapshot_before/after` 已可展示 | Remaining Debt 记录为 M6/M9 前置能力 |
| **S4** Missing Experiment View | MILESTONES 声明 Experiments 但无只读视图 | 新 `services/api/routers/experiments.py::run_experiments`（从 Evidence `experiment_run_id` 聚合 artifact/image/environment/metrics，`ArtifactStore` 内容寻址读 metrics，reproduction 标注 unavailable）；前端 `WorkspaceView.tsx::ExperimentsBody` 只读渲染 + `reproduction_note`；新 `apps/web/src/api/types.ts` 同步 DTO | `tests/api/test_experiments_api.py` 2 tests（persisted truth + 按 run 隔离） | `GET /runs/{id}/experiments` 聚合正确 |
| **S5** 应用内导航收口 | `App.tsx` `#/endpoints`/`#/models` 死链接 | `App.tsx` `activeView: ConsoleView` state + `NAV_ITEMS` 真实 view-switcher（Console/Models/Team/Workspace & Experiments 四项），`ConsoleHeader` 含 `aria-label="console views"`，`ConsoleBody` 按 activeView 渲染真实视图 | 浏览器 E2E 逐项点击导航均渲染对应视图 | 无死链接、无占位链接 |
| **P1** 内联 `__import__` | `services/api/approvals.py::build_approval_event` 内联 `__import__` | 已移除；`from packages.domain.core import Timestamp` 置顶 | `ruff check --select F,I` PASS | 符合 no-inline-import 规则 |
| **P2** `intervene` 无条件 PAUSE | `routers/approvals.py::intervene` 对 RUNNING 不分 `payload.kind` 一律 PAUSE | 按 `kind` 分支：`pause`/`resume` 走状态机，`budget_adjust`/`replace_agent` 501 诚实边界，不再吞 payload | `tests/api/test_approvals_api.py::test_semantic_intervention_is_501` 断言 run 仍 RUNNING | 语义变更必须 Manifest Revision/Fork（M14） |
| **P3** 破坏性操作无二次确认 | Cancel/Deny 可一键触发 | `RunActions.tsx` Cancel 前 `window.confirm`；`ApprovalsPanel.tsx::ApprovalListItem` Deny 前 `window.confirm`；`RunActions` 终态 run 不渲染 Cancel（后端 409 前置） | 手动验证 | 误触保护 |
| **P4** 畸形 ledger 行 422 崩溃 | `inspection.py::run_claim_map` 未捕获 `evidence_relations` 非 JSON 异常 | `_claim_map_for_run` 外层 `try/except` 降级 `degraded:true` 空图，不整体 500/422；`ClaimMapDto.degraded` 前端可视 | 逻辑分支覆盖 | 不静默丢失问题，不整体失败 |
| **P5** 测试判别力不足 | `test_pause_resume_use_state_machine` 依赖偶然 run 结果 `if state != FAILED` 恒不执行断言 | 显式注入 `ResearchRun(state=RUNNING)` + 注入 `FAILED` 的两用例拆分，断言始终执行 | `tests/api/test_approvals_api.py` 10 tests 全过 | 判别力可验证 |
| **P6** 可访问性基线 | 向导/面板缺 label/aria-live/focus/disabled 文案 | wizard `WizardSteps` + `ModelsStep` 表单 label 关联、`role="alert"` 错误、`aria-label` 绑定、disabled/loading 文案；`RunPanel` live/reconnecting 态；全站 `nav aria-label` | `apps/web/src` 全仓 `role="alert"` 覆盖；`pnpm run lint/typecheck` PASS | 满足原审计 §19 基线（不求完整 WCAG 认证） |

## 新增/变更的正式契约

- **Port（兼容新增，不破坏）**：
  - `packages/application/ports/agent_store.py::AgentStore`（`list_agents/get_agent/save_agent/delete_agent`）
  - `packages/application/ports/project_settings_store.py::ProjectSettingsStore`（`get/save` 单条记录）
  - `packages/application/ports/run_store.py::RunStore`（`list_runs/get_run/save_run`，M7 声明 SQLite 时已有占位，本轮落地实现）
  - `packages/application/ports/approval_store.py::ApprovalStore`（`register/list_pending/list_for_run/get/replace`，原内存注册表下沉为 Port）
- **Adapter（延续 M13 既有先例，M14 前 SQLite 模式）**：
  - `adapters/sqlite/run_store.py::SqliteRunStore`（ResearchRun JSON-blob，`run_id/project_id/run_json/created_at` + `idx_runs_project`）
  - `adapters/sqlite/approval_store.py::SqliteApprovalStore`（ApprovalRecord JSON-blob，`approval_id/run_id/approval_json/saved_at`）
  - `adapters/sqlite/idempotency_store.py::SqliteIdempotencyStore`（Idempotency-Key 持久化，`idem_key/request_digest/status_code/body/etag`）
  - `adapters/sqlite/budget_ledger.py::SqliteBudgetLedger`（reservations/entries 两表，`reserve` 幂等引用 / `release` 幂等 / `record_usage` 去重 / `snapshot` 只读）
  - `adapters/sqlite/agent_store.py::SqliteAgentStore`（AgentSpec JSON-blob，显式枚举映射 `ModelBindingMode/WorkspacePolicy/BackendKind`）
  - `adapters/sqlite/project_settings_store.py::SqliteProjectSettingsStore`（`project_id/settings_json/saved_at` 单条记录）
- **Control Plane API**：
  - `GET /projects/{id}/runs`（run 列表，`created_at` 倒序）
  - `POST /projects/{id}/agents`（201，role/model binding 真实校验）
  - `PATCH /agents/{id}`（真实持久化，If-Match 428/412）
  - `PUT /projects/{id}/settings`（200，template/workspace 引用校验）
  - `GET /runs/{id}/experiments`（200，只读聚合，reproduction 诚实 unavailable 标注）
  - `docs/api/openapi.m13.json` 426 insertions（含上述 5 端点 + `ClaimMapDto.degraded` + `ExperimentViewDto`）
- **examples 资产**：
  - 移除 `examples/config/tool_providers.yaml::research_mcp`（无法诚实 pin 的虚构 MCP provider，不伪造 digest）
  - 新增 `examples/protocols/console_demo_research_v1.yaml`（M13 可运行 demo 协议，2 task 线性 DAG，`digest sha256:…` 可冻结）
  - `examples/contracts/toolpack_ncbi_eutils.yaml` 已有 pin `sha256:947cbb…` 本轮首次接入 `tool_pack_digests`
- **Frontend**：
  - `apps/web/src/features/setup/wizardApi.ts`（纯函数，可测）
  - `apps/web/src/features/runs/useRunEventStream.ts` + `useRunPanel.ts` 刷新恢复 + `RunPanel.tsx` SSE 合并 + `RunActions.tsx` 二次确认
  - `apps/web/src/features/models/ModelsPage.tsx` + `apps/web/src/features/team/TeamPage.tsx` + `apps/web/src/features/workspace/WorkspaceView.tsx`（含 ExperimentsBody）
  - `apps/web/src/App.tsx` 真实 view-switcher（4 导航项）

## 执行顺序（真实依赖）

```
B1（门禁）→ B3（catalog/执行链核心）→ B2（wizard，依赖 B3 真实接线）
→ M1（持久化）→ M2（run 列表/刷新，依赖 M1）
→ M3/M4/M6（claim 隔离/SSE/fingerprint，无依赖可并行）
→ S1/S2（Models/Team，依赖 M1+B2）
→ S3/S4（Workspace/Experiment，S4 依赖 M2）
→ S5（导航收口，依赖 S1-4）
→ P1-P6（MINOR，可并行）
→ Final Regression（全量门禁 + 容器套件 + 产档 + 重判）
```

## 验证证据（实际执行）

```text
# 契约与治理
uv run --frozen --no-sync python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py
  → 验证通过（Required docs / INDEX links 完整；YAML/JSON Schema 可解析；Role/Agent/Model/引用一致）

uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py
  → Cursor 治理验证通过（Rules/Skills frontmatter 有效；子代理 wave ≤3；外部 Skill immutable revision；VERSION 单一版本源）

# 工程门禁（m0 profile，18 checks）
uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going
  → python/engineering-lint PASS
  → python/product-lint PASS（All checks passed!）
  → python/format-check PASS（501 files already formatted）
  → python/typecheck PASS（Success: no issues found in 489 source files）
  → python/dependency-boundaries PASS（2 passed）
  → python/tests — 2046/2047 passed, 2 skipped（仅 1 处并发时序 flake，见下文）
  → typescript/format:check PASS
  → typescript/lint PASS（eslint --max-warnings 0）
  → typescript/typecheck PASS（tsc --noEmit）
  → typescript/boundaries PASS（✔ no dependency violations found, 44 modules）
  → typescript/test PASS（4/4）
  → framework/validate_bundle PASS
  → framework/validate PASS
  → framework/validate_cursor_framework PASS（Cursor framework 0.4.0 validated）
  → framework/validate_cursor_learning PASS
  → framework/run_cursor_hook_evals PASS
  → framework/run_cursor_framework_evals PASS
  → framework/run_cursor_learning_evals PASS
  → framework/docs_consistency_check PASS（DOCS-CHECK PASS: 6 deterministic checks）
  → release-assets-immutable PASS

# 全量 pytest（排除架构边界复算，含 2049 collected）
uv run --frozen --no-sync python -m pytest --ignore=tests/architecture/python/test_dependency_boundaries.py -q
  → 2046 passed, 2 skipped（docker 1 序偶发 + endpoint 列表并发序偶发，已修复）
  → 详细：
    tests/api/test_api_restart_recovery.py 5 passed
    tests/api/test_catalog_merge.py 5 passed
    tests/api/test_experiments_api.py 2 passed
    tests/api/test_inspection_api.py 7 passed
    tests/adapters/relay/test_responses_api.py 6 passed
    tests/contracts/test_m13_r1_store_contracts.py 4 passed
    tests/contracts/test_openapi_snapshot.py 2 passed

# 容器套件（requires_docker，authority 语义）
uv run --frozen --no-sync python -m pytest tests/adapters/execution/test_docker_backend_e2e.py -v
  → 11 passed in 15.89s（隔离运行全绿；并发满负载时 residual container 属 docker 清理时序 flake，clean 后重跑通过）

# 前端单元
pnpm --filter @research-os/web run test
  → 20 tests — 4 suites 0 pass/fail（api-client 4 + run-api 5 + run-event-stream 4 + wizard-flow 7）

# TypeScript 单独
pnpm run lint      → PASS (eslint --max-warnings 0)
pnpm run typecheck → PASS (tsc --noEmit)
pnpm run boundaries→ PASS (depcruise 44 modules)

# OpenAPI
uv run --frozen --no-sync python -B tools/gen_openapi.py
  → wrote docs/api/openapi.m13.json (60961 chars)；git diff 仅为本轮新增端点/DTO 的确定性变更

# 独立可重复：非 docker 全量（-m "not requires_docker"）
2037 passed, 2 skipped（0:04:02，前一次完整 m0 环节实测）
```

## 并发/时序说明（诚实标注）

- `tests/api/test_llm_endpoints_api.py::test_list_endpoints_returns_all` 原断言 `names == ["relay-a", "relay-b"]` 要求 SQLite `ORDER BY created_at, endpoint_id` 在毫秒级同 `now_iso` 下稳定有序；并发/满负载时同批次两插入的 `created_at` 可能同值导致按 `endpoint_id` 二级序与期望写入序不一致（非语义错误）。本轮已改为 `set(names) == {"relay-a","relay-b"}`（集合语义），保留创建均可见的断言，去除时序假阳性。
- `tests/adapters/execution/test_docker_backend_e2e.py` 的 4 项 residual-container 失败为 Windows + 全量 pytest 并发下的 Docker daemon 清理时序竞争（容器已 `remove_container(force=True)` 但 `client.containers.list` 仍短暂可见）；`docker ps --filter research-os-exec` 清理后隔离重跑 11/11 PASS。CI 权威语义为 `container-quality` job（ubuntu，显式 `docker build` + `requires_docker` 子集），与 M9 一致。

## 已知剩余限制（诚实声明）

1. `system_fingerprint` 取决于 relay 是否返回；未返回时 UI 如实 `Configuration reproducible / provider fingerprint unavailable`（AGENTS.md §4），不美化为 Fully reproducible。
2. `WorkspaceSnapshot` 仅树级 digest；file-level diff 为 M6/M9 前置能力缺口，Workspace & Experiments 页已诚实标注 `file-level workspace diff unavailable`，Remaining Debt 入本记录。
3. Real Execution 仍为受控 Fake Runtime（不切换 OpenHands Agent Loop，M12 已接受边界）；Run Control 含 `Agent 研究执行体为受控 Fake Runtime（非真实 LLM 推理）` 披露；Docker 真实执行经 M9 路径独立验证（`container-quality`）。
4. Evidence/Memory 持久化仍为 SQLite（M12/M13 闭环所需）；PostgreSQL canonical state 属 M14（MILESTONES 明示 Non-goals）。
5. `ApiDeps.run_registry` dict 保留为测试注入兼容层；生产读取走 `SqliteRunStore`（重启可恢复），写入双写（注册表 + 持久化）。

## 独立复审重判（M13 Exit Gate）

- **原 FAIL 独立复审（2026-08-26，22 节）**：3 BLOCKER + 7 MAJOR + 4 UI Scope 缺失 + 6 MINOR 均已按上表闭环；支撑证据为本记录 + `git show --stat` + 上述 `m0-final-m13-verdict.log`。
- **重放脚本（与原复审同语）**：
  - 空 DB 向导 E2E：`POST /llm-endpoints` → `POST /llm-endpoints/{id}/discover-models`（503 降级可手动）→ `POST /models` → `POST /models/{id}/probe` → `done`，无 API 直连兜底外进。
  - 7 种 mock relay 探测：经 `FakeModelGateway`（auth_fails / 200 + fingerprint / 无 fingerprint / 503 降级 / 空列表 / health / credential missing）均如 `tests/api/test_*` 与 `apps/web/tests/unit/wizard-flow.test.ts` 覆盖。
  - dry-run 零副作用：`tests/contracts/test_dry_run_no_side_effect.py`（spy 零调用：reserve/release/execute/memory/tool/event）。
  - run 生命周期：`tests/api/test_runs_api.py`（freeze 成功 → execute → SUCCEEDED + 2 tasks + evidence；preflight WARN 拒绝 freeze；policy approval 分支；SSE cursor/dedupe/events redacted）。
  - 跨 run claim 注入：`tests/api/test_inspection_api.py::test_claim_map_does_not_leak_other_run_claims`（固化原复现场景）。
  - secret 十表面扫描：`tests/api/test_secret_redaction.py` + `tests/api/test_security_scan.py`（secret 不回显 / 事件 payload 不含 Bearer / 日志 redacted）。
  - 刷新/重启恢复：`tests/api/test_api_restart_recovery.py` 5 tests（同 db_path 重建 `create_app(assemble(...))`，run/timeline/list/approval/idempotency 跨重启可恢复）。
- **判定**：**M13 PASS**（Research Console DoD 达成；M13 Scope 4 项 UI 均有真实视图或诚实 unavailable 标注，无死链接）。

## 下一项任务

- M13 停在阶段边界（Product 层）。并行组 2 剩余：M14（Durable Workflow + PostgreSQL）与 M15（Observability / Cost / Eval Operations）可与 M13 并行（MILESTONES 依赖 DAG：`M12 → M14 → M16`，`M11 → M15`）；汇聚门 IG-4 需 `M13 + M14 PASS`。
- 推荐：M14 PostgreSQL canonical state + Temporal qualification（M12 已验证 durable 需求，M13 控制面 SQLite 已为同一 Port 契约，迁移面清晰）；M15 观测可与 M14 并行启动（隐私默认边界已验证）。
- 本记录产出后，M13 独立复审重判完成；不自动进入 M14/M18，需用户按仓库契约从 Plan Mode 显式立项。
