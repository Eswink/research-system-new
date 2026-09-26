---
id: PLAN-20260926-199
slug: goal-020-closeout-recheck
title: GOAL-020 cycle 4（EC-04）：收口复检（两树同结论 + 按压 + as-is m0 覆盖记录面 + 残余终态）
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
    承 GOAL-20260926-020 的 **EC-04**（收口复检 + 残余登记）。授权沿用该 GOAL 的
    `authorization.ref`：**前端 token 输入与携带**、**记录面门禁覆盖**、**认证运维面**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：读面认证（GET/HEAD）、多租户 / organization scope / RBAC / 对象级授权
    （BOLA/BFLA）、调用方自报身份、新增依赖、把 token **值**写进任何地方、改认证的 401
    响应形态、改 `Idempotency-Key` 语义。
    **本 PLAN 专属边界**：**不得**放宽任何判据 / 阈值 / 门禁（含
    `test_reproducibility_wording.py`、`test_control_plane_auth_same_source.py`、
    `test_security_scan.py`）；**不得**宣称项目安全（`R-M1` 未收口）；
    **本 PLAN 不改产品代码**（收口 = 复检 + 记录 + 状态收口；若复检判红 ⇒ **只修被判红的那个面**）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260926-200-goal-020-closeout-recheck.md
memory_entries:
  - 无可复用事实（收口轮：复检 + 记录 + 状态收口；可复用事实由前三轮的 MEM-146/147/148 承载）
---

# PLAN-20260926-199 — GOAL-020 收口复检（EC-04）

## 目标

把 GOAL-020 收口：**独立复检**（不复用实施方叙述，直接读树 + 跑判据 + 按压）、
**两树同结论**、**as-is 本机 m0 到 23/23 且覆盖记录面**、**治理 validate 绿**、
**CI 台账到终态**、**残余逐条终态**，最后把 GOAL 置 `ACHIEVED`。

## 验收条件

- [x] **AC-1（独立复检非恒真）**：复检脚本在**当前树**与**干净 checkout** 两路同结论，
      且**按压必须判红**（删扫描根 ⇒ 覆盖判据红 ⇒ 逐字节还原）。
- [x] **AC-2（as-is m0 = 23/23 且覆盖记录面）**：终态行
      `PASS: profile=m0; 23 deterministic checks`，且**运行发生在全部收口记录写完之后**
      （按 EC-02 修好的顺序）。
- [x] **AC-3（治理）**：`validate.py` = `Cursor 治理验证通过`（含 `DOCS-CHECK`）。
- [x] **AC-4（CI 台账）**：四次推送逐 run 逐 job 实查（M0 八 job + CodeQL，含 `run_attempt`）。
- [x] **AC-5（残余终态）**：承继残余逐条在位；GOAL-019 的 `W-10`…`W-14` **逐条写明终态**。
- [x] **AC-6（未覆盖范围明写）**：读面未认证 / 多租户未做 / D-12(a) 未做 / `R-M1` 未收口 /
      部署面终态。
- [x] **AC-7（受保护判据零改动）**：三个受保护判据文件本 GOAL 零改动（`git diff` 取证）。

## 实施清单

- [x] **WP-A（复检脚本）**：`scratch/goal020-ec04-closeout-recheck.py` —— 六个面
      （交付面在位 / 运维面五标志 / 残余登记 / 受保护判据零改动 / 按压 / 两树同结论）。
- [x] **WP-B（as-is m0 + 记录面判据）**：先写记录 → 记录面判据 → 全量 m0。
- [x] **WP-C（CI 台账）**：四次推送的 run / 逐 job / `run_attempt` 逐条落表。
- [x] **WP-D（收口）**：EC 置终态 + 状态历史 + 迭代日志 + `latest_recheck` + 残余终态表。

## 证据

- 复检脚本输出（两树判词一致 + 按压判红 + 逐字节还原）。
- `scratch/goal020-c4-m0-as-is.log` 的终态行与逐项计数。
- 治理输出 + `DOCS-CHECK`。
- 四次推送的 run id / 链接 / 逐 job 结论 / `run_attempt`。
- 受保护判据的 `git diff`（空）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-26 | DONE | 收口完成。复检脚本 **32/32**（两树同结论 1368 passed ↔ 1368 passed；按压判红 + 逐字节还原）；as-is m0（记录写完之后）= **23/23**（4365 passed / 214 skipped、零 FAILED）；治理绿；CI 四次推送全绿 `run_attempt=1` ×4。RECHECK-20260926-200 = PASS_WITH_WARNINGS。 |

## 影响报告

- **Domain/API/schema 变化**：**无**（收口轮不改产品代码）。
- **安全/凭据变化**：**无**（不涉及凭据面；不记 token）。
- **兼容性/迁移风险**：无（只增记录）。
- **上游版本影响**：**无**。
- **下一项任务**：GOAL-020 收口后无下一轮；后续若要做 BOLA/BFLA 或读面认证**需另行授权**。
