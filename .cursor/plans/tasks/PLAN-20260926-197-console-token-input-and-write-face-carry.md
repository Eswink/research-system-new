---
id: PLAN-20260926-197
slug: console-token-input-and-write-face-carry
title: GOAL-020 cycle 2（EC-01）：前端 token 输入与携带（三态实跑 + 成对反证 + 存储决策）
status: DONE
created_at: 2026-09-26
updated_at: 2026-09-26
parent_goal: GOAL-20260926-020
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: >-
    承 GOAL-20260926-020 的 **EC-01**（前端 token 输入与携带）。授权沿用该 GOAL 的
    `authorization.ref`：**前端 token 输入与携带**、**记录面门禁覆盖**、**认证运维面**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：读面认证（GET/HEAD）、多租户 / organization scope / RBAC / 对象级授权
    （BOLA/BFLA）、调用方自报身份、新增依赖、把 token **值**写进任何地方、改认证的 401
    响应形态、改 `Idempotency-Key` 语义。
    **本 PLAN 专属边界**：①**存储方式**——`tests/api/test_security_scan.py` 对
    `apps/web/src/**` **无条件**断言无 `localStorage.setItem` / `sessionStorage.setItem`
    字面量，且**不得**用「惰性访问器」绕过它（该判据的意图是「前端持久层无 secret 写入」）
    ⇒ **选内存**，理由与代价落记录；②**不改**该判据、**不改** `test_control_plane_auth_same_source.py`；
    ③**不改** m0 条数；④**不加依赖**（前端只用现有栈 + 浏览器内置 API）；
    ⑤**不宣称项目安全**（`R-M1` 未收口）；⑥前端输入面**不是**访问控制。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-198-console-token-three-states-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-147-frontend-credential-storage-and-app-path-driving.md
---

# PLAN-20260926-197 — 前端 token 输入与携带（EC-01）

## 目标

让前端**能输入并携带**控制面写面 token：认证**开启**时浏览器侧写操作**可用**、
**关闭**时前端行为**逐字不变**；**存储方式与理由落记录**；**token 值不进任何持久面**。

## 验收条件

- [x] **AC-1（三态实跑）**：**(甲)** 认证关闭 ⇒ 前端行为与**基线一致**；
      **(乙)** 认证开启 + 前端**无** token ⇒ 前端**如实呈现「需要认证」**（非空白 / 非崩溃）；
      **(丙)** 认证开启 + 前端**有** token ⇒ 写操作**成功**。
- [x] **AC-2（成对反证）**：**去掉请求头的 token 注入** ⇒ 开启态的写操作**失败**、
      对应判据**判红**；逐字节复原 ⇒ 绿。
- [x] **AC-3（存储决策）**：`localStorage` / `sessionStorage` / **内存** 三选一，
      **写明 XSS 面、刷新即失的代价、为什么选它** ⇒ 落 RECHECK / MEM。
- [x] **AC-4（凭据纪律）**：token **值**不出现在任何 tracked 文件 / 记录 / 日志 / 遥测 /
      测试输出 / **前端可持久化存储**里 ⇒ **grep 反证**（只允许**变量名 / 字段名**出现）；
      并证明 `tests/api/test_security_scan.py` 的两条持久层断言**仍绿且零改动**。
- [x] **AC-5（关闭态逐字不变）**：认证关闭时，请求头集合与基线一致
      （**不加**空 `Authorization`）、既有 web 六门（lint / typecheck / unit / build /
      stub e2e / live e2e）全绿。
- [x] **AC-6（设计基线）**：若 `design-outlines.json` / 像素基线漂移 ⇒ 按既有流程
      **重生成 + 目检**，**不调容差**。

## 实施清单

- [x] **WP-A（token 面）**：`apps/web/src/api/controlPlaneToken.ts` —— **内存**存储
      （模块级变量 + 订阅），导出 get/set/clear/subscribe；**不碰** `localStorage` /
      `sessionStorage` / cookie / URL / `window.name`；**不提供**读取后的回显。
      单测覆盖：设 / 清 / 订阅 / 空值与空白串归一。
- [x] **WP-B（携带）**：`apps/web/src/api/http.ts` 的 `buildHeaders` —— **仅对**写请求
      （`POST` / `PATCH` / `PUT` / `DELETE`，与后端同一分类语义）注入
      `Authorization: Bearer <token>`；**无 token 时不加该头**（关闭态逐字不变）。
      单测：写请求带 / 读请求不带 / 无 token 时写请求也不带头。
- [x] **WP-C（输入面）**：设置页新增「控制面连接」分区（`ConnectionSection`）+
      i18n（zh/en）+ `pageSupport` 的 `disabledOperations` 据实调整；
      **401 如实呈现**：把 401 映射为「需要认证 / 请在此填入控制面 token」的可读文案
      （**不改**后端 401 形态，只在前端适配）。
- [x] **WP-D（三态实跑 + 成对反证）**：live e2e 新增一条 spec（走 `live-specs.ts`
      单一来源），用**运行环境变量**开启认证并设 token（**token 值只来自 env，不落文件**），
      跑三态；成对反证用**临时移除注入**的方式按压（逐字节复原）。
- [x] **WP-E（记录）**：RECHECK + MEM（存储决策三要素）+ GOAL 回写。

## 证据

- 三态实跑：关闭态对照 / 开启态无 token 的界面文案 + 非崩溃 / 开启态有 token 的 2xx。
- 成对反证：移除注入 ⇒ 失败 + 判据红；复原 ⇒ 绿（sha256）。
- 存储决策：三选一的理由（XSS 面 / 刷新即失的代价 / 为什么选它）。
- 凭据纪律：grep 反证（值零命中）+ `test_security_scan.py` 零改动且绿。
- web 六门 + m0 23/23 + 治理绿。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | IN_PROGRESS | 建档（GOAL-020 cycle 2 = EC-01）。已实测定位单一注入点（`http.ts` 的 `buildHeaders`/`send`，60 处写请求全覆盖；两处 GET 例外不需 token）与存储约束（`test_security_scan.py:79-91` ⇒ 内存）。 |

## 影响报告

- **Domain/API/schema 变化**：**无**（不动 DTO / 路由 / 快照；只加请求头）。
- **安全/凭据变化**：**有**——新增一个前端内存态凭据面。**边界**：不落盘、不进日志 /
  遥测 / 记录；**不是**访问控制（`THREAT_MODEL.md` §6.3 第 3 条）；**不宣称**项目安全。
- **兼容性/迁移风险**：低——无 token 时行为与基线一致（AC-5 显式对照）。
- **上游版本影响**：**无**（零依赖改动）。
- **下一项任务**：GOAL-020 cycle 3 = **EC-03**（认证运维面文档）。
