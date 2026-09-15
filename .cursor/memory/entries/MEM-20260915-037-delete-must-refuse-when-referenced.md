---
id: MEM-20260915-037
title: DELETE 面：被引用即 409 且列出引用，不静默级联；合成行必须显式拒绝
status: ACTIVE
created_at: 2026-09-16
updated_at: 2026-09-16
scope: repository
confidence: 0.90
review_after: 2027-09-16
source_plans:
  - .cursor/plans/tasks/PLAN-20260915-061-project-delete-and-archive-semantics.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260915-061-project-delete-and-archive-semantics.md
supersedes: []
tags:
  - delete-semantics
  - referential-integrity
  - idempotency-key
  - console-write-surface
---

# DELETE 面：怎么删一个"还有东西指着它"的注册行

## 做了什么

`DELETE /projects/{id}`（G2/PLAN-061）把 `#/portfolio/projects` 的"不提供删除
（归档即终态）"缺口变成真实能力：默认项目 409 `Project Reserved`、未知 id 404、
未装配 store 503、**仍被引用 409 `Project In Use`** 且 detail 逐项列出引用计数
（`runs=2, drafts=1` 形式）、无引用 204（注册行 + 随项目创建的设置行一起删）。
前端每行一个删除动作（默认项目按钮禁用 + title 说明），确认框文案与后端语义同源。

## 为什么这样做

1. **409 + 引用清单，不级联**：项目注册行下面挂着 runs / 协议草稿 / 实验队列 /
   库资源 / ops 规则与事故。控制面一旦"顺手删掉"，用户会在不知情的情况下丢失研究
   数据；反过来"假装成功但留着行"更糟（用户以为删了）。因此删除是**拒绝 + 可读原因**，
   处置权交回用户。
2. **合成行必须显式拒绝，不能静默 no-op**：`example-project` 由 examples 契约合成，
   删了也还在。对这种行返回 204 会造成"删除成功但列表里还有"的幻觉；
   404 也不对（它确实存在）。正确答案是 409 + 说明它是合成基线。
3. **只报能证实的引用**：`_references()` 只枚举控制面**项目作用域**的存储；
   run 的从属事实（approvals/budget/evidence/eval report）由 runs 承载，
   报了 `runs=N` 就等于报了它们——重复计数只会让用户以为要清更多东西。

## 怎么做与复现

```python
# services/api/routers/projects.py（判定顺序即语义顺序）
DEFAULT_PROJECT_ID → 409 Project Reserved
_merged_projects(deps).get(id) is None → 404
_references(deps, id) 非空 → 409 Project In Use + ", ".join(references)
store.delete_project(id)  # 行不存在 → KeyError → 404（读时在、删时没了）
deps.project_settings_store.delete(id)  # 设置行与项目注册同生，不是研究数据
```

`ProjectStore.delete_project` 只删注册行本身：**端口层不级联**，级联/拒绝的决策留在
路由层（有 context 能给出原因），存储层只做它被要求做的那一件事。

```
python -m pytest tests/api/test_projects_api.py -q          # 13 passed（7 条删除语义）
cd apps/web && pnpm exec playwright test project-delete     # 4 passed（stub：409/204/上下文回退）
cd apps/web && pnpm run test:e2e:live -g 项目删除           # live：409 引用清单 + 204 + 再见 404
```

## 适用边界（踩过的坑）

- **DELETE 也要 `Idempotency-Key`**：`services/api/middleware.py` 的
  `_MUTATING_METHODS` 含 DELETE，漏带即 422。**替身 harness 不校验该头**
  （`tests/e2e/stub-api.ts` 只做路由匹配），所以"stub 全绿"不能证明写面可用——
  live 套件才是这条约束的守卫。
- 删除活动项目时前端把 `activeProject` 回退到默认项目（否则后续读面会持续打已删 id）；
  这条副作用在 `useProjectDeletion` 里，不在组件里。
- 模型/端点/草稿/Agent 的 DELETE 早于本轮落地，语义一致（被引用 409）；项目是
  第一个"引用面横跨多个存储"的删除点，因此多了一个 `_references()` 聚合。
- 归档（PATCH status=ARCHIVED）与删除是两条不同的语义：归档改状态、可恢复；
  删除是移除注册行。页面两个动作并列，不要再把"归档即终态"当缺口说辞。

## 来源

- PLAN-20260915-061 / RECHECK-20260915-061（GOAL-20260915-002 cycle 7 / EC-06）。
- 相关：[[MEM-20260915-036]]（写面必须被读面消费：本项目删除后列表真的变化）、
  [[MEM-20260915-035]]（同一条判据的第一个实例）。
