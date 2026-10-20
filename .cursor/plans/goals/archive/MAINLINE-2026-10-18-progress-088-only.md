# MAINLINE 历史归档 — 进展记录（序 48 / GOAL-088）

> 原文搬运自 `.cursor/plans/goals/MAINLINE.md` 的「进展记录」节（活跃面只保留最近 3 条，
> 序 59 收口时移出）。唯一改动：相对链接基准 `../rechecks/` → `../../rechecks/`。

## 进展记录（移出部分，原文搬运）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-18 | GOAL-20261018-088 | **实验域：设计由检索证据派生** —— `design_source` 新增**第二个来源** `retrieval`：臂与参数从本 run 的 `TrustLabel.RETRIEVED` 证据里读出（run 作用域、确定性、零出网、fail-closed）。**性质维度不可伪造**：同一条内容标成 `USER_PROVIDED` 即**不算**（点名）；**来源唯一**：与显式 `arms` 同场 ⇒ 点名 `undecidable`；无证据 / 无设计块 / **两份设计** / 越白名单**逐条点名**（不取最后一条、不回落）。两个来源共用**同一个**设计块解析器（`design_block_in`）。读数：新判据 **10 条**；既有实验判据 **40 passed** 零回归。 | 实验 | [RECHECK-20261018-530](../../rechecks/RECHECK-20261018-530-goal-088-experiment-design-from-retrieval.md) |
