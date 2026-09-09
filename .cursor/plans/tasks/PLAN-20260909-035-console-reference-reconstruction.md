---
id: PLAN-20260909-035
slug: console-reference-reconstruction
title: Console 原型逐页复刻与隔离示例数据
status: DONE
created_at: 2026-09-09
updated_at: 2026-09-10
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-09 用户要求按上传设计完整复刻前端，允许缺失后端使用标注的示例数据"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260910-037-console-reference-reconstruction.md
memory_entries:
  - .cursor/memory/entries/MEM-20260910-018-quality-gate-mechanics.md
---

# PLAN-20260909-035 — Console 原型逐页复刻与隔离示例数据

## 目标

从上传 project(1).zip 的真实源码、设计令牌与参考图恢复高密度八域科研控制台，
不再以空白 GapLayout 代替设计页面。真实后端链路保留；示例数据、局部交互和
真实数据清晰分离，例子永不写入 PostgreSQL、Run、审批或 BudgetLedger。

## 范围

- 包含：33 条现有路由、外壳、共用组件、逐页设计内容、协议编辑器设计、
  带显著标识的隔离示例状态、响应式/键盘/中英文/主题、回归与视觉证据。
- 不包含：后端 Domain/API/schema/migration、真实模型费用、部署、Git 提交/推送；
  不覆盖并行工作中的 vite.config.ts、eslint.config.mjs、package.json、
  tests/tools/、tools/dev-backend/、tools/dev_backend.mjs。

## 架构与数据流

原始设计只作来源；产品采用现有 React/TypeScript/Vite，无 CDN、Babel runtime、
iframe 或脚本 eval。设计样例以独立前端模块持有可丢弃的内存状态，每页标明来源和
后端缺口。模式切换显式；真实后端失败不静默切换成假成功。既有真实 API、
Compile → Preflight → Start、幂等键、If-Match、SSE 与 URL Run 上下文不变。
Observability 不是 Domain truth，示例用量/预算/评估不进入真实账本。

## 验收条件

- [x] AC-01：上传来源与归档摘要核对，逐页映射与视觉差异可追溯。
- [x] AC-02：33 路由可达、未知路径正确、历史别名和上下文保留。
- [x] AC-03：原型独特的列表/卡片/分栏/图表/编辑器结构落地，不复用空白缺口页。
- [x] AC-04：示例模式标记清晰；过滤/选择/抽屉/示例编辑等交互真实工作且不发业务写请求。
- [x] AC-05：真实后端接口与编译预检启动门禁回归通过，无伪造生产事实。
- [x] AC-06：类型检查、lint、相关单元/E2E/构建与可访问性检查有实际证据。
- [x] AC-07：匹配视口的参考图对照、残余差异和不支持项如实记录。
- [x] AC-08：独立于旧 RECHECK-036 的新复检、交付记录和会话 checkpoint。

## 实施清单

- [x] STEP-01：规则/原型/实际 Git 和测试基线核对。
- [x] STEP-02：示例隔离边界、页面注册与公共设计组件。
- [x] STEP-03：组合与研究页面、协议编辑器、资源与运行页面。
- [x] STEP-04：分析/治理/运维/全局页、外壳和交互完善。
- [x] STEP-05：严格类型/lint/单测/E2E/视觉对照，修复回归。
- [x] STEP-06：新复检和交付文档，保留旧历史结论。

## 子代理使用

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | git | git log -3 --oneline; git status --short | HEAD 00f195a；并行开发后端改动独立保留 |
| EV-02 | STEP-01 | source | 上传 zip SHA-256 df70632fa6423d7d38984aeebfe5c6ab30d694043cbcf56b498c7cdeff54647a | 158 项；含源码、截图和协议编辑器子包 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-09 | 新授权允许明确标注的样例；不沿用旧计划禁止设计 fixture 的范围条件 | 用户明确要求 | 样例与真实业务边界分离，不扩大后端能力声明 |
| 2026-09-09 | 不重写旧完成记录；新建本次计划与复检 | 旧任务缺口页结构不等于用户现在要求的完整视觉 | 不以旧 PASS 推定本轮验收通过 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-09 | — | APPROVED | 用户明确授权实现 | 本轮原始请求 |
| 2026-09-09 | APPROVED | IN_PROGRESS | 读取规则与源码后开始重构 | EV-01..02 |

## 影响报告

- Domain/API/schema：零修改（`git status --short -- services/ packages/ adapters/ migrations/` 为空）。
- 安全/凭据：示例数据全程隔离（33 路由 example e2e 零业务请求实测）；无凭据字面量。
- 兼容性/迁移：既有路由/真实工作流保留（live e2e 3/3、API 回归 24/24）；无数据迁移。
- 上游版本：未安装或升级第三方包；design-fidelity 基线按 WP4.5 重批准（本轮视觉验收后）。
- 下一项任务：本计划 DONE；建议后续独立任务处理顶栏徽章间距（chrome 级）与
  并行后端的提交/推送（授权边界外）。
- 会话 checkpoint：本文件即最终状态；RECHECK-20260910-037 与交付记录
  `docs/frontend/CONSOLE_REFERENCE_RECONSTRUCTION_DELIVERY.md` 为验收与恢复入口。

## 2026-09-09 会话 9 恢复计划（当前执行权威）

本节扩充同一活动计划，不新建第二套任务，不把上轮部分实现视为完成。
授权来自本轮用户明确要求：先理解仓库、制定完整计划，再实施全局前端重构；
尤其包括此前未改造的实时页面。Git 提交、推送、发布和后端扩建仍不在范围内。

### 恢复基线与问题定义

- 工作区：`D:/research-system`；分支 `feat/web-console-hifi-rebuild`；
  HEAD `00f195a2a4ee1baae25eeeab35b26981ca5b54ad`。当前存在大量此前未提交改动。
- 已按 search → read 完整读取 `docs/history-session/7.md`，无剩余 next_cursor；
  历史结论仅用于定位，不替代本轮检查。
- 上传 `project(1).zip` 的 SHA-256 仍为
  `df70632fa6423d7d38984aeebfe5c6ab30d694043cbcf56b498c7cdeff54647a`。
  原型为 React 18 UMD/Babel 静态交付；产品实际为锁定的 React 19/TypeScript/Vite。
  复用视觉和组件职责，不把原型运行时、数据结构或 CDN 引入产品。
- 先前机械迁移产生冗长推断类型、过大函数和未闭环交互；本轮 typecheck 基线
  实测失败：`PanelCostBurn` 动态索引及 `RunDiffViewSection2` 可空值边界。
- 路由审计发现 `ops/compute` 未接入真实 `ClusterPanel`；实时入口全局依赖
  endpoint 加载，可能遮蔽本不依赖中转站的页面。将通过回归确定并修复。
- 旧 Gap 页面、旧实时业务面板、原型迁移页共享同一视觉标准；不得只做新示例页。

### 工程地图与不可变边界

| 层 / 所有者 | 输入与输出 | 本轮处理 |
| --- | --- | --- |
| `App` / navigation | URL route、Run context、source selection、用户偏好 | 单一所有者，别名/前进后退/刷新可恢复 |
| layout / components / styles | 同一套 tokens、密度、主题、表格、表单、状态、Overlay | 全局统一；不复制业务真相 |
| live feature adapters | 已有 API DTO → 展示模型 → 用户明确触发的 API action | 保留身份、ETag、幂等与错误分类 |
| example-console | 冻结设计 fixture → 页面内存视图/交互 | 显著标记、可丢弃、不调用业务 API |
| `services/api` / application / domain | Canonical State、运行/审批/预算/评测 | 只审计和回归，不扩建、不改 schema |
| observability / cost / evaluation | 脱敏遥测 / Ledger projection / EvalReport | 分离来源，UNKNOWN 不变零，分段不可比不伪比较 |
| engineering evidence | Plan、测试日志、截图、Recheck | 不进入产品 Memory/Run/Artifact/Evidence |

当前实现优先于历史文档中的 Next.js/SQLite 演进描述。保持 Accepted ADR 的
产品 UI 所有权、PostgreSQL Canonical State、Compile/Preflight/Freeze 和隐私边界，
不因本轮视觉任务升级栈或修改 ADR。外部 impeccable/shadcn Skill 当前不可见，
使用仓库自有组件与参考源码；不访问用户 home 补装。

### WP0 — 冻结现场、来源及验收基线

- [x] WP0.1：保存任务前相关改动清单、六个受保护文件当前摘要、来源源码摘要。
- [x] WP0.2：读取实际入口/路由/DTO/client/主要 hooks、关联 API 与现有 Tests；
  区分文档声明、旧验收证据和本轮实测，不宣称重新验证 PA-1R。
- [x] WP0.3：记录 typecheck/lint 基线，检查原型和已有截图，建立逐页验证矩阵。

### WP1 — 公共外壳、导航和来源语义

- [x] WP1.1：统一 220px 桌面侧栏、紧凑顶栏、面包屑、工作区/Run 身份、正文间距、
  滚动边界、窄屏导航、命令面板与全局入口；尺寸以参考源码实测校准。
- [x] WP1.2：主题、字体、密度、focus/hover/disabled、表格/卡片/面板与提示状态统一；
  CSS tokens 为唯一视觉参数入口，保留自托管字体和 reduced-motion。
- [x] WP1.3：33 路由、旧别名、未知路由、Run context、query/source、刷新与浏览器历史
  保留；补齐 compute（PageRenderer 接入真实 ClusterPanel 的 ComputePage），并让 command-center 正确使用独立大屏布局。
- [x] WP1.4：每页来源可见且可解释；auto 仅依据已登记能力选择，不依据请求错误；
  切换来源不携带示例对象进入真实 Run/审批/账本，页面切换重置示例需明确告知。
- [x] WP1.5：解除不必要的全局 endpoint 阻塞（liveRoutePolicy 仅首访/端点页依赖），保留明确首次接入入口；页面加载、
  后端错误、无 Run、空列表、权限不足分别呈现，不能统一当作无数据。

### WP2 — 原型原生化与交互闭环

- [x] WP2.1：修复类型基线；用领域内的展示类型替代巨大结构展开（preflightModel 取代
  DryRun 三变体联合类型），消除不安全索引与空值穿透，保持严格规则开启。
- [x] WP2.2：按实际职责拆分大组件和过长函数；保留设计 DOM/CSS 与交互状态流，
  不以压缩行数、关闭 lint、强断言或通用样板页规避门禁。
- [x] WP2.3：列表/卡片/看板、筛选、搜索、Tab、选择、详情抽屉、局部创建/编辑/删除
  等示例动作产生可观察结果；不存在能力的按钮禁用并解释，不保留无提示空回调。
- [x] WP2.4：示例协议 Form/源文档、分区导航、错误摘要、脏状态、预检展示对应当前
  页面样例，不触发真实运行；示例设置/审批/预算操作也不伪称持久化。
- [x] WP2.5：Overlay 支持 Escape、焦点进入/恢复/约束、可访问名称；中文/英文、
  深浅主题与响应式内容实际检查，图表不使用随机数据或伪 LIVE 状态。

### WP3 — 旧实时页面逐页重构（不是单独保留旧控制台）

按下表逐组实施。视觉布局可适应实际 DTO，但任何差异必须记录原因；
不为匹配设计数字而伪造真实数据。缺失功能可进入显式示例视图体验。

| 页面组 / 路由 | 必须保留或重构的设计结构 | 真实数据与操作边界 |
| --- | --- | --- |
| plan/overview | 摘要、预检/进度/论断指标、目标区、快捷入口 | 只聚合实际已加载值，缺失目标/自治级不虚构 |
| plan/protocol | 编辑器工具条、分区表单、源文档、错误摘要、预检报告、操作栏 | 模板 Compile→Preflight→Start；草稿 revision/ETag；无草稿预检接口不放行 |
| plan/team | Role/模板/Agent 分栏或卡片、模型绑定、设置 | 原角色与 Agent 分离；真实保存保持版本冲突和 LWW 提示 |
| portfolio/projects | 列表/看板/网格、详情和表单 | auto 示例；live 仅已知单项目设置，不假装多项目持久化 |
| portfolio/experiments | 队列/矩阵/详情、指标与制品 | 当前 Run 查询；无实验调度与复现能力明确标记 |
| portfolio/runs-history | 工具条、过滤列表、状态与运行选择 | 真实列表/详情；筛选范围说明；Run context 可恢复 |
| portfolio/compare | 运行选择、指标对照、差异分区 | 同名不等于可比；保留未知成本、单位及来源 |
| run/timeline | 运行条、任务/事件分栏、过滤和详情 | 具名 SSE、去重与断线续传；取消确认；不编造时长 |
| run/approvals | 摘要、待处理/历史、审批详情和后果提示 | 真实空态；decide If-Match/Idempotency-Key；无全批同意 |
| run/workspace | 文件/制品导航、预览区、元数据和不可用 Diff | API 无文件内容；Artifact ID 不作为下载链接 |
| library/prompts | 列表+编辑器、版本/A-B 视图 | 缺 API，显式示例局部状态 |
| library/datasets | 数据集表格、详情/字段/质量区 | 缺 API，示例注册/筛选不上传真实数据 |
| library/notebooks | 目录、编辑/预览与执行提示 | 缺 API，不执行代码 |
| library/model-registry | 模型列表、能力/兼容性、Probe 详情 | 真实模型身份与状态；Probe 明确动作；无虚假晋升 |
| library/lineage | 来源图、关系详情、过滤 | 仅显式 Claim/Evidence 引用；无猜测连边 |
| library/endpoints | 端点列表、健康/协议/凭据状态、接入入口 | 不回显密钥；保留真实测试/发现及错误；无 DELETE |
| library/setup | 分步向导与确认、发现/手动模型输入 | Base URL+API Key+Model ID；失败不伪成功；密钥不存偏好 |
| evidence/claims | 图/表切换、论断详情、来源关系与告警 | unsupported/disputed/degraded 完整呈现 |
| insights/reports | 报告列表、预览与表单 | 缺 API；真实 JSON export 不冒充 PDF/发布 |
| insights/cost-analytics | 摘要、维度分布、明细和可比区 | 只渲染服务端金额/币种/状态；无虚构日序列 |
| ops/alerts | 规则/收件箱、过滤与详情 | 示例，不从无关遥测推断已登记告警 |
| ops/incidents | 事故列表、时间线/影响和处理区 | 示例，不把失败 Run 改写为已登记事故 |
| ops/schedules | 计划表、状态与配置 | 示例，不控制后台 scheduler |
| ops/integrations | Provider 卡片、连接/能力详情 | 示例，不以 LLM Endpoint 代替工具凭据 |
| ops/data-health | 质量指标、分布/报告和详情 | 示例，不伪称全局质量已测量 |
| ops/matrix | 加载/空/错误/禁用/未知状态矩阵 | 静态 UI 状态说明，不标实时运维 |
| ops/compute | 节点摘要、Worker 列表、placement 详情 | 已有 cluster API 只读；不外推多卡/HPC |
| ops/observability | Telemetry/Cost/Eval 分区、趋势与故障状态 | 遥测非审计/成本真相；比较分段、missing、infra error、truncated 保留 |
| govern/budget | 预算/用量摘要、预留和流水 | 未知非零；原始 minor units；adjust 501 不启用 |
| govern/audit | Events/Export/Memory 分区 | 当前 Run 事件与 JSON 真导出；Memory 无 API |
| settings | 侧栏分区、偏好/工作区设置、不可用账号区 | 本地偏好与真实项目设置分开；无账户/Billing 伪保存 |
| notifications | 收件箱、分类与局部已读 | 示例无持久化；顶栏不显示假真实未读数 |
| command-center | 独立 2560×1440 仪表盘、统一退出/来源控制 | live 只复用已知查询；世界地图/预测仅示例 |

### WP4 — 回归和真实运行证据

- [x] WP4.1：新增纯函数测试：source policy、route/context/aliases、展示映射、
  空值/UNKNOWN/不可比、示例只读边界；现有单测不得削弱。
- [x] WP4.2：33 路由 example 模式浏览器实跑，监听所有业务 API 请求和 pageerror；
  至少覆盖关键交互，不能以截图存在代替交互通过。
- [x] WP4.3：live/auto 路由回归与真实 HTTP + Fake Ports E2E；验证错误不回退、
  缺少 endpoint 不遮蔽独立查询、真实工作流及副作用门禁。
- [x] WP4.4：1440×900、1280×800、窄屏及大屏检查；深浅主题/中英/密度；
  键盘、焦点恢复、滚动/溢出、字体加载和 reduced-motion。
- [x] WP4.5：同浏览器同视口对照原型渲染与产品截图，记录几何差异/必要数据标识
  及已知残差；不把不同文字、数据或测试替身下的像素差称为绝对 1:1。
- [x] WP4.6：串行执行质量门禁，修复本任务回归；既有独立失败单列，不篡改基线。

| Gate | 实际执行入口 | 必须满足 |
| --- | --- | --- |
| Web typecheck | `pnpm --dir apps/web typecheck` | exit 0 |
| Web lint | `pnpm --dir apps/web lint` | 0 errors / 0 warnings，不禁用规则 |
| Web unit | `pnpm --dir apps/web test` | 原回归和新增用例通过 |
| Browser | `pnpm --dir apps/web test:e2e` | 真实 Chromium 执行，逐项报告 |
| HTTP workflow | `pnpm --dir apps/web test:e2e:live` | 真实 API 进程，隔离 Fake Ports，不使用真实付费模型 |
| Build | `pnpm --dir apps/web build` | exit 0，非只过 TypeScript |
| Boundaries/tooling | `pnpm run check` | 不以 examples 绕过依赖、格式和架构检查 |
| API regression | 冻结 uv 环境执行关联 `tests/api` / contracts | 范围与结果落日志，缺环境明确记录 |
| Governance | 冻结 uv 环境执行 bundle / governance validators | 计划/文档/链接有效，不重生成发布 Manifest |
| Protected paths | 六个非本轮文件 hash 对比 + `git diff --check` | 无误覆盖、无无关提交 |

### WP5 — 独立复检和交付

- [x] WP5.1：从原始 AC 再检查最终 diff、视觉、操作和所有日志；新建本次 Recheck，
  不引用旧 RECHECK-036 的 PASS 代替本轮验收。
- [x] WP5.2：交付记录区分视觉结构、可用交互、真实 API、示例与后端缺口；
  补充启动、入口、切换方式、残余风险与回退步骤。
- [x] WP5.3：全部硬门禁及 AC 有证据后才 DONE；否则保留 IN_PROGRESS/BLOCKED
  与准确剩余项。最终回复前对会话 9 执行 checkpoint 并校验目标一致。

### 依赖、风险、恢复与授权

顺序：WP0 → WP1/WP2 → WP3 → WP4 → WP5。当前无可用独立子代理，根代理
分阶段实施与重新复核；不声称第三方独立审计。长期命令用 job_id 轮询并保存结果，
不将 running 当失败，不并发运行重型验证。

主要风险：巨型生成类型影响可维护性；样例文案假称成功；样例/真实来源串线；
旧控制台全局加载遮蔽页面；SSE/Run context 回归；不同视口和字体导致错判视觉；
未完成的并行改动导致门禁失败。每类分别以类型/交互/网络/路由/截图/哈希证据处理。

回退为任务路径白名单内逐项恢复本轮修改，不使用 reset --hard、clean、整仓格式化
或覆盖工作区。保护文件只做摘要核对。冻结设计归档、真实数据库/凭据、业务架构、
迁移和依赖锁文件均不改；需要扩大这些边界时停止相关部分并先记录新授权需求。

### 本轮追加证据与状态

| ID | 对应项 | 证据 | 当前结果 |
| --- | --- | --- | --- |
| EV-03 | WP0 | session 7 原始历史完整分页读取 | 仅恢复上下文，不作为完成证据 |
| EV-04 | WP0 | 上传文件重新计算 SHA-256 + README / 原型截图 | 摘要一致；参考依赖为静态原型，不直接运行进产品 |
| EV-05 | WP0 | typecheck job `7fbab1cf-323c-4265-8e73-582363fcc1ac` | exit 2，2 个类型错误（EV-07 已修复） |
| EV-06 | WP1 | registry / PageRenderer / LiveConsole 源码 | 发现 compute 漏接及全局 endpoint 耦合（EV-08 起修复） |
| EV-07 | WP2.1 | `pnpm --dir apps/web typecheck` | exit 0；EV-05 两错误已由先前会话修复 |
| EV-08 | WP1.3/1.5 | PageRenderer ops/compute→ComputePage(真实 useCluster)；liveRoutePolicy 仅首访/端点页加载 endpoints | 代码实测 + console-shell e2e 通过 |
| EV-09 | WP4.6 | `pnpm run check` exit 0；`pnpm --dir apps/web typecheck/lint/test/build` exit 0（70 单测）；root lint/format/typecheck/boundaries/tests 18/18 | 全部门禁绿；depcruise 0 违规（@/ 别名改为相对导入） |
| EV-10 | WP4.6 | protected-baseline.json 六文件 sha256 对比 | 全部 unchanged:true；git diff --check 干净 |
| EV-11 | WP1.4/2.3 | `playwright test console-shell a11y-viewport` | 23/23 通过（来源标记、别名、主题/语言持久化、Esc 焦点恢复、五档视口无溢出） |
| EV-12 | WP4.2 | 新增 `tests/e2e/example-isolation.spec.ts`：33 路由 example 实跑 + 项目搜索/抽屉 + 预检确认门 | 3/3 通过；全程零 /api 请求、零 pageerror |
| EV-13 | WP4.3/4.6 | `pnpm --dir apps/web test:e2e` 30/30；`test:e2e:live` 3/3（真实 FastAPI+Fake Ports）；`pytest tests/api` 草稿/联动/审批 24/24；services/packages/adapters/migrations 零 diff | 真实链路与副作用门禁回归通过 |
| EV-14 | WP4.4 | a11y 新增 1280×800 浅主题/英文/密度矩阵 + reduced-motion 字体加载测试 | 2/2 通过（data-theme=light、lang=en、data-density 生效、无横向溢出、fonts loaded>0） |
| EV-15 | WP4.5/AC-03/07 | `tools/console-reference/captureVisualCompare.mjs` 同视口采集 8 页 → 三组子代理对照 `docs/references/design/console-design/reference/` | 8/8 PASS；残差记录于 RECHECK-037（徽章替换为设计决策、导航措辞差异、兼容页无原型） |
| EV-16 | WP5 | `RECHECK-20260910-037`（AC-01..08 逐项 PASS）+ `docs/frontend/CONSOLE_REFERENCE_RECONSTRUCTION_DELIVERY.md` + `MEM-20260910-018` | 新复检独立于 036；交付记录区分五类事实；工程记忆入库 |

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-09 session 9 | IN_PROGRESS | IN_PROGRESS | 用户重新授权恢复；补全旧实时页面与逐页验收计划 | 本轮原始请求，EV-03..06 |
| 2026-09-10 session 10 | IN_PROGRESS | IN_PROGRESS | 全部门禁转绿；WP0-WP2 完成度有运行证据；进入 WP3 逐页审计与 WP4 完整 e2e/视觉对照 | EV-07..11 |
| 2026-09-10 session 10 | IN_PROGRESS | DONE | WP3-WP5 完成：example 隔离 e2e、live 回归、视觉对照 8/8 PASS、新 RECHECK-037 PASS、交付记录与工程记忆入库 | EV-12..16 |
