---
id: PLAN-20260918-104
slug: batch-read-upper-limit-and-fake-boundary
title: 批量读显式上限 + Fake 弱同判写成逐条点名的显式边界（EC-05）
status: IN_PROGRESS
created_at: 2026-09-18
updated_at: 2026-09-18
parent_goal: GOAL-20260918-006
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260918-006 cycle 5 = EC-05（GOAL-005 收口结论 / RECHECK-097 W-2 + W-3）。授权来源：2026-09-18 用户 goal 模式指令（新建承接 GOAL-006 并自动化循环推进、无需逐轮确认）。push-to-main-for-CI 授权沿用 GOAL-001…005 批准口径（只推 main、不 force、不重写历史、不推旁支触发 CI）。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260918-104 — 批量读上限与 Fake 弱同判边界（GOAL-006 cycle 5 = EC-05）

## 目标

EC-05 的两件事（RECHECK-097 W-2 / W-3）：

1. **`dispatch_ownership_many` 加显式上限语义**：超限行为可判定（明确 raise / 分块 /
   契约上限），上限值写在**契约**（port docstring + `PORTS.md` / `CONTROL_PLANE_API.md`）
   而不是隐含；
2. **Fake 的弱同判**：要么与 SQLite/PG 对齐（Fake 实现过期语义并有同判用例），要么在契约里
   把弱化写成**显式边界**——同判用例只断言可同判部分，**不一致处逐条点名**。

## 先探明再动手（只读勘察，逐条可复核）

1. **上限现状**：port 的 `dispatch_ownership_many(run_ids: tuple[str, ...])`
   （`packages/application/ports/workflow_engine.py:279`）契约只写"同判 / 全量条目 /
   一个快照 / 零写零缓存 / 空入参返回空 dict"，**没有任何规模上限**；调用方
   `services/api/run_dispatch_view.py::dispatch_ownership_read_many` 直接把整页 id 传进去，
   而列表路径（`GET /projects/{id}/runs`）**未分页** ⇒ 现在没有分页不代表没有上限问题。
2. **三实现**：SQLite `adapters/sqlite/workflow_engine.py:202`（`json_each(?)` 绑定参数）、
   PG `adapters/postgres/projections.py:192`（`= ANY(%s)`，`workflow_dispatch` 记账）、
   Fake `adapters/fakes/workflow_engine.py:282`（`_ownership_of` 逐 run 装配、记账一次）。
   三者的"超限"今天都没有判定——传 10 万个 id 就发一条 10 万参数的语句。
3. **Fake 的弱同判已被执行性钉住**：`tests/contracts/test_dispatch_ownership_contract.py`
   已有 `test_the_fake_never_expires_a_lease_it_holds`（Fake 恒不过期）与
   `test_the_batch_read_equals_the_per_run_read` / `test_an_empty_batch_reads_nothing`；
   Fake 类 docstring 写"**这不是与持久化实现同强度的判据**"，port docstring 写
   "Fake 无租约过期语义（其"活"= 仍在租约表里）由契约用例钉住"。
   **缺的是**：把"可同判 / 不可同判"**逐条**点名并做成机器判据（今天散在注释里，
   没有一处能回答"这条同判用例断言的是哪一部分、被排除的是哪几条"）。
4. **既有同判轴**：契约用例用三个 `factory`（Fake / SQLite / PG?）跑同一断言；SQLite
   有注入时钟的过期用例（`tests/adapters/sqlite/test_dispatch_ownership.py`：未过期 / 过期 /
   边界秒 / LOST worker / 控制面租约），PG 有 parity（`tests/postgres/test_dispatch_ownership_pg.py`）。

## 口径

- **上限是契约事实，不是实现细节**：常量放 port（三实现共用），值写在 port docstring 与
  `PORTS.md`/`CONTROL_PLANE_API.md`；超限 ⇒ **可判定地拒绝**（`InvalidInputError`），
  **不静默截断**（截断会让读面少条目 = 悄悄说假话）。
- **分块是调用方的决定**：port 一次调用只承诺**一个快照**；跨块就不是同一个快照 ⇒
  服务层分块时必须在文档里写明"整批可能跨多个快照"，不许假装整批同刻。
- **Fake 走"显式边界"路线**：不为了实现同判去给 Fake 造一套时钟/回收语义（Fake 是受控替身，
  无过期路径是**有意**的）。改法 = 契约里逐条点名"可同判轴 / 不可同判轴"，并用机器判据钉住：
  ① 契约文本里的轴清单与判据里的轴集合一致；② 被排除的轴在**真实现**上有对应用例
  （SQLite 注入时钟 / PG parity），不是"谁都没测"；③ Fake 的差异本身有可执行反例
  （`test_the_fake_never_expires_a_lease_it_holds`）。
- **零产品行为变化**（除新增的上限拒绝）：不改 `DispatchOwnership` 语义、不改 DTO、
  不改路由形状。

## 验收条件

- **AC-01 上限可判定（三实现同判）**：超限 ⇒ `InvalidInputError`（Fake/SQLite/PG 各一条，
  参数化同一断言）；恰好等于上限 ⇒ 正常返回全量条目；空入参 ⇒ 空 dict 且**不读库**
  （既有用例保留）。**反证**：把某一实现的上限检查去掉 ⇒ 该参数化用例红。
- **AC-02 上限值在契约**：port docstring 与 `PORTS.md` / `CONTROL_PLANE_API.md` 三处写出
  同一个值（判据：三处文本一致，反证：改一处 ⇒ 红）。
- **AC-03 服务层分块**：列表路径超过上限时按上限分块调用（spy 记录调用次数与每块大小），
  合并结果覆盖所有请求 id；文档写明"整批可能跨多个快照"。
- **AC-04 Fake 边界逐条点名**：契约文本给出"可同判轴 / 不可同判轴"清单；判据断言清单与
  契约用例实际断言的轴集合一致，且每个"不可同判轴"在真实现上有对应用例；反证：删一条轴 ⇒ 红。
- **AC-05 门禁**：定向（`tests/contracts tests/adapters/sqlite tests/postgres tests/api`）+
  规模门禁 + `make validate-all` 全量 23 项 + CI 六 job 终态。

## 实施清单

### WP-A — 批量读显式上限

- [ ] port：`MAX_DISPATCH_BATCH` 常量 + docstring 契约条目（值 / 超限行为 / 为什么不分块）。
- [ ] 三实现：入口处校验（超限 ⇒ `InvalidInputError`，不读库）。
- [ ] 服务层：`dispatch_ownership_read_many` 按上限分块 + 合并（文档写明跨块快照边界）。
- [ ] 用例：三实现参数化的"超限拒绝 / 恰好上限 / 空入参不读库" + 服务层分块 spy 用例。
- [ ] **反证实跑**：去掉一个实现的上限检查 ⇒ 红；还原 ⇒ 绿。

### WP-B — Fake 弱同判的逐条边界

- [ ] 契约文本（port docstring + `PORTS.md`）：可同判轴（无派发方 / 重排 / 活租约 /
      未知 run / 批量=逐 run / 空入参）与不可同判轴（租约过期、LOST worker，逐条点名）。
- [ ] 机器判据：轴清单与契约用例集合一致 + 每个不可同判轴在真实现上有用例 + Fake 差异有
      可执行反例。
- [ ] **反证实跑**：删一条轴 ⇒ 红；把某个"不可同判轴"标成可同判 ⇒ 红。

### WP-C — 文档同源

- [ ] `PORTS.md` 与 `docs/api/CONTROL_PLANE_API.md` 的批量读段落写上限值与超限语义、
      Fake 边界指针（三处同一口径）。

### WP-D — 记录与回写

- [ ] RECHECK-20260918-104、MEM-20260918-077、PLAN/ALL_PLAN/`memory/INDEX.md`、
      GOAL-006 回写（EC-05 状态 / 迭代日志 / child_plans / 状态历史 / 续点 → EC-06）。

## 证据

- 待记（执行后填写：上限反证、边界判据反证、定向、m0、CI）。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 5 = EC-05，driver=client-goal / owner=root-agent）：
  只读勘察确认批量读无上限、三实现都无超限判定；Fake 的弱同判已有执行性反例但**没有**
  逐条点名的契约清单与机器判据；`status: IN_PROGRESS`。

## 影响报告

- **Domain / API / schema**：Domain 零变化；DTO/路由形状不变（新增的只是"超限拒绝"这一
  可判定行为）。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无（不新增参数面之外的输入通道；超限拒绝反而收紧资源面）。
- **兼容性 / 迁移风险**：低——上限值远大于当前真实页大小；若将来分页，调用方按上限分块
  （本 PLAN 已把该路径做成默认行为）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 6 = EC-06（失败的诚实边界：结构化任务级归因，或一等边界
  + 守护线程补偿失败的降级读面可见）。
