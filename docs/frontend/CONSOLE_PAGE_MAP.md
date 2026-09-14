# CONSOLE_PAGE_MAP — 逐页与逐操作映射（PLAN-20260908-034 T02）

设计来源：`docs/references/design/console-design/`（冻结交付包）。
API 路径为后端真实路径；浏览器经同源 `/api` 前缀访问（vite 代理剥离）。
`project_id` 按既有单项目能力处理（`example-project`），不伪造多项目目录。

支持等级：**FULL**＝数据与操作真实；**PARTIAL**＝真实数据 + 部分操作禁用；
**GAP**＝无后端能力，还原结构并逐操作禁用说明。
前端接入清单代码化于 `apps/web/src/navigation/pageSupport.ts`。

## 全局写入语义（适用所有页）

- 所有 POST/PATCH/PUT 必须带 `Idempotency-Key`（缺失 422；同 key 不同 payload 422；
  同 key 同 payload 重放首次响应）。豁免末段：validate/compile/preflight/dry-run/
  test/discover-models/probe。来源 `services/api/middleware.py`。
- `PATCH /llm-endpoints/{id}`、`PATCH /models/{id}`、`PATCH /agents/{id}`、
  `PUT /protocol-drafts/{id}`、`POST /approvals/{id}/decide` 需 `If-Match`
  （缺失 428，不匹配 412）。ETag＝canonical digest。
- 错误统一 RFC7807 `ProblemDto{type,title,status,detail,instance}`，detail 脱敏。
- 控制面 DELETE（WP-B G10）：`/llm-endpoints/{id}`、`/models/{id}`、
  `/agents/{id}`、`/protocol-drafts/{id}` 已提供（被引用 → 409；未知 → 404；
  均带 Idempotency-Key）；`/memory/{id}` 由 WP-F 提供。契约基线
  （examples role/template/agent）与其余资源仍不提供删除。

## Plan（3 页）

### `#/plan/overview` — 概览
- 设计：`components/AppShell.jsx` `PlanOverview`。
- 子视图：摘要头（manifest/目标数/团队/自治级）、预检/进度/论断三卡、研究目标、快捷跳转。
- 数据：聚合已加载的 Run 详情、tasks、claims、usage 与有效预检报告；无独立 overview API。
- 等级：PARTIAL。无运行/无预检时显示"未选择/未执行"，不自动发起预检探测。
- 缺口：原型 manifest 摘要字段（objectives/autonomy）无对应 DTO——映射到真实
  RunDetailDto/协议字段，缺失显示未提供。

### `#/plan/protocol` — 协议 & 预检
- 设计：`screens/DryRun.jsx` + `ProtocolEditor.jsx/.parts/.sections`；子包 README。
- 子视图：工具条、Form/YAML 切换、DIRTY、错误汇总、左侧七区块、粘性操作栏、右侧六区报告。
- API：`GET /protocol-templates`、`GET /protocol-templates/{id}`、
  `POST /protocol-drafts/validate`、`POST/GET/PUT /protocol-drafts*`（修订/ETag/412）、
  `GET /projects/{id}/protocol-drafts`（草稿库）、
  `GET /protocol-drafts/{id}/revisions[/{rev}]`（不可变修订只读）、
  `POST /protocols/validate`（编译器校验）、
  `POST /projects/{id}/compile|preflight|dry-run`（`ProtocolSourceDto{path |
  draft_id+draft_revision}`，WP-B）、
  `POST /projects/{id}/runs`（`protocol_path` 或 `{draft_id,draft_revision}`）。
- 等级：FULL（WP-B：草稿修订预检/启动已接入，与受控模板同源编译链；
  编辑器另接线 Compile/Recheck 动作）。
- Schema 真实顶层 `id/version/phases`，原型虚构对象不写入。

### `#/plan/team` — 团队
- 设计：`screens/Team.jsx`。
- 子视图：Role 目录、团队模板、Agent 列表/绑定编辑、项目设置。
- API：`GET /roles`、`GET /team-templates`、`POST /roles/custom`、
  `POST /team-templates/custom`、`GET/POST /projects/{id}/agents`、
  `PATCH /agents/{id}`（If-Match）、`POST /agents/{id}/clone`、
  `DELETE /agents/{id}`、`GET/PUT /projects/{id}/settings`。
- 等级：FULL（项目设置 PUT 无版本契约：last-write-wins，保存前展示变更并说明）。
- 参考协议预检：来源为项目设置 `reference_protocol`（WP-C，未配置诚实空态）；
  不再硬编码 demo 模板；不冒充运行预检，不改写已冻结 Manifest。
- 缺口：运行中冻结模型/工具集不可被"编辑团队"改写；policy 引用只读。

## Portfolio（4 页）

### `#/portfolio/projects` — 项目集
- 设计：`screens/Projects.jsx`（列表/看板/卡片三视图 + 详情）。
- API：`GET /projects`（真实注册表）、`POST /projects`（创建即带默认设置）、
  `PATCH /projects/{id}`（重命名/归档）；`GET/PUT /projects/{id}/settings`
  按项目精确（WP-B）。侧边栏项目切换器（WorkspaceIdentity live）驱动
  `activeProject` 上下文，runs/drafts/settings 路径即时生效。
- 等级：PARTIAL（真实注册表与归属；看板/日历视图与逐资源全量隔离未交付）。
- 缺口（登记，G2）：不提供项目删除（归档即终态）；agents/memory/experiments
  数据面暂单项目共享；成员/RBAC/租户隔离属 M18 deferred。

### `#/portfolio/experiments` — 实验
- 设计：`screens/Experiments.jsx`（队列/矩阵/日历视图）。
- API：`GET /runs/{run_id}/experiments` → `ExperimentViewDto`、
  `GET /projects/{id}/experiments`（项目级跨 run evidence 视图，WP-E）、
  `POST /projects/{id}/experiments`（计划预注册 DRAFT→PREREGISTERED；
  WP-A 起 SQLite 开发路径与 PG canonical 双支持，store 缺失仍如实 503）、
  `POST /experiments/{plan_id}/archive`。
- 等级：PARTIAL。域内无 queued/running 计划状态，不伪造队列；
  `reproduction_available` 恒 false，如实呈现。
- 缺口（登记）：排队/调度/日历无 API（保持禁用）；队列视图属 example 演示。

### `#/portfolio/runs-history` — 运行历史
- 设计：`screens/RunsHistory.jsx`。
- API：`GET /projects/{id}/runs`（created_at 倒序）、`GET /runs/{id}`。
- 等级：FULL。列表筛选（作用于已加载范围并注明）、选择、详情跳转、刷新恢复。

### `#/portfolio/compare` — 比较
- 设计：`screens/Compare.jsx`。
- API：多 Run 的 `GET /runs/{id}` + `/usage` + `/cost` + `/experiments`。
- 等级：PARTIAL。指标同名但单位/来源/可比条件不明时并列显示。
- 缺口：不计算虚假提升率/置信区间/排名。

## Run（3 页）

### `#/run/timeline` — 运行时间线
- 设计：`screens/Timeline.jsx`。
- API：`GET /runs/{id}`、`GET /runs/{id}/tasks`、`GET /runs/{id}/events`
  （SSE 具名帧：manifest.frozen/task.created/task.leased/task.completed/
  task.retry_scheduled/task.cancelled/run.completed/run.failed/claim.verified/
  claim.disputed/approval.decided；JSON replay + Last-Event-ID/cursor 续传）。
- 等级：FULL。运行状态条、任务区、事件列表、筛选、详情抽屉。
- 缺口：阶段时间/依赖映射缺失时保留区域并说明，不以任务顺序编造泳道时长。

### `#/run/approvals` — 审批
- 设计：`screens/Approvals.jsx`。
- API：`GET /approvals`、`GET /runs/{id}/approvals`（WP-B：选中审批所属 run
  的完整历史，含已裁决）、`POST /approvals/{id}/decide`（approve|deny；
  409 Already Decided/Run Mismatch/Invalid Transition；428/412 版本；
  执行上下文丢失 503 且审批不被消费，WP-H）。
- 等级：FULL（WP-H：human-gate 协议暂停时真实注册 ApprovalRecord 并置
  WAITING_FOR_APPROVAL；approve 续跑、deny→FAILED）。
- 语义：无审批门的 run 列表为空是正确状态；不伪造待决数量；无"一键全部同意"。

### `#/run/workspace` — 工作区
- 设计：`screens/Workspace.jsx`。
- API：`GET /runs/{id}/experiments`、`/evidence`、`/export`、
  `GET /runs/{id}/artifacts` + `GET /artifacts/{id}` + `GET /artifacts/{id}/content`
  （列表/元数据 verified/下载与白名单内联预览，WP-C）。
- 等级：PARTIAL。产物浏览器已接入（store 缺失 503 如实呈现）。
- 缺口（登记）：文件级 Diff 仍无接口；非白名单 media 一律下载（不内联执行）。

## Library（7 页）

### `#/library/prompts` — 提示词
- 设计：`screens/Prompts.jsx`。等级：PARTIAL。
- API：`GET /projects/{id}/library?kind=prompt`（`LibraryResourceDto` 列表）、
  `POST /projects/{id}/library`（kind=prompt）、`PATCH /library/{id}`（重命名/归档）。
- 缺口（登记）：版本树与 A-B 无 API——结构不渲染；列表/详情为真实目录事实。

### `#/library/datasets` — 数据集
- 设计：`screens/Datasets.jsx`。等级：PARTIAL。
- API：`GET /projects/{id}/library?kind=dataset`、`POST ...`（kind=dataset）、
  `PATCH /library/{id}`。
- 缺口（登记）：上传与字段 schema 无 API；dataset_id/version/digest 的评测输入
  仍由 eval spec 承载（本域只登记目录引用，不与其耦合）。

### `#/library/notebooks` — 笔记
- 设计：`screens/Notebooks.jsx`。等级：PARTIAL。
- API：`GET /projects/{id}/library?kind=notebook`、`POST ...`（kind=notebook）、
  `PATCH /library/{id}`。
- 缺口（登记）：单元格编辑与执行无 API。

### `#/library/model-registry` — 模型注册
- 设计：`screens/OpsScreens.jsx` `ModelRegistryScreen`。
- API：`GET/POST /models`、`GET/PATCH /models/{id}`（If-Match）、
  `POST /models/{id}/probe` → `ProbeResultDto`（含 fingerprint、
  provider_fingerprint_available、capability_failures）、
  `GET /models/{id}/compatibility` → `CompatibilityViewDto`。
- 等级：FULL（capability 闭集 12 项、status 4 态、source 5 态如实呈现）。
- WP-B：`DELETE /models/{id}` 已接入（被 agent 显式绑定 → 409，UI 呈现错误）；
  `hard_capability_requirements` 为合并目录投影（role/profile 声明，非恒空）。
- 缺口：`endpoint_healthy_hint` 恒 null——不渲染"已验证兼容性"；
  无训练制品仓库/部署/晋升。

### `#/library/lineage` — 血缘
- 设计：`screens/Lineage.jsx`。
- API：`GET /runs/{id}/claims`（`ClaimDto.relations[]`: claim_id/evidence_id/
  relation/strength）、`GET /runs/{id}/evidence`（source_ref/artifact_id/
  image_digest/model_refs/manifest_digest）、`GET /runs/{id}/lineage`
  （`LineageDto`: nodes/edges typed 投影，读取 persisted 引用构造并确定性排序）。
- 等级：PARTIAL。当前 Run 的显式来源关系（source→evidence→claim→artifact/model）
  由后端投影。
- 缺口（登记）：全局数据集/提示词血缘无 API（G9）——标注不可用；禁止猜测连边；
  引用缺失显示断开关系而非补节点。

### `#/library/endpoints` — 中转站
- 设计：`screens/Endpoints.jsx`。
- API：`GET/POST /llm-endpoints`、`GET/PATCH/DELETE /llm-endpoints/{id}`（If-Match；
  protocol 不可改；被用户模型引用 → DELETE 409）、`POST .../test`（真实 chat，
  需本 endpoint 模型）、`POST .../discover-models`、`GET .../health`。
- 等级：FULL。凭据不回显（ReadDto 无 api_key；`credential: configured|missing`）。
- WP-B（G10）：详情抽屉提供删除动作（确认 + 409 文案；凭据进程内，随重启消散）。

### `#/library/setup` — 首次接入向导
- 设计：`screens/Setup.jsx`。
- API：`POST /llm-endpoints` + `POST /models` + `POST .../test`（真实流程
  Base URL + API Key + Model ID）。
- 等级：FULL。已有配置不因重进被覆盖；API Key 仅表单短暂存在。

## Evidence（1 页）

### `#/evidence/claims` — 论断
- 设计：`screens/Claims.jsx`（图谱/表格切换 + 详情联动）。
- API：`GET /runs/{id}/claims`（unsupported_claims/contradictory_claims/degraded）、
  `GET /runs/{id}/evidence`。
- 等级：FULL。关系仅来自 `ClaimDto.relations`；degraded 如实呈现。
- 缺口（登记）：人工裁定/独立 Review 无接口——禁用。

## Insights（2 页）

### `#/insights/reports` — 报告
- 设计：`screens/Reports.jsx`。等级：PARTIAL。
- API：`GET /runs/{id}/deliverable`（`DeliverableDto`：available/reason/
  artifact_id/artifact_digest/deliverable）读取既有 M12 `build_deliverable`
  持久化产物 `deliverable.json`；未产出交付物的 Run 返回 available=false。
- 缺口（登记）：报告生成/编辑/PDF/发布无 API——生成动作禁用；可另链接真实
  `GET /runs/{id}/export`（JSON bundle），不冒充报告。

### `#/insights/cost-analytics` — 成本分析
- 设计：`screens/CostAnalytics.jsx`。
- API：`GET /runs/{id}/cost`（`CostViewDto`：dimensions[].amount.status 闭集
  ACTUAL/ESTIMATED/MONETARY_UNAVAILABLE/USAGE_UNKNOWN/ZERO/NO_DATA/
  CURRENCY_CONFLICT/PARTIALLY_METERED；pricing_frozen/degraded_reason）、
  `GET /runs/{id}/usage`、`GET /cost/daily`（跨 run 日序列，WP-D）。
- 等级：PARTIAL。日序列只含有数据的日期（无插值）；混合定价日不求和。
- 缺口（登记）：预测/前瞻无 API——不画预测曲线。

## Ops（6 设计页 + 2 兼容页）

### `#/ops/alerts` — 告警
- 设计：`screens/OpsScreens.jsx` `AlertsScreen`。等级：PARTIAL。
- API：`GET /projects/{id}/ops/alerts`（派生只读收件箱：失败 Run、非健康端点、
  离线/排水 worker）。
- 缺口（登记）：无告警规则 CRUD API——规则配置与处理保持禁用。

### `#/ops/incidents` — 事故
- 设计：`screens/Incidents.jsx`。等级：PARTIAL。
- API：`GET /projects/{id}/ops/incidents`（FAILED run 候选列表）。
- 缺口（登记）：无 declare/assign/close 处置工作流；失败 Run 不自动登记为事故。

### `#/ops/schedules` — 调度
- 设计：`screens/OpsScreens.jsx` `SchedulesScreen`。等级：PARTIAL。
- API：`GET /ops/schedules`（进程内 4 个守护 scheduler 的配置事实：interval/
  purpose/enabled）。
- 缺口（登记）：无用户可见创建/启停/触发 API。

### `#/ops/integrations` — 集成
- 设计：`screens/OpsScreens.jsx` `IntegrationsScreen`。等级：PARTIAL。
- API：`GET /tool-providers`（`ToolProviderListDto`：catalog `tool_providers`
  只读投影 + 三态健康；NATIVE=HEALTHY、外部未注册=UNKNOWN）。
- 缺口（登记）：install/approve/revoke 属供应链治理面（G15），不提供；不以模型
  端点接口代替。

### `#/ops/data-health` — 数据健康
- 设计：`screens/DataHealth.jsx`。等级：PARTIAL。
- API：`GET /projects/{id}/ops/data-health`（端点健康计数、dataset 目录计数、
  artifact 抽样校验）。
- 缺口（登记）：无聚合质量报告 API；仅呈现既有状态的可观测计数与校验结果。

### `#/ops/matrix` — 状态矩阵
- 设计：`screens/States.jsx`。等级：GAP（说明性质）。
- 交付明确标注"界面状态说明"：呈现加载/空/错误/权限/未知等组件状态，
  不冒充实时运维状态。

### `#/ops/compute` — 计算节点（兼容页，无设计稿）
- 保留现有能力：`GET /cluster/workers`（worker_ref 短 digest、state、
  heartbeat、gpu_probe_digest）、`GET /runs/{id}/placement`。
- 等级：FULL（只读）。不外推跨地域/多卡/HPC。

### `#/ops/observability` — 运维观测（兼容页，无设计稿）
- 保留：`GET /runs/{id}/telemetry`（tasks/outbox/sink 计数）、
  `GET /runs/{id}/cost`、`GET /evaluations/trend`（segments/comparisons/
  divergences/missing/truncated）。
- 等级：FULL（只读）。保留分段、不兼容、缺失与截断语义。

## Govern（2 页）

### `#/govern/budget` — 预算
- 设计：`screens/Budget.jsx`。
- API：`GET /runs/{id}/usage`（`BudgetViewDto`：entries[]、
  total_estimated_cost_minor null=不完整绝不补 0、known_cost_subtotal_minor、
  unknown_cost_entries、reservations[]）。
- 等级：PARTIAL。已知小计/未知条目/币种如实展示；金额单位比例无契约证据前
  显示原始 minor units。
- 缺口（登记）：预算调整无契约（interventions budget_adjust 恒 501）——禁用。

### `#/govern/audit` — 审计与导出
- 设计：`screens/Govern.jsx`（Audit/Export/Memory 三 Tab）。
- API：`GET /runs/{run_id}/events`（JSON replay）标作**运行事件记录**；
  `GET /runs/{id}/export` 真实导出（JSON bundle 本地下载）；
  Memory Tab：`GET /projects/{id}/memory`、`POST /memory/proposals`、
  `DELETE /memory/{id}`（WP-F 完整 §8 门链直提交；WP-A 起 SQLite 开发路径
  与 PG canonical 双支持）。
- 等级：PARTIAL。
- 缺口（登记）：无全平台审计 API；绝不读取 `.cursor/memory` 补充。

## 全局（3 页）

### `#/settings` — 设置
- 设计：`screens/Settings.jsx`（Profile/Notifications/API Keys/Security/
  Workspace/Preferences/Billing 七分区）。
- 真实：主题/语言/密度＝本地偏好；Workspace 分区走 `GET/PUT /projects/{id}/settings`
  （team_template/model profile/budget policy/workspace/参考协议/compute/policy）。
- 等级：PARTIAL。账户、平台 API Key、双因素、Billing 无 API——锁定并说明
  （禁用判定唯一来源 `pageSupport.disabledOperations`）。

### `#/notifications` — 通知中心
- 设计：`screens/Notifications.jsx`。等级：PARTIAL。
- API：`GET /notifications?limit=`（outbox 事件白名单投影，WP-G；不含 payload
  内容）、`POST /notifications/{id}/read`（已读 view-state 持久化）。
- 缺口（登记）：无实时推送通道；数量只来自当前页投影，不虚构未读总数。

### `#/command-center` — 指挥中心
- 设计：`Command Center.html`（独立 2560×1440 大屏）。
- 复用已验证查询：runs/tasks/claims/usage/cost/telemetry/cluster。
- 等级：PARTIAL。跨项目统计、全球节点位置、预测等缺失区域保留版式并说明；
  刷新时间与实时连接状态分别展示；不建立第二套运行状态。

## 后端能力缺口总登记（本次不扩建）

| # | 缺口 | 影响页面 | 处置 |
| --- | --- | --- | --- |
| G1 | ~~草稿修订预检/启动接口~~ | plan/protocol | **已交付**（WP-B：双来源编译链，等级 FULL） |
| G2 | 多项目管理 | portfolio/projects | **注册表已交付**（WP-A：GET/POST/PATCH /projects + 活动项目上下文 + runs/settings/drafts 真实归属）；项目删除不提供（归档终态），成员/RBAC 属 M18 deferred |
| G3 | ~~通知持久化~~ | notifications、TopBar 铃铛 | **已交付**（WP-G：事件投影+已读；无推送通道） |
| G4 | 账户/身份/Billing/平台 API Keys | settings 四分区 | 锁定+说明（M18/M19 deferred） |
| G5 | ~~预算调整契约~~ | govern/budget | **已交付**（PLAN-046：interventions budget_adjust 走 BudgetLedger 的 release+reserve；replace_agent 语义变更仍 501；预测只覆盖已预留额度） |
| G6 | pause/resume 真实执行效果 | run/timeline 操作 | **已接线**（A5：按钮按能力标注；仍属控制面状态迁移） |
| G7 | ~~alerts/incidents/schedules/data-health~~ | ops 四页 | **只读投影已交付**（PLAN-045：ops/alerts・incidents・schedules・data-health；规则 CRUD/处置流/用户调度/聚合报告仍禁用，见各页缺口）；prompts/datasets/notebooks 见 G7b，reports 见 G7a，integrations 见 G15 |
| G7a | ~~reports 只读视图~~ | insights/reports | **已交付**（PLAN-043：GET /runs/{id}/deliverable 读 M12 持久化交付物；生成/编辑/PDF/发布仍禁用） |
| G7b | ~~prompts/datasets/notebooks 库目录~~ | library 三页 | **已交付**（PLAN-044：GET/POST /projects/{id}/library + PATCH /library/{id}，kind 区分；版本树/上传/单元格执行仍禁用） |
| G8 | 文件浏览/预览；~~下载~~ | run/workspace | **预览/下载已交付**（WP-C）；**制品内容 Diff 已交付**（PLAN-047：GET /artifacts/{a}/diff/{b} 行级 diff，二进制/超限如实标注）；工作区文件树与文件级快照 Diff 仍无接口 |
| G9 | 全局血缘 | library/lineage | **Run 级投影已交付**（PLAN-043：GET /runs/{id}/lineage typed nodes/edges）；全局跨 run 仍无 API |
| G10 | ~~删除端点（endpoint/model/agent/draft）~~ | library/endpoints、model-registry、run/approvals、plan/protocol | **已交付**（WP-B：四类 DELETE，被引用 409；契约基线不可删；memory 记录删除见 WP-F） |
| G11 | ~~审批生产接线~~ | run/approvals | **已交付**（WP-H：human-gate 注册点+续跑；空列表为正确状态） |
| G12 | 成本日序列~~/预测~~ | insights/cost-analytics、govern/budget | **日序列已交付**（WP-D）；**Run 级预留-消耗预测已交付**（PLAN-046：GET /runs/{id}/cost-forecast，仅已预留额度，无 burn-rate 外推）；跨 run/时间序列预测仍无 API |
| G13 | ~~Memory 管理 API~~ | govern/audit Memory Tab | **已交付**（WP-F：§8 门链直提交；两阶段 decide 不提供） |
| G14 | 实验~~创建~~/排队/调度 | portfolio/experiments | **预注册/归档已交付**（WP-E）；queue/schedule 无域支撑保持禁用 |
| G15 | Tool Provider 管理面（install/approve/revoke） | ops/integrations | **目录已交付**（PLAN-043：GET /tool-providers 只读投影 + 三态健康）；管理动作未提供（供应链治理） |
| G16 | Memory capability policy（memory.write 入 policy.yaml 镜像契约） | govern/audit | follow-up（_CAPABILITY_SCOPE 单值映射限制） |

## 旧路由别名映射（T32 交付兼容）

`#/assets/endpoints`→`#/library/endpoints`；`#/assets/models`→`#/library/model-registry`；
`#/assets/compute`→`#/ops/compute`；`#/run/runs`→`#/portfolio/runs-history`；
`#/evidence/inspection`→`#/evidence/claims`；`#/govern/approvals`→`#/run/approvals`；
`#/govern/operations`→`#/ops/observability`；`#/setup`→`#/library/setup`。
