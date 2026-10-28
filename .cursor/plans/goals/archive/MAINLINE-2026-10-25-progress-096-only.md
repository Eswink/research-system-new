# MAINLINE 进展记录归档 —— 序 64（GOAL-20261024-096）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-25 | GOAL-20261024-096 | **一次 run 走完六相科研链 + 报告第 1 节来自本 run 自己的问题**。① **断链**（实测）：23 份协议里没有任何一份同时含 `question` 与 `experiment` 相 ⇒ 没有一次 run 走过完整链。新建 `direction_to_report_v1.yaml`（六相），三条边全走既有机制；C-1 守住（`experiment`/`report` 不声明跨相 inputs）；两份既有协议一字未改。两向判据：改问题产出 ⇒ provider 收到的 query 变（离线与 live 各一层取证）；改检索产出 ⇒ plan 提示词材料变；摘 `question` ⇒ 编译期 `CROSS_PHASE_INPUT_INVALID`。② **报告第 1 节**：`report_facts` 原先写死 `objective=None` ⇒ 新增 `report_question.py` 读本 run 的 `research_question` 制品（新模块，避开 433/450 与 260 的规模线）；两处渲染器口径同步改成「本 run 自提」。③ **收口资产**：096 验证器 + 断言集 + **跨 GOAL** 判据（受判面内每个终态 GOAL 必须有验证器且被分类，含空真守卫）。残余：`W-1` 真跑受中转站限流阻塞（如实登记，不伪造）；`W-2` 计划产物跨相性质标签过宽（承 GOAL-089 `W-4`）；`W-3` 090/095/076 验证器不回填。 | 报告 | [RECHECK-20261024-096](../../rechecks/RECHECK-20261024-096-goal-096-direction-to-report-in-one-run.md) |
