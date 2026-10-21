# MAINLINE 历史归档 — 进展记录（序 57 / GOAL-089）

> 原文搬运自 `.cursor/plans/goals/MAINLINE.md` 的「进展记录」节（活跃面只保留最近 3 条，
> 序 60 收口时移出）。唯一改动：相对链接基准 `../rechecks/` → `../../rechecks/`。

## 进展记录（移出部分，原文搬运）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-19 | GOAL-20261019-089 | **方向驱动问题、问题驱动检索、推进自动起来** —— ① **方向进 canonical**：`ProjectDefinition.direction`（可选、≤2000、空白拒绝，`with_direction` 与 `renamed` **分开**）+ sqlite 往返 + 两端点读写 + OpenAPI/types/隐私清单同轮；② **检索词由系统自己提出的问题决定**：跨相材料进 run-chain 参数材料，改上游产出 ⇒ 换检索词、摘上游 ⇒ **编译期**点名（`CROSS_PHASE_INPUT_INVALID`）；③ **推进自动**：`ScheduleJob.PROGRAM_ADVANCE` + 周期作业调用**与手动端点同一条**装配链（`advance_for`），三种既有闸门语义一字未动；④ **真跑**：新中转站 + 真实 runtime，一句话方向 ⇒ 模型自提问题（`retrieval-augmented generation scientific hypothesis discovery`）⇒ 3 条真实 PMID（`41408154`/`41743026`/`42160738`），run `SUCCEEDED`。读数：新判据 **34 条**；`tests/application+contracts+api` **1471 passed / 76 skipped**；收口验证器本树 **89 条判词**。残余 `W-6`（`producer_trust_label` 推导过宽）如实登记，补偿判据在位。 | 检索 | [RECHECK-20261019-089](../../rechecks/RECHECK-20261019-089-goal-089-direction-drives-question-drives-retrieval.md) |
