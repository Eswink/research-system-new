---
id: RECHECK-20260915-055
plan_id: PLAN-20260915-055
attempt: 1
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-09-15
completed_at: 2026-09-15
reviewer: root-agent-goal-002-cycle2
baseline_ref: e6f09cb
checked_head: e6f09cb+worktree
---

# RECHECK-20260915-055 — 项目级来源血缘（GOAL-002 cycle 2 / EC-01）

## 检查范围

PLAN-20260915-055 声称的交付面：后端项目级血缘投影与端点、前端项目面板与页面接线、
标注收敛、stub/live e2e、设计基线重生成，以及门禁对齐与注入器竞态分流。
**未在本轮复核**：GOAL 其它 EC（G12/G8/G7/G15/G2）与 PLAN-20260915-056 的注入器修复
（后者有自己的 RECHECK-056）。

## 检查结果

| 声称 | 检验方式 | 结果 |
| --- | --- | --- |
| 项目级端点交付，且 run 级规则被复用而非复制 | 读 `services/api/routers/lineage.py` + `project_lineage.py`：两者都调用 `lineage_projection.run_lineage_nodes_edges`（单一来源） | PASS |
| 合并语义：共享节点即跨 run 关系 | `tests/api/test_project_lineage_api.py::test_project_lineage_merges_runs_and_marks_shared_nodes`（共享来源/模型 `shared=true`；单 run 节点 `shared=false`；run 节点不共享） | PASS |
| 库资源以未连边清单交付，且不猜边 | 同文件 `..._reports_library_resources_without_edges`：资源出现在 `library_resources`，且断言边集合中不含 dataset/prompt 端点 | PASS |
| 记录面缺失如实随响应返回 | `reference_recording == "NOT_RECORDED"` 且 `reference_recording_reason` 含「无记录面」（用例 + live 用例各断言一次） | PASS |
| 未知项目不伪装成"有数据" | `..._unknown_project_is_empty_not_404`：200 + 空图（与 `/projects/{id}/runs` 同口径）；live 用例对 `ghost-project` 复验同一口径 | PASS |
| run 级不因合并投影而跨 run 泄漏 | `test_run_lineage_still_scoped_to_its_own_run`：run A 的图不含 run B 的任何节点 | PASS |
| 确定性（同一请求两次结果一致） | `test_project_lineage_is_deterministic`（节点按 `(kind, id)`、边按 `(source,target,relation)` 排序） | PASS |
| OpenAPI 快照含新路径 | `docs/api/openapi.m13.json` 已重生成；快照契约测试在 m0 全量内通过 | PASS |
| 页面真的渲染这些事实（不是只有后端） | stub e2e：摘要 `项目级合并图（运行 / 节点 / 边）：2 / 3 / 1`、节点表 `2（共享）`、`未连边库资源` 表含 `benchmark-v1/critic-v2`、文案含「无记录面」；live e2e：真实装配面同性质 + 幽灵项目空图 | PASS |
| 标注收敛（G9 reason） | `pageSupport.ts` 的 `GAPS.globalLineage` 从「无 API（G9）」改为「已接入（GET /projects/{id}/lineage…）；资源引用无记录面 ⇒ 未连边清单」 | PASS |
| 设计基线覆盖新页面且**不是靠旧基线蒙混** | 实测陈旧基线 vs 新渲染差 **15,933 px = 1.73%**（阈值 2% ⇒ 旧基线不会报警）⇒ 删除后重生成 win32（本地）与 linux（pinned noble 容器）；两张基线目检均含新面板且 4 列不再被裁 | PASS |
| 前端门禁 | `pnpm exec eslint .`（根）= 0 error；`--filter web lint/typecheck` 通过；单测 76 passed；stub e2e **40 passed**；live e2e **20 passed** | PASS |
| Python 门禁 | 本地 m0 = `profile=m0; 23 deterministic checks`（`3411 passed, 6 skipped`） | PASS |

## 结论

result: **PASS_WITH_WARNINGS**

交付面成立且可复现：项目级血缘由**同一套**投影规则合并而成，跨 run 关系只由共享节点
表达（不猜边），库资源的记录面缺失随响应如实返回，页面把这三件事都渲染出来；标注同步收敛。
复核中额外发现并处理了两类问题：① 页面布局缺陷（4 列节点表被 auto-fit 网格裁列）与
② 陈旧设计基线**不会**报警（1.73% < 2% 阈值）——两者都按"先修复再目检"的顺序闭环。

## 告警

- W-1（**范围注记**，EC-01 的显式边界）：EC-01 的措辞含「dataset/prompt 节点与边」，
  但资源↔run 的引用**没有任何记录面**（协议定义只有 `id/version/phases`；`RunManifest`
  只有 `evaluation_dataset_digest` 摘要，无法反查 `LibraryResource` id；evidence 的
  `source_ref` 不携带资源 id）。本轮交付的是**未连边清单 + 响应内原因**。要让数据集/提示词
  成为图节点必须先登记引用（协议/manifest/evidence 的产品变更 + 迁移），属独立 PLAN/ADR；
  在此之前"边"不可交付——画出来就是捏造。
- W-2（规模）：项目级图按 run 全量投影后合并，无分页；单项目 run 数量上千时需要
  分页/增量投影。
- W-3（归一）：合并只按节点 id 精确匹配；同一来源的不同写法不会合并（宁可漏合不猜）。
- W-4（测试替身完整性遗留）：本轮为血缘页 run scope 补了 `/runs/{id}/claims` 与
  `/runs/{id}/evidence` 替身（此前缺失 ⇒ 选中 run 时页面 500）。严格替身仍**只覆盖已被
  用例走到的端点**；后续新增页面时应先补替身再写用例。
- W-5（设计基线阈值）：`maxDiffPixelRatio: 0.02` 对"新增一个中等尺寸面板"这类改动**不敏感**
  （本轮实测 1.73%）。基线更新不能依赖门禁报警，改页面时必须主动重生成并目检。
- W-6（继承，未在本轮处理）：RECHECK-054 的 W-1（worker SIGTERM 打不断阻塞中的 HTTP 读，
  退出上界 = 客户端 30s 超时）仍开放，属 GOAL-002 后续 EC 决策项。

## 复现

```
# 后端
python -m pytest tests/api/test_project_lineage_api.py -q          # 6 passed
# 前端（stub 替身链路 / 真实 API 链路）
cd apps/web && pnpm run test:e2e                                   # 40 passed
cd apps/web && pnpm run test:e2e:live                              # 20 passed
pnpm exec eslint .                                                 # 0 error（2 条既有软阈值 warning）
# 设计基线：先量差异（会把实际值与基线对比），差异 < 2% 时不会报警，必须主动重生成
rm apps/web/tests/e2e/design-fidelity.spec.ts-snapshots/library-lineage-*-win32.png
cd apps/web && pnpm exec playwright test design-fidelity --update-snapshots
bash scratch/gen_linux_baseline_route.sh library-lineage            # pinned noble 容器内重生成
# 本地门
sh scratch/run-m0-cycle12.sh                                       # profile=m0; 23 deterministic checks
```
