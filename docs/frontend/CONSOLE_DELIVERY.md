# Research Console 高保真重建交付（CONSOLE_DELIVERY）

授权计划：[PLAN-20260908-034](../../.cursor/plans/tasks/PLAN-20260908-034-console-design-reconstruction.md)
（cursor plan：控制台高保真重建_9be64bbc）。设计来源：
[console-design 归档](../references/design/console-design/ARCHIVE_NOTE.md)。

## 1. 交付范围与完成度

33 条规范路由全部有独立页面身份与数据来源/缺口说明：

| 域 | 路由 | 等级 | 数据来源 |
| --- | --- | --- | --- |
| Plan | overview / protocol / team | PARTIAL / PARTIAL / FULL | 聚合 / 模板+草稿 / roles+agents+settings |
| Portfolio | projects / experiments / runs-history / compare | PARTIAL / PARTIAL / FULL / PARTIAL | settings / runs experiments / runs / 多 run |
| Run | timeline / approvals / workspace | FULL / PARTIAL / PARTIAL | run+tasks+SSE / approvals / experiments+evidence |
| Library | prompts / datasets / notebooks | GAP ×3 | 无 API（结构+禁用） |
| Library | model-registry / endpoints / setup | FULL ×3 | models / llm-endpoints |
| Library | lineage | PARTIAL | claims+evidence（仅 Run 级） |
| Evidence | claims | FULL | claims+evidence |
| Insights | reports / cost-analytics | GAP / PARTIAL | 无 / cost |
| Ops | alerts/incidents/schedules/integrations/data-health/matrix | GAP ×6 | 无 API |
| Ops | compute / observability | FULL ×2 | cluster+placement / telemetry+cost+trend |
| Govern | budget / audit | PARTIAL ×2 | usage / events+export |
| 全局 | settings / notifications / command-center | PARTIAL / GAP / PARTIAL | prefs+settings / 无 / 复用查询 |

逐操作 API/DTO 映射与缺口 G1–G14：[CONSOLE_PAGE_MAP.md](CONSOLE_PAGE_MAP.md)。
代码化清单：`apps/web/src/navigation/pageSupport.ts`。

## 2. 关键行为保证（验收条件映射）

- AC-02 路由：`registry.ts` 33 条 + `LEGACY_ALIASES`；e2e `console-shell` 验证直达/刷新/
  别名/未找到页不串页。
- AC-04 协议编辑器：`protocolDocument`/`protocolSerialize.applyFormEdit` 文档树定点编辑，
  注释/单数 task_contract/显式 false 无损（`rebuild-baseline` T11）；Validate 零写入；
  412 冲突保留；模板同源预检（`usePreflightAndStart`），自定义草稿预检/启动禁用。
- AC-05 真实性：`useResource` 按对象隔离 + 迟到丢弃；UNKNOWN/未计价/币种冲突/不可比
  语义保留（budget/cost/compare）。
- AC-06 SSE：`useRunEventStream` 按 `NAMED_SSE_EVENTS` addEventListener 消费具名帧。
- AC-07 凭据/纯净：API Key 仅表单短暂存在；设计填充样例只在 `apps/web/tests/e2e/stub-api.ts`
  与 `docs/references/**`（eslint/boundaries/生产构建均排除）。

## 3. 测试与命令

- 单测：`pnpm --dir apps/web test`（56，含 10 个重建基线用例）。
- e2e（确定性替身）：`pnpm --dir apps/web test:e2e`（25：shell/路由/缺口/a11y/截图）。
- e2e（真实 FastAPI + Fake Ports）：`pnpm --dir apps/web test:e2e:live`（3）。
- 后端契约：`uv run --frozen --no-sync python -B -m pytest tests/api tests/contracts/test_openapi_snapshot.py -q`。
- 综合门禁：`uv run --frozen --no-sync python -B .cursor/skills/cursor-framework-check/scripts/run_all_checks.py --profile typescript`（9 项全绿）。
- CI：`.github/workflows/m0-quality.yml` 新增 `console-frontend` job（lint/typecheck/test/build + e2e + live e2e，pinned Playwright）。

## 4. 旧路由兼容

`#/assets/{endpoints,models,compute}`、`#/run/runs`、`#/evidence/inspection`、
`#/govern/{approvals,operations}`、`#/setup` → 规范路由（`LEGACY_ALIASES`）。
vite `/api` 代理与 `Dockerfile.console` 构建入口不变。

## 5. 回退方法

本次仅改前端呈现层 + 文档 + 测试 + CI job；未改 Domain/API/Schema/迁移。回退 =
还原 `apps/web/src`、`apps/web/tests`、`docs/frontend`、`docs/references/design/console-design`、
`eslint.config.mjs`、`playwright*.config.ts`、`m0-quality.yml` 到本次提交前；不删除草稿/数据库数据。

## 6. 视觉对照

设计对照基准：`docs/references/design/console-design/reference/`（73 张，冻结交付包生成）。
实现回归基线：`apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/`（33 路由 dark/normal/zh）。
两者分离；回归基线在设计对照通过后批准。
