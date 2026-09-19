---
id: RECHECK-20260919-109
plan_id: PLAN-20260919-109
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-19
completed_at: 2026-09-19
reviewer: root-agent-goal-007-cycle3
baseline_ref: 9bb468f
checked_head: WORKTREE
---

# RECHECK-20260919-109 — 真实 runtime 离线全链（GOAL-20260919-007 cycle 3 = EC-03）

## 检查范围

EC-03 的四条可判事实逐条对表（每条都要**实跑**证据）：

| EC-03 要求 | 交付 | 判据（可复核） |
| --- | --- | --- |
| 脚本化 mock 端点驱动**真实 adapter**（不是 Fake 冒充） | `tests/e2e/test_ec03_real_runtime_offline_chain.py::mock_relay`（本机 `threading` HTTPServer）+ `build_agent_runtime(agent_runtime=openhands)` | `::test_real_runtime_offline_chain_segments` 段 1：mock 端点**真的收到**补全请求，且线上 model 名来自目录绑定 |
| **会话创建 / 事件映射 / 预算归账 / 制品与证据落 canonical** 四段各自可判 | 段 1..4 由 `_assert_session_created` / `_assert_events_mapped` / `_assert_usage_attributed` / `_assert_deliverable_adjudicated` 分别断言 | 同上一用例的四段；段 2 读 `/artifacts/{id}/content`，段 4 读 `/evidence`、`/artifacts` 与 `run.failed` 消息 |
| **反证**：断开事件映射 / 断开归账 / 断开制品落库各自 ⇒ 对应用例红 | 四处注入各跑一次 | 见「反证与实测」F1..F4 |
| `requires_live_llm` 门控的真实端点手动 E2E，凭据不在环境时**如实 skip**（不记 PASS） | `::test_live_endpoint_is_exercised_only_when_credentials_are_configured` | 默认环境实跑：**1 skipped**（skip 原因点名两个环境变量） |
| 默认门**离线可跑**（无网络依赖） | mock 端点是 loopback；无真端点、无凭据、无外网 | `_MockRelayHandler.requests` 是唯一出网点；用例在本机与 CI 均不触公网 |
| m0 绿 | 见「门禁」 | 见「门禁」 |

## 检查结果

### 断点原本在哪（结构，不是配置）

cycle 2 勘察确认这条链在**第一段之前**就断了，且是三处**结构性**断点：

1. `AgentSessionSpec` 只携带控制面事实（task/role/agent/tool set/manifest ref），
   **不携带** endpoint / model ⇒ 真实 adapter 没有可用的执行目标。
2. 生产把 **3 参**工厂 `build_llm(endpoint, model, credential)` 塞进
   `AdapterDependencies.build_llm`，而 `SessionBuilder.build_session` 按 **1 参**
   `self._build_llm(spec)` 调用 ⇒ 选 `openhands` 时 `create_session` 必然 `TypeError`
   （收敛为 `PermanentPortError(SYSTEM_BUG)`）。这不是「未接线」，是「一调用就炸」。
3. 真实 adapter 的 `AgentSessionResult` **不携带** `structured_output`，而 canonical 的
   制品/证据登记正是由结构化输出驱动的 ⇒ 第四段（制品落库）从来不可达。

### 三段各自怎么补的

```text
execution_target（orchestration，catalog 在手处）
  → AgentSessionSpec.endpoint / .model（Domain 类型；只带 credential_ref）
  → session_llm_factory（URL 策略 → 凭据存在性 → build_llm；拒绝在构造之前）
  → _deliverable（SUCCEEDED 才产出：已映射的 MESSAGE 文本 + message_count + session_id）
  → 既有登记链（artifact → evidence → PROPOSED claim）→ acceptance gate 裁决
```

- **解析点下沉到 orchestration 而非 adapter**：`session_resolution.execution_target`
  是纯映射（有专门用例证明它不读环境、不读文件），adapter 不反向依赖 catalog。
- **解析即受门，且是同一份 host 判据**：工厂复用 cycle 2 的
  `endpoint_url_refusal`（不新造第二份 host 分类），拒绝消息点名缺哪一条事实。
- **交付物只从已映射事件取**：`_deliverable` 的文本来自 `RuntimeEvent.MESSAGE`，
  即已经过 `event_mapping` 的 redact/截断，不新开一条绕过脱敏的通道；非成功终态返回空。
- **用量归因**：`UsageContext` 此前不填 `model_id`（条目无法归因到实际跑的 model），
  本 PLAN 补上——`task_id`/`model_id` 都属本次 run 的绑定（段 3 的判据）。

### 链的实测终点是判拒，而不是通过

四段全绿之后 run 仍然 `FAILED`：`task … rejected by acceptance gate`。这是**链在正常
工作**——合约声明要 `analysis_report`，真实会话交付的是 `session_message`，acceptance
gate 对着合约把它拒了。真实交付物与合约声明的 artifact 名之间的映射是产品决策
（`tool_pack.*` 一侧），不在本 EC 射程；本 EC 的靶子是「真实 runtime 能走完全链并使每
一段可判」，不是「演示合约一定通过」。

### 一处必须如实说明的射程边界（EC-05 的活）

冻结 Tool Set 里是 **tool provider id**（`openhands_workspace` / `m12_artifact` /
`ncbi_eutils`），不是 SDK 工具名。缺 provider → SDK 映射时，控制面**不静默丢工具**，
而是让会话创建失败并点名未注册的 id（`::test_unmapped_tool_set_is_named_not_silently_dropped`
把这一真实行为固定下来）。四段用例因此用**测试侧**的惰性注册补上这一环，好让四段可测；
生产缺这一环的行为是**已测量**的，不是被掩盖的。

## 反证与实测

| # | 注入 | 结果 |
| --- | --- | --- |
| F1 | `session_resolution.execution_target` 恒返回 `(None, None)` | **红**：段 1（`mock never reached`）+ 未映射工具用例；run 失败消息点名 `carries no execution target: endpoint and model` ⇒ 执行目标真的经 spec 到达线上 |
| F2 | `runtime_adapter._deliverable` 断掉 MESSAGE 事件映射 | **红**：段 2 在 artifact 查找处即失败（artifact 列表为空），段 4 的输入同时消失 ⇒ 映射段的可观测是映射结果本身 |
| F3 | `usage_mapping.publish_usage` 提前返回、不写账本 | **红**：段 3（`no positive MODEL_TOKENS entry in the ledger`），段 1/2/4 仍绿 ⇒ 归账段的断言与归账一一对应 |
| F4 | `result_handler.register_session_result` 提前返回空登记 | **红**：artifact/evidence 读面为空（`[]`），且 run 的失败消息仍是 `rejected by acceptance gate` ⇒ 与 F2 的签名可区分（F2 会先撞上 `carries no structured output`） |

四次注入均已复原，`git status --short` 只剩预期改动。

## Warnings（不阻断，如实登记）

- **W-1**：四段里的第 2 段（事件映射）与第 4 段（制品/证据）**共享同一个可观测窗口**
  ——canonical 事件表不落 session 级事件（`RunEvent.agent_session_id` 字段今日无写入方），
  真实会话的映射结果只能经 artifact 载荷读到。因此 F2/F4 会使两段同时失去输入；
  两者可由 run 的失败消息区分（见反证表）。若将来把 session 级事件投影进 canonical，
  第 2 段应改判在那条链上。
- **W-2**：`_deliverable` 产出的键名是事实名 `session_message`，不是合约声明的
  artifact 名（`analysis_report` 等）。演示合约因此判拒——这是**如实**结果，不是缺陷；
  键名映射属 `tool_pack.*` 产品决策（EC-06 一侧）。
- **W-3**：live 用例（`requires_live_llm`）本机**只证明 skip 路径**：无凭据环境 skip 且
  点名所需环境变量。它本身**未被实跑**过（没有真实端点凭据，也不得为其申请），因此
  「真端点全链」是**未验证**状态，不记 PASS。
- **W-4**：离线全链依赖 `RESEARCHOS_WORKSPACE_ALLOW_HOST_SHELL=1` 这一**显式**开发开关
  （`build_local_workspace` 在 `allow_host_shell=False` 时拒绝构造）。默认 deny 未放松，
  但「真实 runtime 能跑完会话」目前确实需要操作者显式打开 host shell——这是射程边界，
  不是已解决项。
- **W-5**：mock 端点在本机回环地址上监听端口（`127.0.0.1:0` 动态分配）。用例需要
  本地 socket 能力；在禁止监听端口的受限沙箱里会失败（CI 与开发机均允许）。
- **W-6**：段 3 的账本断言读到的是**编排注入的账本实例**（`deps.budget`），而不是经
  另一条读面重新取数。理由是 `POST /runs` 的响应是异步派发，账本没有对应的 run 级读面
  （与 evidence/artifact 不同）。因此「归账」判据的读面强度低于段 4。

## 结论

EC-03 **PASS_WITH_WARNINGS**：三处结构性断点（执行目标不进 spec / 3 参工厂对 1 参调用 /
交付物不进结构化输出）已各自修复；离线全链四段在默认门里实跑可判，四段各有独立断言与
独立反证；live 用例如实 skip 并记录（不记 PASS）；默认门离线可跑。W-1…W-6 为如实登记的
射程边界，不阻断。

## 门禁

| 门 | 结果 |
| --- | --- |
| `tests/e2e/test_ec03_real_runtime_offline_chain.py` | **2 passed / 1 skipped**（skip = live 用例，原因点名环境变量） |
| `tests/api/test_session_llm_factory.py` | **10 passed** |
| 尺寸门（450 行 / 50 行函数） | **947 passed**（首跑红：`runtime_support.py::session_llm_factory` 54 行、`_openhands_deps` 83 行、四段用例 66 行 —— 已拆分；**首跑红如实记录，不当作绿**） |
| `ruff check` / `ruff format --check` | 绿 |
| `mypy` | **937 source files, no issues** |
| 受影响套件 | `tests/adapters/openhands` + `tests/application` + `tests/architecture` **765 passed / 1 skipped**；`tests/api` **482 passed**；`tests/e2e` 全绿 |
| m0（23 项） | 见 GOAL-20260919-007 循环日志 cycle 3 行 |
