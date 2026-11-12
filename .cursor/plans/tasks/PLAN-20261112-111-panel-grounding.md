---
id: PLAN-20261112-111
slug: panel-grounding
title: GOAL-111 子计划 —— 面板判词从「某个模型认为」升级为可核验的结构断言
status: DONE
created_at: 2026-11-12
updated_at: 2026-11-12
parent_goal: GOAL-20261111-111
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261112-111-panel-grounding.md
memory_entries: []
---

# PLAN-20261112-111

## 背景与靶子

序 79：面板判词（GOAL-107 交付）是自由文本 `rationale`，读者**无法核对**它指的是
正文哪一句。本轮把它变成**可反驳**的：`REFUTED` 必须指向正文里真实存在的句子
（`S<n>` 编号或真实子串），否则降级 `AMBIGUOUS` 并点名缺什么。

## 交付面（checkbox）

- [x] `panel_grounding.py`（句子编号 + rationale 核验；两种「不成立」分得开）
- [x] `manuscript_panel` 的 `REFUTED` 过核验（不成立 ⇒ 降级点名）
- [x] 四条判据（正例 / 不存在句子 / 空 rationale / 仍 advisory）
- [x] `NOT_JUDGED` 五项逐字不动 + §7 补一句
- [x] 收口资产 + 宪章记账 + 台账 run id 回填

## 复检

`.cursor/plans/rechecks/RECHECK-20261112-111-panel-grounding.md`

## 验收条件

- 五条 EC 全部 PASS；
- 每条新增判据有反证臂且按压后确认判红；
- 全量 m0 终态行 `PASS: profile=m0; 23 deterministic checks`。

## 实施清单

- [x] EC-01 判词引用面
- [x] EC-02 `REFUTED` 必须被指向
- [x] EC-03 四条判据
- [x] EC-04 `NOT_JUDGED` 不动 + §7 补句
- [x] EC-05 收口资产

## 证据

判据读数（2026-11-12 实跑）：`test_panel_grounding.py` **19 passed**（引用面 8 +
降级 5 + advisory 2 + 切句同源 1 + 大小写 3）；`test_manuscript_quality.py` +
`test_manuscript_panel.py` **36 passed**（`NOT_JUDGED` 五项逐字与 advisory 边界）；
`test_goal111_ladder_report_scope.py` **5 passed**（一格推进）；
收口验证器 **69 PASS / 0 FAIL**。

## 影响报告

**Domain / API / schema 变化**：**零**。新增一个纯函数模块
（`deliverable/panel_grounding.py`）+ 面板内的一个降级函数（`ground_verdict`）；
没有新增或修改 Domain 实体、HTTP 路由、schema 或 DTO。**OpenAPI 快照零改动**
（无路由变化）。

**判据口径**：阶梯「报告」行的 `下一级` **追加**了「面板判词本身可被反驳」这一档，
**旧射程声明保留**（「这段写得好不好仍无判据」逐字在）；其余六行逐字未动。

**安全 / 凭据**：零变化。面板仍 advisory（不产生 `Decision`、不进验收门），
判据从源码面钉住这一点。

**兼容性 / 迁移风险**：**行为变化是收紧** —— 真实路径上若模型写了 `REFUTED` 却指不到
正文，该条判词会**从 `REFUTED` 降级为 `AMBIGUOUS`**。这会让面板的 `REFUTED` 票变少
（下游聚合的输入因此变化），但方向是「不可核验的判负不算判负」。`U-2` 已登记：
提示词还没要求模型写 `S<n>`，所以**当前降级率可能很高**；加提示词约束是下一轮的事。

## 工程记忆

（收口时按实际情况填写，或声明无可复用事实。）

## 状态历史

| 日期 | 状态 | 说明 |
| --- | --- | --- |
| 2026-11-12 | IN_PROGRESS | 建档 |
