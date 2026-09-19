---
id: PLAN-20260919-110
slug: honest-substrate-disclosure
title: 诚实披露：执行体性质与运行时指纹进读面 DTO 与页面渲染分支，demo 输出不再与真实结果同形（EC-04）
status: DONE
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 4 = EC-04。授权来源：2026-09-19 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`。本 PLAN 遵守：默认 runtime 保持 Fake、不引入新依赖、不改上游 pin、真实端点调用永不进默认 CI、默认 deny 姿态不得放松、不改 Accepted ADR / Canonical State 边界。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260919-110-honest-substrate-disclosure.md
memory_entries:
  - .cursor/memory/entries/MEM-20260919-082-honest-substrate-disclosure.md
---

# PLAN-20260919-110 — 诚实披露（GOAL-007 cycle 4 = EC-04）

## 目标

让「这个 run 是哪个执行体跑的」在**读面 DTO** 与**页面渲染分支**上都成为可判事实，而不是
只藏在一条无 schema 的事件 payload 里：

```text
冻结的 manifest.frozen（canonical 事件，已有 execution_backend）
  → GET /runs/{id} 的 RunDetailDto.execution_backend / runtime_fingerprint
  → RunPanel 的渲染分支（两种执行体在页面上可区分）
```

同时把**已经过时或从未成立的披露声明**收敛成同一口径（`demo_session_output` /
`CONTROL_PLANE_API.md` / `CONSOLE_PAGE_MAP.md` / `AGENT_RUNTIME.md` / `EVENT_MODEL.md` /
`DOMAIN_MODEL.md`）。

## 本轮勘察事实（只读，2026-09-19；路径可复核）

| 事实 | 现状 |
| --- | --- |
| 执行基质今天唯一的读面 | `manifest.frozen` **事件 payload** 的 `execution_backend`（`packages/application/run_orchestration/eventing.py:73`），经 `GET /runs/{id}/events`；`response_model=None` ⇒ **无 OpenAPI schema**，前端**零引用** |
| run 读面 DTO | `RunDetailDto`（`services/api/dto/runs.py:104-125`）**没有**执行体字段；`_detail_dto`（`services/api/routers/runs.py:40-69`）只填 digest 与 rebuild；**没有任何 manifest 内容路由** |
| 页面 | `RunPanel.tsx:123-168` 的 `RunIdentity` 只渲染 state / SSE chip / Run / Protocol / Manifest 五行；`useRunTimeline` 已同时取 `GET /runs/{id}`、`/tasks`、`/events`（replay + SSE），因此需要的**零新增网络调用** |
| 指纹 | `ModelRuntimeFingerprint` 的 `NOT_VERIFIED` 记录（`services/api/runtime_support.py:69-90`）冻结进 manifest，但**不在任何读面**（连事件 payload 也没有它） |
| demo 文案 | `demo_session_output()`（`services/api/demo.py:17-27`）的披露只在 payload 内部；`M13_R1_COMPLETION_RECORD.md:164` 却声称 Run Control 已含该披露——`apps/web/src` 里**没有**这句话 |
| 已过时的口径 | `AGENT_RUNTIME.md:61-63` 与 `eventing.py:70-72`、`tests/api/test_runtime_selection_surface.py:239-242` 都写着「**零 DTO / 路由 / OpenAPI / 迁移变化**」；`EVENT_MODEL.md:48-51` 说 payload 带「三项」，实际已是五项+；`DOMAIN_MODEL.md:43-60` 仍称 `execution_backend` 「保持 None/不伪填充」（与 `manifest.py:13-21` 现状相反） |
| 设计门 | 结构签名 `apps/web/tests/e2e/design-outlines.json`（`UPDATE_OUTLINES=1 pnpm exec playwright test design-fidelity -g 结构签名`）；像素基线按平台：win32 本机 `--update-snapshots`，linux 走 `bash scratch/gen_linux_baseline_route.sh` 容器配方，跨平台结构一致性用 `bash scratch/verify_linux_outlines.sh` |
| **已知坑** | `#/run/timeline` 的设计基线**不选 run**（`MEM-20260918-075`：基线里是 `runs-empty`）⇒ 只加「选中 run 才显示」的分支**不会**改变现有基线，因此像素/结构门**覆盖不到**新分支——需要显式决定是否新增一条选中 run 的基线变体 |

## 口径

- **披露的定义是「读面字段 + 页面渲染分支」**（GOAL 判定细则）：只在 `types.ts` 里存在字段不算。
- **事实来源只有一个**：DTO 字段取自**冻结的 `manifest.frozen`**（canonical 事件），不新造
  第二个真相源、不新增迁移、不改 `RunManifest` 结构；未冻结的 run ⇒ 字段为 `None`
  （与 `manifest_digest` 的既有 `None` 语义一致，页面显示为「未冻结」，**不得**读成某个执行体）。
- **列表 DTO 不带该字段**：`GET /projects/{id}/runs` 是批量读面，逐 run 读事件会变成 N+1；
  本 EC 只在详情读面上披露，理由写进文档（不做静默省略）。
- **指纹按事实披露**：今天唯一可披露的指纹事实是 `NOT_VERIFIED`（附 substrate 与原因），
  因此 DTO 披露的是**状态与原因**，不是伪造的指纹值——「无法证明底层模型一致时明确标注
  可重复配置而非完全可复现」（AGENTS.md §4）。
- **demo 输出不再与真实结果同形**：读面上两种执行体由 `execution_backend` 区分；`demo_session_output()`
  的文案纳入同一口径源（`demo.py` 为唯一出处，文档与 UI 引用它，不各写一套）。
- **页面改动走既有设计基线流程**：结构签名判红 ⇒ `UPDATE_OUTLINES=1` 重生成 ⇒ 跨平台
  一致性复核；像素基线按平台分别生成。

## 先探明再动手

1. **已探明**：manifest 实体不落库（run 行只有 digest），冻结后的 `execution_backend` 只能
   从事件读面取回；**既有端口就够**，无需新查询路径——`ApiDeps.projection`（`RunProjection`）
   的 `events(run_id)` 返回全部 envelope，筛 `EventType.MANIFEST_FROZEN` 即得 payload。
   据此建 `services/api/run_execution_view.py`（唯一事实来源 = 该 payload）。
2. **已探明**：未冻结 run 的 `events(run_id)` 返回**空列表**（不 404）⇒ 读面拿不到
   `manifest.frozen` ⇒ DTO 给 `None`。页面口径按「未冻结」显示，与 `manifest_digest` 的
   `null → NOT FROZEN` 同形，**不读成某个执行体**。
3. **已探明**：最小可披露形态就是 `selection.fingerprint_record()` 的三件
   （`status` / `substrate` / `reason`，`services/api/runtime_support.py`）；冻结时**空 dict**
   是「未声明该面」（`eventing.frozen_payload` 的既有口径），读面转 `None`——不把 `{}`
   当成一条记录（否则要么崩、要么编出空状态）。
4. **已探明（实测）**：加行后 `run-timeline` 的结构签名**不变**——基线不选 run
   （`runs-empty`），披露行只在选中 run 时渲染 ⇒ 既有像素/结构门**覆盖不到**新分支。
   处置：新增第 34 条基线条目 `run-timeline-substrate`（`#/run/timeline?run=substrate-openhands`），
   win32 与 linux 各一张像素 + 结构签名，跨平台一致性复核（34/34、零漂移）。
5. **已探明**：live 套件的 Fake 链**只有一种**执行体（app 的选择面只有一处取值）⇒ 第二种
   执行体无法靠"真启动"造出来。处置：夹具**声明**一条 run（`LIVE_SUBSTRATE_RUN_ID`），
   冻结事实经**生产自己的** `frozen_payload` + `publish_event` 路径发布（不手写 JSON），
   页面/读面仍走生产代码；live e2e 因此判的是「页面 == 读面」，不是「真跑过 openhands」
   （真实执行体离线全链已由 EC-03 的 `tests/e2e/test_ec03_real_runtime_offline_chain.py` 覆盖）。

## 验收条件

- **AC-01**：`GET /runs/{id}` 返回执行体字段（冻结 run 上等于冻结时的选择；未冻结 ⇒ `None`），
  且该字段**来自 canonical 事件**而非另存一份。
- **AC-02**：页面有**渲染分支**：两种执行体在页面上可区分（不是只在 `types.ts` 里存在）。
- **AC-03**：stub e2e 与 live e2e **各一条**断言两种执行体在页面上可区分。
- **AC-04**：**反证**——去掉渲染分支 ⇒ 对应 e2e 红。
- **AC-05**：web 六门（lint / typecheck / unit / build / stub e2e / live e2e）全绿；OpenAPI
  快照重新生成并提交（`tools/gen_openapi.py`），`types.ts` 同步。
- **AC-06**：设计基线/结构签名按既有流程处置并如实记录覆盖结论（含「基线不选 run ⇒ 门覆盖
  不到新分支」这一事实的处置方式）。
- **AC-07**：文案同源——`demo.py` / `CONTROL_PLANE_API.md` / `CONSOLE_PAGE_MAP.md` /
  `AGENT_RUNTIME.md` / `EVENT_MODEL.md` / `DOMAIN_MODEL.md` 逐处一致；三处「零 DTO/路由/
  OpenAPI」的过时声明与 `M13_R1_COMPLETION_RECORD.md` 的不实披露声明按事实改写。
- **AC-08**：尺寸门 / `ruff` / `mypy` / 受影响套件 / m0 23 项绿。

## 实施清单

- [x] **WP-A** 读面 DTO：`RunDetailDto.execution`（`execution_backend` + 指纹 `status`/`reason`），来源为冻结事件；OpenAPI 快照重生成 + `types.ts` 同步
- [x] **WP-B** 页面渲染分支：`RunIdentityFacts` 增「执行体」「运行时指纹」两行（四态显示口径）+ stub fixtures 四态
- [x] **WP-C** e2e 两条（stub 四态 + live 同值）+ 反证（摘分支 ⇒ stub 红；payload 读空 ⇒ live 红）
- [x] **WP-D** 设计基线/结构签名处置 + 跨平台一致性复核（第 34 条基线条目；34/34 零漂移；覆盖结论如实记录）
- [x] **WP-E** 文案同源收敛（含 M13 记录的不实披露声明更正 + 两处过时口径改写）

## 证据

| 项 | 证据 |
| --- | --- |
| 读面（AC-01） | `services/api/run_execution_view.py`（新，读 `manifest.frozen` payload）+ `services/api/dto/runs.py` 的 `RunExecutionDto` / `RuntimeFingerprintDto` + `services/api/routers/runs.py::_detail_dto(with_execution=…)`；`docs/api/openapi.m13.json` 重生成；`apps/web/src/api/types.ts` 同步 |
| 页面分支（AC-02） | `apps/web/src/features/runs/RunPanel.tsx`：`run-execution-backend` / `run-runtime-fingerprint` 两个 testid + `executionBackendLabel` / `fingerprintLabel`（四态文案） |
| e2e（AC-03） | stub `apps/web/tests/e2e/run-substrate-disclosure.spec.ts`（2 passed，四态互不相同）；live `apps/web/tests/e2e/live-run-substrate-disclosure.spec.ts`（1 passed，页面 == 读面）；live 名单 `apps/web/tests/e2e/live-specs.ts` |
| 反证（AC-04） | F-A 摘渲染两行 ⇒ stub 2 failed（element not found）；F-B `_frozen_payload` 恒空 ⇒ live 1 failed（读面即红）。均记录在 RECHECK-20260919-110 并已复原 |
| web 六门（AC-05） | lint 0 problems / typecheck 绿 / unit 76 passed / build 绿 / stub e2e 87 passed / live e2e 39 passed |
| 设计基线（AC-06） | 第 34 条条目 `run-timeline-substrate` + win32/linux 两张像素 + `design-outlines.json`（34 条）；`design-fidelity` 2 passed；`bash scratch/verify_linux_outlines.sh` ⇒ 34/34 零漂移；覆盖缺口结论写进 RECHECK 与 `docs/frontend/CONSOLE_DELIVERY.md` 更正说明 |
| 文案同源（AC-07） | `docs/roadmap/M13_R1_COMPLETION_RECORD.md`（日期化更正）、`docs/architecture/{AGENT_RUNTIME,EVENT_MODEL,DOMAIN_MODEL}.md`、`docs/api/CONTROL_PLANE_API.md`、`docs/frontend/CONSOLE_PAGE_MAP.md`、`packages/application/run_orchestration/eventing.py` 注释、`tests/api/test_runtime_selection_surface.py` docstring |
| 门禁（AC-08） | 尺寸门 948 passed（首跑红两处，已拆）；ruff check/format 绿；mypy 938 files 绿（首跑红 1 处已修）；受影响套件 2049 passed / 2 skipped；m0 **23/23 PASS** |

## 影响报告

- **Domain/API/schema 变化**：`RunDetailDto` 增 `execution`（可空）；OpenAPI 快照与
  `types.ts` 同步更新。**无** Domain 实体、**无**存储迁移、**无**新路由（复用
  `GET /runs/{id}` 与既有两个详情返回点）。`RunManifest` 结构未变。
- **安全/凭据变化**：无。新读面只读 canonical 事件里的**非敏感**事实
  （执行体标识与指纹状态/原因）；不触端点、不读凭据、不新增出网；真实端点调用仍只在
  `requires_live_llm` 门控下。
- **兼容性/迁移风险**：`execution` 是新增可空字段；未冻结 run 上为 `null`（与
  `manifest_digest` 的既有 `null` 语义一致）。列表路径不带该字段（显式边界，N+1 理由）。
  历史 run 只要 outbox 里有 `manifest.frozen` 就能读回；没有该事件的 run 显示"未冻结"。
- **上游版本影响**：无（未引入依赖、未改 pin）。
- **下一项任务**：EC-05（工具面边界：provider → SDK 工具映射缺口，cycle 3 已实测）→
  EC-06（`tool_pack.*` 两选终态）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 4 建档（EC-04）；两条只读勘察已回填（读面/页面/门禁现状 + 已过时声明清单） |
| 2026-09-19 | IN_PROGRESS | 先探明项 1-5 全部实测回填；WP-A…WP-E 全部落地（含两处反证与两次首跑红） |
| 2026-09-19 | DONE | RECHECK-20260919-110 PASS_WITH_WARNINGS（W-1…W-7）；m0 23/23；WP-A…E 五次提交推送（d291566…cc815fd） |
