# MAINLINE 进展记录归档 —— 序 66（GOAL-20261027-098）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-27 | GOAL-20261027-098 | **拆开创新点的作者与评审者 + 实验脚本由计划选择**。① **自评**（实测）：`novelty` 相与 `review` 相都点名 `novelty_reviewer`，而解析面只按 `agent.role` 取候选、不看 phase ⇒ 两相必然同一个 agent 实例 ⇒ 第二个判词是「评审自己刚写的声明」。新增 `novelty_author` + agent `novelty_writer`（第四个底层模型 `deepseek-v4-pro-0813`）⇒ 角色 / agent / 执行目标三者都不同；判据**跨 28 份出厂协议**判「评审者不得评自己写的产物」。② **选择级派生**：`experiment_design.script` 从出厂闭集（3 个脚本）点名，越界一律点名拒绝；契约 pin > 计划选择 > 装配兜底；反证删掉选择调用 ⇒ 行为判据判红。③ 归档面：`progress-075` 补宪章链接；10 条 4 格历史修订行**逐条登记**为不可修复；`verify_goal{076,090,095}` 三个从未存在的验证器补建并登记（**回填 ≠ 过门禁**）。 | 实验 | [RECHECK-20261027-098](../../rechecks/RECHECK-20261027-098-goal-098-independent-novelty-and-derived-experiment.md) |
