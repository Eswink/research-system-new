---
id: MEM-20261115-243
title: "canonical 序列化拒绝 float：随合约进 manifest 的域对象字段必须用 Decimal（且 run 会静默死）"
status: ACTIVE
created_at: 2026-11-15
updated_at: 2026-11-15
scope: repository
confidence: 0.98
review_after: 2027-05-15
source_plans:
  - .cursor/plans/tasks/PLAN-20261114-113-memory-last-mile.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261115-113-memory-last-mile.md
supersedes: []
tags: [canonical-serialization, decimal, manifest, preflight, contract, goal113]
---

# canonical 序列化拒绝 float：manifest 绑定的域对象字段必须用 Decimal

## 做了什么

GOAL-113 第一版 `MemoryExportSpec.confidence: float = 0.8`（随 `TaskContract` 进
CompiledRunPlan 与 RunManifest）。离线十一相 product-path 9 条判据全红、live 两次
FAILED；run 的死状**极静默**：POST 返回 200、run state=FAILED、**outbox 零事件**、
失败消息为 null。修法：字段改 `Decimal("0.8")`（`Decimal` 是 canonical 词表既有成员，
`budget` 同型）；loader `Decimal(str(...))` 换算；晋升边界 `float(...)` 显式换算
（门链提案面 `MemoryWriteProposal.confidence` 是 float，提案本身不进 digest）。

## 为什么这样做

`packages/domain/serialization.py` 的 `_encode` 对 float **点名拒绝**
（`ValueError: float is not allowed in canonical serialization`）—— 这是确定性
digest 的机械形态：float 的跨平台/跨版本表示不可信。任何**被 `digest_of` 遍历的
dataclass**（TaskContract → plan → manifest）都不得新增 float 字段。

## 结果与反证

- 定位手段：对 `deps.runs.start_run` 包 traceback 的探针（`run_from_execution` 的
  `except ValueError` 会吞掉消息 ⇒ 读 run 行/事件面看不到任何原因）。
- 修复后离线链 9/9 复绿；live run `8ba73c2a` SUCCEEDED。

## 怎么做与复现

复现：给 `TaskContract` 挂一个带 `float` 字段的 spec dataclass、在
`examples/contracts/task_contracts.yaml` 里声明它、跑
`tests/e2e/test_direction_to_manuscript_product_path.py` ⇒ 十一相全 FAILED；
对 `deps.runs.start_run` 包 traceback ⇒ `ValueError: float is not allowed in
canonical serialization`（`packages/domain/serialization.py:37`）。
修复后复跑 ⇒ 9/9 + live SUCCEEDED（读数
`.cursor/plans/goals/evidence/GOAL-20261114-113-live-m12-memory.json`）。

## 适用边界

- 判的是「进 digest 的对象树不得有 float」；`MemoryWriteProposal.confidence`
  这类**不进 digest** 的门链提案面仍是 float，边界处显式 `float(...)` 换算。
- run 静默死（POST 200、state=FAILED、零事件、失败消息 null）只在此收敛路径上
  实测；其它 ValueError 收敛路径未逐一枚举。

## 失效与复核触发器

- 若 canonical 序列化词表放宽（`serialization.py` 允许 float）或 manifest 不再
  内嵌合约正文，本条失效。

## 来源

- GOAL-20261114-113 / PLAN-20261114-113 / RECHECK-20261115-113（F-1 节）。
- live run `8ba73c2a` 之前的两次 FAILED live run（DB `goal106-live-27440-*`）。

## 相关

- `packages/domain/serialization.py`、`packages/domain/manifest.py`、
  `services/api/run_execution.py`（`except ValueError` 收敛路径）。

