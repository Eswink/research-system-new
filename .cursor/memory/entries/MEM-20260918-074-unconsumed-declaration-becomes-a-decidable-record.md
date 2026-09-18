---
id: MEM-20260918-074
title: "无消费者声明的正确终态是'可决策形态'——ADR 草案 + 索引登记 + 三处同源指针 + 反证用例"
status: ACTIVE
created_at: 2026-09-18
updated_at: 2026-09-18
scope: repository
confidence: 0.88
review_after: 2027-09-18
source_plans:
  - .cursor/plans/tasks/PLAN-20260918-101-validation-failure-consumption-adr.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260918-101-validation-failure-consumption-adr.md
supersedes: []
tags:
  - governance
  - decision-records
  - canonical-state
  - docs-consistency
  - test-determinism
---

# 无消费者声明：把它做成"可决策形态"，并钉住它仍是 Proposed

## 做了什么

`on_validation_failure` 是 `failure_policy` 自由 dict 里的未知键：声明的意图被
`failure_policy_view().unhonored` **点名**，但不改变任何判定。GOAL-006 cycle 2（EC-02）先
勘察"能不能在既有 canonical 边界内实现按声明处置"，答案是**不能**：

- `task_executor._attempt_once` 先 `engine.complete(..., outcome="SUCCEEDED")` 落 durable
  终态，`register_and_gate` 才跑验收门；门拒收只走 run 级（`run.failed` / `run.degraded`），
  **任务行不动**；
- `ResearchTaskState._TRANSITIONS` 里 `SUCCEEDED` 是终态、**没有任何出边**，
  `DEAD_LETTER` 只能从 `RETRY_SCHEDULED` 到达 ⇒ 按声明改写"已成功的行"必须新增"从终态出发
  的迁移"或新增状态 = canonical 状态机改动。

于是走 EC-02 的 (b)：写 `docs/adr/ADR-0030-validation-failure-consumption.md`
（**Status: Proposed**，含四条可复核事实、选项 A–E 与各自代价、触发条件、影响面）、
在 `docs/INDEX.md` 登记唯一入口、把三处声明面（`failure_policy.py` docstring /
`TASK_HANDOFF.md` §2.1 / `examples/contracts/task_contracts.yaml` 注释）**同源**指向它，
并用一条读真实文件的用例把这份登记钉住。

## 为什么这样做

- **"文档已写明"不是终态，"可决策形态"才是**：三处各自写过"这事没做"，但没有一处给出
  选项与代价 ⇒ 拍板的人还得重新勘察一遍。ADR 的价值在于把"决策需要的事实"一次写清。
- **选项里必须有"不破坏终态语义"的那条**：把门挪到 durable `SUCCEEDED` 之前（选项 D）
  让拒收落在非终态上，是唯一可能"不新增终态迁移"的路径——把 A/B（改终态/加状态）与 D
  并列，拍板人才能比较代价。
- **待拍板要能被机器认出**：`Status: Proposed` + INDEX 条目标明 Proposed + 反证用例
  （改成 Accepted 就红）——防止草案被当成已接受的决策读。
- **判据读真实文件，不读注释**：同源收敛用"文件里同时出现键名与 ADR 文件名"钉住；
  删任一处指针即红。

## 怎么做与复现

```bash
# 登记判据（4 条：ADR 仍 Proposed / INDEX 登记 / 三处同源指针 / 键仍未被消费）
uv run --frozen --no-sync python -B -m pytest tests/tooling/test_pending_validation_failure_registration.py -q
# 反证 ①：删 examples/contracts/task_contracts.yaml 的 ADR 指针 ⇒ 第 3 条红
# 反证 ②：把 ADR 的 Status 改成 Accepted ⇒ 第 1 条红
```

## 适用边界（踩过的坑）

- **待拍板 ≠ 已解决**：本条的交付是决策记录；产品行为与基线逐字相同。引用时先看
  `Status: Proposed`。
- **选项 D 只是分析、未实测**：门的输入面（artifact/evidence 登记）是否依赖"任务已成功"、
  失败路径的租约与事件次序如何，都要在拍板前做一次只读验证轮。
- **存量未盘点**：既有 run 里"门拒收但任务行 SUCCEEDED"的行没有标记，也没有数量。
- **ADR 编号没有权威登记表**：按目录内最大号 +1（0029 → 0030），并行新增有撞号风险。
- **不要为了"有交付"去改状态机**：终态语义（`terminal()` 的消费点、幂等键去重、剩余工作
  计算）一旦被打破，回归面远大于这条声明本身；这正是 escalation 要挡住的。
- 相关：[[MEM-20260918-069]]（死声明要么给消费者要么移除）、
  [[MEM-20260917-061]]（声明需要消费者或被点名）。

## 来源

- PLAN-20260918-101 / RECHECK-20260918-101（GOAL-20260918-006 cycle 2 = EC-02 (b)）。
- 上游：RECHECK-20260918-095 W-2（`on_validation_failure` 仍无消费者）、
  GOAL-20260918-005 收口结论第 3 项。
