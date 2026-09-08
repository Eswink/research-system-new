---
id: PLAN-20260908-033
slug: research-console-rebuild
title: Research Console 全站设计重建
status: DONE
created_at: 2026-09-08
updated_at: 2026-09-08
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: ".cursor/plans/research_console_全站重建_9c821507.plan.md（用户已批准全站重建 + 协议编辑闭环，设计原件 C:/Users/googl/Desktop/design_handoff_protocol_visual_editor）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260908-035-research-console-rebuild.md
memory_entries:
  - .cursor/memory/entries/MEM-20260908-017-litellm-dotenv-gating.md
---

# PLAN-20260908-033 — Research Console 全站设计重建

## 目标

以协议编辑器设计包为高保真样板，将同一设计系统延展到全部现有前端页面
（配置、模型、团队、运行、工作区、证据、审批、运维），并补齐运行前协议草稿的
真实读取、校验、保存、模板与修订能力。保持现有技术栈（React 19 + Vite + CSS
Modules）、产品契约（DTO 单一 schema truth）、Canonical State（PostgreSQL）与
安全边界不变；运行引擎不改。

## 范围

- 包含：
  - 设计令牌、共享组件、双主题（dark 默认/light 可切换）、密度、中英文 i18n。
  - 应用外壳：左侧信息域导航（Plan/Run/Evidence/Assets/Govern）+ 顶部上下文 +
    二级标签页 + 类型化 hash 导航（刷新/前进后退可恢复）。
  - 协议草稿最小后端：`packages/application/protocol_authoring/`、
    `ProtocolDraftStore` Port、PostgreSQL（013）与 SQLite 实现、
    `services/api/routers/protocol_drafts.py`、受控模板目录、服务端 YAML 校验、
    幂等 + If-Match 修订。
  - 高保真协议编辑器：Form/YAML 双模式（文档语法树解析）、区块导航、错误定位、
    模板、Diff、未应用保护、预检修订绑定启动闭环。
  - 全部现有页面迁移到新外壳与组件规范；旧功能零遗漏。
  - Playwright e2e、后端存储/并发/幂等/拒绝路径/冻结不变性测试、文档与正式 recheck。
- 不包含：
  - 不修改 Domain 状态机、ProtocolDefinition Schema、RunManifest 语义、预算策略。
  - 不新增多项目管理、账户权限体系、运行中 Manifest 修改、自动发布。
  - 设计稿的 `protocol_version 1.4`、美元/100000、演示管理员开关、Tweaks 面板、
    Google Fonts CDN、Babel standalone 不进入生产。
  - 不迁移 Next.js / Tailwind / shadcn；不修改 `FRAMEWORK_MANIFEST.json`。
  - 不自动 commit/push；真实生产数据库迁移另行授权。

## 架构与数据流

- 所有者模块：`apps/web/src/{styles,layout,components,navigation,i18n,features/protocol}`
  （前端）；`packages/application/protocol_authoring/` + `packages/application/ports/protocol_draft_store.py`
  （应用层）；`adapters/{postgres,sqlite}/protocol_draft_store.py`（存储）；
  `services/api/{routers/protocol_drafts.py,dto/protocol_drafts.py}`（入口）。
- 上游输入：用户设计包（归档于 `docs/references/design/protocol-visual-editor/`）、
  `schemas/protocol.schema.json`、`adapters/contracts/protocol_loaders.py`、
  现有 `team_protocol.py`/`runs.py` 契约。
- 下游输出：协议草稿修订表（PostgreSQL 013 / SQLite 同构）、草稿 REST API、
  重建后 Console 全站。
- Canonical State：PostgreSQL Domain Entity 仍是业务真相；草稿是运行前工件，
  修订不可变；草稿修订号 ≠ 工程版本 ≠ RunManifest Revision。
- Port/Adapter：ProtocolDraftStore 由应用层拥有；Pg/Sqlite/InMemory 实现注入 composition。
- Policy/Security Gate：模板只读白名单；YAML 体积/复杂度限制；拒绝重复键/自定义
  标签/未允许字段；错误脱敏；冻结运行不可被草稿变化改写；已保存修订启动必须重新
  Compile → Preflight → Freeze；校验/Dry Run 零研究副作用。

## 验收条件

- [x] AC-01：设计基准固定——设计包归档、控件→字段映射、页面清单与回归基线记录于
  `docs/frontend/CONSOLE_REBUILD.md` 并入文档索引。
- [x] AC-02：设计系统与外壳可用——令牌/主题/密度/i18n/共享组件落地；hash 导航刷新
  可恢复；现有功能在旧面板接入新外壳后仍可访问；组件交互测试通过。
- [x] AC-03：协议草稿后端——草稿 CRUD/模板/校验/修订接口通过契约测试；服务重启后
  草稿恢复；并发 If-Match 冲突 412；幂等重试不产生重复修订；旧 path 请求兼容。
- [x] AC-04：协议编辑器闭环——模板 → 编辑 → 校验 → 保存 → 预检 → 启动 → 查看运行
  全链可操作；Form/YAML 切换不丢输入；报错、冲突、过期报告可恢复；FAIL 阻断启动。
- [x] AC-05：全站页面迁移完成——旧页面清单逐项迁移，原有真实功能无遗漏，全站视觉
  与交互一致；空/加载/错误/403/过期状态覆盖。
- [x] AC-06：浏览器验收与回归——Playwright e2e（固定版本、确定性替身）+ 截图基准
  通过；`test:e2e` 接入；验证双主题、双密度、中英文、目标屏宽、键盘与焦点恢复。
- [x] AC-07：后端健壮性——存储契约、重启恢复、原子版本冲突、幂等重试、模板白名单、
  YAML 拒绝路径、冻结运行不变性、零研究副作用（断言真实注入链）测试通过。
- [x] AC-08：正式复检——前端 lint/typecheck/test/build、`pnpm run check`、
  API/契约 pytest、bundle/governance validator、m0 全量门禁通过；recheck 记录
  逐条验收证据，结论 PASS。

## 实施清单

- [x] STEP-01：登记任务计划与 ALL_PLAN；归档设计参考；记录工作区基线（git status、
  前端 lint/typecheck/test 当前结果）。
- [x] STEP-02：编写 `docs/frontend/CONSOLE_REBUILD.md`（页面清单、设计控件→真实字段
  映射、主题/布局/状态/验收基准）并更新 `docs/INDEX.md`。
- [x] STEP-03：设计令牌、基础样式、主题/密度层 + 共享组件 + 应用外壳 + hash 导航 + i18n。
- [x] STEP-04：协议草稿后端（TDD：契约测试先行）。
- [x] STEP-05：协议编辑器（DryRunPanel 替换 + 编辑器状态机 + 预检闭环）。
- [x] STEP-06：分批迁移全部现有页面（setup/endpoints/models/team → runs/workspace →
  approvals/inspection/operations）。
- [x] STEP-07：Playwright e2e + 后端健壮性测试 + 文档同步。
- [x] STEP-08：全量验证（§验证命令）+ 正式 recheck + 状态推进 DONE。

## 子代理使用

Subagent 默认不启用。全站重建存在强顺序依赖（令牌→组件→外壳→页面），根代理顺序
执行；仅当出现可独立并行的页面迁移批次时，按每 wave ≤3 委派。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | 顺序执行 |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | STEP-01 | check | `git status --short`（基线仅含计划/归档/文档新增，无源码改动） | 基线干净：lint 0 错、typecheck 通过、test 27/27 PASS |
| EV-02 | STEP-01 | test | `pnpm --dir apps/web run lint/typecheck/test` 基线（2026-09-08） | lint exit 0；typecheck exit 0；27 pass / 0 fail |
| EV-03 | STEP-02 | file | `docs/frontend/CONSOLE_REBUILD.md` + `docs/references/design/protocol-visual-editor/` + `docs/INDEX.md` 两处新增 | 已创建并挂索引 |
| EV-04 | STEP-03 | test | `pnpm --dir apps/web run lint/typecheck/test/build`（2026-09-08） | lint 0 错；typecheck 通过；tests 35 pass / 0 fail；build 成功 |
| EV-05 | STEP-03 | file | `apps/web/src/{styles,layout,components,navigation,i18n}` + App.tsx 外壳接入 + RunPanel 上下文 props | tokens/base 样式、AppShell/Sidebar/TopBar、Icon/StatusBadge/Field/PanelSection/States/SegmentedToggle/cx、routes/useHashRoute、i18n zh+en、preferences（唯一 localStorage 面） |
| EV-06 | STEP-04 | test | `pytest tests/api/test_protocol_drafts_api.py tests/api/test_draft_run_linkage.py tests/contracts/test_protocol_draft_store_contract.py tests/application/protocol_authoring/`（2026-09-08） | 31 passed（API 10 + 链路 4 + 存储契约 8 + 服务 9） |
| EV-07 | STEP-04 | test | `pytest tests/postgres -q`（013 migration 在临时 PG 应用）；`mypy packages adapters services tests`；`ruff check packages adapters services tests` | 63 passed；720 files 无错误；All checks passed |
| EV-09 | STEP-05 | test | `pnpm --dir apps/web run lint/typecheck/test/build`（编辑器接入后） | lint 0 错；typecheck 通过；tests 46 pass / 0 fail；build 成功（yaml@2.8.1 pin，ISC） |
| EV-11 | STEP-06 | check | `grep -rn "data-testid\|empty-mark\|role=\"alert\"" apps/web/src/features` 各页状态覆盖 | 11 路由全部接入外壳与真实组件；TeamPage/RunPanel 补空态；旧聚合页拆分为独立域页面；DryRunPanel/useDryRun/ReportView/ProjectionTable 已删除（被编辑器取代） |
| EV-12 | STEP-07 | test | `pnpm --dir apps/web run test:e2e`（Playwright 1.56.1 pin + Chromium 141；确定性 API 替身） | e2e 5 passed（外壳/导航刷新恢复/主题持久化/Form↔YAML 保留/保存闭环/Start 门禁） |
| EV-15 | STEP-07/AC-06 | test | `pnpm --dir apps/web run test:e2e`（AC-06 补充轮，2026-09-08） | **67 passed**：44 张截图基准（11 路由 × dark/light × normal/compact × zh/en，`tests/e2e/screenshots.spec.ts-snapshots/`）+ 3 键盘焦点（Tab 遍历导航/焦点环、模板面板 Esc 与关闭按钮焦点恢复）+ 15 屏宽断言（1440/1280/1024/768/390 × 3 路由无横向溢出）；两次连续运行稳定；模板面板新增 Esc 关闭 + autoFocus + 焦点恢复实现 |
| EV-13 | STEP-08 | check | `run_all_checks.py --profile m0 --keep-going`（DSN 键按 PA-1 F-1 先例钉定后） | **23/23 PASS**；Python 3059 passed/6 skipped；web test 46；release-assets-immutable PASS |
| EV-14 | STEP-08 | file | `.cursor/plans/rechecks/RECHECK-20260908-035-research-console-rebuild.md` | 结果 PASS；F-01 门禁环境非封闭（litellm dotenv × 操作员 .env，先例处置）；F-03 import 边界已修复 |
| EV-10 | STEP-05 | file | `apps/web/src/features/protocol/editor/`（protocolDocument/Serialize、editorState/Reducer、useEditorActions/useSaveDraft/usePreflightAndStart、EditorChrome/Banners/Body/StatusBar/Layout、sections/） | 编辑器全组件落地；App plan/protocol 页接入 |
| EV-08 | STEP-04 | file | `packages/application/protocol_authoring/`、`ports/protocol_draft_store.py`、`adapters/{sqlite,postgres}/protocol_draft_store.py`、`013_protocol_drafts.sql`、`services/api/routers/protocol_drafts.py`、`dto/protocol_drafts.py`、composition/pg_composition 注入、`docs/api/openapi.m13.json` 再生成、前端 `api/draftClient.ts` + types.ts | 后端闭环落地；OpenAPI 契约测试 2 passed |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-08 | 初始化 | 用户批准的 Cursor Plan（research_console_全站重建_9c821507） | 无 |
| 2026-09-08 | 外部 Impeccable/shadcn 技能按 `capability unavailable` 处理 | 计划阶段即声明：与仓库锁定修订一致性未验证；使用本地规范 | 设计实现全部本地化 |
| 2026-09-08 | DONE 后同日补齐 AC-06 缺口（44 截图基准 + 15 屏宽 + 3 键盘焦点 e2e，EV-15）；RECHECK-20260908-035 G-07 证据更新并重新签署 | 复检验收器指出 G-07 弱验证：原 e2e 5 项未覆盖 AC-06 声明的截图/密度/语言/屏宽/焦点子项 | 无 Domain/API 变化；模板面板补 Esc/autoFocus/焦点恢复；全部门禁复跑绿 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-08 | — | APPROVED | 用户批准 Cursor Plan 并指令执行 | 本计划 |
| 2026-09-08 | APPROVED | IN_PROGRESS | 开始阶段一（基准固定） | EV-01/EV-02 |
| 2026-09-08 | IN_PROGRESS | VERIFYING | 六阶段实施完成，进入独立复检 | EV-01..EV-12 |
| 2026-09-08 | VERIFYING | DONE | RECHECK-20260908-035 PASS（m0 23/23）；ALL_PLAN 已更新 | RECHECK-20260908-035 |

## 影响报告

- Domain/API/schema：新增 ProtocolDraftStore Port 与草稿 REST API（向后兼容；
  OpenAPI 快照与前端 DTO 同步）；Domain 状态机不变。
- 安全/凭据：模板白名单、YAML 拒绝路径、错误脱敏；无新凭据面；不放宽 CSP。
- 兼容性/迁移：新增 013 migration（向后兼容，只增表）；旧 protocol path 请求保留；
  回退应用保留草稿数据。
- 上游版本：仅新增已核验 pin 的前端依赖（YAML 文档解析、Playwright）；React/Vite 不动。
- 下一项任务：阶段二（设计系统与应用外壳）。
