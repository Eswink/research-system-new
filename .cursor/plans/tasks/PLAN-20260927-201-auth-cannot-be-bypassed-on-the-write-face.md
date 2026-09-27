---
id: PLAN-20260927-201
slug: auth-cannot-be-bypassed-on-the-write-face
title: GOAL-021 cycle 1（EC-01）：认证不可绕过——枚举来自代码 + 豁免不继承 + 顺序钉住 + 读面按设计放行
status: DONE
created_at: 2026-09-27
updated_at: 2026-09-27
parent_goal: GOAL-20260927-021
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260927-021 的 **EC-01**（认证不可绕过）。授权沿用该 GOAL 的
    `authorization.ref`：**新增对抗性判据 + 修复被证明为真缺陷 + 文档同源**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：给读面（GET/HEAD）加认证、多租户 / organization scope / RBAC、
    BOLA·BFLA 专项实现、调用方自报身份、新增依赖、把 token **值**写进任何地方
    （含**判据源码**——一律用测试内构造的合成假值）、改认证的 401 响应形态、
    改 `Idempotency-Key` 语义、改任何**既有**判据 / 门禁 / 阈值 / 放行面。
    **本 PLAN 专属边界**：**不得**改 `test_control_plane_auth_same_source.py`
    （既有同源判据；AC-4 / AC-5 已覆盖本 EC 的 (b) 结构与 (c) 顺序面 ⇒ 本 PLAN 的新判据
    只补**它没覆盖的**面，**不**重复、**不**顶替）；**不得**宣称项目安全（`R-M1` 未收口）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260927-202-auth-cannot-be-bypassed-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260927-149-enumeration-must-come-from-code-and-be-pressable.md
---

# PLAN-20260927-201 — 认证不可绕过（GOAL-021 EC-01）

## 目标

证明**写面认证不可绕过**，四条各自可判，并把结论固化为**受门禁保护的判据**：

- **(a) 枚举来自代码**：从**构建出的 app**机械枚举全部 mutating 端点（**不是**手写清单），
  在认证开启下逐个发无 token 请求 ⇒ **一律 401**。
- **(b) 豁免面不被继承**：`_ANALYSIS_ACTIONS` 是**幂等**面的例外集，**不是**认证面的豁免
  ⇒ 结构证明（AST 不引用）+ **行为**证明（分析类端点无 token 也 401）。
- **(c) 顺序被钉住**：`PrincipalAuthMiddleware` 注册在 `IdempotencyMiddleware` **之后**
  （后注册者在外层）。
- **(d) 读面与探活按设计放行**：GET/HEAD 与 `/health` 在认证开启、不带 token 时放行，
  **且该设计被显式断言**（不是碰巧）。

**与既有判据的分工（避免重复与顶替）**：`test_control_plane_auth_same_source.py` 的
AC-4 已断言「认证面复用 `_MUTATING_METHODS`」与「不引用 `_ANALYSIS_ACTIONS`」（**结构**面）、
AC-5 已断言注册顺序 ⇒ 本 PLAN 的判据**不重复**这些断言，而是补：
**(a) 的枚举 + 行为全覆盖**（既有判据没有这一条）、**(b) 的行为面**（既有只有结构面）、
**(d) 的「放行是设计」显式断言**。⇒ 四个面**合起来**才是完整交付，**各自**不宣称覆盖全部。

## 验收条件

- [x] **AC-1（枚举来自代码 · 可复核）**：新判据内**调用 `create_app()`** 并遍历其
      OpenAPI / 路由表取得 mutating 端点集合——**不得**出现手写的端点列表或手写计数
      （审查判据源码可据此取反证：把某个端点从保护面移出后，判据**不必改**就能发现）。
- [x] **AC-2（行为全覆盖 · 先红后绿）**：认证开启 + 枚举出的**每一个** mutating 端点
      发无 token 请求 ⇒ **全部 401**；实测计数 **60**（建档期两口径互证）写入判据断言。
      **按压见 AC-5**。
- [x] **AC-3（豁免不被继承 · 结构 + 行为成对）**：**结构**面复用既有 AC-4 的结论
      （**不改该文件**，在 RECHECK 里引其证据）；**行为**面新增：分析类端点
      （`POST /protocol-drafts/validate`、`POST /projects/{id}/validate` /
      `compile` / `preflight` / `dry-run`，以及 model 的 `test` / `probe` /
      `discover-models`）在认证开启、无 token 时 **401**。
      ⇒ 证明「**幂等面放行 ⟹ 认证面放行**」这一推理为**假**。
- [x] **AC-4（读面与探活按设计放行 · 显式断言）**：`GET /health` 与若干普通 GET 在
      认证**开启**、不带 token 时放行（2xx），且判据**显式断言「这是设计」**——
      绑定 `_MUTATING_METHODS` 这个**符号**（读面不放行只可能因为分类被改），
      而不是「碰巧返回 200」。
- [x] **AC-5（按压矩阵 · 逐轮报实际判红集合）**：至少两种按压各让判据**判红**，
      **已实测可证伪**（建档期探针 `scratch/goal021-ec01-probe-press-shape.py`）：
      **按压①** 把 `DELETE` 移出 `_MUTATING_METHODS` ⇒ DELETE 端点得 **404**（非 401）
      ⇒ AC-2 判红；**按压②** 让认证面对分析类 POST 放行 ⇒ 该端点得 **422**（非 401）
      ⇒ AC-3 判红。**逐字节复原**（sha256）⇒ 复跑绿。按压打偏（探针自身写错导致没红）
      **记为失败**。
- [x] **AC-6（既有判据零改动）**：`git diff` 取证
      `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` /
      `test_record_face_is_covered_by_the_gate.py` / `test_security_scan.py`
      **四个文件零改动**。
- [x] **AC-7（规模与收集面）**：新判据文件 **≤ 450 行**（> 450 硬失败）、单函数 **≤ 50 行**；
      放在 `tests/**` ⇒ 属既有 `python/tests` 收集面 ⇒ **不新增 m0 check**
      （终态行仍 `PASS: profile=m0; 23 deterministic checks`）。
- [x] **AC-8（凭据纪律）**：判据中的 token 一律为**测试内构造的合成假值**；
      全仓 token **值**零命中（只允许**变量名**）；`credential_audit.py` 四面 `offenders=0`。
- [x] **AC-9（记录面顺序）**：按 MEM-145 —— 先写记录（本 PLAN + RECHECK + MEM + GOAL 回写）
      ⇒ 跑记录面判据 ⇒ 再跑完整 `make validate-all`（独占、`uv run`、`--keep-going`）；
      **门禁结论覆盖记录面**。

## 实施清单

- [x] **WP-A（先红）：确认判据真能红** —— `scratch/goal021-ec01-probe-press-shape.py`
      （**已跑通**：按压①⇒404、按压②⇒422、基线 401、复原 401）⇒ 证明本 EC 的按压
      **可证伪**。另 `scratch/goal021-ec01-probe-enumeration.py` 取证**枚举两口径一致**
      （AST 装饰器 = OpenAPI paths = **60**，覆盖 **17** 个 router 文件）。
- [x] **WP-B（判据）**：新增 `tests/api/test_write_face_cannot_be_bypassed.py`
      （**285 行 / 18 例**，零超长函数）：(a) 枚举来自代码 + 逐个 401（缺 token / 错 token
      各一轮）；(b) 分析类端点无 token 401（8 条参数化）+ 带对 token 的**配对对照**；
      (d) 读面 / 探活按设计放行（含「**写面路径上的 GET** 不被挑战」这条最锋利形态）。
      **不复制**既有 AC-4 / AC-5 的断言——它们的结构面与顺序面在
      `test_control_plane_auth_same_source.py` 里，本文件**引用**而不**顶替**。
- [x] **WP-C（后绿+复原）：按压 3/3 符合预期** + 逐字节复原 + **报实际判红集合**；
      定向套件（新增判据 + 既有认证判据 + 安全扫描）复跑 **53 passed**。
      **PRESS-3 在判据最终版（285 行）上复跑，红集合逐条相同（10 failed）**。
- [x] **WP-D（记录）**：`RECHECK-20260927-202` + `MEM-20260927-149` + GOAL-021 回写
      （EC-01 → PASS、迭代日志、child_plans、状态历史）。

## 证据

**本轮被全量门抓到并修掉的一处真红（`python/typecheck`）**：`TestClient.app` 的静态类型是
ASGI callable（**不是** `FastAPI`）⇒ 直接 `.openapi()` / `.state` 被 mypy 判错 **7 处**。
**修法**：收敛一处 `_app_of(client) -> FastAPI`（内部按本仓既有约定
`cast(FastAPI, cast(Any, client.app))`，同 `test_memory_api.py`），而**不是**散落 7 个
`cast` 或加 `# type: ignore` 抑制。修后定向 `mypy` **Success: no issues found**、
`ruff check` / `ruff format --check` 全过、判据 **18 passed**。
**⇒ 教训（与 GOAL-020 cycle 1 同形）**：**定向套件绿 ≠ 全量门绿**——本轮的
`python/typecheck` 只有全量门会跑到。

**按压矩阵（3/3 红，每轮报实际判红集合；全部逐字节复原，sha256
`ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`）**：

| 按压 | 改了什么 | 期望 | **实际判红集合** |
| --- | --- | --- | --- |
| **PRESS-1** | `_MUTATING_METHODS` 去掉 `DELETE` | 枚举行为面红 | **3 failed**：`test_every_mutating_endpoint_rejects_a_missing_token` / `..._a_wrong_token` / `test_the_protected_set_is_exactly_the_mutating_classification` |
| **PRESS-2** | `_MUTATING_METHODS` 加入 `GET` | 读面设计面红 | **4 failed**：`test_the_protected_set_is_exactly_...` / `test_health_and_read_endpoints_are_reachable_without_a_token` / `test_the_read_face_is_open_because_it_is_not_in_the_write_classification` / `test_a_read_request_is_never_challenged_even_on_a_mutating_route` |
| **PRESS-3** | 让认证面继承 `_is_analysis_post` 豁免 | 豁免行为面红 | **10 failed**：2 条枚举行为面 + **8 条** `test_analysis_endpoints_still_require_a_token[...]`（8 个分析类路径**逐个**红）；**在判据最终版上复跑，红集合逐条相同** |

- **复原复核**：三轮按压后 `sha256(middleware.py)` 与按压前**逐字相同**，
  `git diff --quiet services/api/middleware.py` ⇒ **IDENTICAL TO HEAD**。
- **终态定向套件**：`tests/api/test_write_face_cannot_be_bypassed.py` +
  `tests/api/test_principal_auth.py` + `tests/architecture/python/test_control_plane_auth_same_source.py`
  + `tests/api/test_security_scan.py` ⇒ **53 passed**（零失败）。
- **判据规模**：285 行（≤ 450 硬上限）、无 > 40 行的函数、`ruff check` + `ruff format --check`
  + `mypy` 全过。
- **零产品代码改动**：本 PLAN 的判据**未证明**任何缺陷 ⇒ 无产品缺陷可修；
  `git diff services/api/middleware.py` 为空（三轮按压已复原）。
- **as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**
  （`PASS [` = **24**、**4577 passed / 21 skipped**、零 `FAILED`/`ERROR`；
  日志 `scratch/goal021-c1-m0-final.log`）。首跑 `python/typecheck` 判红（见上），
  修复后复跑全绿 ⇒ **新增判据落在既有 `python/tests` 收集面内，m0 条数仍为 23**。

## 影响报告

- **产品代码**：本 PLAN **预期零产品代码改动**（自检 = 新增判据）。**例外**：若判据**证明**
  某边界**不成立**（真缺陷）⇒ 在 GOAL-021 授权范围内**修产品代码**，并在此逐条登记
  「判据证明了什么 / 修了什么 / 如何复验」。
- **Domain / API / schema**：**无变化**（不新增端点、不改 DTO、不动 OpenAPI 快照）。
- **安全 / 凭据**：**无放宽**——不改读面放行语义、不改 401 形态、不改
  `Idempotency-Key` 语义、不改任何既有判据 / 门禁 / 阈值；判据中的 token 为
  **测试内构造的合成假值**（**不**引入真实凭据、不落盘、不进日志）。
- **兼容性 / 迁移风险**：**无**（只新增测试与记录；不触碰 Canonical State 与迁移）。
- **上游版本影响**：**无**（零依赖改动）。
- **门禁面**：新增判据落在 `tests/**` ⇒ 属既有 `python/tests` 收集面 ⇒
  **不新增 m0 check**，终态行仍为 `PASS: profile=m0; 23 deterministic checks`。
- **下一项任务**：GOAL-021 的 **EC-02**（token 不泄漏：日志 / 遥测 / 响应 / 事件 /
  前端持久层 / 记录面）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-27 | IN_PROGRESS | derive（GOAL-021 cycle 1）：圈定 EC-01「认证不可绕过」。**设计期已实测两处可证伪性**：①枚举口径两路一致（AST 装饰器 = OpenAPI paths = **60**，覆盖 17 个 router 文件）；②两个按压形态**真的会红**（按压①删 `DELETE` ⇒ 404；按压②继承豁免 ⇒ 422；基线 401、复原 401）⇒ EC-01 的按压条款**可证伪**，不是空话。 |
