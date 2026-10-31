---
id: PLAN-20261031-102
slug: submission-package-and-revision-closure
title: GOAL-102 子计划 —— Artifact 父指针 + 改稿闭环 + 投稿包五件制品 + 期刊闭集
status: DONE
created_at: 2026-10-31
updated_at: 2026-11-01
parent_goal: GOAL-20261031-102
owners:
  - root-agent
subagent_parallel_limit: 3
latest_recheck: .cursor/plans/rechecks/RECHECK-20261031-102-submission-package-and-revision-closure.md
memory_entries: []
---

# PLAN-20261031-102

## 背景与靶子

GOAL-20261031-102 的三个靶子（缺口是建档实测的，靶面不在本计划重新推导）：

1. **改稿闭环**：`Artifact.supersedes` 父指针（域 + 两侧序列化）+ 应答会话携带改稿
   正文 + `action_taken` 引用真实制品；
2. **投稿包**：`submission` 会话相 + 报告相装配五件制品（信 / CRediT 分工 / COI /
   数据可得性 / 补充材料索引）；
3. **期刊闭集**：`journals.yaml` 声明面 + `editorial_decision` 的两个字段 + 三判据。

## 交付面（checkbox）

- [x] EC-01 域字段 + SQLite/Postgres 序列化 + 链校验判据（五条含三环）
- [x] EC-02 改稿装配 + 引用判据 + 三条反证 + 产品入口判据
- [x] EC-03 十一相协议 + 合约 + 五件制品装配 + 11 条单元判据 + 4 条产品判据
- [x] EC-04 闭集声明 + 选择解析/校验 + 9 条判据（四向反证 + 镜像 + 评分禁入）
- [x] EC-05 收口验证器 + 断言集 + 两处清单登记
- [x] EC-06 宪章记账（程序表序 70 / 阶梯 / 进展 / 修订 / ALL_PLAN）

## 复检

收口复检：`tools/verify_goal102_closeout.py --root . --verdict-only`（两树入口跑
`--script-mode shared`，见 GOAL 的 latest_recheck）。

## 备注

- migration 撞冻结面的预案（EC-01/02 Postgres 侧移序 71）**未触发**：030 是纯新增
  可空列，没有动任何既有行。
- `FakeArtifactStore.mark` 的重建白名单丢字段是本轮实测修掉的产品缺陷（判据
  `test_a_revised_body_supersedes_the_manuscript_it_replaces` 先红后绿）。
