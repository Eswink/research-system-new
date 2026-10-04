---
id: PLAN-20261005-279
slug: goal-029-ec03-write-capability-canonical-path
title: GOAL-029 cycle 3（EC-03）：写能力的 canonical 路径与旁路风险 — 唯一性 + 写后读得到 + 旁路可抓 + 残余登记
status: DONE
created_at: 2026-10-05
updated_at: 2026-10-05
latest_recheck: .cursor/plans/rechecks/RECHECK-20261005-280-goal-029-ec03-write-capability-canonical-path.md
memory_entries:
  - .cursor/memory/entries/MEM-20261005-185-verdict-scope-must-be-pressed-too.md
parent_goal: GOAL-20261004-029
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20261004-029 的 **EC-03**。授权沿用该 GOAL 的 `authorization.ref`：
    「新增判据 / 夹具（落 `tests/**`）」+「修实现过程中发现的真缺陷」+ 文档同源更新 +
    push-to-main-for-CI 口径（**只推 `main`**、不 force、不重写历史、不推旁支；
    push 前 `git pull --ff-only origin main`）。
    **本 PLAN 专属边界**：**不修改**任何既有判据 / 门禁 / 阈值 / 放行面；**不新增** `allow`
    规则（写能力在差集表里判「该拒绝」⇒ 本 PLAN **只判定、不实现写工具、不放行**）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构（终态行仍 `23`）；**零**新依赖；
    **不旁路 canonical 路径**（判据本身就是在断言这件事）；**不得**宣称项目安全（`R-M1` 未收口）；
    **不得**宣称投递语义为「恰好一次」（**明确否认**；口径只能是 at-least-once + idempotency +
    deduplication）。
objective: >-
    按 EC-03 的原文判定写能力：**若勘察判定写能力不属 A 组 ⇒ 如实登记理由**。
    勘察结论（建档轮 F-3）：`deliverable.write` / `deliverable.edit` 域里无实体、无写面、
    差集判「该拒绝」⇒ 本 PLAN **不实现写工具**，而是把「canonical 路径唯一 + 写后读得到 +
    旁路可抓 + 残余登记」变成**可复核的机械事实**。
exit_criteria:
  - id: AC-1
    criterion: >-
      **canonical 唯一性**：生产代码里构造 `f"{run_id}:deliverable.json"` 的位置**只有**
      canonical writer（`m12_reference/persistence.py`）；`persist_completion` 的生产调用点
      **只有**一处。AST 判定（不是 grep）。
    status: PASS
  - id: AC-2
    criterion: >-
      **先判后写**：`persist_completion` 的**语句顺序**上，准入守卫先于**任何**写入
      （含属性调用式写入）。承按压教训：只扫 `ast.Name` 会看不见属性调用。
    status: PASS
  - id: AC-3
    criterion: >-
      **写后读得到**（承 MEM: evidence-read-face-claim-relation）：canonical 落点 ⇒ 读面工具
      `deliverable_read` 读到**同一 payload 与同一 digest**；未产出 ⇒ **点名**（不生成空报告）。
    status: PASS
  - id: AC-4
    criterion: >-
      **旁路可抓**：准入用**manifest digest 对账** + `RUNNING→SUCCEEDED` 迁移（两重）；
      store 层**没有**闸门这一点被**显式登记**（保护来自状态机，不来自写入点）。
    status: PASS
  - id: AC-5
    criterion: >-
      **残余登记**：实验计划写面**无共同漏斗**（≥2 生产写入点 + store 无条件 upsert）——
      现状被判据钉住（本 GOAL 不改它）。
    status: PASS
  - id: AC-6
    criterion: >-
      本地门：`ruff check` / `ruff format --check` / `mypy` 绿；
      `tests/architecture/python + tests/application + 读面 API` 全量绿；治理 `validate.py` 绿。
    status: PASS
implementation:
  - id: WP-A
    title: EC-03 判据（唯一性 / 先判后写 / 写后读得到 / 旁路可抓 / 残余登记）
    files:
      - tests/architecture/python/test_deliverable_write_stays_on_the_canonical_path.py
---

## 背景

EC-03 的原文给了两条路：写能力若属 A 组则必须走 canonical 路径并断言「写入后读面真能读到」；
若判定**不属** A 组则**如实登记理由**、本 EC 合并进 EC-01。建档轮勘察（F-3）判定属于后者：
`deliverable.write` / `deliverable.edit` 在**域里没有实体**（无 `Deliverable` 类）、
**没有 HTTP 写面**、在策略差集表里是**「该拒绝」**（写类 ⇒ 落 `default_effect: DENY` 即正确）。

因此本 PLAN 采取**第三条路**（EC-03 的实质要求仍然成立）：**不实现写工具、不放行**，
但把「canonical 路径是唯一入口 + 写入后读面读得到 + 旁路被准入挡住」做成判据 ——
这样「写能力没有旁路」是可复核的事实，而不是文档承诺。

## 验收条件

见 frontmatter `exit_criteria`（AC-1…AC-6）。

## 实施清单

- [x] **WP-A**：新增 `tests/architecture/python/test_deliverable_write_stays_on_the_canonical_path.py`：
      AST 判定 id 构造点与调用点、语句级先判后写、写后读得到（与读面工具同落点）、
      旁路双重准入、store 无闸门的登记、计划写面无漏斗的登记。
- [x] **按压**：把准入守卫移到 `save_audit` 之后 ⇒ 首版判据**未咬住**（只扫 `ast.Name`）⇒
      改为**语句级**顺序断言 ⇒ 该按压判红；复原后 9 passed。
- [x] **记录**：本 PLAN 收口（`DONE`）+ `RECHECK-20261005-280` + `ALL_PLAN` 投影 +
      GOAL 迭代日志与状态历史。

## 证据

- **commit**：`72b29ef`（WP-A 同提交；显式路径）。
- **判据例数**：新增 **9 passed**；`tests/architecture/python + tests/application + 读面 API`
  合计 **995 passed / 1 skipped**。
- **AST 读数**：id 构造点 = `packages/application/m12_reference/persistence.py:107`（唯一）；
  `persist_completion` 调用点 = `packages/application/m12_reference/clean_run.py:174`（唯一）；
  `save_plan` 调用点 = 3 处（`m12_reference/persistence.py:45` + `routers/experiments.py:192,209`）。
- **按压**：首版未咬住（判据缺口，已在 RECHECK 的 P-1 如实登记）⇒ 加固后咬住（1 failed）⇒ 复原绿。
- **本地门**：`ruff` / `format` / `mypy`（1091 files）绿。
- **CI**：见 GOAL「CI 台账」（本提交 `72b29ef` 的行）。

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-10-05 | IN_PROGRESS | 建档（cycle 3 derive）并执行 WP-A。 |
| 2026-10-05 | DONE | WP-A 收口；判据 9 passed；按压暴露并修正判据自身缺口；`RECHECK-20261005-280` = PASS_WITH_WARNINGS。 |

## 影响报告

- **改动面**：新增判据一份（`tests/architecture/python/`）。
- **Domain / API / schema 变化**：无。
- **安全 / 凭据变化**：无（未放宽任何放行面；未新增 `allow`；写能力仍落 `default_effect: DENY`）。
- **兼容性 / 迁移风险**：无（纯新增判据）。
- **上游版本影响**：无（未动依赖）。
