---
id: PLAN-20260919-107
slug: runtime-selection-surface
title: Runtime 选择面：配置驱动 Fake | OpenHands（两组合根同侧、未配置一致、选择结果与运行时指纹进 manifest/读面）（EC-01）
status: DONE
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 1 = EC-01（GOAL-006 收口结论长程项第 1 项中「按声明给 adapter 接线」的 adapter 接线部分）。授权来源：2026-09-19 用户 goal 模式指令（新建承接 GOAL-007 并自动化循环推进、无需逐轮确认），并显式授权解除该项 escalation。受控出网边界与 push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`（本 PLAN 严格遵守：默认 runtime 保持 Fake、不引入新依赖、凭据只从环境变量读、真实端点不进默认 CI）。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260919-107-runtime-selection-surface.md
memory_entries:
  - MEM-20260919-079
---

# PLAN-20260919-107 — Runtime 选择面（GOAL-007 cycle 1 = EC-01）

## 目标

把「组合根硬编码 `FakeAgentRuntime`、OpenHands adapter 零接线、而
`packages/domain/manifest.py:12` 的 docstring 却声称『runtime 装配由
OpenHandsRuntimeAdapter 决定』」这条**声明与事实的落差**收敛成**配置驱动的选择面**：

1. **一个选择点**：两个组合根（SQLite 与 PG）读**同一个选择函数**，不各写一套 `if`。
2. **未配置时与今日一致**：默认仍是 Fake + 受控 demo 输出；现有套件全绿。
3. **选择结果与运行时指纹可判**：选择写进 `RunManifest.execution_backend`（该字段今天
   恒为 `None`，正是这条落差的可观测形态），并在读面上可判。

本 PLAN **只做 EC-01**：受控出网门链（EC-02）、离线全链（EC-03）、UI 披露（EC-04）、
工具面边界（EC-05）、`tool_pack.*`（EC-06）各自独立成 cycle，本 PLAN 不预做。

## 先探明再动手（本轮只读勘察已确认的事实）

1. **两个根、两处硬编码**：`services/api/composition.py:264-277`（`_sqlite_store_parts`）
   与 `services/api/pg_composition.py:159-172`（`_build_pg_orchestration`）各自构造
   `FakeAgentRuntime(structured_output=demo_session_output())`；`pg_composition.py:22`
   从 `composition` 复用 `demo_session_output`。二者是同侧（同一函数）的**现状反例**。
2. **选择面的注入点已经存在**：`OrchestrationDependencies.runtime: AgentRuntime`
   （`packages/application/run_orchestration/dependencies.py:23`）——构造点只有上述两处，
   因此「两侧同侧」在结构上**可判定**（数 `FakeAgentRuntime(` 的直接构造点）。
3. **真实 adapter 的构造入口**：`adapters/openhands/runtime_adapter.py:64`
   `OpenHandsRuntimeAdapter(deps: AdapterDependencies)`；依赖包
   `adapters/openhands/session_types.py:77`（`credential_resolver` / `policy_evaluator` /
   `build_llm` / `build_workspace` 为必填）。⇒ 组合根**已经具备**构造它的零件
   （`RegistryCredentialResolver`、`policy_evaluator`、`OpenAIChatGateway` 全在 `ApiDeps` 里）。
4. **manifest 的冻结路径是单入口**：`freeze_manifest(run_id, plan, report, context, *,
   pricing_freeze)`（`packages/application/preflight/preflight.py:173`）→ `_manifest_of`
   （同文件 `:218-252`）。`_manifest_of` 今天**不设** `execution_backend` / `environment`
   —— 与 `packages/domain/manifest.py:11-14` 的 M7 边界声明一致。⇒ 要让选择进 manifest，
   最小改动是给 `PreflightContext` 加一个**中性命名**的字段（见「口径」第 3 条）。
5. **ports 目录有字符串门禁（关键约束）**：`tests/contracts/test_common_contract.py:272-278`
   扫描 `packages/application/ports/*.py`，禁止出现 token
   `("openhands", "litellm", "lite_llm", "temporal", "openai", "anthropic", "adapters.")`。
   ⇒ **runtime 取值词表不能放在 ports 里**（否则选择面一落地就撞门禁）。
6. **domain 侧没有同形字符串门禁**：`tests/architecture/python/test_domain_boundaries.py`
   只跑 import-linter（依赖纯度），不扫字符串；`RunManifest` 已有
   `workspace_backend` / `execution_backend: str | None` 这类**后端标识字符串**先例。
7. **没有测试钉死 manifest digest**：`tests/api/**` 与 `tests/e2e/**` 中不存在对
   `manifest_digest` / `manifest_semantic_digest` 的硬编码断言（唯一命中
   `tests/adapters/sqlite/test_evidence_memory_persistence.py:92` 是手工夹具串
   `"sha256:manifest"`，与 manifest 冻结无关）⇒ 填充一个**本就声明、今天恒 None** 的
   manifest 字段不会撞既有断言。**这一点在实施时须复验**（WP-A 第 1 步）。
8. **读面 DTO 的增字段有既成流程**：`RunDetailDto`（`services/api/dto/runs.py:104`）增字段
   会改 OpenAPI 快照（`docs/api/openapi.m13.json`）与 web `types.ts`；这是 SCHEMA 已登记的
   耦合（记忆：OpenAPI snapshot & web types coupling）。
9. **`demo_session_output` 的现状**：`services/api/demo.py:17-27`，返回
   `{"analysis_report": {"summary": "controlled fake session output (M13-R1 console demo)",
   "status": "ok"}}`；披露目前**只在 payload 文案里**，读面没有独立的执行体字段（EC-04 主题）。

## 口径（设计取舍，先写死避免实施时漂移）

1. **选择点放在哪**：新增 `services/api/runtime_support.py`（组合层，允许 import adapters），
   导出 `RuntimeSelection`（值对象：`kind` / `adapter` 标识 / `configured` 等）与
   `build_agent_runtime(settings, *, gateway, credentials, policy_evaluator, ...) -> AgentRuntime`。
   两个组合根都调它。**runtime 取值词表（含 `"openhands"` 字面量）只允许出现在组合层与
   adapter 层**，不进 `packages/application/ports/**`（事实 5）也不进 `packages/domain/**`
   （AGENTS.md §5「OpenHands 类型不得进入 Domain」的精神：Domain 只存**中性标识字符串**）。
2. **配置面**：`ApiSettings` 增 `agent_runtime`（env `RESEARCHOS_AGENT_RUNTIME`），
   **默认 `"fake"`**（事实：AGENTS.md §1/§9 + 本 GOAL authorization 第 (3) 条
   「默认 runtime 保持 Fake；选择真实 runtime 必须显式配置 + policy 允许」）。
   **未知取值 ⇒ 装配期显式报错（fail-closed），不静默回退 Fake** —— 静默回退会让
   「我配了真实 runtime」与「我跑的是 demo」不可区分，正是 AGENTS.md §4 要消灭的漂移。
3. **选择进 manifest 的通道**：给 `PreflightContext`（`packages/application/ports/resource_catalog.py`）
   加一个**中性命名**的 optional 字段（拟 `execution_substrate: str | None = None`），
   由组合根从 `RuntimeSelection` 填充；`_manifest_of` 把它写进
   `RunManifest.execution_backend`。**该字段名不得含 token**（事实 5）。
4. **「未配置时与今日一致」的可执行口径**（EC-01 的回归对照）：
   (a) 默认路径 `demo_session_output()` 返回值**逐字段相等**；
   (b) **现有套件全绿**（含 stub/live e2e、契约套件、OpenAPI 快照门）；
   (c) 唯一允许的差异是**加性**的：manifest 里一个**本就声明、今天恒 None** 的字段被如实填充，
   以及读面新增的可选字段。「加性披露」不算行为变化，本 PLAN **必须在证据里点名这条**，
   不靠含糊表述掩盖。
5. **本 PLAN 不做真实出网**：`build_agent_runtime` 在选 `openhands` 时**只构造 adapter**
   （受控 deps、离线），**不发起任何出站调用**；「构造了但没被门链放行就不许跑」属 EC-02，
   本 PLAN 只保证**构造路径可用且可判**。本 PLAN 的任何用例都不得触网。
6. **不新增依赖、不改上游 pin**（GOAL authorization；命中即 BLOCKED）。

## 验收条件

- **AC-01 单侧选择点（结构判据）**：`services/api/composition.py` 与
  `services/api/pg_composition.py` **各自只有一个** runtime 装配点，且都经
  `services/api/runtime_support.py` 的同一函数；反向搜索证明
  `FakeAgentRuntime(` 的直接构造**不再出现**在两个组合根里。
- **AC-02 未配置时与今日一致**：默认（未配置）⇒ 选择结果为 `fake`；`demo_session_output()`
  返回值逐字段与今日相等；受影响套件全绿。
- **AC-03 选择 `openhands` ⇒ 真实 adapter 被构造**：显式配置 `RESEARCHOS_AGENT_RUNTIME=openhands`
  ⇒ `OrchestrationDependencies.runtime` 是 `OpenHandsRuntimeAdapter` 实例（`isinstance` 可判），
  且构造**不发起任何出站调用**（离线）。
- **AC-04 未知取值 fail-closed**：`RESEARCHOS_AGENT_RUNTIME=<未知>` ⇒ 装配期**显式报错**并点名
  取值与非法的原因；**不得**静默回退 Fake。
- **AC-05 选择结果与运行时指纹可判**：选 `fake` 与选 `openhands` 两条路径产出的
  `RunManifest.execution_backend` 取值**不同且可读**；运行时指纹（AGENTS.md §4 的七件事实）
  在读面上有**可判的载体**——已实现并能证明的项如实给出，**证明不了的项显式标注为未验证**，
  **不得留空冒充已验证**（判据须点名这条）。
- **AC-06 反证（先红后复原）**：
  ① 把任一组合根改回硬编码 `FakeAgentRuntime(...)` ⇒ AC-01 的结构判据红；
  ② 把选择函数短路成恒返回 Fake ⇒ AC-03 红；
  ③ 把未知取值改成静默回退 Fake ⇒ AC-04 红；
  ④ 把 `execution_backend` 的填充去掉 ⇒ AC-05 红。
- **AC-07 门禁**：先自查规模门禁（50 行函数 / 450 行文件）与**快照类门禁**
  （OpenAPI 快照 / 设计基线；若读面 DTO 有增字段则同步 `docs/api/openapi.m13.json` +
  `apps/web/src/api/types.ts` + e2e 夹具）；再跑 `make validate-all` 全量 23 项 +
  受影响定向套件（`tests/api`、`tests/application`、`tests/contracts`、`tests/architecture`）
  + web 门（lint / typecheck / unit / build / stub e2e / live e2e）。**本地不绿不得 push。**
- **AC-08 安全**：本 PLAN 的代码**零真实端点调用**、零凭据字面量；`Domain` 不出现厂商名；
  `packages/application/ports/**` 不出现 token（事实 5 的门禁保持绿）；不新增依赖。

## 实施清单

### WP-A — 探明与选择面骨架（先探明再动手）

- [x] 复验事实 7（无测试钉死 manifest digest：`tests/api/**`、`tests/e2e/**` 反向搜索）
      与事实 5（ports 字符串门禁的**确切** token 列表与扫描范围）——把结果写进本 PLAN 的「证据」。
- [x] 新增 `services/api/runtime_support.py`：`RuntimeSelection` 值对象 +
      `build_agent_runtime(settings, ...) -> AgentRuntime`；取值词表与 `"openhands"` 字面量
      只在本模块与 adapter 层出现。
- [x] `ApiSettings` 增 `agent_runtime`（env `RESEARCHOS_AGENT_RUNTIME`，默认 `"fake"`；
      未知取值 fail-closed 报错）。
- [x] **WP-A commit**（独立提交）。

### WP-B — 两个组合根接线（同侧）

- [x] `composition.py::_sqlite_store_parts` 与 `pg_composition.py::_build_pg_orchestration`
      改为经 `build_agent_runtime(...)` 取 runtime；**两处形态一致**。
- [x] 反向搜索确认 `FakeAgentRuntime(` 在两个组合根里**零直接构造**。
- [x] **WP-B commit**（独立提交）。

### WP-C — 选择结果进 manifest / 读面

- [x] `PreflightContext` 加中性命名的 optional 字段；组合根从 `RuntimeSelection` 填充；
      `_manifest_of` 写进 `RunManifest.execution_backend`。
- [x] 读面：执行体标识与运行时指纹的**可判载体**（DTO 增字段按既成流程同步
      OpenAPI 快照 + `types.ts` + e2e 夹具）；证明不了的指纹项**显式标注未验证**。
- [x] **WP-C commit**（独立提交）。

### WP-D — 判据与反证

- [x] AC-01 结构判据（组合根反向搜索 + 单装配点）。
- [x] AC-02 回归对照（默认路径 `demo_session_output()` 逐字段相等 + 受影响套件）。
- [x] AC-03/04/05 用例（选 openhands 构造真实 adapter 且零出站；未知取值 fail-closed；
      manifest `execution_backend` 两路径不同）。
- [x] AC-06 四条反证**逐条先红后复原**，每条记下红/绿的真实输出。
- [x] **WP-D commit**（独立提交）。

### WP-E — 文档同源 + 记录与回写

- [x] 收敛 `packages/domain/manifest.py` 的 M7 边界声明（事实 1：今天声称「runtime 装配由
      OpenHandsRuntimeAdapter 决定」而实际是 Fake）、`docs/architecture/AGENT_RUNTIME.md`、
      `docs/integration/OPENHANDS_ADAPTER.md` 到与事实一致的口径。
- [x] 写 RECHECK（`.cursor/plans/rechecks/RECHECK-20260919-107-*.md`）+ MEM + ALL_PLAN 投影 +
      GOAL 回写（EC-01 状态 / 迭代日志 / child_plans / 状态历史）。
- [x] **WP-E commit**（独立提交）。

## 证据

（实施时逐条填写；未实跑不得记 PASS。）

- **事实复验（WP-A）**：
  - **事实 5 精确化**：`tests/contracts/test_common_contract.py::test_provider_types_do_not_leak_from_ports`
    只扫 `packages/application/ports/*.py`（顶层 `.py`），禁止 token
    `("openhands", "litellm", "lite_llm", "temporal", "openai", "anthropic", "adapters.")`
    —— `openai` 也在名单里，所以 `PreflightContext` 的新字段连 docstring 都不能带这些词，
    落地时字段名取 `execution_substrate` / `runtime_fingerprints`。
  - **事实 7 复验**：`tests/api/**`、`tests/e2e/**` 中**没有**对
    `manifest_digest` / `manifest_semantic_digest` 的硬编码断言——唯二命中是手工夹具串
    （`tests/adapters/sqlite/test_evidence_memory_persistence.py:92` 的 `"sha256:manifest"`、
    `tests/application/test_pause_coordination.py:112` 的 `"manifest-digest"`），与冻结无关。
    因此填充一个**本就声明、今天恒 None** 的 manifest 字段不撞既有断言（实跑证实）。
- **AC-01 结构判据**：`tests/api/test_runtime_selection_surface.py::test_no_composition_root_builds_the_fake_runtime_directly`
  （AST 数 `FakeAgentRuntime(...)` 调用点，两个组合根均 0）+ `::test_composition_roots_call_the_one_selection_point`。
- **AC-02 回归对照**：`::test_unconfigured_settings_select_the_controlled_demo_runtime`（默认 `fake` /
  `configured=False`）、`::test_explicit_fake_is_marked_configured`（显式与默认可区分）、
  `::test_demo_session_output_is_unchanged`（**逐字段**等于
  `{"analysis_report": {"summary": "controlled fake session output (M13-R1 console demo)", "status": "ok"}}`）；
  受影响套件 `tests/api` **459 passed / 1 skipped**（DSN pin 配方；见下方「环境事实」）。
- **AC-03 / AC-04 / AC-05 用例输出**：`tests/api/test_runtime_selection_surface.py` **13 passed**
  （含 `::test_openhands_selection_constructs_the_real_adapter_offline`——用「`resolve` 即炸」的
  凭据替身证明**构造期不解析凭据**，因此不触网；`::test_openhands_without_required_faces_names_what_is_missing`
  逐项点名；`::test_unknown_runtime_fails_closed_naming_the_value`；
  `::test_frozen_manifest_records_the_selected_substrate`、
  `::test_frozen_manifest_stays_undeclared_without_a_selection`、
  `::test_runtime_fingerprints_are_explicitly_not_verified`、
  `::test_frozen_event_payload_carries_the_substrate_to_the_read_face`）。
- **AC-06 反证四条（先红后复原，全部实跑）**：
  | # | 注入 | 结果 |
  | --- | --- | --- |
  | ① | `pg_composition._build_pg_orchestration` 改回硬编码 `FakeAgentRuntime(...)` | `test_no_composition_root_builds_the_fake_runtime_directly` **红**（1 failed / 12 passed）⇒ 复原 |
  | ② | `build_agent_runtime` 的 openhands 分支短路成 `_fake_runtime()` | `test_openhands_selection_constructs_the_real_adapter_offline` + `::test_openhands_without_required_faces_names_what_is_missing` **红**（2 failed）⇒ 复原 |
  | ③ | 未知取值改成静默回退 Fake | `test_unknown_runtime_fails_closed_naming_the_value` **红**（`DID NOT RAISE RuntimeConfigurationError`）⇒ 复原 |
  | ④ | `_manifest_of` 去掉 `execution_backend=context.execution_substrate` | `test_frozen_manifest_records_the_selected_substrate` + `::test_frozen_event_payload_carries_the_substrate_to_the_read_face` **红**（`assert None == 'openhands'`）⇒ 复原 |
  四次复原后 `git status --short` 干净、13 passed。
- **AC-07 门禁**：规模门禁 `tests/tooling/test_python_source_limits.py` **944 passed**（0.00 超限）；
  `ruff check` + `ruff format --check` 绿；`mypy` **934 source files, no issues**；
  m0 全量 23 项（见「CI / 门禁」）；架构门 `tests/architecture/python` **963 passed**
  （含 import-linter 两条；**必须用 `uv run --frozen --no-sync` 启动**，否则 `lint-imports` 不在 PATH 会误红）。
- **AC-08 安全**：本 PLAN 的产品代码零真实端点调用（唯一构造路径不解析凭据、不建连接）；
  零凭据字面量（测试里的 `sk-test-...` 是既有受控夹具串，不与真实端点组合）；
  ports token 门禁保持绿；`ruff`/mypy 全绿；**零新增依赖**（未改 `pyproject.toml` / lock）。
- **环境事实（重要，非代码缺陷）**：`tests/api` 单独跑时 3 条 `@pytest.mark.postgres` 用例
  （`tests/api/test_worker_plane_composition.py` 的 2 条 + `test_api_assembly_reads_artifact_blob_dir_env`）
  会**真连 PG**：它们只在加载 `tests/postgres/conftest.py` 时才按标记 skip，
  单独跑该文件则不加载 ⇒ 容器不在时红。这是既有口径（记忆：postgres marker skip needs PG conftest），
  **不是本轮回归**；m0 全量跑时该 conftest 在射程内。
- **CI run（六 job 终态）**：

## 状态历史

- 2026-09-19 done：EC-01 交付并复检 **PASS_WITH_WARNINGS**（RECHECK-20260919-107，W-1…W-6）。
  5 个 WP 各自独立提交：WP-A 选择面骨架（`runtime_support.py` + `ApiSettings.agent_runtime`）、
  WP-B 两组合根接线（含 PG 凭据面单实例修复）、WP-C manifest/读面载体、WP-D 13 条判据、
  WP-E 文档同源收敛（`manifest.py` 的声明与事实不符已更正 + `AGENT_RUNTIME.md` §3.1）。
  四条反证逐条先红后复原；m0 **23/23**；`mypy` 934 files 干净。
  实现期返工三处（记录诚实）：① 初版把 runtime 装配内联进 `_sqlite_store_parts` ⇒ 撞
  50 行函数门禁（58 行）+ `composition.py` 到 451 行（超 450）⇒ 按「随改动搬代码」拆出
  `_sqlite_orchestration` / `_sqlite_apideps`，并把 `sqlite_artifact_blob_dir` 与
  `build_sqlite_draft_service` 移到 `assembly.py`（该模块本就为此存在）；
  ② `composition.py` 不再 re-export `demo_session_output` ⇒ `tests/api/base_fixtures.py`
  导入失败（243 errors）⇒ 改从真正的属主 `services.api.demo` 导入（**机械搬 import，
  未改任何断言**）；③ m0 抓出 `python/typecheck` 6 条 mypy 错（守卫列表不带窄化、测试触
  私有属性、缺 cast）⇒ 守卫改成直接判两个值使 mypy 真窄化，**未削弱任何判据**。
- 2026-09-19 derive：由 GOAL-20260919-007 cycle 1 派生（EC-01 为 EC 表首个待办项）。
  本轮**只读勘察**确认了九条起点事实（两个组合根各硬编码一处 Fake 装配点、真实 adapter
  的构造入口与必填依赖、manifest 冻结的单入口 `_manifest_of` 今天不设 `execution_backend`、
  **ports 目录有 `openhands` token 字符串门禁**、domain 侧只有依赖门禁无字符串门禁、
  `tests/api`+`tests/e2e` 无钉死的 manifest digest、DTO 增字段需同步 OpenAPI/web types、
  `demo_session_output` 的披露只在 payload 内）。据此写死六条设计口径（选择点位置、
  配置面默认 Fake + fail-closed、选择进 manifest 的中性通道、回归对照的可执行定义、
  本 PLAN 不做真实出网、不新增依赖）。`status: IN_PROGRESS`。

## 影响报告

- **Domain/API/schema 变化**：预期**有**——`RunManifest.execution_backend` 从恒 `None`
  变为如实取值（digest 自动覆盖）；`PreflightContext` 加一个 optional 中性字段；
  读面 DTO 可能加字段（按流程同步 OpenAPI 快照 + `types.ts` + e2e 夹具）。
  **无 canonical 状态机变化、无迁移、无 Accepted ADR 变化。**
- **安全/凭据**：本 PLAN 零真实端点调用、零凭据字面量；默认仍 Fail-closed（未配置 =
  Fake）；不放松 §9 默认 deny。
- **兼容性/迁移风险**：`RunManifest` 为 frozen dataclass，新增**取值**不改结构；
  但**已冻结的旧 run** 与新 run 的 `execution_backend` 不同（旧为 `None`）——读面须能
  区分「未记录」与「记录了 Fake」，不得把 `None` 读作 Fake。
- **上游版本影响**：无（不新增依赖、不改 pin）。
- **下一项任务**：EC-02（受控出网门链）。
