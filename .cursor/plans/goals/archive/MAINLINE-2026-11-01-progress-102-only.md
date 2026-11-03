# MAINLINE 进展记录归档 —— 序 70（GOAL-20261031-102）

（自 `MAINLINE.md` 的 `## 进展记录` **原样搬入**；唯一允许的改动是相对链接基准修正：`../rechecks/` → `../../rechecks/`。活跃面保留**最近三条**。）

| 日期 | GOAL | 一句话结论 | 能力域 | RECHECK |
| --- | --- | --- | --- | --- |
| 2026-11-01 | GOAL-20261031-102 | **改稿闭环 + 投稿包五件制品 + 期刊闭集**。① **改稿闭环（artifact 父指针）**：`Artifact.supersedes`（域 + SQLite/Postgres 两侧序列化 + 链校验三反证）⇒ 应答会话的第二块 `revised_manuscript` 在报告相装成 `manuscript_v2.md`（supersedes → v1、不降硬规则门槛）；每条 `action_taken` 必须引用 v2 且引用的名字必须在本 run 制品名集合里（编造/空谈各点名）——「手稿真的改了」从应答信的一句话变成可判的结构事实；② **投稿包**：`submission` 会话相（十一相，申报过的扩展）+ 报告相装配五件制品（信逐字 / CRediT 27 角色闭集映射与本 run 分派对齐 / COI 结构化布尔字段 / 数据可得性 digest 读面字节可重算 / 补充材料索引）；③ **期刊闭集**：`journals.yaml`（无评分字段）+ 两字段 + 三判据（越闭集/空依据/半选各点名）+ 合约镜像判漂移。产品入口 6 条 + 9 条单元 e2e 全绿（真容器实验）。实测修掉 `FakeArtifactStore.mark` 重建白名单丢字段一处；另修 charter 读取器拒读 GOAL-101 的 W 编号乱序（纯重排零内容改动） |  深度+质量 | [RECHECK-20261031-102-submission-package-and-revision-closure.md](../../rechecks/RECHECK-20261031-102-submission-package-and-revision-closure.md) |
