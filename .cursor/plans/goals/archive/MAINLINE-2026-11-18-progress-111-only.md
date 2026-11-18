# MAINLINE 进展记录归档 —— 序 79（GOAL-20261111-111）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**，保持活跃面上的原序；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-11-12 | GOAL-20261111-111 | **面板判词从「某个模型认为」升级为可核验的结构断言**。`panel_grounding.py`：正文切成**编号句子** `S1…Sn`（确定性、与 `manuscript_quality._SENTENCE_SPLIT` **同一个正则**，判据钉住）；`REFUTED` 的 `rationale` 必须落在正文的字节上（`S<n>` 在范围内 / 引用真实子串），指不到就**降级** `AMBIGUOUS` + `UNGROUNDED_REFUTED:` 点名缺什么（模型原话保留）。**两种「不成立」分得开**：空 rationale（没做功课）≠ 指不到（给了个假的）。约束**只落在 `REFUTED`**：`SUPPORTED` / `AMBIGUOUS` / 设施失败原样通过。`NOT_JUDGED` 五项**逐字未动**、判定表一字未动、面板仍 advisory。阶梯只改「报告」一格，**其余六格逐字未动**。 | 复检 | [RECHECK-20261112-111](../../rechecks/RECHECK-20261112-111-panel-grounding.md) |
