---
id: MEM-20260925-138
title: "文档级威胁模型草案的交付判据是「射程围栏」：未覆盖范围 + 唯一可引用口径 + 纯增量"
status: ACTIVE
created_at: 2026-09-25
updated_at: 2026-09-25
scope: repository
confidence: 0.9
review_after: 2027-03-25
source_plans:
  - .cursor/plans/tasks/PLAN-20260925-176-authorization-surface-threat-model-draft.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260925-177-authorization-surface-threat-model-draft.md
supersedes: []
tags: [threat-model, bola, bfla, authorization, m18, docs-only, goal-016, d-12]
---

## 做了什么

GOAL-016 的 **EC-05（D-12(b)）**在 `docs/security/THREAT_MODEL.md` **增量补第 6 节**
（106 → 252 行，**146 增 0 删**）：授权面 BOLA / BFLA 的**实况清单**（124 条控制面路由
逐条零授权依赖、无调用方认证、策略只到能力级不到对象级、域实体无归属概念）、
**`### 6.3 未覆盖范围`**（8 条）、**`### 6.4 与 M18 边界的关系`**、`### 6.5 若取 (a)：
范围与代价`、`### 6.6 引用约束`。**零代码 / 零门禁 / 零判据改动**（diff 只含 2 个 docs 文件）。

## 为什么这样做

- **「先出草案再定覆盖」的风险是草案被当成结论**：一句「已做威胁建模」就足以让空白变成
  假安全。所以 (b) 的交付物必须**自带围栏**：写清未覆盖什么 + 规定唯一可引用的口径。
- **围栏要写进文档，而不只是写进记录**：记录会被翻篇，文档会被引用。把
  「**不得**引作安全结论」写进被引用文件本身，才能跟着引用一起被传播。
- **「有意未做」与「疏漏」必须区分**：控制面无认证不是某处校验写错，而是
  **M18 明文 DEFERRED** 的结果（`MILESTONES.md:973` 写着「不标记部分完成」）。
  不写这层，后续每轮都会重新把它当缺陷报一次。
- **纯增量是这类文档的硬判据**：威胁模型是**被引用面很广**的既有资产，
  重写会静默改掉别人的引用语义。`git diff --numstat` 的**删除数为 0** 是
  可机械取证的一条，应写进验收条件而不是靠自觉。
- **无认证时的 BOLA/BFLA 与「校验写错」不是一类问题**：没有认证就**没有主体**，
  「越权」无从定义 ⇒ 这类缺口**无法**靠加测试修好，前置永远是**主体模型**。

## 怎么做与复现

- **勘察口径（只读、零写）**：用只读子代理并行铺开 8 个问题（路由清单 / 认证机制 /
  授权检查层 / 对象归属 / M18 定义 / `docs/security/` 现状 / 不得夸大的既有控制 /
  BOLA-BFLA 既有提及），每条事实要 `file:line`。**关键搜索**：
  `Depends(` / `Security(` / `current_user` / `HTTPBearer` / `APIKeyHeader` 的**零命中**
  本身就是最有价值的事实（「没有」也要取证）。
- **纯增量取证**：`git diff --numstat docs/security/THREAT_MODEL.md` ⇒ 第二列必须为 **0**。
- **diff 只含 docs 取证**：`git status --porcelain` 逐条核对改动集；
  并发写者文件必须排除在 `git add` 之外。
- **反引号引用**：`tools/docs_consistency_check.py` 的 `[backtick-ref]` 只检查
  以 `packages/ tools/ tests/ docs/ …` 开头的纯路径；**含 `:` 或空格的引用会被跳过**
  ⇒ 「`文件.py:261`」这种 `file:line` 写法既不触发检查、又能被人工复核。但**别用省略号
  缩写路径**（`010…012` 会被判不存在）。
- **发布快照别顺手刷**：`FRAMEWORK_MANIFEST.json` 是**只由显式发布流程生成**的
  （`docs/operations/REPOSITORY_HYGIENE.md:21`）。改它会让 docs-only 的 diff 破功，
  而且它**本就已过期**（实测 220 条里 131 条 hash 与现树不符）——
  它度量的是「发布那一刻」，不是「现在」。

## 适用边界

- **交付物不是安全性**：本文档只把「缺什么」变成可引用依据；**没有**提高任何访问控制强度。
- **会过期且不会自己红**：这是 (b) 的固有代价。要做「防漂移」必须先有 (a) 的判据，
  而 (a) 的前置是**主体模型**（M18 或明文授权的等价子集）——**没有第二个主体可测**。
- **(a) 的最小形态也可能立刻全红**：把「每条路由必须有授权状态」写成判据 ⇒ 今天 124 条
  路由全部不合规 ⇒ 只能退化成「现状白名单快照」（只防漂移、不提供安全），
  而白名单**本身就是待还的债**。**别**把这条退路说成已覆盖。
- **控制面暴露面由部署决定**，不要读成「只可能本机访问」：开发脚本绑 `127.0.0.1`，
  容器内 `uvicorn` 监听 `0.0.0.0` 而发布端口是回环——**本节未验证任何部署拓扑**。
- 结论绑定**当前树**；`file:line` 会漂移，复核以**符号名**为准。

## 来源

- `.cursor/plans/tasks/PLAN-20260925-176-authorization-surface-threat-model-draft.md`（WP1–WP5）
- `.cursor/plans/rechecks/RECHECK-20260925-177-authorization-surface-threat-model-draft.md`
- `.cursor/plans/goals/GOAL-20260925-016-decisions-landed-and-threat-model.md`（EC-05）
- `docs/roadmap/OPEN_DECISIONS_BRIEFING.md` D-12（判词与选项同源）
- `docs/security/THREAT_MODEL.md` 第 6 节（交付物本身）
- `docs/roadmap/MILESTONES.md` M18（`DEFERRED` 的权威定义）
- `docs/security/IDENTITY_AND_ACCESS.md`（未来主体模型的唯一落点）
