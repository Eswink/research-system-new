---
id: PLAN-20260927-205
slug: principal-attribution-cannot-be-forged
title: GOAL-021 cycle 3（EC-03）：主体归因不可伪造——不能自报 + 读面不污染 + 不串（可证伪形态）
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
    承 GOAL-20260927-021 的 **EC-03**（主体归因不可伪造）。授权沿用该 GOAL 的
    `authorization.ref`：**新增对抗性判据 + 修复被证明为真缺陷 + 文档同源**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：给读面（GET/HEAD）加认证、多租户 / organization scope / RBAC、
    BOLA·BFLA 专项实现、**调用方自报身份**（单 token ⇒ 单主体不变）、新增依赖、
    把 token **值**写进任何地方、改认证的 401 响应形态、改 `Idempotency-Key` 语义、
    改任何**既有**判据 / 门禁 / 阈值 / 放行面。
    **本 PLAN 专属边界**：**不得**给 `Principal` 加租户 / 角色字段（M18 面）；
    **不得**改 `test_control_plane_auth_same_source.py` 与
    `tests/api/test_principal_auth.py`（既有主体判据）；**不得**宣称项目安全（`R-M1` 未收口）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260927-206-principal-attribution-cannot-be-forged-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260927-151-testclient-hides-contextvar-bleed.md
---

# PLAN-20260927-205 — 主体归因不可伪造（GOAL-021 EC-03）

## 目标

证明**主体归因不可伪造**，三条各自可判：

- **(a) 不能自报身份**：请求**无法**影响主体身份——带对 token 时主体**恒为配置主体**；
  任何自报输入（`X-Principal-Id` / `X-Actor` 头、query 参数、body 字段）
  **都不改变**主体（单 token ⇒ 单主体不变）。
- **(b) 读面无认证路径的既有行为与基线一致**：认证开启时**读请求**不带 token ⇒ 主体为
  **`None`**（不被前一个写请求污染、也不被猜成某个身份）；认证**关闭**时行为与基线**逐字**一致。
- **(c) 请求之间不串**：**可证伪形态** = **同一任务内的顺序**（带 token 的写请求之后，
  紧接一个不带 token 的读请求 —— 后者必须看不到前者的主体）。

## 验收条件

- [x] **AC-1（自报不可生效）**：带对 token + 各种自报输入 ⇒ 主体**仍是**配置主体；
      逐个输入形态留档（头 / query / body 各至少一种）。
- [x] **AC-2（三态在位）**：认证关闭 ⇒ 放行且主体 `None`；开启 + 无 token ⇒ 401；
      开启 + 对 token ⇒ 放行且主体 = 配置主体。
- [x] **AC-3（读面基线）**：**在前有一个写请求**的情形下，读请求主体仍 `None`。
- [x] **AC-4（顺序形态 · 可判红）**：把 `reset_current_principal` 换成 no-op
      ⇒ 顺序判据**判红**（读请求看到写请求的主体）⇒ **逐字节复原**（sha256）⇒ 绿。
      **先已验证该形态可证伪**（`scratch/goal021-ec03-probe-shape.py`：
      基线 `read actor=None`、no-op 后 `read actor=service:probe-principal`）。
- [x] **AC-5（并发形态作为补充覆盖，且写明前提）**：并发用例在位，但断言**必须**写明
      **前提「父上下文干净」** —— 实测该形态的结果**取决于父任务上下文**
      （干净 ⇒ 0 violations；已污染 ⇒ 20）⇒ **不得**把「并发 0 violations」单独写成
      「并发安全」。**这是本 PLAN 最要紧的诚实约束**。
- [x] **AC-6（主体是标识不是凭据）**：`Principal.actor` 形态为 `<kind>:<id>`，
      **不含**任何凭据成分；且 `Principal` **没有**租户 / 角色字段（M18 面不越界）。
- [x] **AC-7（既有判据零改动）**：`tests/api/test_principal_auth.py` /
      `test_control_plane_auth_same_source.py` / `test_reproducibility_wording.py` /
      `test_record_face_is_covered_by_the_gate.py` 四个文件 `git diff --quiet` 全空。
- [x] **AC-8（规模与收集面）**：新判据 ≤ 450 行、单函数 ≤ 50 行；落 `tests/**`
      ⇒ 不新增 m0 check（终态行仍 23）。
- [x] **AC-9（记录面顺序）**：先写记录 ⇒ 跑记录面判据 ⇒ 再跑全量门。

## 实施清单

- [x] **WP-A（先红）：确认判据真能红** —— 复用并留档
      `scratch/goal021-ec03-probe-shape.py`（**已跑通**）与
      `scratch/goal021-ec03-probe-concurrency-precondition.py`（**已跑通**：
      干净父上下文 0 / 已污染 20）。
- [x] **WP-B（判据）**：新增 `tests/api/test_principal_cannot_be_forged.py`：
      自报无效 + 三态 + 读面基线 + **顺序形态**（唯一可判红）+ 并发（**写明前提**）。
- [x] **WP-C（后绿+复原）：反证 1/1 红** + 逐字节复原 + 定向套件复跑绿。
- [x] **WP-D（记录）**：`RECHECK-20260927-206` + `MEM-20260927-151` + GOAL-021 回写。

## 证据

**交付**：`tests/api/test_principal_cannot_be_forged.py`（**311 行 / 15 例**）。

**最要紧的一条（先红后绿的关键；详见 `RECHECK-20260927-206` 第一节）**：
首版判据用 `TestClient`（同步 portal）⇒ **按压不红（14 passed）** ⇒ 说明该驱动的
**每请求各起任务**特性把「写请求主体残留给下一读请求」这一现象**遮住了** ⇒
判据**不可证伪**（假绿）。改用 **`httpx.ASGITransport` + 同任务 `await`** 后，
同一按压 **4 failed**。⇒ **本 EC 的判据必须用后者**；
`MEM-20260927-151` 记录该失效模式。

**反证（1/1 红，逐字节复原）**：把 `finally: reset_current_principal(token)` 换成 `pass`
⇒ **4 failed**（四条顺序形态判据全红）⇒ `sha256` 复原一致
（`ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`）
+ `git diff` **IDENTICAL TO HEAD** ⇒ 复跑 **15 passed**。

**三条实测**：自报（头 / query / body）**全部无效**，真实 app 带自报头照常 201 但主体不变；
读面无主体且**不被前一个写请求污染**（含连续 5 写、交替 4 轮、被拒写之后）；
顺序形态可判红。**`Principal` 字段集恰为 `{id, kind}`**（M18 边界为机械事实）。

**并发用例**：0 violations —— **已在断言与文档写明前提「父上下文干净」，
并且不作安全结论**（实测：父上下文被污染时同形态得 **20 violations**）。

**既有判据零改动**：四个文件 `git diff --quiet` 全空。**零产品代码改动**。

**本轮修掉的缺陷 = 判据自身 1 处（驱动形态选错）**，**非**产品缺陷。

**as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**
（`PASS [` = **24**、**4606 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c3-m0-v2.log`）
⇒ 新增判据落在既有 `python/tests` 收集面内，**m0 条数仍为 23**。

## 影响报告

- **产品代码**：预期**零改动**（自检）。若判据**证明**主体可被伪造 ⇒ 在 GOAL-021 授权内
  修产品代码并逐条登记（**不得**引入自报身份来「修」它）。
- **Domain / API / schema**：**无变化**（`Principal` 不加字段——M18 面不越界）。
- **安全 / 凭据**：**无放宽**；判据中的 token 为**测试内构造的合成假值**。
- **门禁面**：落 `tests/**` ⇒ 不新增 m0 check。
- **下一项任务**：GOAL-021 的 **EC-04**（前端 token 面不是访问控制）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-27 | IN_PROGRESS | derive（GOAL-021 cycle 3）：圈定 EC-03「主体归因不可伪造」。**设计期已实测判据形态**（两个 scratch 探针）：**顺序形态可判红**（基线读 `None`、no-op reset 后读看到写请求主体）；**并发形态结果取决于父任务上下文**（干净 `0 violations` / 已污染 `20 violations`）⇒ 并发**只能作补充覆盖且必须写明前提**；**自报不可生效**（`X-Principal-Id` / `X-Actor` / query / body 字段全部无效，请求照常 201）。 |
