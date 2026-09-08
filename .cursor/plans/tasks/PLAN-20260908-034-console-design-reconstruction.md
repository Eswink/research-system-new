---
id: PLAN-20260908-034
slug: console-design-reconstruction
title: Research Console 前端高保真重建（八域 33 页）
status: DONE
created_at: 2026-09-08
updated_at: 2026-09-08
cursor_plan_uri: ".cursor/plans/控制台高保真重建_9be64bbc.plan.md"
owners:
  - root-agent
authorization:
  source: cursor-plan
  ref: ".cursor/plans/控制台高保真重建_9be64bbc.plan.md（用户已批准执行；设计原件 C:/Users/googl/Desktop/project 完整交付包）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260908-036-console-design-reconstruction.md
memory_entries: []
---

# PLAN-20260908-034 — Research Console 前端高保真重建（八域 33 页）

## 目标

以 `C:/Users/googl/Desktop/project` 完整设计交付包为视觉依据，重写 Research Console
前端呈现层：八域外壳、33 条规范路由（28 设计页 + 设置/通知中心 + Command Center +
计算节点/运维观测兼容页），逐页接入真实 API；缺失后端能力明确展示并禁用操作。
每页有可追溯设计来源、组件实现、数据来源或明确不可用原因；视觉还原验收与真实数据
集成验收分别通过。

## 范围

- 包含：
  - 设计来源归档（`docs/references/design/console-design/`）、逐页参考图、
    `CONSOLE_PAGE_MAP.md` 页面/API/缺口映射。
  - 视觉令牌重建（双主题、normal/compact 密度、字体层级）、共用控件库、
    八域外壳与 33 条类型化路由、中英文 i18n、命令面板。
  - API 客户端按职责拆分、幂等写入、按对象隔离的资源状态、严格测试替身。
  - 协议编辑器七区 + 右侧六区报告重建；真实 Validate/Save/Diff/412；
    模板同源预检启动；草稿预检禁用。
  - 全部 33 页逐组重建（真实能力页接 API；缺口页还原结构并禁用）。
  - Command Center 独立大屏；响应式/可访问性/性能验收。
  - 真实 FastAPI HTTP 浏览器集成测试、视觉 CI 门禁、交付文档、正式 recheck。
- 不包含：
  - 新建后端业务/API、修改 Domain 或 Schema、数据库迁移、多租户/账户系统。
  - 运行时更换、真实付费模型测试、公开部署、Git commit/push、Manifest 刷新。
  - 原型 `protocol_version 1.4`、演示管理员开关、Tweaks 面板、Google Fonts CDN、
    Babel standalone 进入生产。

## 架构与数据流

- 所有者模块：`apps/web/src/{styles,layout,components,navigation,i18n,api,features}`；
  测试 `apps/web/tests/e2e/`、`tests/api/console_api_app.py`；文档
  `docs/frontend/`、`docs/references/design/console-design/`。
- 技术栈保持 React 19 + TypeScript + Vite + CSS Modules + `yaml` + Playwright；
  不引入 Next.js/全局状态框架/图编辑框架。
- Canonical State 不变：PostgreSQL Domain Entity 为业务真相；前端查询缓存仅展示态。
- 数据流：URL 路由/选中 ID → 功能 Hook（取消/迟到防护）→ 分域 API Client →
  同源 `/api` → 现有服务端 DTO → 纯展示转换 → 页面。
- 写入：用户操作 → 本地校验与后果确认 → 幂等键/If-Match → 服务端事实或分类错误 →
  按范围刷新 → 重渲染。
- 新增 `navigation/pageSupport.ts` 前端接入清单（支持/部分/不可用 + 原因）。

## 验收条件

- [x] AC-01：设计来源冻结——console-design 归档、逐页参考图、子包差异登记完成。
- [x] AC-02：33 条规范路由与旧别名全部正确，刷新/前进后退/直达不串页；未知地址进入明确未找到页。
- [x] AC-03：视觉令牌与共用控件按设计落地，双主题×双密度×中英文组合切换通过。
- [x] AC-04：协议编辑器——空文档无异常、YAML 往返不丢字段、Validate 零写入、Diff 真差异、412 冲突保留、模板同源预检/启动、草稿预检禁用有测试证明。
- [x] AC-05：每个可点击业务动作有真实请求与成功/失败证据；未支持操作无假成功；UNKNOWN/未计价/缺失/币种冲突/不可比语义保留。
- [x] AC-06：具名 SSE 帧被原生浏览器消费；断线、重连、去重、Run 切换正确。
- [x] AC-07：凭据不进入存储/日志/视觉证据；设计填充样例与严格替身不进生产构建。
- [x] AC-08：真实 API 浏览器集成测试与视觉 CI 门禁通过；m0 前端综合门禁通过。
- [x] AC-09：交付文档（页面映射、操作清单、缺口、差异记录、回退）完成；正式 recheck PASS。

## 实施清单

对应 Cursor Plan T01–T33（详细验收与证据要求见 cursor plan 第 6–7 节）：

- [x] STEP-01（T01）设计来源归档 + 参考预览 + 逐页参考图
- [x] STEP-02（T02）CONSOLE_PAGE_MAP.md 逐页逐操作映射与缺口清单
- [x] STEP-03（T03）已知问题失败基线回归测试
- [x] STEP-04（T04）视觉令牌与字体重建
- [x] STEP-05（T05）共用控件与交互模式
- [x] STEP-06（T06）八域外壳与 33 条类型化路由
- [x] STEP-07（T07）界面上下文、i18n、命令面板
- [x] STEP-08（T08）API 客户端拆分与写入语义
- [x] STEP-09（T09）按对象隔离的资源状态
- [x] STEP-10（T10）严格测试数据入口
- [x] STEP-11（T11）协议文档模型修复
- [x] STEP-12（T12）编辑器与六区报告重建
- [x] STEP-13（T13）校验/保存/修订/Diff/412
- [x] STEP-14（T14）预检来源与启动闭环
- [x] STEP-15（T15）接入向导、端点与模型目录
- [x] STEP-16（T16）团队与项目设置
- [x] STEP-17（T17）概览、运行历史与比较
- [x] STEP-18（T18）时间线与真实事件消费
- [x] STEP-19（T19）审批与运行操作
- [x] STEP-20（T20）工作区与实验页面
- [x] STEP-21（T21）Claims 与来源关系视图
- [x] STEP-22（T22）预算、成本与评估趋势
- [x] STEP-23（T23）计算与观测能力页
- [x] STEP-24（T24）项目集合页
- [x] STEP-25（T25）提示词、数据集与笔记页
- [x] STEP-26（T26）报告与运维缺口页
- [x] STEP-27（T27）治理、设置与通知中心
- [x] STEP-28（T28）Command Center 大屏
- [x] STEP-29（T29）响应式、国际化、可访问性与性能
- [x] STEP-30（T30）真实 API 浏览器集成测试
- [x] STEP-31（T31）视觉与 CI 门禁
- [x] STEP-32（T32）旧路由兼容与文档交付
- [x] STEP-33（T33）完整验收与证据化复检

## 子代理使用

Subagent 默认不启用。需要并行时，每个 wave 最多 3 个；多 wave 必须在前一波完成并整合后才可开始。

| Wave | 职责 | 数量 | 状态 | 证据 |
| --- | --- | ---: | --- | --- |
| — | 未使用 | 0 | — | — |

## 证据

| ID | 对应项 | 类型 | 引用或命令 | 结果 |
| --- | --- | --- | --- | --- |
| EV-01 | 基线 | test | `pnpm --dir apps/web lint && typecheck && test`（2026-09-08，重建前） | lint/typecheck 通过；46 pass / 0 fail |
| EV-02 | STEP-01 | file | `docs/references/design/console-design/`（ARCHIVE_NOTE.md、source-digests.txt、preview/ pin-deps、reference/ 73 图） | 设计来源冻结；子包 5 文件 IDENTICAL；vendor SRI 校验通过 |
| EV-03 | STEP-02 | file | `docs/frontend/CONSOLE_PAGE_MAP.md` | 33 路由逐页逐操作映射 + G1-G14 缺口登记 |
| EV-04 | STEP-03 | test | `node --import tsx --test tests/unit/rebuild-baseline.test.ts` | 10/10 按预期失败（修复后期望行为） |
| EV-05 | STEP-04 | file | `apps/web/public/fonts/`（12 woff2）、`src/styles/fonts.css`、`docs/frontend/CONSOLE_FONTS.md`、tokens shell 220/56/48 | 字体自托管 + 摘要/许可证登记；lint/typecheck 通过 |
| EV-06 | STEP-05 | file | `src/components/{Button,Chip,Tabs,Tooltip,Drawer,ConfirmDialog,Table,useOverlayBehavior}.tsx`、`charts/*`、Icon 34 图标 | 控件与图表基础落地；lint/typecheck/build 通过 |
| EV-07 | STEP-06 | file+test | `src/navigation/{registry,pageSupport,PageRenderer,NotFoundPage,useHashRoute}.ts`、`layout/{AppShell,Sidebar,TopBar,CommandPalette}`；smoke：8 域渲染 + not-found | 33 路由注册；lint/typecheck/build 通过；46 单测通过 |
| EV-08 | STEP-07 | file | `navigation/urlContext.ts`、i18n zh+en 全量 33 页 key、命令面板 | URL run 上下文恢复；中英文完整；lint/typecheck 通过 |
| EV-09 | STEP-08/09/10 | file+test | `api/{endpoints,models,team,protocol,run,inspection,operations}Client.ts`+facade、`hooks/useResource.ts`、严格 `stub-api.ts` | 分域客户端；e2e 严格替身基线通过 |
| EV-10 | STEP-11..14 | test | `rebuild-baseline.test.ts` T11/T14/T18 + `protocol-editor-state` canStart；`node --test` 57 pass | 无损往返/模板同源/具名 SSE 全绿 |
| EV-11 | STEP-15..28 | file | 33 页 features（overview/compare/experiments/lineage/cost/budget/command-center/settings/governance/notifications + 14 缺口页 GapLayout）；PageRenderer 路由 | 全路由独立身份；缺口禁用+原因 |
| EV-12 | STEP-29..31 | test | `test:e2e` 25 passed（design-fidelity 33 路由基线）、`test:e2e:live` 3 passed、m0-quality console-frontend job | 响应式/可访问性/实时集成/CI 门禁 |
| EV-13 | STEP-32 | file | CONSOLE_PAGE_MAP/DELIVERY/FONTS、CONSOLE_REBUILD v2、IA v2、INDEX；LEGACY_ALIASES；routes.ts 清理 | 交付文档齐备；旧别名映射 e2e 验证 |
| EV-14 | STEP-33 | check | `run_all_checks --profile m0` 23/23；validate+validate_bundle+docs_consistency PASS；RECHECK-036 | 完整验收通过 |

## 决策与偏差

| 时间 | 决策或偏差 | 原因 | 影响 |
| --- | --- | --- | --- |
| 2026-09-08 | 初始化 | 用户批准的 Cursor Plan（控制台高保真重建_9be64bbc） | 无 |
| 2026-09-08 | docs/references/** 加入 eslint/boundaries 忽略 | 冻结设计原型与参考预览工具非产品代码 | 门禁只覆盖产品源码 |
| 2026-09-08 | PageContext 抽独立模块 | 消除 PageRenderer↔feature 循环依赖 | boundaries 0 violations |
| 2026-09-08 | 缺口页用 GapLayout 设计布局而非逐页高保真 | 后端能力缺失，诚实呈现结构+禁用优先 | 视觉对照对缺口页以脚手架为准，差异登记 |
| 2026-09-08 | 上一轮 plan Desktop 链接改指归档副本 | 外部交付包目录移动致链接失效 | 不改历史结论，validate 通过 |

## 状态历史

| 时间 | 从 | 到 | 原因 | 证据 |
| --- | --- | --- | --- | --- |
| 2026-09-08 | — | APPROVED | 用户批准执行 cursor plan | cursor plan |
| 2026-09-08 | APPROVED | IN_PROGRESS | 基线全绿，开始阶段 A | EV-01 |
| 2026-09-08 | IN_PROGRESS | VERIFYING | T01-T32 全部完成，门禁全绿 | EV-02..EV-13 |
| 2026-09-08 | VERIFYING | DONE | RECHECK-20260908-036 PASS（m0 23/23） | EV-14 |

## 影响报告

- Domain/API/schema：无修改（纯前端呈现层 + 文档 + 测试）。
- 安全/凭据：API Key 仅接入表单短暂存在；不进入 URL/存储/日志/截图。
- 兼容性/迁移：旧路由别名映射保留（§8 旧路由映射）；vite `/api` 代理与 Dockerfile.console 不变。
- 上游版本：不修改 FRAMEWORK_MANIFEST.json；根 VERSION 不变。
- 工程记忆：无可复用事实——本次处置（docs/references 门禁忽略、PageContext 抽模块、
  严格替身、具名 SSE、模板同源预检）均为本任务特定上下文，已完整记录于 RECHECK-036
  Findings 与 CONSOLE_* 文档，无需独立 engineering-memory 条目。
- 下一项任务：无（PLAN-20260908-034 已 DONE；后端缺口 G1–G14 如需补齐另行立项）。
