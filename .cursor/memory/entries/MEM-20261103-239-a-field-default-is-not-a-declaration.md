---
id: MEM-20261103-239
title: "字段缺省值不是声明：四级回落里「未声明」必须是一等事实"
status: ACTIVE
created_at: 2026-11-03
updated_at: 2026-11-03
scope: repository
confidence: 0.95
review_after: 2027-05-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261103-105-citation-readings-and-review-driven-revision.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261103-105-citation-readings-and-review-driven-revision.md
supersedes: []
---

# 字段缺省值不是声明

## 做了什么

GOAL-20261103-105 EC-03 修掉了 `retmax` 的缺省抹平：`ProjectSettings.retmax` 的缺省从
`3` 改成 `None`，`_retmax_of` 缺省返回 `None`。修完并把它升到协议相级
（`ProtocolPhase.run_chain_arguments`），优先级最终为
显式参数 > 协议相级 > 项目声明（**仅当已声明**） > `RESEARCHOS_RETMAX` > 默认 3。

## 为什么这样做

**「四级回落」里最贵的一格不是任何一级的值，而是「这一级到底声明了没有」。** 只要字段的
缺省值是一个**有意义的业务值**（这里是 `3`），它就同时表达了两件事：「没人配置」与「有人
把它配成 3」。施加点无法区分，于是把字段缺省当成一次声明施加下去，**下面各级全部失效**。
实测形态：`RESEARCHOS_RETMAX=9` 在构造期给 `{'retmax': 9}`，运行期被压成 `{'retmax': 3}`；
显式参数 `retrieval_calls(7)` 同样从 7 变成 3。

这也解释了为什么「修一个回落优先级」容易被做成**再叠一层覆盖**：只要 `None` 不被当作
合法取值，任何修法都只能靠"谁最后写谁赢"。让 `None` 成为「未声明」的**唯一**表示，
施加点原有的 `declared is None ⇒ 原样返回` 立刻生效，一行都不用改。

## 怎么做与复现

- 设计回落时，先问「未声明」有没有**自己的**表示。没有就先加，别急着排优先级。
- 判据要判**施加之后**的值（本 GOAL 读的是出站请求的 `pageSize`），不是构造期的调用表 ——
  缺陷恰好发生在构造期与运行期之间。
- 反证方向要对：把缺省改回业务值 ⇒ 「未声明臂」应红，而「显式声明压过 env」应**仍绿**。
  两者同时红说明修法把声明那一级也弄坏了。
- 钉住缺陷的既有判据（这里是 `test_project_settings_defaults_retmax_to_three`）就是
  **要改的东西**：它断言的是错的行为，改写它属于修复，不属于放宽。

## 适用边界

- 只对**有回落链**的配置量成立。单级配置（读不到就用常量）没有这个歧义。
- `None` 一旦成为「未声明」的表示，**就不能再表示"显式关掉"**。若某个量需要
  「关掉」这一档，它要另有表示（本 GOAL 的 `retmax` 不需要：取 0 条没有业务含义）。
- 本条的判据口径依赖「施加点只判 `is None`」。若将来施加点改成真值判断
  （`if not retmax`），`None` 与 `0` 会重新合流 —— 那时这条记忆的前提就失效了。

## 来源

- 计划：`.cursor/plans/tasks/PLAN-20261103-105-citation-readings-and-review-driven-revision.md`
- 复检：`.cursor/plans/rechecks/RECHECK-20261103-105-citation-readings-and-review-driven-revision.md`
  （`D-1` 段记了修复前/后的实测读数，`反证臂汇总` 表记了两向按压）
- 代码：`packages/application/ports/resource_catalog.py`（缺省 `None`）、
  `packages/application/run_orchestration/phase_call_arguments.py`（`retmax_for_phase`）
- 判据：`tests/application/test_retmax_undeclared_is_a_fact.py`（5 条，含三条反证臂）

## 相关

- `[[declared-but-never-constructed-is-a-dead-seam]]`：同类 —— 声明在文档里而施加点拿不到。
- `MEM-20261103-238`：同一轮的邻居（静默失效要有文本判据）。
