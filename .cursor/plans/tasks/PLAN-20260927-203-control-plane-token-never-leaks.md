---
id: PLAN-20260927-203
slug: control-plane-token-never-leaks
title: GOAL-021 cycle 2（EC-02）：token 不泄漏——日志 / 遥测 / 401 body / 事件 / 前端持久层 / 记录面
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
    承 GOAL-20260927-021 的 **EC-02**（token 不泄漏，承 AGENTS.md §10 观测隐私面）。授权沿用该 GOAL 的
    `authorization.ref`：**新增对抗性判据 + 修复被证明为真缺陷 + 文档同源**三条；
    push-to-main-for-CI 口径（**只推 main、不 force、不重写历史、不推旁支**）；
    默认 runtime 保持 **Fake**、默认 CI **离线**。
    **明文不做**：给读面（GET/HEAD）加认证、多租户 / organization scope / RBAC、
    BOLA·BFLA 专项实现、调用方自报身份、新增依赖、把 token **值**写进任何地方
    （含**判据源码**——一律用测试内构造的合成假值）、改认证的 401 响应形态、
    改 `Idempotency-Key` 语义、改任何**既有**判据 / 门禁 / 阈值 / 放行面。
    **本 PLAN 专属边界**：**不得**改 `tests/api/test_security_scan.py` 的持久层 / `sk-` 断言
    （既有安全判据），也**不得**改 `tests/api/test_secret_redaction.py`；本 PLAN 的新判据
    只补**它们没覆盖的**面（控制面 token 在日志 / 遥测 / 401 / 事件 / 记录面）；
    **不得**宣称项目安全（`R-M1` 未收口）。
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20260927-204-control-plane-token-never-leaks-recheck.md
memory_entries:
  - .cursor/memory/entries/MEM-20260927-150-credential-leak-is-per-exit-and-shape-based.md
---

# PLAN-20260927-203 — token 不泄漏（GOAL-021 EC-02）

## 目标

证明**控制面 token** 不出现在六个出口，并把结论固化为受门禁保护的判据：

1. **日志**（含 access log / 应用 log / 异常消息）；
2. **遥测 / span 属性**（含把 token 塞进 attributes 的对抗输入）；
3. **错误响应体**（含 401 的 `detail`——两个拒绝成因各自点名但**不回显凭据**）；
4. **事件 payload**（canonical 只记主体**标识**，不记凭据）；
5. **前端持久层**（浏览器存储；既有 `test_security_scan.py` 已覆盖 ⇒ **不重复**）；
6. **记录面**（`.cursor/plans`、`.cursor/memory` 只有**变量名**、无 token **值**）。

**与既有判据的分工（不重复、不顶替）**：
`test_secret_redaction.py` 判的是**中转站 API key** 在 DTO / error 出口的脱敏；
`test_security_scan.py` 判的是 DTO / SSE / Export / error 四个出口的 `sk-` 与前端持久层。
**本 PLAN 判的是控制面认证 token 这一条凭据**在其**特有出口**（401 body 的两个点名文案、
`sanitize_attributes` 的对抗输入、日志捕获）上的行为。

## 验收条件

- [x] **AC-1（日志面 · 行为判据）**：认证开启 + 带合成 token 发写请求（缺 token / 错 token /
      对 token 三类各一次），用**捕获 handler** 收全部日志记录 ⇒ token **值**零命中。
      **判据自身不得把 token 写进断言字面量**——用运行时构造的合成值。
- [x] **AC-2（遥测面 · 结构 + 对抗行为）**：
      **结构**：span attribute 词汇是**闭集 allow-list**，未知键**整个丢弃**
      （`authorization` 这类键进不去）；
      **对抗行为**：把 token 塞进**允许清单内**的字符串键 ⇒ 该值**不得**原样导出。
      **如实登记已知边界**：`redact_text` 是**形态匹配**（bearer 形态会被脱敏，
      **裸不透明串**在允许键内会留下）——判据断言的是**真实行为**，不是想象中的强脱敏。
- [x] **AC-3（401 响应面）**：两个 401 的 `title` / `detail` / 整个 body **不含** token 值；
      且两个拒绝成因**各自被点名**（缺 Bearer 头 / 不匹配）——**断言形态一字未改**。
- [x] **AC-4（事件 payload）**：canonical 事件里记的是**主体标识**（`actor`），
      **不是**凭据；带 token 的写请求产生的 `approval.decided` payload **不含** token 值。
- [x] **AC-5（记录面）**：`.cursor/plans` + `.cursor/memory` 中 token **值**零命中
      （只允许**变量名**）；`tools/credential_audit.py` 四面 `offenders=0`。
- [x] **AC-6（反证 · 先红后绿）**：临时让某出口泄漏（把 token 值写进日志）⇒ 判据**判红**
      ⇒ **逐字节复原**（sha256）⇒ 绿。**按压打偏记为失败**。
- [x] **AC-7（既有判据零改动）**：`test_security_scan.py` / `test_secret_redaction.py` /
      `test_reproducibility_wording.py` / `test_record_face_is_covered_by_the_gate.py` /
      `test_control_plane_auth_same_source.py` 五个文件 `git diff --quiet` 全空。
- [x] **AC-8（规模与收集面）**：新判据 **≤ 450 行**、单函数 **≤ 50 行**；落 `tests/**`
      ⇒ 属既有 `python/tests` 收集面 ⇒ **不新增 m0 check**（终态行仍 23）。
- [x] **AC-9（记录面顺序）**：按 MEM-145 —— 先写记录 ⇒ 跑记录面判据 ⇒ 再跑全量门。

## 实施清单

- [x] **WP-A（先红）：确认泄漏判据真能红** —— 用 `scratch/goal021-ec02-probe-leak-surfaces.py`
      取证六个出口的**当前行为**（**已跑通**：日志零命中 / 未知属性键被丢弃 /
      两个 401 body 零命中 / **裸不透明串在允许键内会留下**）。
- [x] **WP-B（判据）**：新增 `tests/api/test_control_plane_token_never_leaks.py`：
      日志捕获 + 遥测对抗输入 + 401 body + 事件 payload + 记录面结构判据。
- [x] **WP-C（后绿+复原）：反证 1/1 红** + 逐字节复原 + 定向套件复跑绿。
- [x] **WP-D（记录）**：`RECHECK-20260927-204` + `MEM-20260927-150` + GOAL-021 回写。

## 证据

**交付**：`tests/api/test_control_plane_token_never_leaks.py`（**312 行 / 12 例**）。

**六出口实测（每出口一个判据，不笼统断言）**：
日志（三类请求捕获 ⇒ **零命中**，且**捕获装置自证有效**——哨兵记录能被截到）；
遥测（未知键 **整个丢弃**；允许键 + bearer 形态 **必被脱敏**；
允许键 + **裸不透明串 会留下**——**如实断言现状**）；
401 body（两个 401 零命中，且两个成因**各自点名**）；成功响应不回显；
事件 payload（零命中，`actor` = `service:leak-probe`）；记录面（凭据值零命中，
且**变量名**确有出现以排除扫描面选错）。

**反证（1/1 红，逐字节复原）**：在中间件里对 `provided` 记一条日志
⇒ `TestTheTokenNeverReachesLogs::test_no_log_record_contains_the_token` **1 failed**
⇒ `sha256` 复原一致（`ca03dac36982d5509e34ae719e352fbc84cd70189a526bd3389621597c82691a`）
+ `git diff` **IDENTICAL TO HEAD** ⇒ 复跑 **12 passed**。

**既有判据零改动**：`test_security_scan.py` / `test_secret_redaction.py` /
`test_reproducibility_wording.py` / `test_record_face_is_covered_by_the_gate.py` /
`test_control_plane_auth_same_source.py` 五个文件 `git diff --quiet` **全空**。

**受影响套件**：`tests/api/` + `tests/architecture/python/` ⇒ **745 passed, 4 skipped**。

**本轮修掉的缺陷 = 判据自身 1 处**（**非**产品缺陷）：首版记录面判据用
`glob("*.md").__next__()` 取**任意**第一个文件 ⇒ 判据自己判红且理由错；改为跨全部记录文件
统计。**零产品代码改动**（中间件 `git diff` 为空）。

**as-is 本机 m0（记录写完之后）= `PASS: profile=m0; 23 deterministic checks`**
（`PASS [` = **24**、**4590 passed / 21 skipped**、零 `FAILED`/`ERROR`；
日志 `scratch/goal021-c2-m0.log`）⇒ 新增判据落在既有 `python/tests` 收集面内，**m0 条数仍为 23**。

## 影响报告

- **产品代码**：预期**零改动**（自检）。若判据**证明**某出口真的泄漏 **控制面 token**
  ⇒ 在 GOAL-021 授权内修产品代码并逐条登记。
- **Domain / API / schema**：**无变化**。
- **安全 / 凭据**：**无放宽**；判据中的 token 为**测试内构造的合成假值**。
- **门禁面**：落 `tests/**` ⇒ 不新增 m0 check。
- **下一项任务**：GOAL-021 的 **EC-03**（主体归因不可伪造）。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-27 | DONE | 收口（GOAL-021 cycle 2）：圈定 EC-02「token 不泄漏」。**设计期已实测六出口现状**（`scratch/goal021-ec02-probe-leak-surfaces.py`）：日志捕获**零命中**；遥测**未知键被整个丢弃**（`authorization` / `raw_headers` 进不去）；两个 401 body **零命中**；**但** `redact_text` 是**形态匹配** —— `Bearer <x>` 会脱敏、**裸不透明串**在**允许键内**会留下 ⇒ 该边界**如实登记**为判据的适用边界，**不**写成「任意形态都安全」。 |
