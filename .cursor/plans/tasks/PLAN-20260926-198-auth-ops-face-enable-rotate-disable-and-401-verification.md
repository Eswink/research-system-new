---
id: PLAN-20260926-198
slug: auth-ops-face-enable-rotate-disable-and-401-verification
title: GOAL-020 cycle 3（EC-03）：认证运维面（开启/轮换/关闭 + 验证 401 + 部署面终态）
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
    承 GOAL-20260926-020 的 **EC-03**（认证运维面）。授权沿用该 GOAL 的 `authorization.ref`：
    **前端 token 输入与携带**、**记录面门禁覆盖**、**认证运维面**三条；push-to-main-for-CI 口径
    （**只推 main、不 force、不重写历史、不推旁支**）；默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：读面认证（GET/HEAD）、多租户 / organization scope / RBAC / 对象级授权
    （BOLA/BFLA）、调用方自报身份、新增依赖、把 token **值**写进任何地方、改认证的 401
    响应形态、改 `Idempotency-Key` 语义。
    **本 PLAN 专属边界**：**不得**放宽 `tests/architecture/python/test_control_plane_auth_same_source.py`
    的同源句 / 未覆盖锚点 / 必需措辞 / `_FORBIDDEN_PHRASES` / AST 断言；
    **不得**改 `test_runbook_same_source.py` 的 `## 1.`…`## 5.` 固定节名（新增内容只走 `###`）；
    **不得**宣称项目安全；**不得**把前端输入面或本节写成访问控制。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-199-auth-ops-face-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260926-148-auth-ops-face-401-verification-and-deployment-checks.md
---

# PLAN-20260926-198 — 认证运维面（EC-03）

## 目标

把「**怎么开 / 怎么轮换 / 怎么关 / 怎么验证 401 / 部署要注意什么**」写成**可照抄、
可复核**的运维面，并**收口** GOAL-019 登记的「deployment face unverified」残余
（`W-12`）——要么给出可复核的验证步骤与结论，要么如实登记「为什么在本机不可验证」。

## 验收条件

- [x] **AC-1（五个面各自在位）**：三处文档（`IDENTITY_AND_ACCESS.md` / `LIVE_MODEL_RUNBOOK.md` /
      `CONTROL_PLANE_API.md`）补齐**开启 / 轮换 / 关闭 / 验证 401 / 部署面**五个面，
      **不是互相顶替**（每处都要能独立查到该走哪一步）。
- [x] **AC-2（401 验证可复核）**：给出**四步命令 + 判词读法**，且有**实测记录**
      （关闭态与开启态的真实状态码），使「401 是否正常」不靠感觉判断。
- [x] **AC-3（部署面终态）**：给出**检查项**并**如实登记本机不可验证的部分**
      （反代 / TLS / 多副本），**不得**产生验证结论、**不得**宣称部署面已覆盖。
- [x] **AC-4（既有判据零改动且绿）**：`test_control_plane_auth_same_source.py`（11 例）
      与 `test_runbook_same_source.py`（10 例）**全绿**且**零改动**；
      四份文档的 canonical 同源句**各恰好一次**。
- [x] **AC-5（零夸大）**：新写入的文字不命中 `_FORBIDDEN_PHRASES` 的肯定语境；
      `## 1.`…`## 5.` 节名未改名 / 未改号（新内容只走 `###`）。

## 实施清单

- [x] **WP-A（401 验证取证）**：`scratch/goal020-ec03-401-verification.py` —— 对真实控制面
      跑关闭态与开启态：读面 200 / 写面不带 401 / 带错 401 / 带对 2xx / 启动警告在场；
      两个 401 的 `detail` **各自点名**成因。
- [x] **WP-B（三处文档）**：runbook 新增 `### 2.2`（四步验证 + 读法表）与 `### 2.3`
      （部署面四条检查项 + 不可验证登记）；`IDENTITY_AND_ACCESS.md` 新增「运维面」小节
      并更新未覆盖第 5 条；`CONTROL_PLANE_API.md` 补运维面与部署面两条。
- [x] **WP-C（威胁模型同源）**：`THREAT_MODEL.md` §6.7 追加运维面条目
      （**追加在 `零夸大` 之后**，避免把该必需措辞挤出 1200 字观察窗）。
- [x] **WP-D（记录）**：RECHECK + MEM + GOAL 回写。

## 证据

- **五面在位**：三处文档逐处 diff（各自可独立查到开启 / 轮换 / 关闭 / 验证 / 部署）。
- **401 实测**：`scratch/goal020-ec03/401-verification-summary.json` +
  脚本输出的逐条状态码。
- **判据零改动**：`git diff --stat -- tests/architecture/python/test_control_plane_auth_same_source.py
  tests/architecture/python/test_runbook_same_source.py` = 空。
- **同源句计数**：四份文档各 **1** 次。
- **部署面终态**：检查项 3 条 + **未验证声明**（本机单进程、无真实拓扑）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | DONE | 四 WP 完成。**五面在位**（4 文件 / 115 插入，产品代码零改动）；**401 实测** 关闭态 200/201/警告在场、开启态 200/401/401/201（两个 401 各自点名成因）；**既有判据零改动且 21 passed**；同源句各恰好 1 次；零夸大。`W-12` 收口为「检查项 + 不可验证登记」。RECHECK-20260926-199 = PASS_WITH_WARNINGS。 |
| 2026-09-26 | IN_PROGRESS | 建档（GOAL-020 cycle 3 = EC-03）。已确认四份文档的既有判据约束（同源句逐字一次 / 各自未覆盖锚点 / 1200 字窗 / 21 条禁用短语 / runbook 五个固定节名）与 `§6.7` 的窗口余量（`零夸大` 在 offset 1054，窗 1200）。 |

## 影响报告

- **Domain/API/schema 变化**：**无**（只动文档；不动 DTO / 路由 / 快照）。
- **安全/凭据变化**：**无新增面**（登记的是**运维步骤**；token 值仍只在环境变量里）。
- **兼容性/迁移风险**：低——文档改动受既有判据约束，已逐条满足且判据零改动。
- **上游版本影响**：**无**（零依赖改动）。
- **下一项任务**：GOAL-020 cycle 4 = **EC-04**（收口复检 + 残余登记）。
