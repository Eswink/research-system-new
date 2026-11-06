# MAINLINE 进展记录归档 —— 序 72（GOAL-20261103-104）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-11-03 | GOAL-20261103-104 | **设计门禁扩到四组合 + 联调补齐 + 三条悬空样式**。① 三处静默失效的样式引用补上（`styles.muted` 改局部 / 两个 `var(--bg)`→`--bg-app` / `var(--text-dim)`→`--fg-faint`）+ 机械判据 `css-token-references.test.ts`（token 面 + 类名面 + 反证臂：注入 `var(--not-a-token)` 判红并点名）；② `design-fidelity` 参数化为四组合（双主题 × 双密度 × 中英文，对角取样）+ `run-timeline-phases` 让**十一相填充态**进基线（11 个 `phase-node`）+ **元素级**像素判据把门钉在 `phase-track` 上（整页截图看不见折叠线以下的进度条 —— 实测反证：只改颜色时结构签名与整页像素都仍绿，元素级判据判红 563 px）；win32 与 linux 各 144 张基线；③ 7 条后端路由接线（评审判词 / 研究方向 / 研究程序四条）或如实登记（库单件 / 记忆时效 / 任务重试），+ 判据 `backend-route-coverage.test.ts` / `unconsumed-registry.test.ts` 与 `docs/frontend/UNCONSUMED.md`；④ 收口验证器 + 断言集；⑤ `W-5`/`W-7` 核对不回退。 | 复检 | [RECHECK-20261103-104](../../rechecks/RECHECK-20261103-104-design-gate-and-integration-coverage.md) |
