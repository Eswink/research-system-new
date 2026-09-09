---
id: RECHECK-20260910-037
plan_id: PLAN-20260909-035
attempt: 1
status: COMPLETED
result: PASS
created_at: 2026-09-10
completed_at: 2026-09-10
reviewer: root-agent-recheck-pass
baseline_ref: 00f195a
checked_head: working-tree-on-00f195a
---

# RECHECK-20260910-037 — Console 原型逐页复刻与隔离示例数据独立复检

本复检独立于 RECHECK-20260908-036（其结论针对 PLAN-20260908-034，不用于推定本轮验收）。
从 PLAN-20260909-035 的原始 AC 重查，逐项以本轮实际命令输出、浏览器运行与视觉对照为证据。

## 冻结范围

- 任务计划：`.cursor/plans/tasks/PLAN-20260909-035-console-reference-reconstruction.md`。
- 验收条件：AC-01 至 AC-08；不继承实现阶段完成声明。
- 变更范围：`apps/web/src/`（example-console 隔离示例树、LiveConsole/ConsoleFrame/
  SourceControl 来源语义、registry/PageRenderer/liveRoutePolicy、features 逐页、
  components 表格拆分、protocol editor hooks 拆分）；`apps/web/tests/`
  （console-invariants、example-project-draft、example-isolation、a11y 矩阵、
  design-fidelity 基线重批准）；`tools/console-reference/`（工程证据工具）；
  `.cursor/plans/`。
- 保留边界：六个受保护文件（`apps/web/vite.config.ts`、`eslint.config.mjs`、
  根 `package.json`、`apps/web/package.json`、`tests/tools/`、`tools/dev-backend/`、
  `tools/dev_backend.mjs`）sha256 与 `scratch/console-reference-recovery/protected-baseline.json`
  逐项一致（unchanged:true）；`git diff --check` 干净；Domain/API/schema/migration
  零改动（`git status --short -- services/ packages/ adapters/ migrations/` 为空）。
- 基线：Git `00f195a`；工作树含并行后端改动（dev-backend 工具等），未 commit、未 push。

## 检查结果

| AC | 检查 | 命令或证据 | 结果 |
| --- | --- | --- | --- |
| AC-01 | 来源核对 | 上传 zip SHA-256 `df70632f…54647a` 与 EV-02 一致；`docs/references/design/console-design/reference/` 31 页参考图与 registry 33 路由映射逐页存在（compute/observability 为兼容扩展页，无原型来源，已在 InfrastructureExample 标注） | PASS |
| AC-02 | 33 路由可达 | `example-isolation` e2e 遍历 CANONICAL_ROUTES 全部 33 条：页面身份 testid 可见、零 /api 请求、零 pageerror；`console-shell` 别名/未知路由/刷新保持；`navigation-preferences` 单测覆盖 LEGACY_ALIASES 与往返 | PASS |
| AC-03 | 原型结构落地 | 三组子代理视觉对照（1440×900 与 2560×1440，dark/normal/zh）：portfolio-projects、plan-protocol、evidence-claims、govern-budget、library-endpoints、ops-observability、settings、command-center 全部 PASS——侧栏/顶栏/主区/面板构成与参考一致，无空白 Gap 页冒充设计页 | PASS |
| AC-04 | 示例标记与交互 | SourceControl 顶栏常驻“示例数据·不写入后端”徽章 + 抽屉解释；example-isolation 实测：项目搜索过滤/详情抽屉/Esc 关闭、协议预检确认门→启动按钮启用且点击仅产生页内“示例门禁演示”回执；全程零业务请求 | PASS |
| AC-05 | 真实链路回归 | `test:e2e:live` 3/3（真实 FastAPI+Fake Ports：模板同源预检、草稿校验零副作用+修订、启动+事件 replay）；`pytest tests/api/test_protocol_drafts_api.py test_draft_run_linkage.py test_approvals_api.py` 24/24；后端目录零 diff；真实失败不伪装（LiveEndpointState 错误态不回落示例） | PASS |
| AC-06 | 质量门禁 | `pnpm run check` exit 0（format/lint/typecheck/boundaries/18 工具测试）；web typecheck 0、lint 0/0、unit 70/70、build 0；默认 e2e 30/30；a11y 新增 1280×800 浅主题/英文/密度矩阵与 reduced-motion 字体加载通过 | PASS |
| AC-07 | 视觉对照与残差 | 同视口对照见 AC-03；残差如实记录：顶栏来源徽章较原型 LIVE 旗为有意替换（设计决策，非缺陷）；导航子项文案与面包屑措辞差异（协议与预检 vs 协议&空跑等）为产品术语统一；ops/compute、ops/observability 无原型来源，按兼容扩展页呈现并标注 | PASS |
| AC-08 | 新复检+交付+checkpoint | 本文件；交付记录 `docs/frontend/CONSOLE_REFERENCE_RECONSTRUCTION_DELIVERY.md`；计划状态历史与 ALL_PLAN 投影同步 | PASS |

## 验证命令与结果

- `pnpm run check`：exit 0（含 root eslint .、prettier、双 tsc、depcruise 0 违规、18/18）。
- `pnpm --dir apps/web typecheck/lint/test/build`：0 / 0 / 70 pass / 0。
- `pnpm --dir apps/web exec playwright test`：30 passed（console-shell 6、a11y 20、
  design-fidelity 33 路由基线重批准、example-isolation 3、rebuild-baseline 1）。
- `pnpm --dir apps/web test:e2e:live`：3 passed（真实 HTTP + Fake Ports，无付费模型）。
- `uv run --frozen --no-sync pytest tests/api/{test_protocol_drafts_api,test_draft_run_linkage,test_approvals_api}.py`：24 passed；`tests/contracts/test_openapi_snapshot.py`：2 passed。
- 受保护文件 sha256 对比 protected-baseline.json：6/6 unchanged。
- 视觉对照：`tools/console-reference/captureVisualCompare.mjs` 采集 8 页 → 子代理逐对判定 PASS。

## Findings

- F-01（已处置）：`production-boundaries.test.mjs` 对增长后的 web 树输出 >1MB，
  spawnSync 默认 maxBuffer 触发 ENOBUFS 假失败；提高该测试子进程 maxBuffer 至 64MB，
  断言不变（violations==[] 实测 0 违规）。
- F-02（已处置）：新会话引入的 `@/` 别名 import 使 depcruise `not-to-unresolvable`
  报 11 项；全部改为相对路径，未动受保护 tsconfig/vite 配置。
- F-03（已处置）：架构门禁拒绝 features 树内 `PASS/FAIL/BLOCK/REVISE` 与币种字面量；
  示例预检改为从 fixture 严重度推导（preflightModel），实时页状态词仅回显后端值、
  色调由 findings 严重度派生；未放宽门禁正则。
- F-04（已处置）：`tools/console-reference/*.mjs` 与 scratch 基线副本的浏览器全局
  （document/localStorage/getComputedStyle/innerWidth）触发 root eslint no-undef；
  以 `/* global */` 声明修正，未禁用规则、未改受保护 eslint 配置。
- F-05（已处置）：design-fidelity 33 路由基线为 034 轮旧渲染；本轮按 WP4.5 在
  子代理视觉对照 PASS 后 `--update-snapshots` 重批准并复跑通过（19.6s 稳定）。
- 观察：ops/compute、ops/observability 无原型参考图（兼容扩展），示例态以固定
  fixture 呈现并声明“并非真实集群/遥测”；live 态走真实 cluster/telemetry API。
- 观察：顶栏来源徽章在 1440 宽度下与语言切换钮间距偏紧（子代理记录为
  chrome-level cosmetic，结构无损），后续视觉迭代可微调。

## 结论

AC-01 至 AC-08 全部有本轮实际运行证据并通过；后端 Domain/API/schema/migration
零修改；示例数据全程隔离（33 路由零业务请求实测）；受保护路径逐项哈希一致。
判定 **PASS**。PLAN-20260909-035 可进入 DONE。
