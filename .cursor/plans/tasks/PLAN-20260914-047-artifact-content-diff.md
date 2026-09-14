---
id: PLAN-20260914-047
slug: artifact-content-diff
title: 制品内容 Diff（G8 / EC-04「artifact diff」）+ workspace 页 diff 接实
status: DONE
created_at: 2026-09-14
updated_at: 2026-09-14
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 7（/goal 持续循环迭代指令）；范围=EC-04「artifact 文件 diff」一项；真 pause-resume 执行协调/实验队列/memory capability policy（G16）属后续 cycle"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260914-047-artifact-content-diff.md
memory_entries:
  - MEM-20260914-024-live-console-artifact-fixtures-and-api-prefix
---

# PLAN-20260914-047 — 制品内容 Diff（cycle 7，EC-04 第二批）

## 目标

把 workspace 页上"文件 Diff 未接入（UnavailableState）"的诚实缺口，落地为**真实可用的
制品内容 Diff**：

- 新增 `GET /artifacts/{left_id}/diff/{right_id}`：两侧都是既有 persisted、content-addressed
  制品（`ArtifactStore`），返回**行级 diff**（unified hunks）+ 统计；两侧 digest 相同 =
  明确"无差异"（事实，不是空实现）。
- 前端 workspace 页：在制品列表上选两侧 → 展示 diff；不可比/超限/二进制**如实标注**，
  不渲染假空 diff。

## 诚实边界

- **不做文件系统 diff**：控制面没有 workspace 快照枚举面（`WorkspaceBackend` 只在 CLI
  参考链里装配）；按"制品 = 内容寻址的版本对象"做 diff，并在响应与页面注明该口径。
- **二进制/非 UTF-8 不解码**：`available=false` + reason（不给"看起来一样"的假结论）。
- **超限拒绝**：单侧内容超过 diff 上限（2 MiB，与 `/content` 的 10 MiB 内联上限分开）
  时 `available=false` + reason，不截断成半份 diff 冒充全量。
- **tombstone/缺 blob**：沿用 410 语义（不 200 空字节）。
- diff 结果**不落库**：纯派生只读投影，不入 canonical state。

## 范围

- 包含：
  - WP-A 应用层：`packages/application/artifacts/diff.py`——纯函数
    `diff_artifacts(DiffSide, DiffSide) -> ArtifactDiff`（difflib unified hunks + 计数 +
    truncated 标志），二进制/超限/非 UTF-8 判定。
  - WP-B API：`GET /artifacts/{left_id}/diff/{right_id}`（404 未知 id、503 store 缺失、
    410 tombstone/缺 blob、200 + available=false 不可比），DTO + openapi 再生。
  - WP-C 前端：workspace 页 diff 面板（两侧选择 + hunk 渲染）+ pageSupport/DOC 同步。
  - WP-D 测试与收口：应用层/API 用例、stub e2e、live e2e、m0、RECHECK-047。
- 不包含：pause-resume 执行协调、实验队列、memory capability policy（G16）、
  ReproducibilityAudit 投影（仍诚实标注 unavailable）。

## 架构与数据流

```
GET /artifacts/{left}/diff/{right}
  → deps.artifacts.meta/get（两侧）
  → 404 未知侧 / 410 tombstone·缺 blob；单侧超限 → available=false + TOO_LARGE
  → application.artifacts.diff.diff_artifacts(DiffSide(left), DiffSide(right))
  → {identical, available, reason, lines[], stats{added,removed,context}, truncated}
```

## 验收条件

- [x] AC-01（WP-A）：纯函数 diff 覆盖 文本变更 / 相同 digest / 二进制 / 超限 /
  非 UTF-8 / 大文件截断；无副作用、无持久化。
- [x] AC-02（WP-B）：端点 404（任一侧未知）/503（store 缺失）/410（tombstone）；
  相同内容 → identical=true 且 lines 空；不可比 → 200 + available=false + reason；
  openapi 零漂移。
- [x] AC-03（WP-C）：workspace 页可选两侧并渲染 diff；不可比原因可见；pageSupport G8
  与 CONSOLE_PAGE_MAP G8 同步；web 门全绿。
- [x] AC-04（WP-D）：m0 全绿 + stub/live e2e；push 后 quality-ubuntu 与 console-frontend
  全绿；RECHECK-047 回填。

## 实施清单

- [x] WP-A 应用层 diff
- [x] WP-B API + DTO + openapi
- [x] WP-C 前端 workspace diff + 文档
- [x] WP-D 测试 + 本地门 + 收口

## 证据

- 2026-09-14 WP-A：`packages/application/artifacts/diff.py`（纯函数，无 IO/无持久化；
  `MAX_DIFF_BYTES=2 MiB`、`MAX_DIFF_LINES=2000`、`MAX_LINE_LENGTH=500`；NUL 嗅探 +
  UTF-8 解码失败 → `NOT_TEXT`/`BINARY_CONTENT`）；`tests/application/test_artifact_diff.py`
  10 passed。实现与计划文字的差异：参数从 `diff_texts(left_label, right_label, bytes)`
  改为 `diff_artifacts(DiffSide, DiffSide)`（避免 6 参数触发 ruff PLR0913，语义等价）。
- 2026-09-14 WP-B：`services/api/routers/artifacts.py` 新增
  `GET /artifacts/{left_id}/diff/{right_id}`（`_diff_meta` 404/410、`_blob` 410、
  超限短路 `_unavailable_diff`）；`services/api/dto/artifacts.py` 三个 DTO（含
  `comparison=ARTIFACT_CONTENT` 与口径 note）；`docs/api/openapi.m13.json` 再生
  （+163 行）；`tests/api/test_artifacts_api.py` 11 passed（新增 4 例：行级变更 /
  同 digest identical / 二进制 unavailable+reason / 未知侧 404 与 store 缺失 503）；
  `test_openapi_snapshot` 2 passed。
- 2026-09-14 WP-C：`apps/web/src/features/workspace/ArtifactDiffPanel.tsx`（两侧选择 +
  hunks 渲染 + 不可比原因 + truncated 标记）；`WorkspaceView.tsx` 抽出
  `WorkspaceArtifacts` 让产物列表同时驱动 ArtifactBrowser 与 diff 面板（不重复请求）；
  `api/{types,artifactClient,client}.ts`；`LivePage.module.css` diff 行样式；
  `navigation/pageSupport.ts` GAPS.fileBrowse 与 `docs/frontend/CONSOLE_PAGE_MAP.md` G8、
  `docs/api/CONTROL_PLANE_API.md` 同步。web 门：lint（`--max-warnings 0`）+ typecheck +
  unit 73 passed。
- 2026-09-14 WP-D：stub e2e `apps/web/tests/e2e/workspace-diff.spec.ts` 2/2（行级 diff
  渲染；不可比较时给原因且不渲染空 diff；用例内覆盖路由，不动全局 stub fixture 与
  design-fidelity 基线）；live e2e `apps/web/tests/e2e/live-artifact-diff.spec.ts` 2/2
  （真实 HTTP：1 added / 1 removed / 3 context；同制品自身 identical 且 lines 空；
  未知制品 404 且 title=Artifact Not Found），live 套件 17/17；m0 23/23 PASS（`uv run`
  + Postgres 测试容器 + DSN 固化）；全量 pytest 3297 passed/6 skipped/0 failed（DSN 固化后 postgres 用例实跑）；ruff check/format +
  mypy（4 文件）全绿。
- 2026-09-14 live 正向链的实现说明（与计划文字的差异，如实记录）：计划设想用参考链
  产出的 stdout/result 制品做 live diff，但实测 `tests/api/console_api_app.py` 的
  m12 参考链在 Fake 执行下 run 终态为 FAILED 且 `GET /runs/{id}/artifacts` 返回 0 条
  （无后台 worker，链不真正执行）。改为在该 test-only 装配启动时放入两份受控 JSON
  （`LIVE_DIFF_ARTIFACTS`：`live-fixture:before.json` / `live-fixture:after.json`），
  live 断言仍是真实 HTTP + 真实 diff 计算；不存在"用空列表糊过去"的假绿。

## 已知风险

- 既有 `artifacts.py` 已 176 行，新增端点需控制在该文件与 450 行上限内；
  diff 逻辑放应用层，路由保持薄。（已满足：routers/artifacts.py 收口时约 260 行。）
- ~~stub/live e2e 需要两条真实存在的制品~~（已按上文 live 装配方案落地）。
- 前端 workspace 页已有 ArtifactBrowser（只读列表），diff 面板复用它拿到的列表而不是
  再发一次请求。（已落地：`WorkspaceArtifacts` 单列表驱动两个面板。）

## 状态历史

- 2026-09-14 由 GOAL cycle 7 派生，进入执行。
- 2026-09-14 WP-A/WP-B/WP-C/WP-D 完成，本地门与 e2e 全绿，进入复检。

## 影响报告

- **改动**：应用层新增 `packages/application/artifacts/diff.py`；API 新增只读端点
  `GET /artifacts/{left}/diff/{right}` + 3 个 DTO；前端 workspace 页新增 diff 面板并
  重构产物列表为单一数据源；docs 三处同步；openapi 再生；新增测试（10 应用层 +
  4 API + 2 stub e2e + 2 live e2e）。
- **lint/typecheck/test**：ruff check/format 绿；mypy 4 文件 Success；全量 pytest
  3297 passed/6 skipped/0 failed（DSN 固化后 postgres 用例实跑）；m0 23/23 PASS；web lint/typecheck/unit（73）绿；stub e2e 2/2；
  live e2e 17/17。
- **Domain/API/schema 变化**：无新表、无迁移（diff 是派生只读投影）；Domain 无改动；
  API 面新增一条 GET。
- **安全/凭据变化**：无。live 制品由 test-only 装配写入受控 Fake store，不含真实凭据
  或生产数据；不新增网络出口。
- **兼容性/迁移风险**：无破坏性变更；workspace 页原"文件 Diff 未接入"占位被真实面板
  替换（页面语义增强，非降级）。
- **上游版本影响**：无（仅用标准库 `difflib`）。
- **下一项任务**：cycle 8 = EC-04 剩余（真 pause-resume 执行协调 / 实验队列 /
  memory capability policy G16）。
