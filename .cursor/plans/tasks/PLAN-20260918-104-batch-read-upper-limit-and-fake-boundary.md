---
id: PLAN-20260918-104
slug: batch-read-upper-limit-and-fake-boundary
title: 批量读显式上限 + Fake 弱同判写成逐条点名的显式边界（EC-05）
status: DONE
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260918-104-batch-read-cap-and-fake-boundary.md
memory_entries:
  - MEM-20260918-077
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
   （`packages/application/ports/workflow_engine.py`）契约只写"同判 / 全量条目 /
   一个快照 / 零写零缓存 / 空入参返回空 dict"，**没有任何规模上限**；调用方
   `services/api/run_dispatch_view.py::dispatch_ownership_read_many` 直接把整页 id 传进去，
   而列表路径（`GET /projects/{id}/runs`）**未分页** ⇒ 查询规模随页长无界放大。
2. **三实现**：SQLite（`json_each(?)` 绑定参数）、PG（`= ANY(%s)`，`workflow_dispatch`
   记账）、Fake（`_ownership_of` 逐 run 装配、记账一次）。三者的"超限"今天都没有判定——
   传 10 万个 id 就发一条 10 万参数的语句。
3. **PG 的错误边界**：`dispatch_ownership_many` 把调用包在 `try` 里、统一走
   `_wrap_operational` ⇒ 转 `TransientPortError`。**上限校验若写在 `try` 之内会被误分类成
   瞬时失败**（调用方会去重试一个永远不会成功的调用），必须放在 `try` 之外。
4. **Fake 的弱同判已被执行性钉住**：`tests/contracts/test_dispatch_ownership_contract.py`
   已有 `test_the_fake_never_expires_a_lease_it_holds` 与
   `test_the_batch_read_equals_the_per_run_read`；但"可同判 / 不可同判"只写在注释里，
   **没有一处能回答**"这条同判用例断言的是哪一部分、被排除的是哪几条"，也没有任何东西
   阻止文本漂移。

## 口径

- **上限是契约事实，不是实现细节**：常量放 port（三实现共用 `validate_dispatch_batch`），
  值写在 port 常量与三处契约文本；超限 ⇒ **可判定地拒绝**（`InvalidInputError`），
  **不静默截断**（截断会让读面少条目 = 悄悄说假话）。
- **分块是调用方的决定**：port 一次调用只承诺**一个快照**；跨块就不是同一个快照 ⇒
  服务层分块时必须在文档里写明"整批可能跨多个快照"，不许假装整批同刻。
- **Fake 走"显式边界"路线**（不对齐）：不为了同判给 Fake 造时钟/回收语义（Fake 是受控替身，
  无过期路径是**有意**的）。改法 = 契约里逐条点名"可同判轴 / 不可同判轴"，并用机器判据钉住
  点名与断言一致。
- **零产品行为变化**（除新增的上限拒绝）：不改 `DispatchOwnership` 语义、不改 DTO、
  不改路由形状、不改 OpenAPI 快照。

## 验收条件

- **AC-01 上限可判定（三实现同判）**：超限 ⇒ `InvalidInputError`（`retryable=False`）；
  恰好等于上限 ⇒ 正常返回全量条目；空入参 ⇒ 空 dict 且不读库。**反证**：去掉某实现的上限
  检查 ⇒ 该参数化用例红。
- **AC-02 上限值在契约**：port 方法 docstring 与 `PORTS.md` / `CONTROL_PLANE_API.md` 三处
  同名同值（判据：三处文本一致，反证：改一处 ⇒ 红）。
- **AC-03 服务层分块**：超过上限时按上限分块调用（记录每次块大小），合并结果覆盖所有请求
  id；重复 id 不占额度；任一块读不到 ⇒ 整批空（不给半份）；文档写明跨块快照边界。
- **AC-04 Fake 边界逐条点名**：契约文本给出"可同判轴 / 不可同判轴"清单；判据断言清单与
  契约用例实际断言的轴集合一致，且每个"不可同判轴"在真实现上有对应用例；反证：删一条轴、
  把某条轴标错类、把引用写错 ⇒ 红。
- **AC-05 门禁**：定向（`tests/contracts tests/adapters/sqlite tests/postgres tests/api`）+
  规模门禁 + `make validate-all` 全量 23 项 + CI 六 job 终态。

## 实施清单

### WP-A — 批量读显式上限

- [x] port：`MAX_DISPATCH_OWNERSHIP_BATCH = 500` + `validate_dispatch_batch()`（三个实现
      共用同一句判据）+ docstring 契约条目（值 / 口径 / 失败分类 / 谁分块）。
- [x] 三实现：入口最早处校验（Fake / SQLite 在读库之前；PG 在 `try` 之外），超限 ⇒
      `InvalidInputError`。
- [x] 服务层：`dispatch_ownership_read_many` 按上限分块 + 合并（重复 id 先归一；任一块
      读不到 ⇒ 整批空）；docstring 写明"整批可能跨多个快照（块内仍是一个快照）"。
- [x] 用例：三实现参数化的"超限拒绝 / 恰好上限" + SQLite 语句探针（超限时语句数 == 0，
      留对照读反空洞）+ PG 分类与已关闭引擎反证 + 服务层四条单元用例（块大小 / 覆盖 /
      重复 id / 半份答案）。
- [x] **反证实跑**：P1 Fake 去掉校验 ⇒ 红；P2 SQLite 校验挪到取数之后 ⇒ 语句探针红；
      P3 PG 校验挪进 `try` ⇒ 误分类成 `TransientPortError`（红）；三条均复原。

### WP-B — Fake 弱同判的逐条边界

- [x] 契约文本（port **模块 docstring** 末节）：8 条可同判轴 + 3 条不可同判轴（租约过期 /
      LOST worker / 重排与 `BOTH`），每条点名判据文件与用例名。
- [x] 机器判据 `tests/contracts/test_dispatch_ownership_weak_equivalence.py`（7 条）：引用可解析、
      可同判轴必须在三实现上跑、与套件里所有三实现用例**双向一一对应**、不可同判轴的引用
      不许声称三实现、`_FACTORIES` 来自注册表且含 Fake、上限值与两个文档同源。
- [x] **反证实跑**：P4 把批量读用例改 `_PERSISTENT_FACTORIES` ⇒ 2 failed；P5 某条
      `[不同判]` 改 `[同判]` ⇒ 3 failed；P6 用例名写错一个字母 ⇒ 3 failed；三条均复原。

### WP-C — 文档同源

- [x] `PORTS.md` 与 `docs/api/CONTROL_PLANE_API.md`：上限常量 + 值 + 超限语义 + 分块责任 +
      跨块快照边界 + 弱同判边界指针（两处都指向判据文件）。
- [x] **反证实跑**：P7 把 `PORTS.md` 的值改成 400 ⇒ 判据 1 failed；复原。

### WP-D — 记录与回写

- [x] RECHECK-20260918-104（PASS_WITH_WARNINGS，W-1…W-5）、MEM-20260918-077、
      PLAN/ALL_PLAN/`memory/INDEX.md`、GOAL-006 回写（EC-05 PASS + 证据块 / 迭代日志 /
      child_plans / 状态历史 / 续点 → EC-06）。

## 证据

- **反证**：P1…P7 共七条，全部**先红后复原**（细节与实测输出见
  RECHECK-20260918-104「反证与实测」表）。
- **定向**（`RESEARCHOS_POSTGRES_DSN` pin 到测试库、PG 测试容器在跑）：
  `tests/contracts/test_dispatch_ownership_weak_equivalence.py`、
  `tests/contracts/test_dispatch_ownership_contract.py`、
  `tests/adapters/sqlite/test_dispatch_read_snapshot.py`、
  `tests/adapters/sqlite/test_dispatch_ownership.py`、
  `tests/api/test_run_dispatch_view_api.py`、
  `tests/postgres/test_dispatch_ownership_pg.py`、`tests/tooling/test_python_source_limits.py`
  ⇒ **1003 passed**。
- **规模门禁**（50 行函数 / 450 行文件）：**940 passed**（返工后：port 方法 docstring 由
  63 行降到 ≤50；`adapters/postgres/workflow_engine.py` 由 454 行压回 450）。
- **lint/格式**：`ruff check` + `ruff format --check` 变更文件全绿。
- **m0 全量 23 项 = PASS**（`PASS: profile=m0; 23 deterministic checks`）。
  诚实记录：首次以 `.venv/Scripts/python.exe` 直接启动 m0 ⇒ `python/dependency-boundaries`
  与 `python/tests` 红，原因是 `lint-imports` 不在该启动方式的 PATH 上（两条红同源：
  `tests/architecture/python/test_*boundaries.py` 里 `shutil.which("lint-imports")` 取不到）；
  改用仓库既定启动方式 `uv run --frozen --no-sync python -B ...run_all_checks.py --profile m0`
  ⇒ **23/23 PASS**（同一工作树，零代码改动）。**不是**代码回归，也未降低任何判据。
- 文档门随 m0 `framework/docs_consistency_check` = **DOCS-CHECK PASS**。
- CI：见 GOAL-006 迭代日志 cycle 5 行的 run 编号与六 job 结论。

## 状态历史

- 2026-09-18 建档（GOAL-006 cycle 5 = EC-05，driver=client-goal / owner=root-agent）：
  只读勘察确认批量读无上限、三实现都无超限判定；Fake 的弱同判已有执行性反例但**没有**
  逐条点名的契约清单与机器判据；`status: IN_PROGRESS`。
- 2026-09-18 收口：WP-A…WP-D 全部完成；P1…P7 七条反证先红后复原；定向 **1003 passed**、
  规模门禁 **940 passed**、m0 **23/23 PASS**；`status: DONE`，`latest_recheck` 指向
  RECHECK-20260918-104（PASS_WITH_WARNINGS）。

## 影响报告

- **Domain / API / schema**：Domain 零变化；DTO / 路由形状 / OpenAPI 快照不变——新增的
  只是"超限拒绝"这一可判定行为，以及服务层在超大页上的分块（结果集合不变）。
- **持久化 / 迁移**：无。
- **安全 / 凭据**：无新增输入通道；过滤仍全走绑定参数（`json_each(?)` / `= ANY(%s)`），
  超限拒绝反而收紧资源面。
- **兼容性 / 迁移风险**：低。上限 500 远大于今天任何真实页；调用方按上限分块后，
  跨块读可能跨快照（已在三处文档登记）。
- **上游版本影响**：无。
- **下一项任务**：GOAL-006 cycle 6 = EC-06（失败的诚实边界：结构化任务级归因，或一等边界
  + 守护线程补偿失败的降级读面可见）。
