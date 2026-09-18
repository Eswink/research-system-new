---
id: RECHECK-20260918-102
plan_id: PLAN-20260918-102
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-18
completed_at: 2026-09-18
reviewer: root-agent-goal-006-cycle3
baseline_ref: 7f116d4
checked_head: 49142e2
---

# RECHECK-20260918-102 — 控制台消费重建读面（GOAL-006 cycle 3 = EC-03）

## 检查范围

PLAN-20260918-102 声称的交付面：`run/timeline` 页面**真的渲染** `RunDetailDto.rebuild`
（三态 + `missing` 字段名）、stub e2e 与 live e2e 各一条链、`CONTROL_PLANE_API.md` 与页面
文案同源、设计基线/结构签名判据实跑。

**不在本轮**：`rebuild` 读面本身的判定（GOAL-005 cycle 6 = EC-06 已交付，本轮只消费）；
DTO / 路由 / OpenAPI 快照（零改动）；`tools/snapshot_migrate.py` 的运营语义（未改）。

## 检查结果

| 复查项 | 检验方式 | 结果 |
| --- | --- | --- |
| AC-01 页面消费（结构判据） | 读 `apps/web/src/features/runs/RunPanel.tsx` 的渲染路径 | PASS（`RunPanel`（201 行）第 37–39 行：`<ResourceBoundary state={flow.run}>` 内、`RunIdentity` 之后渲染 `<RebuildReadiness rebuild={flow.run.data.rebuild} />`；不是"只在 `types.ts` 里存在"） |
| AC-01 三态可区分 + `missing` 点名 | 读 `RebuildReadiness.tsx`（80 行） | PASS（`statusCopy` 三态分支 + `statusTone` 三色调；`missing` 逐条落入 `KeyValueList` 且带 testid `run-rebuild-missing`；字段名映射只影响展示，API 字段名不变） |
| AC-01 文案不越界 | 读文案 + e2e 断言 | PASS（`SELF_CONTAINED` ⇒ "记录自足：重建所需输入都在库内"；`REFUSED` ⇒ "读面拒绝给出结论（这不是「不可回填」的判定）"；面板固定注 `run-rebuild-note` "不预告重建结果"） |
| AC-02 stub e2e 一条链 | `pnpm exec playwright test run-rebuild-readiness` | PASS（**2 passed**：三态可区分 + `missing` 点名 / 文案不越界） |
| AC-02 反证（实跑） | 临时删掉 `RunPanel` 的 `RebuildReadiness` 渲染分支 | PASS（**2 failed**，"element(s) not found"；还原 ⇒ **2 passed**） |
| AC-02 替身路由补全 | 读 `stub-routes-runs.ts`（105 行）+ `stub-routes.ts` 注册 | PASS（新增 `GET /runs/{id}`、`/tasks`、`/events` 三条；`/runs/{id}` 用精确锚定 `^/runs/[^/]+$`，不遮蔽既有子资源路由；未注册的 run ⇒ 404 而不是静默空对象） |
| AC-03 live e2e 一条链 | `playwrightLive.config.ts` 实跑（真实 app，Fake Ports） | PASS（**2 passed**：① 真启动 `m12_reference_research_v1.yaml` ⇒ 读面 `SELF_CONTAINED` 且页面同值；② 夹具历史行 ⇒ `REFUSED` + 四个字段名在页面上逐个出现） |
| AC-03 夹具由域代码生成 | 读 live spec 取值方式 | PASS（两条都用 `page.request.get('/api/runs/{id}')` 先取**读面真值**再与 DOM 比对；页面断言值不是 spec 里写死的常量 ⇒ 页面值 == 读面返回值） |
| AC-03 spec 幂等 | 复查两次运行 | PASS（`Idempotency-Key` 用 `Date.now()`；两次实跑均 2 passed，无状态残留依赖） |
| AC-04 文档同源 | 读 `docs/api/CONTROL_PLANE_API.md` + `docs/frontend/CONSOLE_PAGE_MAP.md` | PASS（rebuild 段写明控制台消费点 `RebuildReadiness.tsx` 与同一口径：自足 ≠ 必过、拒绝 ≠ 不可回填、`missing` 是行字段名；页面地图条目补同一句） |
| AC-05 设计基线 / 结构签名 | `pnpm exec playwright test design-outline-guard` + `design-fidelity` | PASS（**6 passed** + **2 passed**；`#/run/timeline` 基线不选 run ⇒ 该路由像素与 DOM 签名不变，`design-outlines.json` 无需重生成——这是实跑结论，不是"没跑"） |
| AC-05 规模门禁 | eslint `architecture/max-lines-hard` / `max-lines-per-function` | PASS（`typescript/lint` 绿；最长新文件 105 行，全部单函数 < 50 行逻辑行） |
| AC-05 web 六门 | `run_all_checks.py --profile typescript` + playwright 两套 | PASS（typescript **9/9**（含 web lint/test/typecheck/build）；stub e2e **85 passed**；live e2e **38 passed**） |
| AC-05 m0 全量 | `make validate-all`（DSN pin 配方） | PASS（**23 deterministic checks**；含 full pytest、docs-check、framework/learning/hook evals） |
| AC-05 未越界 | `git diff 7f116d4 49142e2 --stat` | PASS（9 文件：2 个新组件/spec、4 个 e2e 支撑、2 处文档；**零** Domain/API/schema/迁移/依赖改动，`schemas/openapi.m13.json` 未动） |

### 交付物在位（结构证据）

- `apps/web/src/features/runs/RebuildReadiness.tsx`（**新增**，80 行）。
- `apps/web/src/features/runs/RunPanel.tsx`（接入渲染分支）。
- `apps/web/tests/e2e/stub-routes-runs.ts`（**新增**，受控三态 fixture + run 详情路由）。
- `apps/web/tests/e2e/run-rebuild-readiness.spec.ts`（**新增**，stub 链）。
- `apps/web/tests/e2e/live-run-rebuild-readiness.spec.ts`（**新增**，live 链）+ `live-specs.ts` 登记。
- `docs/api/CONTROL_PLANE_API.md`、`docs/frontend/CONSOLE_PAGE_MAP.md`（同源口径）。

## 反证与实测

1. **反证（页面渲染分支）**：删 `RunPanel` 里的 `RebuildReadiness` 渲染 ⇒ stub spec
   **2 failed**（`getByText("重建就绪（读面）")` / `getByTestId("run-rebuild")` 找不到元素）；
   还原 ⇒ **2 passed**。说明该 spec 钉的是"页面真的消费读面"，不是"接口里有字段"。
2. **stub 链**：`pnpm exec playwright test run-rebuild-readiness --reporter=line` ⇒ **2 passed**；
   全量 stub 套件 `pnpm exec playwright test` ⇒ **85 passed**。
3. **live 链**：`RESEARCHOS_POSTGRES_DSN="" pnpm exec playwright test --config playwrightLive.config.ts` ⇒
   **38 passed**（含新 2 条）。
4. **live 现场核对（受控探针，非猜测）**：把 live app 起在 8012 上直接读读面 ——
   `m12_reference_research_v1.yaml` ⇒ `manifest_digest`/`manifest_semantic_digest`/
   `protocol_body_digest` 三者齐全 ⇒ `SELF_CONTAINED`；`console_demo_research_v1.yaml` ⇒
   `manifest_digest` 为 `null` ⇒ `REFUSED` + `missing: ["manifest_digest"]`；
   夹具历史行 ⇒ `REFUSED` + 四个字段名。**这决定了 live spec 用哪条协议**（探针进程已收掉）。
5. **web 门**：`run_all_checks.py --profile typescript` ⇒ **PASS: profile=typescript; 9
   deterministic checks**（首跑 1 红：新 live spec 的内联 `import("...").Page` 触发
   `no-restricted-syntax` ⇒ 改为顶层 `import type { Page }`，未改任何断言；另 `stub-routes-runs.ts`
   按 prettier 重排）。
6. **设计门**：`design-outline-guard` **6 passed**、`design-fidelity` **2 passed**
   （33 路由主截图 + 结构签名）——判据绿且基线未变。
7. **m0 全量**：`make validate-all`（`RESEARCHOS_POSTGRES_DSN` 按 test DSN pin、其余三个 DSN
   键置空）⇒ **PASS: profile=m0; 23 deterministic checks**（首跑即绿，无返工）。
8. **治理**：`validate.py` 绿（见 GOAL-006 迭代日志 cycle 3 行）。

## 告警（W）

- **W-1（`SOURCE_DEPENDENT` 没有 live 证据）**：三态在 stub 链上齐全，live 链只拿到两态
  （自足 / 拒绝）。live 夹具里没有"两个 digest 齐、无冻结正文、来源仍可解析"的行（要构造它
  得先有 freeze 过 manifest 又没有正文的行，属人为形态）⇒ 该态的**页面渲染**由 stub 覆盖，
  **分类判定**由既有 API 用例覆盖（`tests/api/test_run_source_and_rebuild_api.py`），
  但"真实 HTTP 上的 SOURCE_DEPENDENT"未实跑。
- **W-2（`missing` 的人话映射只覆盖三条）**：`FIELD_LABELS` 收录 `manifest_semantic_digest` /
  `protocol_body` / `frozen_manifest`，其余（如 `manifest_digest`、`protocol_source`）原样展示
  行字段名。这是**有意的**（不猜语义），但读者看到 `protocol_source` 时仍需回读 API 文档。
- **W-3（`missing` 的 `frozen_manifest` 标签是预留项）**：分类器当前 `_MISSING_ORDER` 里
  **不存在** `frozen_manifest`（只有四个字段名），该映射项今天不会被命中 —— 如实登记，
  不删也不假装它有来源。
- **W-4（本次没重生成任何设计基线）**：结构签名与像素判据都绿且未变，因为
  `#/run/timeline` 的设计基线**不选 run**（新面板只在选中 run 时渲染）。这意味着新面板的
  **视觉**没有基线截图保护：结构变化由 e2e（testid + 文案断言）保护，像素回归不覆盖它。
  要覆盖得新增一条"带 run 的 run/timeline"基线（含 win32/linux 双平台像素），本轮不做。
- **W-5（替身 run 详情路由的射程）**：新路由只服务受控 fixture（三个固定 id），未注册 id 返回
  404。它**不**为既有用例提供通用 run 详情替身；`apiHarness.ts` 仍是无人引用的休眠件
  （本轮未接线，也未删除）。

## 结论

**PASS_WITH_WARNINGS**。EC-03 的结构判据成立：`run/timeline` 的渲染路径里 `rebuild` 有渲染
分支，三态文案可区分且不越界，`missing` 按行字段名点名；stub 与 live 两条链各一条，前者有
反证（去掉渲染分支 ⇒ 红），后者断言"页面值 == 读面返回值"（值来自真实 HTTP，不是 spec 常量）；
`CONTROL_PLANE_API.md` 与页面文案同源；web 六门、设计两门、规模门禁与 m0 全量 23 项全绿。
零 Domain/API/schema 变化。W-1…W-5 是适用边界：`SOURCE_DEPENDENT` 无 live 证据、字段名映射
部分留白、`frozen_manifest` 标签是预留、新面板无像素基线、替身 run 路由只服务受控 fixture。

## 门禁

- web 六门 / 设计两门 / 规模门禁 / m0 全量 23 项：见「反证与实测」第 2、4…7 条。
- CI 六 job：见 GOAL-006 迭代日志 cycle 3 行（本条推送的 run 按闭合约定在回合汇报给出终态）。
