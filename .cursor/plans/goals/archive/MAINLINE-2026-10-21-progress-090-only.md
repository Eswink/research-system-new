# MAINLINE 历史归档 — 进展记录（序 58 / GOAL-090）

> 原文搬运自 `.cursor/plans/goals/MAINLINE.md` 的「进展记录」节（活跃面只保留最近 3 条，
> 序 61 收口时移出）。唯一改动：相对链接基准 `../rechecks/` → `../../rechecks/`。

## 进展记录（移出部分，原文搬运）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-20 | GOAL-20261020-090 | **证据域：覆盖门的性质维不再可被跨相边间接满足** —— `EVIDENCE_COVERAGE` 新增**第三个正交维度** `minimum_tool_evidences`：只数**带 `tool_refs`** 的证据 ⇒ 问的是**调用事实**（工具证据登记时必带 provider/tool），而不能被「声明事实」间接满足。**咬住的洞**（GOAL-089 `W-6` 实测）：`producer_trust_label` 只看「产出方声明了 `run_chain` + 能力面落在带 `network_domains` 的 provider 上」，**不问本次是否真的执行过调用** ⇒ 一个只为把 provider 排除出**会话工具面**而声明 `run_chain` 的会话格（产出是**模型写的字**）被推成 `RETRIEVED`，下游检索格的 `minimum_retrieved_sources` 可被**单独满足**。出货检索格声明新维并升版 `1.1.0`。**同源的第二件**：同期把 GOAL-089 收口「为 m0 证据与覆盖的树脱节而多跑三次全量门（约 48 分钟）」的顺序纪律变成机器事实 —— `tools/run_m0_with_witness.py` 把「门跑的是哪棵树」写成**树内见证**（HEAD + 受判面脏文件+ 各自 `sha256`），判据重算当前树指纹比对，三态（没跑过 / 指纹不等 / 覆盖成立）**分得开**。两处**自我指涉**缺陷均由判据在当轮抓到并修掉（见证文件不得算进受判面；`--skip-run` 的见证无终态行 ⇒ 不得冒充正式见证）。读数：新判据 **15 条**（工具维 10 + 见证 5）；两向按压各判红并 raw `sha256` 逐字节复原；受影响套件 **1270 passed / 72 skipped**；`count_retrieved_sources` 与 `TrustLabel` **一行未动**（B 被否、A 留待拍板）。 | 证据 | [RECHECK-20261020-090](../../rechecks/RECHECK-20261020-090-goal-090-tool-dimension-and-m0-witness.md) |
