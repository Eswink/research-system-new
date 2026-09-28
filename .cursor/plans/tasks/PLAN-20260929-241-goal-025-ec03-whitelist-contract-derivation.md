---
id: PLAN-20260929-241
slug: goal-025-ec03-whitelist-contract-derivation
title: GOAL-025 cycle 3（EC-03）：读面白名单的契约派生与两向差异清单 —— 从 OpenAPI 快照派生读面 + 逐条差异判定 + 反证
status: DONE
created_at: 2026-09-29
updated_at: 2026-09-29
parent_goal: GOAL-20260929-025
cursor_plan_uri: null
subagent_parallel_limit: 3
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260929-025 的 **EC-03**（收 GOAL-024 的残余 `G24-3`：读面白名单是「人工判定 +
    机械自审」，**不是**从契约派生）。授权沿用该 GOAL 的 `authorization.ref`：范围 = 「**新增判据**」
    （一律落 `tests/**`，落在既有 `python/tests` 收集面内 ⇒ m0 条数仍 `23`）」+「**测试侧夹具 / 探针**」；
    push-to-main-for-CI 口径（**只推 main、不 force**、不重写历史、不推旁支；push 前 `git pull --ff-only`）。
    **本 PLAN 专属边界**：**只新增**两个文件（`read_face_whitelist_derivation.py` +
    `test_privacy_read_face_whitelist_derivation.py`），**只读**复用 GOAL-024 的三份受判资产
    （`read_face_route_registry.py` / `read_face_canary_support.py` / `content_canary_support.py`）
    与其既有清单 / 分类（**逐字节不改**）；**不修改**任何既有判据 / 夹具 / 门禁 / 阈值 / 放行面；
    **不动**权威快照 `docs/api/openapi.m13.json`（它由 `test_openapi_snapshot.py` 逐字节重生成钉住）；
    **不改** `PRODUCT_ROOTS` / m0 条数 / 作业结构；**零**新依赖；**全离线**（无真实出网）；
    派生算法的修补**只允许**落本轮新增文件；**不得**宣称项目安全（`R-M1` 未收口）。
exit_criteria:
  - id: AC-1
    criterion: >-
      **派生面存在且非空**：从**权威契约面**（提交的 OpenAPI 快照 `docs/api/openapi.m13.json` 的
      GET 路径集）+ **框架内建路由**（OpenAPI schema 不含的那一半，逐条带理由）派生读面；
      派生面**非空且有下界**（快照读不到 / 变空 ⇒ 判红，不许退化成「无差异 ⇒ 通过」）。
    status: PASS
  - id: AC-2
    criterion: >-
      **两向差异清单逐条判定**：`派生 − 人工清单` 与 `人工清单 − 派生` 两向逐条点名；
      本轮实测差异 = **∅**（逐条判定为「无差异」），差异非空即判红并把清单本身放进失败消息。
    status: PASS
  - id: AC-3
    criterion: >-
      **三条独立路径互相钉住**：①提交的快照 × ②应用**实时** schema（`app.openapi()`）
      ③应用**运行时路由树**（`read_routes(app)`）—— 任一条漂移都会在差异清单里点名
      （实时 schema 与快照不一致 ⇒ 判红「快照可能过期」）。
    status: PASS
  - id: AC-4
    criterion: >-
      **终态**：四道门全绿；既有判据**逐字节未改**且与本轮新判据合跑全绿；
      三处源码按压**先红后绿**且 raw `sha256` 逐字节复原；as-is 本机 m0 =
      `PASS: profile=m0; 23 deterministic checks`（**记录写入之后**）；治理 `validate.py` 绿；
      CI 台账到终态（八 job + CodeQL + `run_attempt`）。
    status: PASS
latest_recheck: .cursor/plans/rechecks/RECHECK-20260929-242-goal-025-ec03-whitelist-contract-derivation.md
memory_entries:
  - .cursor/memory/entries/MEM-20260929-165-manual-whitelist-needs-a-derivability-check.md
---

# PLAN-20260929-241 — GOAL-025 cycle 3（EC-03）：读面白名单的契约派生与两向差异清单

**动因**：GOAL-024 的读面白名单（68 条路由逐条 `declared_content` / `zero_hit`）是**人工判定 +
机械自审**——它能挡住「未分类的新路由」（运行期观测到未登记路径 ⇒ 判红），但**不能**回答
「这份人工清单**是否等于**应用对外声明的读面」。本 PLAN 补上**派生**这一半：把**权威契约面**
（受门逐字节钉住的 OpenAPI 快照）当参照，与人工清单做**两向**差分，差异逐条判定。

**权威面的选择理由（写在判据源码里，不靠散文）**：`docs/api/openapi.m13.json` 由
`tests/contracts/test_openapi_snapshot.py` **重新生成并与提交前的字节逐字比对** ⇒ 不会静默漂移，
且它同时是**前端类型的生成源**。人工写的 `docs/api/CONTROL_PLANE_API.md` 是文档、会漂移 ⇒
**不作为**权威面（本轮实测的另一条候选被否）。

## 验收条件

见 frontmatter `AC-1`…`AC-4`。

## 实施清单

- [x] WP1：`tests/observability/read_face_whitelist_derivation.py`（**128 行**）—— 快照派生
      （读不到 / 结构不符 ⇒ 空元组，由下界判红）、任意 schema 派生、框架路由逐条登记
      （`FRAMEWORK_ROUTES`，4 条带理由）、两向差异与判据入口（`derivation_findings`）、
      派生面下界 `MIN_DERIVED = 40`。
- [x] WP2：`tests/observability/test_privacy_read_face_whitelist_derivation.py`（**124 行 / 10 例**）
      —— 非空取证（快照在位 + 达下界）、主判据（派生 == 人工清单）、框架登记自审 +
      「框架路由必须进人工清单」（**含上界 `== 4`**）、实时 schema 与快照一致、
      运行时路由树 == 派生面、三条判据内反证（多一条 / 少一条 / 快照读不到）、
      真实应用上的新增读路由按压、可复跑（同树重复派生逐条相同）。
- [x] WP3：`RECHECK-20260929-242`（独立复检）。
- [x] WP4：记录（本 PLAN / GOAL 回写）+ 四道门 + as-is m0 + push + CI 台账终态。

## 证据

| 观测 | 数值 / 结论 |
| --- | --- |
| 新判据 | `test_privacy_read_face_whitelist_derivation.py` **10 passed** |
| 派生面（本轮实跑） | 提交快照 GET **64** 条 + 框架内建登记 **4** 条 = 派生面 **68** 条；人工清单 **68** 条 |
| 两向差异清单 | **∅（空）** —— `派生 − 清单` = ∅、`清单 − 派生` = ∅（逐条判定为无差异） |
| 派生面下界 | `MIN_DERIVED = 40`：快照读不到 ⇒ `派生面低于下界:… < 40 ⇒ 快照可能读不到` 判红（**不许空真**） |
| 三条路径互钉 | 快照 × 实时 `app.openapi()` × 运行时路由树：三向差分全为 ∅；实时与快照不一致 ⇒ 判红「快照可能过期」 |
| 框架内建登记 | `/docs`、`/docs/oauth2-redirect`、`/openapi.json`、`/redoc` —— 逐条理由非空 + 上界 `len(FRAMEWORK_ROUTES) == 4` |
| 判据内反证（两向） | R1 清单多一条 `/__extra` ⇒ 判红点名；R2 清单少一条 `/health` ⇒ 判红点名；R3 快照读不到（空目录）⇒ 下界判红；R4 **真实应用**上新增读路由 ⇒ 实时 schema 与快照立刻差异并点名该路由 |
| 按压（源码级，先红后绿） | P1 框架清单塞入清单里没有的 `/__bogus-frame` ⇒ `读面白名单与契约派生面不一致:['派生面有而清单没有:/__bogus-frame']`（连带 2 例）；P2 派生根 `GET`→`PATCH` ⇒ `快照里的 GET 只有 9 条 < 下界 40` + 两向差异长清单（5 例）；P3 两向差异只留一向 ⇒ `test_an_extra_registry_entry_is_red` 判红（清单陈旧那一向是承重的） |
| 逐字节复原（raw `sha256`） | 三处按压后均回到 `ae9bf121fdc4f4b1ae15e488d13d8f1707bc2b9a4dce5ef7bc12e6ed1f3aa888`（`MATCHES_BASELINE True`），复绿 **10 passed**；证据 `scratch/goal025-ec03-press-matrix.log`（**二进制写盘**） |
| 四道门 | `ruff format --check` = `2 files already formatted`；`ruff check` = `All checks passed!`；`mypy` = `Success: no issues found in 2 source files`；规模 **128 / 124 行**（规模门定向跑 **1058 passed**） |
| 既有判据未改 | `tests/observability/` 全目录 **134 passed, 1 skipped**（cycle 2 后 124 + 1 ⇒ **+10** 恰为本轮新判据）；`git status -- tests/observability` 只显示本轮两个**新增**文件 |
| m0 / 治理 / CI | 见 GOAL 迭代日志与 CI 台账（**记录写入之后**才跑；终态行 `PASS: profile=m0; 23 deterministic checks`） |

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-29 | IN_PROGRESS | 建档（GOAL-025 cycle 3，EC-03）；两个新文件与判据已进工作树（10 例全绿、四道门绿、三处源码按压先红后绿且 raw `sha256` 逐字节复原）；复检与收口记录待写。 |
| 2026-09-29 | DONE | 两个新文件进树（**10 例全绿**）、四道门绿、三处源码按压先红后绿且 raw `sha256` 逐字节复原、`RECHECK-20260929-242` = `PASS_WITH_WARNINGS`（`W-1`…`W-6`）。 |

## 影响报告

- **Domain/API/schema**：无（`tests/**` + 记录）。权威快照 `docs/api/openapi.m13.json` **只读**。
- **安全/凭据**：无凭据改动；新判据全离线；本轮不构造任何金丝雀（读面路由集合面，不含内容）。
- **兼容性/迁移风险**：无（纯新增文件；既有判据逐字节未改，m0 条数仍 `23`）。
- **上游版本影响**：无（零依赖改动）。
- **下一项任务**：GOAL-025 cycle 4（EC-04：自举收口 —— `tools/verify_goal025_closeout.py` 进树 +
  `IN_SCOPE` 纯收紧 + 两树复检 + as-is m0 + CI 台账 + 残余逐条）。
