# Research OS Console — UI 设计提示词 v0.1（草案）

> **用途**：面向 UI 生成/实现代理的提示词集合。每次生成取「Part 0 元提示词 + 目标屏幕 Part N」拼接后投喂。
>
> **依据（不可与以下文件冲突）**
> - `AGENTS.md` — 产品不变量（Compile/Preflight 先行、模型漂移可见、Canonical State、Memory Gate、观测隐私）
> - `docs/api/CONTROL_PLANE_API.md` — 端点契约
> - `apps/web/src/api/types.ts` — **DTO 单一 schema truth**（OpenAPI 由 `docs/api/openapi.m13.json` 维护）
> - `docs/product/CONSOLE_INFORMATION_ARCHITECTURE.md` / `END_TO_END_USER_JOURNEY.md` — 信息架构与用户旅程
> - `docs/configuration/AUTONOMY_AND_GATES.md`、`TEAM_TEMPLATES.md` — 自治等级、门禁类型、团队模板
>
> **状态**：草案。本文档不修改任何产品契约、API 或 Domain 语义；若与 DTO 冲突，以 DTO 为准并回报冲突。

---

## 1. 头脑风暴结论：这个系统的人格

### 1.1 它不是什么

不是一个聊天界面。Research OS 是「研究 Agent 操作系统 + 自主研发控制平面 + 证据原生审计系统」。用户在里面管理的是**一次可审计的科研运行**，不是一段对话。所有设计决策都从这里推导。

### 1.2 主隐喻

**控制室（Control Room）为体，流水线（Pipeline）为骨，证据链（Evidence Chain）为血脉。**

最接近的参照物：Linear（密度与工艺）、Grafana（可观测性）、Argo/GitHub Actions（流水线与日志）、W&B（实验追踪）。明确**不**参照：消费级聊天产品、看板式任务工具。

### 1.3 五条设计第一性原理（由 AGENTS.md 不变量直接推导）

| # | 原则 | 来源 | 在界面上的硬要求 |
| --- | --- | --- | --- |
| P1 | **Preflight 先于执行** | AGENTS.md §3 | Dry Run 是一等公民闸门，不是 tooltip。状态非 PASS 时「启动」按钮必须禁用，且把机器可读 finding 翻译成「为什么不能启动 + 定位到哪里修」 |
| P2 | **证据原生** | AGENTS.md §8 | 任何 Claim 必须携带来源与状态徽章；`PROPOSED` ≠ `VERIFIED`；无证据支撑的陈述在视觉上必须呈现为「未完成」（虚线描边 + 灰阶 + Unverified 徽章） |
| P3 | **模型漂移可见** | AGENTS.md §4 | 每张模型卡片同时展示 `model_name`（请求）与 `returned_model_name` / `system_fingerprint`（实测）；`provider_fingerprint_available=false` 时**必须**渲染「Configuration reproducible / provider fingerprint unavailable」，**禁止**渲染「Fully reproducible model」（DTO 注释为硬约束） |
| P4 | **不确定就是不确定** | BudgetLedger「不伪造 cost（UNKNOWN 语义）」 | `estimated_cost_minor=null` / `unknown_cost_entries>0` 时显示 `UNKNOWN`，禁止用 `0`、`—`、占位符或骨架屏冒充真实数据。空状态 ≠ 零 |
| P5 | **默认拒绝、显式授权** | AGENTS.md §9 | 高风险动作（审批、发布、预算扩张、外部副作用）必须带**后果预览**：会发生什么、影响哪些 Task、是否产生 Manifest Revision 或 Fork。禁止「一键全部同意」 |

### 1.4 信息架构收敛建议

`docs/product/CONSOLE_INFORMATION_ARCHITECTURE.md` 的 13 项项目内导航平铺会淹没用户。建议收敛为 **5 个信息域 + 二级 Tab**，保留全部能力但降低首屏决策成本：

```text
Plan      Overview · Protocol & Preflight · Team · Research Map
Run       Tasks · Timeline · Workspace & Experiments
Evidence  Sources · Claims & Evidence · Reviews · Deliverables
Assets    Models · Tools · Compute · Evaluation
Govern    Audit · Memory · Settings
```

全局侧边保留：Projects / Runs / Models / Roles & Agents / Tools / Compute / Evaluation / Settings。

### 1.5 视觉语言（dark-first）

专业工具美学：深色为默认（长时间盯屏 + 日志/时间线密集），浅色为可切换选项。高密度但分区清晰，无装饰性动效。

**颜色语义**（唯一强调色 + 语义色，不使用大面积渐变/发光）：

| 语义 | Token | 值（dark） | 用途 |
| --- | --- | --- | --- |
| 应用底 | `bg-app` | `#0B0D10` | 最外层 |
| 面板 | `bg-panel` | `#12151A` | 卡片/侧栏 |
| 抬升 | `bg-raised` | `#171B21` | 表格头、悬浮层 |
| 悬停 | `bg-hover` | `#1E242C` | 行/项 hover |
| 边框 | `border` | `#232A33` / 强调 `#2E3742` | 0.5–1px |
| 主文字 | `fg` | `#E6EAF0` | 正文 |
| 次文字 | `fg-muted` | `#9AA6B4` | 元信息 |
| 弱文字 | `fg-faint` | `#6B7684` | 时间戳、ID |
| 强调 | `accent` | `#4C8DFF` | 主操作、链接、选中 |
| 成功/已验证 | `success` | `#35A56F` | VERIFIED、SUCCEEDED |
| 警告 | `warn` | `#D9962A` | WARN、待审批、预算趋紧 |
| 危险 | `danger` | `#E0524C` | FAIL、DENY、失败 |
| 未知 | `unknown` | `#8B7BD8` | UNKNOWN、待探测、不可复现标注 |

**状态四重编码**：形状 + 图标 + 文字 + 颜色。禁止仅靠颜色单通道传达状态（色盲友好为硬性要求）。

**排版**：正文 13px/1.6，元信息 12px，标签 11px，标题 15/18/22px。ID、digest、时间戳、代码、命令一律等宽字体（`ui-monospace, "JetBrains Mono", Consolas`）。中文字体回退 `PingFang SC / Microsoft YaHei`。

**间距**：4 / 8 / 12 / 16 / 24 / 32 / 48。**圆角**：chip 4、控件 6、卡片 8、面板 12。**动效**：仅用于状态变化与实时流入，150–200ms `ease-out`；禁止装饰性动画、渐显堆叠、骨架脉冲以外的加载特效。

**预算/成本配色说明**：本控制台的成本面板采用工程语义（超支=危险红/警告橙，健康=成功绿），不套用金融涨红跌绿惯例。若产品定位需要对齐该惯例，请在 Part 0 中显式覆盖此条。

---

## 2. Part 0 — 元提示词（所有屏幕共用，必须作为前缀）

```text
你是 Research OS Console 的前端实现代理。Research OS 是一个「研究 Agent 操作系统 +
自主研发控制平面 + 证据原生审计系统」的控制面 UI，不是一个聊天界面。

【产品人格】
主隐喻是控制室：用户在管理一次可审计的科研运行。参照 Linear / Grafana / Argo / W&B
的密度与工艺，不要参照消费级聊天产品。

【技术栈】
React 18 + TypeScript strict + Vite。数据只来自 Control Plane API，前端只消费
API DTO（见 apps/web/src/api/types.ts，单一 schema truth）。禁止 import 后端
Domain 概念；禁止把 API 响应缓存在 localStorage 当作 Canonical State；刷新后
状态全部从 API 恢复。

【视觉】
深色优先。背景 #0B0D10，面板 #12151A，抬升 #171B21，边框 #232A33，主文字
#E6EAF0，次文字 #9AA6B4。强调色 #4C8DFF，成功 #35A56F，警告 #D9962A，
危险 #E0524C，未知 #8B7BD8。0.5px 边框，圆角 4/6/8/12。正文 13px/1.6，
ID 与 digest 用等宽字体。动效仅用于状态变化与实时流入，150–200ms。

【五条不可协商的规则】
1. Preflight 先于执行：状态非 PASS 时禁止提供可点击的「启动」入口，并把机器可读
   finding 翻译成人类可读的「为什么不能启动 + 去哪里修」。
2. 证据原生：Claim 必须显示 status 徽章（PROPOSED / VERIFIED / DISPUTED /
   REFUTED），无证据或未升级的 Claim 用虚线描边 + 灰阶呈现为「未完成」。
3. 模型漂移可见：同时展示请求的 model_name 与实测的 returned_model_name /
   system_fingerprint。provider_fingerprint_available 为 false 时，必须渲染
   "Configuration reproducible / provider fingerprint unavailable"，
   严禁渲染 "Fully reproducible model"。
4. 不确定就是不确定：cost 为 null 或 unknown_cost_entries > 0 时显示 UNKNOWN，
   禁止用 0、占位符或骨架屏冒充真实数据。空状态与零值必须视觉可区分。
5. 默认拒绝、显式授权：高风险操作（审批 / 发布 / 预算扩张 / 外部副作用）必须带
   后果预览（会发生什么、影响哪些 Task、是否产生 Manifest Revision 或 Fork），
   禁止提供「一键全部同意」。

【安全与隐私】
永不渲染 API Key 明文——DTO 只提供 credential: "configured" | "missing"。
错误消息一律使用后端返回的 redacted 字段（error_message_redacted），
禁止展示未脱敏原文。禁止用前端隐藏按钮代替授权：无权访问的资源必须在 API 层
返回并渲染为 403 状态，而不是隐藏入口。

【状态矩阵——每个视图都必须实现】
empty（首次、有引导动作）/ loading（骨架）/ error（可重试 + 脱敏原因）/
partial（部分数据 + 明确缺什么）/ forbidden（403 说明）/ stale（数据过期，
显示上次更新时间 + 刷新）/ live（SSE 连接中，断线时显示「重连中」，
禁止假装实时）。

【可访问性】
所有状态用 形状 + 图标 + 文案 + 颜色 四重编码。键盘可达全部交互，
焦点环清晰可见。表格支持列排序与键盘导航。语义化 HTML + ARIA。

【输出要求】
产出可直接运行的 TSX，组件单一职责，纯展示组件与数据获取分离。不要编造
DTO 中不存在的字段；需要但缺失的字段标注 TODO 并说明应向哪个端点补齐。
```

---

## 3. Part 1 — Setup Wizard（首次配置）

**目标**：让用户在 3 分钟内完成「中转站可用 → 模型可探测 → 默认模型选定」，并理解这不是注册流程而是能力接入。

**布局**：居中单列向导（最大宽 640px），顶部步骤条 `Relay → Test → Models → Probe → Defaults`，不可跳过但可回退。左侧固定一张「你会得到什么 / 我们不会做什么」的说明卡（不存储 Key 明文、不代理流量到第三方）。

**数据契约**：`POST /llm-endpoints`（`LlmEndpointCreateDto`：`name, base_url, protocol: "OPENAI_COMPATIBLE", api_style: "chat_completions" | "responses", api_key?, enabled?, request_timeout_seconds?, max_retries?, concurrency_limit?, discovery?`）→ `POST /llm-endpoints/{id}/test`（`EndpointTestResultDto`）→ `POST /llm-endpoints/{id}/discover-models`（`model_ids[]`）→ `POST /models/{id}/probe`（`ProbeResultDto`）。

**关键交互**：
- Test 结果展示三行：`ok`、`returned_model_name`、`system_fingerprint`（可能为 `null` → 显示 `not provided`）；错误只渲染 `error_message_redacted`。
- Discover 结果以多选列表呈现 `model_ids`，支持全选与按前缀过滤。
- Probe 对每个选中模型并行执行，逐行显示探测中 → 结果；`capability_failures[]` 展示失败能力项。
- `provider_fingerprint_available=false` 的模型行渲染紫色 `unknown` 徽章 + 提示文案「Configuration reproducible / provider fingerprint unavailable」。

**禁止事项**：任何一步失败时允许「继续」；显示 Key 明文；把探测失败静默吞掉。

**验收**：无端点时应用首屏即为向导；Key 字段 `type="password"` 且 DTO 回读只含 `configured/missing`；模拟 `ok=false` 时展示脱敏错误并阻断继续。

---

## 4. Part 2 — Endpoints & Models（资产域）

**目标**：一屏掌握「哪些中转站健康、哪些模型可用、每个模型具备什么能力、指纹是否可信」。

**布局**：左侧端点列表（名称 + 健康点 + 凭据状态 chip），右侧模型表格（列：Display name / Model ID / Endpoint / Enabled / Capabilities / Reproducibility / Last probe）。顶部工具条：Add endpoint、Discover models、Probe all、筛选（enabled / unhealthy / fingerprint unavailable）。

**数据契约**：`GET /llm-endpoints`（`LlmEndpointReadDto`）、`GET /llm-endpoints/{id}/health`（`EndpointHealthDto`）、`GET /models/{id}/compatibility`（`CompatibilityViewDto`：`model, endpoint_id, endpoint_healthy_hint: boolean | null, hard_capability_requirements[]`）。

**关键交互**：
- 健康点三态：ok（绿实心）/ fail（红实心）/ unknown（紫空心，`endpoint_healthy_hint=null`）。
- Capabilities 列渲染为 chip 组，每个 chip 显示 `status` 与 `confidence`，hover 显示 `source`（`manual` / `probe`）与 `probe_version`。
- Reproducibility 列：`fingerprint.system_fingerprint` 有值 → 绿 + `Fully reproducible model`；无值 → 紫 + `Configuration reproducible`。**严格遵守 DTO 注释**。
- 行内动作：Probe / Edit / Disable；Disable 需二次确认（它会影响 Dry Run）。

**验收**：`endpoint_healthy_hint=null` 不显示为「健康」；表格可键盘导航；关掉某模型后 Dry Run 页出现对应 finding。

---

## 5. Part 3 — Team & Model Binding（Plan 域）

**目标**：让「谁做什么、用哪个模型、有哪些权限、评审是否异构」在一屏内可审计。

**布局**：三段式。上：Team Template 选择器（LEAN / STANDARD / RIGOROUS，卡片式，显示角色数与适用场景）。中：Role 列表（26 个候选，显示 `min/max` 实例数、激活状态、折叠原因）。下：Agent 卡片网格，每张卡 = Role + 模型绑定（`EXPLICIT_MODEL / MODEL_PROFILE / INHERIT`）+ capability chips + 权限边界（`forbidden_capabilities`）。

**数据契约**：`GET /roles`（`RoleDefinitionDto`）、`GET /team-templates`（`TeamTemplateDto`）、`POST /projects/{id}/agents`（`AgentCreateDto`）、`PATCH /agents/{id}`（`AgentUpdatePayload`）、`POST /agents/{id}/clone`。能力串形如 `literature.search`、`workspace.write.notes`、`evidence.write`、`budget.read`、`protocol.propose`。

**关键交互**：
- 异构评审可视化：把共享同一 `ModelDefinition` 的 Reviewer 用同色连线标出，并在违反时于 Dry Run 产生 `HETEROGENEITY_VIOLATION` finding。UI 只做提示，判定权在 Preflight。
- 模型绑定下拉只列出该 endpoint 下 `enabled` 的模型；绑定后卡片立即显示该模型的 reproducibility 徽章。
- `forbidden_capabilities` 以「禁止」图标 + 删除线样式呈现（Reviewer 只读、Writer 不得改 Claim truth、ExperimentEngineer 禁止外部发布）。
- Template 切换为破坏性操作：若已有自定义绑定，提示将覆盖并列出差异。

**验收**：切换 Template 后 Agent 卡片数与角色定义一致；同模型 Reviewer 有视觉提示；无权限的能力项不可勾选。

---

## 6. Part 4 — Protocol & Dry Run Gate（Plan 域 · 核心闸门）

**目标**：把「启动前必须验证」变成用户能读懂、能定位、能修的一道门。

**布局**：左右分栏。左：Protocol 源（`ProtocolSourceDto`，YAML 编辑器 + `POST /protocols/validate` 实时校验）。右：Dry Run 结果面板，分区为
`Status` / `Findings` / `Resolved Plan` / `Budget` / `Approvals` / `Risks`。

**数据契约**：`POST /protocols/validate`、`POST /projects/{id}/compile`（`CompileResultDto`：`plan_id, protocol_digest, findings[{code, severity, message}], successful`）、`POST /compiled-plans/{id}/preflight`（`PreflightReportDto`：`status: PASS|WARN|FAIL, findings[{code, severity, message, subject_ref}], estimated_cost: number|null, reserved_budget_ref, unresolved_risks[]`）、`DryRunProjectionDto`（`role_counts, agent_models, tools, workspaces, compute_profiles, budget_reservations[], estimated_cost_minor: number|null, approval_actions[]`）。

**关键交互（P1 硬要求）**：
- 顶部状态条三态：`PASS`（绿，启用 Start）/ `WARN`（橙，Start 可用但需确认勾选「我已知悉 N 项警告」）/ `FAIL`（红，Start 禁用）。
- Findings 按 severity 分组，每条显示 `code`（等宽 chip）+ `message` + `subject_ref`（可点击跳转到对应 Role/Agent/Model）。
- Resolved Plan 展示 `role_counts` 的激活/折叠投影：被折叠的 Role 以降透明度 + 「collapsed」标注呈现，不隐藏。
- Budget 区：`estimated_cost_minor` 与 `budget_reservations[]`；`estimated_cost_minor=null` 时大字显示 `UNKNOWN` 并说明原因（P4）。
- Approvals 区：列出 `approval_actions[]`，说明运行时会在何处中断。

**文案示例**：`Preflight failed · 3 errors · 1 warning — Start is disabled until errors are resolved.`

**验收**：`FAIL` 时 Start 按钮 `disabled` 且有 `aria-disabled` 与可见解释；`subject_ref` 跳转可用；修改 protocol 后自动重新 compile 并更新 `protocol_digest`。

---

## 7. Part 5 — Run Timeline（Run 域 · 签名屏）

**目标**：让一次运行在时间维度上完全可解释：谁在跑、用什么模型、调了什么工具、花了多少、被策略怎么判、失败如何重试。

**布局**：三区。
- **顶部状态条**：Run state（`RunDetailDto.state`）+ `manifest_digest`（等宽，可复制）+ 运行 controls（Pause / Resume / Cancel / Fork）+ 实时指示点（SSE 连接状态）。
- **中部**：双栏。左为 Phase/Task 泳道（`TaskDto`：`task_id, contract_id, agent_id, status, attempt`），右为事件流（`RunEventDto`：`event_id, type, schema_version, occurred_at, actor, scope, run_id, task_id, trace_id, payload`）。
- **底部抽屉**：选中事件后展开详情——Agent / Model / Tool / arguments（**redacted view**）/ result / artifacts / cost / latency / policy decision / retry 信息。

**数据契约**：`GET /runs/{id}`、`GET /runs/{id}/tasks`、`GET /runs/{id}/events`、`GET /runs/{id}/stream`（SSE，支持 cursor/resume）、`GET /runs/{id}/usage`。

**关键交互**：
- 事件按 `event_id` 去重（客户端必须实现幂等）；断线显示「Reconnecting · 已落后 N 条」，恢复后按 cursor 补齐，**禁止**用动画假装实时。
- 事件类型用图标 + 颜色区分：task / agent / tool / policy / budget / error / gate。
- `payload` 一律以 redacted 视图渲染：结构化展示但敏感值显示为 `***`；提供「复制 event_id + trace_id」而非复制全文。
- `attempt > 1` 的任务行显示重试次数徽章，hover 展示失败分类与退避时间。
- 干预动作（Pause / Cancel / Fork）需后果预览：Fork 会创建新 lineage 并要求确认是否同时替换模型（AGENTS.md §5：替换模型/Tool Set 必须产生 Manifest Revision 或 Fork）。

**验收**：SSE 重连后事件无重复无丢失；敏感参数在 DOM 中不可见；`manifest_digest` 一键复制；Cancel 后所有进行中 Task 收敛为终态且 UI 不再显示「进行中」。

---

## 8. Part 6 — Approvals & Interventions（Run 域）

**目标**：把「人类在环」做成可决策的队列，而不是弹窗噪音。

**布局**：常驻右侧抽屉 + 顶部待办计数徽章。每张审批卡 = `action` + `risk` + `policy_source` + `context` + 后果预览 + Approve/Deny。

**数据契约**：`GET /approvals`（`ApprovalDto`：`id, run_id, action, risk, context, policy_source, status, version`）、`POST /approvals/{id}/decide`（`ApprovalDecideDto`：`decision: "approve" | "deny"`）、`POST /runs/{id}/interventions`。

**关键交互（P5 硬要求）**：
- 每张卡展示后果预览：「Approving 将允许 ⟨action⟩，影响 ⟨N⟩ 个 Task，不产生 Manifest Revision」或「Replacing this model will create a Manifest Revision」。
- 门禁类型 chip 区分：`POLICY_GATE / BUDGET_GATE / QUALITY_GATE / HUMAN_GATE / SECURITY_GATE / PUBLISH_GATE`。
- Mutating 请求携带 `Idempotency-Key` 与 `If-Match: <version>`；版本冲突（409）渲染为「该审批已被他人处理，已刷新为最新状态」，禁止静默覆盖。
- 按 `risk` 排序，高风险置顶；支持键盘 `A` 批准 / `D` 拒绝（需焦点在卡上，且仍需确认高风险项）。
- 自治等级提示：显示当前 `GUARDED_AUTONOMOUS` 等级下哪些动作自动、哪些需审批。

**验收**：并发决策 409 有明确提示；Deny 后对应 Task 状态可见变化；禁止出现「Approve all」按钮。

---

## 9. Part 7 — Claims & Evidence Map（Evidence 域 · 差异化屏）

**目标**：让每个结论的来龙去脉可追溯，并让「未验证」在视觉上无所遁形。

**布局**：双视图切换。**Graph 视图**：Claim 节点 ↔ Evidence 节点 ↔ Source，关系边标注 `relation` 与 `strength`。**Table 视图**：Claim 列表（statement / status / 证据数 / 来源数 / 更新时间）。

**数据契约**：`ClaimMapDto`、`ClaimDto`（`id, statement, status`）、`EvidenceDto`（`id, source_ref, content_digest, run_id, experiment_run_id, artifact_id, image_digest, environment_digest, model_refs[], manifest_digest`）、`RelationDto`（`claim_id, evidence_id, relation, strength`）。

**关键交互（P2 硬要求）**：
- `status` 徽章四态：`PROPOSED`（灰虚线）、`VERIFIED`（绿实心）、`DISPUTED`（橙，存在 REFUTES 证据）、`REFUTED`（红）。**PROPOSED 必须呈现为未完成**，禁止与 VERIFIED 使用同一视觉权重。
- 点击 Claim 展开证据链：每条 Evidence 显示 `source_ref`、`content_digest`（等宽截断 + 可复制）、来源类型（literature / experiment / artifact）。
- Experiment 证据额外显示 `image_digest` 与 `environment_digest`，作为复现锚点。
- 矛盾处理：存在 `REFUTES` 关系时，Claim 转 `DISPUTED`，旧证据保留不删除，UI 显式并列展示矛盾双方。
- 升级路径：`promote_claim_to_verified` 是唯一升级入口；UI 不得提供「标记为已验证」这类绕过 gate 的控件。

**验收**：无证据的 Claim 视觉上明显未确认；REFUTES 后状态与配色同步变化；`content_digest` 可复制且完整（title 属性全量）。

---

## 10. Part 8 — Workspace & Experiments（Run 域）

**目标**：让实验的可复现状态一眼可见，并诚实呈现「不可复现」的情况。

**布局**：左侧文件树 / workspace 快照列表 + diff 视图；右侧实验表格（`experiment_run_id` / metrics / image digest / environment digest / reproduction）。

**数据契约**：`ExperimentViewDto`（`experiments[], reproduction_note`）、`ExperimentRunDto`（`experiment_run_id, artifact_ids[], image_digest, environment_digest, metrics, reproduction_available`）。

**关键交互**：
- 复现状态两态：`reproduction_available=true` → 绿 `Reproducible` + 展示 `image_digest` / `environment_digest`；`false` → 紫 `Not reproducible` + 展示 `reproduction_note` 原文（禁止美化或省略）。
- metrics 以键值表渲染，未知键显示原始 key，禁止猜测单位。
- Diff 视图为只读，标注「read-only snapshot」；不允许在 Console 内直接编辑运行中的 workspace。

**验收**：`reproduction_available=false` 时不出现任何「Reproducible」字样；`reproduction_note` 完整可见。

---

## 11. Part 9 — Budget & Usage（Govern 域）

**目标**：成本可见、预留可见、未知可见。

**布局**：顶部四张指标卡（Total estimated / Reserved / Unknown entries / Burn rate），中部按 `resource_type` 分组的用量表（`UsageEntryDto`：`entry_id, resource_type, quantity, unit, cost_status, estimated_cost_minor, actual_cost_minor, model_id, task_id`），右下按 Agent/Model 归因的堆叠条。

**数据契约**：`GET /runs/{id}/usage`（`BudgetViewDto`：`entries[], total_estimated_cost_minor, unknown_cost_entries, reservations[]`）。

**关键交互（P4 硬要求）**：
- `cost_status` 非已知 / `estimated_cost_minor=null` → 显示紫色 `UNKNOWN` 徽章，并在指标卡中单列 `Unknown entries: N`，**禁止**计入 total 或显示为 0。
- `actual_cost_minor` 与 `estimated_cost_minor` 并存时并列展示，标注哪个是结算值。
- `reservations[]` 展示预留与已用的对比条；超预留时转 `danger`。
- 预算扩张动作走审批（P5），带后果预览。

**验收**：构造 `unknown_cost_entries=3` 时，总额与未知项分别正确呈现且总额不含未知项；无数据时为空状态而非 0。

---

## 12. Part 10 — Audit, Export & Memory（Govern 域）

**目标**：一次性交付可审计、可导出、可复现的证据包；并对长期记忆施加治理。

**布局**：三 Tab。**Audit**：append-only 事件轨迹（时间倒序，支持按 actor/scope/type 过滤）。**Export**：`ExportBundleDto`（`run_id, run_state, manifest_digest, evidence[], claims[], usage, exported_from`）预览 + 导出按钮。**Memory**：MemoryWriteProposal 队列（来源 / 置信度 / 适用范围 / 过期策略），支持 approve / reject / delete。

**关键交互**：
- Audit 行展示 `actor`（System / Agent / User / Policy）与 `scope`，支持深链定位到原 Task。
- Export 前展示摘要（包含哪些证据、多少 Claim、usage 是否含未知项），导出为不可变包并展示 `manifest_digest`。
- Memory 卡片必须显示 provenance 与 confidence；无来源的条目不允许写入；删除为真实删除并可重建索引（AGENTS.md §8）。
- 观测隐私提示：Audit 视图只渲染 digest 与元数据，不渲染 prompt 全文（AGENTS.md §10）。

**验收**：导出包摘要与实际内容一致；Memory 无 provenance 条目被拒绝且有解释；Audit 中不含敏感参数原文。

---

## 13. 组件清单（生成时优先复用）

| 组件 | 用途 | 关键变体 |
| --- | --- | --- |
| `StatusBadge` | 统一状态呈现 | proposed / verified / disputed / refuted / unknown / pass / warn / fail |
| `ReproducibilityChip` | 模型与实验复现状态 | fully-reproducible / configuration-reproducible / not-reproducible |
| `DigestText` | digest / ID 展示 | 等宽 + 截断 + hover 全量 + 一键复制 |
| `FindingRow` | Preflight finding | severity（error / warning / info）+ code chip + subject_ref 跳转 |
| `RedactedView` | 脱敏参数渲染 | 结构化展示 + 敏感值 `***` |
| `ConsequencePreview` | 高风险动作后果 | 动作 / 影响范围 / 是否产生 Revision 或 Fork |
| `EmptyState` | 空状态 | 说明 + 引导动作（与零值明确区分） |
| `LiveIndicator` | SSE 连接 | live / reconnecting / behind-N / offline |
| `MetricCard` | 指标 | label + 值 + UNKNOWN 变体 |
| `ApprovalCard` | 审批 | gate 类型 chip + risk + 后果预览 + approve/deny |

---

## 14. 文案语气与术语表

**语气**：陈述事实、给出定位、不承诺结果。禁止「智能」「一键」「颠覆」「极致」等营销词；禁止用拟人化描述 Agent（它是组件，不是同事）。

| 英文 | 中文 | 说明 |
| --- | --- | --- |
| Run | 运行 | 一次完整科研执行 |
| Preflight | 预检 | 启动前的确定性校验门 |
| Dry run | 干运行 | 编译 + 预检的无副作用投影 |
| Claim / Evidence | 论断 / 证据 | 严禁把 Claim 直接渲染为「结论」 |
| Verified / Proposed / Disputed / Refuted | 已验证 / 待验证 / 存疑 / 已否证 | Claim 状态 |
| Manifest revision | 清单修订 | 运行中变更模型/Tool Set 的合规路径 |
| Fork | 分叉 | 创建新 lineage |
| Lease / Heartbeat | 租约 / 心跳 | 任务可靠性语义 |
| Redacted | 已脱敏 | 后端返回即脱敏，前端不得还原 |
| UNKNOWN | 未知 | 与 0、空值严格区分 |

---

## 15. 反模式清单（生成时必须拒绝）

1. 把 LLM 输出直接渲染为「结论」而不带 Claim 状态与来源。
2. 用进度条或打字机动画伪造执行进度（只有真实事件才推进）。
3. 用 0 / 占位符 / 骨架屏冒充未知成本或未探测指纹。
4. 渲染 API Key 明文、未脱敏错误原文或完整 prompt。
5. 用前端隐藏按钮代替授权（授权必须在 API 层）。
6. 把派生索引、缓存或 SSE 增量当作 Canonical State 展示（刷新后必须从 API 全量恢复）。
7. 提供「一键全部同意」「跳过预检」「标记为已验证」等绕过 gate 的控件。
8. 在 Preflight 未通过时提供可点击的启动入口。
9. `provider_fingerprint_available=false` 时宣称可完全复现。
10. 用颜色单通道传达状态（违反可访问性硬要求）。

---

## 16. 验收清单（DoD 草案）

- [ ] 每个屏幕实现完整状态矩阵（empty / loading / error / partial / forbidden / stale / live）
- [ ] 五条不可协商规则有对应可视化与回归用例（P1–P5）
- [ ] DTO 字段零编造；缺失字段以 TODO + 端点建议标注
- [ ] 键盘可达全部交互；状态四重编码；焦点环可见
- [ ] SSE 去重与断线重连有测试覆盖
- [ ] 敏感数据不在 DOM 中出现（针对 Part 5/7 的专项断言）
- [ ] TypeScript strict 通过；ESLint / dependency-cruiser 边界门禁通过
- [ ] UI 不 import 后端 Domain 概念（架构断言，对应 ADR-0008）
- [ ] 与 `docs/api/openapi.m13.json` 契约测试一致（后端 schema 漂移可被发现）
