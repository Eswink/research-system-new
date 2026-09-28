---
id: MEM-20260929-163
title: "响应头是独立的受判出口：回显类头的取值多是**标识符**派生，内容金丝雀与标识符回显必须分成两个命题；受判头需 ABSENT 档兜住「登记为不发射」"
status: ACTIVE
created_at: 2026-09-29
updated_at: 2026-09-29
scope: repository
confidence: 0.9
review_after: 2027-03-29
source_plans:
  - .cursor/plans/tasks/PLAN-20260929-237-goal-025-ec01-response-header-face-in-scan.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260929-238-goal-025-ec01-response-header-face-in-scan.md
supersedes: []
tags: [response-headers, content-canary, identifier-echo, judged-face, absence-registration, goal-025, ec-01]
---

## 做了什么

GOAL-025 cycle 1 把「读面**响应头**」纳入非 canonical 出口的受判面（GOAL-024 的读面判据只扫
**响应体**，`response_text()` 只读 `response.content`）。默认离线链上实跑 **65 条**读路由，
观测到的响应头只有 **5 个名字**（`content-type` 65 / `content-length` 65 / `etag` 4 /
`content-disposition` 1 / `x-content-type-options` 1；`last-modified` **0**），
受判头（`content-disposition` / `etag`）零命中，并且**先证明这两个头是活的**。

## 为什么这样做（为什么值得记）

- **响应头是**独立的**出口，不是响应体的一部分**：扫描器若只取 body，整条头面**不在射程内**，
  而头恰恰是最容易被"顺手回显"的地方（本仓 `_content_headers()` 就把 `artifact.id` 写进
  `Content-Disposition.filename`、把 `artifact.digest` 写进 `ETag`）。
- **回显类头的取值多半是标识符，不是内容** ⇒ 这里有一个**假红陷阱**：若夹具把金丝雀塞进
  `artifact_id`，头面判据会红，但那是**契约行为**（id 本来就在 `/artifacts/{artifact_id}`
  元数据面上可见），不是泄漏。正确口径是：受判命题 = 「**内容（正文）**不出现在头里」，
  标识符回显**显式排除**，并且这条边界要有**自己的机械断言**（断言夹具标识符不含金丝雀 token），
  否则边界只活在散文里，下一个人一改夹具就制造假红。
- **`ABSENT` 是必须的第三档**：若只分「受判 / 豁免」，一个「登记为不发射」的头（如
  `last-modified`：产品根零发射点）会被登记成**豁免**，于是它**将来真的开始发射**时
  **不会判红** ⇒ 新的回显面静默逃逸。第三档把它变成「出现即判红，需重新分类」。
- **豁免必须是机械的**：`EXEMPT` 除理由外还要有**值形态断言**（十进制计数 / 常量 `nosniff` /
  媒体类型字符集）；只写散文理由的豁免会在自审里判红（按压 P3 实测）。
- **正控制要证明「头是活的」**：零命中可能是「头根本没在发」⇒ 必须断言
  `Content-Disposition.filename` 逐字符等于净化后的 `artifact.id`、`ETag` 逐字符等于
  `artifact.digest`。顺带发现实测细节：处置词是 **`inline`**（由制品 `media_type` 决定），
  不是想当然的 `attachment` —— 断言写死了就会假红（本轮踩到并改成「两者之一」）。

## 怎么做与复现

1. **分区**：`HEADER_RULES` 写在判据源码里（受判 / 豁免 / 不发射），
   理由空、重复、未知判定、未分类的观测头、不发射却出现、登记陈旧、受判面下界 —— 七条判红。
2. **绝对扫描**：**任何**头（含豁免头）的值命中金丝雀都判红，失败消息点名**路由 + 头名 + kind**。
3. **非空取证**：受判头逐条观测计数必须 > 0，且实取路由数 ≥ 下界（防空转）。
4. **两向反证**：受判头带金丝雀 ⇒ 红（真实应用按压路由）；内容进 canonical / 正文 ⇒ **不**红。
5. **按压复原**：改判据源码的清单（删规则 / 抽空理由 / 改判 ABSENT→EXEMPT）三处**先红后绿**，
   raw `sha256` 逐字节复原、证据**二进制写盘**。

## 适用边界

- 只覆盖**读面（GET）**响应头；**写面**（POST/PATCH/PUT）响应头不在射程。
- `EXEMPT` 的形态断言是**形态**而非「永不承载内容」的证明；以「任何头值零命中」绝对扫描兜底。
- `Content-Disposition.filename` 的**取值来源面**（`artifact.id` 是否可能承载用户文本）**未判定**。
- 只对**默认离线链**成立；真实 runtime / 工具面 / 部署面未验证。
- **不构成**任何"项目安全"结论（`R-M1` 未收口）。

## 来源

- 交付：`tests/observability/read_face_header_inventory.py`（217 行）、
  `tests/observability/test_privacy_read_face_headers.py`（245 行 / 13 例全绿）
- 复检：RECHECK-20260929-238（`PASS_WITH_WARNINGS`；`W-3` = 取值来源面未判定）
- 前置：MEM-20260928-162（读面零命中必须配**有上界的白名单**；其「适用边界」第 1 条正是本轮的靶子）
