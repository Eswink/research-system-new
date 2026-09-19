---
id: RECHECK-20260919-107
plan_id: PLAN-20260919-107
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle1
baseline_ref: f0f7114
checked_head: WORKTREE
---

# RECHECK-20260919-107 — Runtime 选择面（GOAL-20260919-007 cycle 1 = EC-01）

## 检查范围

EC-01 的四条可判事实逐条对表（每条都要**实跑**证据，不认「文档已写明」）：

| EC-01 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| 配置驱动的 `Fake \| OpenHands` 选择 | `services/api/runtime_support.py`（`resolve_runtime_selection` / `build_agent_runtime`；词表 `fake` / `openhands`）+ `ApiSettings.agent_runtime`（`RESEARCHOS_AGENT_RUNTIME`） | `tests/api/test_runtime_selection_surface.py`（13 passed） |
| **两个组合根同侧** | `composition._sqlite_orchestration` 与 `pg_composition._build_pg_orchestration` 都经同一函数；组合根里 `FakeAgentRuntime(...)` 直接构造归零 | `::test_no_composition_root_builds_the_fake_runtime_directly`（AST 数调用点）+ `::test_composition_roots_call_the_one_selection_point` |
| **未配置时与今日一致** | 默认路径仍构造受控 demo 执行体、仍用同一 `demo_session_output()` | `::test_unconfigured_settings_select_the_controlled_demo_runtime` + `::test_demo_session_output_is_unchanged` + 受影响套件 |
| 选择结果与**运行时指纹**进 manifest / 读面 | `PreflightContext.execution_substrate` / `runtime_fingerprints` → `_manifest_of` → `RunManifest.execution_backend` / `model_runtime_fingerprints`；`MANIFEST_FROZEN` payload 带 `execution_backend` | `::test_frozen_manifest_records_the_selected_substrate`、`::test_frozen_manifest_stays_undeclared_without_a_selection`、`::test_runtime_fingerprints_are_explicitly_not_verified`、`::test_frozen_event_payload_carries_the_substrate_to_the_read_face` |
| 未知取值不静默回退 | 装配期 `RuntimeConfigurationError` 点名取值 | `::test_unknown_runtime_fails_closed_naming_the_value` |
| **反证**（拆掉任一环 ⇒ 判据红） | 四条注入各跑一次 | 见「反证与实测」 |

**不在本 EC 射程内**（如实登记，不伪装已收口）：受控出网门链（EC-02，本轮只到「缺面点名拒绝」
与「构造期不解析凭据」）、离线全链（EC-03）、UI 披露（EC-04）、工具面边界（EC-05）、
`tool_pack.*`（EC-06）。

## 检查结果

### 选择面的真实形状

- `RuntimeSelection(kind, configured)`：`kind ∈ {fake, openhands}`；`configured` 区分
  「默认」与「显式选了同一个值」——读面因此不会把两者混成一句话。
- **未知取值 fail-closed**：`resolve_runtime_selection` 对非空且不在词表内的取值抛
  `RuntimeConfigurationError`，消息里同时点名**取值**与**合法词表**。这是有意选的口径：
  静默回退会让「我配了真实 runtime」与「我跑的是 demo」在读面上不可区分，正是
  AGENTS.md §4 要消灭的漂移。
- **`openhands` 分支的必填面**：`credential_resolver` 与 `policy_evaluator` 缺**任一**即
  **点名拒绝**（消息列出缺的那几项）。理由是 AGENTS.md §5：不受 Policy Wrapper 约束的
  真实 runtime 不允许被装配出来。
- **构造期零出站**：`OpenHandsRuntimeAdapter.__init__` 只建 `SessionBuilder` 并存依赖；
  用例用「`resolve` 即炸」的凭据替身证明**构造期连凭据都没解析**。
- **默认 deny 不放松**：`build_workspace` 传的是 `build_local_workspace` **不带**
  `allow_host_shell=True`，即 host shell 仍按 §9 默认 deny；真实 runtime 因此「可装配、
  但会话创建仍受约束」。

### 选择结果的读面载体（零 DTO / 路由 / OpenAPI / 迁移变化）

- `PreflightContext` 新增两个**中性命名**字段（`execution_substrate` / `runtime_fingerprints`）
  ——命名受既有门禁约束：`test_provider_types_do_not_leak_from_ports` 扫描
  `packages/application/ports/*.py`，禁止 token `openhands` / `openai` / `litellm` / …，
  所以词表只能留在组合层，Port/Domain 只见中性的基质标识字符串。
- `_manifest_of` 把它写进 `RunManifest.execution_backend`（M7 声明过、此前**恒为 None**）。
- `MANIFEST_FROZEN` payload 增 `execution_backend` ⇒ 读面走**既有**
  `GET /runs/{id}/events`（与 GOAL-006 EC-06 同一形态）。
- **诚实边界**：`None` = 冻结时未声明（M7「不伪填充」口径），**不得**读作「这是 Fake」。

### 运行时指纹槽位：显式未验证，而不是留空

`RuntimeSelection.fingerprint_record()` 给出 `{"substrate", "status": "NOT_VERIFIED", "reason"}`。
理由写在代码注释与 RECHECK 里：默认的受控 demo 执行体**不发起任何模型调用**，AGENTS.md §4
要的七件事实一件也不存在；**留空**会让读面分不清「没探」与「探了但没问题」。真实事实由
EC-02 的门链与 EC-03 的离线全链在拿到 probe 结果后替换。**本 EC 不宣称任何 §4 事实已验证。**

### 一处**声明与事实不符**的收敛（本轮更正）

`packages/domain/manifest.py` 的 M7 边界注释原写：

> `execution_backend` / `environment`（runtime 装配由 OpenHandsRuntimeAdapter 决定，
> adapter 不反向上报执行环境标识）

而事实是：两个组合根**硬编码** `FakeAgentRuntime`，`OpenHandsRuntimeAdapter` 在
`services/`/`packages/`（非 docstring）下**零引用**（`rg` 可复核），该字段因此恒为 `None`。
本轮把这条注释改成事实（装配点唯一且如实上报），并把同一口径写进
`docs/architecture/AGENT_RUNTIME.md` 的新 §3.1（含「本节不宣称的部分」）。

### 顺带修好的一条**同实例**缺陷（PG 根）

PG 根的凭据面此前在 `build_postgres_assembly` 与 `build_postgres_apideps` **各解析一次**。
`RegistryCredentialResolver` 是**有状态的**（`register()` 写进实例内存，API Key 从
`POST /llm-endpoints` 进来），两套会让 runtime 解析不到操作者刚注册的凭据。本轮把它收敛成
`_PgRuntimeInputs`（credentials / policy / selection）单实例贯穿两处；SQLite 根同样只用
`_ControlFaces` 里那一个实例。**这条是设计期发现，不是被用例抓出来的**——如实记录。

## 反证与实测

四条注入**逐条实跑**（先红后复原，`git status --short` 每次复原后干净）：

| # | 注入 | 实测结果 |
| --- | --- | --- |
| ① | `pg_composition._build_pg_orchestration` 改回硬编码 `FakeAgentRuntime(structured_output=demo_session_output())` | `test_no_composition_root_builds_the_fake_runtime_directly` **红**：`1 failed, 12 passed` |
| ② | `build_agent_runtime` 的 openhands 分支短路成 `return _fake_runtime()` | `::test_openhands_selection_constructs_the_real_adapter_offline` + `::test_openhands_without_required_faces_names_what_is_missing` **红**：`2 failed, 11 passed` |
| ③ | 未知取值改成 `return RuntimeSelection(kind=FAKE_RUNTIME, configured=False)` | `::test_unknown_runtime_fails_closed_naming_the_value` **红**：`Failed: DID NOT RAISE RuntimeConfigurationError` |
| ④ | `_manifest_of` 去掉 `execution_backend=context.execution_substrate` | `::test_frozen_manifest_records_the_selected_substrate` + `::test_frozen_event_payload_carries_the_substrate_to_the_read_face` **红**：`AssertionError: assert None == 'openhands'` |

复原后 `tests/api/test_runtime_selection_surface.py` **13 passed**，工作树干净。

## 告警（W）

- **W-1「未配置时逐字节一致」的口径是加性的，不是字面的**：默认路径现在会冻结
  `execution_backend="fake"` 与一条 `NOT_VERIFIED` 指纹记录 ⇒ **manifest digest 与改动前
  不同**。这是 EC-01 自身要求（「选择结果进 manifest」）的直接后果，本 RECHECK 点名而不粉饰。
  可执行口径 = `demo_session_output()` 逐字段不变 + 受影响套件全绿（都实跑）。
- **W-2 已冻结的旧 run 与新 run 不可直接比**：旧 run 的 `execution_backend` 是 `None`、
  新 run 是 `"fake"`/`"openhands"`。读面必须把 `None` 读作「未声明」而不是某个执行体
  （判据里有专门一条钉这个边界）。
- **W-3「真实 runtime 可用」远未成立**：EC-01 只到「可装配 + 可判 + 零出站」。真正跑起来
  需要门链（EC-02）、离线全链（EC-03）与 host shell deny 的显式配置，**都还没做**。
- **W-4 OpenHands SDK 导入横幅**：选中 `openhands` 时 `adapters.openhands` 的导入会打印
  SDK 横幅（`OPENHANDS_SUPPRESS_BANNER` 未设）。默认路径不受影响（import 是惰性的）；
  属既有行为，本轮未改，登记为噪声项。
- **W-5 `RuntimeSelection` 只在 `ApiDeps` 上，不在 Worker 平面**：`worker_gateway`
  组合面不构造 runtime，因此不受影响；但「两个组合根同侧」这条判据的射程**只覆盖
  SQLite/PG 两条控制面路径**，写成显式边界。
- **W-6 指纹槽位仍是占位**：`model_runtime_fingerprints` 在本路径写的是 `NOT_VERIFIED`
  记录，不是 §4 的七件事实。**不得**把它读作已做模型漂移校验。

## 结论

**PASS_WITH_WARNINGS。** EC-01 的四条要求全部有**实跑**判据（13 条用例）与**四条先红后复原**
的反证支撑；两个组合根确实收敛到同一个选择点；默认路径的受控 demo 行为逐字段不变；
未知取值不静默回退；选择结果与（显式未验证的）指纹状态都进了 manifest 并经既有事件读面可判。
同时如实登记了五条 W（其中 W-1/W-3 是最需要读者注意的两条：manifest digest 有意的加性变化、
以及「可装配 ≠ 可运行」）。**本 RECHECK 不构成「产品已支持真实 LLM 执行」的结论。**

## 门禁

- `tests/api/test_runtime_selection_surface.py`：**13 passed**。
- 受影响套件：`tests/api tests/architecture/python tests/tooling`（DSN pin 配方）——
  除 3 条 `@pytest.mark.postgres` 用例因**单独跑该文件不加载 `tests/postgres/conftest.py`**
  而真连 PG 失败（既有口径，非回归）外全绿；m0 全量跑时该 conftest 在射程内。
- 规模门禁 `tests/tooling/test_python_source_limits.py`：**944 passed**，零超限。
- `ruff check` / `ruff format --check`：绿。`mypy`：**934 source files, no issues**。
- **m0 全量**：`PASS: profile=m0; 23 deterministic checks`（`3803 passed, 200 skipped`，
  539.63s）；DOCS-CHECK PASS。
- CI：本次推送的 run 见回合汇报（GOAL 台账闭合约定；本条回写提交自身的 run 按同一约定
  在回合汇报给出终态）。
