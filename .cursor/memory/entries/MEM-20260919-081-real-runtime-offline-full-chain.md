---
id: MEM-20260919-081
title: "真实 runtime 的离线全链配方：执行目标必须进 spec（3 参工厂对 1 参调用 = 一调用就炸）；canonical 不落 session 级事件，映射段只能经 artifact 判"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-109-real-runtime-offline-full-chain.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-109-real-runtime-offline-full-chain.md
supersedes: []
tags:
  - agent-runtime
  - openhands-adapter
  - offline-e2e
  - execution-target
  - observability-window
  - falsification
---

# 真实 runtime 离线全链（GOAL-20260919-007 / EC-03）

## 做了什么

让「选了真实 runtime」在**默认门里**（离线、无凭据、无外网）跑通一条端到端链：

```text
execution_target（orchestration，catalog 在手处）
  → AgentSessionSpec.endpoint / .model（Domain 类型；只带 credential_ref）
  → session_llm_factory（URL 策略 → 凭据存在性 → build_llm；拒绝在构造之前）
  → _deliverable（SUCCEEDED 才产出：已映射的 MESSAGE 文本 + message_count + session_id）
  → 既有登记链（artifact → evidence → PROPOSED claim）→ acceptance gate 裁决
```

- `packages/application/run_orchestration/session_resolution.py`：`execution_target`（纯映射）。
- `packages/application/ports/agent_runtime.py`：`AgentSessionSpec.endpoint/.model`。
- `services/api/runtime_support.py`：`session_llm_factory` + `_gated_session_target`。
- `adapters/openhands/runtime_adapter.py`：`_deliverable`；`session_builder.record_usage` 补 `model_id` 归因。
- 判据：`tests/e2e/test_ec03_real_runtime_offline_chain.py`、`tests/api/test_session_llm_factory.py`。

## 为什么这样做

1. **断点原本是结构性的，不是配置问题**。三处：① `AgentSessionSpec` 不携带
   endpoint/model ⇒ 真实 adapter 没有执行目标；② 生产把 **3 参** `build_llm` 塞进
   `AdapterDependencies.build_llm`，而 `SessionBuilder.build_session` 按 **1 参**
   `self._build_llm(spec)` 调用 ⇒ `create_session` 必然 `TypeError`（收敛为
   `PermanentPortError(SYSTEM_BUG)`）——**不是「未接线」，是「一调用就炸」**；
   ③ 真实 adapter 的 `AgentSessionResult` 不携带 `structured_output`，而 canonical 的
   制品/证据登记由结构化输出驱动 ⇒ 第四段从来不可达。
   **教训**：Port 的依赖是 callable 时，接线处的**元数/契约**必须由一条**真的调用它**的
   用例来判；「装上了」与「调得通」是两件事。
2. **解析点在 catalog 在手的层**（orchestration），adapter 只消费。解析是纯映射，三段
   各自独立收敛为 `None`；有 model 而 endpoint 不在目录时返回 `(None, model)`，拒绝消息
   才能精确到「缺 endpoint」。不回落别的 model、不编造 endpoint（AGENTS.md §4）。
3. **解析即受门，且复用同一份 host 判据**（`endpoint_url_refusal`）——不新造第二份；
   拒绝发生在**构造 LLM 之前**，因此零出站。
4. **交付物只从已映射事件取**：`_deliverable` 的文本来自 `RuntimeEvent.MESSAGE`
   （已过 `event_mapping` 的 redact/截断），不新开绕过脱敏的通道；非成功终态返回空
   （把失败会话的中间文本登记成结论 = 把「没做完」伪装成「有产出」）。

## 怎么做与复现

- 判据：`uv run --frozen --no-sync python -B -m pytest tests/e2e/test_ec03_real_runtime_offline_chain.py -q`
  ⇒ **2 passed / 1 skipped**（skip = `requires_live_llm` 且无凭据，原因点名环境变量）。
- 离线跑真实 adapter 需要**三件显式开关/替身**（缺任何一件都会红，且失败消息点名）：
  1. `allow_localhost_endpoints=True` + `EndpointUrlPolicy(allow_localhost=True)`
     ——mock 端点在 `127.0.0.1`，默认策略拒绝；
  2. `workspace_allow_host_shell=True`（`build_local_workspace` 在 `allow_host_shell=False`
     时**拒绝构造**，「可装配」与「可运行」因此分开）；
  3. **provider → SDK 工具注册**：冻结 Tool Set 里是 tool provider id，缺映射时会话创建
     失败并点名未注册的 id（测试侧用惰性工具补这一环；生产缺这一环的行为有专门用例固定）。
- mock 端点用 `threading.HTTPServer(("127.0.0.1", 0), handler)`，实现
  `GET /models` + `POST /v1/chat/completions`（含 usage 12/3/15）。
- **四段判据与各自的反证**（记录在 RECHECK-20260919-109）：
  1. 会话创建：mock 真的收到补全请求 + 线上 model 名来自目录绑定（F1：目标恒 None ⇒ 红）；
  2. 事件映射：artifact 载荷的 `message_count`/`session_id`（F2：断映射 ⇒ 红）；
  3. 预算归账：账本里有正向 `MODEL_TOKENS` 且 `task_id`/`model_id` 归因正确（F3：不写账本 ⇒ 红）；
  4. 制品与证据：`/artifacts`、`/evidence` 非空并由 acceptance gate 裁决（F4：空登记 ⇒ 红）。

## 适用边界（踩过的坑）

- **canonical 事件表不落 session 级事件**（`RunEvent.agent_session_id` 今日无写入方），
  所以「事件映射」段的唯一可判窗口是**制品载荷**；段 2 与段 4 因此共享同一窗口。
  断言顺序上段 2 先撞，两者可用 run 的失败消息区分：F2 ⇒ `carries no structured output`，
  F4 ⇒ 仍走到 `rejected by acceptance gate`。
- **链的实测终点是判拒**：合约要 `analysis_report`，真实会话交付 `session_message`，
  acceptance gate 判拒——这是链在正常工作。键名→合约 artifact 名的映射是 `tool_pack.*`
  产品决策，adapter 不自行发明键名。
- **live 用例只是如实 skip**（无凭据环境），`requires_live_llm` 的 skip **不是** PASS；
  跑它需要 `RESEARCHOS_LIVE_E2E_ENDPOINT` + `RESEARCHOS_LIVE_E2E_KEY`（只从环境读）。
- **`mypy` 侧**：`ApiDeps.credentials` 声明为 Port 而 fixture 注入 Fake 时，
  `.register(...)` 需要 `cast(FakeCredentialResolver, ...)`；`TestClient` 的 `.json()`
  返回 `Any`，放进 typed 返回要 `cast`。
- **本地跑全套的 DSN 污染**：`tests/api` 里几个组合根用例会因 litellm 注入 operator `.env`
  的 DSN 而失败（`password authentication failed`）——
  用 `RESEARCHOS_POSTGRES_DSN=<test DSN>` 钉住即绿；不是代码回归。
- **尺寸门**：`runtime_support.py` 的工厂 54 行、e2e 的 `_openhands_deps` 83 行、四段用例
  66 行都超过 50 行函数上限，**首跑就红**；拆成 `_gated_session_target` / `_point_catalog_at`
  + `_register_live_key` + `_real_runtime` / 四个 `_assert_*` 段函数后转绿。

## 来源

- `.cursor/plans/tasks/PLAN-20260919-109-real-runtime-offline-full-chain.md`
- `.cursor/plans/rechecks/RECHECK-20260919-109-real-runtime-offline-full-chain.md`
- 代码：`packages/application/run_orchestration/session_resolution.py`、
  `services/api/runtime_support.py`、`adapters/openhands/runtime_adapter.py`、
  `adapters/openhands/session_builder.py`
- 判据：`tests/e2e/test_ec03_real_runtime_offline_chain.py`、
  `tests/api/test_session_llm_factory.py`
- 文档：`docs/architecture/AGENT_RUNTIME.md` §3.3、`docs/integration/OPENHANDS_ADAPTER.md`
