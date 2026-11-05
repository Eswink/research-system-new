# MAINLINE 进展记录归档 —— 序 71（GOAL-20261101-103）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-11-01 | GOAL-20261101-103 | **相级进度成为一等事实 + 前端全链可见**。① `phase.started` / `phase.completed` 两个 Domain Event（`EventType` 39→41）+ `RunDetailDto.phases`（相结构取自 run **自己冻结的**协议正文；四态闭集；**失败/停车/重排不发 completed**）+ 前端十一相进度条（`data-phase-state` 四态计算色两两不同）；② 两个域层早有、读面不披露的字段补齐（`Artifact.supersedes` / `ReviewFinding.reviewer_model`）+ OpenAPI 快照与 `types.ts` 同轮重生成；③ 手稿链可读：19 类制品标签闭集（未命中不伪造）+ ReportsPage 手稿 Markdown 视图 + 编辑决定按四值闭集解析 + 投稿包 5 链接；④ `retmax` 进 `ProjectSettings` 并四级回落（**不声明时调用表逐字段不变**，`apply_retmax(calls, None)` 返回同一对象）；⑤ 早期一代三个验证器（026/028/029）首次进负判射程（**19 条判词**此前 0 条可见）+ 一条反证臂；叙述质量强口径**逐项论证**（§7：1/2/3 只能人评、4/5 可机械判但本轮不实现）。 | 复检 | [RECHECK-20261101-103](../../rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md) |
