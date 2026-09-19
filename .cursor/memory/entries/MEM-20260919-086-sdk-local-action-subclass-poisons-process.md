---
id: MEM-20260919-086
title: "不要在函数内定义 SDK Action 子类：SDK 枚举具体子类时命中 <locals> 直接抛错，毒化同进程后续所有事件 round-trip（m0 字母序看不见）"
status: ACTIVE
created_at: 2026-09-19
updated_at: 2026-09-19
scope: repository
confidence: 0.9
review_after: 2027-09-19
source_plans:
  - .cursor/plans/tasks/PLAN-20260919-113-goal-007-closeout-recheck.md
source_rechecks:
  - .cursor/plans/rechecks/RECHECK-20260919-113-goal-007-closeout-recheck.md
supersedes: []
tags:
  - openhands-sdk
  - test-isolation
  - cross-suite-pollution
  - ordering-dependent
  - e2e
---

# SDK 局部 Action 子类 = 进程级污染（GOAL-20260919-007 / cycle 7 收口）

## 做了什么

收口复检在干净 checkout 上合并跑六条 EC 的判据套件时 **2 failed**（`tests/contracts`
的两条 openhands fork 用例），同一条命令在当前树**也红** ⇒ 与干净 checkout 无关，
是**跨套件污染**。定位到根因后把 `tests/e2e/test_ec03_real_runtime_offline_chain.py`
的三个惰性工具类从**函数内**提升到**模块级**（与 `tests/adapters/openhands/test_spike_e2e.py`
同形态），**未改任何断言**：同一命令 83 passed / **2 failed** / 1 skipped → **85 passed / 1 skipped**。

## 为什么这样做（可复用结论）

1. **根因（读的是安装的 SDK 源码，不是猜）**：`openhands/sdk/utils/models.py::_get_checked_concrete_subclasses`
   会遍历 `Action.__subclasses__()` 构建判别联合，遇到 `"<locals>" in sub.__qualname__`
   直接抛
   `Local classes not supported! <module>.<name> / openhands.sdk.tool.schema.Action`。
   所以**只要进程里存在过**一个函数内定义的 `Action` 子类，此后任何
   `Event.model_validate_json(event.model_dump_json(...))`（SDK 的 fork 路径就会走它）
   都会失败 —— 毒化是**进程级、且不可逆**的（类对象一直在 `__subclasses__` 里）。
2. **为什么 CI 看不见**：触发条件是"污染源文件先跑"。m0 / CI 是字母序，
   `tests/contracts` 排在 `tests/e2e` **之前** ⇒ 永久掩盖。**顺序依赖的假绿**：
   重排测试文件、或用 `-p no:randomly` 之外的方式定点跑，就会红。
3. **动作**：任何给 SDK 注册工具的测试，`Action` / `Observation` / `ToolDefinition` 子类
   一律定义在**模块级**（本仓已有先例：`test_spike_e2e.py`、`test_error_cancel_integration.py`）。
   需要惰性导入 SDK 时，把导入放模块级但**只影响该测试模块**，比"函数内建类"安全得多。
4. **复现命令**（任何树都能跑，10 秒级）：
   `pytest tests/e2e/test_ec03_real_runtime_offline_chain.py tests/contracts/test_agent_runtime_contract.py`

## 怎么做与复现

- 复原（用于反证）：把类挪回函数内 ⇒ 上面这条命令立刻 2 failed。
- 定位：从失败栈看 `_copy_event_for_fork` → `Event.model_validate_json` →
  `Local classes not supported!`；再在 SDK 里 grep 这句即得确切判据。

## 适用边界

- 本记录只覆盖 **SDK 判别联合的局部类**问题；其他 SDK 全局注册（`register_tool` 按名注册）
  造成的"顺序依赖"不在内（本轮未观察到其导致失败）。
- 修复**不改变**判据强度：EC-03 的四段链路断言、EC-05 的契约断言均未动。
- 干净 checkout 封印**保留**了这个红（因 clone 停在修复前的 tip），本轮把它当作封印的
  正样本：clone 与当前树在修复前**结论一致**（都红），修好后又一致（都绿）。

## 来源

- `.cursor/plans/rechecks/RECHECK-20260919-113-goal-007-closeout-recheck.md` W-10
- 代码：`tests/e2e/test_ec03_real_runtime_offline_chain.py`（模块级 `_InertAction` /
  `_InertExecutor` / `InertTool`）、对照 `tests/adapters/openhands/test_spike_e2e.py`
- 上游：`.venv/Lib/site-packages/openhands/sdk/utils/models.py`（`_get_checked_concrete_subclasses`）
