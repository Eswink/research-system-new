---
id: MEM-20260929-165
title: "人工白名单要做可派生性复检：权威面选「受门逐字节钉住的快照」，差异必须两向都算（只留一向时「清单陈旧」会静默通过）"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-241-goal-025-ec03-whitelist-contract-derivation.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-242-goal-025-ec03-whitelist-contract-derivation.md
supersedes: []
tags: [whitelist, derivation, openapi-snapshot, two-way-diff, authority-face, goal-025, ec-03]
---

## 做了什么

GOAL-025 cycle 3 把 GOAL-024 的读面白名单（68 条路由逐条人工判定）从「人工判定 + 机械自审」
补上**派生**这一半：从**受门钉住的 OpenAPI 快照**（`docs/api/openapi.m13.json`，64 条 GET）
∪ **框架内建登记**（4 条，逐条带理由）派生读面，与人工清单做**两向**差分；本轮差异 = ∅。

## 为什么这样做（为什么值得记）

- **权威面必须自己受门**：候选里有 `docs/api/CONTROL_PLANE_API.md`（人写的 API 文档）——
  会漂移、**不能**当权威面。选 OpenAPI 快照的理由是可机械复核的：它由
  `tests/contracts/test_openapi_snapshot.py` **重新生成并与提交前字节逐字比对**，
  且同时是前端类型的生成源。**判据的权威性来自别的门，不来自自己的措辞。**
- **差异必须两向都算（实测踩到）**：按压「只留 `派生 − 清单` 一向」后，主判据**照样全绿**，
  只有那条专门断言「清单里多一条 ⇒ 判红」的反证例才红。也就是说：**单向差分时，
  「人工清单陈旧 / 膨胀」这一类缺陷会静默通过**。两向既互不顶替，也必须各有一条判据钉住。
- **快照里没有的那一半要显式登记**：FastAPI 内建文档路由（`/docs` / `/redoc` / `/openapi.json` /
  `/docs/oauth2-redirect`）**不在** OpenAPI schema 里 ⇒ 不登记就变成「派生面与人工清单永远差 4 条」
  的噪声，且**没有任何判据**能区分「框架路由」与「清单漏登记」。
- **三条独立路径互钉比一条强**：提交的快照 × 应用**实时** `app.openapi()` × 运行时路由树；
  实时与快照不一致 ⇒ 判红「快照可能过期」（按压把派生根改错时，这条判据同时判红）。
  快照过期这类问题**只有**拿实时面比才看得见（单看快照什么都发现不了）。
- **非空取证 + 下界**：派生面有 `MIN_DERIVED = 40` 下界，快照读不到 / 变空 ⇒ 判红。
  否则「读不到快照 ⇒ 派生集空 ⇒ 无差异 ⇒ 通过」是一条**空真**绿路（按压实测会退化成
  `快照里的 GET 只有 9 条 < 下界 40`）。
- **登记不能伪造读面**：框架那 4 条是人工维护的，但有「运行时路由树 == 派生面」兜底 ⇒
  把一条**不存在**的路由写进登记会让判据判红（实测按压 P1 就是这条）。

## 怎么做与复现

1. **派生**：读提交的 JSON 快照 ⇒ 取含 `get` 的路径；再并上 `FRAMEWORK_ROUTES`（逐条理由非空、
   上界写死 `== 4`）。读不到 / 结构不符 ⇒ 返回空元组，由**下界**判红（不静默退化）。
2. **差分**：`diff_findings` 同时算 `派生 − 清单` 与 `清单 − 派生`，逐条点名并直接进失败消息。
3. **互钉**：另加两条判据（实时 schema vs 快照、运行时路由树 vs 派生面）。
4. **反证**：判据内三条（多一条 / 少一条 / 快照读不到）+ 真实应用上挂一条新读路由
   （实时 schema 立刻差异并点名）。
5. **按压**：改框架登记（红：`派生面有而清单没有:/__bogus-frame`）、改派生根（红：下界 + 两向长清单）、
   抽掉一向差异（红：只有对应反证例红 ⇒ 证明它承重）；三处 raw `sha256` 逐字节复原。

## 适用边界

- 派生的是**路径集合**，**不是分类**（`declared_content` / `zero_hit` 仍是人工判定 + 机械自审）。
- 权威面只覆盖**应用声明的 GET 路径**：不含 HEAD / OPTIONS，也不证明这些路由**一定返回内容**。
- 框架那一半是**人工登记**；新框架路由需人工同步（但登记不存在者会被运行时树判红）。
- 运行时树的叶子过滤是「`methods` 含 `GET`」⇒ **兼有 GET 与写方法**的路由会被算进读面（本仓无此形态）。
- 权威性**依赖** `test_openapi_snapshot.py` 的重生成门在位；门一放宽，前提失效。
- **不构成**任何"项目安全"结论（`R-M1` 未收口）。

## 来源

- 交付：`tests/observability/read_face_whitelist_derivation.py`（128 行）、
  `tests/observability/test_privacy_read_face_whitelist_derivation.py`（124 行 / 10 例全绿）
- 复检：RECHECK-20260929-242（`PASS_WITH_WARNINGS`；`W-1`/`W-2` 就是本条的边界）
- 前置：MEM-20260928-162（读面白名单的零命中必须配有上界的白名单）、
  MEM-20260928-161（清单必须是带理由的分区）
