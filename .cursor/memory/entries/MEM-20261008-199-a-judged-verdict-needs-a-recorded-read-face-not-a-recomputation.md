---
id: MEM-20261008-199
title: "「判据判过」的证据必须是**求值点落下的记录**：派生式读面在一扇从未求值的门上照样给结论"
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
tags: [acceptance-gate, read-face, canonical-state, replay-vs-record, goal-035]
---

## 做了什么

`GateOutcome.evaluations`（哪条判据 / 过没过 / 判词里的数）一直存在，但**只有被拒的路径**
把它带进失败消息（`gate_rejection_reason`）；**通过的路径上判词哪里都读不到**
（`ReviewFinding` / `Decision` 都是纯内存对象、从不落库；`handoff.decision_refs` 因此
指向一个**不存在**的对象）。

本轮把它**在求值点落库**（新 `ReviewFindingStore`：SQLite + PG + 迁移 016），经
`GET /runs/{run_id}/reviews` 只读回读。判词渲染收成**唯一一处**（`criterion_line`），
落库面与失败消息共用 —— 否则读者会读到一份「像判词」的文本。

## 为什么这样做

**记录 ≠ 重算。** 看上去更省的替代是**派生式读面**：读取时按 canonical 事实（合约 +
账本来源 + 制品）重跑一遍判据，直接把判词算出来。它有一个致命性质：

> **在一扇从未求值的门上，重算照样会给出结论。**

于是读面无法区分「门判过」与「门根本没跑」—— 而这两件事的处置完全相反（一个是正常
收尾，一个是执行链缺了一环）。这正是本仓一贯禁止的**掩蔽**形态（判据绿而事实不在）。

配套纪律（本轮一并落地）：

- 读面**未接存储**必须 **503 并点名**（不是空列表）：空列表与「门没判过」长得一样；
- 未知 run **404**（与 `/usage/` 同口径）；
- 读数要与**独立来源**自洽：判词里的性质维读数 == 读面上 `RETRIEVED` 证据条数；
  计数维读数 == 检索来源 + 声明输入（自产制品**不**计入）—— 两条都由读面推导，不重算判据。

## 怎么做与复现

```bash
uv run --frozen --no-sync python -B -m pytest tests/e2e/test_two_dimensional_coverage_and_claim_relation.py -q   # 5 passed
uv run --frozen --no-sync python -B -m pytest tests/contracts/test_review_finding_store_contracts.py -q           # 3 passed
RESEARCHOS_POSTGRES_DSN=… uv run --frozen --no-sync python -B -m pytest \
  tests/postgres/test_review_finding_store_pg.py tests/postgres/test_migration_files.py -q                       # 8 passed
```

按压（判据不得空转）：把落库改成直接返回 ⇒ 判据 **4 failed**（三条 `assert 0 == 1`）；
把计数维改成「自产也计入」⇒ **1 failed**（`assert 4 == (2 + 1)`）。

## 适用边界

- 适用于任何「某条判据在这一次执行里判过没有」的可复核要求（验收门 / 评审 / 策略裁决 /
  覆盖判据）。
- **不**适用于「事实本身可重算且重算就是真相」的场合（例如 digest 重算、计数投影）——
  那里派生是对的，因为答案不依赖「有没有跑过」。
- 落库必须带**作用域**（run/task/contract）：`ReviewFinding` 这类域类型本身不含归属，
  作用域放在存储面（本轮做法），避免为读面改域类型。

## 来源

- `.cursor/plans/tasks/PLAN-20261008-323-goal-035-ec01-finding-store-and-two-dimensional-coverage.md`
- `.cursor/plans/rechecks/RECHECK-20261008-324-goal-035-ec01-finding-store-and-coverage.md`
- 相关：[[MEM-20261008-200-existing-judges-decide-where-a-new-read-face-may-land]]
