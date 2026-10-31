# MAINLINE 进展记录归档 —— 序 67（GOAL-20261028-099）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-28 | GOAL-20261028-099 | **产出投稿形状的手稿（IMRaD + 真参考文献）**。① 新建八相协议 `direction_to_manuscript_v1.yaml`（v2 七相 + `manuscript`，**v2 一字未改**）+ 合约 `research_manuscript`：**不声明** `report:` ⇒ 手稿相是**会话相**，模型写 Abstract 与六个 IMRaD 节，汇编器在 report 相装出 `manuscript.md`。② 新建 `deliverable/references.py`：Vancouver 行（作者/题名/刊名/年份/doi/PMID 逐字取自落盘的 tool-result 字节），**两种作者形态都认**（实测 6 条列表 / 4 条整串），缺失**点名**不填占位符。③ 数字可核：正文任何 Unicode 十进制数位（引用标记除外）⇒ 点名拒绝；`[n]` 与 References **双向闭合**。④ 从**产品入口**产出（`TestClient(create_app(deps))`），关掉开关 ⇒ 报告**同一 run 字面逐字节**不变。96 条新判据（38+24+22+5+7）全过。| 报告 | [RECHECK-20261028-099](../../rechecks/RECHECK-20261028-099-goal-099-submission-shaped-manuscript.md) |
