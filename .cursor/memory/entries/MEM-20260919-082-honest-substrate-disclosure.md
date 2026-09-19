---
id: MEM-20260919-082
title: "披露只有落成读面字段 + 页面分支才算数；不选 run 的页面基线看不见「选中 run 才渲染」的分支（结构签名不变）"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-110-honest-substrate-disclosure.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-110-honest-substrate-disclosure.md
supersedes: []
tags:
  - console
  - design-baseline
  - disclosure
  - read-face
  - e2e-fixtures
  - falsification
---

# 诚实披露：执行体读面 + 页面分支（GOAL-20260919-007 / EC-04）

## 做了什么

把「这个 run 是哪个执行体跑的」从"声称存在"变成可判事实：

```text
冻结的 manifest.frozen（canonical outbox 事件：execution_backend / runtime_fingerprint）
  → RunProjection.events(run_id)（既有端口，与 GET /runs/{id}/events 同一实现）
  → services/api/run_execution_view.run_execution_dto → RunDetailDto.execution
  → RunPanel 两行：run-execution-backend / run-runtime-fingerprint
```

- 读面：`services/api/run_execution_view.py`（新）、`services/api/dto/runs.py`、
  `services/api/routers/runs.py`（`_detail_dto(with_execution=…)`，**只详情路径**）。
- 页面：`apps/web/src/features/runs/RunPanel.tsx`（`RunIdentityFacts`）。
- 判据：`apps/web/tests/e2e/run-substrate-disclosure.spec.ts`（stub，四态）、
  `apps/web/tests/e2e/live-run-substrate-disclosure.spec.ts`（live，页面 == 读面）。

## 为什么这样做

1. **「声称已披露」与「已披露」是两件事，而且可以量化区分**：M13 完成记录写着
   Run Control 含"执行体为受控 Fake Runtime"披露，实测该字符串**只**出现在协议注释与
   `demo_session_output()` 的 payload 文案里，`apps/web/src` 零引用 ⇒ 用户看不到。
   **判据**：披露必须落成（a）读面字段 +（b）**页面渲染分支**；只在类型定义里加字段
   不算——反证很容易做（摘掉分支，e2e 必红）。
2. **事实来源只能有一个**：manifest 实体不落库（run 行只有 digest），因此读面**回读冻结
   事件**而不是另存一份基质字段——不新增迁移、不让"读面说的"与"事件里记的"有机会分叉。
   两个 `RunProjection` 实现的 `events()` 都经 publisher 的 `@property published` 查
   `outbox_events` 表 ⇒ 进程重启后仍读得到（读代码确认，不是假设）。
3. **四态必须分开说**，否则"没冻结"会被读成"某个执行体"：具体执行体 / 冻结了但
   **未声明**（`execution_backend = null`）/ **未冻结**（`execution = null`）/ 指纹
   `未声明`。空 dict 是"未声明该面"，**不能**当成一条记录（否则读面要崩或编出空状态）。

## 怎么做与复现

- 复现读面：`GET /api/runs/{id}` → `execution.execution_backend`（未冻结 ⇒ 整个
  `execution` 为 `null`）。
- 复现页面：`#/run/timeline?run=<id>`，看 `run-execution-backend` /
  `run-runtime-fingerprint` 两个 testid。
- 两处反证（记录在 RECHECK-20260919-110）：
  - 摘掉 `RunPanel` 两行 ⇒ **stub 两条 e2e 都红**（钉在页面分支上，不是钉在 DTO 上）；
  - `_frozen_payload` 恒返回 `{}` ⇒ **live 用例在读面就红**（`execution_backend` 是
    `undefined`）⇒ 读面真的从冻结事件取值。

## 适用边界（踩过的坑）

- **设计基线的盲区（本轮最有价值的一条）**：`#/run/timeline` 的既有基线**不选 run**
  （`runs-empty`），而披露行只在选中 run 时渲染 ⇒ 加行后**结构签名逐字节不变**。
  也就是说：门是绿的，但它没在看你。处置 = 新增**同页的选中 run 变体基线条目**
  （第 34 条，`#/run/timeline?run=substrate-openhands`），win32 与 linux 各一张像素；
  跨平台结构签名 34/34 零漂移。规范路由仍是 `registry.ts` 的 33 条。
  **通用规律**：给某个路由的基线固定了查询参数（或依赖页面内部状态）时，同一路由的
  **其他状态**要各自有一条基线，否则改动落在门外面。
- **live 夹具的 UUID 会撞上别人的"不存在的 run"哨兵**：本轮把
  `22222222-2222-4222-8222-222222222222` 当作自己的受控 run，而
  `live-workspace-snapshots.spec.ts` 正是拿它断言 404 ⇒ 该用例变红（404→200）。
  教训：新增 live 夹具 run id 前**全局搜一遍**该 UUID；这条依赖由用例偶然捕获，没有机械门禁。
- **live 的"第二种执行体"是声明的，不是真跑的**：一个 app 实例的选择面只有一个取值，
  所以夹具用生产自己的 `frozen_payload` + `publish_event` 发布一条 `openhands` 声明。
  live 判"页面 == 读面"，真实执行体的离线全链判在 EC-03 的用例里，两者互补。
- **指纹今天只可能是 `NOT_VERIFIED`**：可披露的是**状态 + 原因**，不是指纹值；
  `VERIFIED` 的渲染分支无用例走过（没有真实 probe 事实可造）。
- **列表路径不带该字段**是显式边界（逐 run 回读事件 = N+1），由 `with_execution` 参数
  与文档写明，不是静默省略。
- **尺寸门的两次首跑红**：`console_api_app.py` 的夹具函数 62 行（拆
  `_bind_disclosure_selection` + `_declare_substrate_run`）、`RunIdentity` 57 行
  （拆 `RunIdentityFacts`）。另 `mypy` 首次红在 `deps.projection` 可空未判。

## 来源

- `.cursor/plans/tasks/PLAN-20260919-110-honest-substrate-disclosure.md`
- `.cursor/plans/rechecks/RECHECK-20260919-110-honest-substrate-disclosure.md`
- 代码：`services/api/run_execution_view.py`、`services/api/dto/runs.py`、
  `services/api/routers/runs.py`、`packages/application/run_orchestration/eventing.py`、
  `apps/web/src/features/runs/RunPanel.tsx`
- 判据：`apps/web/tests/e2e/run-substrate-disclosure.spec.ts`、
  `apps/web/tests/e2e/live-run-substrate-disclosure.spec.ts`、
  `tests/api/console_api_app.py`
- 文档：`docs/api/CONTROL_PLANE_API.md`（`execution` 读面）、
  `docs/frontend/CONSOLE_PAGE_MAP.md`、`docs/roadmap/M13_R1_COMPLETION_RECORD.md`（更正）
