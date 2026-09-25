---
id: MEM-20260925-137
title: "写「豁免 / 维持现状」类决定时：非 ASCII 枚举必须关 core.quotepath，且判据要同时断言「转义后的假 0」"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-174-landed-decisions-are-citable.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-175-landed-decisions-are-citable.md
supersedes: []
tags: [git, quotepath, non-ascii, docs-gate, adr, goal-016, d-07, d-08, d-09]
---

## 做了什么

GOAL-016 的 **EC-04** 把三条「维持类」决定固化成可引用依据：`ADR-0031` 补**「否证条件」**
（`Status` 仍 `Proposed`）、`MODEL_COMPATIBILITY.md` 增 §9 记下
**`ModelCompatibilityProfile` 维持派生视图**（改一等实体必须先出迁移/回滚 ADR）、
新建 **`ADR-0032`** 记录 **30 条非 ASCII 历史路径豁免**（**不重命名**，引用 `AGENTS.md` §13）。
新判据 `tests/tooling/test_landed_decisions_are_citable.py`（6 条）把这些事实全部钉住。

## 为什么这样做

- **「维持现状」也是一种决定，但它不自带证据**：不写下来，下一轮还会被重新提问；
  写成 ADR / 架构章节 + 结构判据之后，它才成为可引用、可复检的依据。
- **`git ls-files` 会让非 ASCII 路径「消失」**：默认 `core.quotepath=true` 把非 ASCII
  转义成 `\NNN` 八进制形态，于是**朴素枚举非 ASCII 数 = 0**。任何「数一下有多少非 ASCII
  路径」的脚本（审计、清单、门禁）若不关转义，得出的「没有」是**假绿**而不是事实。
- **只断言真实基数还不够**：若判据只断言「关掉转义 = 30」，将来有人把枚举改回朴素写法，
  判据会**跟着一起变假**。所以要把「转义的 0」本身也写成断言。
- **「补否证条件」≠「拍板」**：维持 `Proposed` 的 ADR 也可以获得**可执行的下一步**——
  写清「什么证据会证伪它、何时该改判」。这既给了后续行动依据，又不越权把 `Status`
  改成 `Accepted`。判据要**同时**硬断言「含否证条件节」与「全文无 `Status: Accepted`」。
- **判据先红时先怀疑文档措辞，而不是先放宽判据**：本轮两条红都是**断行 / 多一个字**，
  而它们恰好说明「不可逐字引用的措辞本身就是缺陷」。

## 怎么做与复现

- **枚举（必须带 `-c core.quotepath=false`）**：
  `git -c core.quotepath=false ls-files` ⇒ 本仓实测 3389 条中 **30** 条含非 ASCII；
  对照 `git ls-files`（朴素）⇒ 非 ASCII **0** 条、且存在 `\3` 转义形态。
- **判据形态（双向 + 双数 + 可按压）**：
  ① 「现实 ↔ 清单」**双向**比对（既报「现实有、文档没写」的漏登记，也报
  「文档写了、现实没有」的过期条目）；② 同时断言「朴素枚举 = 0 且 `\3` 形态存在」
  与「关转义 = 30」；③ **按压**：从清单删一条真实路径 ⇒ 必须报出；往现实塞一条
  `docs/新路径.md` ⇒ 必须报出（内存比对，不落盘）。
- **不动 `Status` 的取证**：`grep -c "Status: Accepted"` 在 `ADR-0031` 上 = **0**；
  并跑既有「待拍板 / 可分别决定」判据确认未被本次补写破坏（实测 `18 passed`）。
- **文档可被逐字引用**：§13 引文收进**同一行**（断行会让连续子串匹配失败）；
  前置条件写成 `**必须先出 ADR**` 这种**整块可匹配**的形态。
- **doc 一致性门**：`uv run --frozen --no-sync python -B tools/docs_consistency_check.py`
  ⇒ `DOCS-CHECK PASS: 6 deterministic checks`。反引号里的路径**要么是真实存在的对象，
  要么别放进反引号**——省略号缩写（`010…012`）与凭印象写的文件名都会被
  `[backtick-ref]` 当场抓出。

## 适用边界

- **豁免只管清单里的既有 30 条**：新建非 ASCII 路径**仍判红**（规则与判据都未动）；
  本 EC **未**验证「新路径确实被拦」——那是既有命名门禁的职责，不在本决定范围。
- **`ADR-0031` 仍 `Proposed`**：本轮补的是**否证条件**（何时该改判），**不是**拍板。
  **不得**把本轮读成「`tool_pack.*` 已获准」。
- **`ADR-0032` 的 `Status: Accepted`** 与 `ADR-0031` 的 `Proposed` **不冲突**：前者记录
  「不再重命名」这一**已执行**事实，后者是「要不要给 `tool_pack.*` 开口子」这一**未拍板**
  的问题。
- **「关掉转义」是枚举命令的属性，不是仓库配置**：不要为了省事去改仓库的
  `core.quotepath` 设置（那会改变所有人的日常输出）；在**调用点**加 `-c` 即可。
- 结论依赖「非 ASCII 路径数 = 30」这一**当时**事实；若日后有路径重命名，须同步更新
  `ADR-0032` 的清单（判据会双向报出漂移）。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-174-landed-decisions-are-citable.md`（WP1–WP5）
- `.cursor/plans/rechecks/RECHECK-20260925-175-landed-decisions-are-citable.md`
- `.cursor/plans/goals/GOAL-20260925-016-decisions-landed-and-threat-model.md`（EC-04）
- `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-07 / D-08 / D-09（判词与范围同源）
- `docs/adr/ADR-0032-legacy-non-ascii-path-exemption.md`（豁免清单与枚举命令）
- `AGENTS.md` §13（Repository Path Naming）
