---
id: PLAN-20260919-109
slug: real-runtime-offline-full-chain
title: 真实 runtime 离线全链：spec 携带执行目标 → 会话创建 → 事件映射 → 预算归账 → 制品/证据落 canonical（EC-03）
status: DONE
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 3 = EC-03。授权来源：2026-09-19 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；受控出网边界与 push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`。本 PLAN 遵守：默认 runtime 保持 Fake、不引入新依赖、凭据只从环境变量/密钥服务读、真实端点调用永不进默认 CI、默认 deny 姿态不得放松、不改上游 pin。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260919-109-real-runtime-offline-full-chain.md
memory_entries:
  - .cursor/memory/entries/MEM-20260919-081-real-runtime-offline-full-chain.md
---

# PLAN-20260919-109 — 真实 runtime 离线全链（GOAL-007 cycle 3 = EC-03）

## 目标

让「选了真实 runtime」在**默认门里**跑通一条端到端链，且**不依赖网络、不依赖真实凭据**：

```text
脚本化 mock 端点 → 会话创建 → 事件映射进 canonical → 预算归账 → 制品/证据落 canonical
```

今天这条链在**第一段之前**就断了，而且是**结构性**的（cycle 2 勘察确认）：

| 事实 | 现状 |
| --- | --- |
| `AgentSessionSpec` 携带什么 | 只有任务的**控制面**事实（task/role/agent/tool set/manifest ref），**不携带** endpoint / model / 凭据（`packages/application/ports/agent_runtime.py:28-40`） |
| 生产如何给 session 造 LLM | `AdapterDependencies.build_llm` 被塞入 **3 参工厂** `build_llm(endpoint, model, credential)`，而 `SessionBuilder.build_session` 按 **1 参** `self._build_llm(spec)` 调用（`adapters/openhands/session_builder.py:60`） |
| 后果 | 选 `openhands` 时 `create_session` 在 `TypeError` 上收敛为 `PermanentPortError(SYSTEM_BUG)`（`adapters/openhands/error_mapping.py:111-116`）——**不是**「未接线」，是「一调用就炸」 |
| 已有的可复用资产 | `tests/adapters/openhands/test_spike_e2e.py` 已用**本地 threading HTTP 服务器**驱动真实 `build_llm` + 真实 `OpenAISDK Conversation` 跑通「mock 端点 → 会话 → 事件 → 结果」；EC-03 要补的是**控制面那一段**（domain spec → 执行目标 → 该工厂），以及归账/制品/证据落 canonical |

因此本 PLAN 的**第一件事**是把 session 期的执行目标**显式化并受门**，而不是在 adapter 里
偷偷读环境。

## 口径

- **执行目标在 catalog 可用的地方解析**（`session_resolution.resolve_sessions` 有
  `context.catalog` 与 `context.plan.resolved_models`），**不在 adapter 里解析**：
  adapter 不得反向依赖 catalog，也不得自行读环境/策略。
- **解析即受门**：URL 策略裁决复用 cycle 2 的 `endpoint_url_refusal`（**不新造第二份
  host 判据**）；被拒或缺 endpoint/model/凭据绑定 ⇒ 该 session **不创建**，任务以
  **点名**的失败原因收敛，**零出站**。
- **spec 是 Port 类型**：新字段必须保持中性命名（`ports` 有 provider token 门禁
  `test_provider_types_do_not_leak_from_ports`），不得出现厂商名/SDK 名。
- **凭据值不进 spec**：spec 只带 `credential_ref`（键名）；值在 adapter 侧经
  `CredentialResolver` 取，且不写日志/事件。
- **离线全链四段各自可判定**：会话创建 / 事件映射 / 预算归账 / 制品与证据落 canonical，
  任一段断开都要能让对应用例红。
- **live 门控如实 skip**：真端点 E2E 走 `requires_live_llm`，无凭据环境 skip 并记录
  skip 事实，**不记 PASS**；不得为它申请凭据、不得用假凭据冒充。

## 先探明再动手

1. `SessionSpecContext`（`packages/application/run_orchestration/task_executor.py:67-77`）
   与 `AgentSessionSpec` 的字段差异 —— **结论**：最小补两个字段
   `endpoint: LLMEndpoint | None` 与 `model: ModelDefinition | None`；其余
   （task/role/agent/tool set/manifest ref）已由既有字段覆盖。
2. `plan.resolved_models` 的形状与 `ModelDefinition.endpoint_id` 的解析路径 ——
   **结论**：`plan.resolved_models` 是 `agent_id → model_id`（与
   `RunManifest.resolved_models` 同源）；解析链为
   `catalog.models[model_id].endpoint_id → catalog.endpoints[...]`。逐段独立收敛为
   `None`，不回退、不编造。
3. 预算归账：控制面是否真的把 usage 写进 canonical —— **结论**：adapter 侧
   `SessionBuilder.record_usage` → `usage_mapping.publish_usage` →
   `BudgetLedger.record_usage`；编排与读取端共享同一账本实例。e2e 读到的是
   **可归因**的 `MODEL_TOKENS` 条目（数量为正、`task_id` 属本 run、
   `model_id` 属目录绑定），不是"账本非空"。缺口：`UsageContext` 此前不填
   `model_id` ⇒ 本 PLAN 补上（spec 携带目标后该事实在 adapter 侧可见）。
4. 制品与证据：落点与真实结果映射 —— **结论**：
   `result_handler.register_session_result` 由**结构化输出**驱动（空 ⇒
   `InvalidInputError`），经 `ArtifactStore.put` + `EvidenceLedger.register_*`
   落 canonical，读面是 `GET /runs/{id}/artifacts|evidence` 与
   `/artifacts/{id}/content`。真实 adapter 此前**不携带** `structured_output`
   ⇒ 第四段结构性断开；本 PLAN 的 `_deliverable` 映射补上这一环（见 WP-D）。
5. `FakeAgentRuntime` 与真实 adapter 在 `AgentSessionResult` 上的形态差异 ——
   **结论**：映射段要用**真实 SDK 事件源**（不可注入替身），因为要证的正是
   「真实事件树 → RuntimeEvent → canonical」；可判窗口只有一处——制品载荷里的
   `message_count` / `session_id`（canonical 事件表不落 session 级事件，
   `RunEvent.agent_session_id` 字段今日无写入方）。这一重叠（第 2 段与第 4 段
   共享同一个可观测窗口）已如实写进 RECHECK。

## 验收条件

- [x] **AC-01**：`RESEARCHOS_AGENT_RUNTIME=openhands` + mock 端点（离线）⇒ 一条 run 走完
  **会话创建 → 事件映射 → 预算归账 → 制品/证据落 canonical**；四段各有独立断言。
- [x] **AC-02**：默认（未配置 runtime）路径**逐字节不变**：现有套件全绿、demo 输出不变。
- [x] **AC-03**：执行目标解析受门——URL 被拒 / 缺 endpoint / 缺 model 绑定 ⇒ session **不创建**
  且失败原因**点名**缺失事实，出站调用 **0**。
- [x] **AC-04**：`requires_live_llm` 门控用例在无凭据环境**如实 skip**（记录 skip，不记 PASS）。
- [x] **AC-05**：默认门**离线可跑**：新增用例不触网（mock 端点是本机回环；无真端点/凭据/外网）。
- [x] **AC-06**：反证——断开四段中任一段 ⇒ 对应用例红（F1..F4，见 RECHECK）。
- [x] **AC-07**：尺寸门 / `ruff` / `mypy` / 受影响套件 / m0 23 项绿。

## 实施清单

- [x] **WP-A** spec 携带执行目标（中性字段）+ 解析点下沉到 `session_resolution`
- [x] **WP-B** 解析即受门：被拒/缺失 ⇒ 任务点名失败、零出站
- [x] **WP-C** 组合根接线 spec→LLM 工厂（凭据经 `CredentialResolver`，复用 `build_llm`）
- [x] **WP-D** 离线全链四项判据 + 反证 + live 门控 skip 用例
- [x] **WP-E** 文档同源（`docs/architecture/AGENT_RUNTIME.md` §3.3 / `OPENHANDS_ADAPTER.md`）

## 证据

| 判据 | 命令 | 结果 |
| --- | --- | --- |
| 离线全链四段 + live skip | `pytest tests/e2e/test_ec03_real_runtime_offline_chain.py -q -rs` | **2 passed / 1 skipped**（skip 原因：缺 `RESEARCHOS_LIVE_E2E_ENDPOINT` / `_KEY`） |
| 执行目标解析与受门工厂 | `pytest tests/api/test_session_llm_factory.py -q` | **10 passed** |
| 反证 F1..F4 | 四处注入各跑一次 | 全红且各自可控（见 RECHECK-20260919-109 反证表）；注入已复原 |
| 尺寸门 | `pytest tests/tooling/test_python_source_limits.py -q` | **947 passed**（首跑红：三个超 50 行函数，已拆分） |
| 受影响套件 | `pytest tests/adapters/openhands tests/application tests/architecture` / `tests/api` / `tests/e2e` | **765 passed / 1 skipped** / **482 passed** / 全绿 |
| 静态门 | `ruff check` / `ruff format --check` / `mypy` | 绿 / 绿 / **937 files, no issues** |
| m0 | `run_all_checks.py --profile m0 --keep-going` | 见 GOAL-20260919-007 循环日志 cycle 3 |

## 影响报告

- **Domain / API / schema**：无变化。`AgentSessionSpec` 的两个新字段是 **Port 类型的中性
  Domain 引用**（`LLMEndpoint` / `ModelDefinition`），不是新 DTO；无 OpenAPI / web types /
  e2e 夹具变化，无迁移。
- **安全 / 凭据**：凭据只以 `credential_ref`（键名）进 spec，值在 adapter 侧经
  `CredentialResolver` 取（复用既有面）；新增拒绝路径**零出站**；真实端点调用只在
  `requires_live_llm` 门控下发生，默认 CI 不触网。新增 `RESEARCHOS_WORKSPACE_ALLOW_HOST_SHELL`
  开发开关，**默认 `0` = deny**，默认姿态未放松。
- **兼容性 / 迁移**：默认路径（runtime 未配置 ⇒ Fake）不受影响——Fake 不读新字段，
  有专门回归用例（`test_fake_path_ignores_the_new_fields`）。既有 adapter 测试全绿。
- **上游 / 依赖**：无新依赖、无 pin 变更、无 Fork（AGENTS.md §12 未触发）。
- **残留（如实登记，不阻断）**：provider → SDK 工具映射缺失（EC-05 的活，行为已测量并点名）；
  live 用例本机只证明 skip 路径；会话级事件不进 canonical（段 2/段 4 共享制品窗口）；
  「真实 runtime 会话」目前需显式打开 host shell 开关。详见 RECHECK 的 W-1..W-6。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 3 建档（EC-03）；先探明项 2-5 待补 |
| 2026-09-19 | IN_PROGRESS | 勘察结论回填（探明项 1-5）；WP-A..WP-C 落地；e2e 与工厂用例首跑红后修绿 |
| 2026-09-19 | DONE | WP-D 反证 F1..F4 完成并复原；WP-E 文档同源；尺寸门首跑红 → 拆分转绿；RECHECK-20260919-109 = PASS_WITH_WARNINGS |
