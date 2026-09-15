---
id: MEM-20260915-032
title: 项目级血缘用"共享节点"表达跨 run 关系；没有记录面的资源只作未连边清单
status: ACTIVE
created_at: 2026-09-15
updated_at: 2026-09-15
scope: repository
confidence: 0.90
review_after: 2027-09-15
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-055-project-scope-provenance-lineage.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-055-project-scope-provenance-lineage.md
supersedes: []
tags:
  - lineage
  - provenance
  - console
  - honesty-boundary
---

# 项目级血缘的合并口径与记录面边界

## 做了什么

新增 `GET /projects/{project_id}/lineage`（`services/api/project_lineage.py` +
`services/api/lineage_projection.py`）：把 run 级投影规则（`run_lineage_nodes_edges`）
作用到项目内每个 run，**按节点 id 合并**成一张图；`shared = len(run_ids) > 1` 即"跨 run 关系"。
库资源（dataset/prompt/notebook）以**未连边清单**呈现，响应带
`reference_recording="NOT_RECORDED"` + 原因文案。前端 `library/lineage` 用
`ProjectLineagePanel` 渲染这三件事。

## 为什么这样做

- 跨 run 关系有两种做法：**猜边**（按名称/摘要模糊匹配）或**只报共享**。项目里选了后者：
  节点 id 相同就是被多个 run 引用过，这是 persisted truth 直接可证的；猜边会产生假证据。
- 资源↔run 的边**当前不可证**：协议定义只有 `id/version/phases`；`RunManifest` 只有
  `evaluation_dataset_digest`（摘要无法反查 `LibraryResource.id`）；evidence 的 `source_ref`
  不携带资源 id。既然推不出，就在响应里如实说"无记录面"，而不是画一条看起来合理的边。
- 共享节点把"跨 run"这件事变成**结构事实**（哪个 source/artifact/model 被哪些 run 用过），
  这正是 G9 缺口里可交付的那一半。

## 怎么做与复现

```
python -m pytest tests/api/test_project_lineage_api.py -q      # 6 passed
cd apps/web && pnpm run test:e2e && pnpm run test:e2e:live     # 40 / 20 passed
```

判据要点：`shared == (len(run_ids) > 1)` 全量自洽；未知项目 **200 + 空图**（与
`/projects/{id}/runs` 同口径，不 404）；run 级端点不因合并投影跨 run 泄漏节点；
同一请求两次结果逐字节一致（节点按 `(kind,id)`、边按 `(source,target,relation)` 排序）。

## 适用边界

- 合并按**节点 id 精确匹配**：同一来源的不同写法（`paper://x` vs `x`）不会合并——不猜。
- 无分页：项目内 run 数量大时需要分页/增量投影（当前控制台规模无此问题）。
- 想让数据集/提示词进入图，必须先在协议/manifest/evidence 里登记资源引用（产品变更 + 迁移）；
  在登记面出现之前，"资源↔run 边"不可交付。
- 页面仍标 `partial`：能力已接入，但资源引用记录面缺失这一子项仍在（标注里写明，不缩小范围）。

## 来源

- PLAN-20260915-055 / RECHECK-20260915-055（GOAL-20260915-002 cycle 2 / EC-01）。
- 相关：[[MEM-20260913-020]]（GOAL cycle 门禁机制）、[[MEM-20260915-030]]（收口复验配方）。
