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
  `PATCH /projects/{id}`（重命名/归档）、`DELETE /projects/{id}`（G2/PLAN-061：
  被引用 409 并列出引用、默认项目 409、无引用 204）；`GET/PUT /projects/{id}/settings`
  按项目精确（WP-B）。侧边栏项目切换器（WorkspaceIdentity live）驱动
  `activeProject` 上下文，runs/drafts/settings 路径即时生效。
- 等级：PARTIAL（真实注册表与归属；看板/日历视图与逐资源全量隔离未交付）。
- 缺口（登记，G2）：项目删除只对无引用项目可用（有引用时须先自行处置研究数据，
  控制面不级联）；默认项目为合成基线不可删；agents/memory/experiments
  数据面暂单项目共享；成员/RBAC/租户隔离属 M18 deferred。

### `#/portfolio/experiments` — 实验
- 设计：`screens/Experiments.jsx`（队列/矩阵/日历视图）。
- API：`GET /runs/{run_id}/experiments` → `ExperimentViewDto`、
  `GET /projects/{id}/experiments`（项目级跨 run evidence 视图，WP-E）、
  `POST /projects/{id}/experiments`（计划预注册 DRAFT→PREREGISTERED；
  WP-A 起 SQLite 开发路径与 PG canonical 双支持，store 缺失仍如实 503）、
  `POST /experiments/{plan_id}/archive`、`GET /experiment-plans`（计划列表）、
  `POST /projects/{id}/experiments/{plan_id}/queue`（入队：入队即解析协议来源）、
  `GET /projects/{id}/experiment-queue`、
  `PATCH /experiment-queue/{entry_id}`（改期）、`DELETE /experiment-queue/{entry_id}`
  （取消）。
- 等级：PARTIAL。队列条目状态只来自域状态机（QUEUED/DISPATCHING/DISPATCHED/
  FAILED/CANCELLED），不发明进度字段；`reproduction_available` 恒 false，如实呈现。
  派发由控制面队列消费者按 `not_before`/创建时间顺序执行（与 `POST /runs` 同一装配链，
  进程内同步、串行推进）；认领过期（进程中断）重新派发 = at-least-once，不假装
  exactly-once；派发失败以 `FAILED + reason` 呈现，不静默重试。
- 缺口（登记）：复现执行无 API（保持禁用 → `disabledOperations: ["reproduce-run"]`）；
  日历/矩阵视图未实现（设计参照仍在 example 演示）；队列条目不发 outbox 事件。

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
- 等级：FULL。运行状态条、任务区、事件列表、筛选、详情抽屉；**重建就绪（读面）**面板
  直接渲染 `GET /runs/{id}` 的 `rebuild`（三态 + `missing` 行字段名），文案与
  `docs/api/CONTROL_PLANE_API.md` 同口径：记录自足 ≠ 重建必过、读面拒绝 ≠ 不可回填。
  同页另有**执行基质（读面）**两行：`执行体`（`GET /runs/{id}` 的
  `execution.execution_backend`；"未冻结"与"已冻结但未声明"分开说）与
  `运行时指纹`（`execution.runtime_fingerprint`，只报 `status`，非 `VERIFIED`
  时同显 `reason`）。两行同源——manifest 不落库，值都从 `manifest.frozen` payload
  读回，不设第二真相源（GOAL-007 EC-04）。
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
  （列表/元数据 verified/下载与白名单内联预览，WP-C）、
  `GET /runs/{id}/workspace-snapshots` + `GET /workspace-snapshots/{digest}/files` +
  `GET /workspace-snapshots/{left}/diff/{right}`（PLAN-058：run 记录过的快照 digest、
  单快照文件树、两快照文件级 diff）。
- 等级：FULL。产物浏览器已接入（store 缺失 503 如实呈现）；快照面板按 digest 只读
  （快照根未配置时端点 503 并说明原因）。
- 边界（登记）：快照面只回答"该 run 记录过哪些 digest、哪些仍保留"——控制面不持久化
  run→工作区绑定，不声称"这就是执行时的工作区"；文件级 diff 只比路径/大小/sha256，
  内容行级 diff 在制品面板；非白名单 media 一律下载（不内联执行）。

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
  （`LineageDto`: nodes/edges typed 投影，读取 persisted 引用构造并确定性排序）、
  `GET /projects/{id}/lineage`（`ProjectLineageDto`: 项目内各 Run 的**合并图**，
  同一节点 id 由多个 Run 贡献即 `shared=true`——跨 Run 关系由共享节点表达）。
- 等级：PARTIAL。当前 Run 的显式来源关系 + 项目级合并图均由后端投影；
  库资源以**未连边清单**列出。
- 缺口（登记）：数据集/提示词与 Run 的**引用关系无记录面**（协议定义与 RunManifest
  均不含资源 id，`evaluation_dataset_digest` 无法反查 LibraryResource）——响应内
  `reference_recording=NOT_RECORDED` 如实返回；禁止猜测连边；引用缺失显示断开关系
  而非补节点。

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
  `GET /runs/{id}/usage`、`GET /cost/daily`（跨 run 日序列，WP-D）、
  `GET /projects/{id}/cost-forecast`（项目级成本预测，G12/PLAN-057）。
- 等级：PARTIAL。日序列只含有数据的日期（无插值）；混合定价日不求和。
- 预测口径：只对**已计价**的天（ACTUAL/ESTIMATED/ZERO 且金额非空）取日均外推
  （`MEAN_OF_VALUED_DAYS` × `horizon_days`，1~90）；逐日返回
  `included_in_projection` 与 `exclusion_reason`（USAGE_UNKNOWN/
  MONETARY_UNAVAILABLE/NO_DATA/CURRENCY_CONFLICT/PARTIALLY_METERED/
  MIXED_PRICING）；样本为空或跨币种时 `projected_minor=null` +
  `unavailable_reason`（绝不隐式换算、绝不当 0）。
- 缺口（登记）：无按资源维度分解的时序预测与置信区间（方法只有日均外推，
  不含回归/季节性）；归属不明的条目只计数不猜测所属项目。

## Ops（6 设计页 + 2 兼容页）

### `#/ops/alerts` — 告警
- 设计：`screens/OpsScreens.jsx` `AlertsScreen`。等级：FULL。
- API：`GET /projects/{id}/ops/alerts`（派生收件箱：失败 Run、非健康端点、离线/排水 worker）；
  `GET/POST /projects/{id}/ops/alert-rules`、`PATCH/DELETE /ops/alert-rules/{rule_id}`（静音规则写面）。
- 口径：规则命中只打 `muted`/`muted_by` 标记并给出 `muted_count`，**不隐藏**告警；
  未配置 OpsStore 时规则面 503 并如实标注原因。

### `#/ops/incidents` — 事故
- 设计：`screens/Incidents.jsx`。等级：FULL。
- API：`GET /projects/{id}/ops/incidents`（已登记事故 + FAILED run 候选）；
  `POST /projects/{id}/ops/incidents`（登记，可关联来源 run）、
  `POST /ops/incidents/{id}/assign`、`POST /ops/incidents/{id}/close`（写处理结论）。
- 口径：候选 ≠ 已登记（失败 Run 不会自动变事故）；已关闭再处置 409；
  已登记的 run 从候选移出但仍留在已登记列表可追溯。

### `#/ops/schedules` — 调度
- 设计：`screens/OpsScreens.jsx` `SchedulesScreen`。等级：PARTIAL。
- API：`GET /ops/schedules`（调度定义 + 每项运行事实：job/interval/enabled/note/
  executor_attached/run_count/last_run_at/last_outcome/next_due_at + 作业词表 `jobs`）；
  `POST /ops/schedules`（登记定义）、`PATCH /ops/schedules/{name}`（启停 / 改间隔）、
  `POST /ops/schedules/{name}/trigger`（手动触发一次 pass）。
- 口径（EC-03）：执行体仍是既有进程内守护线程——定义只决定启停与间隔（下一轮生效），
  trigger 调用与定时 pass **相同的函数**并把运行事实写回读面（`运行事实` 列即证据）；
  没有执行体的作业如实标注且禁用触发；未跑过的定义显示"未运行 · UNKNOWN"（不伪造成功）。
- 缺口（登记）：不能新增执行路径（只能绑定既有 job 词表，无自定义 pass）、
  无删除/归档定义、无 cron 表达式与日历视图；`POST`/`PATCH` 需 `Idempotency-Key`。

### `#/ops/integrations` — 集成
- 设计：`screens/OpsScreens.jsx` `IntegrationsScreen`。等级：PARTIAL。
- API：`GET /tool-providers`（`ToolProviderListDto`：catalog `tool_providers`
  只读投影 + 三态健康；NATIVE=HEALTHY、外部未注册=UNKNOWN；目录只含 examples
  契约 + **已批准**注册）；`GET/POST /tool-provider-registrations`、
  `PATCH /tool-provider-registrations/{id}`、`/{id}/approve`、`/{id}/revoke`、
  `/{id}/health-check`（G15 / PLAN-060：登记 PENDING → 批准 ACTIVE →
  吊销 REVOKED 终态；信任级别由状态推导，注册方不能声明 BUILT_IN/VERIFIED；
  pin 必须是 `sha256:<hex>`；批准后 preflight/compile 立即可见）；
  `GET /tool-packs` + `POST /tool-packs/install`、`/{id}/approve-update`、
  `/{id}/revoke`（PLAN-065 / EC-02 console 操作入口：提交完整 manifest 文档，
  控制面重算内容 digest 并要求与声明值相等——不符 422 且 detail 落在面板内；
  **权限扩张只登记为待批准**，横幅展示候选 digest 与 diff 明细，表里 digest 列
  始终是生效版本，批准后才替换；REVOKE 终态、理由必填）。
- 缺口（登记）：provider 凭据绑定无写面；健康复核不含 schema digest 漂移比对；
  平台默认策略（`examples/config/policy.yaml`）没有 `tool_pack.*` 规则 ⇒ default
  DENY，真实部署下 console 写面需运维显式放行这三个能力（live 夹具层已放行，
  登记在 RECHECK-20260915-065）；不以模型端点接口代替。处置待拍板，见
  `docs/adr/ADR-0031-toolpack-capability-policy.md`（Status: `Proposed`）。

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
  unknown_cost_entries、reservations[]）、`GET /runs/{id}/cost-forecast`
  （run 级预留-消耗）、`GET /projects/{id}/cost-forecast`（项目级时序外推，
  G12/PLAN-057，与成本分析页共用面板）。
- 等级：PARTIAL。已知小计/未知条目/币种如实展示；金额单位比例无契约证据前
  显示原始 minor units。
- 缺口（登记）：run 级不外推未预留开销（口径 `RESERVED_ONLY` 随响应返回）；
  项目级外推见成本分析页。

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
| G6 | pause/resume 真实执行效果 | run/timeline 操作 | **已交付**（PLAN-048：PAUSED = 派发面停止认领该 run 的任务（claim_next 过滤，已持租约不撤销），本进程执行器在 phase 边界观测后零任务执行返回 PAUSED；resume 恢复派发，仅持有暂停上下文时继续剩余任务，否则 `continuation=NONE`。无抢占式中断；跨进程暂停上下文不持久化） |
| G7 | ~~alerts/incidents/schedules/data-health~~ | ops 四页 | **三页已交付写面**（PLAN-059：ops/alerts 的静音规则 CRUD + ops/incidents 的 declare/assign/close 走真实 `OpsStore`，写面被读面消费——规则只打 `muted/muted_by` 标记不隐藏告警、登记事故回链来源 run 的告警、已登记 run 移出候选；PLAN-066：ops/schedules 的定义登记/启停/触发，执行体仍是既有守护线程、trigger 复用同一条 pass、停用后 `run_count` 冻结；PLAN-045 的只读投影为底）；data-health 聚合报告仍禁用（见该页缺口）；prompts/datasets/notebooks 见 G7b，reports 见 G7a，integrations 见 G15 |
| G7a | ~~reports 只读视图~~ | insights/reports | **已交付**（PLAN-043：GET /runs/{id}/deliverable 读 M12 持久化交付物；生成/编辑/PDF/发布仍禁用） |
| G7b | ~~prompts/datasets/notebooks 库目录~~ | library 三页 | **已交付**（PLAN-044：GET/POST /projects/{id}/library + PATCH /library/{id}，kind 区分；版本树/上传/单元格执行仍禁用） |
| G8 | 文件浏览/预览；~~下载~~ | run/workspace | **已交付**：预览/下载（WP-C）；制品内容 Diff（PLAN-047：GET /artifacts/{a}/diff/{b} 行级 diff，二进制/超限如实标注）；**工作区快照文件树与文件级 Diff（PLAN-058：GET /workspace-snapshots/{digest}/files 与 /{left}/diff/{right}，按 digest 只读、只比元数据；需配置 RESEARCHOS_WORKSPACE_SNAPSHOT_ROOT）**；剩余受限 = 无 run→工作区绑定记录面（只能回答"记录过哪些快照"） |
| G9 | 全局血缘 | library/lineage | **已交付**（PLAN-043 Run 级投影 + PLAN-055 项目级合并图 `GET /projects/{id}/lineage`：共享节点即跨 Run 关系）；剩余受限 = 数据集/提示词与 Run 的引用关系无记录面（库资源只作未连边清单，响应内如实标注） |
| G10 | ~~删除端点（endpoint/model/agent/draft）~~ | library/endpoints、model-registry、run/approvals、plan/protocol | **已交付**（WP-B：四类 DELETE，被引用 409；契约基线不可删；memory 记录删除见 WP-F） |
| G11 | ~~审批生产接线~~ | run/approvals | **已交付**（WP-H：human-gate 注册点+续跑；空列表为正确状态） |
| G12 | 成本日序列/预测 | insights/cost-analytics、govern/budget | **已交付**（日序列 WP-D；Run 级预留-消耗 PLAN-046；**项目级时序外推 PLAN-057** = `GET /projects/{id}/cost-forecast`，只对已计价的天取日均外推，方法/样本/排除项随响应返回，跨币种不给金额）；剩余受限 = 无按资源维度分解的预测与置信区间 |
| G13 | ~~Memory 管理 API~~ | govern/audit Memory Tab | **已交付**（WP-F：§8 门链直提交；两阶段 decide 不提供） |
| G14 | ~~实验创建/排队/调度~~ | portfolio/experiments | **已交付**（WP-E 预注册/归档 + PLAN-052 队列/调度：`ExperimentQueueEntry` 域 + SQLite/PG 存储 + 原子认领派发器 + 五端点 + console live）；未交付面继续标注：复现执行、日历/矩阵视图 |
| G15 | ~~Tool Provider 管理面（install/approve/revoke）~~ | ops/integrations | **已交付**（PLAN-043 目录只读投影 + PLAN-060 注册治理写面：`GET/POST /tool-provider-registrations`、PATCH、approve/revoke/health-check 六端点 + SQLite 注册表 + 控制面面板；PENDING 不入目录、APPROVE 后以 USER_APPROVED 进目录并被 preflight/compile 消费、REVOKE 终态退出；pin 必须 `sha256:<hex>`）；剩余受限 = provider 凭据绑定仍无写面；ToolPack 供应链**后端**写面已由 PLAN-064 补上（`GET /tool-packs` + install/approve-update/revoke：扩张不生效直到批准、digest 由控制面重算自证、INSTALLED 的 digest 进入 preflight/compile 读面），**console 操作入口已由 PLAN-065 交付**（安装表单 + 待批准横幅（候选 digest 与 diff 明细，表中 digest 列始终是生效版本）+ 批准/吊销动作；stub 与 live e2e 各一条链；平台默认策略未放行 `tool_pack.*` ⇒ 真实部署需运维显式放行，见该项）；健康复核仍无 schema 漂移比对 |
| G16 | ~~Memory capability policy~~ | govern/audit Memory Tab | **已交付**（PLAN-049：memory.write 入 policy.yaml 镜像契约 + 门链 policy 阶段实时生效；GET /policy/capabilities 只读呈现逐 tier 判决；规则变更仍需改 policy.yaml） |

## 旧路由别名映射（T32 交付兼容）

`#/assets/endpoints`→`#/library/endpoints`；`#/assets/models`→`#/library/model-registry`；
`#/assets/compute`→`#/ops/compute`；`#/run/runs`→`#/portfolio/runs-history`；
`#/evidence/inspection`→`#/evidence/claims`；`#/govern/approvals`→`#/run/approvals`；
`#/govern/operations`→`#/ops/observability`；`#/setup`→`#/library/setup`。
