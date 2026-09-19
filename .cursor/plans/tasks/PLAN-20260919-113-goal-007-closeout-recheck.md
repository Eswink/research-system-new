---
id: PLAN-20260919-113
slug: goal-007-closeout-recheck
title: GOAL-007 收口复检：EC-01…EC-06 在当前树与干净 checkout 上的证据 + 终止条款判定
status: IN_PROGRESS
created_at: 2026-09-19
updated_at: 2026-09-19
parent_goal: GOAL-20260919-007
cursor_plan_uri: null
owners:
  - root-agent
authorization:
  source: user-request
  ref: "GOAL-20260919-007 cycle 7 = 收口（GOAL「终止与收口」前置）。授权来源：2026-09-19 用户 goal 模式指令（自动化循环推进、无需逐轮确认）；push-to-main-for-CI 授权见 GOAL-20260919-007 frontmatter `authorization.ref`（只推 main、不 force、不重写历史、不推旁支）。复检**不新增产品能力**，只做证据复核、登记面收口与**复检实测出的缺陷修复**；不得放松默认 deny / 不改 Accepted ADR / 不改门禁与断言强度。"
subagent_parallel_limit: 3
latest_recheck: null
memory_entries: []
---

# PLAN-20260919-113 — GOAL-20260919-007 收口复检（cycle 7 = 收口）

## 目标

六条 EC 已全部 PASS（EC-06 于 cycle 6 收口）。按 GOAL「终止与收口」条款，`ACHIEVED`
还需**独立复检**：不读历史 RECHECK 的结论文本，直接在**当前树**与**干净 checkout** 上
复核六条 EC 的证据面（交付物 / 判据用例 / 登记一致），并写「终止与收口 · 收口结论」。

## 口径

- 复检脚本 `scratch/verify_goal007_closeout.py`（只读，gitignored）三层判据 =
  A 交付物在树 / B 判据用例在树 / C 登记面一致（GOAL 的 EC 表逐行 `status: PASS`、
  `latest_recheck` 指向、child_plans 文件存在且 DONE、ALL_PLAN 六行 DONE、MEM 文件存在）；
  任何一条不成立即非零退出（**不接受"记录里说 PASS"**）。
- **干净 checkout 封印**：`git clone --no-hardlinks` 到仓库外（`d001b62`，六条 EC 全部落地
  的 tip），在**克隆树**上跑同一份复检脚本与六条 EC 的判据套件；`node_modules` 用 junction
  指向本机已安装依赖（依赖是安装物、不是仓库内容），如实披露这一处。
- 定向套件在**同一轮**里真跑（六条 EC 的判据文件合并 + 收口额外复验），CI 台账以 GitHub API
  的逐 job conclusion 为准。
- **附带更正**（复检发现的登记面缺陷，如实登记）：EC 状态表的 **EC-04 / EC-05 行**在
  cycle 4 / cycle 5 回写时**漏改**——`status` 至今仍是表示「未完成」的枚举值、`evidence`
  仍为空串，与迭代日志、状态历史、两条 RECHECK 的 PASS 结论矛盾（GOAL-006 收口时也出现过
  同一类漂移，是**反复出现**的失败模式）。收口时按 RECHECK-110 / RECHECK-111 更正。
- **复检实测出的缺陷**：干净 checkout 上合并跑判据时发现**跨套件污染**（`tests/e2e` 的
  惰性工具类定义在函数内 ⇒ SDK 枚举 `Action` 具体子类时命中 `<locals>` 直接抛错 ⇒
  同进程后续 fork 的事件 round-trip 全挂）。修复方式是把类提升到模块级（与
  `tests/adapters/openhands/test_spike_e2e.py` 同形态），**不动任何断言**。

## 验收条件

- **AC-01** `scratch/verify_goal007_closeout.py` 在当前树全绿（层级 A/B/C，条数实测登记）。
- **AC-02** 六条 EC 的判据套件合并真跑通过（合并 passed/skipped 登记）；跨套件污染修复后
  原红组合转绿（同一命令前后对照）。
- **AC-03** 干净 checkout（`d001b62` clone）封印：复检脚本 + 判据套件在克隆树上真跑，
  结果与当前树一致；clone 的 `git status` 干净、文件数与 `git ls-files` 一致。
- **AC-04** 治理 `validate.py` 绿 + 本地 m0 全绿（23 项）+ 尺寸门/ruff/mypy 绿。
- **AC-05** GOAL 写入「终止与收口 · 收口结论」（EC 终态表 + 仍未处理的长程项 + 恢复条件），
  `latest_recheck` 指向 RECHECK-20260919-113，EC 表更正为逐行 PASS。
- **AC-06** 残余登记：六条 EC 的 W 列表汇总 + 「不因本 GOAL 存在而被宣称已解决」的项
  （ADR-0031 仍未拍板、门控无生产调用点、威胁建模/BOLA-BFLA 未覆盖、依赖 pin 升级、
  hook 侧 L3 门、`artifacts/` 明文 token 清理等）。

## 实施清单

- [ ] **WP-A** 复检脚本（三层判据）+ 当前树全绿
- [ ] **WP-B** 六条 EC 判据套件合并真跑 + 跨套件污染修复与对照
- [ ] **WP-C** 干净 checkout 封印（clone 上跑复检脚本与判据套件）
- [ ] **WP-D** 收口登记：RECHECK-20260919-113 + GOAL「收口结论」/`status: ACHIEVED` +
  EC 表更正 + 迭代日志 row 7 + ALL_PLAN
- [ ] **WP-E** 门禁：m0 23 项 / 治理 validate / 尺寸门 / ruff / mypy

## 证据

（执行后回填。）

## 影响报告

（执行后回填。）

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 7 建档（收口）；口径：独立复检（当前树 + 干净 checkout 双面）+ 登记面更正 + 复检实测缺陷修复 |
