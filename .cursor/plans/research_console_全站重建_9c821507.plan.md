---
name: Research Console 全站重建
overview: 以已解压设计包中的协议编辑器为高保真样板，将同一设计系统延展至全部现有前端页面，并补齐运行前协议草稿的真实读取、校验、保存和模板能力。保留当前技术栈、产品契约及安全边界，采用分阶段替换、浏览器验收和可回退的兼容迁移。
todos:
  - id: design-baseline
    content: 固定设计来源、字段映射、全站页面清单与现有行为回归基线。
    status: completed
  - id: design-system-shell
    content: 实现设计令牌、共享组件、双主题密度、中英文和可恢复的应用导航。
    status: completed
  - id: protocol-draft-backend
    content: 新增兼容现有契约的协议草稿存储、模板、校验与修订接口，并接入运行前分析链。
    status: completed
  - id: protocol-editor
    content: 实现高保真 Form/YAML 协议编辑器、Diff、冲突恢复和绑定修订的预检启动流程。
    status: completed
  - id: migrate-console-pages
    content: 分组迁移配置、模型、团队、运行、工作区、证据、审批及运维页面。
    status: completed
  - id: verify-and-handoff
    content: 完成浏览器视觉与交互验收、前后端回归、迁移说明及正式复检。
    status: completed
isProject: false
---

# Research Console 全站设计重建计划

## 1. 已确认的目标与范围

用户已确认：
- 以协议页为高保真样板，将设计语言延展到**全部现有前端页面**。
- 本次包含协议编辑所需的**最小后端补齐**，交付真实可用的界面，而非仅有演示数据的原型。
- 本阶段只制定计划；批准后才修改代码、安装依赖或执行测试。

设计依据为[设计交付说明](d:/research-system/docs/references/design/protocol-visual-editor/README.md)和[样式令牌](d:/research-system/docs/references/design/protocol-visual-editor/source/styles/tokens.css)。包内只有 6 个文件，缺少说明中引用的应用外壳、翻译、图标及其他页面；这些部分需要依据现有产品能力延展设计，不能宣称是在逐页复刻完整原稿。

**交付边界：全站界面重建 + 运行前协议编辑；保持现有运行引擎和业务真相来源不变。** 本次不增加多项目管理、账户权限体系、运行中 Manifest 修改、自动发布或新的科研评估领域模型。

## 2. 源码核查与关键取舍

- [现有前端包](d:/research-system/apps/web/package.json)实际使用 React 19.2、TypeScript 6 和 Vite 6.3.5。保留此技术栈，采用 CSS 自定义属性与 CSS Modules，不迁移 Next.js，也不引入整套 Tailwind/shadcn 架构。
- [App.tsx](d:/research-system/apps/web/src/App.tsx)目前用组件状态切换页面，默认页纵向堆叠多个业务面板；[main.tsx](d:/research-system/apps/web/src/main.tsx)未加载设计样式。此次需要建立应用外壳与共享组件，而非只替换几处颜色。
- 复用[HTTP 层](d:/research-system/apps/web/src/api/http.ts)、[API 客户端](d:/research-system/apps/web/src/api/client.ts)、[DTO 类型](d:/research-system/apps/web/src/api/types.ts)和[运行事件订阅](d:/research-system/apps/web/src/features/runs/useRunEventStream.ts)的现有契约与可测逻辑。DTO 指浏览器与服务端交换的数据结构。
- 现有协议接口仅接收预置文件路径，无法直接承接设计稿的 Apply：

```88:91:services/api/dto/team_protocol.py
class ProtocolSourceDto(BaseModel):
    """协议文件路径（examples/protocols/ 内，wizard 选择）。"""

    path: str = Field(min_length=1, max_length=500)
```

- [真实协议 Schema](d:/research-system/schemas/protocol.schema.json)规定的是 `id / version / phases`，并拒绝额外字段。设计稿中的 `manifest / objectives / evaluation / budget / policy` 不能原样成为新产品契约。
- 设计稿的 `protocol_version: 1.4`、美元除以 `100000`、演示管理员开关、固定摘要与模拟预检均不进入生产。工程版本仍只来源于[VERSION](d:/research-system/VERSION)；金额、权限、枚举和校验以服务端为准。
- [ADR-0008](d:/research-system/docs/adr/ADR-0008-own-product-ui.md)的历史 Next.js 表述与当前 Vite 实现存在差异。本次保留当前实现并记录此差异，不顺带改写 Accepted ADR。

## 3. 全站设计方案

### 应用外壳与导航

采用“左侧信息域导航 + 顶部项目/运行上下文 + 二级标签页 + 主工作区”，将现有能力归入：
- **规划 Plan**：协议与预检、团队与模型绑定。
- **运行 Run**：运行列表、任务与时间线、工作区与实验。
- **证据 Evidence**：研究结论与证据关系、可复现信息和导出。
- **资产 Assets**：中转站、模型、已有接口支持的计算节点与运行分配。
- **治理 Govern**：审批、用量与成本、遥测和评估趋势。

首次接入向导保留为独立流程。仅展示真实可用的导航项，不为规划中的 Tools CRUD、Research Map 或多项目功能制造空页面。

使用轻量、类型化的 URL hash 导航，支持刷新、前进后退和直达页面；无需新增路由框架。共享上下文只保存选中的运行 ID 等界面状态，业务内容继续从 API 获取，消除多个面板反复粘贴 Run ID 的操作。

### 视觉与交互规范

- 深色默认、浅色可切换；提供紧凑/标准密度。沿用设计包的背景层级、语义色、4/8 间距体系、圆角及等宽信息样式。
- 中文默认，支持英文；补齐实际页面文案，移除演示用 Tweaks 控件。
- 建立面板、表单字段、标签页、状态徽章、摘要文本、表格、空态、错误态、确认对话框和差异抽屉。
- 状态同时使用文字、图标、形状与颜色；所有交互可键盘访问，错误关联到具体输入，抽屉关闭后恢复焦点。
- 桌面双栏；窄屏改为上下布局并收拢导航。以 1440、1280、1024、768、390 像素宽度检查溢出；表格和 YAML 允许局部滚动，页面本身不横向溢出。
- 保持现有内容安全策略；不加载 Google Fonts CDN 或 Babel standalone。字体使用本地回退；需要精确字体时先核验许可，再以本地资产交付。

## 4. 分阶段实施

### 阶段一：固定设计基准与回归基线

- 批准后使用项目 `all-plan` 流程，在[任务计划目录](d:/research-system/.cursor/plans/tasks/)登记执行计划，并更新[唯一活动索引](d:/research-system/.cursor/plans/ALL_PLAN.md)。
- 将用户设计参考归档到拟新增的[设计参考目录](d:/research-system/docs/references/design/protocol-visual-editor/)，记录来源与内容摘要，明确其是设计参考而非产品契约。
- 形成“设计控件 → 真实字段/接口 → 可编辑或只读”的映射；记录既有工作区改动与测试结果，保护不相关工作。
- 在拟新增的[重建设计说明](d:/research-system/docs/frontend/CONSOLE_REBUILD.md)固定页面清单、主题、布局、状态和验收基准，并同步[文档索引](d:/research-system/docs/INDEX.md)。
- 核验新增 YAML 解析和浏览器测试依赖的确切版本、许可证及兼容性后 pin 到 package 文件与锁文件；不使用浮动 `latest`。外部 Impeccable/shadcn 与仓库锁定修订的一致性目前未验证，按 `capability unavailable` 处理，使用本地规范完成工作。

**完成条件：每个现有页面和设计交互都有明确归属；产品语义冲突已有明确处理方式。**

### 阶段二：设计系统与应用外壳

主要修改[App.tsx](d:/research-system/apps/web/src/App.tsx)、[main.tsx](d:/research-system/apps/web/src/main.tsx)，新增：
- [样式目录](d:/research-system/apps/web/src/styles/)：令牌、基础样式、主题和密度。
- [布局目录](d:/research-system/apps/web/src/layout/)：应用外壳、导航、二级标签页和上下文选择。
- [共享组件目录](d:/research-system/apps/web/src/components/)：单一职责的可访问组件。
- [导航目录](d:/research-system/apps/web/src/navigation/)和[文案目录](d:/research-system/apps/web/src/i18n/)：类型化路由和中英文文案。

旧业务面板先接入新外壳，再逐页替换；避免一次性删除可工作的前端。浏览器只允许持久化主题、密度、语言与编辑模式偏好，不持久化凭据、运行真相或协议正文。

**完成条件：现有功能仍可访问，导航可恢复，主题、密度和基础组件通过交互测试。**

### 阶段三：最小协议草稿后端

新增独立的协议编写应用模块，不把 YAML 解析或存储逻辑堆进现有路由：
- [protocol_authoring](d:/research-system/packages/application/protocol_authoring/)：草稿读取、校验、保存及修订引用解析。
- [protocol_draft_store.py](d:/research-system/packages/application/ports/protocol_draft_store.py)：由应用层拥有的存储接口。
- 复用并拆出[协议加载器](d:/research-system/adapters/contracts/protocol_loaders.py)的内存文档解析能力，仍通过同一 Schema 与编译器验证。
- 新增 PostgreSQL 与 SQLite 草稿存储实现；生产 PostgreSQL 路径使用 PostgreSQL，SQLite 开发路径保持可用。PostgreSQL 拟新增[013_protocol_drafts.sql](d:/research-system/adapters/postgres/migrations/013_protocol_drafts.sql)，实施时复核最新序号连续性，不重命名历史 migration。
- 新增[协议草稿路由](d:/research-system/services/api/routers/protocol_drafts.py)与[DTO](d:/research-system/services/api/dto/protocol_drafts.py)，在[装配入口](d:/research-system/services/api/composition.py)及[PostgreSQL 装配入口](d:/research-system/services/api/pg_composition.py)注入实现。

接口能力：
- 模板目录及模板正文：只从受控协议模板提供，不接受任意文件系统路径。
- 项目草稿的创建、列表、读取、保存及历史修订读取。
- 未保存 YAML 的服务端校验，返回可定位的错误路径与错误码。
- 保存返回草稿 ID、修订号、资源版本和摘要；区分原文摘要与协议语义摘要。草稿修订号不代表新的工程版本，也不是 RunManifest Revision。

一致性与安全：
- 修改携带 `Idempotency-Key` 与 `If-Match`；存储层以事务保证并发版本检查和修订唯一性。重复重试不产生多次修订，陈旧修改返回 412 并保留浏览器草稿供比较。
- 限制 YAML 体积与解析复杂度，拒绝重复键、自定义执行标签及未允许字段；错误脱敏，不执行用户输入，不修改 `examples/`。
- 扩展[协议分析路由](d:/research-system/services/api/routers/team_protocol.py)和[运行入口](d:/research-system/services/api/routers/runs.py)，支持精确的已保存草稿修订引用，保留旧 `path / protocol_path` 请求兼容。
- 启动必须加载该不可变修订并重新 Compile → Preflight → Freeze；草稿后续变化不能改写已冻结运行。校验和 Dry Run 不启动研究执行、不写长期 Memory、不产生真实预算预留。
- 同步[OpenAPI 快照](d:/research-system/docs/api/openapi.m13.json)、前端 DTO、接口说明与契约测试；保持协议 Schema、Domain 状态机和核心安全策略不变。

**完成条件：草稿可在服务重启后恢复；并发、重试、非法输入和旧客户端兼容测试通过；已保存修订能够进入现有运行链。**

### 阶段四：高保真协议编辑器与预检闭环

重点替换 DryRunPanel.tsx / useDryRun.ts（已删除，被 `apps/web/src/features/protocol/editor/` 协议草稿编辑器取代），按编辑器、区块、校验、转换和报告拆分。

- 保留设计的工具条、Form/YAML 切换、左侧分区导航、错误汇总、字段定位、未应用提示、模板选择、Diff 抽屉及固定 Apply/Discard 操作区。
- **高保真复用交互结构，字段适配真实契约**：协议标识/版本、阶段与依赖、角色与能力、输入输出与 TaskContract 引用、阶段门禁、超时及停止条件。团队模型绑定使用现有团队功能；预算和治理策略展示真实只读投影，不新增任意政策编辑器。
- 使用支持文档语法树的 YAML 解析方案维护 Form/YAML 转换；不复制原型字符串拼接序列化。切换不丢输入；无法解析的文本保留在 YAML 模式并显示错误，禁止静默丢字段或破坏注释。
- 本地草稿、最近服务端保存版本、正在保存和冲突状态分离；只有 API 成功返回后显示“已保存”。切换协议、覆盖模板或离开页面时保护未应用修改。
- 修改后将旧预检标为过期；异步结果校验其协议修订和请求上下文，迟到响应不能覆盖新草稿。
- 将“启动”入口统一到有效预检上下文：无未应用修改、无待完成保存/校验、报告匹配当前修订；FAIL 阻断，WARN 需明确确认。服务端仍执行最终预检，前端按钮不代替安全门禁。
- 右侧保留六个信息区：状态、发现项、解析计划、预算、审批与风险。未知金额显示真实未知状态，不能用零补齐。

**完成条件：模板 → 编辑 → 校验 → 保存 → 预检 → 启动 → 查看运行全链可操作；报错、冲突与过期报告均可恢复。**

### 阶段五：迁移其余全部现有页面

按功能组复用同一组件与状态规范：
1. [首次配置](d:/research-system/apps/web/src/features/setup/)、[端点](d:/research-system/apps/web/src/features/endpoints/)、[模型](d:/research-system/apps/web/src/features/models/)和[团队](d:/research-system/apps/web/src/features/team/)：重做向导、列表、绑定和探测反馈；保留手动 Model ID、失败回退、凭据只写和模型指纹披露。
2. [运行](d:/research-system/apps/web/src/features/runs/)与[工作区](d:/research-system/apps/web/src/features/workspace/)：重做运行选择、任务列表、时间线和实验详情；保留取消确认、终态限制、事件去重、断线重连及受控模拟 Runtime 的真实说明。
3. [审批](d:/research-system/apps/web/src/features/approvals/)、[证据检查](d:/research-system/apps/web/src/features/inspection/)与[运维](d:/research-system/apps/web/src/features/operations/)：重做审批后果预览、证据关系、用量/成本、遥测和评估趋势；接入已有计算节点查询，保持只读语义。

每组覆盖空、加载、错误、部分结果、403、过期状态；实时状态仅在确有事件连接的视图使用。没有数据或权限时明确说明，不制造成功数字或可用性声明。

**完成条件：旧页面清单逐项迁移，原有真实功能无遗漏，全站视觉与交互一致。**

### 阶段六：浏览器验收、回归与交付

- 保留现有[前端单元测试](d:/research-system/apps/web/tests/unit/)，新增协议草稿转换、状态机、响应竞态与导航测试。
- 新增固定版本的 Playwright 浏览器测试与截图基准，放入[浏览器测试目录](d:/research-system/apps/web/tests/e2e/)，添加 `test:e2e` 脚本并接入持续集成。交互使用确定性 API 测试替身；另以测试服务和隔离数据库验证真实协议链，均不使用付费 LLM 或真实凭据。
- 验证深浅主题、两档密度、中英文、目标屏宽、键盘与焦点恢复；协议样板逐状态对照设计说明，其余页面对照已固定的组件规范。
- 后端新增存储契约、重启恢复、原子版本冲突、幂等重试、模板白名单、YAML 拒绝路径及冻结运行不变性测试。零研究副作用测试必须断言实际注入链中的调用，不能只检查未使用的假对象。
- 更新接口、部署迁移及回退说明，执行正式 `recheck`，逐条关联验收证据；通过后才将项目计划标记完成。

## 5. 批准后执行的验证入口

当前没有运行以下测试，也不把源码调查当作验证通过。

- 前端：`pnpm --dir apps/web run lint`、`pnpm --dir apps/web run typecheck`、`pnpm --dir apps/web run test`、`pnpm --dir apps/web run build`。
- 架构与根工具链：`pnpm run check`。
- 新浏览器门禁：`pnpm --dir apps/web run test:e2e`。
- API 与契约：`uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts -q`，另运行新增 PostgreSQL/SQLite 存储测试。
- 契约校验：`uv run --frozen --no-sync python -B .cursor/skills/system-spec-check/scripts/validate_bundle.py`。
- 治理校验：`uv run --frozen --no-sync python -B .cursor/skills/governance-check/scripts/validate.py`。
- 最终综合门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile m0 --keep-going`。

所有 Python 命令执行前在 PowerShell 设置 `$env:PYTHONUTF8 = "1"; $env:PYTHONIOENCODING = "utf-8"`。重负载全量门禁串行运行；环境缺失与已有失败分别记录，不扩大当前任务去修改无关代码或放松校验器。

## 6. 兼容性、回退与最终交付

- **Domain/Schema**：保留现有 ProtocolDefinition、RunManifest 和状态机；新增的是草稿管理接口、应用层存储契约与持久化结构。
- **安全/凭据**：不新增管理员演示开关，不放宽 CSP、网络、Memory 写入及运行权限；前端不保存 Key、Prompt 或业务真相。
- **迁移**：新增表采用向后兼容方式；旧协议文件路径继续可用。只在开发/隔离测试数据库执行迁移，真实生产数据库变更另行授权。回退应用后保留新增数据，不自动删除草稿或历史修订。
- **上游**：保留现有 React/Vite/OpenHands 版本；仅增加已核验并锁定的必要前端依赖。不得修改 `FRAMEWORK_MANIFEST.json` 来通过日常开发门禁。
- **交付物**：统一设计系统、完整前端页面、真实协议编辑闭环、截图与浏览器测试证据、接口与迁移文档、正式复检结果。
- 全程不自动 commit、push、发布或覆盖无关用户改动。下一项执行任务是“固定设计基准与回归基线”，不是立即批量替换源码。