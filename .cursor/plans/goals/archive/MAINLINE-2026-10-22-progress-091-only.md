# MAINLINE 进展记录归档 —— 序 55（GOAL-20261020-091）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-20 | GOAL-20261020-091 | **复检域：两个不同的模型在同一件产物上真的判出不同结论** —— 建档实测出两处**结构不可达**的根因并修掉：① 真实会话交付物是**信封**（正文在 `content` 里），而 `REVIEW_SCORE` 只按顶层点分路径取值 ⇒ 判词恒 `review score unknown` ⇒ **两个模型无论判什么，判定面看到的都是同一个「不知道」**（修法：路径每段先解信封，复用既有 `declared_object`）；② 上游产物只以**证据**身份落库、**不进**评审者提示词 ⇒ 两位评的不是同一件东西（修法：第四段「被评对象」，并列 / 有界 / 截断可见 / 同源，只挂 `REVIEWER`）。**顺带剥出一处既有缺陷**：`SessionBuilder` 把**已渲染的 `str`** 交给 `compose_prompt`，而后者按**视图对象**再渲染 ⇒ 检索段 / 前序段 / 被评对象段**全部被静默丢弃**（真实 run 实测：`send_message` 收到的字符串里 `UNDER REVIEW` 段整个不见）—— GOAL-081/082 在真实会话上一直没生效。**真跑读数**：`dual_model_review_v1` 上 `main/glm-5.3` 判负(0.45)、`main/kimi-k2.6` 判过(0.82)，两位都指出同一弱点（“significantly higher” 未被操作化）而**严重程度判断不同**，`dissent` 非空、`independent is true`。读数：新判据 **20 条**（信封 4 + 提示词 12 + 成对 4），见证 `--verify-only` 三态；`aggregate_panel` / `TrustLabel` / `count_retrieved_sources` **一行未动**。 | 复检 | [RECHECK-20261020-091](../../rechecks/RECHECK-20261020-091-goal-091-two-models-judge-the-same-artifact.md) |
