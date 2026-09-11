---
id: PLAN-20260910-036
slug: frontend-legacy-rewrite
title: 前端最早一批遗留页面与组件重写（setup 向导、集群 hook、编辑器外壳对齐）
status: DONE
created_at: 2026-09-10
updated_at: 2026-09-10
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "2026-09-10 用户要求重写仍存活的最早一批前端页面与组件并统一样式，范围经确认含编辑器外壳对齐与顶栏徽章间距"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260910-038-frontend-legacy-rewrite.md
memory_entries: []
---

# PLAN-20260910-036 — 前端最早一批遗留页面与组件重写

## 目标

消除高保真重建（PLAN-033/034/035）之后 live 树仍存活的三处早期遗留，使全站统一到
CONSOLE_REBUILD 规格：最早一批（2026-08-26 至 08-31）完全无样式的 setup 向导整树、
同代手写数据 hook useCluster、以及 09-08 v1 轮跳过对齐的协议编辑器外壳；
并关闭 RECHECK-037 的顶栏来源徽章间距观察项。

## 范围

- 包含：apps/web live 树 features/setup 全部组件与 hook、LiveConsole 向导包装区、
  features/operations/useCluster、protocol/editor 外壳视觉层、layout/TopBar 间距、
  i18n 词典新增 setup 键、design-fidelity 快照基线按新设计重录（用户批准）。
- 不包含：后端 Domain/API/schema/migration、示例数据 reference 树、真实 API 契约、
  提交与推送授权范围外的动作。

## 架构与数据流

向导保留 relay → test → models → done 四步真实流程与全部写请求语义；
视觉语言移植 example-console reference SetupScreen 各步设计，仅借版式，
示例模式状态机不移植。数据 hook 迁移到 useResource 获得迟到响应保护与
401/403/501/503 分类。诚实性纪律不变：探测失败不伪装成功、凭据状态只显
configured 或 missing、UNKNOWN 不以零渲染。

## 验收条件

- [x] AC-01：live 向导零裸元素——全部经共享组件与 CSS Module 与 tokens 渲染，中英主题密度四组合无样式错位。
- [x] AC-02：全部既有 data-testid 保留；wizard-flow 单元测试不改通过；design-fidelity 以 relay-wizard 断言页面身份成功。
- [x] AC-03：useCluster 对外接口保持消费面（cluster/error/busy/loadCluster）；未使用的 placement/loadPlacement 死字段移除（ComputePage 已直接用 useResource 查放置）；ComputePage 仅 void 调用一行适配；operations-loader 测试通过。
- [x] AC-04：编辑器外壳对齐参考规格（输入控件补齐 base .input 规格、竖线 16px、segment 半径/间距、活动项 hover 抑制、tooltip i18n 化），protocol-editor-state 测试与草稿链路不变。
- [x] AC-05：顶栏 right gap 10→14px；全部保真快照（含顶栏页面）在 2% 容差内通过。
- [x] AC-06：typecheck、lint（0 warning）、单元 70/70、build、e2e 30/30、e2e:live 3/3、根 eslint/typecheck/depcruise 全绿；仅 library-setup 基线按新设计重录；Domain/API/schema 零改动。

## 实施清单

- [x] STEP-01：setup 向导重写（RelayWizard 外壳 + 信息卡 + 四步组件 + ErrorRow/ProbeFacts + steps/RelayWizard/WizardSteps module.css + setup.* i18n 键 + LiveConsole Button 化）。
- [x] STEP-02：useCluster 迁移到 useResource 并适配消费方。
- [x] STEP-03：协议编辑器外壳对齐参考规格 + editor.*.tip 键。
- [x] STEP-04：TopBar 徽章间距修复。
- [x] STEP-05：门禁全绿、快照重录、四步 + 失败分支视觉走查（scratch/frontend-legacy-rewrite-20260910/step*.png）。

## 已知风险

- library-setup 保真快照基线必然变化（裸 HTML 到新设计），重录需用户批准为新基线。
- 向导重写触碰 M13 时代诚实性分支逻辑，以行为测试为回归网。

## 偏差记录

- i18n 词典超软性 300 行门禁：setup.* 拆出 setupZh.ts/setupEn.ts 合并（键集合不变，Record 类型仍强制中英对齐）。
- wizardApi 的 discovery 诊断串保持英文原样（单元测试契约），UI 以本地化 framing + mono 技术细节呈现。
- DIRTY pill 保留英文 mono 设计令牌（与参考设计一致，同 DUE/PAID 先例）。
- 视觉走查用一次性脚本 scratch/frontend-legacy-rewrite-20260910/wizard-steps.mjs（不入产品树）。

## 证据

（补记：2026-09-11 由 PLAN-20260910-037 收口轮按 governance-check 要求补齐本计划
缺失章节；事实来源为 RECHECK-20260910-038 与提交 9c3e34d，不新增判定。）

- 提交：9c3e34d（feat(web): rewrite legacy setup wizard and align v1 editor chrome）。
- 复检：RECHECK-20260910-038 PASS（独立复检代理逐文件核查 + 根级门禁实跑：
  typecheck/lint/单测 70/70/backend-clean/build/e2e 30/30/live 3/3/根 eslint/
  typecheck/depcruise 0 violations；library-setup 基线一张按批准重录）。
- AC-01~AC-06 证据表见 RECHECK-20260910-038 ## 检查结果。

## 状态历史

- 2026-09-10 计划创建并获批准（用户指定重写范围）；实施与复检同日完成，
  DONE（RECHECK-038 PASS）。
- 2026-09-11 治理补记：按 governance-check 要求补齐 证据/状态历史/影响报告
  章节与无可复用事实声明（追加式，不改动既有判定与记录）。

## 影响报告

- Domain/API/schema/migration：零改动（git status --porcelain 于复检确认）。
- 安全/凭据：零改动；向导不触网、不导出凭据。
- 兼容性：wizard-flow/protocol-editor-state 等既有测试契约保持；testid 全保留。
- 上游版本影响：无新依赖。
- 下一项任务：PLAN-20260910-037 前端预留接口 ↔ 后端对接。
- 工程记忆：无可复用事实新增（重写模式已由 033~035 记录覆盖）。
