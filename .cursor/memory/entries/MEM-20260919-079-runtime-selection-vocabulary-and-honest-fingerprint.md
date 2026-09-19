---
id: MEM-20260919-079
title: "runtime 选择面：词表归组合层（ports 有 token 门禁）、未知取值 fail-closed、指纹槽位显式未验证而非留空"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-107-runtime-selection-surface.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-107-runtime-selection-surface.md
supersedes: []
tags:
  - agent-runtime
  - composition-root
  - dependency-boundaries
  - honesty-boundaries
  - model-drift
---

# 让 runtime 变成可配置的：三条不显然的约束

## 做了什么

GOAL-007 cycle 1（EC-01）把「组合根硬编码 `FakeAgentRuntime`、OpenHands adapter 零接线」
收敛成**配置驱动的选择面**：

- 新模块 `services/api/runtime_support.py`：`RuntimeSelection(kind, configured)` +
  `resolve_runtime_selection(settings)` + `build_agent_runtime(settings, *, selection, …)`；
- `ApiSettings.agent_runtime`（env `RESEARCHOS_AGENT_RUNTIME`，默认空串 = 未配置）；
- 两个组合根（`composition.py` / `pg_composition.py`）都经这一个装配点；
- 选择结果经 `PreflightContext.execution_substrate` 冻结进
  `RunManifest.execution_backend`，并随 `MANIFEST_FROZEN` payload 出现在既有
  `GET /runs/{id}/events` 上（零 DTO / 路由 / OpenAPI / 迁移变化）。

## 为什么这样做（三条不显然的约束，都是踩过才知道）
1. **`packages/application/ports/*.py` 有 provider token 字符串门禁**：
   `tests/contracts/test_common_contract.py::test_provider_types_do_not_leak_from_ports`
   扫该目录顶层 `.py`，禁止 `("openhands", "litellm", "lite_llm", "temporal", "openai",
   "anthropic", "adapters.")`。**`openai` 也在名单里** ⇒ 想在 Port 里放一个「runtime 取值
   词表」会在落地那一刻撞门禁。正确形态：**词表归组合层**（`services/api/**` 允许 import
   adapters），Port/Domain 只见**中性的不透明标识字符串**（`execution_backend: str | None`）。
2. **未知取值必须 fail-closed，不能静默回退默认值**：若 `RESEARCHOS_AGENT_RUNTIME=typo`
   悄悄回退成 Fake，读面上「我配了真实 runtime」与「我跑的是 demo」**不可区分**——这正是
   AGENTS.md §4 要消灭的漂移。所以装配期抛 `RuntimeConfigurationError` 并同时点名**取值**
   与**合法词表**。同理，`RuntimeSelection.configured` 让「默认」与「显式选了同一个值」
   在披露上可区分。
3. **指纹槽位要显式写「未验证」，不能留空**：受控 demo 执行体**不发起任何模型调用**，
   AGENTS.md §4 要的七件事实（ModelDefinition / endpoint 配置摘要 / 返回的 model 名 /
   系统指纹 / 白名单响应头 / probe 套件版本 / 兼容性结论）**一件也不存在**。留空会让读面
   分不清「没探」与「探了但没问题」；因此写 `{"substrate", "status": "NOT_VERIFIED",
   "reason"}`，真实事实由后续拿到 probe 结果的链路替换。

## 顺带发现的一条真缺陷（设计期，不是用例抓的）

PG 根的凭据面此前在 `build_postgres_assembly` 与 `build_postgres_apideps` **各解析一次**。
`RegistryCredentialResolver` **有状态**（`register()` 写进实例内存；API Key 从
`POST /llm-endpoints` 进来），所以两套实例会让 runtime **解析不到操作者刚注册的凭据**。
修法：把 credentials / policy / selection 收进一个 `_PgRuntimeInputs` 单实例贯穿两处；
SQLite 根同理只用 `_ControlFaces` 里那一个。**教训：装配根里"再 new 一个 resolver"看着无害，
对有状态面就是两个真相。**

## 边界（不要读成已支持真实执行）

「可装配 ≠ 可运行」。EC-01 只保证构造路径可用且**零出站**（用例用「`resolve` 即炸」的凭据
替身证明构造期连凭据都没解析）；真正跑起来还需要受控出网门链（EC-02）、离线全链（EC-03）、
以及 host shell deny 的显式配置。另外默认路径现在会冻结 `execution_backend="fake"` 与一条
`NOT_VERIFIED` 记录 ⇒ **manifest digest 与改动前不同**（加性披露，不是行为回归）；
旧 run 的 `None` 必须读作「未声明」，**不得**读作某个具体执行体。

## 怎么做与复现

```python
# 选择面（组合层；两个组合根都只经这一个点）
from services.api.runtime_support import resolve_runtime_selection, build_agent_runtime
selection = resolve_runtime_selection(settings)   # 未知取值 -> RuntimeConfigurationError
runtime = build_agent_runtime(settings, selection=selection, credentials=..., policy_evaluator=...)
```

- 默认（`RESEARCHOS_AGENT_RUNTIME` 未设）⇒ `RuntimeSelection(kind="fake", configured=False)`
  ⇒ 受控 demo 执行体，`demo_session_output()` 逐字段不变。
- `RESEARCHOS_AGENT_RUNTIME=openhands` ⇒ `OpenHandsRuntimeAdapter`（构造期不解析凭据、不出网）；
  缺 `credential_resolver` / `policy_evaluator` 时抛 `RuntimeConfigurationError` 并**点名缺项**。
- 选择结果落 `RunManifest.execution_backend`（经 `PreflightContext.execution_substrate`），
  读面 = 既有 `GET /runs/{id}/events` 的 `MANIFEST_FROZEN` payload 里的 `execution_backend`。

判据：`tests/api/test_runtime_selection_surface.py`（13 条，含组合根 AST 结构判据与
两条 manifest/读面判据）。反证配方（四条，各跑一次即可复现）：

| 注入 | 期望 |
| --- | --- |
| 组合根改回 `FakeAgentRuntime(structured_output=demo_session_output())` | 结构判据红（AST 数到 1 处） |
| `build_agent_runtime` 的 openhands 分支改成 `return _fake_runtime()` | 选择/拒绝两条红 |
| 未知取值改成静默 `return RuntimeSelection(kind=FAKE_RUNTIME, configured=False)` | `DID NOT RAISE` |
| `_manifest_of` 去掉 `execution_backend=context.execution_substrate` | manifest/读面两条红 |

## 适用边界（踩过的坑）

- **不要**在 `packages/application/ports/**` 或 `packages/domain/**` 放 runtime 取值词表
  ——ports 有 token 字符串门禁（含 `openai`），domain 有「厂商不进 Domain」的边界。
- **不要**把「未知取值」做成回退默认值：那是把配置错误变成静默的 demo 运行。
- **不要**把 `model_runtime_fingerprints` 留空来「表示没探」：留空与「探了没问题」不可区分。
- **不要**在读面上把 `execution_backend is None` 读成某个执行体（旧 run 没有这个事实）。
- **不要**在装配根里对**有状态**的面（`RegistryCredentialResolver`）再 new 一个：
  两个实例就是两个真相，runtime 会解析不到刚注册的凭据。
- **不要**把「能装配」读成「能跑」：门链（EC-02）、离线全链（EC-03）与 host shell deny 的
  显式配置都没做之前，真实 runtime 只是「装得上」。
- 单独跑 `tests/api/test_worker_plane_composition.py` 时 3 条 `@pytest.mark.postgres` 用例会
  **真连 PG**（只有加载 `tests/postgres/conftest.py` 时才按标记 skip）——这是既有口径，
  不是回归；跑 m0 全量时在射程内。

## 来源

- PLAN：`.cursor/plans/tasks/PLAN-20260919-107-runtime-selection-surface.md`
- RECHECK：`.cursor/plans/rechecks/RECHECK-20260919-107-runtime-selection-surface.md`
  （PASS_WITH_WARNINGS，W-1…W-6）
- 代码：`services/api/runtime_support.py`、`services/api/composition.py`、
  `services/api/pg_composition.py`、`packages/application/ports/resource_catalog.py`
  （`PreflightContext.execution_substrate` / `runtime_fingerprints`）、
  `packages/application/preflight/preflight.py::_manifest_of`、
  `packages/application/run_orchestration/eventing.py::frozen_payload`
- 上游约束：AGENTS.md §1（用户 LLM 接入）/ §4（模型同名漂移可见性）/
  §5（OpenHands 约束：类型不进 Domain、工具面必须过 Policy Wrapper）/ §9（默认 deny）
- 关联：[[MEM-20260918-074]]、[[MEM-20260918-078]]
