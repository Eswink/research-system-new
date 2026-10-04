---
id: RECHECK-20261005-280
slug: goal-029-ec03-write-capability-canonical-path
title: GOAL-029 EC-03 复检 — 写能力的 canonical 路径与旁路风险（唯一性 + 写后读得到 + 旁路可抓 + 残余登记）
status: COMPLETED
result: PASS_WITH_WARNINGS
created_at: 2026-10-05
updated_at: 2026-10-05
plan_id: PLAN-20261005-279
parent_goal: GOAL-20261004-029
reviewer: root-agent
owners:
  - root-agent
---

## 复检对象

`PLAN-20261005-279`（GOAL-20261004-029 的 cycle 3 子计划）—— EC-03：写能力
（`deliverable.write` / `deliverable.edit`）的 canonical 路径与旁路风险。

## 检查结果

| AC | 判据 | 结果 | 证据 |
| --- | --- | --- | --- |
| AC-1 | canonical 唯一性 | **PASS** | AST 扫 `packages` / `services` / `adapters`：构造 `f"{run_id}:{_DELIVERABLE_NAME}"` 的位置**只有** `packages/application/m12_reference/persistence.py:107`；`persist_completion` 的生产调用点**只有** `clean_run.py:174` |
| AC-2 | 先判后写 | **PASS** | 读 `persist_completion` 的**语句顺序**：准入（`_succeeded_run`）先于 `_put_manifest` / `_put_deliverable` / `save_audit` / `save_run` |
| AC-3 | 写后读得到 | **PASS** | canonical 落点（同 id、同分类 `research_deliverable`）⇒ 读面工具 `deliverable_read` 读到**同一 payload** 与 **同一 digest**；未产出 ⇒ **点名**（不生成空报告） |
| AC-4 | 旁路可抓 | **PASS** | 准入用 **manifest digest 对账** + `RUNNING→SUCCEEDED` 迁移（两重）；store 层**没有**闸门这一点被**显式登记**（protection 来自状态机，不来自写入点） |
| AC-5 | 残余登记 | **PASS** | `save_plan` 的生产调用点 **3 处**（`m12_reference/persistence.py:45` + `routers/experiments.py:192,209`）⇒ 无共同漏斗；`experiment_store` 实现含 `ON CONFLICT`（无条件 upsert）—— 现状被钉住 |
| AC-6 | 本地门 | **PASS** | `ruff` / `format` / `mypy`（1091 files）绿；`tests/architecture/python + tests/application + 读面 API` **995 passed / 1 skipped**；新增判据 **9 passed** |

## 按压（两向）——**判据自身的一次修正**

| # | 按压形态 | 结果 | 说明 |
| --- | --- | --- | --- |
| P-1（首版，**未咬住**） | 把 `_succeeded_run` 移到 `save_audit` **之后**（守卫不再第一步） | 9 passed（**判据仍绿**） | **判据的缺口**：首版「先判后写」只扫 `ast.Name` 调用 ⇒ 看不见**属性调用式**写入（`persistence.experiment_store.save_audit(...)`）⇒ 守卫挪到它后面时判据不红 |
| P-2（加固后，**咬住**） | 同上按压 | **1 failed**（`test_the_guard_precedes_the_write`） | 改为**语句级**顺序断言（逐语句收集 guard / write 的行号，比对 `min(guard) < min(write)`）⇒ 该按压判红；复原后 9 passed |

**这条修正本身是 EC-03 的一部分**：它证明「判据自己咬不咬得住」也需要按压取证
（与本文档同族的教训：`W-1` 类缺口往往不是被测对象错了，而是**判据的射程**没覆盖到）。

## 复检发现（如实登记，未修）

- **`W-1`**：**域里没有 `Deliverable` 实体** —— 交付物是 application 层的未定型 `dict` + artifact。
  因此 EC-03 证的是「**写入点唯一 + 写后读得到 + 旁路被准入挡住**」，
  **不**是「有一个领域类型被正确构造」。若将来引入 `Deliverable` 域实体，本判据需同轮复核。
- **`W-2`**：store 层**没有闸门**（`ArtifactStore.put` 对已存在 id 是 update；`_put_deliverable`
  无「已存在则拒」）。保护**只**来自 canonical 路径的状态机准入。本判据把这一点**钉住**
  （防「以为 store 会拦」），但**不改**它 —— 加闸门会动既有写路径与判据。
- **`W-3`**：实验计划写面**无共同漏斗**（3 个生产写入点、store 无条件 upsert、无 provenance 层）
  —— 本 GOAL **原样保留**（收窄要动既有写路径与判据）；已以判据固定现状。
- **`W-4`**：`deliverable.write` / `deliverable.edit` 在差集表里是**「该拒绝」**
  （写类 ⇒ `default_effect: DENY` 即正确）⇒ 本 GOAL **不**给它们放行、**不**实现写工具；
  EC-03 只做**判定**（该 EC 的原文允许「若勘察判定写能力不属 A 组 ⇒ 如实登记理由」）。
- **`W-5`**：本判据扫的是 `packages` / `services` / `adapters` 三个生产根，
  **不**扫 `tests` / `tools`（那里的同 id 写入是受控夹具，非生产路径）—— 射程有界且写在源码里。

## 结论

`PLAN-20261005-279` 的 **AC-1…AC-6 全 PASS**；`result = PASS_WITH_WARNINGS`
（五条 `W-NN` 如实登记：域无实体 / store 无闸门 / 计划写面无漏斗 / 写能力仍该拒绝 / 射程有界）。
**EC-03 收口**（判定在树 + canonical 唯一性 + 写后读得到 + 旁路可抓 + 残余登记）。

**明确否认**：**不**宣称项目安全（`R-M1` 未收口）；**不**宣称投递语义为「恰好一次」
（**明确否认**；口径只能是 at-least-once + idempotency + deduplication）。
