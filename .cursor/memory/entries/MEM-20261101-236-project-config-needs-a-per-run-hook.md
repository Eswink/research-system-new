---
id: MEM-20261101-236
title: "项目级配置不能在进程级装配面取值（会把第一个项目的设置施加给之后所有项目）"
status: ACTIVE
created_at: 2026-11-01
updated_at: 2026-11-01
scope: repository
confidence: 0.95
review_after: 2027-05-01
source_plans:
  - .cursor/plans/tasks/PLAN-20261101-103-phase-events-and-frontend-visible-chain.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md
supersedes: []
---

# 项目级配置不能在进程级装配面取值

## 做了什么

`retmax`（每次检索取几条）从「只读进程级 env」扩到「项目级声明」时，第一版想把它直接
写进 `CapabilityDeps.calls`（组合根装配时构造）。正确做法是给 `CapabilityDeps` 加一个
`retmax: int | None` 字段，由 `runner_wiring._with_project_retmax` 在**每次 run** 用
`RunContext.project` 派生一份，再由 `phase_call_arguments.apply_retmax` 施加到调用参数上。

## 为什么这样做

`CapabilityDeps` 是**进程级**装配面（组合根只造一次），而 `retmax` 是**项目级**声明。
在装配期取值 = 把「装配时第一个项目的设置」施加到之后所有项目的 run 上，而且这个错误
**没有任何判据会红**（两个项目各自单独跑都正确）。取值点必须晚于「这条 run 属于哪个
项目」已知 —— 即 `RunContext` 已经存在的那一层。

## 怎么做与复现

1. 给配置项分档：**进程级**（组合根装配时可以定）/ **请求级 / run 级**（必须在有上下文
   的那一层取）。只读 env 的项一旦要变项目级，就属于后者；
2. 在 per-run 层用 `dataclasses.replace` 派生一份（`_with_project_retmax`），不动进程级
   对象；
3. 判据钉两件事：① 取值点在 per-run 层（源码点名 `_with_project_retmax(` 出现在
   `runner_wiring`）；② 未声明时**返回同一个对象**（`apply_retmax(calls, None) is calls`）。

## 适用边界

- 只覆盖「装配一次、用到多次」的配置面；真正的进程级常量（如 `DEFAULT_RETMAX`）不适用；
- 「返回同一对象」这条 `is` 断言只对**无变化即原样返回**的实现成立（本仓的零回归口径）；
  若实现改成"总是派生一份但值相同"，判据要改成**逐字段相等**而不是 `is`。

## 来源

- GOAL-20261101-103 EC-05（`retmax` 进项目级）
- `.cursor/plans/rechecks/RECHECK-20261101-103-phase-events-and-frontend-visible-chain.md`
- 判据：`tests/application/test_retmax_project_setting.py`
