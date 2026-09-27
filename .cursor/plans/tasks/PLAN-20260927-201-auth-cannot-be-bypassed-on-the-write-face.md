---
id: PLAN-20260927-201
slug: auth-cannot-be-bypassed-on-the-write-face
title: GOAL-021 cycle 1（EC-01）：认证不可绕过——枚举来自代码 + 豁免不继承 + 顺序钉住 + 读面按设计放行
status: IN_PROGRESS
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
latest_recheck: null
memory_entries: [无可复用事实（本 PLAN 的判据设计事实由 RECHECK 承载；收口时对齐）]
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

- [ ] **AC-1（枚举来自代码 · 可复核）**：新判据内**调用 `create_app()`** 并遍历其
      OpenAPI / 路由表取得 mutating 端点集合——**不得**出现手写的端点列表或手写计数
      （审查判据源码可据此取反证：把某个端点从保护面移出后，判据**不必改**就能发现）。
- [ ] **AC-2（行为全覆盖 · 先红后绿）**：认证开启 + 枚举出的**每一个** mutating 端点
      发无 token 请求 ⇒ **全部 401**；实测计数 **60**（建档期两口径互证）写入判据断言。
      **按压见 AC-5**。
- [ ] **AC-3（豁免不被继承 · 结构 + 行为成对）**：**结构**面复用既有 AC-4 的结论
      （**不改该文件**，在 RECHECK 里引其证据）；**行为**面新增：分析类端点
      （`POST /protocol-drafts/validate`、`POST /projects/{id}/validate` /
      `compile` / `preflight` / `dry-run`，以及 model 的 `test` / `probe` /
      `discover-models`）在认证开启、无 token 时 **401**。
      ⇒ 证明「**幂等面放行 ⟹ 认证面放行**」这一推理为**假**。
- [ ] **AC-4（读面与探活按设计放行 · 显式断言）**：`GET /health` 与若干普通 GET 在
      认证**开启**、不带 token 时放行（2xx），且判据**显式断言「这是设计」**——
      绑定 `_MUTATING_METHODS` 这个**符号**（读面不放行只可能因为分类被改），
      而不是「碰巧返回 200」。
- [ ] **AC-5（按压矩阵 · 逐轮报实际判红集合）**：至少两种按压各让判据**判红**，
      **已实测可证伪**（建档期探针 `scratch/goal021-ec01-probe-press-shape.py`）：
      **按压①** 把 `DELETE` 移出 `_MUTATING_METHODS` ⇒ DELETE 端点得 **404**（非 401）
      ⇒ AC-2 判红；**按压②** 让认证面对分析类 POST 放行 ⇒ 该端点得 **422**（非 401）
      ⇒ AC-3 判红。**逐字节复原**（sha256）⇒ 复跑绿。按压打偏（探针自身写错导致没红）
      **记为失败**。
- [ ] **AC-6（既有判据零改动）**：`git diff` 取证
      `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` /
      `test_record_face_is_covered_by_the_gate.py` / `test_security_scan.py`
      **四个文件零改动**。
- [ ] **AC-7（规模与收集面）**：新判据文件 **≤ 450 行**（> 450 硬失败）、单函数 **≤ 50 行**；
      放在 `tests/**` ⇒ 属既有 `python/tests` 收集面 ⇒ **不新增 m0 check**
      （终态行仍 `PASS: profile=m0; 23 deterministic checks`）。
- [ ] **AC-8（凭据纪律）**：判据中的 token 一律为**测试内构造的合成假值**；
      全仓 token **值**零命中（只允许**变量名**）；`credential_audit.py` 四面 `offenders=0`。
- [ ] **AC-9（记录面顺序）**：按 MEM-145 —— 先写记录（本 PLAN + RECHECK + MEM + GOAL 回写）
      ⇒ 跑记录面判据 ⇒ 再跑完整 `make validate-all`（独占、`uv run`、`--keep-going`）；
      **门禁结论覆盖记录面**。

## 实施清单

- [ ] **WP-A（先红）：确认判据真能红** —— 复用并留档
      `scratch/goal021-ec01-probe-press-shape.py`（**已跑通**：按压①⇒404、按压②⇒422、
      基线 401、复原 401）⇒ 证明本 EC 的两个按压**可证伪**。
- [ ] **WP-B（判据）**：新增 `tests/api/test_write_face_cannot_be_bypassed.py`：
      (a) 枚举来自代码 + 逐个 401；(b) 分析类端点无 token 401；(d) 读面 / 探活按设计放行
      （显式绑定 `_MUTATING_METHODS` 符号）。**不复制**既有 AC-4 / AC-5 的断言。
- [ ] **WP-C（后绿+复原）：按压 2/2** + 逐字节复原 + 报**实际判红集合**；
      定向套件（新增判据 + 既有认证判据）复跑绿。
- [ ] **WP-D（记录）**：`RECHECK-20260927-202` + `MEM-20260927-149` + GOAL-021 回写
      （EC-01 → PASS、迭代日志、child_plans、状态历史）。

## 证据

- （待填：按压矩阵、定向套件输出、m0 终态行、CI run）

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
