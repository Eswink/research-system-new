# MAINLINE 进展记录归档 —— 序 68（GOAL-20261029-100）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-10-29 | GOAL-20261029-100 | **把「手稿」做成「能投出去的稿」，并把引用标记钉死**。① **引用编号注入提示词**：编号规则提成**一个**函数 `references.numbered_records`（去重后首次出现顺序），汇编器与渲染器**都调它**；每行以 `[n]` 开头，不可引用的 `ids[]` 记录标 `[not citable]` **不占编号**（占号会让其后整体错位）。三向判据：逐条相等 / 编造编号点名 / **改回裸标识 ⇒ 判据必须红**（真文件按压，6 条红）。② **投稿决策面**：`scientific_editor` **首次被协议激活**（`editorial` 相）；`EditorialDecision` 四值闭集进域，越界值点名拒绝、非 `accept` 而 `required_changes` 为空 ⇒ 点名判红；与验收门 验收门那两个判词 **刻意分开**。③ **返修底座**：`ReviewPoint`（`P1…Pn` + 三档严重性）由审稿人的 `weakest_link` 派生（此前**从未被解析成记录**）→ `AuthorResponse` → `response_letter.md`；漏答 / 编造编号 / **删一条应答** 三条反证各判红；**无表 / 无列 / 无迁移**。④ **`retmax` 可配**：具名默认 3 + `RESEARCHOS_RETMAX` + 显式参数，**默认逐字段不变**、非法值点名拒绝。⑤ 修掉 5 处**实现**缺陷（能力面漏声明 / 面板相跨相输入恒 ambiguous / `task.contract` 不存在 / 已渲染字符串被再渲染 / 应答信只 put 不 register）。判据 64 条（8+19+26+11）+ 产品入口 9 条全过。| 报告 | [RECHECK-20261029-100](../../rechecks/RECHECK-20261029-100-goal-100-submission-ready-and-citation-binding.md) |
