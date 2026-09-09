---
id: RECHECK-20260908-036
plan_id: PLAN-20260908-034
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-08
completed_at: 2026-09-08
reviewer: root-agent-independent-pass
baseline_ref: 6e452a7
checked_head: working-tree-on-4c3b12a
---

# RECHECK-20260908-036 — Research Console 高保真重建独立复检

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260908-034-console-design-reconstruction.md`
  （cursor plan：`.cursor/plans/控制台高保真重建_9be64bbc.plan.md`）。
- 验收条件：AC-01 至 AC-09；复检从原始目标重查，不继承实现阶段完成声明。
- 变更范围：`apps/web/src/`（styles/tokens/base/fonts + 自托管 public/fonts、
  components 控件与 charts、navigation registry/pageSupport/PageRenderer/urlContext/
  NotFoundPage、layout AppShell/Sidebar/TopBar/CommandPalette、api 分域客户端、
  hooks/useResource、i18n zh+en、features 33 页）；`apps/web/tests/`（unit 基线 +
  e2e shell/design-fidelity/live/strict-stub）；`tests/api/console_api_app.py`；
  `docs/frontend/{CONSOLE_PAGE_MAP,CONSOLE_DELIVERY,CONSOLE_FONTS}.md`、
  `docs/frontend/CONSOLE_REBUILD.md`、`docs/product/CONSOLE_INFORMATION_ARCHITECTURE.md`、
  `docs/INDEX.md`、`docs/references/design/console-design/`；`eslint.config.mjs`、
  `playwright*.config.ts`、`tsconfig.json`、`m0-quality.yml`、`.cursor/plans/`。
- 保留边界：Domain 状态机、ProtocolDefinition Schema、RunManifest 语义、既有 REST
  契约（零修改）、`FRAMEWORK_MANIFEST.json`、根 `VERSION`、生产部署文件、无关用户改动。
- 基线：Git `6e452a7`（重建起点）；复检工作树含并发代理提交 `4c3b12a`
  （English path naming，与本任务无冲突且其命名门禁通过）。未 commit、未 push。
- 门禁环境：Docker Desktop（postgres-test healthy）；DSN 键钉定
  （`RESEARCHOS_POSTGRES_DSN`＝postgres-test 凭据，其余 DSN 键空串），阻断 litellm
  `load_dotenv()` 注入操作员 personal-production DSN（见 [[m0-gating-dsn-pinning]]）。

## 检查结果

| Gate | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | 设计来源冻结 | `docs/references/design/console-design/`：source-digests.txt(52)、ARCHIVE_NOTE、子包 5 文件 cmp IDENTICAL、preview/pin-deps SRI 校验、reference/ 73 图 | PASS |
| AC-02 | 33 路由 + 别名不串页 | `registry.ts` CANONICAL_ROUTES=33；`console-shell` e2e 直达/刷新/别名/未找到页；`navigation-preferences` 往返+别名全规范 | PASS |
| AC-03 | 令牌/控件/双主题双密度中英文 | tokens 对齐设计 220/56/48/16；自托管字体 OFL+摘要；components+charts；`a11y-viewport` 5 档无溢出+焦点环+Esc 恢复；design-fidelity 33 路由截图 | PASS |
| AC-04 | 编辑器闭环 | `rebuild-baseline` T11 空/列表/标量根、注释/单数 task_contract/显式 false 无损；Validate 零写入、412 保留；模板同源预检、草稿禁用（`canStart` sourcePath 门） | PASS |
| AC-05 | 真实动作/无假成功/语义保留 | `useResource` 迟到丢弃；budget/cost UNKNOWN/币种/未计价；compare 不可比并列；GAP 页操作禁用+原因 | PASS |
| AC-06 | 具名 SSE | `useRunEventStream` addEventListener(NAMED_SSE_EVENTS)；`rebuild-baseline` T18 源码断言 | PASS |
| AC-07 | 凭据/纯净 | API Key 仅表单；填充样例仅 stub-api + docs/references（eslint/boundaries ignore docs/references）；无管理员开关/伪通知 | PASS |
| AC-08 | 集成+CI+门禁 | `test:e2e:live` 3 通过（真实 FastAPI+Fake Ports）；m0-quality console-frontend job；`run_all_checks --profile m0` 23/23 PASS | PASS |
| AC-09 | 交付文档+复检 | CONSOLE_PAGE_MAP/DELIVERY/FONTS/REBUILD v2/IA v2/INDEX；validate+validate_bundle+docs_consistency PASS；本复检 | PASS |

## 验证命令与结果

- `pnpm --dir apps/web lint/typecheck/test/build`：lint 0、typecheck 0、57 unit pass、build ok。
- `pnpm --dir apps/web test:e2e`：25 passed（含 design-fidelity 33 路由、strict-stub 基线）。
- `pnpm --dir apps/web test:e2e:live`：3 passed（真实 HTTP + Fake Ports）。
- `pnpm boundaries`：0 violations（PageContext 抽独立模块消除循环依赖）。
- `pytest tests/api tests/contracts/test_openapi_snapshot.py tests/architecture/test_module_file_naming.py`：221 passed（postgres healthy）。
- `validate_bundle.py` / `governance-check/validate.py` / `docs_consistency_check.py`：PASS。
- `run_all_checks.py --profile typescript`：9/9；`--profile m0`：23/23。

## Findings

- F-01（已处置）：`tests/api/test_worker_plane_composition.py` 3 例在无 Postgres 时失败；
  启动 postgres-test 后全过——环境依赖，非本任务回归。DSN 钉定见 [[m0-gating-dsn-pinning]]。
- F-01b（已确认非回归）：`python/tests` 在合并 m0 运行中偶发 1 例失败
  （`test_protocol_draft_store_contract.py` 草稿 id 顺序断言，跨测试 Postgres 状态串扰）；
  单独以门禁命令 `pytest --ignore=tests/architecture/python/test_dependency_boundaries.py`
  全量运行 3060 passed / 6 skipped，且 `--profile m0` 复跑 23/23 PASS。属既有测试
  耦合偶发，非本任务改动引入（本任务未触碰 Postgres 草稿路径；live e2e 用 SQLite in-memory）。
- F-02（已处置）：`eslint .` 覆盖 docs/references 原型与 preview 工具致 no-undef；
  将 `docs/references/**` 加入 eslint/boundaries 忽略（冻结参考材料，不入产品门禁）。
- F-03（已处置）：PageRenderer ↔ feature 页面循环依赖（PageContext 类型）；抽
  `navigation/pageContext.ts` 消除。
- F-04（已处置）：命名门禁拒绝 `playwright.live.config.ts`/`legacy-shapes.ts`；
  重命名 `playwrightLive.config.ts`/`legacyShapes.ts`。
- F-05（已处置）：上一轮 cursor plan 与本轮 plan 的 Desktop 绝对链接/已删文件链接失效；
  改指归档副本或当前实现文件（不改历史结论）。
- 观察：`GET /approvals` 生产恒空（ApprovalStore 无注册点）→ 审批页空态如实呈现，
  登记为 G11，非 UI 缺陷。

## 结论

AC-01 至 AC-09 全部有证据支撑并通过；m0 23 项确定性门禁全绿；后端契约/Schema/
Domain 零修改；缺口 G1–G14 明确登记且对应操作禁用无假成功。判定 **PASS**。
PLAN-20260908-034 可进入 DONE。
