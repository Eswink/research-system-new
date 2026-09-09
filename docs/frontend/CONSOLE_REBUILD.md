# Research Console 全站重建设计说明（CONSOLE_REBUILD）

> 状态：v2（2026-09-08）。当前八域设计授权计划：
> [PLAN-20260908-034](../../.cursor/plans/tasks/PLAN-20260908-034-console-design-reconstruction.md)；
> 设计来源：[console-design 完整交付包归档](../references/design/console-design/ARCHIVE_NOTE.md)
> （八域、33 规范路由、Command Center 大屏）。
> 历史：v1（PLAN-20260908-033，五域 + protocol-visual-editor 子包）保留于 git 历史，
> 其结论与证据不被覆写；逐页/逐操作映射与缺口见
> [CONSOLE_PAGE_MAP.md](CONSOLE_PAGE_MAP.md)，交付清单见 [CONSOLE_DELIVERY.md](CONSOLE_DELIVERY.md)。
> 本文档是全站重建期间的单一 UI 规范真相；与 [UI_DESIGN_PROMPTS.md](UI_DESIGN_PROMPTS.md)
> 冲突时以本文档 + DTO 为准。

## 0. v2 八域外壳（2026-09-08）

- 侧栏 220px（折叠 56px）、顶栏 48px、工作区间距 16px；八域展开子导航 + 面包屑 +
  命令面板（⌘K）+ 独立大屏入口。
- 33 条规范路由各有独立页面身份（`navigation/registry.ts` + `PageRenderer.tsx`）；
  旧别名（assets/*、govern/approvals、run/runs、evidence/inspection、setup、
  govern/operations）经 `LEGACY_ALIASES` 映射；未知地址进入未找到页。
- 页面/操作支持等级登记于 `navigation/pageSupport.ts`（与 CONSOLE_PAGE_MAP.md 同源）；
  缺口页用 GapPage 脚手架呈现结构 + 禁用操作 + 原因，不替换为统一"即将推出"卡片。
- 字体自托管（[CONSOLE_FONTS.md](CONSOLE_FONTS.md)），生产不加载 Google Fonts/CDN/Babel。
- 协议编辑器：YAML 文档树定点编辑无损往返；模板同源预检/启动；自定义草稿预检禁用（G1）。
- 实时事件：消费服务端具名 SSE 帧（`NAMED_SSE_EVENTS`），去重/重连/Run 切换。

## 1. 不变量（与 AGENTS.md / UI_DESIGN_PROMPTS 对齐）

- P1 Preflight 先于执行：FAIL 阻断启动；WARN 需显式确认；服务端仍做最终预检。
- P3 模型漂移可见：`provider_fingerprint_available=false` 时渲染
  "Configuration reproducible / provider fingerprint unavailable"，禁止渲染 Fully reproducible。
- P4 不确定就是不确定：`estimated_cost_minor=null` / unknown 计数 > 0 → 显示 UNKNOWN，不用 0 补齐。
- P5 默认拒绝：高风险动作带后果预览；无"一键全部同意"。
- 状态四重编码（形状+图标+文字+颜色）；键盘可达；错误关联输入；抽屉关闭恢复焦点。
- 浏览器持久化仅限主题/密度/语言/编辑模式偏好；不持久化凭据、运行真相、协议正文。
- 不加载 Google Fonts CDN / Babel standalone；保持现有 CSP；字体用本地回退栈。
- 工程版本展示只来自根 `VERSION`（当前 0.4.0）；不采用设计稿 `protocol_version 1.4`。

## 2. 技术栈与目录

React 19 + TypeScript + Vite + CSS 自定义属性 + CSS Modules（不引入 Tailwind/shadcn/Next.js）。

```text
apps/web/src/
  styles/      tokens.css（逐值复用设计包令牌）、base.css、themes、density
  layout/      AppShell、Sidebar、TopBar、SecondaryTabs、ContextHost
  components/  Panel、Button、Field、Chip、StatusBadge、Table、EmptyState、
               ErrorState、ConfirmDialog、Drawer、Tabs、Tooltip、Icon
  navigation/  routes.ts（类型化 hash 路由）、useHashRoute
  i18n/        zh.ts、en.ts、I18nProvider（中文默认）
  features/    现有功能目录保留；逐页换肤并接入外壳
```

## 3. 信息架构与页面清单（全站）

侧边导航 = 5 个信息域；首次接入向导为独立流程（无端点或显式"添加中转站"时全屏接管）。

| 域 | 路由（hash） | 页面 | 来源功能（迁移自） | 二级 Tab |
| --- | --- | --- | --- | --- |
| Plan 规划 | `#/plan/protocol` | 协议编辑与预检 | DryRunPanel + ReportView + ProjectionTable（重写为编辑器） | 编辑器 / 报告 |
| Plan 规划 | `#/plan/team` | 团队与模型绑定 | TeamPage + EndpointsHome 设置面 | 角色/Agents/模板/设置 |
| Run 运行 | `#/run/runs` | 运行列表与详情 | RunPanel + RunActions + TimelineView | 任务 / 时间线 / 事件 |
| Run 运行 | `#/run/workspace` | 工作区与实验 | WorkspaceView | 实验 / 导出 |
| Evidence 证据 | `#/evidence/inspection` | 证据检查 | InspectionPanel（claims/evidence/reviews） | Claims / Evidence / Reviews |
| Assets 资产 | `#/assets/endpoints` | 中转站管理 | EndpointsHome | 端点 / 健康 |
| Assets 资产 | `#/assets/models` | 模型目录 | ModelsPage | 模型 / 兼容性 |
| Assets 资产 | `#/assets/compute` | 计算节点 | ClusterPanel（只读） | — |
| Govern 治理 | `#/govern/approvals` | 审批 | ApprovalsPanel | — |
| Govern 治理 | `#/govern/operations` | 运维观测 | OperationsPanel（用量/成本/遥测/评估趋势） | 用量 / 遥测 / 评估 |
| （独立流程） | `#/setup` | 首次接入向导 | RelayWizard | 分步向导 |

顶部上下文条：当前选中 Run ID（来自共享 UI 上下文；仅界面状态，业务数据仍从 API 取）。
导航为类型化 hash 路由：刷新、前进后退、直达均可恢复；不引入路由框架。
仅上表导航项可见——不为 Tools CRUD / Research Map / 多项目制造空页面。

## 4. 设计控件 → 真实契约映射（协议编辑器）

设计稿 7 区块基于虚构 schema（objectives/evaluation/budget/policy），真实协议
`schemas/protocol.schema.json` 为 `id / version / phases`（`additionalProperties: false`）。
编辑器 Form 区块按真实契约重建，交互结构逐项复用设计稿：

| 设计控件（原区块） | 处置 | 真实契约 / 接口 |
| --- | --- | --- |
| Chrome：Form↔YAML 分段切换、DIRTY 徽章、Templates▾、Diff、Validate | 复用 | 草稿 API（阶段三）；Diff=草稿 vs 最近保存修订；Validate=服务端校验 |
| Dirty digest 横幅（`37b2c9… → dirty`） | 复用，摘要真实 | 最近保存修订的 `source_digest` → `未保存` |
| 错误横幅（可展开跳转区块） | 复用 | 服务端校验错误（path/code/message）+ 客户端 Form 联动 |
| 区块导航（错误计数徽章 + 底部汇总） | 复用，区块重建 | 区块见下 |
| Manifest 区（version/id 锁定、name、autonomy 卡片） | 改造 | **标识区**：`protocol.id`（只读，pattern `^[a-z0-9]+(?:_[a-z0-9]+)*_v[0-9]+_[0-9]+_[0-9]+$`）、`version`（只读 SemVer，展示工程 VERSION 来源）、`phases` 计数 chip。autonomy_level 不属于协议契约 → 不出现 |
| Objectives 区（mini-card 列表） | 结构复用 → **Phases 区** | `phases[]` 卡片：`id`、`name`、`strategy`（6 枚举 select）、`depends_on[]`（chip 多选，DAG 校验由编译器执行）、`inputs[]/outputs[]`（chip）、`timeout_seconds`（数字）、`gate`（POLICY/BUDGET/QUALITY/HUMAN/SECURITY/PUBLISH_GATE 色调 select，映射设计稿 kind→tone）、`stop_conditions`（max_iterations/budget_exhausted） |
| Team 区（template 卡片 + overrides 表） | 拆分 | 团队模板留在 TeamPage（`/team-templates`）；协议内为每 phase `required_roles[]` 表（role select 来自 `/roles` + min/max instances）与 `required_capabilities[]`（chip） |
| Evaluation 区（benchmarks/languages/n_per_lang/temperature） | 不适用 | 协议无此字段；评测/实验参数属于 Experiment 输入，不进入协议编辑器 |
| Budget 区（cap/hard_stop/reservations/donut） | 只读投影 | 右侧报告区展示真实预算投影（dry-run `estimated_cost_minor`，null → UNKNOWN）；不提供协议内预算编辑 |
| Gates 区（kind + trigger 卡片） | 改造 | `gate` 属于 phase（单选枚举 + 色调）；缺失 BUDGET_GATE 等校验由编译器 findings 呈现 |
| Policy 区（admin 门控） | 只读投影 | 无演示管理员开关；policy 语义（heterogeneous review 等）属治理配置，报告区只读展示 |
| 模板下拉（4 preset） | 复用 | 模板来自服务端受控目录（阶段三 `GET /protocol-drafts/templates`；来自 `examples/protocols/` 快照注册，不接受任意路径） |
| YAML 视图 + serialize 字符串拼接 | 复用外观 | 文档语法树 YAML 库（js-yaml，保留注释/格式）；不可解析文本留在 YAML 模式并报错，不静默丢字段 |
| Apply/Discard（双快照 + dirty 比较） | 复用 | Apply = 保存到草稿存储（Idempotency-Key + If-Match → 修订）；Discard = 回退到最近保存修订 |
| 右侧 Preflight 报告（状态条 + 6 zone） | 复用 | 真实 `/compile`、`/preflight`、`/dry-run`（按草稿修订引用）；zone = 状态/发现项/解析计划/预算/审批/风险 |

启动闭环：编辑器启动按钮仅在有已保存修订、无未应用修改、报告匹配该修订时可点；
FAIL 阻断、WARN 显式确认；`POST /projects/{id}/runs` 扩展接受 `{draft_id, revision}`，
服务端加载不可变修订重新 Compile → Preflight → Freeze（草稿后续变化不改写冻结运行）。
旧 `protocol_path` 请求保留兼容。

## 5. 主题 / 密度 / 布局 / 状态

- 主题：dark 默认（`data-theme="light"` 切换），令牌逐值取自设计包 tokens.css。
- 密度：`data-density="normal" | "compact"`（行高/字号变量，见令牌）。
- 语言：中文默认，英文可切换；全部文案走 i18n（无硬编码字符串）。
- 布局：桌面双栏（编辑器/报告、列表/详情）；≤1024px 上下堆叠；≤768px 收拢导航
  为抽屉；390px 不横向溢出。检查宽度：1440 / 1280 / 1024 / 768 / 390。
- 页面状态：每个视图覆盖 empty / loading / error / partial / 403 / stale 六态；
  实时状态仅在确有 SSE 连接的视图（运行时间线）呈现。

## 6. 验收基准（阶段六逐条对照）

1. 上表 11 个路由全部可达、可恢复（刷新后 hash 还原页面；前进后退正确）。
2. 协议闭环：模板 → 编辑 → 校验 → 保存 → 预检 → 启动 → 查看运行全链可操作；
   冲突（412）保留浏览器草稿并可 Diff；迟到响应不覆盖新草稿。
3. 双主题、双密度、中英文切换即时生效并持久化；无视觉破损。
4. 键盘：导航/编辑器/对话框全程可达；焦点圈可见；抽屉关闭恢复焦点。
5. 旧功能零遗漏：§3 表"来源功能"逐项在新页面可用（含向导、探测、取消确认、
   终态限制、事件去重、断线重连、导出、审批后果预览、UNKNOWN 成本语义）。
6. 截图基准：Playwright 对每个路由 × dark/compact/zh 基准截图，变更需显式更新。
7. 回归基线（2026-09-08，工作区干净时）：`lint`、`typecheck` 通过；`test` 27/27
   通过。重建完成后这些门禁不得回归。

## 7. 迁移与回退

- 分阶段替换：旧面板先接入新外壳，再逐页替换；任一阶段应用可运行。
- 草稿表向后兼容（只增表 013）；旧 `path/protocol_path` 接口保留；回退应用后
  草稿数据保留不删除。
- 真实生产数据库迁移另行授权；开发/隔离环境先行验证。
