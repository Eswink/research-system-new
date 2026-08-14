# Changelog

## v0.4.0 — 2026-08-14（learning-evals fixture 污染修复）

- `run_cursor_learning_evals.py` `build()` 不再复制真实 `.cursor/learning/`
  资产，改为构造空 learning 骨架（REGISTRY + SKILL_RELATIONS +
  inbox/accepted/rejected/clusters 目录）：原实现把真实 LEARN 提案复制进
  临时目录后由 `install()` 覆盖 REGISTRY entries，使 fixture 测试中出现
  "proposal missing registry entry" 与 target_paths 不存在（fixture
  污染）；真实 LEARN-20260813-001/002 资产本身无问题，未改动。
- 验证：`run_cursor_learning_evals` PASS（valid/single/no-validation/cycle
  四模式）；`validate_cursor_learning` PASS（2 proposals, 9 relations）；
  engineering-lint（F/I）PASS。m0 profile 恢复全绿（此前唯一 FAIL 项）。

## v0.4.0 — 2026-08-14（M7 Quality Gate Closure）

- M7 收尾工程债（PLAN-20260814-011）：m0 profile 全绿恢复。
- ruff lint/format：`run_orchestration/__init__.py` import 排序、
  `service.py` unused imports 清理、`tests/e2e/test_orchestration_convergence.py`
  import 排序；12 个 M7 文件 `ruff format`。`ruff check` 0 errors、
  `ruff format --check` 244 files 全过。
- mypy strict：16 errors → 0（227 files Success）。`preflight.py`
  frozen_contracts 显式 `dict[str, object]`（RunManifest 字段方差对齐）；
  `test_m2_policy_budget.py` Reserver 补齐 BudgetLedger protocol release；
  `test_run_rejections.py` capabilities 键改用 ModelCapability 枚举；
  `test_fault_convergence.py` `_start` 返回 RunOutcome；
  `test_cancel_resume.py` `_drift_parts` TypedDict 精确类型化。
- 全量回归：pytest 989 passed；validate_bundle / governance validate
  PASS；TypeScript 全 PASS。learning-evals 为独立 P2 项（BACKLOG）。

## v0.4.0 — 2026-08-14（M7 Reliable Mock Vertical Slice）

- M7 完成（commit `782887d`）：`Foundation / Executable Research Kernel =
  completed`；M7 是核心基础设施阶段结束的 Integration Milestone。
- RunOrchestrationService 端到端编排（Compile → Preflight → Freeze →
  TeamResolve → Execute → Evidence/Claim → Gate → Complete，
  `packages/application/run_orchestration/`）；ResearchRun 实体与 Run
  状态机真实迁移（`packages/domain/run.py`）。
- SQLite 持久化三件套 `adapters/sqlite/`：SqliteWorkflowEngine
  （tasks/leases/idempotency_records/outbox_events）+ SqliteArtifactStore
  （内容寻址 blob）+ SqliteOutboxEventPublisher（Transactional Outbox）；
  M5 contract suite 验收持久化实现。
- TaskLease/heartbeat + `recover_expired_leases` 重启恢复；IdempotencyRecord
  submit 幂等去重；retry/backoff（F-01/F-02）；协作式 cancel + CANCELLED
  事件；Pause/Resume 拒绝 manifest digest mismatch
  （`task_executor._assert_frozen_manifest`，落实 AGENTS.md §5）。
- Reference Scenario `examples/protocols/sort_analysis_v1.yaml`
  （2-phase，execution + review/QUALITY_GATE）；E2E 故障注入矩阵
  F-01..F-12（`tests/e2e/` 12 文件）。
- 文档对账（同日）：M7 retrospective plan/recheck；Completion Matrix；
  M7 Completion Record；BACKLOG 三区重构（M7 完成日期以 commit 为准修正
  为 08-14；resume Manifest check 勾选修正；"M8" 引用改为 post-M7 能力）。

## v0.4.0 — 2026-08-13（M6 OpenHands Runtime Adapter）

- M6 完成（commit `f4b2168`）：OpenHandsRuntimeAdapter 实现 AgentRuntime
  Protocol 全 6 方法；openhands-sdk==1.42.0 采用为 ADOPTED（uv.lock sdist
  sha256 `4706ae2c…`；revision lock `v1.42.0@391fbb8d`）。
- LLM Relay 三要素端到端（S7 mock 端点实证，无厂商绑定，key 不落
  Domain/log）；非知名 model 加 `openai/` 前缀变换（仅 llm_factory）。
- cancel 语义显式收敛 CANCELLED 终态（重复 cancel 幂等；终端后 no-op）；
  Policy Wrapper 独占 execute_tool 直通面（DENY 阻断不触达 SDK、
  REQUIRE_APPROVAL 发事件）；错误模型按 ErrorClassification.kind 闭集
  映射，SDK 类型零越过边界。
- Workspace LocalWorkspace 路径绝对化 + 根校验；host shell 默认 deny；
  Usage 归一化入 BudgetLedger；真实 adapter 与 Fake 共享 contract suite。
- 全量回归：pytest 840 passed；mypy strict 183 files；m0 profile PASS。
- 文档对账（2026-08-14）：M6 计划/复检/记忆为原开发窗口记录，保留不动；
  CHANGELOG 本条为对账补记。

## v0.4.0 — 2026-08-12（M5R 独立复审）

- M5R 独立复审（非开发窗口自评）：全部 6 个 spike 重跑复现 PASS；upstream
  provenance 独立验证（git ls-remote tag v1.42.0 → commit `391fbb8d` 与 clone
  一致；GitHub 页面确认官方仓库；MIT LICENSE 实测；PyPI sdist 下载实测哈希）。
- 复审修复：
  - S5 spike 文件路径改绝对路径 + CWD 泄漏断言（原相对路径实证
    `LocalWorkspace.file_upload/download` 以裸 Path 相对 CWD 解析，曾残留
    `spike.txt` 于仓库根目录）。
  - `OPENHANDS_REVISION_LOCK.yaml` sdist digest 修正为 PyPI 实测
    `4706ae2c…`（原记录 `e8be3e58…` 与 PyPI 不符且不属于相邻版本，判定抄录
    错误）；PyPI sdist 与 git tag 源码文本级一致（无 installed/源码漂移）。
  - 审计 §8 补充 LocalWorkspace 文件 API 路径基准不一致（file_upload/download
    裸 Path vs git_* working_dir 相对）；M5 matrix §4 / M6 Design Notes §5 /
    Risk Register 增 R-17；contract 数量修正为实测 127。
- 回归：pytest 734 passed；tests/contracts 127 passed；m0 profile 18/18 PASS。
- 结论不变：M5R = PASS；M6 readiness = READY（新增非阻断证据差异，无 BLOCK）。

## v0.4.0 — 2026-08-12

- M5R Upstream Source Intelligence & Runtime Qualification 落地：
  - 以 OpenHands Software Agent SDK v1.42.0（commit `391fbb8d`，MIT）真实源码 +
    最小可执行实验对 M5 的 14 个 Port 做现实校验；clone 至仓库外隔离位置
    `d:\upstream\`，SDK 保持 PLANNED 不入 uv.lock。
  - 产物：`docs/references/upstream/` 下 revision lock（机器可读）、源码审计
    （10 领域 file:path:symbol 级证据）、Port 兼容矩阵、修正日志（零代码修正，
    5 项候选驳回）、M6 Adapter Design Notes、M6 Risk Register（16 项，无
    BLOCK）、M6 Readiness Report。
  - Executable spikes S1-S6 全部以 mock credential 通过（TestLLM 脚本化响应），
    实证：LLM 三要素 base_url 原样透传；interrupt→PAUSED 非终态；重复 run 幂等；
    resume 需显式 conversation_id（"Resumed conversation from persistent
    storage"）；错误路径双通道（ConversationRunError + ConversationErrorEvent）。
  - SWE-ReX README 级对照：命令执行独立于 workspace 是通用模式，支撑
    ExecutionBackend 独立 Port 边界。
  - 关键结论：AgentRuntime/ModelGateway/ToolProvider/WorkspaceBackend/
    ExecutionBackend 需 adapter 承接（cancel 语义、resume 漂移、execute_tool
    直通、host shell、插件 digest 为主要承接点）；其余 9 个 Port 完全
    Research OS 自有；M5R = PASS，M6 readiness = READY。
  - m0 profile 18/18 PASS；pytest 732 passed；mypy 166 files；双 validator PASS。

## v0.4.0 — 2026-08-12

- M5 Ports + Fakes 落地：
  - Port 权威位置统一为 `packages/application/ports/`：AgentRuntime / WorkflowEngine / ModelGateway（收编原 ModelRelayGateway）/ ToolProvider / WorkspaceBackend / ExecutionBackend / ArtifactStore / EventPublisher / PolicyEvaluator / CredentialResolver / MemoryStore / BudgetLedger（收编原 BudgetReservationPort）+ EndpointStore / ResourceCatalog；旧模块改为兼容导出，全仓 import 迁移。
  - 统一错误模型 `ports/errors.py`（Transient / Permanent / Timeout / InvalidInput / Cancelled，消息 redaction）；协作式 cancellation；operation-key 幂等语义。
  - domain 增量：`ToolResultRecord`、`ExecutionRun`（ExecutionStatus 含 TIMED_OUT）、`EventType`/`EventEnvelope`（27 事件 + payload digest 强校验，EVENT_MODEL.md §1/§2）。
  - `PolicyEvaluator` Port 收编：`NativePolicyEvaluator` 声明实现 Port；`preflight/policy_check.py` 改为经 `PreflightContext.policy_evaluator` 注入，不再直接实例化。
  - 12 个 Fake 实现 `adapters/fakes/`（deterministic / 错误注入 / call recording / close 语义；不依赖网络/API Key/Docker/OpenHands；import-linter 契约 `.importlinter.fakes` 锁定）。
  - Contract suite `tests/contracts/`（注册表驱动，真实 adapter 注册后自动复用）：通用矩阵 + AgentRuntime/WorkflowEngine/各 Port 特定语义 + provider 类型泄漏与序列化边界断言。
  - 文档：新增 `docs/architecture/PORTS.md`（Port 规格 + D1-D6 决策记录）；`AGENT_RUNTIME.md` §1 签名按契约资产规则同步修正为 sync。
- 全部 696 测试通过；mypy 162 files；8 项架构边界测试（新增 fakes 契约）；bundle / governance validators 通过。

## v0.4.0 — 2026-08-11

- M4 Role / Team / Task 落地：
  - TaskContract 补齐 `input_schema` / `budget` / `failure_policy`（domain + loader，不再静默丢弃）；新增 `domain_discovery_input_v1` / `experiment_run_input_v1` 输入 schema。
  - AcceptanceCriterion 结构化参数（artifact/minimum_sources/metric/operator/threshold/evaluator）与纯函数求值器 `packages/domain/acceptance.py`（9 类，SCHEMA_VALID 经 jsonschema，fail-closed）。
  - HandoffBundle 增加 `created_at` / `producer_agent_id` / `producer_role_id` 与加载器 `load_handoff_bundles`；digest 改为 `sha256:<64 hex>` 强校验。
  - RoleDefinition 增加 `default_skills`（可折叠等价 Skill）与 `forbidden_capabilities`（Reviewer 只读 / Writer 不得改 Claim truth 与 Experiment metric / ExperimentEngineer 禁止外部发布）；AgentSpec 增加 `skill_refs` / `capability_refs` / `context` / `runtime_kind` / `budget_policy_ref` 完整配置面。
  - 新增 `schemas/skill.schema.json` + `examples/config/skills.yaml`（6 个 Skill，机器可加载）。
  - Role activation/collapsing 引擎 `packages/domain/activation.py`；RolePool `selection_strategy` 进入编译期选择 `packages/application/protocol_compile/selection.py`。
  - CompiledRunPlan 增加 `role_activations` / `phase_assignments` 投影（phase→role→agent 稳定绑定）。
  - Preflight 新增 role 类检查（ROLE_DISABLED / AGENT_PERMISSION_DENIED / HETEROGENEITY_VIOLATION），缺失角色、Agent 权限越界、异构评审约束在启动前被发现。
- 全部 528 测试通过；bundle validator / governance validator 通过。
- 独立复审修复（本日）：
  - `reviewer_b` 主模型从 `research_alpha` 改为 `coding_beta`，消除与 `writer` 的模型共享（HETEROGENEITY_VIOLATION 前置条件）；
  - `check_heterogeneity` 按 role 聚合模型并逐对输出 finding，修复 Reviewer 缺位时 `set().union()` 崩溃；
  - AgentSpec `workspace_policy` 改为可选（None=继承 Role 默认），编译期投影到 CompiledRunPlan `agent_workspace_policies`，越界配置产生 `WORKSPACE_POLICY_VIOLATION`；
  - `compiled-run-plan.schema.json` 增加 `agent_workspace_policies` 可选属性；
  - 新增 INHERIT binding、workspace policy 继承/边界、fixtures 异构回归测试。
- M4 技术债收口（本日，测试 540→555）：
  - `compiled-run-plan.schema.json` 将 `agent_workspace_policies` 改为必填（序列化契约强制，fixture 同步）；
  - `SELECTION_STRATEGY_DEGRADED`（INFO finding）让 COST_AWARE / EVAL_SCORE_AWARE 的编译期 FIXED 退化可见；compiler 不再丢弃非 ERROR findings（INFO/WARNING 随计划携带，preflight 状态语义不变）；
  - 写面 capability 与有效 workspace policy 静态交叉验证（`workspace.write.code` / `workspace.delete` 需 `isolated_writable`，`deliverable.write/edit` 需 `deliverable_only` 或 `isolated_writable`），执行期 Policy Wrapper 仍负责运行时 enforce；
  - `RoleDefinition.review_panel_role`（WRITER / REVIEWER / NONE）取代 `_WRITER_ROLES` / `_REVIEWER_ROLES` 常量，异构评审约束支持自定义角色；schema/loader/fixtures/validator 同步。

## v0.4.0 — 2026-08-11

- M3 Model Relay Compatibility 落地：OpenAI-compatible 中转站运行层（EndpointStore CRUD、env credential resolver、endpoint test、`/models` discovery、capability probe、ModelEligibilityPolicy、circuit breaker、ModelRuntimeFingerprint、fallback audit、secret redaction）。
- 新增 `packages/application/model_relay`（Ports + eligibility + probe/discovery/fingerprint/fallback use cases）与 `adapters/relay`（httpx gateway + SSE 解析 + env resolver + YAML/内存 store）。
- 新增 4 个契约 schema（probe-result / endpoint-health / model-runtime-fingerprint / fallback-audit-record）与 4 个契约 fixture；`llm-endpoint.schema.json` 扩展 discovery/circuit_breaker 配置。
- 新增依赖 httpx 0.28.1（BSD-3-Clause）与 tenacity 9.1.4（Apache-2.0），均 pin + 供应链登记。
- 新增 `docs/reliability/CIRCUIT_BREAKER.md` 与 `docs/integration/MODEL_PROBE.md`。
- 新增 application/relay 依赖边界契约（`.importlinter.application` / `.importlinter.relay`）。
- 全部 339 测试通过；m0 18 个确定性门禁通过。

## v0.4.0 — 2026-08-10

- Cursor 工程自动化脚本迁移到对应 `.cursor/skills/<skill>/scripts/`；删除根 `scripts/`。
- 清理遗留的双版本语义与 `research_os_baseline` session context。
- Reviewer 输出改为 hard gate + evidence，不固化数值自评分。
- Plan Mode 改为风险/歧义驱动；明确用户已授权实现时不重复确认。
- 区分 learning lifecycle 与 framework evolution lifecycle。


当前主包统一为一个版本体系。

### Research OS
- 用户通过 OpenAI-compatible 中转站配置 `Base URL + API Key + Model ID`。
- 每个 Agent 可独立绑定模型。
- Role / Agent / Task / Handoff 分离。
- OpenHands Native 是 MVP Agent Runtime adapter。
- Tool / Skill / Capability、Workspace、Evidence、Experiment、Evaluation 保持独立。
- 包含 Protocol compile/preflight、可靠任务语义、预算、数据治理和安全边界。

### Cursor Engineering Framework
- Project Rules 使用 `.cursor/rules/*.mdc`。
- Agent Skills 使用 `SKILL.md`。
- Custom Subagents 使用 `.cursor/agents/*.md`。
- Hooks 提供 secret/shell/subagent/evolution 等机器级控制。
- Cursor 工程知识库存放于 `.cursor/knowledge/`。
- 自学习采用 Observation → Proposal → Replay → Validation → Promotion。
- Subagent 改为“按波次最多 3 个”，取消整个用户任务累计 3 个上限。
- 发布质量由确定性 validators/evals + release manifest 驱动；独立 reviewer 按变更风险选择。
