---
id: PLAN-20260915-055
slug: project-scope-provenance-lineage
title: 项目级来源血缘（G9）：run 级投影合并为项目图，共享节点即跨 run 关系
status: DONE
created_at: 2026-09-15
updated_at: 2026-09-15
parent_goal: GOAL-20260915-002
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260915-002 cycle 2 = EC-01（G9 全局跨 run 血缘）。授权来源同 GOAL-20260915-002：2026-09-15 用户会话指令「继续我们的 goal 文件，我们需要继续循环迭代 10-20 次，让我们的系统更加的完整！」；push-to-main-for-CI 授权沿用 GOAL-001 批准口径。"
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260915-055-project-scope-provenance-lineage.md
memory_entries:
  - MEM-20260915-032-project-lineage-merge-and-honest-unlinked-resources
---

# PLAN-20260915-055 — 项目级来源血缘（GOAL-002 cycle 2 / EC-01）

## 目标

把 `library/lineage` 从「只有 run 级投影 + 全局血缘无 API」推进到**项目作用域血缘图**：
同一套投影规则作用到项目内每个 run，按节点 id 合并 ⇒ **共享节点即跨 run 关系**
（不猜边）；数据集/提示词/笔记本以**未连边清单**呈现，并在响应里如实标注
「资源与 run 的引用关系当前没有记录面」（`reference_recording=NOT_RECORDED` + 原因）。

## 背景

GOAL-20260912-001 收口时该页的诚实标注是：`global_lineage_available=false` +
"全局数据集/提示词血缘无 API（G9）：仅 Run 级引用"。前端页面因此对该能力只能显示空图，
`pageSupport` 的 reason 也只能描述缺口。本计划交付真实后端消费者与真实页面。

**记录面的事实证伪**（决定"未连边清单"而不是"猜测连边"）：协议定义只有
`id/version/phases`；`RunManifest` 只有 `evaluation_dataset_digest`（摘要无法反查
`LibraryResource` id）；evidence 的 `source_ref` 不携带资源 id。⇒ 资源↔run 的边**当前
不可从 persisted truth 推出**，交付为未连边清单 + 响应内原因说明，而不是画一条猜的边。

## 范围

- 后端：`services/api/lineage_projection.py`（run 级投影规则单一来源）、
  `services/api/project_lineage.py`（合并 + 共享标记 + 未连边资源）、
  `services/api/routers/lineage.py`（新增 `GET /projects/{project_id}/lineage`）、
  `services/api/dto/inspection.py`（`ProjectLineageNodeDto/ResourceDto/Dto`）。
- 前端：`apps/web/src/features/lineage/projectLineageColumns.tsx`、`ProjectLineagePanel.tsx`、
  `LineagePage.tsx`（run scope 与 project scope 拆组件）、
  `apps/web/src/api/{types.ts,inspectionClient.ts,client.ts}`、
  `apps/web/src/navigation/pageSupport.ts`（GAPS.globalLineage 收敛）、
  `apps/web/src/features/shared/LivePage.module.css`（`.stack` 整宽堆叠）。
- 测试：`tests/api/test_project_lineage_api.py`（6 用例）、stub e2e
  `apps/web/tests/e2e/project-lineage.spec.ts` + `stub-routes-lineage.ts`、live e2e
  `apps/web/tests/e2e/live-project-lineage.spec.ts`（两个 playwright 配置的
  `testIgnore`/`testMatch` 同步）。
- 文档：`docs/api/openapi.m13.json`（快照重生成）、`docs/frontend/CONSOLE_PAGE_MAP.md`。

## 验收条件

- [x] AC-01：项目级端点交付——合并图（`run/source/evidence/claim/artifact/model` 节点与
      `cited_by/supports/materialized_as/produced_with` 关系）、`shared` 语义
      （`run_ids.length > 1`）、未连边库资源清单、`reference_recording=NOT_RECORDED` + 原因；
      未知项目与 `/projects/{id}/runs` 同口径返回**空图而非 404**；run 级端点不因合并投影
      而跨 run 泄漏节点。`tests/api/test_project_lineage_api.py` 6 passed。
- [x] AC-02：OpenAPI 快照含 `/projects/{project_id}/lineage`（`docs/api/openapi.m13.json`
      重生成后的快照契约测试通过）。
- [x] AC-03：前端 live 化 + 标注收敛——`pageSupport` 的 G9 reason 改为「已接入 + 记录面边界」；
      stub e2e 断言共享节点/未连边资源/诚实说明；live e2e 断言真实装配面同一性质与幽灵项目空图。
- [x] AC-04：设计基线按既有流程重生成并目检（win32 本地 + linux 固定在 pinned playwright
      容器内），且记录**旧基线不会报警**的实测差异。
- [x] AC-05：本地 m0 = `profile=m0; 23 deterministic checks`（含 3411 passed / 6 skipped）。
- [x] AC-06：发现的注入器竞态（`blackhole()` 返回时分区尚未生效）另立 PLAN-20260915-056
      修复并单独记账，不混入本计划的验收面。

## 实施清单

- [x] WP-A 后端投影/合并/路由 + DTO + API 用例 + OpenAPI 快照
- [x] WP-B 前端面板/列/接线/stub 与 live e2e + playwright 双配置同步
- [x] WP-C 设计基线重生成（win32/linux）+ 页面全页目检 + `.stack` 布局修复
- [x] WP-D 门禁对齐（50 行函数上限、ruff 参数上限、stub 完整化）+ PLAN-056 分流
- [x] WP-E m0 全量 + RECHECK-055 + GOAL-002/ALL_PLAN/记忆记账 + CI 复验

## 证据

| WP | 证据 | 结果 |
| --- | --- | --- |
| WP-A | `pytest tests/api/test_project_lineage_api.py -q` → **6 passed**；`mypy` 全量通过（项目级模块无 `Any` 泄漏） | PASS |
| WP-A | 合并语义用例：共享来源/模型 `shared=true` 且 `run_ids` 含两个 run；只被一个 run 引用的节点 `shared=false`；run 节点不共享；`shared == (len(run_ids) > 1)` 全量自洽 | PASS |
| WP-A | run 级隔离未破坏：`test_run_lineage_still_scoped_to_its_own_run` 断言 run 级图不含另一 run 的节点 | PASS |
| WP-B | `pnpm run test:e2e` → **40 passed**（含新 `project-lineage.spec.ts`：摘要 `2 / 3 / 1`、`2（共享）`、未连边库资源、`无记录面`）；`pnpm run test:e2e:live` → **20 passed**（含新 live 用例 + 幽灵项目空图断言） | PASS |
| WP-B | `pnpm exec eslint .`（根）= 0 error（2 条既有软阈值 warning）；`pnpm --filter web run lint/typecheck` 通过；`pnpm --filter web run test` = **76 passed** | PASS |
| WP-C | 全页目检发现真实布局缺陷：`.cards` auto-fit 网格把 4 列节点表压窄，"贡献运行/共享"列被裁掉 ⇒ 新增 `.stack` 整宽堆叠并复检（截图见 RECHECK 复现块） | PASS |
| WP-C | 陈旧基线与新渲染实测差 **15,933 px = 1.73%**（`maxDiffPixelRatio: 0.02` 之下不会报警）⇒ win32 与 linux 基线均强制重生成（linux 用 pinned `mcr.microsoft.com/playwright:v1.56.1-noble`，脚本 `scratch/gen_linux_baseline_route.sh`） | PASS |
| WP-D | 门禁对齐：`project_lineage()` 53 行 → 拆 `_merge_runs/_node_dtos/_resource_dtos`；`LineagePage` 53 行 → 拆 `RunScope/ProjectScope`；`ProjectLineagePanel` 61 行 + max-len → 拆 `mergeSummary/NoteCard`；测试 `_seed_evidence` 7 参数 → `_EvidenceSeed` dataclass；stub 补 `/runs/{id}/claims|evidence`（血缘页 run scope 的真值端点，此前缺失会 500） | PASS |
| WP-E | 本地 m0 23/23（`3411 passed, 6 skipped`）；RECHECK-055 = PASS_WITH_WARNINGS | PASS |

## 已知风险

- **资源↔run 的边当前不可交付**：没有记录面（见「背景」的实证据）。本计划不猜边；
  若将来要让数据集/提示词成为图节点，需要先在协议/manifest/evidence 里登记资源引用
  （产品变更 + 迁移，属独立 PLAN/ADR）。
- 项目级图随 run 数增长：当前按 run 全量投影后合并（无分页）。项目 run 数量在控制台
  规模下（数十）可接受；若将来单项目 run 上千，需要引入分页/增量投影（登记为 W）。
- 合并只按节点 id：同一来源在不同 run 里若用不同写法（`paper://x` vs `x`）不会合并——
  这是数据归一问题，不在这里做模糊匹配（宁可漏合也不猜）。

## 状态历史

- 2026-09-15 创建（IN_PROGRESS）：GOAL-20260915-002 cycle 2，取 EC-01（G9）。
- 2026-09-15 WP-A 完成：投影规则抽到 `lineage_projection.py`，新增 `project_lineage.py`
  与 `GET /projects/{project_id}/lineage`；6 条 API 用例绿；OpenAPI 快照重生成。
- 2026-09-15 WP-B 完成：前端面板 + stub/live e2e + 双 playwright 配置同步；
  stub e2e 40 passed、live e2e 20 passed、根 eslint 0 error、web 单测 76 passed。
- 2026-09-15 WP-C 完成：全页目检发现列被裁 → `.stack` 布局修复；实测旧基线差异 1.73%
  （不报警）后强制重生成 win32 + linux 基线并复检。
- 2026-09-15 WP-D/WP-E 完成：门禁对齐 + 注入器竞态分流 PLAN-056；本地 m0 23/23；
  RECHECK-055 = PASS_WITH_WARNINGS。

## 影响报告

- 改动：新增 `services/api/lineage_projection.py`、`services/api/project_lineage.py`、
  `apps/web/src/features/lineage/{ProjectLineagePanel.tsx,projectLineageColumns.tsx}`、
  `apps/web/tests/e2e/{project-lineage.spec.ts,live-project-lineage.spec.ts,stub-routes-lineage.ts}`、
  `tests/api/test_project_lineage_api.py`；修改 `services/api/routers/lineage.py`、
  `services/api/dto/inspection.py`、前端 lineage/api/navigation/dto 接线、
  `apps/web/playwright*.config.ts`、`docs/api/openapi.m13.json`、
  `docs/frontend/CONSOLE_PAGE_MAP.md`、两条 `library-lineage` 设计基线 PNG。
- lint/typecheck/test：根 eslint 0 error；web lint/typecheck 通过、单测 76 passed；
  stub e2e 40 passed；live e2e 20 passed；Python 侧 m0 全量 23/23（3411 passed / 6 skipped）。
- Domain/API/schema 变化：**新增只读端点** `GET /projects/{project_id}/lineage`
  （`ProjectLineageDto`：nodes/edges/library_resources/reference_recording/degraded）；
  run 级 `LineageDto` 的字段未变（`global_lineage_reason` 文案更新为指向项目级端点）。
  无数据库迁移、无 schema 变更。
- 安全/凭据变化：无（只读投影；无新凭据面、无新外部调用）。
- 兼容性/迁移风险：run 级端点的 `global_lineage_reason` 文案变化属**响应文案**变更；
  前端不再把 `global_lineage_available=false` 当成"没有全局血缘"的唯一事实来源
  （改为渲染项目级面板）。无破坏性变更。
- 上游版本影响：无。
- 下一项任务：GOAL-20260915-002 cycle 3 = EC-02（G12 跨 run 时序成本预测）。
