# MAINLINE 进展记录归档 —— 序 74（GOAL-20261104-106）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-11-05 | GOAL-20261104-106 | **十一相手稿链首次在真实模型 + 真实中转站下成立**。`direction_to_manuscript_v1.yaml`（question → retrieval → novelty → plan → experiment → review → manuscript → editorial → revision → submission → report）此前**真实 run 合计 0 次**（2026-11-04 全仓 115 个 SQLite 逐一普查）—— 它只被 mock 中转站 e2e 验证过，而「产品入口跑通全链」那条 live 判据跑的是 `direction_to_report_v2`（七相）。本轮补上 live 判据（`tests/e2e/test_the_manuscript_chain_runs_live.py`，产品组合根 `assemble()`、**一律不补缝**、读数先写盘再断言）+ 跑到一次 `SUCCEEDED` + GOAL-105 两件机制在**真实手稿**上的取证（脚注三读数与正文重算逐项相等 / 每条 `action_taken` 与**它自己那条**评审点实词重叠）+ 失败形态台账 + 收口验证器（断言**真实 run 的读数文件在树**，不是散文说跑过）。 | 报告+实验+复检 | [RECHECK-20261104-107](../../rechecks/RECHECK-20261104-107-manuscript-chain-live.md) |
