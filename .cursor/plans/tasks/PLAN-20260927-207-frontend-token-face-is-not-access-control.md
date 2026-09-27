---
id: PLAN-20260927-207
slug: frontend-token-face-is-not-access-control
title: GOAL-021 cycle 4（EC-04）：前端 token 面不是访问控制——仅内存（结构）+ 后端独立成立（行为）+ 两处文档同源
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
    承 GOAL-20260927-021 的 **EC-04**（前端 token 面不是访问控制）。授权沿用该 GOAL 的
    `authorization.ref`：**新增对抗性判据 + 修复被证明为真缺陷 + 文档同源**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：给读面（GET/HEAD）加认证、多租户 / organization scope / RBAC、
    BOLA·BFLA 专项实现、调用方自报身份、新增依赖、把 token **值**写进任何地方、
    改认证的 401 响应形态、改 `Idempotency-Key` 语义、改任何**既有**判据 / 门禁 / 阈值 / 放行面。
    **本 PLAN 专属边界**：**不得**改 `tests/api/test_security_scan.py`（前端持久层的
    无条件字面量断言）与 `apps/web/tests/unit/control-plane-token.test.ts`（既有前端判据）；
    **不得**给前端加持久化（localStorage / sessionStorage / cookie / URL）；
    **不得**把「前端能输入 token」写成访问控制或安全结论（`R-M1` 未收口）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260927-208-frontend-token-is-not-access-control-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-147-frontend-credential-storage-and-app-path-driving.md
---

# PLAN-20260927-207 — 前端 token 面不是访问控制（GOAL-021 EC-04）

## 目标

证明**前端 token 面是便利面、不是访问控制**，两条各自可判：

- **(a) 仅内存**：`apps/web/src` 的 token 存储**零**浏览器持久层写入（结构判据）；
  **刷新即失**是**已记录的代价**（GOAL-020 的三选一决策，理由见 `MEM-20260926-147`）。
- **(b) 后端独立成立**：**绕过前端**、直接用 HTTP 调 API ⇒ 带 token 成功 / 不带 token **401**
  ——结论**与前端是否存在无关**（后端不依赖任何前端状态）。

**文档同源**：在 `docs/security/IDENTITY_AND_ACCESS.md` 与 `docs/security/THREAT_MODEL.md`
写明「**前端 token 面是便利面，不是访问控制**」，且**不得**触发既有的肯定式安全断言词表。

## 验收条件

- [x] **AC-1（仅内存 · 结构判据）**：`apps/web/src/**` **零**浏览器持久层写入调用
      （既有 `test_security_scan.py` 已覆盖 ⇒ **引用不重复**）；
      **新增**一条判据：token 模块**不导出**任何持久化通道
      （即它只暴露 set / clear / 存在性 / 头值，**没有**读写浏览器存储的入口）。
- [x] **AC-2（后端独立成立 · 行为判据）**：**不经前端**直接调 API：带对 token ⇒ 写操作成功；
      不带 token ⇒ **401**。⇒ 权限判定**完全在后端**，前端状态不参与。
- [x] **AC-3（前端不是判定点 · 结构判据）**：前端代码里**没有**任何「依据 token 存在与否
      决定是否允许某操作」的授权逻辑——token 只影响**是否附上请求头**；
      请求被拒时前端**如实呈现**（把 401 反映给用户），**不**静默降级、**不**伪装成功。
- [x] **AC-4（文档同源）**：两处安全文档各含「前端 token 面**不是**访问控制」的同源表述；
      且**未**触发 `test_control_plane_auth_same_source.py` 的 `_FORBIDDEN_PHRASES`
      （即**不得**被写成更强结论）；同源声明句与各文档未覆盖锚点**仍恰好一次**。
- [x] **AC-5（反证 · 先红后绿）**：给前端 token 存储**临时接上**一个浏览器持久层写入
      ⇒ 结构判据**判红** ⇒ **逐字节复原**（sha256）⇒ 绿。**按压打偏记为失败**。
- [x] **AC-6（既有判据零改动）**：`tests/api/test_security_scan.py` /
      `apps/web/tests/unit/control-plane-token.test.ts` /
      `test_control_plane_auth_same_source.py` 三个文件 `git diff --quiet` 全空。
- [x] **AC-7（规模与收集面）**：新判据 ≤ 450 行、单函数 ≤ 50 行；**web 门**（lint / typecheck /
      unit / build / stub e2e / live e2e）逐条实跑；设计基线若漂移按既有流程重生成 + 目检。
- [x] **AC-8（记录面顺序）**：先写记录 ⇒ 跑记录面判据 ⇒ 再跑全量门。

## 实施清单

- [x] **WP-A（先红）：确认结构判据真能红** —— 临时给 `controlPlaneToken.ts` 接一个
      持久层写入 ⇒ 既有 `test_security_scan.py` 判红（证明其字面量断言**对新增写入有效**）
      ⇒ 复原。
- [x] **WP-B（判据 + 文档）**：新增前端结构判据（token 模块无持久化通道）
      + 后端行为判据（绕过前端直调 API）+ 两处安全文档补「便利面不是访问控制」。
- [x] **WP-C（后绿+复原）**：反证 1/1 红 + 逐字节复原 + web 门 + 定向套件复跑绿。
- [x] **WP-D（记录）**：`RECHECK-20260927-208` + GOAL-021 回写（EC-04 → PASS）。

## 证据

**交付**：`tests/api/test_frontend_token_is_not_access_control.py`（**163 行 / 6 例**）
+ 两处安全文档同源登记。

**判定点只在后端**：绕过前端直调 API ⇒ 无 token **401** / 有 token **201**
（同一请求，差别只在请求头）；中间件源码**不含** `localStorage` / `apps/web` / `window.` /
`document.` 等前端概念（且含 `RESEARCHOS_CONTROL_PLANE_TOKEN` ⇒ 确实读到源码）；
被拒的写请求**不改动 canonical**（项目数不变）。

**仅内存且单一持有**：token 模块**代码**剥注释后零持久化命中（`localStorage` /
`sessionStorage` / `indexedDB` / `document.cookie` / `window.name`），
含**两条反向对照**（源码含注释决策说明、剥注释后不含、`subscribeControlPlaneToken` 在代码里）；
`apps/web/src` 里**没有别处**保存 token 值。

**反证（1/1 红，逐字节复原；含一次按压打偏的如实登记）**：
临时给 `setControlPlaneToken` 加 `window.localStorage.setItem(...)` ⇒
**既有** `test_security_scan.py` **1 failed**（其字面量断言有效）；
**首版本 EC 判据 6 passed（未红）** ⇒ 首版只断言**导出函数名**、**不绑定行为** ⇒
**不可证伪** ⇒ **按纪律记为「按压打偏」并修正**（改为剥注释后扫代码）；
修正后同一按压 ⇒ **本 EC 判据 1 failed**。
复原后 `sha256` 一致（`32d7c4fc5e76b8d72c4a4b18e6713227b90564ab7b2b036ffbc40910595a6f44`）
+ `git diff` **IDENTICAL TO HEAD** ⇒ 复跑 **12 passed**。

**文档同源**：`IDENTITY_AND_ACCESS.md` 未覆盖范围新增**第 8 条**；
`THREAT_MODEL.md` §6.3 第 3 条追加**实况更新**；既有同源判据 + 话术判据 + 安全扫描
⇒ **22 passed**；**未触发** `_FORBIDDEN_PHRASES`；同源句与未覆盖锚点**仍恰好一次**。

**既有判据零改动**：`test_security_scan.py` / `control-plane-token.test.ts` /
`test_control_plane_auth_same_source.py` 三个文件 `git diff --quiet` **全空**。

**web 门**：`lint` 通过（`--max-warnings 0` 无输出）；`typecheck` 通过；
unit **94 passed / 0 failed**。**零产品代码改动**。

**本轮修掉的缺陷 = 判据自身 1 处（断言不绑定行为）**，**非**产品缺陷。

**as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**
（`PASS [` = **24**、**4613 passed / 21 skipped**、零 `FAILED`/`ERROR`；日志 `scratch/goal021-c4-m0.log`）
⇒ 新增判据落在既有 `python/tests` 收集面内，**m0 条数仍为 23**。

## 影响报告

- **产品代码**：预期**零改动**（自检 + 文档）。若判据**证明**前端真的构成访问控制
  （例如前端里存在授权判定点）⇒ 在 GOAL-021 授权内修**前端**并逐条登记。
- **Domain / API / schema**：**无变化**。
- **安全 / 凭据**：**无放宽**；**不得**给前端加持久化；判据中的 token 为**合成假值**。
- **门禁面**：落 `tests/**` 与 `apps/web/tests/**` ⇒ 属既有收集面 ⇒ 不新增 m0 check。
- **下一项任务**：GOAL-021 的 **EC-05**（收口复检 + 残余登记）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-27 | IN_PROGRESS | derive（GOAL-021 cycle 4）：圈定 EC-04「前端 token 面不是访问控制」。**建档期已核实的起点**：既有 `apps/web/tests/unit/control-plane-token.test.ts` 已覆盖「写请求携带 / 读请求不携带 / 关闭态不加空头 / 持久化面零命中」；`docs/security/THREAT_MODEL.md` §6.3 第 3 条已写明「`apps/web` 的按钮可见性 / 路由可见性**不是**访问控制」。⇒ **本轮的增量** = **后端独立成立的行为判据**（绕过前端直调 API）+ **token 模块无持久化通道**的结构判据 + **`IDENTITY_AND_ACCESS.md` 补同源表述**（该处尚无此句）。 |
