---
id: MEM-20260923-106
title: "运行链的证据键只含 `ids`（实测）：同一条 task 里第二次检索要么**硬失败**要么塌成一条 ⇒ 单 task 的非自产来源上限是 3；`minimum_sources: 10` 这类门槛**加调用**补不上"
status: ACTIVE
created_at: 2026-09-23
updated_at: 2026-09-23
scope: repository
confidence: 0.9
review_after: 2027-09-23
source_plans:
  - .cursor/plans/tasks/PLAN-20260922-138-real-experiment-chain-via-m12.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260923-139-goal-011-closeout-recheck.md
supersedes: []
tags:
  - run-chain
  - evidence
  - goal-011
  - refutation
---

# 运行链的证据键（`_operation_key`）与来源上限（GOAL-011 cycle 9 实测）

## 做了什么

把「多声明几次检索调用就能满足 `minimum_sources: 10`」这条假设**实测证伪**（这是用户拍板取
(B) 时隐含的前提）：写 `scratch/goal011-c9-runchain-source-count-probe.py`，在同一条 task 上
声明多次检索调用（A 重复参数 / B 分页参数 / C 不同 query），并读 evidence 面。

## 为什么这样做

- **证据与来源的 id 是 `operation_key` 的函数**（`packages/application/evidence/tool_evidence.py`：
  `evidence:{run_id}:{operation_key}`、`source_origin_for = tool:{tool_id}:{task_id}:{operation_key}`），
  而 `_operation_key` **只带 `ids`**（`packages/application/run_orchestration/phase_capabilities.py`）。
  ⇒ 同一 task 内**第二次**检索要么与第一次**撞键**（`conflicting source registration: tool:…`，硬失败），
  要么塌成同一条；**改 `retmax`/`retstart` 不影响键**，所以"加调用"不等于"加来源"。
- **上限是 3**：实测 evidence 面 = `GENERATED / USER_PROVIDED / RETRIEVED×2`，非自产独立来源 **3**
  条，对着 `minimum_sources: 10` 的门槛。
- 同一批实测还被证明**未接线**（契约判据已声明、产品路径没有调用方）：`SCHEMA_VALID` 的
  `schema_check`、`TEST_PASSES` 的 tests 事实、`POLICY_COMPLIANT` 的策略裁决——`EvaluationInputs`
  里根本没有对应字段。

## 怎么做与复现

1. `python scratch/goal011-c9-runchain-source-count-probe.py`：三种"多调用"表达各自跑一遍；
   判据是 **evidence 行数与是否硬失败**，不是调用次数。
2. 要看**终局判词**：`PLAN=single EXPERIMENT=0 python scratch/goal011-c9-m12-offline-chain.py`
   ⇒ 逐字 `SCHEMA_VALID … unavailable; EVIDENCE_COVERAGE: 3 < 10 sources`。
3. 结论只能往**产品程序**上走（键要带参数摘要、或给这条判据重新做一次决定）；**不要**在装配面
   堆调用——那会在第二次调用处直接红。

## 适用边界

- 判的是**当前的键设计**，不是"检索没用"：单次分页检索确实能拿到多条 PMID（它们进**同一条**
  evidence/source 的 payload）。
- 与 [[retrieved-evidence-nature]] 那条（`RETRIEVED` 加在 TrustLabel 上、覆盖判据按来源性质判）
  相互独立：那条判**性质**，这条判**条数上限**。

## 来源

- `scratch/goal011-c9-runchain-source-count-probe.py`（A/B/C 三方案；输出 `conflicting source registration`）；
  `PLAN-20260922-138`「实测结论」节 + 证据 E-3/E-4/E-5。
