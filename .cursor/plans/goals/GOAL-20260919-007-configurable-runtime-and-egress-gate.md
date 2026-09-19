---
id: GOAL-20260919-007
slug: configurable-runtime-and-egress-gate
title: 真实执行体接线：runtime 可配置、受控出网门链、离线全链进 CI、诚实披露与工具面边界
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    2026-09-19 用户会话指令（goal 模式）：**新建承接 GOAL-007**，承接 GOAL-20260918-006
    收口结论「仍未处理的长程项」第 1 项里「按声明给 adapter 接线」的 **adapter 接线部分**
    （该 GOAL「不进入循环 / 需人工拍板」节第 3 项），把它做成可独立验收、独立 RECHECK 的 EC，
    之后由本驱动**自动化循环推进、无需逐轮确认**。四段授权原文如下：
    (1) **解除该项 escalation 的授权**：用户明确授权把「需人工拍板」第 3 项中
    **adapter 接线部分**移入本 GOAL 的 EC（据此该项不再阻塞循环）；同一项的
    **`tool_pack.*` 产品决策部分仍留人工面**，不在授权内，触及即 BLOCKED。
    (2) **受控出网边界**：真实 LLM 端点**仅由用户配置**（Base URL + API Key + Model ID，
    协议 `OPENAI_COMPATIBLE`，AGENTS.md §1）；凭据**只从环境变量或密钥服务读取**，
    源码、示例与测试**不写可用凭据字面量**；**真实端点调用永不进默认 CI**（只走
    `requires_live_llm` 门控的人工路径）。
    (3) **默认 runtime 保持 Fake**：CI 与离线开发不依赖网络；**选择真实 runtime 必须
    显式配置 + policy 允许**，两者缺一即拒绝（fail-closed 姿态不得放松，AGENTS.md §9）。
    (4) **push-to-main-for-CI 授权**沿用 GOAL-001…006 的批准口径：**只推 main、不 force、
    不重写历史、不推旁支触发 CI**；push 前 `git pull --ff-only origin main`
    （必要时 --rebase，始终不 force）。循环预算与纪律以本文件 frontmatter 为准
    （客户端自带的迭代/重试/超时上限一律让位于此）。
    GOAL-001…006 全部**只读**（001/002/004/005/006 ACHIEVED、003 BLOCKED），本 GOAL 不修改
    它们；如需指名只允许按只追加补一行事实更正（当前不需要）。
objective: >
  把「组合根仍注入 FakeAgentRuntime、OpenHands adapter 已建未接线」这条**已登记的边界**
  变成**有终态结论的事实**：runtime 变成**配置驱动**的选择面（Fake | OpenHands，两个组合根
  同侧），未配置时与今日**逐字节一致**；选择真实 runtime 时必须走**受控出网门链**
  （端点 URL 策略 / 凭据存在性 / 端点健康 / 模型能力匹配），拒绝语义**点名缺哪条事实**且
  **一次都不发起出站调用**；真实 runtime 的**离线全链**（脚本化 mock 端点 → 会话创建/事件映射
  → 预算归账 → 制品与证据落 canonical）进默认 CI，真端点路径只走 `requires_live_llm` 人工门控
  并如实记录 skip；**执行体性质与运行时指纹**在 UI 与控制面读面**诚实披露**（受控 demo 输出
  不再与真实结果同形）；OpenHands 侧**工具集冻结 + Policy Wrapper 强制**的边界有一等判据；
  `tool_pack.*` / 脚本策略拿到**二选一终态**（既有边界内实现，或 ADR 草案 + 权威登记 + 同源收敛）。
  **全程不删测试、不改门禁、不以「未观测到失败」或「扫描没报问题」充当 PASS；
  不新增依赖、不改上游 pin、不自行修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  ——触及即 BLOCKED。**
exit_criteria:
  - id: EC-01
    criterion: >-
      **Runtime 选择面**（GOAL-006「不进入循环 / 需人工拍板」第 3 项的 adapter 接线部分）：
      配置驱动的 `Fake | OpenHands` 选择，**两个组合根**（`services/api/composition.py`
      与 `services/api/pg_composition.py`）**同侧**（读同一个选择点，不各写一套）；
      **未配置时行为与今日逐字节一致**（默认仍是受控 demo 输出、现有套件全绿）；
      选择结果与**运行时指纹**进 manifest / 读面（AGENTS.md §4 漂移可见性：`ModelDefinition`、
      endpoint 配置摘要、返回的 model 名、系统指纹、白名单响应头、probe 套件版本、兼容性结论）。
    verify: >-
      结构判据（两个组合根各只有**一个** runtime 装配点、都经同一选择函数；反向搜索确认
      `FakeAgentRuntime(` 的直接构造不再散落在组合根里；未配置 ⇒ 选择函数返回 Fake 且
      `demo_session_output()` 仍被使用）+ **回归对照**：未配置时现有套件全绿且
      demo 会话输出**逐字节不变** + 选择 OpenHands ⇒ 真实 adapter 被构造（受控 deps，
      离线）+ 选择结果与指纹字段在 manifest / 读面**可判** + **反证**（把选择函数短路回
      硬编码 Fake ⇒ 选择用例红；把指纹字段去掉 ⇒ manifest/读面判据红）+ 受影响套件 + m0 绿。
    status: PASS
    evidence: >-
      PLAN-20260919-107 / RECHECK-20260919-107（PASS_WITH_WARNINGS，W-1…W-6）。交付：
      新模块 `services/api/runtime_support.py`（`RuntimeSelection(kind, configured)` +
      `resolve_runtime_selection` + `build_agent_runtime`）+ `ApiSettings.agent_runtime`
      （`RESEARCHOS_AGENT_RUNTIME`，默认空串 = 未配置 ⇒ 受控 demo 执行体）；**两个组合根
      同侧**（`composition._sqlite_orchestration` 与 `pg_composition._build_pg_orchestration`
      都经同一函数，组合根内 `FakeAgentRuntime(...)` 直接构造 **AST 判据数到 0**）；
      **未知取值 fail-closed** 并同时点名取值与合法词表（不静默回退——静默回退会让
      「配了真实 runtime」与「跑的是 demo」不可区分）；`openhands` 分支在缺
      `credential_resolver` / `policy_evaluator` 时**点名拒绝**（AGENTS §5：不受 Policy
      Wrapper 约束的真实 runtime 不允许被装配），且**构造期零出站**（用例用「`resolve`
      即炸」的凭据替身证明构造期连凭据都没解析）；选择结果经
      `PreflightContext.execution_substrate` 冻结进 `RunManifest.execution_backend`
      （M7 声明过、此前**恒为 None**——原注释称「runtime 装配由 OpenHandsRuntimeAdapter
      决定」与事实不符，本轮更正），并随 `MANIFEST_FROZEN` payload 出现在既有
      `GET /runs/{id}/events` 上（**零 DTO / 路由 / OpenAPI / 迁移变化**）；指纹槽位写
      **显式 `NOT_VERIFIED` 记录**而不是留空（留空分不清「没探」与「探了没问题」，且
      受控 demo 不发起任何模型调用 ⇒ AGENTS §4 七件事实一件也不存在）。
      **反证四条先红后复原**：① PG 根改回硬编码 ⇒ 结构判据红（1 failed）；② openhands
      分支短路成 Fake ⇒ 2 failed；③ 未知取值改静默回退 ⇒ `DID NOT RAISE`（1 failed）；
      ④ 去掉 `execution_backend` 填充 ⇒ 2 failed（`assert None == 'openhands'`）。
      顺手修掉一条**同实例**真缺陷：PG 根凭据面此前两处各解析一次，而
      `RegistryCredentialResolver` **有状态**（API 注册的 Key 只在该实例内存里）⇒ 收敛成
      `_PgRuntimeInputs` 单实例贯穿装配与 ApiDeps。门禁：定向 `tests/api` 459 passed /
      1 skipped（DSN pin 配方）、架构门 **963 passed**、规模门禁 **944 passed**、
      `mypy` **934 files 无问题**、m0 **PASS: profile=m0; 23 deterministic checks**
      （3803 passed / 200 skipped）、DOCS-CHECK PASS。W：加性披露使 manifest digest 与
      改动前不同（EC 自身要求，已点名）、旧 run 的 `None` 不得读作某个执行体、
      「可装配 ≠ 可运行」（门链与全链属 EC-02/EC-03）、SDK 导入横幅为既有噪声、
      选择面射程只覆盖控制面两条路径、指纹槽位仍是占位。
  - id: EC-02
    criterion: >-
      **受控出网门链**：真实 runtime 启用时走 policy / preflight 门——**端点 URL 策略**
      （复用既有 `EndpointUrlPolicy` 与 `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 语义，
      不新造第二套）、**凭据存在性**、**端点健康**、**模型能力匹配**；**拒绝语义点名缺哪条
      事实**（哪一项门把它挡下，可被读到）；**反证：缺配置或策略不允许 ⇒ 拒绝且一次都不
      发起出站调用**。
    verify: >-
      门链用例（逐项：缺 endpoint / 缺凭据 / 端点不健康 / 能力不匹配 ⇒ 各自被点名拒绝，
      且**出站调用计数 == 0**——用可观测的传输层计数器/替身证明，不是"没报错"）+
      **反证**（逐项把对应门去掉 ⇒ 对应用例红）+ URL 策略复用判据（结构上引用既有
      `validate_endpoint_url` / `EndpointUrlPolicy`，不出现第二份 host 判据）+ 契约/文档同源
      （`docs/integration/OPENHANDS_ADAPTER.md` 与 `docs/architecture/AGENT_RUNTIME.md` 口径一致）
      + 受影响套件 + m0 绿。
    status: PASS
    evidence: >-
      PLAN-20260919-108 / RECHECK-20260919-108（PASS_WITH_WARNINGS，W-1…W-6）。交付：
      门链第一环原本**完全缺失**——`validate_endpoint_url` 只被两个**手动**操作调用
      （`/llm-endpoints/{id}/test`、`/models/{id}/probe`），run 路径上的
      `build_endpoint_health` 对目录内每个 endpoint 直接 `probe_connectivity`：
      把 `http://127.0.0.1:8080/v1` 写进目录，run **会先对它发起真实 HTTP 请求**。
      本轮把「拒绝」前移到「触网」：`_probe_endpoint` 在**解析凭据之前**做 URL 裁决，
      被拒 ⇒ `EndpointHealth.UNKNOWN` 且**一次出站都没有**；`_check_endpoint` 在 health
      之前插入 URL 环且**短路**（被拒时不再派生 `ENDPOINT_UNHEALTHY` / `CREDENTIAL_MISSING`
      ——探测没发生，`UNKNOWN` 是派生噪声，真实阻塞事实是策略没放行）。复用既有判据：
      新增 `endpoint_url_refusal` 只是 `validate_endpoint_url` 的薄包装，
      结构判据证明全仓 `ipaddress` 只出现在 `endpoint_policy.py` 一处。
      **短路的对照是实跑的**：同一 context 去掉裁决注入 + 清空 health/凭据面 ⇒
      `ENDPOINT_UNHEALTHY` 与 `CREDENTIAL_MISSING` **本来都会报**。
      顺手修一处真实缺陷：`CREDENTIAL_MISSING` 消息原本不点名 `credential_ref`
      （只说 endpoint），现改为 `credential {ref} for endpoint {id} cannot be resolved`。
      **出站 0 有两个独立可观测面**：记录型 `httpx.BaseTransport` 注入真实
      `OpenAIChatGateway`（传输层）+ `FakeBase.calls`（端口层）。
      **反证三条改红复原**：删探针短路 ⇒ 2 failed（传输层 + 端到端同时红）；
      删 URL 环 ⇒ 2 failed 且失败形态降级为**不点名**的 `ENDPOINT_UNHEALTHY`；
      删 `run_execution` 注入 ⇒ 1 failed。判据 9 passed；尺寸门 945 passed；
      受影响套件 1519 passed / 70 skipped / 3 failed（3 条为 `@pytest.mark.postgres`
      环境依赖，m0 全量下通过）；`ruff` / `mypy`（935 files）绿；
      m0 **PASS: profile=m0; 23 deterministic checks**。默认姿态未放松
      （`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 默认 `0` = deny）。
  - id: EC-03
    criterion: >-
      **真实 runtime 的离线全链进默认 CI**：脚本化 mock 端点驱动 OpenHands adapter
      （先例：`tests/e2e/test_m12_usage_real_relay.py` 用 `httpx.MockTransport` 驱动真实
      `OpenAIChatGateway`）→ **会话创建 / 事件映射** → **预算归账** → **制品与证据落 canonical**；
      另附 `requires_live_llm` 环境门控的**真实端点手动 E2E**（凭据不在环境时 **skip 并如实记录**，
      **不得伪造、不得为其申请凭据**）。
    verify: >-
      默认（离线）套件里一条**端到端链**：mock 端点 ⇒ 真实 adapter 产出的会话结果经事件映射
      进 canonical 事件链、usage 归账进 BudgetLedger、制品/证据可读；**反证**（断开事件映射 /
      断开归账 / 断开制品落库各自 ⇒ 对应用例红）+ live 门控用例在无凭据环境**如实 skip**
      （记录 skip 事实，不记 PASS）+ 默认门**离线可跑**（无网络依赖）+ m0 绿。
    status: PASS
    evidence: >-
      PLAN-20260919-109 / RECHECK-20260919-109（PASS_WITH_WARNINGS，W-1…W-6）。三处**结构性**
      断点各自修复：① `AgentSessionSpec` 不携带执行目标（endpoint/model）⇒ 解析点下沉到
      `session_resolution.execution_target`（纯映射，逐段独立收敛为 `None`）并随 spec 携带
      （Domain 类型；只带 `credential_ref`，凭据值仍由 adapter 侧 `CredentialResolver` 取）；
      ② 生产把 **3 参** `build_llm` 塞给按 **1 参** `self._build_llm(spec)` 调用的
      `SessionBuilder.build_session` ⇒ `create_session` 必然 `TypeError`（「一调用就炸」，
      不是「未接线」）⇒ `session_llm_factory` 按与 EC-02 **同一条链**（URL 策略 → 凭据存在性）
      在**构造 LLM 之前**裁决，拒绝点名事实且**零出站**；③ 真实 adapter 的
      `AgentSessionResult` 不携带 `structured_output`（第四段结构性不可达）⇒ SUCCEEDED 时
      携带最小交付物 `session_message`（取自**已映射**的 `RuntimeEvent.MESSAGE`，复用同一份
      redact/截断），非成功终态保持空。离线全链四段各有独立断言与独立反证：会话创建（mock
      端点真的收到补全请求，线上 model 名来自目录绑定；F1 目标恒 `None` ⇒ 红）、事件映射
      （artifact 载荷的 `message_count`/`session_id`；F2 断映射 ⇒ 红）、预算归账（正向
      `MODEL_TOKENS` 且 `task_id`/`model_id` 归因正确——顺带补上 `UsageContext` 缺失的
      `model_id`；F3 不写账本 ⇒ 红）、制品与证据（`/artifacts`、`/evidence` 非空并由既有
      acceptance gate 裁决；F4 空登记 ⇒ 红）。**链的实测终点是判拒**：合约声明要
      `analysis_report`、真实会话交付 `session_message`，acceptance gate 判拒是链在正常
      工作（键名→合约 artifact 名的映射属 `tool_pack.*` 产品决策）。live 用例挂
      `requires_live_llm`，无凭据环境**如实 skip**（skip 不是 PASS；本机只证明 skip 路径）。
      实测边界（EC-05 的活）：冻结 Tool Set 里是 tool provider id，缺 provider→SDK 映射时
      控制面**不静默丢工具**而是点名未注册的 id（`::test_unmapped_tool_set_is_named_not_silently_dropped`
      固定该行为），四段用例因此用测试侧惰性注册补这一环。
  - id: EC-04
    criterion: >-
      **诚实披露**：UI 与控制面读面标明**当前执行体**（受控 demo vs 真实 runtime）与
      **运行时指纹**；**demo 输出不再与真实结果同形**——现有 `demo_session_output`
      的披露文案纳入**同源收敛**（同一口径在域/读面/UI/文档逐处一致，不出现两套说法）。
    verify: >-
      结构判据（读面 DTO 有执行体字段且**页面有渲染分支**，不是"只在 `types.ts` 里存在"）+
      stub e2e 与 live e2e 各一条（断言两种执行体在页面上**可区分**）+ **反证**（去掉渲染分支
      ⇒ 对应 e2e 红）+ web 六门（lint / typecheck / unit / build / stub e2e / live e2e）+
      页面改动的设计基线/结构签名按既有流程重生成（跨平台一致性用既有容器配方复核）+
      文案同源（`CONTROL_PLANE_API.md` / `CONSOLE_PAGE_MAP.md` / `demo.py` 同一口径）。
    status: PENDING
    evidence: ""
  - id: EC-05
    criterion: >-
      **工具面边界**：OpenHands 侧**工具集冻结**（AgentSession 有效 Tool Set 不可变）+
      **Policy Wrapper 强制**（AGENTS.md §5：不得绕过 policy 直接调 `execute_tool`）；
      **MCP / tool provider 的接入边界如实登记**（本循环只登记边界，不新增接入面）。
    verify: >-
      结构判据（非门控的直通面在组合装配路径上**不可达**；唯一公共执行入口是门控入口）+
      用例（policy DENY ⇒ 工具 executor **未被触达**；REQUIRE_APPROVAL ⇒ 拒绝反馈 + 审批事件）+
      **反证**（把门控入口换回直通 ⇒ 用例红）+ 工具集冻结用例（会话内有效 Tool Set 不可被改写）
      + 接入边界登记（文档同源、逐条点名已覆盖与未覆盖）+ 受影响套件 + m0 绿。
    status: PENDING
    evidence: ""
  - id: EC-06
    criterion: >-
      **`tool_pack.*` / 脚本策略的二选一终态**：(a) 在**既有边界内实现**（既有
      `tool_pack.install` / `.update` / `.revoke` 能力与 `tool_pack_digests` 供应链面，
      不新增 canonical 状态、不新增迁移）；**或** (b) 产出 **ADR 草案**（`docs/adr/`，
      Status: Proposed）+ **权威登记**（`docs/INDEX.md` 唯一入口）+ **声明/文档同源收敛**。
      Accepted 与否**归用户**。**触及产品决策时按 escalation 立即 BLOCKED。**
    verify: >-
      二选一：(a) 用例（策略放行/拒绝各自可判 + 供应链 digest 进入既有读面；
      **反证：去掉策略门 ⇒ 用例红**）；(b) ADR 草案文件在树（`Status: Proposed`）+ 权威登记
      + 声明面反向搜索每处命中要么是「真实消费者 + 用例」要么是「不提供/待决」说明 +
      文档逐处一致。两条都要求：**不得只改注释/文案充数**，且**不得**把 `Status` 写成 Accepted。
    status: PENDING
    evidence: ""
budget:
  max_cycles: 20
  per_cycle_minutes: 120
  no_progress_stop_cycles: 2
fix_policy:
  same_signature_retries: 2
  cycle_fix_retries: 3
  forbidden:
    - 修改 validator/门禁/快照/测试断言使其通过
    - skip/删除测试或降低断言强度
    - git push --force / 重写历史 / 推非 main 分支触发 CI
    - 伪造或夸大验证证据（未实跑不得记 PASS）
    - git add -A（并发工作树；只加显式路径）
escalation_triggers:
  - 需要修改 Accepted ADR / 核心安全策略 / Canonical State 边界
  - 破坏性数据迁移或不可逆动作
  - 新依赖/上游版本 pin 变更（含为判据引入新的解析/传输库——优先用现有依赖实现）
  - 同一失败签名超过 fix_policy 上限
  - 授权范围内的 runtime 接线不受此限；`tool_pack.*` 产品决策、新增依赖/上游 pin 变更、Accepted ADR / Canonical State 边界仍须拍板
  - 威胁建模/授权面（BOLA/BFLA）覆盖类决策——需用户或 ADR 拍板，本循环不得自行决定
  - 依赖 pin 升级（`undici` / `vite` / `yaml` 等有修复版本的包）——上游 pin 变更，需用户或 ADR 拍板
child_plans:
  - .cursor/plans/tasks/PLAN-20260919-107-runtime-selection-surface.md
  - .cursor/plans/tasks/PLAN-20260919-108-egress-gate-chain.md
  - .cursor/plans/tasks/PLAN-20260919-109-real-runtime-offline-full-chain.md
latest_recheck: null
memory_entries: []
---

# GOAL-20260919-007 — 真实执行体接线（自迭代循环）

本文件是 **GOAL 记录**（位于 `PLAN-*` 之上的编排层），格式契约见本目录 `README.md`；
工程事实、验收与复检仍由 PLAN/RECHECK/MEM 体系承载（单一流程权威：
`.cursor/rules/20-plan-memory-recheck.mdc`）。GOAL 只做编排与记账。

## 目标与退出标准

GOAL-006 收口（ACHIEVED）时把「仍未处理的长程项」如实登记进「终止与收口 · 收口结论」，
并把六项依赖人工拍板的项照抄进「不进入循环 / 需人工拍板」。其中**第 3 项**写着：

> **后继入口第 8 项：按声明给 adapter 接线 / `tool_pack.*` 策略**：组合根仍注入
> FakeAgentRuntime、OpenHands adapter 已建未接线，方向是「runtime 可配置」；`tool_pack.*`
> 与脚本策略涉及受控出网与产品决策，可能触及 Accepted ADR 与核心安全策略。

**用户已显式授权把其中的 adapter 接线部分移入 EC**（见 frontmatter `authorization.ref` 第 (1) 条），
据此该项不再阻塞本循环；**`tool_pack.*` 的产品决策部分仍留人工面**（EC-06 只允许
「既有边界内实现」或「ADR 草案 + 权威登记」，且**不得**自行把 ADR 置为 Accepted）。

| EC | 主题 | 来源 | 状态 |
| --- | --- | --- | --- |
| EC-01 | Runtime 选择面（配置驱动 Fake \| OpenHands，两个组合根同侧，未配置逐字节一致，选择结果与指纹进 manifest/读面） | GOAL-006 人工面第 3 项（adapter 接线部分） | **PASS**（RECHECK-20260919-107，W-1…W-6） |
| EC-02 | 受控出网门链（URL 策略 / 凭据 / 端点健康 / 能力匹配；拒绝点名缺哪条事实；出站调用 0） | 同上 + AGENTS.md §9 | **PASS**（RECHECK-20260919-108，W-1…W-6） |
| EC-03 | 真实 runtime 离线全链进默认 CI（mock 端点 → 会话/事件/归账/制品；真端点走 `requires_live_llm`） | 同上 + AGENTS.md §11 | **PASS**（RECHECK-20260919-109，W-1…W-6） |
| EC-04 | 诚实披露（执行体性质 + 运行时指纹进读面与 UI；demo 输出不再与真实结果同形） | 同上 + AGENTS.md §4 | **PENDING** |
| EC-05 | 工具面边界（Tool Set 冻结 + Policy Wrapper 强制；MCP/tool provider 接入边界如实登记） | AGENTS.md §5 | **PENDING** |
| EC-06 | `tool_pack.*` / 脚本策略二选一终态（既有边界内实现 或 ADR 草案 + 权威登记 + 同源收敛） | GOAL-006 人工面第 3 项（产品决策部分） | **PENDING** |

**优先级**：EC-01 → EC-02 → EC-03 → EC-04 → EC-05 → EC-06（derive 取 EC 表首个 PENDING；
若某 EC 本轮**部分交付**，其「下一轮输入」优先于表序）。

**不在本 GOAL 的 EC 内**（登记为背景，不伪装成已收口）：GOAL-006 人工面六项中除第 3 项
adapter 接线部分以外的全部内容、GOAL-006 六条 EC 的 W 列表、扫描 coverage 口径 —— 见
「不进入循环 / 需人工拍板」节。这些**不因本 GOAL 存在而被宣称已解决**。

### 本轮已探明的现状（事实类，用于判定起点；不当作验收依据）

以下由**只读勘察**在 2026-09-19 建档时确认（路径 + 行号可复核）：

1. **两个组合根各硬编码一个 Fake 装配点**：`services/api/composition.py:264-277` 与
   `services/api/pg_composition.py:159-172` 都构造
   `FakeAgentRuntime(structured_output=demo_session_output())`；`pg_composition.py:22` 直接
   复用 `composition` 的 `demo_session_output`。
2. **OpenHands adapter 已建、完全未接线**：`adapters/openhands/runtime_adapter.py:64`
   `OpenHandsRuntimeAdapter(deps: AdapterDependencies)`（依赖包见
   `adapters/openhands/session_types.py:77`）。`rg "adapters\.openhands|OpenHandsRuntimeAdapter"`
   在 `services/` 与 `packages/`（非 docstring）下**零命中**；所有构造都在 tests 里。
   `packages/domain/manifest.py:12` 的 docstring 却声称「runtime 装配由 OpenHandsRuntimeAdapter
   决定」—— **声明与事实不符**，这是 EC-01/EC-04 要收敛的原始落差。
3. **端口与价值对象**：`packages/application/ports/agent_runtime.py:115`（`AgentRuntime` Protocol，
   六方法）；契约注册表 `tests/contracts/registry.py:251` 已同时登记 `FakeAgentRuntime` 与
   `_openhands_runtime_factory`（测试侧），说明**同判基座已存在**。
4. **受控出网的既有零件**：`EndpointUrlPolicy`（`packages/application/model_relay/endpoint_policy.py:14`）
   + `validate_endpoint_url`（同文件 `:40`）已实现 scheme/host 判定与 localhost/private/link-local
   拒绝；`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` **只在** `services/api/settings.py:118-121` 被读，
   **默认 `"0"`（fail-closed）**。
5. **预检门已存在但走的是"声明 + 端点健康"，不是活体能力探测**：
   `packages/application/preflight/checks.py` 的 `check_models` 产出 `MODEL_MISSING` /
   `MODEL_ELIGIBILITY` / `ENDPOINT_UNHEALTHY` / `CREDENTIAL_MISSING`；端点健康来自
   `services/api/preflight_support.py:31`（`gateway.probe_connectivity`）。
6. **指纹已实现、但主运行路径不写 manifest**：`ModelRuntimeFingerprint` 定义在
   `packages/domain/models.py:133-151`，由 `build_fingerprint`（`packages/application/model_relay/fingerprint.py:61`）
   构造，只在模型探测路由（`services/api/routers/models.py:222-258`）与 M12 参考路径生产；
   `RunManifest.model_runtime_fingerprints`（`packages/domain/manifest.py:49`）在 **services/api
   主运行路径从未被填充**。
7. **离线 mock 先例已存在**：`tests/e2e/test_m12_usage_real_relay.py:62-98` 用 `httpx.MockTransport`
   驱动真实 `OpenAIChatGateway`（`adapters/relay/gateway.py:63`）做 usage 归账；`requires_live_llm`
   标记登记在 `pyproject.toml:112`，当前**只有该文件**使用（`tests/e2e/test_m12_usage_real_relay.py:35`）。
8. **demo 披露文案现状**：`services/api/demo.py:17-27` 的 `demo_session_output()` 返回
   `{"analysis_report": {"summary": "controlled fake session output (M13-R1 console demo)", "status": "ok"}}`；
   披露目前**只在 payload 内部**，读面/UI 没有独立的"执行体性质"字段。

以上八条是**起点事实**，不是验收依据；EC 的 PASS 仍只认各自的判据与反证。

### EC-01 判定细则（Runtime 选择面）

- 「两个组合根同侧」指：**同一个选择函数**（同一个模块、同一份判据）被两处调用；
  不允许 SQLite 根与 PG 根各写一套 `if`。
- **禁止的 PASS 依据**：「配置项已定义」「文档已写明方向」。PASS 只认**结构判据**
  （装配点唯一 + 反向搜索无散落构造）**加回归对照**（未配置 ⇒ 逐字节一致）**加反证**。
- 「未配置时逐字节一致」的判据是**可执行的**：默认路径下 `demo_session_output()` 的返回值
  与今日**逐字段相等**，且现有套件（含 stub/live e2e）全绿。
- 「运行时指纹」在本 EC 里指 **AGENTS.md §4 的七件事实**（`ModelDefinition`、endpoint 配置摘要、
  返回的 model 名、系统指纹、白名单响应头、probe 套件版本、兼容性结论）在**选择了真实
  runtime 时**进入 manifest / 读面；无法证明的项**显式标注为未验证**，不得留空冒充已验证。

### EC-02 判定细则（受控出网门链）

- **必须复用**既有 `EndpointUrlPolicy` / `validate_endpoint_url` 与
  `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 语义；**新造第二份 host 判据即判负**。
- 「一次都不发起出站调用」的判据必须是**可观测的出站计数 == 0**（传输层替身/计数器），
  不是「没抛异常」。
- 门链的**每一项**都要有点名拒绝的事实（缺 endpoint / 缺凭据 / 端点不健康 / 能力不匹配），
  且拒绝语义可被调用方读到（错误信息或 findings 里点名）。
- 默认姿态**不得放松**：未显式配置 ⇒ 真实 runtime 不可选；URL 策略默认仍 fail-closed。

### EC-03 判定细则（离线全链进 CI）

- 「离线全链」指**默认门里就能跑通**：不依赖网络、不依赖真实凭据、不标记 `requires_live_llm`。
- 链路四段必须**各自可判定**：会话创建 / 事件映射进 canonical / 预算归账 / 制品与证据落 canonical；
  任一段断开都要能让对应用例红。
- live 门控用例在无凭据环境**必须如实 skip**；**不得**为它申请凭据、不得用假凭据冒充 live。
- 若某段链路今天**在架构上不可达**（例如事件映射要求真实 SDK 事件源），如实登记为一等边界
  并把该段写成显式未覆盖，**不得**用"近似"充当覆盖。

### EC-04 判定细则（诚实披露）

- 「披露」的定义是**读面字段 + 页面渲染分支**：只在 `types.ts` 里存在字段不算。
- 「demo 输出不再与真实结果同形」指：两种执行体在**读面上可区分**（字段/取值不同），
  且文案**不冒充**真实研究结论；现有 `demo_session_output()` 的披露文案纳入同一口径源。
- 页面改动必须走既有设计基线流程（结构签名判红 ⇒ `UPDATE_OUTLINES=1` 重生成 ⇒ 跨平台
  一致性复核），否则 web 门会红。
- live e2e 的夹具必须由域代码生成（内容寻址 digest 不可手写），spec 要幂等。

### EC-05 判定细则（工具面边界）

- 「Policy Wrapper 强制」指：**唯一公共执行入口**是门控入口；直通面在**组合装配路径上不可达**
  （结构判据），并有运行时用例证明 DENY 时 executor **未被触达**。
- 「工具集冻结」指会话内有效 Tool Set **不可被改写**（用例证明改写被拒或不可达）。
- MCP / tool provider 的**接入边界**本 EC 只**如实登记**（已覆盖与未覆盖逐条点名），
  **不新增接入面**；新增接入面即超出本 EC，按 escalation 处理。

### EC-06 判定细则（`tool_pack.*` 二选一）

- (a) **实现**的硬边界：只允许既有能力名（`tool_pack.install` / `.update` / `.revoke`）与既有
  供应链读面；**不得**新增 canonical 状态、不得新增迁移、不得改 Accepted ADR。
- (b) **ADR 草案**必须给出：问题陈述、候选方案与代价、为何本轮不做、触发条件、影响面。
  **`Status` 必须保持 `Proposed`**；把打上 `Accepted` 视为越权（判负）。
- 两条共同要求：**至少有 1 条用例或结构判据**证明不是文案改动。

## 循环入口协议

按 README 的 7 步判定执行，一切状态以「文件 + 工作树 + 远端实况」为准：

1. 本文件 `status != ACTIVE` → 只输出终止摘要（ACHIEVED/BLOCKED/ABORTED + 依据），本轮不做改动。
2. 迭代日志最后一行判定续点：无记录 → 开 cycle 1（执行 ①）；有子 PLAN 在
   IN_PROGRESS → 继续 ②；本地验证已过、有未推送 commit → ④⑤；CI 未记录结论 →
   ⑤（等待/判定，禁止猜测绿）；CI 有失败且未达上限 → ⑥。
3. 每 cycle 收口必须：CI 终态已记录 + 本文件（迭代日志/EC 状态/child_plans/
   latest_recheck/状态历史）已回写；未收口不得开新 cycle。
4. 进入 cycle 时在迭代日志声明 `driver=client-goal` / `owner=root-agent`；另一驱动
   持有未收口 ACTIVE cycle 时等待，不并发双写。

**当前续点**：**cycle 3 收口（EC-01 / EC-02 / EC-03 PASS）**，下一步 = **cycle 4 = EC-04
（诚实披露）**：UI 与控制面读面标明**当前执行体**（受控 demo vs 真实 runtime）与**运行时
指纹**；**demo 输出不再与真实结果同形**——现有 `demo_session_output` 的披露文案纳入
**同源收敛**（同一口径在域/读面/UI/文档逐处一致）。判定细则见「EC-04 判定细则」：
「披露」= **读面字段 + 页面渲染分支**（只在 `types.ts` 里存在字段不算）；stub e2e 与
live e2e 各一条断言两种执行体在页面上**可区分**；页面改动必须走既有设计基线流程
（结构签名判红 ⇒ `UPDATE_OUTLINES=1` 重生成 ⇒ 跨平台一致性复核），否则 web 门会红。
**已知前置事实**：EC-01 已把选择结果写进 `RunManifest.execution_backend`（随
`MANIFEST_FROZEN` payload 出现在 `GET /runs/{id}/events`），读面 DTO 与页面渲染分支是
EC-04 要补的那一半；`demo_session_output()`（`services/api/demo.py:17-27`）目前的披露只在
payload 内部（`"controlled fake session output (M13-R1 console demo)"`），读面/UI 没有独立的
「执行体性质」字段。状态以本文件「迭代日志」末行 + 工作树实况为准；不凭记忆假设上一轮状态。

## 驱动

驱动无关（README「驱动适配」）：本实例由客户端 goal 模式驱动（每轮触发 = 一次入口
协议），亦可换会话/定时驱动；仅当 `status=ACTIVE` 时推进。同一时刻仅一个驱动推进。

## 单 cycle SOP

按 README ①~⑦ 执行。本实例附加约定：

- ① derive 主题顺序：EC 表首个 PENDING；若上一 cycle 部分交付，以其「下一轮输入」为准。
  子 PLAN 必须独立可验收、独立 RECHECK（`.cursor/plans/rechecks/`），frontmatter 带
  `parent_goal: GOAL-20260919-007` 并投影 ALL_PLAN。
- ② 按子 PLAN 的 WP 推进，**每 WP 独立 commit**（显式路径；并发工作树，禁 `git add -A`）。
- ③ 本地验证：`make validate-all` 全量 23 项（DSN 固化配方）+ 受影响定向套件 + web 门
  （lint/typecheck/unit/build/stub e2e/live e2e）；页面改动时按既有流程重生成设计基线
  与结构签名（`UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`，
  跨平台一致性用既有容器配方复核）。实现完成后**先自查规模门禁**（50 行函数 / 450 行文件）
  与快照类门禁（OpenAPI / 设计基线），再跑 m0。本地不绿不得 push。
- ④ 子 PLAN 收口（RECHECK DONE）后 GOAL 记录 commit 列表。
- ⑤ `git pull --ff-only origin main`（必要时 --rebase，不 force）→ `git push origin main`
  → 按本机口径查 m0-quality 最新 run（无 gh CLI：`git credential fill` 取已存令牌走
  GitHub REST API，按 head_sha 匹配 + `/jobs` 读六个 job 结论）→ 轮询到终态并记录
  run 链接与结论。只改 `.cursor/**` 的记录提交同样触发六 job CI，按同口径等待。
- ⑥ 按「CI 失败分类与纠错」处置；修复以独立 commit 落 main 并回到 ⑤。
- ⑦ 回写本文件：迭代日志（含 driver/owner 声明行）、EC 状态、child_plans、
  latest_recheck、状态历史；未达终态且未触顶 → 直接进入下一 cycle ①。
- **未实跑不得记 PASS**；本机无法验证记 PENDING 并停止推进，不猜测绿。
- **CI 台账闭合约定**（沿用 GOAL-005/006）：逐条记录每个推送提交触发的 run 到终态；
  写下本条的这个提交自身触发的 run 在回合汇报里给出终态，不再回写文件。

**本 GOAL 特有的执行纪律**（安全面，来自 authorization.ref）：

- 默认 runtime 保持 Fake；**CI 与离线开发不依赖网络**。
- 选择真实 runtime 必须**显式配置 + policy 允许**，两者缺一即拒绝。
- 凭据**只从环境变量或密钥服务读取**；源码、示例与测试**不写可用凭据字面量**
  （测试里出现的假 token 只允许是不可用的占位串，且不得与真实端点组合）。
- **真实端点调用永不进默认 CI**，只走 `requires_live_llm` 门控的人工路径。
- **Domain 不得出现厂商名**；**OpenHands 类型不得进 Domain**（adapter 层隔离）。
- **不引入新依赖、不改上游 pin**（需要即 BLOCKED）。

## CI 失败分类与纠错

按 README 分类表执行；本仓已知 flake/env 签名（重跑不修，先排除环境干扰）：
observability OTLP teardown race（stopped receiver 端口）、m0 全量单跑在负载下的 timing
用例（隔离复跑对照）、DSN 注入（需固化配方：`RESEARCHOS_POSTGRES_DSN` 指向 test DSN、
其余 DSN 键清空，防 litellm `load_dotenv` 注入 operator `.env`）、
`framework/run_cursor_framework_evals` 在 Windows 上偶发文件占用（复跑对照）、
**kill 后台 m0 会留孤儿 pytest**（复跑前先确认无残留进程/容器，否则污染下一轮）、
`python/dependency-boundaries` 在直接跑 `.venv/Scripts/python.exe` 时会因 `lint-imports`
不在 PATH 而误红（用仓库既定 `uv run --frozen --no-sync` 启动）。

`.github/workflows/m0-quality.yml` 属治理面：循环内不修改；需要改动即 BLOCKED 提请人工。
账户级计费阻断（runner_id=0、无 step、2 秒结束）非代码缺陷：不推进 cycle，恢复后先复核
`runner_id != 0` 再回填结论（GOAL-003 cycle 1 的处置模板）。

**本 GOAL 新增的失败面**：真实 runtime 相关用例若在 CI 上表现不稳定（例如 mock 端点
的时序假设），**优先把用例改成不依赖时序**；若确认是环境相关缺陷而无法在既有边界内修，
按 README 的 flake/env 与基础设施两行处置，不得靠重跑掩盖。

## 终止与收口

- **ACHIEVED**：EC-01…EC-06 全 PASS 且有实跑证据 + 收口 RECHECK（独立复检，
  `result: PASS` 或 `PASS_WITH_WARNINGS`）+ 本文件 `latest_recheck` 指向该 RECHECK +
  「终止与收口」写明收口结论（含仍未处理项，如有）。
- **BLOCKED**：`budget.max_cycles` 触顶、或 `no_progress_stop_cycles` 连续命中、
  或命中 `escalation_triggers`（含 `tool_pack.*` 产品决策、canonical 边界与依赖 pin 决策）。
  写 BLOCKED 记录（原因/EC 状态表/收口复检/安全扫描处置/恢复条件/仍未处理的长程项），
  恢复条件由用户拍板。
- **ABORTED**：用户显式终止本目标。

收口时必须把「仍未处理的长程项」如实登记为后继入口（不隐藏缺口），并给出恢复条件
（新建承接 GOAL 或显式变更 budget 并置回 ACTIVE）。

### 收口结论

（尚未收口；本文件 `status: ACTIVE`。）

## 不进入循环 / 需人工拍板

以下项**不在本 GOAL 的 EC 内**，循环内不得自行决定；一旦 EC 的实现必须改动它们才能继续，
按 `escalation_triggers` 立即置 `status: BLOCKED` 并留人工决策（可选动作只限「如实登记 +
给出选项与影响面」，不含实现）：

1. **威胁建模/授权面覆盖**（GOAL-005/006 收口结论的既有口径）：越权、BOLA/BFLA、业务逻辑风险
   需要独立审计射程与决策面，本循环只负责**如实写明未覆盖**，不自行开展。
2. **`artifacts/` 内未跟踪明文 token 文件的清理**（RECHECK-091 W-4）：文件从未提交
   （`git ls-files artifacts/` = 0），清理属操作者决策；本循环只登记事实。
3. **`tool_pack.*` 的产品决策部分**（GOAL-006 人工面第 3 项的另一半）：EC-06 只允许
   「既有边界内实现」或「ADR 草案（Proposed）+ 权威登记 + 同源收敛」；
   **是否采纳、是否把 ADR 置为 Accepted 归用户**。用户已授权的是 adapter 接线部分，
   **不含**本项的产品决策。
4. **450 行硬上限贴线的持续重构**：`packages/application/run_orchestration/service.py`
   等贴线文件属「下一行就会红」的状态；**随改动搬代码**（每个 cycle 的 ③ 自查），
   **不单独成 EC**。需要改门禁时即 BLOCKED。
5. **依赖 pin 升级**（RECHECK-20260918-093 W-1）：`undici@5.29.0`、`vite@6.3.5`、
   `yaml@2.8.1` 全部有修复版本，但都在 **devDependency 链**上，升级属上游 pin 变更 ⇒
   命中 `escalation_triggers`，由用户/ADR 拍板。**不得**读作「依赖面无风险」。
6. **hook 侧 L3 门修复**（RECHECK-20260918-093 W-2）：根因是插件检测层（semgrep 1.136.0）
   未安装，修复命令见 `docs/audits/MIMOSA_POST_CLOSURE_AUDIT_20260918.md §3.3`；但装上后
   `MIMOSA_GIT_GATE_MODE=graded` 的 medium 会**交互式询问**，可能挡住无人值守提交 ⇒
   修与不修都是**安全策略决定**，留人工。

**既有口径（照抄 GOAL-005/006 收口结论）**：收口扫的覆盖缺口
（`threatModel`/`findingDiscovery` partial）⇒ 静态扫描不给出授权面结论；扫描
`verdictEffect=none`，**不得**读作「项目安全」；扫描 coverage inconclusive 同样
**不得**读作项目安全。本 GOAL 的任何 EC PASS 也不构成整体安全结论。

**ecosystem 口径**：EC-04 的执行体披露与 EC-03 的 mock 端点都**不得**被读作
「产品已支持真实 LLM 执行」——真实 runtime 的可用性取决于用户配置与 policy 放行，
本 GOAL 交付的是**可配置性与门链**，不是「默认启用真实执行」。

## 迭代日志
| # | 子 PLAN | commits | 本地验证 | CI run/结论 | 修复 | 剩余差距 | 下一轮输入 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 建档（本文件；driver=client-goal / owner=root-agent） | 建档提交见本行「本地验证」列之下的补录（回写下条补 commit hash） | 治理 `validate.py` 绿（建档后实跑）；只读勘察八条现状事实（见「本轮已探明的现状」） | 建档提交自身的 run 见回合汇报（按闭合口径） | 无 | EC-01…EC-06 全 PENDING | cycle 1 = EC-01（Runtime 选择面：配置驱动 Fake \| OpenHands，两个组合根同侧） |
| 1 | PLAN-20260919-107（EC-01：Runtime 选择面；driver=client-goal / owner=root-agent） | `fb8ddf8`（derive）、`10422e5`（WP-A 选择面骨架：`runtime_support.py` + `ApiSettings.agent_runtime`）、`ade2081`（WP-B 两组合根接线 + PG 凭据面单实例）、`0e01d2e`（WP-C 选择结果进 manifest/读面）、`54e2986`（WP-D 13 条判据）、`2d71e87`（WP-E 文档同源收敛）、`5b03d27`（mypy 门禁修正）、本次回写提交（RECHECK-20260919-107 / MEM-20260919-079 / PLAN DONE / ALL_PLAN / memory INDEX + 本文件）；本条推送的 run 按闭合约定在回合汇报给出终态 | derive 前只读勘察九条事实；实现后：**反证四条先红后复原**（PG 根改回硬编码 ⇒ 结构判据红 1 failed；openhands 分支短路 ⇒ 2 failed；未知取值静默回退 ⇒ `DID NOT RAISE`；去掉 `execution_backend` 填充 ⇒ `assert None == 'openhands'` 2 failed）；`tests/api/test_runtime_selection_surface.py` **13 passed**；定向 `tests/api` **459 passed / 1 skipped**；架构门 **963 passed**；规模门禁 **944 passed**；`ruff check` / `format --check` 绿；`mypy` **934 files no issues**；m0 **PASS: profile=m0; 23 deterministic checks**（3803 passed / 200 skipped，539.63s）；DOCS-CHECK PASS | `11d47cf`（建档）的 M0 run **35446933910 = cancelled**（`concurrency.cancel-in-progress` 结构性取消：紧随其后的 `fb8ddf8` 推送取消了在飞的 M0；同一内容的覆盖由 `fb8ddf8` 的 run 承担）；`11d47cf` 的 Push-on-main run **35446933991 = success**；`fb8ddf8` 的 M0 run **35447242640 = success**（六个 job 全 success：collector-quality / console-frontend / container-quality / quality-windows-latest / quality-ubuntu-latest / eval-gate）、Push-on-main run **35447242522 = success**；本条推送的 run 见回合汇报 | 返工三处（记录诚实，**未改任何断言**）：① 初版把 runtime 装配内联进 `_sqlite_store_parts` ⇒ 撞 50 行函数门禁（58 行）+ `composition.py` 涨到 451 行（超 450）⇒ 拆出 `_sqlite_orchestration` / `_sqlite_apideps`，并把 `sqlite_artifact_blob_dir` 与 `build_sqlite_draft_service` 移到 `assembly.py`（该模块本就为此存在）；② `composition.py` 不再 re-export `demo_session_output` ⇒ `tests/api/base_fixtures.py` 导入失败（243 errors）⇒ 改从属主 `services.api.demo` 导入（机械搬 import）；③ m0 抓出 `python/typecheck` 6 条 mypy 错（守卫列表不带窄化、测试触私有属性、缺 cast）⇒ 守卫改成直接判两个值使 mypy 真窄化 | EC-01 **PASS**（RECHECK-20260919-107 = PASS_WITH_WARNINGS，W-1…W-6：加性披露使 manifest digest 变化、旧 run 的 `None` 不得读作执行体、「可装配 ≠ 可运行」、SDK 导入横幅、选择面射程只覆盖控制面两路径、指纹槽位仍是占位）；EC-02…EC-06 PENDING | cycle 2 = EC-02（受控出网门链：URL 策略 / 凭据存在性 / 端点健康 / 能力匹配；拒绝点名缺哪条事实；出站调用 0） |
| 2 | PLAN-20260919-108（EC-02：受控出网门链；driver=client-goal / owner=root-agent） | 本次推送为**单次批量推送**（derive + WP-A…WP-E + 回写同推，沿用 GOAL-006 cycle 1 与 cycle 1 的攒批形态以避开 M0 并发取消） | derive 前只读勘察八条事实（其中两条是关键发现：`validate_endpoint_url` 只有两个**手动**调用点；`_probe_endpoint` 无 URL 裁决即出网）；实现后：**反证三条先红后复原**（删 `_probe_endpoint` 短路 ⇒ 2 failed；删 `_check_endpoint` 的 URL 环 ⇒ 2 failed 且失败形态降级为**不点名**的 `ENDPOINT_UNHEALTHY`；删 `run_execution` 注入 ⇒ 1 failed）；`tests/api/test_runtime_egress_gate.py` **9 passed**；尺寸门 **945 passed**；受影响套件（tests/api + tests/application + tests/contracts + tests/architecture/python）**1519 passed / 70 skipped / 3 failed**（3 条为 `@pytest.mark.postgres` 靶向运行未加载 `tests/postgres/conftest.py` 的环境依赖，同一批在 m0 全量下通过）；`ruff check` / `format --check` 绿；`mypy` **935 files no issues**；m0 **PASS: profile=m0; 23 deterministic checks**（4003 passed / 10 skipped，500.00s）；治理 `validate.py` 绿 | `f3e388a`（cycle 1 回写提交）的 M0 run **35451031056 = success**（六个 job 全 success：collector-quality / console-frontend / container-quality / quality-windows-latest / quality-ubuntu-latest / eval-gate）、Push-on-main run **35451030745 = success**（本轮补记到台账）；本条推送的 run 按闭合约定在回合汇报给出终态 | 返工两处（**未改任何断言**）：① `_probe_endpoint` 加一行 URL 裁决使 `run_execution.execution_inputs` 涨到 51 行 ⇒ 撞 50 行函数门禁 ⇒ 抽出 `_live_preflight`（并写明「裁决与 health 必须同源求值」）；② m0 首跑 `framework/validate` 红：`PLAN-20260919-108` 缺 `## 影响报告` 章节 ⇒ 补齐后治理验证通过、m0 全量复跑绿（**这条首跑红如实记录，不当作绿**） | EC-01/EC-02 **PASS**（RECHECK-107 / RECHECK-108，均 PASS_WITH_WARNINGS）；EC-03…EC-06 PENDING | cycle 3 = EC-03（真实 runtime 离线全链进默认 CI：脚本化 mock 端点 → 会话创建/事件映射 → 预算归账 → 制品与证据落 canonical；另附 `requires_live_llm` 门控的真端点手动 E2E，无凭据环境如实 skip） |
| 3 | PLAN-20260919-109（EC-03：真实 runtime 离线全链；driver=client-goal / owner=root-agent） | `9bb468f`（derive）、`adf8b83`（WP-A spec 携带执行目标 + 解析点下沉）、`63746f2`（WP-B/WP-C 受门工厂 + 组合根接线 + host shell 显式开关）、`46ceae3`（WP-D 交付物映射 + usage 归因）、`8e398a3`（WP-D 四段判据与 live 门控用例）、`a1137f4`（WP-E 文档同源）、本次回写提交（RECHECK-20260919-109 / MEM-20260919-081 / PLAN DONE / ALL_PLAN / memory INDEX + 本文件）；本条批量推送的 run 按闭合约定在回合汇报给出终态 | derive 前只读勘察确认**三处结构性断点**（spec 不携带执行目标 / 3 参工厂对 1 参调用 / 交付物不进结构化输出）；实现后：**反证四条先红后复原**（F1 `execution_target` 恒 `None` ⇒ 段 1 红 + run 失败消息点名 `carries no execution target: endpoint and model`；F2 断 MESSAGE 映射 ⇒ 段 2 红且 artifact 列表为空；F3 不写账本 ⇒ 段 3 红而 1/2/4 绿；F4 空登记 ⇒ 制品/证据读面为 `[]` 但 run 仍走到 acceptance gate，与 F2 签名可区分）；`tests/e2e/test_ec03_real_runtime_offline_chain.py` **2 passed / 1 skipped**（skip = live 用例，原因点名 `RESEARCHOS_LIVE_E2E_ENDPOINT` / `_KEY`）；`tests/api/test_session_llm_factory.py` **10 passed**；受影响套件 `tests/adapters/openhands`+`tests/application`+`tests/architecture` **765 passed / 1 skipped**、`tests/api` **482 passed**、`tests/e2e` 全绿；尺寸门 **947 passed**；`ruff check` / `format --check` 绿；`mypy` **937 files no issues**；m0 **PASS: profile=m0; 23 deterministic checks**（改完源码与文档后跑；`.cursor` 记录写入在其后，追加跑 `--profile framework` **8 项 PASS** 覆盖治理/文档面）；治理 `validate.py` 绿。**跑法提示**：`tests/api` 全量需 `RESEARCHOS_POSTGRES_DSN` 钉到 test DSN（否则 litellm `load_dotenv` 注入 operator `.env` ⇒ 3 条组合根用例 `password authentication failed`），`lint-imports` 需 `.venv/Scripts` 在 PATH | `032c30e`（cycle 2 回写提交 = 上一 cycle 批量推送的 tip）的 M0 run **35454369106 = success**、Push-on-main run **35454368423 = success**（六 job 全 success：collector-quality / console-frontend / container-quality / quality-windows-latest / quality-ubuntu-latest / eval-gate）——本轮按闭合约定补记入台账；本条批量推送的 run 见回合汇报 | 返工三处（记录诚实，**未改任何断言**）：① 尺寸门首跑红——`runtime_support.py::session_llm_factory` 54 行、e2e `_openhands_deps` 83 行、四段用例 66 行 ⇒ 拆出 `_gated_session_target` / `_point_catalog_at` + `_register_live_key` + `_real_runtime` + 四个 `_assert_*` 段函数（并把四次读面合并为 `_ChainReads`，顺带解决 6 参函数）；② `mypy` 三条（`deps.credentials` 声明为 Port 而实际是 Fake ⇒ 需 `cast`；`TestClient.json()` 返回 `Any` ⇒ 需 `cast`；一处 `assert replace` 的凑数写法删除）；③ e2e 断言按**实测**修正而非按预期：会话终态**不是** SUCCEEDED（合约要 `analysis_report`、真实会话交付 `session_message` ⇒ acceptance gate 判拒），段 2 改为读 artifact 载荷的 `message_count`/`session_id`，段 3 从「账本非空」改为**可归因**（`task_id`/`model_id`） | EC-01/EC-02/EC-03 **PASS**（RECHECK-107 / 108 / 109，均 PASS_WITH_WARNINGS）；EC-04…EC-06 PENDING。EC-03 的 W-1…W-6：段 2/段 4 共享制品窗口（canonical 不落 session 级事件）、`session_message` 键名属 `tool_pack.*` 决策、live 用例本机只证明 skip 路径、真实会话目前需显式 host shell 开关、mock 端点需本地 socket、段 3 的读面强度低于段 4 | cycle 4 = EC-04（诚实披露：执行体性质 + 运行时指纹进读面与 UI；demo 输出不再与真实结果同形） |

## 状态历史

- 2026-09-19 建档：由 GOAL-20260918-006「终止与收口 · 收口结论」的长程项第 1 项中
  「按声明给 adapter 接线」的 **adapter 接线部分**建立（用户 goal 模式指令：承接该项并
  自动化循环推进、无需逐轮确认；同时显式授权解除该项的 escalation）。`status: ACTIVE`；
  EC-01…EC-06 全 PENDING；GOAL-001…006 保持**只读**（001/002/004/005/006 ACHIEVED、
  003 BLOCKED）。建档时以**只读勘察**确认了八条现状事实（两个组合根各硬编码一个
  `FakeAgentRuntime` 装配点、OpenHands adapter 零接线、`EndpointUrlPolicy` 与
  `RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 既有语义、预检四门已有、指纹已实现但主运行路径
  不写 manifest、mock 端点与 `requires_live_llm` 先例已存在、demo 披露只在 payload 内）；
  这些是**起点事实**而非验收依据。
- 2026-09-19 cycle 1 收口：EC-01 **PASS**（PLAN-20260919-107 / RECHECK-20260919-107 =
  PASS_WITH_WARNINGS，W-1…W-6）。runtime 从「组合根硬编码 Fake、OpenHands adapter 零接线、
  而 `manifest.py` 却声称『runtime 装配由 OpenHandsRuntimeAdapter 决定』」收敛成
  **配置驱动的选择面**：`services/api/runtime_support.py` 是唯一装配点，两个组合根同侧
  （AST 判据数到 `FakeAgentRuntime(...)` 直接构造 0 处）；未配置 ⇒ 受控 demo 执行体，
  `demo_session_output()` 逐字段不变；**未知取值 fail-closed** 并点名取值与合法词表；
  `openhands` 缺凭据面/policy 面时点名拒绝，且**构造期零出站**（「`resolve` 即炸」的凭据
  替身证明构造期连凭据都没解析）；选择结果冻结进 `RunManifest.execution_backend` 并随
  `MANIFEST_FROZEN` payload 出现在既有 `GET /runs/{id}/events`（零 DTO / 路由 / OpenAPI /
  迁移变化）；指纹槽位写显式 `NOT_VERIFIED` 记录而非留空。**四条反证先红后复原**。
  顺手修掉 PG 根凭据面「两处各解析一次」的**同实例**真缺陷（`RegistryCredentialResolver`
  有状态）。门禁：13 条判据全绿、定向 `tests/api` 459 passed、架构门 963 passed、
  规模门禁 944 passed、`mypy` 934 files 干净、m0 **23/23**、DOCS-CHECK PASS。
  **一处声明与事实不符的更正**：`packages/domain/manifest.py` 的 M7 边界注释原称
  「runtime 装配由 OpenHandsRuntimeAdapter 决定」——事实上组合根硬编码 Fake 且该 adapter
  在 `services/`/`packages/` 零引用，字段因此恒为 None；本轮按事实改写，
  并在 `docs/architecture/AGENT_RUNTIME.md` 新增 §3.1 装配事实表（含「本节不宣称的部分」）。
  CI 台账见迭代日志 cycle 1 行。
- 2026-09-19 CI 口径事实（本轮实测，供后续 cycle 复用）：`.github/workflows/m0-quality.yml`
  有 `concurrency: {group: m0-quality-…-refs/heads/main, cancel-in-progress: true}` ⇒
  **连续推送会取消在飞的 M0 run**（本轮 `11d47cf` 的 M0 run 35446933910 即被紧随的
  `fb8ddf8` 取消，终态 `cancelled`）。因此**同内容的多 WP 应攒成一次推送**（GOAL-006
  cycle 1 也是这个形态），或推送后等在飞 run 到终态再推下一次；被取消的那条要如实记为
  `cancelled` 并说明覆盖由哪条 run 承担，不得当作 success。
- 2026-09-19 cycle 2 收口：EC-02 **PASS**（PLAN-20260919-108 / RECHECK-20260919-108 =
  PASS_WITH_WARNINGS，W-1…W-6）。受控出网以前**只加在「拒绝」上，没加在「触网」上**：
  `validate_endpoint_url` 只有两个**手动**调用点（`/llm-endpoints/{id}/test`、
  `/models/{id}/probe`），而 run 路径的 `build_endpoint_health` 对目录内每个 endpoint
  直接发 `GET /models`——`http://127.0.0.1:8080/v1` 写进目录，run 会**先对它发起真实
  HTTP 请求**再判不健康。本轮把门链第一环前移到**触网之前**：`_probe_endpoint` 先做 URL
  裁决（且放在解析凭据之前），被拒 ⇒ `UNKNOWN` 且**出站 0**；`_check_endpoint` 同环**短路**，
  不再派生 `ENDPOINT_UNHEALTHY`。判据不靠「没抛异常」：记录型 `httpx.BaseTransport` 注入
  真实 `OpenAIChatGateway`（传输层计数）+ `FakeBase.calls`（端口层计数）**两个独立面**，
  并且**反面同跑**（同一 URL、只把策略放开 ⇒ 确实出站）。顺手修一处真实缺陷：
  `CREDENTIAL_MISSING` 消息原本不点名 `credential_ref`，运维只能看出哪条链断了、看不出
  要配哪一条凭据。默认姿态未放松（`RESEARCHOS_ALLOW_LOCALHOST_ENDPOINTS` 默认 `0`）。
- 2026-09-19 一条边界事实（本轮实测，供后续 cycle 与「不进入循环」节复用）：
  `packages/application/ports/**` **不能** import `packages/application/model_relay/**`——
  后者 `__init__.py` 反向 `from packages.application.ports import (...)`，而
  `packages/application/__init__.py` 又在 `ports` 之前执行，任何反向导入都会落在
  **部分初始化**的模块上（是否真报错取决于导入顺序，属软失败点）。需要跨越这条边界的
  值对象（如 URL 策略）只能以**中性编码**（`Mapping[str, str]` 裁决结果）注入，
  或在服务层求值——沿用 `provider_health` 的既有口径。
- 2026-09-19 cycle 3 收口：EC-03 **PASS**（PLAN-20260919-109 / RECHECK-20260919-109 =
  PASS_WITH_WARNINGS，W-1…W-6）。这条链在 cycle 2 勘察时断在**第一段之前**，而且是
  **结构性**的三处：① `AgentSessionSpec` 只携带控制面事实、**不携带**执行目标
  （endpoint/model），真实 adapter 因此无从装配 LLM；② 生产把 **3 参** `build_llm` 塞进
  `AdapterDependencies.build_llm`，而 `SessionBuilder.build_session` 按 **1 参**
  `self._build_llm(spec)` 调用 ⇒ 选 `openhands` 时 `create_session` 必然 `TypeError`
  （收敛为 `PermanentPortError(SYSTEM_BUG)`）——**不是「未接线」，是「一调用就炸」**；
  ③ 真实 adapter 的 `AgentSessionResult` **不携带** `structured_output`，而 canonical 的
  制品/证据登记正是由结构化输出驱动 ⇒ 第四段从来不可达。本轮三段各自补上：执行目标在
  **catalog 在手的层**（orchestration）解析为纯映射并随 spec 携带（**只带
  `credential_ref`，不带凭据值**）；会话 LLM 工厂按与 EC-02 **同一条链**（URL 策略 →
  凭据存在性）在**构造 LLM 之前**裁决，拒绝点名事实且**零出站**；SUCCEEDED 时携带最小
  交付物（取自**已映射**的 `RuntimeEvent.MESSAGE`，复用同一份 redact/截断），非成功终态
  保持空（把失败会话的中间文本登记成结论 = 把「没做完」伪装成「有产出」）。
  **一处方法论要点**（本轮实测）：Port 的依赖是 callable 时，**元数/契约**必须由一条
  真的调用它的用例来判——「装上了」与「调得通」是两件事。**链的实测终点是判拒**：
  四段全绿后 run 仍 `FAILED`（`rejected by acceptance gate`），因为合约要 `analysis_report`
  而真实会话交付 `session_message`——这是链在正常工作，不是缺陷；键名→合约 artifact 名的
  映射属 `tool_pack.*` 产品决策（EC-06 一侧）。**如实登记的射程边界**：冻结 Tool Set 里是
  tool provider id 而非 SDK 工具名，缺映射时会话创建**点名**未注册的 id（不静默丢工具，
  有专门用例固定该行为），四段用例用测试侧惰性注册补这一环；live 用例本机**只证明 skip
  路径**（skip 不是 PASS）；canonical 不落 session 级事件 ⇒ 段 2 与段 4 共享制品窗口。
  门禁：四段用例 **2 passed / 1 skipped**、工厂用例 **10 passed**、尺寸门 **947 passed**
  （首跑红 ⇒ 三个超 50 行函数已拆分）、`mypy` **937 files 干净**、m0 **23/23**、
  `--profile framework` **8/8**、DOCS-CHECK PASS。CI 台账见迭代日志 cycle 3 行
  （含上一 cycle 批量推送 run 的补记）。
