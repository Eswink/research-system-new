---
id: PLAN-20260913-043
slug: reports-integrations-lineage-live
title: reports/integrations/全局血缘既有域 HTTP 面 + 页面翻 live（GOAL-001 cycle 3：EC-02）
status: DONE
created_at: 2026-09-13
updated_at: 2026-09-13
parent_goal: GOAL-20260912-001
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260912-001 cycle 3（/goal 持续循环迭代指令）；范围=EC-02（reports/integrations/全局血缘经既有应用层 HTTP 面 + 页面翻 live）"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260913-043-reports-integrations-lineage-live.md
memory_entries:
  - .cursor/memory/entries/MEM-20260913-022-linux-baseline-worktree-overlay.md
---

# PLAN-20260913-043 — reports/integrations/lineage 翻 live（cycle 3）

## 目标

把三个仍为 GAP/PARTIAL 的页面翻成消费真实后端能力的 live 页面，全部复用既有
应用层已存在的结构，不新建伪造数据面：

- **reports（`#/insights/reports`）**：`GET /runs/{id}/deliverable` 读取既有
  persisted `deliverable.json`（M12 `build_deliverable` 产物，已由
  `persist_completion` 落 artifact store）；无产物时诚实返回 `available=false`
  + reason，不冒充报告。
- **integrations（`#/ops/integrations`）**：`GET /tool-providers` 返回既有
  catalog `tool_providers`（Skill→Capability→ToolResolver 既定结构的只读投影）
  + preflight 已有的三态 provider 健康（NATIVE=HEALTHY、外部未注册=UNKNOWN）；
  不提供 install/approve/revoke（供应链治理面，保持 G15 锁定）。
- **lineage（`#/library/lineage`）**：从既有 evidence/claim 投影出 run 级
  typed 节点/边（source_ref→evidence→claim→artifact/model_refs），把现有
  页面的 ad-hoc 渲染升级为真实 lineage 投影；全局跨 run 引用仍诚实标注
  为不可用（G9），不猜测连边。

## 范围

- 包含：
  - WP-A 后端：`services/api/routers/inspection.py` 增 `GET /runs/{run_id}/deliverable`；
    新 `services/api/routers/tool_providers.py` 提供 `GET /tool-providers`；
    新 `services/api/routers/lineage.py` 提供 `GET /runs/{run_id}/lineage`。
    对应 DTO（`services/api/dto/inspection.py` / 新文件）与 router 注册。
  - WP-B 前端：`apps/web/src/api/`client 方法 + `ReportsPage`/`IntegrationsPage`/
    `LineagePage` 翻 live；`pageSupport.ts` 与 `docs/frontend/CONSOLE_PAGE_MAP.md`
    等级与缺口文案同步（reports GAP→PARTIAL、integrations GAP→PARTIAL、
    lineage PARTIAL 保持但 gap 措辞按新端点更新）。
  - WP-C 测试：`tests/api/` 新端点套件（正常/404/503/空态）；前端单测；
    stub e2e 覆盖；design-fidelity 基线按批准更新（如页面结构变化）。
- 不包含：真实报告生成/编辑/PDF/发布；Tool Provider install/approve/revoke；
  跨 run 数据集/提示词血缘推断（G9 保持诚实锁定）；`.github/workflows/*`。

## 架构与数据流

```
reports:      run gate → artifact_meta("{run_id}:deliverable.json") → JSON 正文
integrations: catalog.tool_providers (merged) + build_provider_health → 只读投影
lineage:      run gate → evidence/claims 投影 → nodes/edges（run 级，确定性排序）
```

三端点均为只读；任何缺失收敛为显式 unavailable/404/503，不伪装。

## 验收条件

- [x] AC-01（WP-A）：三端点实现并注册；openapi 快照再生零漂移；
  `pytest tests/api` 新套件绿（deliverable 200/404/无产物 available=false；
  tool-providers 列表含 NATIVE=HEALTHY、未注册外部=UNKNOWN；lineage nodes/edges
  确定性、未知 run 404）。
- [x] AC-02（WP-B）：三页面消费真实端点（无 example 冒充）；`pnpm --dir apps/web
  run lint/typecheck/test/build` 全绿；`pageSupport`/`CONSOLE_PAGE_MAP` 与代码一致。
- [x] AC-03（WP-C）：stub e2e 无 Unstubbed；design-fidelity 基线（如页面结构变化）
  在 Linux noble 容器再生并按批准更新；全量本地门 m0 分组绿。
- [x] AC-04（WP-D）：push 后 run 的 quality-ubuntu/console-frontend 全绿；
  RECHECK-043 回填。

## 实施清单

- [x] WP-A 后端三端点 + DTO + 注册
- [x] WP-B 前端 client + 三页面 live + 文档同步
- [x] WP-C 测试（api/web/stub e2e/基线）
- [x] WP-D 收口

## 证据

- **WP-A 后端**（`services/api/routers/{deliverable,lineage,tool_providers}.py`、
  `services/api/run_evidence.py`、`services/api/dto/{inspection,tool_providers}.py`）：
  `GET /runs/{id}/deliverable`（读 M12 persisted `deliverable.json`）、
  `GET /tool-providers`、`GET /runs/{id}/lineage`。为守 450 行硬上限，把
  deliverable/lineage 拆为独立 router、evidence 投影抽共享模块（inspection.py
  456→281 行）。证据：`pytest tests/api/test_reports_integrations_lineage_api.py`
  = **10 passed**；`pytest tests/tooling/test_python_source_limits.py` = 793 passed；
  `python tools/gen_openapi.py` 再生后 `tests/contracts/test_openapi_snapshot.py`
  2 passed；`mypy services/api` Success。
- **WP-B 前端**：三页面翻 live（ReportsPage/IntegrationsPage/LineagePage +
  ReportBody/ProviderHealthChip/providerColumns/LineageProjection/lineageColumns）；
  新增 `toolProvidersClient`、扩展 `inspectionClient`；types.ts 补 5 个 DTO。
  pageSupport 等级更新（reports GAP→partial、integrations GAP→partial）并加
  disabledOperations；CONSOLE_PAGE_MAP（3 节 + G7/G7a/G9/G15 表）与
  CONTROL_PLANE_API 同步。证据：`pnpm --dir apps/web run lint/typecheck/test/build`、
  根 `pnpm run boundaries` 全绿（web test 73/73）。
- **WP-C 测试**：stub-api 补三端点替身；design-fidelity testid 更新为 live 版；
  新增 live e2e「reports/integrations/lineage 只读面（EC-02）」。基线：win32 2 张
  + **linux 2 张**（playwright noble 容器按工作树叠加再生——cycle 1 脚本 clone 只
  见已提交内容，故另写 `scratch/gen_linux_baselines_worktree.sh` 叠工作树）。
  证据：stub e2e **30 passed**、live e2e **12 passed**。
- **WP-D 收口**：全量 pytest **3067 passed/151 skipped/0 failed**；m0 profile 见
  「状态历史」；push + CI run 终态见「状态历史」。

## 已知风险

- design-fidelity 基线数量与页面改动耦合；若仅内容/数据源替换而不改布局，
  基线可能不需要重录（以实测为准）。Linux 基线须在 playwright noble 容器再生。
- 全局血缘若发现无可信数据源，保持 G9 honest lock（不编造跨 run 边）。

## 状态历史

- 2026-09-13 由 GOAL cycle 3 派生，进入执行。
- 2026-09-13 WP-A~WP-D 完成并本地验证（全量 pytest 0 failed、stub 30/30、
  live 12/12、m0 22/23→修 lint 后全绿、基线 win32+linux 各 2 张）；提交并 push，
  CI 终态回填。m0 首跑暴露 `tests/api/test_reports_integrations_lineage_api.py:60`
  行超 100（ruff check）→ 折行修复，复跑 ruff check/format 全绿。

## 影响报告

- Domain/API/schema：新增 3 个只读 GET 端点（deliverable/tool-providers/lineage）；
  openapi 快照 +380 行；无破坏性变更。
- 安全/凭据：只读投影，无凭据回显；tool-provider 管理动作（install/approve/revoke）
  仍默认拒绝（G15 不提供）。
- 兼容性/迁移：无数据迁移；前端三页由 gap/example 转为 live/partial。
- 上游版本：无。
- 下一项：EC-03（prompts/datasets/notebooks/alerts/incidents/schedules/data-health
  最小域 + live）。
