---
id: PLAN-20260919-109
slug: real-runtime-offline-full-chain
title: 真实 runtime 离线全链：spec 携带执行目标 → 会话创建 → 事件映射 → 预算归账 → 制品/证据落 canonical（EC-03）
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: []
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

## 先探明再动手（待本轮只读勘察补全）

1. `SessionSpecContext`（`packages/application/run_orchestration/task_executor.py:67-77`）
   与 `AgentSessionSpec` 的字段差异 —— 补哪几个字段最小。
2. `plan.resolved_models` 的形状（agent_id → model_id）与 `ModelDefinition.endpoint_id`
   的解析路径。<!-- 待补 -->
3. 预算归账：`UsageContext` / `publish_usage` / `BudgetLedger` 在 adapter 侧已接
   （`adapters/openhands/usage_mapping.py`），要确认**控制面**是否真的把 usage 写进
   canonical。<!-- 待补 -->
4. 制品与证据：`RunContext` → artifact store / evidence ledger 的落点，Fake 链是否已覆盖，
   真实 runtime 结果如何映射。<!-- 待补 -->
5. `FakeAgentRuntime` 与真实 adapter 在 `AgentSessionResult` 上的形态差异 —— 事件映射段
   的判据要用真实 SDK 事件源还是可注入事件源。<!-- 待补 -->

## 验收条件

- **AC-01**：`RESEARCHOS_AGENT_RUNTIME=openhands` + mock 端点（离线）⇒ 一条 run 走完
  **会话创建 → 事件映射 → 预算归账 → 制品/证据落 canonical**；四段各有独立断言。
- **AC-02**：默认（未配置 runtime）路径**逐字节不变**：现有套件全绿、demo 输出不变。
- **AC-03**：执行目标解析受门——URL 被拒 / 缺 endpoint / 缺 model 绑定 ⇒ session **不创建**
  且失败原因**点名**缺失事实，出站调用 **0**。
- **AC-04**：`requires_live_llm` 门控用例在无凭据环境**如实 skip**（记录 skip，不记 PASS）。
- **AC-05**：默认门**离线可跑**：新增用例不触网（可用记录型 transport 计数佐证）。
- **AC-06**：反证——断开四段中任一段 ⇒ 对应用例红。
- **AC-07**：尺寸门 / `ruff` / `mypy` / 受影响套件 / m0 23 项绿。

## 实施清单

- [ ] **WP-A** spec 携带执行目标（中性字段）+ 解析点下沉到 `session_resolution`
- [ ] **WP-B** 解析即受门：被拒/缺失 ⇒ 任务点名失败、零出站
- [ ] **WP-C** 组合根接线 spec→LLM 工厂（凭据经 `CredentialResolver`，复用 `build_llm`）
- [ ] **WP-D** 离线全链四项判据 + 反证 + live 门控 skip 用例
- [ ] **WP-E** 文档同源（`docs/architecture/AGENT_RUNTIME.md` §3.3 / `OPENHANDS_ADAPTER.md`）

## 证据

（执行后回填。）

## 影响报告

（执行后回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 3 建档（EC-03）；先探明项 2-5 待补 |
