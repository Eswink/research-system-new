---
id: MEM-20261008-200
title: "新增读面落在哪，由**既有判据**决定：事件面被内容金丝雀挡、制品面被条数断言挡 —— 想放宽它们就是改判据"
status: ACTIVE
created_at: 2026-10-08
updated_at: 2026-10-08
scope: repository
confidence: 0.95
review_after: 2027-04-08
source_plans:
  - .cursor/plans/tasks/PLAN-20261008-323-goal-035-ec01-finding-store-and-two-dimensional-coverage.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261008-324-goal-035-ec01-finding-store-and-coverage.md
supersedes: []
tags: [read-face, privacy-canary, judge-conflict, design-change, goal-035]
---

## 做了什么

要让「验收门的逐条判词」可读时，最省的两个落点**各自被一条既有判据挡下**（都是实测，
不是推演）：

| 想落在哪 | 挡下它的既有判据 | 为什么撞 |
| --- | --- | --- |
| **新事件 payload** | `tests/e2e/test_vertical_slice_happy_path.py::test_artifact_content_is_not_in_domain_json`（内容隐私金丝雀） | 该断言要求**任何**事件 payload 里零出现 `analysis_report`；而 `ARTIFACT_EXISTS` 的判词**逐字点名合约声明的制品名**（`artifact analysis_report exists`）⇒ 同形同串 |
| **每任务一份「结论制品」** | `tests/e2e/test_idempotency.py` | 断言 `list_refs()` 条数**精确值**（`_SEEDED + 1` / `+3`）⇒ 新增一类制品即撞 |

第三条路（**独立存储 + 独立只读路由**）不撞任何既有断言 ⇒ 采用。**没有放宽任何既有判据**。

## 为什么这样做

这两条断言各自的**意图**都成立（内容不进事件面 / 制品条数可判幂等），只是它们用
**子串**与**精确计数**表达意图，于是把「同形的声明派生文本」「新增一类制品」一并挡住。
在「不得放宽既有判据」的约束下，正确动作是**改设计**，不是改断言：

- 判词进事件面 ≈ 让隐私断言放行制品名 ⇒ 那是把受判面写窄；
- 结论做成制品 ≈ 让幂等断言改数 ⇒ 那是把判据改成「改了多少就写多少」。

**顺带实测到的既有张力**（如实登记，本轮未改任何判据）：该金丝雀的第三条断言在**失败
路径**上其实已经与既有产品行为相抵触 —— 被拒的 run 会在 `run.failed` 的 `message` 里
带着同一句判词（点名制品名）；它今天仍绿，只因为那些夹具的 run **从不失败**。

## 怎么做与复现

```bash
# 设计期对照按压（已被弃的两个落点，两次都判红）
# ① 判词放进新事件 payload ⇒ tests/e2e/test_vertical_slice_happy_path.py 1 failed（点名 analysis_report）
# ② 断掉 retrieved 证据的 relation ⇒ tests/e2e/test_two_dimensional_coverage_and_claim_relation.py
#    1 failed: assert 2 == 0（读面空，而判词仍写 "2 >= 1 retrieved"）
uv run --frozen --no-sync python -B -m pytest tests/e2e tests/observability -q   # 修完后全绿
```

新增读面的**连带义务**（漏一条就判红，两条都是既有的）：

- `tests/observability/read_face_route_registry.py` 必须逐条登记（未分类 ⇒
  `未分类的读面路由:/runs/{run_id}/reviews`）；
- 派生一致性判据把人工清单与 **OpenAPI 快照 ∪ 运行时路由树**两向比对 ⇒ 快照要重生成
  （`tools/gen_openapi.py`）、web 类型要同步。

## 适用边界

- 适用于任何「新增读面 / 新增制品类 / 新增事件类型」的落点选择。
- 结论只在**本仓的既有判据集合**下成立 —— 换仓库要先做同样的实测（这正是本条的方法）。
- 登记隐私清单时**一等边界**必须写全：本例的判词按模板只含声明派生的标识符/枚举/计数，
  但 `SCHEMA_VALID` 判负时含校验器错误文本（可能引用输出片段）⇒ 该面是
  「按模板不含正文」**而非**「结构性保证零正文」。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-323-goal-035-ec01-finding-store-and-two-dimensional-coverage.md`
- `.cursor/plans/rechecks/RECHECK-20261008-324-goal-035-ec01-finding-store-and-coverage.md`
- 相关：[[MEM-20261008-199-a-judged-verdict-needs-a-recorded-read-face-not-a-recomputation]]、
  [[MEM-20261008-198-a-round-changes-identity-not-the-phase-id]]
