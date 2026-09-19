---
id: PLAN-20260919-113
slug: goal-007-closeout-recheck
title: GOAL-007 收口复检：EC-01…EC-06 在当前树与干净 checkout 上的证据 + 终止条款判定
status: DONE
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
latest_recheck: .cursor/plans/rechecks/RECHECK-20260919-113-goal-007-closeout-recheck.md
memory_entries:
  - MEM-20260919-085
  - MEM-20260919-086
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

- [x] **WP-A** 复检脚本（三层判据）+ 当前树全绿
- [x] **WP-B** 六条 EC 判据套件合并真跑 + 跨套件污染修复与对照
- [x] **WP-C** 干净 checkout 封印（clone 上跑复检脚本与判据套件）
- [x] **WP-D** 收口登记：RECHECK-20260919-113 + GOAL「收口结论」/`status: ACHIEVED` +
  EC 表更正 + 迭代日志 row 7 + ALL_PLAN
- [x] **WP-E** 门禁：m0 23 项 / 治理 validate / 尺寸门 / ruff / mypy

## 证据

- **WP-A**：`scratch/verify_goal007_closeout.py`（只读，gitignored；三层判据 A 交付物 /
  B 判据用例 / C 登记面）⇒ 当前树 **80 checks / 0 failures**。C 层抓出并更正一处**登记面
  漂移**：EC-04 / EC-05 的 frontmatter 行在 cycle 4 / cycle 5 回写时漏改（`status` 仍是
  「未完成」枚举、`evidence` 空串）——与迭代日志/状态历史/RECHECK-110/111 矛盾；
  用 `git log -L` 回溯确认那两行**自建档后从未被改过**。
- **WP-B**：六条 EC 判据套件**合并真跑**（同一命令、同一进程）：
  `tests/api/test_runtime_selection_surface.py` + `test_runtime_egress_gate.py` +
  `test_session_llm_factory.py` + `tests/e2e/test_ec03_real_runtime_offline_chain.py` +
  `tests/architecture/python/test_tool_plane_boundary.py` +
  `tests/contracts/test_agent_runtime_contract.py` +
  `tests/tooling/test_toolpack_capability_policy_pending.py` ⇒ **85 passed / 1 skipped**。
  **修复前同一命令 83 passed / 2 failed / 1 skipped**：两条 `[_openhands_runtime_factory]`
  fork 用例红，根因 = `tests/e2e` 的惰性工具把 SDK `Action` 子类定义在**函数内**，SDK 枚举
  具体子类时命中 `<locals>` 抛 `Local classes not supported!` ⇒ 同进程后续事件 round-trip
  （fork 走它）全挂；**m0 / CI 是字母序**（`tests/contracts` 在 `tests/e2e` 之前）所以看不见。
  修复 = 三个类提升到模块级（与 `tests/adapters/openhands/test_spike_e2e.py` 同形态），
  **未改任何断言**。
- **WP-C**：`git clone --no-hardlinks` 到仓库外（`d001b62`；`node_modules` 以 junction 指向
  本机已安装依赖——依赖是安装物、非仓库内容，**如实披露这一处人为补足**）。clone 上：
  复检脚本 80 checks / 1 failure（唯一失败项 = RECHECK-113 文件尚未存在，属收口循环自身产物，
  非证据面缺陷）；六条 EC 判据套件 83 passed / **2 failed** / 1 skipped = **与当前树修复前的
  同一签名**（两树结论一致）。
- **WP-D**：GOAL `status: ACHIEVED`；`latest_recheck` 指向 RECHECK-20260919-113；
  child_plans 增列本 PLAN；EC 表逐行更正为 PASS（EC-04 / EC-05 补证据）；
  「终止与收口 · 收口结论」写入 EC 终态表 + 收口期间两件事 + 8 项残余 + 恢复条件；
  迭代日志 row 7；`MEM-20260919-085`（GOAL 记录漂移）与 `MEM-20260919-086`（SDK 局部
  `Action` 子类毒化进程）+ `memory/INDEX.md` 两行。
- **WP-E**：m0 **PASS: profile=m0; 23 deterministic checks**；尺寸门 **950 passed**；
  `ruff check` / `ruff format --check` 绿（含本轮改动的 e2e 文件）；`mypy`（含改动文件）绿；
  治理 `validate.py` 绿。

## 影响报告

- **Domain / API / schema**：无变化（本轮零产品代码改动；唯一代码改动在 `tests/e2e/`）。
- **安全 / 凭据**：无变化；默认 deny 姿态未触碰；未新增依赖、未改 pin。
- **兼容性 / 迁移**：无迁移、无数据变更。
- **上游版本影响**：无。
- **测试面**：一处**跨套件污染**被修复（顺序依赖的假绿），判据强度不变；m0 / CI 与所有
  既有套件的断言均未改动。
- **残余（不因收口而消失）**：8 项长程项见 GOAL「终止与收口 · 收口结论」；其中
  `docs/adr/ADR-0031-toolpack-capability-policy.md` 仍是 **`Status: Proposed`**，
  **是否采纳归用户**。

## 状态历史

| 时间 | 状态 | 说明 |
| --- | --- | --- |
| 2026-09-19 | IN_PROGRESS | cycle 7 建档（收口）；口径：独立复检（当前树 + 干净 checkout 双面）+ 登记面更正 + 复检实测缺陷修复 |
| 2026-09-19 | DONE | 复检脚本 80 checks / 0 failures；判据套件合并 85 passed / 1 skipped（修复前 2 failed）；干净 checkout 封印（两树一致）；m0 23/23；GOAL `ACHIEVED` + 收口结论 + EC 表更正 + 两项 MEM；治理 validate 绿 |
