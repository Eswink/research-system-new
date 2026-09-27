---
id: PLAN-20260927-209
slug: goal-021-closeout-recheck
title: GOAL-021 cycle 5（EC-05 收口）：独立复检（28/28）+ 两树同结论 + as-is m0 23/23 + 残余与未覆盖范围逐条
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
    承 GOAL-20260927-021 的 **EC-05**（收口复检 + 残余登记）。授权沿用该 GOAL 的
    `authorization.ref`：**新增对抗性判据 + 修复被证明为真缺陷 + 文档同源**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **本 PLAN 专属边界（收口轮）**：**不改产品代码**（收口 = 复检 + 记录 + 状态收口；
    若复检判红 ⇒ **只修被判红的那个面**）；**不得**放宽任何判据 / 门禁 / 阈值 / 放行面；
    **不得**动 GOAL-001…020（只读）；**不得**宣称项目安全（`R-M1` 未收口）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260927-210-goal-021-closeout-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260927-152-press-restore-must-use-binary-io.md
---

# PLAN-20260927-209 — GOAL-021 收口复检（EC-05）

## 目标

对 GOAL-021 的四个 EC 交付做**独立复检**，并把收口结论、**残余**与**未覆盖范围**逐条落地：

- **独立复检脚本**对**当前树**跑出结论（本机）；
- **as-is 本机 m0 到 23/23**（**记录写完之后**跑，承 MEM-145）；
- 治理 `validate.py` 绿（含 `DOCS-CHECK`）；
- **CI 台账到终态**（M0 八 job + CodeQL，含 `run_attempt`）；
- **承继残余逐条在位**；**未覆盖范围逐条明写**。

## 验收条件

- [x] **AC-1（独立复检 28/28）**：`scratch/goal021-ec05-closeout-recheck.py` 六面全通过：
      交付面（4 判据 + 4 PLAN 在位、行数 ≤ 450）/ **按压面**（收窄保护面 ⇒ EC-01 判据判红 ⇒
      **逐字节复原** ⇒ 复绿）/ 受保护判据零改动（5 文件）/ 残余（5 条）/ 未覆盖（5 条）/ 凭据面。
- [x] **AC-2（as-is 本机 m0）**：终态行 `PASS: profile=m0; 23 deterministic checks`，
      且**运行在记录写入之后**。
- [x] **AC-3（治理 validate 绿）**：`.cursor/skills/governance-check/scripts/validate.py`
      输出 `Cursor 治理验证通过` + `DOCS-CHECK PASS`。
- [x] **AC-4（CI 台账到终态）**：本 GOAL 五次推送逐 run 逐 job（含 `run_attempt`）记录；
      flake 判定靠**同一代码的复跑对照**。
- [x] **AC-5（残余逐条）**：`R-M1` / `R-D1` / `W-10` / `W-11` / `W-12` 等在 GOAL 正文逐条在位。
- [x] **AC-6（未覆盖范围逐条）**：读面未认证 / 多租户未做 / BOLA·BFLA 未做 / 部署面未验证 /
      `R-M1` 不得宣称项目安全 —— **逐条明写**。
- [x] **AC-7（EC 全 PASS 与收口动作）**：EC-01…EC-05 全 PASS ⇒ 置 **ACHIEVED**；
      `latest_recheck` 指向存在的 PASS/PASS_WITH_WARNINGS 复检；`child_plans` / `memory_entries` 对齐。

## 实施清单

- [x] **WP-A（复检脚本）**：`scratch/goal021-ec05-closeout-recheck.py`（**已跑通 28/28**）。
- [x] **WP-B（收口记录）**：`RECHECK-20260927-210` + `MEM-20260927-152` + GOAL 置 ACHIEVED。
- [x] **WP-C（门 + 台账）**：记录面判据 → 全量 m0 → CI 台账终态。

## 证据

**独立复检（`scratch/goal021-ec05-closeout-recheck.py`）⇒ 28/28 通过**：

| 面 | 结果 |
| --- | --- |
| 交付面 | 4 个判据在位且 ≤ 450 行（**285 / 312 / 311 / 163**）；4 份 PLAN 在位 |
| **按压面** | 收窄保护面（删 `DELETE`）⇒ EC-01 判据 **exit=1（判红）**；复原后 **exit=0**；**sha256 逐字节一致** |
| 受保护判据零改动 | 5 个文件 `git diff --quiet` **全空**（`test_security_scan` / `test_secret_redaction` / `test_reproducibility_wording` / `test_record_face_is_covered_by_the_gate` / `test_control_plane_auth_same_source`） |
| 残余 | `R-M1` / `R-D1` / `W-10` / `W-11` / `W-12` **逐条在位** |
| 未覆盖范围 | 读面未认证 / 多租户 / BOLA / 部署面 / `R-M1` **逐条在位** |
| 凭据面 | 扫 9 个文件**零**真实 token 字面量；变量名在**正确落点** 3/3（中间件 + 两处安全文档） |

**复检脚本首次运行暴露两处「复核自身」的缺陷（均如实登记并修正）**：

1. **按压复原用文本模式读写 ⇒ Windows 把 LF 写成 CRLF ⇒ raw sha256 不一致**
   （`git diff` 因 `.gitattributes` 归一化**报无改动** ⇒ 该假象只有 raw sha256 能抓）
   ⇒ 改用 **`read_bytes` / `write_bytes`**。落 `MEM-20260927-152`。
2. **凭据面断言「变量名应出现在 GOAL 正文」是错的**：变量名落在**实现 / 安全文档**面
   （本 GOAL 只沿用「只登记变量名」的纪律措辞）⇒ 断言改为扫**正确的落点**
   （中间件 + 两处安全文档，3/3 在位）。

**⇒ 本轮修掉的缺陷 = 复检脚本自身 2 处**，**非**产品缺陷。

## 影响报告

- **产品代码**：**零改动**（收口轮；复检未判红任何产品面）。
- **Domain / API / schema**：**无变化**。
- **安全 / 凭据**：**无放宽**；复检脚本只读（除按压外），按压后逐字节复原。
- **门禁面**：**未新增 / 未放宽任何 check**；m0 条数仍 23。
- **下一项任务**：**本 GOAL 的终态**。后续若要推进：**BOLA·BFLA 与逐调用方身份**
  **需另行授权**；**部署面验证**需要真实拓扑。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-27 | DONE | 收口轮：独立复检 **28/28**；复检脚本自身 2 处缺陷已修（文本模式读写 / 变量名落点断言）；**零产品缺陷**。 |
